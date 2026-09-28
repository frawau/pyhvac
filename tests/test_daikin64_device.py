import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.daikin import (
    DAIKIN64_LAYOUT,
    DAIKIN64_MODELS,
    Daikin64Checksum,
    Daikin64Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Daikin64 values here:
# - IRac::daikin64 calls setFan(convertFan(fan)) and then setTurbo(turbo) and
#   setQuiet(quiet) with both false, which reset kDaikin64FanTurbo (kMax) and
#   kDaikin64FanQuiet (kMin) to kDaikin64FanAuto;
# - the legacy glue (IRGHVAC.trans_swing) has no "on" key, so swingv stays
#   kOff and IRDaikin64::setSwingVertical never sets the SwingV bit.
DEFECTS = (
    Defect("fan", "1", "auto", "C resets kDaikin64FanQuiet to auto"),
    Defect("fan", "5", "auto", "C resets kDaikin64FanTurbo to auto"),
    Defect("swing_v", "swing", "off", "legacy glue never passes swing on"),
)


def device():
    return Daikin64Device("daikin", "DGS01 remote")


def read(state, previous=None):
    _, main, _ = device().frames(previous, state, ())
    return DAIKIN64_LAYOUT.read(main.data)


@pytest.mark.parametrize("record", oracle_params("DAIKIN64"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("DAIKIN64"):
        state = state_from_record(dev, record["state"])
        _, main, _ = dev.frames(None, state, ())
        values = DAIKIN64_LAYOUT.read(main.data)
        assert DAIKIN64_LAYOUT.build(**values) == bytearray(main.data)


def test_checksum_is_the_nibble_sum_of_the_known_good_state():
    # kDaikin64KnownGoodState = 0x7C16161607204216, sent LSB first.
    data = bytearray((0x7C16161607204216).to_bytes(8, "little"))
    assert Daikin64Checksum().check(data)
    data[7] &= 0x0F
    Daikin64Checksum().apply(data)
    assert data[7] == 0x7C


def test_temperature_is_bcd():
    dev = device()
    _, main, _ = dev.frames(None, dev.normalise(HvacState(True, "cool", 23.0)), ())
    assert main.data[6] == 0x23


def test_off_carries_mode_cool_in_every_mode():
    # IRac passes mode "off"; IRDaikin64::convertMode maps it to cool.
    dev = device()
    for mode in dev.capabilities.modes:
        for t in (16.0, 30.0):
            values = read(dev.normalise(HvacState(False, mode, t)))
            assert (values["mode"], values["temperature"]) == ("cool", int(t))


def test_power_bit_without_previous_is_the_target_power():
    # A fresh IRac has no previous state for DAIKIN64: Power = on.
    dev = device()
    assert read(dev.normalise(HvacState(True, "heat", 20.0)))["power"] == 1
    assert read(dev.normalise(HvacState(False, "heat", 20.0)))["power"] == 0


@pytest.mark.parametrize(
    "before, after, toggle",
    [(True, True, 0), (True, False, 1), (False, False, 0), (False, True, 1)],
)
def test_power_bit_with_previous_toggles_on_change(before, after, toggle):
    # IRac::handleToggles: result.power = desired.power ^ prev->power.
    dev = device()
    previous = dev.normalise(HvacState(before, "cool", 22.0))
    target = dev.normalise(HvacState(after, "cool", 22.0))
    assert read(target, previous)["power"] == toggle


def test_encode_passes_previous_to_the_toggle():
    dev = device()
    on = HvacState(True, "cool", 22.0)
    fresh = dev.encode(None, on).signal
    again = dev.encode(on, on).signal
    assert fresh != again


@pytest.mark.parametrize(
    "fan, raw", [("auto", 1), ("1", 9), ("2", 8), ("3", 4), ("4", 2), ("5", 3)]
)
def test_every_fan_level_uses_its_documented_value(fan, raw):
    dev = device()
    _, main, _ = dev.frames(
        None, dev.normalise(HvacState(True, "cool", 22.0, fan=fan)), ()
    )
    assert DAIKIN64_LAYOUT.read_raw(main.data, "fan") == raw


def test_swing_sets_the_swing_bit():
    dev = device()
    swing = dev.normalise(HvacState(True, "cool", 22.0, swing_v="swing"))
    still = dev.normalise(HvacState(True, "cool", 22.0))
    assert (read(swing)["swing_v"], read(still)["swing_v"]) == ("swing", "off")


def test_message_shape():
    dev = device()
    pulses = dev.encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:5] == (9800, 9800, 9800, 9800, 4600)
    assert pulses[-2:] == (4600, 100000)
    assert len(pulses) == 4 + 2 + 2 * 64 + 2 + 2


@pytest.mark.parametrize("model", DAIKIN64_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("daikin", model), Daikin64Device)


@pytest.mark.parametrize("model", DAIKIN64_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.daikin import Daikin64

    legacy = LegacyDevice("daikin", model, Daikin64)
    assert Daikin64Device("daikin", model).capabilities == legacy.capabilities


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(r for r in load_oracle("DAIKIN64") if r["state"]["swing"] == "on")
    with pytest.raises(AssertionError, match="swing_v"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("DAIKIN64")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:2], DEFECTS)
