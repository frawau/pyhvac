import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.hitachi import (
    HITACHI_AC_LAYOUT,
    HITACHI_AC_MODELS,
    HitachiAcChecksum,
    HitachiAcDevice,
)
from pyhvac.state import HvacState

# The C path never sends swing on: the old vocabulary's "on" has no entry in
# IRGHVAC.trans_swing / trans_hswing, so build_ircode skips the key, swingv and
# swingh stay kOff, and IRac::hitachi never sets the SwingV / SwingH bits
# (HitachiProtocol byte 14 bit 7, byte 15 bit 7).
DEFECTS = (
    Defect("swing_v", "swing", "off", "C glue has no 'on' swing: sends off"),
    Defect("swing_h", "swing", "off", "C glue has no 'on' hswing: sends off"),
)

MODES = ("auto", "heat", "cool", "dry", "fan")


def device():
    return HitachiAcDevice("hitachi", "RAS-35THA6 remote")


def read(state, previous=None):
    dev = device()
    (frame,) = dev.frames(previous, dev.normalise(state), ())
    return HITACHI_AC_LAYOUT.read(frame.data)


def raw(state, name):
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(state), ())
    return HITACHI_AC_LAYOUT.read_raw(frame.data, name)


@pytest.mark.parametrize("record", oracle_params("HITACHI_AC"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("HITACHI_AC"):
        state = state_from_record(dev, record["state"])
        (frame,) = dev.frames(None, state, ())
        values = HITACHI_AC_LAYOUT.read(frame.data)
        assert HITACHI_AC_LAYOUT.build(**values) == bytearray(frame.data)


def test_checksum_matches_a_c_frame():
    # Off, cool, 16 °C, fan auto, as sent by the C library.
    data = bytearray.fromhex("80080c02fd807f8848904004008060600000000000000000800000c5")
    assert HitachiAcChecksum(0, 27, 27, reverse=True).check(data)
    data[27] = 0
    HITACHI_AC_LAYOUT.checksum.apply(data)
    assert data[27] == 0xC5


def test_fields_are_stored_bit_reversed():
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(HvacState(True, "cool", 24.0)), ())
    # kHitachiAcCool = 4, 24 °C << 1 = 48, kHitachiAcFanAuto = 1, all reversed.
    assert (frame.data[10], frame.data[11], frame.data[13]) == (0x20, 0x0C, 0x80)


@pytest.mark.parametrize("mode", MODES)
def test_off_carries_mode_auto_in_every_mode(mode):
    # IRac passes mode "off"; IRHitachiAc::convertMode maps it to auto.
    for t in (16.0, 32.0):
        values = read(HvacState(False, mode, t))
        assert (values["power"], values["mode"]) == (0, "auto")
        sent = raw(HvacState(False, mode, t), "temperature")
        assert sent == int(f"{int(t) << 1:08b}"[::-1], 2)


@pytest.mark.parametrize("mode", MODES)
def test_setpoint_is_sent_in_every_mode_even_fan(mode):
    # setMode(kHitachiAcFan) writes the special temperature 64, but IRac calls
    # setTemp(degrees) afterwards, so the C path always sends the setpoint.
    for t in (16, 23, 32):
        (frame,) = device().frames(None, HvacState(True, mode, float(t)), ())
        assert frame.data[11] == int(f"{t << 1:08b}"[::-1], 2)


def test_setpoint_is_clamped_to_16_32():
    assert raw(HvacState(True, "cool", 10.0), "temperature") == raw(
        HvacState(True, "cool", 16.0), "temperature"
    )
    assert raw(HvacState(True, "cool", 40.0), "temperature") == raw(
        HvacState(True, "cool", 32.0), "temperature"
    )


@pytest.mark.parametrize("mode", MODES)
def test_byte_9_flags_the_minimum_setpoint(mode):
    # IRHitachiAc::setTemp: byte 9 is 0x90 at kHitachiAcMinTemp, else 0x10.
    for power in (False, True):
        for t, byte in ((16.0, 0x90), (17.0, 0x10), (32.0, 0x10)):
            dev = device()
            (frame,) = dev.frames(None, dev.normalise(HvacState(power, mode, t)), ())
            assert frame.data[9] == byte


@pytest.mark.parametrize("fan, code", [("auto", 1), ("1", 2), ("2", 3), ("3", 4)])
def test_fan_levels_follow_convert_fan(fan, code):
    # kLow -> kHitachiAcFanLow, kMedium -> +1, kHigh -> kHitachiAcFanHigh - 1.
    state = HvacState(True, "cool", 24.0, fan=fan)
    assert raw(state, "fan") == int(f"{code:08b}"[::-1], 2)
    assert read(state)["fan"] == fan


@pytest.mark.parametrize(
    "fan, sent", [("auto", "1"), ("1", "1"), ("2", "2"), ("3", "2")]
)
def test_dry_has_only_low_and_medium(fan, sent):
    assert read(HvacState(True, "dry", 24.0, fan=fan))["fan"] == sent


@pytest.mark.parametrize(
    "fan, sent", [("auto", "1"), ("1", "1"), ("2", "2"), ("3", "3")]
)
def test_fan_mode_has_no_auto(fan, sent):
    assert read(HvacState(True, "fan", 24.0, fan=fan))["fan"] == sent


def test_off_keeps_the_requested_fan():
    # An off message is in mode auto, so no dry / fan clamp applies.
    assert read(HvacState(False, "dry", 24.0, fan="3"))["fan"] == "3"
    assert read(HvacState(False, "fan", 24.0))["fan"] == "auto"


def test_swing_on_sets_the_documented_bits():
    state = HvacState(True, "cool", 24.0, swing_v="swing", swing_h="swing")
    assert (read(state)["swing_v"], read(state)["swing_h"]) == ("swing", "swing")
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(state), ())
    assert (frame.data[14], frame.data[15]) == (0xE0, 0xE0)


def test_previous_is_ignored():
    dev = device()
    on = HvacState(True, "cool", 22.0)
    off = HvacState(False, "cool", 22.0)
    assert dev.encode(None, on).signal == dev.encode(off, on).signal
    assert dev.encode(on, on).signal == dev.encode(None, on).signal


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (3300, 1700)
    assert pulses[-2:] == (400, 100000)
    assert len(pulses) == 2 + 2 * 224 + 2


@pytest.mark.parametrize("model", HITACHI_AC_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("hitachi", model), HitachiAcDevice)


@pytest.mark.parametrize("model", HITACHI_AC_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.hitachi import Hitachi

    legacy = LegacyDevice("hitachi", model, Hitachi)
    assert HitachiAcDevice("hitachi", model).capabilities == legacy.capabilities


def test_undeclared_swing_v_deviation_is_reported():
    dev = device()
    record = next(
        r for r in load_oracle("HITACHI_AC") if r["state"].get("swing") == "on"
    )
    with pytest.raises(AssertionError, match="swing_v"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_undeclared_swing_h_deviation_is_reported():
    dev = device()
    record = next(
        r for r in load_oracle("HITACHI_AC") if r["state"].get("hswing") == "on"
    )
    with pytest.raises(AssertionError, match="swing_h"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=DEFECTS[:1])


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("HITACHI_AC")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)
