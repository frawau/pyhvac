import gzip
import json
from pathlib import Path

import pytest

from pyhvac.ir.codec import decode
from pyhvac.protocols.airspool import AIRSPOOL, AirspoolDevice
from pyhvac.state import HvacState

GOLDEN = Path(__file__).parent / "fixtures" / "golden" / "airspool.json.gz"
# The status of a fresh 0.1.x Airspool object (what the golden records were
# built from).
FRESH_AIRSPOOL = {
    "mode": "cool",
    "temperature": 24,
    "fan": "auto",
    "sleep": "off",
    "swing": "off",
    "hswing": "off",
    "se_step": "off",
    "display": "on",
    "turbo": "off",
    "power": "on",
    "se": "off",
}


def from_old(old):
    """The HvacState and actions matching an old Airspool status dict."""
    old = {**FRESH_AIRSPOOL, **old}
    state = HvacState(
        power=old["power"] == "on",
        mode=old["mode"],
        temperature=old["temperature"],
        fan="auto" if old["fan"] == "auto" else old["fan"][len("fan") :],
        swing_v="swing" if old["swing"] == "on" else "off",
        swing_h="swing" if old["hswing"] == "on" else "off",
        features={
            "sleep": old["sleep"] == "on",
            "powerful": old["turbo"] == "on",
            "light": old["display"] == "on",
            "power_limit": old["se"] == "on",
        },
    )
    return state, ("se_step",) if old["se_step"] == "on" else ()


RECORDS = json.loads(gzip.decompress(GOLDEN.read_bytes()))


@pytest.mark.parametrize("record", RECORDS, ids=range(len(RECORDS)))
def test_reproduces_golden(record):
    state, actions = from_old(record["state"])
    cmd = AirspoolDevice("airspool", "generic").encode(None, state, actions)
    assert list(cmd.signal.pulses) == record["pulses"]


def frame(**kw):
    base = dict(power=True, mode="cool", temperature=24.0)
    base.update(kw)
    cmd = AirspoolDevice("airspool", "generic").encode(None, HvacState(**base))
    return decode(AIRSPOOL, cmd.signal.pulses, expected=["main"])[0].data


def test_reference_capture_cool_24():
    # 24 degC -> 75 degF; see tests/test_airspool.py REFERENCES
    assert frame().hex(" ").upper() == "23 CB 26 01 75 04 23 00 00 00 00 E0 00 91"


def test_light_defaults_on():
    assert frame()[6] & 0x20


def test_se_step_is_in_the_frame_not_in_the_state():
    dev = AirspoolDevice("airspool", "generic")
    target = HvacState(True, "cool", 26.0)
    cmd = dev.encode(None, target, ["se_step"])
    data = decode(AIRSPOOL, cmd.signal.pulses, expected=["main"])[0].data
    assert data[6] & 0x40
    assert cmd.state == dev.normalise(target)


def test_previous_is_ignored():
    dev = AirspoolDevice("airspool", "generic")
    target = HvacState(True, "cool", 24.0)
    assert dev.encode(None, target) == dev.encode(
        HvacState(False, "heat", 30.0), target
    )


def test_temperature_snaps_to_half_degrees():
    cmd = AirspoolDevice("airspool", "generic").encode(
        None, HvacState(True, "cool", 24.3)
    )
    assert cmd.state.temperature == 24.5
