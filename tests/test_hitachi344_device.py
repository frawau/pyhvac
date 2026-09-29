import pytest

from oracle import load_oracle
from port_oracle import (
    Defect,
    assert_matches_oracle,
    assert_sequence_matches_c,
    oracle_params,
    sequence_params,
    state_from_record,
)
from pyhvac.ir.codec import decode
from pyhvac.protocols.hitachi import (
    HITACHI344,
    HITACHI344_LAYOUT,
    HITACHI344_MODELS,
    Hitachi344Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Hitachi344 values here:
# - the old glue (IRGHVAC.trans_swing) has no "on" entry, so IRac keeps
#   swingv kOff and IRac::hitachi344's setSwingVToggle(false) leaves the
#   button at kHitachiAc344ButtonPowerMode (0x13) instead of
#   kHitachiAc344ButtonSwingV (0x81).
DEFECTS = (Defect("button", "swing_v", "power_mode", "C path never sends swing: 0x13"),)


def device():
    return Hitachi344Device("hitachi", "RAS-22NK")


def with_hswing(record):
    # A record without "hswing" leaves IRac's swingh at kOff, which
    # IRHitachiAc344::convertSwingH maps to its default, Middle: canonical "3"
    # (the oracle records match only so). The port has no "off" swing_h (the
    # legacy entity has none), so the record is read as "middle".
    if "hswing" in record["state"]:
        return record
    return {**record, "state": {**record["state"], "hswing": "middle"}}


def read(state, previous=None):
    dev = device()
    if previous is not None:
        previous = dev.normalise(previous)
    (main,) = dev.frames(previous, dev.normalise(state), ())
    return HITACHI344_LAYOUT.read(main.data)


@pytest.mark.parametrize("record", oracle_params("HITACHI_AC344"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, with_hswing(record), dev.LAYOUTS, DEFECTS)


@pytest.mark.parametrize("record, states", sequence_params("HITACHI_AC344"))
def test_sequence_matches_a_persistent_c_object(record, states):
    # The swing button depends on the message before, but the 0.1.7 glue
    # never passes swing on (DEFECTS), so this cannot catch a wrong swing
    # toggle: it checks that no other field depends on the message before.
    dev = device()
    assert_sequence_matches_c(
        dev, record, states, dev.LAYOUTS, DEFECTS, adapt=with_hswing
    )


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("HITACHI_AC344"):
        state = state_from_record(dev, with_hswing(record)["state"])
        (main,) = dev.frames(None, state, ())
        values = HITACHI344_LAYOUT.read(main.data)
        assert HITACHI344_LAYOUT.build(**values) == bytearray(main.data)


def test_every_oracle_frame_has_inverted_pairs_from_byte_3():
    # portkit checksum only tries InvertedPairs(0, n) on even lengths.
    for record in load_oracle("HITACHI_AC344"):
        (frame,) = decode(HITACHI344, record["pulses"], expected=["main"])
        assert HITACHI344_LAYOUT.checksum.check(frame.data)


def test_no_field_sits_in_a_complement_byte():
    complements = HITACHI344_LAYOUT.checksum.positions()
    for name, f in HITACHI344_LAYOUT.fields.items():
        assert not {b // 8 for b in f.bits} & complements, name


@pytest.mark.parametrize("mode", ["cool", "fan", "dry", "heat"])
@pytest.mark.parametrize("t", [16.0, 32.0])
def test_off_carries_mode_cool_in_every_mode(mode, t):
    # IRac passes mode "off"; IRHitachiAc424::convertMode maps it to cool.
    values = read(HvacState(False, mode, t))
    assert (values["mode"], values["temperature"], values["power"]) == (
        "cool",
        int(t),
        0,
    )


def test_fan_mode_keeps_the_setpoint():
    # IRac calls setTemp(degrees) after setMode, which had set
    # kHitachiAc424FanTemp (27).
    assert read(HvacState(True, "fan", 18.0))["temperature"] == 18


@pytest.mark.parametrize(
    "fan, code, byte9, byte29",
    [
        ("auto", 5, 0x92, 0x00),
        ("1", 1, 0x98, 0x00),
        ("2", 2, 0x92, 0x00),
        ("3", 3, 0x92, 0x00),
        ("4", 4, 0x92, 0x00),
        ("5", 6, 0xA9, 0x30),
    ],
)
def test_every_fan_level_uses_its_documented_value(fan, code, byte9, byte29):
    dev = device()
    (main,) = dev.frames(
        None, dev.normalise(HvacState(True, "cool", 22.0, fan=fan)), ()
    )
    raw = {k: HITACHI344_LAYOUT.read_raw(main.data, k) for k in ("fan", "fan_byte9")}
    assert (raw["fan"], raw["fan_byte9"], main.data[29]) == (code, byte9, byte29)


@pytest.mark.parametrize(
    "fan, code", [("auto", 5), ("1", 1), ("2", 2), ("3", 2), ("4", 2), ("5", 2)]
)
def test_dry_allows_auto_or_up_to_low(fan, code):
    dev = device()
    (main,) = dev.frames(None, dev.normalise(HvacState(True, "dry", 22.0, fan=fan)), ())
    assert HITACHI344_LAYOUT.read_raw(main.data, "fan") == code


def test_fan_mode_has_no_auto_fan():
    dev = device()
    (main,) = dev.frames(None, dev.normalise(HvacState(True, "fan", 22.0)), ())
    assert HITACHI344_LAYOUT.read_raw(main.data, "fan") == 1
    assert main.data[9] == 0x98


@pytest.mark.parametrize(
    "swing_h, raw", [("auto", 0), ("1", 5), ("2", 4), ("3", 3), ("4", 2), ("5", 1)]
)
def test_every_swing_h_position(swing_h, raw):
    dev = device()
    (main,) = dev.frames(
        None, dev.normalise(HvacState(True, "cool", 22.0, swing_h=swing_h)), ()
    )
    assert HITACHI344_LAYOUT.read_raw(main.data, "swing_h") == raw


def test_swing_v_without_previous_presses_the_swing_button():
    # A fresh IRac (no previous state for the protocol) passes swingv as is.
    assert read(HvacState(True, "cool", 22.0, swing_v="swing"))["button"] == "swing_v"
    assert read(HvacState(True, "cool", 22.0))["button"] == "power_mode"


@pytest.mark.parametrize(
    "before, after, button",
    [
        ("off", "off", "power_mode"),
        ("off", "swing", "swing_v"),
        ("swing", "off", "swing_v"),
        ("swing", "swing", "power_mode"),
    ],
)
def test_swing_v_with_previous_toggles_on_change(before, after, button):
    # As IRac::handleToggles does for HITACHI_AC344 with a previous state.
    previous = HvacState(True, "cool", 22.0, swing_v=before)
    target = HvacState(True, "cool", 22.0, swing_v=after)
    assert read(target, previous)["button"] == button


def test_swing_v_state_bit_is_never_set():
    # IRac::hitachi344 only calls setSwingVToggle, never setSwingV.
    assert read(HvacState(True, "cool", 22.0, swing_v="swing"))["swing_v"] == 0


def test_encode_passes_previous_to_the_toggle():
    dev = device()
    on = HvacState(True, "cool", 22.0, swing_v="swing")
    assert dev.encode(None, on).signal != dev.encode(on, on).signal


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (3300, 1700)
    assert pulses[-2:] == (400, 100000)
    assert len(pulses) == 2 + 2 * 344 + 2


@pytest.mark.parametrize("model", HITACHI344_MODELS)
def test_capabilities_are_the_documented_controls(model):
    # Unchanged from the legacy entity: Hitachi424's controls plus every
    # kHitachiAc344SwingH* position (Auto, LeftMax..RightMax).
    caps = Hitachi344Device("hitachi", model).capabilities
    assert caps.modes == ("cool", "fan", "dry", "heat")
    assert (caps.temperature.min, caps.temperature.max) == (16.0, 32.0)
    assert caps.fan.values == ("auto", "1", "2", "3", "4", "5")
    assert caps.swing_v.values == ("off", "swing")
    assert caps.swing_h.values == ("auto", "1", "2", "3", "4", "5")
    assert dict(caps.features) == {}


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(
        r for r in load_oracle("HITACHI_AC344") if r["state"].get("swing") == "on"
    )
    with pytest.raises(AssertionError, match="button"):
        assert_matches_oracle(dev, with_hswing(record), dev.LAYOUTS, defects=())


def test_missing_hswing_is_not_silently_accepted():
    dev = device()
    record = next(r for r in load_oracle("HITACHI_AC344") if "hswing" not in r["state"])
    with pytest.raises(AssertionError, match="swing_h"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


# No real capture in ir_Hitachi_test.cpp needs it, but decodeHitachiAC
# (kHitachiAc344Bits) matches with _tolerance + 5 (30 %) and kMarkExcess.
def test_decode_tolerance_is_the_c_decoders():
    assert (HITACHI344.tolerance, HITACHI344.mark_excess) == (0.30, 50)
