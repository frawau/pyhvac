import gzip
import json
from pathlib import Path

import pytest

from port_oracle import assert_matches_golden
from pyhvac import registry
from pyhvac.choices import FAN_5, ON_OFF, SWING
from pyhvac.ir.codec import decode
from pyhvac.plugins.daikin import (
    DAIKIN_NATIVE,
    DAIKIN_NATIVE_LAYOUT,
    Daikinth,
    DaikinNativeDevice,
    Smash2,
)
from pyhvac.state import HvacState

GOLDEN = Path(__file__).parent / "fixtures" / "golden" / "daikin.json.gz"
LEGACY = {"Daikinth": Daikinth, "Smash2": Smash2}
MODEL = {"Daikinth": "generic", "Smash2": "smash 2"}
FAN = {v: k for k, v in FAN_5.labels.items()}  # "lowest" -> "1", ...


def from_old(cls, old):
    """The HvacState an old Daikinth/Smash2 state stands for.

    An old object switched off applies only the mode (set_mode("off")
    clears everything else it was given) and sends its stored status with
    the power bit cleared: for a fresh object that is cool, 25 °C, fan auto,
    swing and powerful off (Smash2's stored mode "off" also encodes cool).
    """
    status = {"fan": "auto", "swing": "off", "powerful": "off", **cls().status}
    if old["mode"] == "off":
        old = {**status, "mode": "cool"}
        power = False
    else:
        old = {**status, **old}
        power = True
    return HvacState(
        power=power,
        mode=old["mode"],
        temperature=old["temperature"],
        fan=FAN[old["fan"]],
        swing_v="swing" if old["swing"] == "on" else "off",
        features={"powerful": old["powerful"] == "on"},
    )


def _records():
    records = json.loads(gzip.decompress(GOLDEN.read_bytes()))
    for n, rec in enumerate(records):
        if rec["class"] not in LEGACY:
            continue
        marks = []
        if rec["state"].get("powerful") == "on":
            marks = [
                pytest.mark.skip(
                    reason="old code_powerful tested the string 'on' against True, "
                    "so powerful was never sent; fixed on purpose (mask[13] = 0x80)"
                )
            ]
        yield pytest.param(rec, id=f"{rec['class']}-{n}", marks=marks)


RECORDS = list(_records())


def test_every_class_has_records():
    assert {r.values[0]["class"] for r in RECORDS} == set(LEGACY)


@pytest.mark.parametrize("record", RECORDS)
def test_reproduces_golden(record):
    cls = record["class"]
    device = DaikinNativeDevice("daikin", MODEL[cls])
    assert_matches_golden(device, record, from_old(LEGACY[cls], record["state"]))


def body(**kw):
    base = dict(power=True, mode="cool", temperature=25.0)
    base.update(kw)
    cmd = DaikinNativeDevice("daikin", "smash 2").encode(None, HvacState(**base))
    (frame,) = decode(DAIKIN_NATIVE, cmd.signal.pulses, expected=["main"])
    return frame.data


def test_layout_round_trip():
    data = DAIKIN_NATIVE_LAYOUT.build(
        mode="heat",
        power=True,
        temperature=0x44,
        fan="3",
        swing_v="swing",
        powerful=True,
        off=False,
    )
    assert DAIKIN_NATIVE_LAYOUT.checksum.check(data)
    assert DAIKIN_NATIVE_LAYOUT.read(data) == {
        "mode": "heat",
        "power": 1,
        "temperature": 0x44,
        "fan": "3",
        "swing_v": "swing",
        "powerful": 1,
        "off": 0,
    }


def test_legacy_frame_bytes():
    # Daikinth cool 25 (golden): the checksum is the reflected byte sum.
    assert body().hex() == "885be400008c4c0005000000000000a3001047"


def test_setpoint_is_twice_the_temperature_bit_reversed():
    assert body(temperature=18.0)[6] == 0x24  # bit_reverse(36)
    assert body(temperature=31.0)[6] == 0x7C  # bit_reverse(62)


def test_fan_mode_sends_25():
    assert body(mode="fan", temperature=18.0)[6] == body(temperature=25.0)[6]


def test_fan_mode_keeps_the_setpoint_in_the_state():
    cmd = DaikinNativeDevice("daikin", "generic").encode(
        None, HvacState(True, "fan", 20.0)
    )
    assert cmd.state.temperature == 20.0


def test_dry_replaces_the_setpoint():
    assert body(mode="dry", temperature=18.0)[6] == 0x03


def test_off_clears_power_and_keeps_mode_and_settings():
    data = body(power=False, mode="dry", temperature=20.0, fan="4")
    assert data[5] == 0x04  # dry, no power bit
    assert data[6] == 0x14  # bit_reverse(40): the setpoint, not dry's 0x03
    assert data[8] & 0x0F == 0x06  # high
    assert data[16] == 0x02


def test_off_from_auto_keeps_auto():
    # The old `y or x` merge turned auto's 0x00 back into FBODY's cool 0x0C.
    assert body(power=False, mode="auto")[5] == 0x00


@pytest.mark.parametrize(
    "mode, byte", [("auto", 0x80), ("heat", 0x82), ("dry", 0x84), ("fan", 0x86)]
)
def test_mode_bytes(mode, byte):
    assert body(mode=mode)[5] == byte


@pytest.mark.parametrize(
    "fan, nibble",
    [("auto", 0x5), ("1", 0xC), ("2", 0x2), ("3", 0xA), ("4", 0x6), ("5", 0xE)],
)
def test_fan_codes(fan, nibble):
    assert body(fan=fan)[8] == nibble


def test_swing_sets_the_high_nibble():
    assert body(swing_v="swing")[8] == 0xF5


def test_powerful_bit():
    assert body(features={"powerful": True})[13] == 0x80
    assert body()[13] == 0x00


def test_previous_is_ignored():
    dev = DaikinNativeDevice("daikin", "smash 2")
    target = HvacState(True, "cool", 24.0, fan="2")
    assert dev.encode(None, target) == dev.encode(
        HvacState(False, "heat", 30.0, swing_v="swing"), target
    )


def test_capabilities():
    caps = DaikinNativeDevice.capabilities
    assert caps.modes == ("cool", "fan", "dry", "heat", "auto")
    assert (caps.temperature.min, caps.temperature.max) == (18.0, 31.0)
    assert caps.temperature.decimals == (0,)
    assert caps.fan == FAN_5
    assert caps.swing_v == SWING
    assert caps.swing_h is None
    assert dict(caps.features) == {"powerful": ON_OFF}
    assert not caps.actions


def test_every_offered_value_encodes_distinctly():
    dev = DaikinNativeDevice("daikin", "generic")
    caps = dev.capabilities
    base = HvacState(True, "cool", 25.0)
    for field, choice in (("fan", caps.fan), ("swing_v", caps.swing_v)):
        frames = {
            dev.encode(None, HvacState(**{**base.to_dict(), field: v})).signal
            for v in choice.values
        }
        assert len(frames) == len(choice.values)
    modes = {dev.encode(None, HvacState(True, m, 25.0)).signal for m in caps.modes}
    assert len(modes) == len(caps.modes)
    temps = {
        dev.encode(None, HvacState(True, "cool", float(t))).signal
        for t in range(18, 32)
    }
    assert len(temps) == 14
    on = dev.encode(None, HvacState(True, "cool", 25.0, features={"powerful": True}))
    assert on.signal != dev.encode(None, base).signal


def test_setpoint_clamps():
    dev = DaikinNativeDevice("daikin", "generic")
    assert dev.normalise(HvacState(True, "cool", 16.0)).temperature == 18.0
    assert dev.normalise(HvacState(True, "cool", 35.0)).temperature == 31.0


@pytest.mark.parametrize("model", ["generic", "smash 2"])
def test_registered(model):
    dev = registry.get_device("daikin", model)
    assert isinstance(dev, DaikinNativeDevice)
    assert (dev.brand, dev.model) == ("daikin", model)
