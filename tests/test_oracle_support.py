import gzip
import json
import random

import pytest

from oracle import ORACLE_DIR, check_against_oracle, load_oracle
from pyhvac.fields import Field, Joined, Layout, Sum8
from pyhvac.ir.codec import DecodeError, encode
from pyhvac.ir.model import Frame, Protocol, PulseDistance, Section

NEC = Protocol(
    "nec",
    {
        "nec": Section(
            PulseDistance(560, 560, 1690), header=(9000, 4500), footer=(560,), gap=40000
        )
    },
)
FRAMES = [Frame("nec", b"\x12\x34")]


def record(pulses):
    return {"state": {}, "pulses": list(pulses)}


def test_accepts_matching_jittered_record():
    rng = random.Random(7)
    pulses = [round(d * rng.uniform(0.95, 1.05)) for d in encode(NEC, FRAMES).pulses]
    check_against_oracle(NEC, record(pulses), FRAMES)


def test_rejects_different_bytes():
    pulses = encode(NEC, [Frame("nec", b"\x12\x35")]).pulses
    with pytest.raises(AssertionError):
        check_against_oracle(NEC, record(pulses), FRAMES)


def test_rejects_different_timing():
    pulses = [d * 2 for d in encode(NEC, FRAMES).pulses]
    with pytest.raises((AssertionError, DecodeError)):
        check_against_oracle(NEC, record(pulses), FRAMES)


def test_load_oracle_reads_gzipped_json(tmp_path, monkeypatch):
    monkeypatch.setattr("oracle.ORACLE_DIR", tmp_path)
    (tmp_path / "NEC.json.gz").write_bytes(
        gzip.compress(json.dumps([record([1, 2])]).encode())
    )
    assert load_oracle("NEC") == [record([1, 2])]


FILES = sorted(ORACLE_DIR.glob("*.json.gz"))


@pytest.mark.parametrize("path", FILES, ids=[p.name for p in FILES])
def test_fixture_is_well_formed(path):
    records = json.loads(gzip.decompress(path.read_bytes()))
    assert records
    for rec in records:
        assert {"plugin", "model", "class", "variant", "state", "pulses"} <= set(rec)
        assert rec["pulses"]
        assert all(isinstance(d, int) and d > 0 for d in rec["pulses"])


# A Joined layout: one Layout over consecutive frames (a checksum that spans
# them), for assert_matches_oracle.
_JOINED = Layout(b"\x12\x00\x00", {"x": Field.at(1, 0, 4)}, checksum=Sum8(0, 2, 2))


class _TwoFrameDevice:
    """Frame "a" holds byte 0, frame "b" bytes 1-2; byte 2 sums bytes 0-1."""

    PROTOCOL = Protocol("two", {"a": NEC.sections["nec"], "b": NEC.sections["nec"]})
    capabilities = None

    def __init__(self, x):
        self.x = x

    def frames(self, previous, target, actions):
        data = _JOINED.build(x=self.x)
        return [Frame("a", bytes(data[:1])), Frame("b", bytes(data[1:]))]


def _joined_record(x):
    data = _JOINED.build(x=x)
    pulses = encode(
        _TwoFrameDevice.PROTOCOL, [Frame("a", data[:1]), Frame("b", data[1:])]
    )
    return record(pulses.pulses)


def _patch_state(monkeypatch):
    import port_oracle

    monkeypatch.setattr(port_oracle, "state_from_record", lambda device, old: None)
    return port_oracle


def test_joined_layout_matches_identical_frames(monkeypatch):
    po = _patch_state(monkeypatch)
    po.assert_matches_oracle(
        _TwoFrameDevice(3), _joined_record(3), (Joined(_JOINED, 2),)
    )


def test_joined_layout_accepts_a_declared_field_and_its_cross_frame_checksum(
    monkeypatch,
):
    po = _patch_state(monkeypatch)
    defects = (po.Defect("x", 5, 3, "test"),)
    po.assert_matches_oracle(
        _TwoFrameDevice(5), _joined_record(3), (Joined(_JOINED, 2),), defects
    )


def test_joined_layout_rejects_an_undeclared_field(monkeypatch):
    po = _patch_state(monkeypatch)
    with pytest.raises(AssertionError, match="'x'"):
        po.assert_matches_oracle(
            _TwoFrameDevice(5), _joined_record(3), (Joined(_JOINED, 2),)
        )


def test_joined_layout_must_cover_every_frame(monkeypatch):
    po = _patch_state(monkeypatch)
    with pytest.raises(AssertionError, match="one layout"):
        po.assert_matches_oracle(
            _TwoFrameDevice(3), _joined_record(3), (Joined(_JOINED, 1),)
        )
