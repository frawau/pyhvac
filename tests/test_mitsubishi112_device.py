import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac.protocols.mitsubishi_electric import (
    MITSUBISHI112,
    MITSUBISHI112_LAYOUT,
    MITSUBISHI112_MODELS,
    Mitsubishi112Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented values here:
# - the old swing labels go through IRGHVAC.trans_swing ("90°" -> kHigh,
#   "60°" -> kUpperMiddle) into IRMitsubishi112::convertSwingV, which maps
#   kHigh to kMitsubishi112SwingVHigh (so kMitsubishi112SwingVHighest is never
#   sent) and has no kUpperMiddle case (it falls back to SwingVAuto);
# - convertFan maps lowest (kMin) to kMitsubishi112FanMin, but
#   IRac::mitsubishi112 then calls setQuiet(false), and since FanMin equals
#   kMitsubishi112FanQuiet, setQuiet turns it into kMitsubishi112FanLow.
DEFECTS = (
    Defect("swing_v", "1", "2", "C sends SwingVHigh for highest"),
    Defect("swing_v", "2", "auto", "C has no upper-middle case: sends auto"),
    Defect("fan", "1", "2", "setQuiet(false) turns FanMin into FanLow"),
)

# ir_Mitsubishi_test.cpp (KPOA remote capture): power on, cool, 23 °C,
# fan 2 (quiet), swing V and H auto.
REAL_CAPTURE = bytes.fromhex("23cb2601002403083a00000030ae")


def device(model="KPOA remote"):
    return Mitsubishi112Device("mitsubishi_electric", model)


def read(state):
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(state), ())
    return MITSUBISHI112_LAYOUT.read(frame.data)


def _with_c_defaults(record):
    # A record without "fan" relied on IRac's default (kAuto), which
    # IRMitsubishi112::convertFan sends as kMitsubishi112FanMed ("medium").
    # Missing swing/hswing (kOff) fall back to auto, as the port's defaults.
    # Swing "off" (no longer offered: the header has no off code) is what C
    # sent for it, auto.
    state = {"fan": "medium", **record["state"]}
    if state.get("swing") == "off":
        state["swing"] = "auto"
    return {**record, "state": state}


@pytest.mark.parametrize("record", oracle_params("MITSUBISHI112"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, _with_c_defaults(record), dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("MITSUBISHI112"):
        state = state_from_record(dev, _with_c_defaults(record)["state"])
        (frame,) = dev.frames(None, state, ())
        values = MITSUBISHI112_LAYOUT.read(frame.data)
        assert MITSUBISHI112_LAYOUT.build(**values) == bytearray(frame.data)
        assert MITSUBISHI112_LAYOUT.checksum.check(frame.data)


@pytest.mark.parametrize(
    "state",
    [
        HvacState(True, "cool", 23.0, fan="1", swing_v="auto", swing_h="auto"),
        HvacState(
            True,
            "cool",
            23.0,
            fan="4",
            swing_v="auto",
            swing_h="auto",
            features={"quiet": True},
        ),
    ],
)
def test_the_kpoa_capture_is_reproduced(state):
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(state), ())
    assert frame.data == REAL_CAPTURE


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat"])
def test_off_carries_mode_auto_and_the_setpoint(mode):
    # IRac passes mode "off"; convertMode maps it to auto.
    for t in (16.0, 25.0, 31.0):
        values = read(HvacState(False, mode, t))
        assert (values["power"], values["mode"], values["temperature"]) == (
            0,
            "auto",
            31 - int(t),
        )


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat"])
def test_setpoint_is_31_minus_whole_degrees_clamped_to_16_31(mode):
    # setTemp clamps to kMitsubishi112MinTemp/MaxTemp (16-31).
    assert read(HvacState(True, mode, 10.0))["temperature"] == 15
    assert read(HvacState(True, mode, 21.0))["temperature"] == 10
    assert read(HvacState(True, mode, 26.0))["temperature"] == 5
    assert read(HvacState(True, mode, 31.0))["temperature"] == 0
    assert read(HvacState(True, mode, 35.0))["temperature"] == 0


def test_capabilities_are_the_documented_values():
    caps = device().capabilities
    # kMitsubishi112MinTemp / kMitsubishi112MaxTemp, whole degrees.
    assert (caps.temperature.min, caps.temperature.max) == (16.0, 31.0)
    assert caps.temperature.decimals == (0,)
    assert caps.modes == ("auto", "cool", "dry", "heat")  # no fan-only mode
    assert caps.fan.values == ("1", "2", "3", "4")  # no auto code
    # kMitsubishi112SwingVAuto and five positions: no off code.
    assert caps.swing_v.values == ("auto", "1", "2", "3", "4", "5")
    assert caps.swing_h.values == ("auto", "1", "2", "3", "4", "5", "6")
    assert set(caps.features) == {"quiet"}


def test_swing_v_off_is_not_offered():
    # Removed: C sent kMitsubishi112SwingVAuto for it.
    assert "off" not in device().capabilities.swing_v.values
    assert device().normalise(HvacState(True, "cool", 22.0)).swing_v == "auto"


def test_mode_codes():
    for mode, raw in (("auto", 7), ("cool", 3), ("dry", 2), ("heat", 1)):
        values = read(HvacState(True, mode, 20.0))
        assert values["mode"] == mode
        assert MITSUBISHI112_LAYOUT.fields["mode"].values[mode] == raw


@pytest.mark.parametrize("fan, raw", [("1", 2), ("2", 3), ("3", 5), ("4", 0)])
def test_every_fan_level_uses_the_documented_code(fan, raw):
    # "1" (lowest) sends kMitsubishi112FanMin although the C path sends
    # FanLow (the declared fan defect).
    dev = device()
    (frame,) = dev.frames(
        None, dev.normalise(HvacState(True, "cool", 22.0, fan=fan)), ()
    )
    assert MITSUBISHI112_LAYOUT.read_raw(frame.data, "fan") == raw


@pytest.mark.parametrize("fan", ["1", "2", "3", "4"])
def test_quiet_overrides_the_fan(fan):
    # setQuiet(true) runs after setFan and stores kMitsubishi112FanQuiet.
    state = HvacState(True, "cool", 22.0, fan=fan, features={"quiet": True})
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(state), ())
    assert MITSUBISHI112_LAYOUT.read_raw(frame.data, "fan") == 0b010


@pytest.mark.parametrize(
    "swing, raw",
    [("auto", 7), ("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 5)],
)
def test_every_vertical_swing_value(swing, raw):
    # kMitsubishi112SwingVAuto, then the positions counting down from
    # kMitsubishi112SwingVHighest.
    dev = device()
    state = dev.normalise(HvacState(True, "cool", 22.0, fan="3", swing_v=swing))
    (frame,) = dev.frames(None, state, ())
    assert MITSUBISHI112_LAYOUT.read_raw(frame.data, "swing_v") == raw


@pytest.mark.parametrize(
    "swing, raw",
    [
        ("auto", 0b1100),
        ("1", 0b0001),
        ("2", 0b0010),
        ("3", 0b0011),
        ("4", 0b0100),
        ("5", 0b0101),
        ("6", 0b1000),
    ],
)
def test_every_horizontal_swing_value(swing, raw):
    dev = device()
    state = dev.normalise(HvacState(True, "cool", 22.0, fan="3", swing_h=swing))
    (frame,) = dev.frames(None, state, ())
    assert MITSUBISHI112_LAYOUT.read_raw(frame.data, "swing_h") == raw


def test_previous_is_ignored():
    dev = device()
    on = HvacState(True, "cool", 22.0, fan="3")
    off = HvacState(False, "cool", 22.0, fan="3")
    assert dev.encode(off, on).signal == dev.encode(None, on).signal
    assert dev.encode(on, on).signal == dev.encode(None, on).signal
    assert dev.encode(on, off).signal == dev.encode(None, off).signal


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (3450, 1696)
    assert pulses[-2:] == (450, 100000)
    assert len(pulses) == 2 + 2 * 112 + 2


@pytest.mark.parametrize(
    "old, field",
    [
        ({"swing": "90°"}, "swing_v"),
        ({"swing": "60°"}, "swing_v"),
        ({"fan": "lowest"}, "fan"),
    ],
)
def test_undeclared_deviation_is_reported(old, field):
    dev = device()
    record = next(
        r
        for r in load_oracle("MITSUBISHI112")
        if all(r["state"].get(k) == v for k, v in old.items())
        and r["state"]["mode"] != "off"
    )
    with pytest.raises(AssertionError, match=field):
        assert_matches_oracle(dev, _with_c_defaults(record), dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("MITSUBISHI112")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, _with_c_defaults(record), (), DEFECTS)


# No real capture in ir_Mitsubishi_test.cpp needs it, but
# decodeMitsubishi112 matches with _tolerance + kTcl112AcTolerance (30 %)
# and no mark excess.
def test_decode_tolerance_is_the_c_decoders():
    assert (MITSUBISHI112.tolerance, MITSUBISHI112.mark_excess) == (0.30, 0)
