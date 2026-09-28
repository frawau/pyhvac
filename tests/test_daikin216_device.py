import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.daikin import (
    DAIKIN216_FIRST,
    DAIKIN216_MODELS,
    DAIKIN216_SECOND,
    Daikin216Device,
)
from pyhvac.state import HvacState

# The C path never sends swing on: the old vocabulary's "on" has no entry in
# IRGHVAC.trans_swing / trans_hswing, so build_ircode skips the key, swingv and
# swingh stay kOff, and IRac::daikin216 writes kDaikin216SwingOff instead of
# the documented kDaikin216SwingOn (0b1111).
DEFECTS = (
    Defect("swing_v", "swing", "off", "C glue has no 'on' swing: sends off"),
    Defect("swing_h", "swing", "off", "C glue has no 'on' hswing: sends off"),
)


def device():
    return Daikin216Device("daikin", "ARC433B69 remote")


def second(state):
    dev = device()
    _, frame = dev.frames(None, dev.normalise(state), ())
    return DAIKIN216_SECOND.read(frame.data)


@pytest.mark.parametrize("record", oracle_params("DAIKIN216"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layouts_round_trip_every_oracle_state():
    dev = device()
    for record in load_oracle("DAIKIN216"):
        state = state_from_record(dev, record["state"])
        first, sec = dev.frames(None, state, ())
        for layout, frame in ((DAIKIN216_FIRST, first), (DAIKIN216_SECOND, sec)):
            values = layout.read(frame.data)
            assert layout.build(**values) == bytearray(frame.data)


def test_first_section_is_constant():
    assert bytes(DAIKIN216_FIRST.build()) == bytes.fromhex("11da27f000000002")


@pytest.mark.parametrize("mode", ["auto", "dry", "cool", "heat", "fan"])
def test_off_frame_matches_the_c_path_in_every_mode(mode):
    # The C path sends mode "off", which convertMode turns into auto.
    read = second(HvacState(False, mode, 24.0))
    assert (read["power"], read["mode"], read["temperature"]) == (0, "auto", 24)


def test_setpoint_is_clamped_to_10_32():
    assert second(HvacState(True, "cool", 5.0))["temperature"] == 10
    assert second(HvacState(True, "heat", 40.0))["temperature"] == 32


def test_quiet_is_a_fan_speed():
    read = second(HvacState(True, "cool", 24.0, fan="3", features={"quiet": True}))
    assert (read["fan"], read["powerful"]) == ("quiet", 0)


def test_powerful_cancels_quiet_and_leaves_fan_auto_as_the_c_path_does():
    state = HvacState(
        True, "cool", 24.0, fan="3", features={"quiet": True, "powerful": True}
    )
    read = second(state)
    assert (read["fan"], read["powerful"]) == ("auto", 1)


def test_powerful_keeps_the_fan_speed():
    read = second(HvacState(True, "cool", 24.0, fan="2", features={"powerful": True}))
    assert (read["fan"], read["powerful"]) == ("2", 1)


def test_swing_on_sets_the_documented_nibble():
    read = second(HvacState(True, "cool", 24.0, swing_v="swing", swing_h="swing"))
    assert (read["swing_v"], read["swing_h"]) == ("swing", "swing")
    raw = DAIKIN216_SECOND.build(swing_v="swing", swing_h="swing")
    assert (raw[8] & 0x0F, raw[9] & 0x0F) == (0xF, 0xF)


@pytest.mark.parametrize("model", DAIKIN216_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("daikin", model), Daikin216Device)


def test_capabilities_match_the_legacy_entity():
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.daikin import Daikin216

    legacy = LegacyDevice("daikin", "ARC433B69 remote", Daikin216)
    assert device().capabilities == legacy.capabilities


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(
        r for r in load_oracle("DAIKIN216") if r["state"].get("swing") == "on"
    )
    with pytest.raises(AssertionError, match="swing_v"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("DAIKIN216")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:1], DEFECTS)
