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
from pyhvac import registry
from pyhvac.plugins.daikin import (
    DAIKIN128,
    DAIKIN128_FIRST,
    DAIKIN128_MODELS,
    DAIKIN128_SECOND,
    Daikin128Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Daikin128 values here:
# IRDaikin128::convertMode returns kDaikinDry (0b010, the DAIKIN protocol's
# dry), which is kDaikin128Cool; the header documents kDaikin128Dry = 0b0001.
# pyhvac's IRGHVAC.trans_swing has no "on" key, so IRac never receives a
# vertical swing and SwingV (documented 1-bit field) is always 0.
# IRDaikin128::convertFan maps kMin to quiet (with DAIKIN's kDaikinFanQuiet,
# 0b1011, not kDaikin128FanQuiet) and kMax to kDaikin128FanPowerful, then
# IRac::daikin128 cancels both with setQuiet(false)/setPowerful(false), as
# the old model has no quiet/powerful feature: lowest and highest send auto.
MODE_DRY = Defect("mode", "dry", "cool", "convertMode sends kDaikinDry (= cool)")
SWING = Defect("swing_v", "swing", "off", "trans_swing drops 'on': SwingV stays 0")
FAN_LOWEST = Defect("fan", "1", "auto", "convertFan + IRac cancel quiet: auto")
FAN_HIGHEST = Defect("fan", "5", "auto", "convertFan + IRac cancel powerful: auto")
DEFECTS = (MODE_DRY, SWING, FAN_LOWEST, FAN_HIGHEST)


def device():
    return Daikin128Device("daikin", "BRC52B63 remote")


def on(mode="cool", temperature=24.0, **kw):
    return device().normalise(HvacState(True, mode, temperature, **kw))


def off(mode="cool", temperature=24.0, **kw):
    return device().normalise(HvacState(False, mode, temperature, **kw))


@pytest.mark.parametrize("record", oracle_params("DAIKIN128"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


@pytest.mark.parametrize("record, states", sequence_params("DAIKIN128"))
def test_sequence_matches_a_persistent_c_object(record, states):
    # Power and swing toggles depend on the message before, which C's IRac keeps.
    dev = device()
    assert_sequence_matches_c(dev, record, states, dev.LAYOUTS, DEFECTS)


def test_layouts_round_trip_every_oracle_state():
    dev = device()
    for record in load_oracle("DAIKIN128"):
        state = state_from_record(dev, record["state"])
        _, first, second = dev.frames(None, state, ())
        for layout, frame in ((DAIKIN128_FIRST, first), (DAIKIN128_SECOND, second)):
            values = layout.read(frame.data)
            assert layout.build(**values) == bytearray(frame.data)


def test_first_checksum_is_the_top_nibble_of_byte_7():
    # A C frame from the oracle: 16 1a 00 00 00 00 23 b4 (auto, 23 °C, off).
    data = bytearray.fromhex("161a0000000023b4")
    assert DAIKIN128_FIRST.checksum.check(data)
    data[7] &= 0x0F
    DAIKIN128_FIRST.checksum.apply(data)
    assert data.hex() == "161a0000000023b4"


def test_first_checksum_nibble_is_free_of_fields():
    bits = {b for f in DAIKIN128_FIRST.fields.values() for b in f.bits}
    assert not bits & set(range(60, 64))


def test_temperature_is_bcd():
    _, first, _ = device().frames(None, on(temperature=23.0), ())
    assert first.data[6] == 0x23


def test_power_toggle_without_previous_follows_the_c_path():
    dev = device()
    _, first_on, _ = dev.frames(None, on(), ())
    _, first_off, _ = dev.frames(None, off(), ())
    assert DAIKIN128_FIRST.read(first_on.data)["power"] == 1
    assert DAIKIN128_FIRST.read(first_off.data)["power"] == 0


@pytest.mark.parametrize(
    "was, now, toggle",
    [(False, True, 1), (True, False, 1), (True, True, 0), (False, False, 0)],
)
def test_power_toggles_only_when_power_changes(was, now, toggle):
    dev = device()
    previous = on() if was else off()
    target = on(temperature=20.0) if now else off(temperature=20.0)
    _, first, _ = dev.frames(previous, target, ())
    assert DAIKIN128_FIRST.read(first.data)["power"] == toggle


def test_encode_uses_previous_for_the_toggle():
    dev = device()
    a = dev.encode(on(), on(temperature=20.0)).signal
    b = dev.encode(None, on(temperature=20.0)).signal
    assert a != b


@pytest.mark.parametrize("mode", ["auto", "dry", "cool", "heat", "fan"])
def test_off_frame_carries_mode_auto_in_every_mode(mode):
    _, first, _ = device().frames(None, off(mode, 18.0), ())
    read = DAIKIN128_FIRST.read(first.data)
    assert (read["mode"], read["temperature"], read["power"]) == ("auto", 18, 0)


@pytest.mark.parametrize("mode", ["dry", "cool", "heat", "fan"])
@pytest.mark.parametrize("fan, code", [("1", 0b1001), ("5", 0b0011)])
def test_extreme_fan_levels_send_quiet_and_powerful(mode, fan, code):
    # kDaikin128FanQuiet / kDaikin128FanPowerful, the documented codes
    _, first, _ = device().frames(None, on(mode, fan=fan), ())
    assert DAIKIN128_FIRST.read_raw(first.data, "fan") == code


@pytest.mark.parametrize("fan", ["1", "5"])
def test_extreme_fan_levels_send_auto_in_auto_and_off(fan):
    # setFan: quiet and powerful fall back to auto in mode auto (and an off
    # message carries mode auto)
    dev = device()
    for state in (on("auto", fan=fan), off("cool", fan=fan)):
        _, first, _ = dev.frames(None, state, ())
        assert DAIKIN128_FIRST.read(first.data)["fan"] == "auto"


@pytest.mark.parametrize("mode", ["auto", "dry", "cool", "heat", "fan"])
def test_economy_only_in_cool_and_heat(mode):
    _, _, second = device().frames(None, on(mode, features={"economy": True}), ())
    expected = int(mode in ("cool", "heat"))
    assert DAIKIN128_SECOND.read(second.data)["economy"] == expected


def test_economy_is_cleared_when_off():
    _, _, second = device().frames(None, off("cool", features={"economy": True}), ())
    assert DAIKIN128_SECOND.read(second.data)["economy"] == 0


@pytest.mark.parametrize("sleep", [False, True])
def test_sleep_sets_the_documented_bit(sleep):
    # Daikin128Protocol byte 7 bit 1 (Sleep, setSleep), in every mode.
    for mode in ("auto", "dry", "cool", "heat", "fan"):
        _, first, _ = device().frames(None, on(mode, features={"sleep": sleep}), ())
        assert first.data[7] >> 1 & 1 == sleep
        assert DAIKIN128_FIRST.read(first.data)["sleep"] == sleep


def test_light_without_previous_follows_the_c_path():
    # IRac::daikin128 from a fresh object: setLightToggle(light ?
    # kDaikin128BitWall : 0), Wall = byte 9 bit 3, Ceiling (bit 0) never set.
    for light in (False, True):
        _, _, second = device().frames(None, on(features={"light": light}), ())
        assert second.data[1] & 0b1001 == (0b1000 if light else 0)


@pytest.mark.parametrize(
    "was, now, toggle",
    [(False, True, 1), (True, False, 1), (True, True, 0), (False, False, 0)],
)
def test_light_toggles_only_when_it_changes(was, now, toggle):
    # IRac::handleToggles: result.light = desired.light ^ prev->light.
    previous = on(features={"light": was})
    target = on(temperature=20.0, features={"light": now})
    _, _, second = device().frames(previous, target, ())
    assert DAIKIN128_SECOND.read(second.data)["wall"] == toggle
    assert DAIKIN128_SECOND.read(second.data)["ceiling"] == 0


def test_registry_serves_the_port():
    for model in DAIKIN128_MODELS:
        assert isinstance(registry.get_device("daikin", model), Daikin128Device)


def _without(defect):
    return tuple(d for d in DEFECTS if d is not defect)


@pytest.mark.parametrize(
    "defect, pick",
    [
        (SWING, lambda s: s.get("swing") == "on" and s["fan"] == "auto"),
        (MODE_DRY, lambda s: s["mode"] == "dry" and s.get("swing") == "off"),
        (FAN_LOWEST, lambda s: s["mode"] == "cool" and s.get("fan") == "lowest"),
        (FAN_HIGHEST, lambda s: s["mode"] == "cool" and s.get("fan") == "highest"),
    ],
)
def test_undeclared_deviation_is_reported(defect, pick):
    dev = device()
    record = next(r for r in load_oracle("DAIKIN128") if pick(r["state"]))
    with pytest.raises(AssertionError, match=defect.field):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=_without(defect))


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("DAIKIN128")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:2], DEFECTS)


# No real capture in ir_Daikin_test.cpp needs it, but
# decodeDaikin128 matches with kDaikinTolerance (35 %) and
# kDaikinMarkExcess (kMarkExcess).
def test_decode_tolerance_is_the_c_decoders():
    assert (DAIKIN128.tolerance, DAIKIN128.mark_excess) == (0.35, 50)
