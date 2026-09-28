import random

import portkit
from pyhvac.fields import Field, Layout, Sum8
from pyhvac.ir.codec import encode
from pyhvac.ir.model import Frame, Protocol, PulseDistance, Section

PROTOCOL = Protocol(
    "planted",
    {
        "leader": Section(None, header=(10000,), gap=25000),
        "main": Section(
            PulseDistance(460, 420, 1270), header=(3500, 1700), footer=(460,), gap=40000
        ),
    },
)
LAYOUT = Layout(
    b"\x11\xda\x00\x00\x00",
    {"fan": Field.at(3, 4, 3), "temp": Field.at(2, 0, 8)},
    checksum=Sum8(0, 4, 4),
)


def records():
    """Synthetic oracle records with a fan field planted at byte 3 bits 4-6."""
    out = []
    for fan in (0, 3, 4, 7):
        for temp in (18, 24, 30):
            data = bytes(LAYOUT.build(fan=fan, temp=temp))
            pulses = encode(
                PROTOCOL, [Frame("leader", b""), Frame("main", data)]
            ).pulses
            out.append({"state": {"fan": fan, "temp": temp}, "pulses": list(pulses)})
    return out


def test_cluster_groups_within_tolerance():
    assert portkit.cluster([428, 430, 1280, 1275, 3650]) == [
        (429, 2),
        (1278, 2),
        (3650, 1),
    ]


def test_bursts_split_after_long_spaces():
    pulses = records()[0]["pulses"]
    parts = portkit.bursts(pulses)
    assert [len(p) for p in parts] == [2, 4 + 2 * 40]


def test_timings_report_drafts_the_protocol():
    text = portkit.timings_report(records())
    assert "bitless" in text and "40 bits" in text
    assert "Section(None, header=(10000,), gap=25000)" in text
    assert "PulseDistance(460, 420, 1270)" in text


def test_decode_all_then_diff_finds_the_planted_field():
    decoded = portkit.decode_all(records(), PROTOCOL, ["leader", "main"])
    assert not [m for _, m in decoded if isinstance(m, Exception)]
    report = portkit.diff_report(decoded)
    fan_line = next(line for line in report.splitlines() if line.startswith("fan:"))
    # byte 3 bits 4-6, plus checksum bits (byte 4) that follow them
    assert "(1, 3, 4)" in fan_line and "(1, 3, 6)" in fan_line
    assert "(1, 3, 7)" not in fan_line


def test_single_key_pairs():
    states = [{"a": 1, "b": 1}, {"a": 2, "b": 1}, {"a": 2, "b": 2}]
    assert portkit.single_key_pairs(states) == {"a": [(0, 1)], "b": [(1, 2)]}


def test_find_checksums_finds_the_planted_sum():
    rng = random.Random(3)
    frames = []
    for _ in range(30):
        data = bytearray(rng.randrange(256) for _ in range(6))
        Sum8(0, 5, 5).apply(data)
        frames.append(bytes(data))
    assert Sum8(0, 5, 5, False) in portkit.find_checksums(frames)


def test_smoke_on_real_fixture():
    text = portkit.timings_report(portkit.load_records("DAIKIN2"))
    assert "(10024, 200)" in text
