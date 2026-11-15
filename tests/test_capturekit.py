"""tools/capturekit.py: hvactest captures to checks, a match and portkit records."""

import base64

import pytest

import gzip
import json

from capturekit import Capture, check, load, main, match, parse_note, records
from hvactest.log import SessionLog
from pyhvac import registry
from pyhvac.ir.formats import to_broadlink
from pyhvac.state import HvacState

DAIKIN = registry.get_device("Daikin", "FTXM20R5V1B")


def packet(device=DAIKIN, power=True, mode="cool", temperature=24.0, **kw):
    state = HvacState(power, mode, temperature, **kw)
    return to_broadlink(device.encode(None, state).signal)


def write_log(path, entries):
    """hvactest-style log: one learn event per (note, packet or None)."""
    log = SessionLog(path)
    log.write("send", model=["X", "Y"])  # other events are ignored
    for note, pkt in entries:
        code = None if pkt is None else base64.b64encode(pkt).decode()
        log.write("learn", model=["X", "Y"], code=code, note=note)
    return path


BASE = "power=on mode=cool temperature=24 fan=auto"


def test_parse_note():
    assert parse_note("power=on mode=cool  temperature=24 # baseline") == {
        "power": "on",
        "mode": "cool",
        "temperature": "24",
    }
    assert parse_note("  # only a comment") == {}
    for bad in ("power", "=on", "fan=", "fan=1 fan=2"):
        with pytest.raises(ValueError):
            parse_note(bad)


def test_check_clean_log(tmp_path):
    log = write_log(
        tmp_path / "c.jsonl",
        [
            (BASE, packet()),
            ("power=on mode=cool temperature=25 fan=auto", packet(temperature=25.0)),
            ("power=on mode=cool temperature=26 fan=auto", None),  # retried
            ("power=on mode=cool temperature=26 fan=auto", packet(temperature=26.0)),
        ],
    )
    captures, problems = load(log)
    assert problems == []
    assert [c.index for c in captures] == [1, 2, 3]
    assert isinstance(captures[0], Capture)
    assert captures[1].setting["temperature"] == "25"
    assert check(captures) == ([], [])
    assert main(["check", str(log)]) == 0


def test_check_reports_bad_notes(tmp_path, capsys):  # Review Focus 1
    log = write_log(
        tmp_path / "c.jsonl",
        [
            (BASE, packet()),
            ("power=on mode=cool tempreature=25 fan=auto", packet(temperature=25.0)),
            ("power=on mode=cool24 temperature=24 fan=auto", packet(mode="heat")),
            ("power=maybe mode=cool temperature=24 fan=auto", packet(mode="dry")),
            ("power=on mode=cool temperature=hot fan=auto", packet(fan="1")),
            ("", packet(fan="2")),
            ("power on", packet(fan="3")),
        ],
    )
    captures, problems = load(log)
    assert len(problems) == 1 and "capture 7" in problems[0]
    errors, warnings = check(captures)
    text = "\n".join(errors)
    assert "capture 2" in text and "temperature" in text
    assert "capture 3" in text and "mode" in text
    assert "capture 4" in text and "power" in text
    assert "capture 5" in text and "temperature" in text
    assert "capture 6" in text and "no note" in text
    assert "did you mean temperature" in text
    assert main(["check", str(log)]) == 1
    assert "capture 7" in capsys.readouterr().out


def test_left_out_keys_are_the_baseline_and_features_are_listed(tmp_path):
    log = write_log(
        tmp_path / "c.jsonl",
        [
            (BASE, packet()),
            ("power=off", packet(power=False)),
            ("powerful=on", packet(features={"powerful": True})),
        ],
    )
    captures, _ = load(log)
    assert captures[1].setting == {
        "power": "off",
        "mode": "cool",
        "temperature": "24",
        "fan": "auto",
    }
    errors, warnings = check(captures)
    assert errors == []
    assert warnings == ["features (not core settings): powerful"]


def test_same_code_under_two_settings_is_an_error(tmp_path):
    log = write_log(
        tmp_path / "c.jsonl",
        [(BASE, packet()), ("power=on mode=heat temperature=24 fan=auto", packet())],
    )
    errors, _ = check(load(log)[0])
    assert any("capture 1" in e and "capture 2" in e for e in errors)


def test_check_warns_on_repeats(tmp_path):  # Review Focus 4
    log = write_log(
        tmp_path / "c.jsonl",
        [(BASE, packet()), (BASE, packet(temperature=25.0))],
    )
    errors, warnings = check(load(log)[0])
    assert errors == []
    assert any("capture 1" in w and "capture 2" in w for w in warnings)
    assert main(["check", str(log)]) == 0


def test_fahrenheit_temperatures_are_accepted(tmp_path):
    log = write_log(
        tmp_path / "c.jsonl",
        [("power=on mode=cool temperature=75F fan=auto", packet())],
    )
    assert check(load(log)[0]) == ([], [])


def test_empty_log(tmp_path, capsys):  # Review Focus 5
    log = write_log(tmp_path / "c.jsonl", [(BASE, None), (BASE, None)])
    captures, _ = load(log)
    assert captures == []
    errors, _ = check(captures)
    assert errors == ["no usable capture: every Learn timed out or the log is empty"]
    assert main(["check", str(log)]) == 1


# --------------------------------------------------------------------- match


def some_candidates():
    """A few protocol families: matching against all of them takes ~20 s."""
    from hvacir import match as M

    return [
        c
        for c in M.candidates()
        if c.name.startswith(("Daikin", "Airspool", "Electra", "Gree", "Kelon"))
    ]


def daikin_session(tmp_path, extra=()):
    entries = [
        (BASE, packet()),
        ("temperature=20", packet(temperature=20.0)),
        ("temperature=28", packet(temperature=28.0)),
        ("mode=heat", packet(mode="heat")),
        ("mode=dry", packet(mode="dry")),
        ("mode=auto", packet(mode="auto")),
        ("fan=low", packet(fan="1")),
        ("fan=mid", packet(fan="3")),
        ("fan=high", packet(fan="5")),
        ("power=off", packet(power=False)),
        *extra,
    ]
    return load(write_log(tmp_path / "c.jsonl", entries))[0]


def test_known_model_is_supported(tmp_path):
    verdict = match(daikin_session(tmp_path))
    assert verdict.path == "supported", verdict.reasons
    assert verdict.candidate.startswith("Daikin")
    assert verdict.fans["low"] == "1" and verdict.fans["high"] == "5"


def test_fahrenheit_notes_match(tmp_path):  # Review Focus 3
    dev = registry.get_device("Airspool", "Mini-split")
    entries = []
    for i, c in enumerate((20.0, 22.0, 24.0, 26.0, 28.0)):
        f = round(c * 9 / 5 + 32)
        note = (
            f"power=on mode=cool temperature={f}F fan=auto"
            if i == 0
            else (f"temperature={f}F")
        )
        entries.append((note, packet(dev, temperature=c)))
    entries.append(("mode=heat", packet(dev, mode="heat", temperature=20.0)))
    captures = load(write_log(tmp_path / "c.jsonl", entries))[0]
    verdict = match(captures, some_candidates())
    assert verdict.path == "supported", verdict.reasons
    assert verdict.candidate.startswith("Airspool")


def test_labels_not_one_to_one_are_not_supported(tmp_path):  # Review Focus 2
    captures = daikin_session(tmp_path, extra=[("fan=quiet", packet(fan="1"))])
    verdict = match(captures, some_candidates())
    assert verdict.path != "supported"
    assert any("low" in r and "quiet" in r for r in verdict.reasons)


def test_missing_variant_is_variant(tmp_path):
    from hvacir import match as M

    dev = registry.get_device("Beko", "BEVCA 120")
    entries = [("power=on mode=cool temperature=24 fan=auto", packet(dev))]
    entries += [
        (f"temperature={t}", packet(dev, temperature=float(t))) for t in (18, 22, 30)
    ]
    entries += [(f"mode={m}", packet(dev, mode=m)) for m in ("heat", "dry", "fan")]
    entries += [(f"fan={f}", packet(dev, fan=f)) for f in ("1", "2", "3")]
    entries.append(("power=off", packet(dev, power=False)))
    captures = load(write_log(tmp_path / "c.jsonl", entries))[0]
    cands = [c for c in M.candidates() if c.name != "ElectraAcDevice/aux"]
    verdict = match(captures, cands)
    assert verdict.path == "variant", verdict
    assert verdict.candidate == "ElectraAcDevice"
    assert verdict.gaps


def test_unknown_code_is_new(tmp_path):
    from pyhvac.ir.formats import broadlink_packet

    def nec(byte):
        pulses = [9000, 4500]
        for i in range(32):
            bit = (byte >> (i % 8)) & 1
            pulses += [560, 1690 if bit else 560]
        return broadlink_packet(pulses + [560])

    entries = [("power=on mode=cool temperature=24 fan=auto", nec(0x12))]
    entries += [(f"temperature={t}", nec(t)) for t in (20, 26)]
    captures = load(write_log(tmp_path / "c.jsonl", entries))[0]
    verdict = match(captures)
    assert verdict.path == "new"
    assert verdict.candidate is None


def test_feature_capture_is_mapped(tmp_path):
    captures = daikin_session(
        tmp_path,
        extra=[("turbo=on", packet(features={"powerful": True}))],
    )
    verdict = match(captures, some_candidates())
    assert verdict.path == "supported", verdict.reasons
    assert verdict.features == {"turbo=on": "powerful=True"}


def test_unreproduced_feature_makes_a_variant(tmp_path):
    captures = daikin_session(
        tmp_path,
        extra=[("ionizer=on", packet(temperature=21.0))],  # not what pyhvac sends
    )
    verdict = match(captures, some_candidates())
    assert verdict.path == "variant"
    (reason,) = [r for r in verdict.reasons if "ionizer" in r]
    # what the code really carries, against the capture's core setting
    assert "differs from its core setting only in: temperature" in reason


def test_records_round_trip(tmp_path):
    from portkit import decode_all, load_protocol, load_records

    captures = daikin_session(tmp_path)
    out = records(captures, tmp_path / "rec", "MYREMOTE")
    assert out == tmp_path / "rec" / "MYREMOTE.json.gz"
    recs = load_records("MYREMOTE", fixtures=tmp_path / "rec")
    assert len(recs) == len(captures)
    assert recs[0]["state"] == captures[0].setting
    proto = load_protocol("pyhvac.protocols.daikin:DAIKIN312")
    decoded = decode_all(recs, proto, ["leader", "main", "main"])
    assert all(not isinstance(m, Exception) for _, m in decoded)


def test_match_cli_json(tmp_path, capsys):
    daikin_session(tmp_path)
    assert main(["match", str(tmp_path / "c.jsonl"), "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["path"] == "supported"


def test_commands_refuse_an_empty_log(tmp_path):  # Review Focus 5
    log = write_log(tmp_path / "c.jsonl", [(BASE, None)])
    assert main(["match", str(log)]) == 1
    assert main(["records", str(log), str(tmp_path / "r"), "X"]) == 1
