import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac.protocols.daikin import (
    DAIKIN216,
    DAIKIN216_FIRST,
    DAIKIN216_MODELS,
    DAIKIN216_SECOND,
    Daikin216Device,
)
from pyhvac.state import HvacState
from pyhvac.ir.codec import decode

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


# IRDaikin216::setFan: kDaikinFanAuto (0xA), and kDaikinFanMin (1) ..
# kDaikinFanMax (5) sent as the speed plus 2. kDaikinFanQuiet stays the quiet
# feature (setQuiet), not a fan step.
@pytest.mark.parametrize(
    "fan,raw", [("auto", 0xA), ("1", 3), ("2", 4), ("3", 5), ("4", 6), ("5", 7)]
)
def test_every_fan_speed_uses_its_documented_value(fan, raw):
    dev = device()
    state = dev.normalise(HvacState(True, "cool", 24.0, fan=fan))
    assert state.fan == fan
    _, frame = dev.frames(None, state, ())
    assert DAIKIN216_SECOND.read_raw(frame.data, "fan") == raw


def test_quiet_is_not_a_fan_step():
    assert "quiet" not in device().capabilities.fan.values


def test_old_fan_labels_are_the_speeds_the_c_path_sent():
    # convertFan (IRDaikinESP's): kLow -> kDaikinFanMin, kMedium ->
    # kDaikinFanMed, kHigh -> kDaikinFanMax - 1.
    labels = device().capabilities.fan.labels
    assert (labels["1"], labels["3"], labels["4"]) == ("low", "medium", "high")


def test_swing_on_sets_the_documented_nibble():
    read = second(HvacState(True, "cool", 24.0, swing_v="swing", swing_h="swing"))
    assert (read["swing_v"], read["swing_h"]) == ("swing", "swing")
    raw = DAIKIN216_SECOND.build(swing_v="swing", swing_h="swing")
    assert (raw[8] & 0x0F, raw[9] & 0x0F) == (0xF, 0xF)


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


# ir_Daikin_test.cpp DecodeDaikin216.RealExample: decodeDaikin216 matches
# with kDaikinTolerance (35 %) and kDaikinMarkExcess (kMarkExcess); this
# capture has bit marks as short as 306 µs for 460.
REAL_RAW = (
    "3402 1770 382 1340 382 480 382 478 382 480 380 1342 382 478 356 504 "
    "382 480 380 478 384 1342 380 480 380 1342 382 1342 382 478 382 1340 "
    "382 1340 384 1340 382 1342 382 1340 380 480 382 480 382 1296 426 480 "
    "380 480 382 480 380 480 382 480 382 478 382 1342 382 1342 382 1340 356 "
    "1368 382 478 382 480 382 478 380 480 382 480 382 480 382 478 382 480 "
    "382 478 358 504 382 480 380 480 382 480 382 480 380 480 382 478 382 "
    "480 382 478 382 480 354 506 354 506 380 480 382 480 382 480 382 480 "
    "380 1342 382 480 382 480 382 478 382 478 382 478 384 478 382 29652 "
    "3426 1772 382 1340 382 480 380 478 382 480 382 1342 382 480 382 480 "
    "382 478 356 506 382 1342 380 480 382 1340 382 1340 382 478 356 1366 "
    "382 1340 384 1340 382 1340 382 1342 382 478 382 478 382 1340 382 478 "
    "382 478 382 478 382 480 382 480 384 478 358 504 382 478 382 480 382 "
    "478 382 480 382 480 382 478 382 480 382 478 382 478 382 478 382 478 "
    "384 478 382 478 360 500 358 504 382 478 382 480 382 480 382 478 382 "
    "478 382 1340 382 1342 382 480 380 480 382 1342 382 478 382 480 356 506 "
    "382 478 382 480 382 480 356 506 382 478 382 480 382 478 382 480 382 "
    "478 382 480 380 480 380 480 382 1342 382 478 382 1342 382 480 382 480 "
    "382 478 382 478 382 480 382 478 382 480 356 504 384 478 382 480 382 "
    "480 380 480 382 478 382 480 382 480 382 478 356 504 384 478 380 480 "
    "382 480 382 480 382 478 356 506 382 478 382 480 380 480 382 478 382 "
    "480 382 478 382 480 358 504 382 478 382 478 356 504 382 478 382 480 "
    "382 478 382 478 382 478 382 480 380 480 382 480 380 480 356 506 356 "
    "504 382 480 382 478 382 478 382 478 382 478 382 480 382 478 382 480 "
    "382 480 382 1340 382 1342 382 478 384 478 382 478 382 480 380 480 382 "
    "478 382 480 356 506 382 478 382 480 382 478 356 506 380 480 382 478 "
    "382 478 382 478 382 480 382 480 380 480 382 1342 382 1340 382 480 356 "
    "504 382 1342 382"
)


def test_real_raw_capture_decodes():
    pulses = [int(x) for x in REAL_RAW.split()]
    first, second = decode(DAIKIN216, pulses, expected=["main", "main"])
    assert first.data + second.data == bytes.fromhex(
        "11da27f000000002" "11da270000002600a0000000000000c0000098"
    )
