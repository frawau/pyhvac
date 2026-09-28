import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.daikin import (
    DAIKIN176_FIRST,
    DAIKIN176_MODELS,
    DAIKIN176_SECOND,
    Daikin176Device,
)
from pyhvac.state import HvacState

# The C path never sends kDaikin176SwingHAuto (0x5): IRGHVAC.trans_hswing has
# no entry for the old value "on", so swingh stays at IRac's default kOff and
# IRDaikin176::convertSwingH turns that into kDaikin176SwingHOff (0x6).
DEFECTS = (Defect("swing_h", "swing", "off", "C sends SwingHOff for swing 'on'"),)


def device():
    return Daikin176Device("daikin", "BRC4C153 remote")


def _with_c_defaults(record):
    # A record without "fan" relied on IRac's default (kAuto), which
    # IRDaikin176::convertFan sends as kDaikin176FanMax, labelled "high".
    return {**record, "state": {"fan": "high", **record["state"]}}


@pytest.mark.parametrize("record", oracle_params("DAIKIN176"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, _with_c_defaults(record), dev.LAYOUTS, DEFECTS)


def test_layouts_round_trip_every_oracle_state():
    dev = device()
    for record in load_oracle("DAIKIN176"):
        state = state_from_record(dev, _with_c_defaults(record)["state"])
        first, second = dev.frames(None, state, ())
        for layout, frame in ((DAIKIN176_FIRST, first), (DAIKIN176_SECOND, second)):
            values = layout.read(frame.data)
            assert layout.build(**values) == bytearray(frame.data)


@pytest.mark.parametrize("mode", ["dry", "fan"])
def test_dry_and_fan_send_17(mode):
    dev = device()
    _, second = dev.frames(None, dev.normalise(HvacState(True, mode, 30.0)), ())
    assert DAIKIN176_SECOND.read(second.data)["temperature"] == 17 - 9


@pytest.mark.parametrize(
    "mode, alt", [("auto", 7), ("cool", 7), ("heat", 7), ("dry", 2), ("fan", 6)]
)
def test_alt_mode_follows_the_mode(mode, alt):
    dev = device()
    _, second = dev.frames(None, dev.normalise(HvacState(True, mode, 24.0)), ())
    read = DAIKIN176_SECOND.read(second.data)
    assert (read["mode"], read["alt_mode"], read["mode_button"]) == (mode, alt, 0)


@pytest.mark.parametrize("mode", ["auto", "dry", "cool", "heat", "fan"])
def test_off_frame_matches_the_c_path_in_every_mode(mode):
    # The C path sends mode "off", which convertMode turns into cool, with
    # the setpoint as given (the dry/fan 17 °C rule does not apply to cool).
    dev = device()
    state = dev.normalise(HvacState(False, mode, 12.0))
    _, second = dev.frames(None, state, ())
    read = DAIKIN176_SECOND.read(second.data)
    assert (read["power"], read["mode"], read["alt_mode"]) == (0, "cool", 7)
    assert read["temperature"] == 12 - 9


def test_fan_and_swing_codes():
    dev = device()
    for fan, code in (("1", 1), ("2", 3)):
        for swing, scode in (("off", 6), ("swing", 5)):
            state = dev.normalise(HvacState(True, "cool", 24.0, fan, swing_h=swing))
            _, second = dev.frames(None, state, ())
            assert second.data[11] == code << 4 | scode


@pytest.mark.parametrize("model", DAIKIN176_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("daikin", model), Daikin176Device)


def test_capabilities_match_the_legacy_entity():
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.daikin import Daikin176

    for model in DAIKIN176_MODELS:
        legacy = LegacyDevice("daikin", model, Daikin176)
        assert device().capabilities == legacy.capabilities


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(
        r for r in load_oracle("DAIKIN176") if r["state"].get("hswing") == "on"
    )
    with pytest.raises(AssertionError, match="swing_h"):
        assert_matches_oracle(dev, _with_c_defaults(record), dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("DAIKIN176")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:1], DEFECTS)
