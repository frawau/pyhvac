"""tools/capturekit.py: hvactest captures to checks, a match and portkit records."""

import base64

import pytest

from capturekit import Capture, check, load, main, parse_note
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
