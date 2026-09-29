import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac.protocols.daikin import (
    DAIKIN160,
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


def c_record(record):
    """``record`` with the old vocabulary's swing "off" read as "auto".

    The header has no SwingV off value and the port no longer offers one:
    IRDaikin160::convertSwingV sent kOff as kDaikin160SwingVAuto, so the C
    frame recorded for "off" is the frame for "auto".
    """
    state = dict(record["state"])
    if state.get("swing") == "off":
        state["swing"] = "auto"
    return {**record, "state": state}


def records():
    return [c_record(r) for r in load_oracle("DAIKIN160")]


@pytest.mark.parametrize("record", oracle_params("DAIKIN160"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, c_record(record), dev.LAYOUTS, DEFECTS)


def test_layouts_round_trip_every_oracle_state():
    dev = device()
    for record in records():
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


def test_swing_off_is_not_offered():
    # The header documents kDaikin160SwingVAuto and five positions, no off:
    # a state asking for off normalises to auto (0xF), which is what the C
    # path sent for it.
    dev = device()
    assert "off" not in dev.capabilities.swing_v.values
    state = dev.normalise(HvacState(True, "cool", 24.0, swing_v="off"))
    assert state.swing_v == "auto"
    _, second = dev.frames(None, state, ())
    assert DAIKIN160_SECOND.read_raw(second.data, "swing_v") == 0xF


# setFan: kDaikinFanAuto (0xA), kDaikinFanMin (1) .. kDaikinFanMax (5) sent as
# the speed plus 2.
@pytest.mark.parametrize(
    "fan,raw", [("auto", 0xA), ("1", 3), ("2", 4), ("3", 5), ("4", 6), ("5", 7)]
)
def test_every_fan_speed_uses_its_documented_value(fan, raw):
    dev = device()
    state = dev.normalise(HvacState(True, "cool", 24.0, fan=fan))
    assert state.fan == fan
    _, second = dev.frames(None, state, ())
    assert DAIKIN160_SECOND.read_raw(second.data, "fan") == raw


def test_old_fan_labels_are_the_speeds_the_c_path_sent():
    # IRDaikin160::convertFan: kLow -> kDaikinFanMin + 1, kMedium -> + 2,
    # kHigh -> kDaikinFanMax - 1.
    labels = device().capabilities.fan.labels
    assert (labels["2"], labels["3"], labels["4"]) == ("low", "medium", "high")


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


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(
        r
        for r in records()
        if r["state"]["swing"] == "60°" and r["state"]["mode"] != "off"
    )
    with pytest.raises(AssertionError, match="swing_v"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = records()[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:1], DEFECTS)


# No real capture in ir_Daikin_test.cpp needs it, but
# decodeDaikin160 matches with kDaikinTolerance (35 %) and
# kDaikinMarkExcess (kMarkExcess).
def test_decode_tolerance_is_the_c_decoders():
    assert (DAIKIN160.tolerance, DAIKIN160.mark_excess) == (0.35, 50)
