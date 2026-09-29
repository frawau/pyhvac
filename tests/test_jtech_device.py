import gzip
import json
from pathlib import Path

import pytest

from pyhvac.plugins.sharp import JTechDevice
from pyhvac.state import HvacState

GOLDEN = Path(__file__).parent / "fixtures" / "golden" / "sharp.json.gz"

FAN = {"auto": "auto", "lowest": "1", "low": "2", "medium": "3", "highest": "4"}
SWING_V = {"auto": "auto", "swing": "swing", "ceiling": "1", "90°": "2"}
SWING_V.update({"60°": "3", "45°": "4", "30°": "5"})
SWING_H = {"left": "1", "middle": "2", "right": "3", "swing": "swing"}


# The status of a fresh 0.1.x JTech object (what the golden records were
# built from).
FRESH_JTECH = {
    "mode": "off",
    "temperature": 25,
    "fan": "auto",
    "swing": "auto",
    "hswing": "middle",
    "target": "off",
    "purifier": "off",
    "economy": "off",
    "powerful": "off",
}


def from_old(old):
    old = {**FRESH_JTECH, **old}
    return HvacState(
        power=old["mode"] != "off",
        mode="cool" if old["mode"] == "off" else old["mode"],
        temperature=old["temperature"],
        fan=FAN[old["fan"]],
        swing_v=SWING_V[old["swing"]],
        swing_h=SWING_H[old["hswing"]],
        features={
            "purifier": old["purifier"] == "on",
            "powerful": old["powerful"] == "on",
            "economy": old["economy"] == "on",
            "spot": old["target"],
        },
    )


# The golden records were built from a fresh JTech object: that is "previous".
PREVIOUS = from_old({})


def _records():
    records = json.loads(gzip.decompress(GOLDEN.read_bytes()))
    for n, rec in enumerate(records):
        if rec["class"] != "JTech":
            continue
        state = rec["state"]
        if state["mode"] == "off":
            reason = "old 'off from off' sent 0x31: the restart bug, fixed on purpose"
        elif state.get("target", "off") != "off":
            reason = "old code never encoded spot from a fresh object, fixed on purpose"
        else:
            reason = None
        marks = [pytest.mark.skip(reason=reason)] if reason else []
        yield pytest.param(rec, id=f"jtech-{n}", marks=marks)


@pytest.mark.parametrize("record", list(_records()))
def test_reproduces_golden(record):
    cmd = JTechDevice("sharp", "j-tech").encode(PREVIOUS, from_old(record["state"]))
    assert list(cmd.signal.pulses) == record["pulses"]


ON = HvacState(True, "cool", 24.0)
OFF = HvacState(False, "cool", 24.0)


def power_byte(previous, target):
    dev = JTechDevice("sharp", "j-tech")
    prev = None if previous is None else dev.normalise(previous)
    return dev.frames(prev, dev.normalise(target), ())[0].data[5]


@pytest.mark.parametrize(
    "previous, target, expected",
    [
        (OFF, ON, 0x11),
        (ON, ON, 0x31),
        (ON, OFF, 0x21),
        (OFF, OFF, 0x21),
        (None, ON, 0x11),
        (None, OFF, 0x21),  # the restart case: off must work with no history
    ],
)
def test_power_transitions(previous, target, expected):
    assert power_byte(previous, target) == expected


def test_off_frame_keeps_the_mode():
    dev = JTechDevice("sharp", "j-tech")
    data = dev.frames(None, dev.normalise(HvacState(False, "dry", 24.0)), ())[0].data
    assert data[6] & 0x0F == 0x03


def test_unknown_previous_sends_the_special_frames():
    dev = JTechDevice("sharp", "j-tech")
    frames = dev.frames(None, dev.normalise(ON), ())
    assert [f.data[5] for f in frames] == [0x11, 0x71, 0x71]


def test_special_frame_only_when_changed():
    dev = JTechDevice("sharp", "j-tech")
    on_powerful = dev.normalise(
        HvacState(True, "cool", 24.0, features={"powerful": True})
    )
    frames = dev.frames(dev.normalise(ON), on_powerful, ())
    assert [f.data[5] for f in frames] == [0x31, 0x61]
    assert frames[1].data[10] & 0x01
    assert len(dev.frames(on_powerful, on_powerful, ())) == 1


def test_fan_forced_auto_in_dry():
    dev = JTechDevice("sharp", "j-tech")
    assert dev.normalise(HvacState(True, "dry", 24.0, fan="3")).fan == "auto"


def test_half_degree_setpoint():
    dev = JTechDevice("sharp", "j-tech")
    data = dev.frames(None, dev.normalise(HvacState(True, "cool", 24.5)), ())[0].data
    assert data[4] == 0x70 + 24 - 15
