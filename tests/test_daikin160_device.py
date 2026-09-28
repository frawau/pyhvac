import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.daikin import (
    DAIKIN160_FIRST,
    DAIKIN160_MODELS,
    DAIKIN160_SECOND,
    Daikin160Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented kDaikin160SwingV* positions here:
# the old labels go through IRGHVAC.trans_swing ("90°" -> kHigh, "60°" ->
# kUpperMiddle) into IRDaikin160::convertSwingV, which maps kHigh to
# kDaikin160SwingVHigh (so kDaikin160SwingVHighest is never sent) and has no
# kUpperMiddle case (it falls back to kDaikin160SwingVAuto).
DEFECTS = (
    Defect("swing_v", "1", "2", "C sends 'high' (0x4) for highest"),
    Defect("swing_v", "2", "auto", "C has no upper-middle case: sends auto"),
)


def device():
    return Daikin160Device("daikin", "ARC423A5 remote")


@pytest.mark.parametrize("record", oracle_params("DAIKIN160"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layouts_round_trip_every_oracle_state():
    dev = device()
    for record in load_oracle("DAIKIN160"):
        state = state_from_record(dev, record["state"])
        first, second = dev.frames(None, state, ())
        for layout, frame in ((DAIKIN160_FIRST, first), (DAIKIN160_SECOND, second)):
            values = layout.read(frame.data)
            assert layout.build(**values) == bytearray(frame.data)


def test_first_frame_is_constant():
    dev = device()
    first, _ = dev.frames(None, dev.normalise(HvacState(True, "heat", 28.0)), ())
    assert first.data == bytes.fromhex("11da27f00d000f")


@pytest.mark.parametrize("mode", ["auto", "dry", "cool", "heat", "fan"])
def test_off_frame_matches_the_c_path_in_every_mode(mode):
    # The C path sends mode "off", which convertMode turns into auto, with
    # the setpoint as given.
    dev = device()
    state = dev.normalise(HvacState(False, mode, 21.0))
    _, second = dev.frames(None, state, ())
    read = DAIKIN160_SECOND.read(second.data)
    assert (read["power"], read["mode"], read["temperature"]) == (0, "auto", 11)


@pytest.mark.parametrize("temperature", [10.0, 21.0, 32.0])
def test_temperature_is_stored_as_degrees_minus_10(temperature):
    dev = device()
    state = dev.normalise(HvacState(True, "cool", temperature))
    _, second = dev.frames(None, state, ())
    assert DAIKIN160_SECOND.read(second.data)["temperature"] == temperature - 10


def test_swing_off_is_sent_as_auto():
    # The header has no "off" value; the C path falls back to auto (0xF).
    dev = device()
    off = dev.frames(None, dev.normalise(HvacState(True, "cool", 24.0)), ())
    auto = dev.frames(
        None, dev.normalise(HvacState(True, "cool", 24.0, swing_v="auto")), ()
    )
    assert off == auto
    assert DAIKIN160_SECOND.read_raw(off[1].data, "swing_v") == 0xF


def test_swing_positions_follow_the_header():
    dev = device()
    raw = {
        v: DAIKIN160_SECOND.read_raw(
            dev.frames(
                None, dev.normalise(HvacState(True, "cool", 24.0, swing_v=v)), ()
            )[1].data,
            "swing_v",
        )
        for v in ("1", "2", "3", "4", "5")
    }
    assert raw == {"1": 5, "2": 4, "3": 3, "4": 2, "5": 1}


def test_registry_serves_the_port():
    for model in DAIKIN160_MODELS:
        assert isinstance(registry.get_device("daikin", model), Daikin160Device)


@pytest.mark.parametrize("model", DAIKIN160_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.daikin import Daikin160

    legacy = LegacyDevice("daikin", model, Daikin160)
    assert Daikin160Device("daikin", model).capabilities == legacy.capabilities


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(
        r
        for r in load_oracle("DAIKIN160")
        if r["state"]["swing"] == "60°" and r["state"]["mode"] != "off"
    )
    with pytest.raises(AssertionError, match="swing_v"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("DAIKIN160")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:1], DEFECTS)
