import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.ir.codec import decode
from pyhvac.plugins.sanyo import (
    SANYO_AC,
    SANYO_AC_LAYOUT,
    SANYO_AC_MODELS,
    SanyoAcDevice,
)
from pyhvac.state import HvacState

# The C path deviates from the documented SanyoProtocol values here:
# - swing "90°"/"60°" (canonical "1"/"2"): IRGHVAC.trans_swing maps them to
#   kHigh and kUpperMiddle; IRSanyoAc::convertSwingV sends kHigh as
#   kSanyoAcSwingVHigh (6) and has no kUpperMiddle case, so it sends
#   kSanyoAcSwingVAuto (0). The port counts the documented positions from
#   the top: Highest (7), High (6);
# - sleep: IRGHVAC.build_ircode's key map has no "sleep", so IRac's sleep
#   stays -1 and IRac::sanyo's setSleep(sleep >= 0) never sets Sleep
#   (byte 6 bit 3).
SWING_HIGHEST = Defect("swing_v", "1", "2", "glue sends kHigh for 90°")
SWING_HIGH = Defect("swing_v", "2", "auto", "convertSwingV: no kUpperMiddle")
SLEEP = Defect("sleep", 1, 0, "legacy glue never passes sleep")
DEFECTS = (SWING_HIGHEST, SWING_HIGH, SLEEP)

# ir_Sanyo_test.cpp, DecodeRealExamples ("On", issue #1211): power on,
# cool, 21 C, fan auto, swing Upper Middle, beep on, sensor wall, sensor
# temperature 11 C.
REAL_EXAMPLE = bytes.fromhex("6a7147002085000032")


# The oracle records name the legacy five angles; the port has six positions
# labelled with the header's names. Each angle is read as the position C
# sent for it (90° and 60° as the documented ones, see the Defects).
ANGLE_AS_POSITION = {
    "90°": "highest",
    "60°": "high",
    "45°": "upper middle",  # C: kSanyoAcSwingVUpperMiddle
    "30°": "low",  # C: kSanyoAcSwingVLow
    "0°": "lowest",  # C: kSanyoAcSwingVLowest
}


def as_positions(record):
    swing = record["state"].get("swing")
    if swing not in ANGLE_AS_POSITION:
        return record
    return {**record, "state": {**record["state"], "swing": ANGLE_AS_POSITION[swing]}}


def device(model="generic"):
    return SanyoAcDevice("sanyo", model)


def frame(state, previous=None):
    dev = device()
    if previous is not None:
        previous = dev.normalise(previous)
    (main,) = dev.frames(previous, dev.normalise(state), ())
    return main.data


def read(state, previous=None):
    return SANYO_AC_LAYOUT.read(frame(state, previous))


@pytest.mark.parametrize("record", oracle_params("SANYO_AC"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, as_positions(record), dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("SANYO_AC"):
        state = state_from_record(dev, as_positions(record)["state"])
        (main,) = dev.frames(None, state, ())
        values = SANYO_AC_LAYOUT.read(main.data)
        assert SANYO_AC_LAYOUT.build(**values) == bytearray(main.data)


def test_every_oracle_frame_has_the_nibble_sum_and_the_fixed_bits():
    for record in load_oracle("SANYO_AC"):
        (main,) = decode(SANYO_AC, record["pulses"], expected=["main"])
        assert SANYO_AC_LAYOUT.checksum.check(main.data)
        assert main.data[0] == 0x6A
        assert main.data[1] >> 5 == 0b011  # byte 1 bits 5-7, as kReset


def test_the_real_capture_differs_only_by_what_the_entity_cannot_express():
    # The remote reported its own sensor temperature (11 C) with beep on and
    # the wall sensor; IRac sends the setpoint as the sensor temperature,
    # beep off and the A/C sensor. Everything else is the capture.
    ours = frame(HvacState(True, "cool", 21.0, fan="auto", swing_v="3"))
    theirs = SANYO_AC_LAYOUT.read(REAL_EXAMPLE)
    assert SANYO_AC_LAYOUT.read(ours) == {
        **theirs,
        "sensor_temp": 21 - 4,
        "beep": 0,
        "sensor": 1,
    }
    patched = bytearray(ours)
    for name in ("sensor_temp", "beep", "sensor"):
        SANYO_AC_LAYOUT.write_raw(
            patched, name, SANYO_AC_LAYOUT.read_raw(REAL_EXAMPLE, name)
        )
    SANYO_AC_LAYOUT.checksum.apply(patched)
    assert bytes(patched) == REAL_EXAMPLE


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat"])
@pytest.mark.parametrize("t", [16.0, 30.0])
def test_off_carries_mode_auto_and_power_off_in_every_mode(mode, t):
    # IRac passes mode "off"; convertMode maps it to kSanyoAcAuto, and
    # setPower(false) writes kSanyoAcPowerOff (0b01).
    values = read(HvacState(False, mode, t))
    assert (values["power"], values["mode"], values["temp"]) == (1, "auto", t - 4)


@pytest.mark.parametrize(
    "mode, raw", [("auto", 4), ("cool", 2), ("dry", 3), ("heat", 1)]
)
def test_mode_codes_and_the_setpoint_in_every_mode(mode, raw):
    for t in (16.0, 23.0, 30.0):
        data = frame(HvacState(True, mode, t))
        values = SANYO_AC_LAYOUT.read(data)
        assert SANYO_AC_LAYOUT.read_raw(data, "mode") == raw
        assert (values["power"], values["temp"]) == (2, t - 4)


def test_setpoint_is_clamped_to_16_30():
    assert read(HvacState(True, "cool", 10.0))["temp"] == 16 - 4
    assert read(HvacState(True, "cool", 40.0))["temp"] == 30 - 4


@pytest.mark.parametrize("t", [16.0, 23.0, 30.0])
def test_sensor_temperature_is_the_setpoint_from_the_ac_sensor(t):
    # IRac::sanyo: no sensor reading -> setSensorTemp(degrees);
    # setSensor(!iFeel) with iFeel off; beep and the off timer stay off.
    values = read(HvacState(True, "heat", t))
    assert values["sensor_temp"] == values["temp"] == t - 4
    assert (values["sensor"], values["beep"]) == (1, 0)
    assert (values["off_timer"], values["off_hour"]) == (0, 0)


@pytest.mark.parametrize("fan, raw", [("auto", 0), ("1", 2), ("2", 3), ("3", 1)])
def test_every_fan_level(fan, raw):
    data = frame(HvacState(True, "cool", 22.0, fan=fan))
    assert SANYO_AC_LAYOUT.read_raw(data, "fan") == raw


@pytest.mark.parametrize(
    "swing_v, raw",
    [("auto", 0), ("1", 7), ("2", 6), ("3", 5), ("4", 4), ("5", 3), ("6", 2)],
)
def test_every_swing_v_value(swing_v, raw):
    # kSanyoAcSwingVAuto, then Highest (7) down to Lowest (2); "4" is
    # kSanyoAcSwingVLowerMiddle, which the legacy entity could not reach.
    data = frame(HvacState(True, "cool", 22.0, swing_v=swing_v))
    assert SANYO_AC_LAYOUT.read_raw(data, "swing_v") == raw


def test_capabilities_are_the_documented_values():
    caps = device().capabilities
    # kSanyoAcTempMin / kSanyoAcTempMax, whole degrees.
    assert (caps.temperature.min, caps.temperature.max) == (16.0, 30.0)
    assert caps.modes == ("auto", "cool", "dry", "heat")  # no fan-only code
    assert caps.fan.values == ("auto", "1", "2", "3")
    assert caps.swing_v.values == ("auto", "1", "2", "3", "4", "5", "6")
    assert caps.swing_v.label("4") == "lower middle"
    assert caps.swing_h is None
    assert set(caps.features) == {"sleep"}


@pytest.mark.parametrize("angle", ["45°", "30°", "0°"])
def test_legacy_angles_are_read_as_what_c_sent(angle):
    dev = device()
    record = next(
        r for r in load_oracle("SANYO_AC") if r["state"].get("swing") == angle
    )
    with pytest.raises(ValueError, match=angle):
        state_from_record(dev, record["state"])
    assert_matches_oracle(dev, as_positions(record), dev.LAYOUTS, DEFECTS)


@pytest.mark.parametrize("power", [True, False])
def test_sleep_bit(power):
    assert read(HvacState(power, "cool", 22.0))["sleep"] == 0
    values = read(HvacState(power, "cool", 22.0, features={"sleep": True}))
    assert values["sleep"] == 1


def test_previous_is_ignored():
    dev = device()
    on = HvacState(True, "cool", 22.0, swing_v="1", features={"sleep": True})
    off = HvacState(False, "heat", 30.0)
    assert dev.encode(off, on).signal == dev.encode(None, on).signal
    assert dev.encode(on, on).signal == dev.encode(None, on).signal
    assert dev.encode(on, off).signal == dev.encode(None, off).signal


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (8500, 4200)
    assert pulses[-2:] == (500, 100000)
    assert len(pulses) == 2 + 2 * 72 + 2


@pytest.mark.parametrize("model", SANYO_AC_MODELS)
def test_registry_serves_the_port(model):
    dev = registry.get_device("sanyo", model)
    assert isinstance(dev, SanyoAcDevice)


@pytest.mark.parametrize(
    "select, defect, field",
    [
        (lambda s: s.get("swing") == "90°", SWING_HIGHEST, "swing_v"),
        (lambda s: s.get("swing") == "60°", SWING_HIGH, "swing_v"),
        (lambda s: s.get("sleep") == "on", SLEEP, "sleep"),
    ],
)
def test_undeclared_deviation_is_reported(select, defect, field):
    dev = device()
    record = next(r for r in load_oracle("SANYO_AC") if select(r["state"]))
    others = tuple(d for d in DEFECTS if d != defect)
    with pytest.raises(AssertionError, match=field):
        assert_matches_oracle(dev, as_positions(record), dev.LAYOUTS, defects=others)
