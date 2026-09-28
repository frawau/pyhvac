import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.daikin import DAIKIN2_FIRST, DAIKIN2_SECOND, Daikin2Device
from pyhvac.state import HvacState

# IRremoteESP8266 deviates from its own documented Daikin2 values here:
# convertSwingV adds kDaikin2SwingVHighest to an enum that already starts at
# 1 (and has no case for upper-middle), and convertSwingH has no case for off.
DEFECTS = (
    Defect("swing_v", "1", "2", "C sends 'high' for highest"),
    Defect("swing_v", "2", "3", "C sends 'upper middle' for high"),
    Defect("swing_v", "3", "auto", "C has no upper-middle case: sends auto"),
    Defect("swing_h", "off", 0xBE, "C has no off case: sends auto (0xBE)"),
)


def device():
    return Daikin2Device("daikin", "ARC477A1 remote")


@pytest.mark.parametrize("record", oracle_params("DAIKIN2"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layouts_round_trip_every_oracle_state():
    dev = device()
    for record in load_oracle("DAIKIN2"):
        state = state_from_record(dev, record["state"])
        _, first, second = dev.frames(None, state, ())
        for layout, frame in ((DAIKIN2_FIRST, first), (DAIKIN2_SECOND, second)):
            values = layout.read(frame.data)
            assert layout.build(**values) == bytearray(frame.data)


def test_cool_raises_setpoint_to_18():
    dev = device()
    _, _, second = dev.frames(None, dev.normalise(HvacState(True, "cool", 12.0)), ())
    assert DAIKIN2_SECOND.read(second.data)["temperature"] == 18


def test_off_clears_power_and_sets_power2():
    dev = device()
    _, first, second = dev.frames(
        None, dev.normalise(HvacState(False, "cool", 24.0)), ()
    )
    assert DAIKIN2_SECOND.read(second.data)["power"] == 0
    assert DAIKIN2_FIRST.read(first.data)["power2"] == 1


def test_registry_serves_the_port():
    assert isinstance(registry.get_device("daikin", "FTXZ25NV1B"), Daikin2Device)


def test_capabilities_match_the_legacy_entity():
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.daikin import Daikin2

    legacy = LegacyDevice("daikin", "ARC477A1 remote", Daikin2)
    assert device().capabilities == legacy.capabilities


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(r for r in load_oracle("DAIKIN2") if "hswing" not in r["state"])
    with pytest.raises(AssertionError, match="swing_h"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


@pytest.mark.parametrize("mode", ["auto", "dry", "cool", "heat", "fan"])
def test_off_frame_matches_the_c_path_in_every_mode(mode):
    # The C path sends mode "off", which Daikin2 turns into auto, with the
    # setpoint as given (the cool minimum does not apply to auto).
    dev = device()
    state = dev.normalise(HvacState(False, mode, 12.0))
    _, _, second = dev.frames(None, state, ())
    read = DAIKIN2_SECOND.read(second.data)
    assert (read["mode"], read["temperature"]) == ("auto", 12)


def test_powerful_cancels_quiet_as_the_c_path_does():
    dev = device()
    state = dev.normalise(
        HvacState(True, "cool", 24.0, features={"quiet": True, "powerful": True})
    )
    _, _, second = dev.frames(None, state, ())
    read = DAIKIN2_SECOND.read(second.data)
    assert (read["powerful"], read["quiet"]) == (1, 0)


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("DAIKIN2")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:2], DEFECTS)


def test_every_daikin2_model_is_served_by_the_port():
    for model in (
        "ARC477A1 remote",
        "FTXZ25NV1B",
        "FTXZ35NV1B",
        "FTXZ50NV1B",
        "Daikin2",
    ):
        assert isinstance(registry.get_device("daikin", model), Daikin2Device)
