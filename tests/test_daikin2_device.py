import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac.protocols.daikin import (
    DAIKIN2_FIRST,
    DAIKIN2_SECOND,
    Daikin2Device,
    DAIKIN2,
)
from pyhvac.state import HvacState

# IRremoteESP8266 deviates from its own documented Daikin2 values here:
# convertSwingV adds kDaikin2SwingVHighest to an enum that already starts at
# 1 (and has no case for upper-middle), and convertSwingH has no case for off.
DEFECTS = (
    Defect("swing_v", "1", "2", "C sends 'high' for highest"),
    Defect("swing_v", "2", "3", "C sends 'upper middle' for high"),
    Defect("swing_v", "3", "auto", "C has no upper-middle case: sends auto"),
    Defect("swing_h", "off", "auto", "C has no off case: sends auto (0xBE)"),
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


def test_normalise_reports_the_cool_minimum():
    # setTemp: kDaikin2MinCoolTemp (18) in cool, kDaikinMinTemp (10) otherwise.
    dev = device()
    assert dev.normalise(HvacState(True, "cool", 12.0)).temperature == 18.0
    assert dev.normalise(HvacState(True, "heat", 12.0)).temperature == 12.0
    # Off messages carry mode auto: the requested setpoint is kept.
    assert dev.normalise(HvacState(False, "cool", 12.0)).temperature == 12.0


# setFan: kDaikinFanAuto (0xA), kDaikinFanQuiet (0xB), and kDaikinFanMin (1)
# .. kDaikinFanMax (5) sent as the speed plus 2.
@pytest.mark.parametrize(
    "fan,raw",
    [("auto", 0xA), ("1", 0xB), ("2", 3), ("3", 4), ("4", 5), ("5", 6), ("6", 7)],
)
def test_every_fan_step_uses_its_documented_value(fan, raw):
    dev = device()
    state = dev.normalise(HvacState(True, "cool", 24.0, fan=fan))
    assert state.fan == fan
    _, _, second = dev.frames(None, state, ())
    assert DAIKIN2_SECOND.read_raw(second.data, "fan") == raw


def test_old_fan_labels_are_the_speeds_the_c_path_sent():
    # IRDaikinESP::convertFan: kLow -> kDaikinFanMin, kMedium -> kDaikinFanMed,
    # kHigh -> kDaikinFanMax - 1.
    labels = device().capabilities.fan.labels
    assert (labels["2"], labels["4"], labels["5"]) == ("low", "medium", "high")


def test_swing_h_auto_is_kdaikin2swinghauto():
    dev = device()
    state = dev.normalise(HvacState(True, "cool", 24.0, swing_h="auto"))
    assert state.swing_h == "auto"
    _, first, _ = dev.frames(None, state, ())
    assert first.data[17] == 0xBE  # kDaikin2SwingHAuto


@pytest.mark.parametrize("light,raw", [(False, 3), (True, 1)])
def test_light_as_irac_sends_it(light, raw):
    # Light (byte 7 bits 4-5): kDaikinLightBright (1) on, kDaikinLightOff (3)
    # off, as IRac::daikin2 sets it.
    dev = device()
    state = dev.normalise(HvacState(True, "cool", 24.0, features={"light": light}))
    _, first, _ = dev.frames(None, state, ())
    assert (first.data[7] >> 4) & 0x03 == raw


# Real captures (ir_Daikin_test.cpp). The port does not model the clock,
# fresh air, beep or eye bits these remotes also sent, so every field the
# layouts do model is compared.
ISSUE_1035_ON = bytes(  # TestDaikin2Class.Issue1035, on_code
    [
        0x11, 0xDA, 0x27, 0x00, 0x01, 0x15, 0x43, 0x90, 0x29, 0x0C, 0x80, 0x04,
        0xC0, 0x16, 0x24, 0x00, 0x00, 0xBE, 0xC1, 0x2D, 0x11, 0xDA, 0x27, 0x00,
        0x00, 0x09, 0x2A, 0x00, 0xB0, 0x00, 0x00, 0x06, 0x60, 0x00, 0x00, 0xC1,
        0x90, 0x60, 0x0C,
    ]
)  # fmt: skip
ISSUE_908_FAN_MEDIUM = bytes(  # TestDaikin2ClassNew.Issue908, fanMedium
    [
        0x11, 0xDA, 0x27, 0x00, 0x01, 0x4A, 0x42, 0xB0, 0x28, 0x0C, 0x80, 0x04,
        0xB0, 0x16, 0x24, 0x00, 0x00, 0xAA, 0xC3, 0x5E, 0x11, 0xDA, 0x27, 0x00,
        0x00, 0x09, 0x3C, 0x00, 0x50, 0x00, 0x00, 0x06, 0x60, 0x00, 0x00, 0xC1,
        0x90, 0x60, 0xBE,
    ]
)  # fmt: skip


def assert_fields_match(ours, capture):
    first, second = capture[:20], capture[20:]
    assert DAIKIN2_FIRST.read(ours[1].data) == DAIKIN2_FIRST.read(first)
    assert DAIKIN2_SECOND.read(ours[2].data) == DAIKIN2_SECOND.read(second)


def test_real_capture_with_quiet_fan_light_and_swing_h_auto():
    # "Power: On, Mode: 0 (Auto), Temp: 21C, Fan: 11 (Quiet), Swing(V): 1
    # (Highest), Swing(H): 190 (Auto), Light: 1 (High), Mould: On, Purify: On"
    dev = device()
    state = dev.normalise(
        HvacState(
            True,
            "auto",
            21.0,
            fan="1",
            swing_v="1",
            swing_h="auto",
            features={"light": True, "cleaning": True, "purifier": True},
        )
    )
    assert_fields_match(dev.frames(None, state, ()), ISSUE_1035_ON)


def test_real_capture_with_fan_speed_3():
    # "Power: On, Mode: 0 (Auto), Temp: 30C, Fan: 3 (Medium), Swing(V): 3
    # (Upper Middle), Swing(H): 170 (Middle), Light: 3 (Off), Mould: On,
    # Purify: On"
    dev = device()
    state = dev.normalise(
        HvacState(
            True,
            "auto",
            30.0,
            fan="4",
            swing_v="3",
            swing_h="3",
            features={"cleaning": True, "purifier": True},
        )
    )
    assert_fields_match(dev.frames(None, state, ()), ISSUE_908_FAN_MEDIUM)


def test_off_clears_power_and_sets_power2():
    dev = device()
    _, first, second = dev.frames(
        None, dev.normalise(HvacState(False, "cool", 24.0)), ()
    )
    assert DAIKIN2_SECOND.read(second.data)["power"] == 0
    assert DAIKIN2_FIRST.read(first.data)["power2"] == 1


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


# No real capture in ir_Daikin_test.cpp needs it, but
# decodeDaikin2 matches with _tolerance + kDaikin2Tolerance (30 %) and
# kDaikinMarkExcess (kMarkExcess).
def test_decode_tolerance_is_the_c_decoders():
    assert (DAIKIN2.tolerance, DAIKIN2.mark_excess) == (0.30, 50)
