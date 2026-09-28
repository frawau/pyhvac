import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.daikin import (
    DAIKIN_ARC_FIRST,
    DAIKIN_ARC_MODELS,
    DAIKIN_ARC_SECOND,
    DAIKIN_ARC_THIRD,
    DaikinArcDevice,
)
from pyhvac.state import HvacState

# The C path never sends swing: pyhvac's IRGHVAC.trans_swing/trans_hswing have
# no "on" key, so IRac keeps swingv/swingh at kOff and IRac::daikin calls
# setSwingVertical/Horizontal(false). The header documents
# kDaikinSwingOn = 0b1111 for SwingV/SwingH; the port sends it.
DEFECTS = (
    Defect("swing_v", "swing", "off", "C path drops swing 'on' (kDaikinSwingOn)"),
    Defect("swing_h", "swing", "off", "C path drops hswing 'on' (kDaikinSwingOn)"),
)


def device():
    return DaikinArcDevice("daikin", "ARC433 remote")


def third(state):
    dev = device()
    frames = dev.frames(None, dev.normalise(state), ())
    return DAIKIN_ARC_THIRD.read(frames[3].data)


@pytest.mark.parametrize("record", oracle_params("DAIKIN"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layouts_round_trip_every_oracle_state():
    dev = device()
    layouts = (DAIKIN_ARC_FIRST, DAIKIN_ARC_SECOND, DAIKIN_ARC_THIRD)
    for record in load_oracle("DAIKIN"):
        state = state_from_record(dev, record["state"])
        leader, *mains = dev.frames(None, state, ())
        assert (leader.data, leader.nbits) == (b"\x00", 5)
        for layout, frame in zip(layouts, mains):
            values = layout.read(frame.data)
            assert layout.build(**values) == bytearray(frame.data)


def test_half_degree_setpoints_are_sent():
    assert third(HvacState(True, "cool", 24.5))["half_degrees"] == 49


@pytest.mark.parametrize("mode", ["auto", "dry", "cool", "heat", "fan"])
@pytest.mark.parametrize("temperature", [10.0, 32.0])
def test_off_frame_carries_mode_auto_in_every_mode(mode, temperature):
    # The C path sends mode "off", which convertMode turns into auto; the
    # setpoint is kept as given.
    read = third(HvacState(False, mode, temperature))
    assert (read["power"], read["mode"], read["half_degrees"]) == (
        0,
        "auto",
        int(temperature * 2),
    )


def test_powerful_cancels_quiet():
    read = third(
        HvacState(True, "cool", 24.0, features={"quiet": True, "powerful": True})
    )
    assert (read["powerful"], read["quiet"]) == (1, 0)


def test_economy_cancels_powerful():
    read = third(
        HvacState(True, "cool", 24.0, features={"economy": True, "powerful": True})
    )
    assert (read["powerful"], read["economy"]) == (0, 1)


def test_quiet_and_economy_coexist():
    read = third(
        HvacState(True, "cool", 24.0, features={"economy": True, "quiet": True})
    )
    assert (read["quiet"], read["economy"]) == (1, 1)


def test_all_three_leave_economy_only():
    feats = {"economy": True, "powerful": True, "quiet": True}
    read = third(HvacState(True, "cool", 24.0, features=feats))
    assert (read["quiet"], read["powerful"], read["economy"]) == (0, 0, 1)


def test_swing_sends_the_documented_value():
    dev = device()
    state = dev.normalise(
        HvacState(True, "cool", 24.0, swing_v="swing", swing_h="swing")
    )
    data = dev.frames(None, state, ())[3].data
    assert data[8] & 0x0F == 0xF and data[9] & 0x0F == 0xF


def test_registry_serves_the_port():
    for model in DAIKIN_ARC_MODELS:
        assert isinstance(registry.get_device("daikin", model), DaikinArcDevice)


def test_capabilities_match_the_legacy_entity():
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.daikin import Daikin

    for model in DAIKIN_ARC_MODELS:
        legacy = LegacyDevice("daikin", model, Daikin)
        assert DaikinArcDevice("daikin", model).capabilities == legacy.capabilities


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(r for r in load_oracle("DAIKIN") if r["state"].get("swing") == "on")
    with pytest.raises(AssertionError, match="swing_v"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("DAIKIN")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:3], DEFECTS)
