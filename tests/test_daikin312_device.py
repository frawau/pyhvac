import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.ir.model import Frame
from pyhvac.plugins.daikin import (
    DAIKIN312_FIRST,
    DAIKIN312_MODELS,
    DAIKIN312_SECOND,
    Daikin312Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Daikin312 values here:
# - IRDaikin312::convertSwingH has no kOff case, so "off" is sent as
#   kDaikin312SwingHAuto (0xF) instead of kDaikin312SwingHOff (0x0);
# - the old glue (IRGHVAC.trans_swing) has no "on" entry, so IRac keeps
#   swingv kOff and sends kDaikin312SwingVOff (0x0) instead of
#   kDaikin312SwingVSwing (0xF).
DEFECTS = (
    Defect("swing_h", "off", "swing", "C has no off case: sends swing (0xF)"),
    Defect("swing_v", "swing", "off", "C path never sends swing: sends off (0x0)"),
)


def device():
    return Daikin312Device("daikin", "ARC466A67 remote")


def frames(**kw):
    dev = device()
    features = kw.pop("features", {})
    state = dev.normalise(HvacState(features=features, **kw))
    return dev.frames(None, state, ())


@pytest.mark.parametrize("record", oracle_params("DAIKIN312"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layouts_round_trip_every_oracle_state():
    dev = device()
    for record in load_oracle("DAIKIN312"):
        state = state_from_record(dev, record["state"])
        _, first, second = dev.frames(None, state, ())
        for layout, frame in ((DAIKIN312_FIRST, first), (DAIKIN312_SECOND, second)):
            values = layout.read(frame.data)
            assert layout.build(**values) == bytearray(frame.data)


def test_leader_is_five_zero_bits():
    leader, _, _ = frames(power=True, mode="cool", temperature=24.0)
    assert leader == Frame("leader", b"\x00", 5)


def test_half_degree_setpoint():
    _, _, second = frames(power=True, mode="heat", temperature=22.5)
    assert second.data[6] == 45


def test_cool_raises_setpoint_to_18():
    _, _, second = frames(power=True, mode="cool", temperature=12.0)
    assert DAIKIN312_SECOND.read(second.data)["temperature"] == 36  # 18 °C


def test_off_clears_power_and_sets_power2():
    _, first, second = frames(power=False, mode="cool", temperature=24.0)
    assert DAIKIN312_SECOND.read(second.data)["power"] == 0
    assert DAIKIN312_FIRST.read(first.data)["power2"] == 1


@pytest.mark.parametrize("mode", ["auto", "dry", "cool", "heat", "fan"])
def test_off_frame_matches_the_c_path_in_every_mode(mode):
    # The C path sends mode "off", which Daikin312 turns into auto, with the
    # setpoint as given (the cool minimum does not apply to auto).
    _, _, second = frames(power=False, mode=mode, temperature=12.0)
    read = DAIKIN312_SECOND.read(second.data)
    assert (read["mode"], read["temperature"]) == ("auto", 24)


def test_powerful_cancels_quiet_as_the_c_path_does():
    _, _, second = frames(
        power=True,
        mode="cool",
        temperature=24.0,
        features={"quiet": True, "powerful": True},
    )
    read = DAIKIN312_SECOND.read(second.data)
    assert (read["powerful"], read["quiet"]) == (1, 0)


@pytest.mark.parametrize("light,raw", [(False, 3), (True, 1)])
def test_light_as_irac_sends_it(light, raw):
    _, first, _ = frames(
        power=True, mode="cool", temperature=24.0, features={"light": light}
    )
    assert first.data[12] & 0x03 == raw


def test_beep_off_and_auto_clean_are_hardwired():
    _, first, _ = frames(power=True, mode="cool", temperature=24.0)
    assert first.data[7] >> 6 == 3  # Beep off
    assert first.data[14] & 0x10  # Clean


def test_registry_serves_the_port():
    for model in DAIKIN312_MODELS:
        assert isinstance(registry.get_device("daikin", model), Daikin312Device)


def test_capabilities_match_the_legacy_entity():
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.daikin import Daikin312

    for model in DAIKIN312_MODELS:
        legacy = LegacyDevice("daikin", model, Daikin312)
        assert device().capabilities == legacy.capabilities


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(r for r in load_oracle("DAIKIN312") if "hswing" not in r["state"])
    with pytest.raises(AssertionError, match="swing_h"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("DAIKIN312")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:2], DEFECTS)
