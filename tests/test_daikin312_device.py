import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.ir.model import Frame
from pyhvac.plugins.daikin import (
    DAIKIN312,
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


def test_normalise_reports_the_cool_minimum():
    # setTemp: kDaikin312MinCoolTemp (18) in cool, kDaikinMinTemp otherwise.
    dev = device()
    assert dev.normalise(HvacState(True, "cool", 12.5)).temperature == 18.0
    assert dev.normalise(HvacState(True, "heat", 12.5)).temperature == 12.5
    assert dev.normalise(HvacState(False, "cool", 12.5)).temperature == 12.5


# setFan (as IRDaikinESP's): kDaikinFanAuto (0xA), kDaikinFanQuiet (0xB), and
# kDaikinFanMin (1) .. kDaikinFanMax (5) sent as the speed plus 2.
@pytest.mark.parametrize(
    "fan,raw",
    [("auto", 0xA), ("1", 0xB), ("2", 3), ("3", 4), ("4", 5), ("5", 6), ("6", 7)],
)
def test_every_fan_step_uses_its_documented_value(fan, raw):
    _, _, second = frames(power=True, mode="cool", temperature=24.0, fan=fan)
    assert DAIKIN312_SECOND.read_raw(second.data, "fan") == raw


def test_old_fan_labels_are_the_speeds_the_c_path_sent():
    # convertFan (IRDaikinESP's): kLow -> kDaikinFanMin, kMedium ->
    # kDaikinFanMed, kHigh -> kDaikinFanMax - 1.
    labels = device().capabilities.fan.labels
    assert (labels["2"], labels["4"], labels["5"]) == ("low", "medium", "high")


# kDaikin312SwingVOff (0x0), kDaikin312SwingVAuto a.k.a. swing (0xF), and
# kDaikin312SwingVHighest (0x1) .. kDaikin312SwingVLowest (0x6).
@pytest.mark.parametrize(
    "swing_v,raw",
    [("off", 0x0), ("swing", 0xF)] + [(str(n), n) for n in range(1, 7)],
)
def test_every_swing_v_position_uses_its_documented_value(swing_v, raw):
    _, _, second = frames(power=True, mode="cool", temperature=24.0, swing_v=swing_v)
    assert DAIKIN312_SECOND.read_raw(second.data, "swing_v") == raw


def test_swing_h_has_no_positions():
    # kDaikin312SwingH{Wide,LeftMax,...,RightMax} are 0xA3..0xAC, which do not
    # fit the header's 4-bit SwingH field: only off and swing are offered.
    assert device().capabilities.swing_h.values == ("off", "swing")


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


# No real capture in ir_Daikin_test.cpp needs it, but
# decodeDaikin312 matches with kDaikinTolerance (35 %) and no mark
# excess.
def test_decode_tolerance_is_the_c_decoders():
    assert (DAIKIN312.tolerance, DAIKIN312.mark_excess) == (0.35, 0)
