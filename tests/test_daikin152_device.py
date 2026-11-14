import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac.protocols.daikin import DAIKIN152_MAIN, Daikin152Device
from pyhvac.state import HvacState

# The C path never sends vertical swing: IRGHVAC.trans_swing has no entry for
# the old "on" value, so IRac's swingv stays kOff and IRac::daikin152 calls
# setSwingV(false). The header documents kDaikinSwingOn (0xF) for it.
DEFECTS = (Defect("swing_v", "swing", "off", "C never sets kDaikinSwingOn"),)


def device():
    return Daikin152Device("daikin", "ARC480A5 remote")


@pytest.mark.parametrize("record", oracle_params("DAIKIN152"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("DAIKIN152"):
        state = state_from_record(dev, record["state"])
        _, main = dev.frames(None, state, ())
        values = DAIKIN152_MAIN.read(main.data)
        assert DAIKIN152_MAIN.build(**values) == bytearray(main.data)


def test_leader_is_five_zero_bits():
    dev = device()
    leader, _ = dev.frames(None, dev.normalise(HvacState(True, "cool", 24.0)), ())
    assert (leader.section, leader.data, leader.nbits) == ("leader", b"\x00", 5)
    assert dev.LAYOUTS[0] is None


def _read(state):
    dev = device()
    _, main = dev.frames(None, dev.normalise(state), ())
    return DAIKIN152_MAIN.read(main.data)


@pytest.mark.parametrize("mode", ["auto", "dry", "cool", "fan"])
def test_setpoint_floor_is_18_outside_heat(mode):
    assert _read(HvacState(True, mode, 10.0))["temperature"] == 18


def test_heat_setpoint_floor_is_10():
    assert _read(HvacState(True, "heat", 10.0))["temperature"] == 10


@pytest.mark.parametrize(
    "mode, expected",
    [("auto", 18.0), ("dry", 18.0), ("cool", 18.0), ("fan", 18.0), ("heat", 10.0)],
)
def test_normalise_reports_the_per_mode_floor(mode, expected):
    # setTemp: kDaikinMinTemp (10) in heat, kDaikin2MinCoolTemp (18) in every
    # other mode; the capabilities give the union (10..32).
    assert device().normalise(HvacState(True, mode, 10.0)).temperature == expected


def test_normalise_keeps_the_setpoint_of_an_off_state():
    assert device().normalise(HvacState(False, "heat", 10.0)).temperature == 10.0


# IRDaikin152::setFan: kDaikinFanAuto (0xA), kDaikinFanQuiet (0xB), and
# kDaikinFanMin (1) .. kDaikinFanMax (5) sent as the speed plus 2.
@pytest.mark.parametrize(
    "fan,raw",
    [("auto", 0xA), ("1", 0xB), ("2", 3), ("3", 4), ("4", 5), ("5", 6), ("6", 7)],
)
def test_every_fan_step_uses_its_documented_value(fan, raw):
    dev = device()
    state = dev.normalise(HvacState(True, "cool", 24.0, fan=fan))
    assert state.fan == fan
    _, main = dev.frames(None, state, ())
    assert DAIKIN152_MAIN.read_raw(main.data, "fan") == raw


def test_old_fan_labels_are_the_speeds_the_c_path_sent():
    # convertFan (IRDaikinESP's): kLow -> kDaikinFanMin, kMedium ->
    # kDaikinFanMed, kHigh -> kDaikinFanMax - 1.
    labels = device().capabilities.fan.labels
    assert (labels["2"], labels["4"], labels["5"]) == ("low", "medium", "high")


# TestDecodeDaikin152.RealExample: "Power: Off, Mode: 0 (Auto), Temp: 26C,
# Fan: 2 (UNKNOWN), Swing(V): Off, Powerful: Off, Quiet: On, Econo: Off".
REAL_EXAMPLE = bytes(
    [
        0x11, 0xDA, 0x27, 0x00, 0x00, 0x00, 0x34, 0x00, 0x40, 0x00,
        0x00, 0x00, 0x00, 0x20, 0x00, 0xC5, 0x40, 0x00, 0xAB,
    ]
)  # fmt: skip


def test_real_capture_with_fan_speed_2():
    dev = device()
    state = dev.normalise(
        HvacState(False, "auto", 26.0, fan="3", features={"quiet": True})
    )
    _, main = dev.frames(None, state, ())
    # The remote also set byte 16 bit 6, a bit the header leaves unnamed;
    # with it, the port's frame is the capture byte for byte.
    ours = bytearray(main.data)
    ours[16] |= 0x40
    DAIKIN152_MAIN.checksum.apply(ours)
    assert bytes(ours) == REAL_EXAMPLE


@pytest.mark.parametrize("mode", ["dry", "fan"])
def test_dry_and_fan_keep_the_requested_setpoint(mode):
    # setMode's kDaikin152DryTemp/FanTemp are overwritten by IRac's setTemp.
    assert _read(HvacState(True, mode, 27.0))["temperature"] == 27


@pytest.mark.parametrize("mode", ["auto", "dry", "cool", "heat", "fan"])
def test_off_frame_matches_the_c_path_in_every_mode(mode):
    # The C path sends mode "off", which Daikin152 turns into auto, so the
    # 18 °C floor applies even when the last mode was heat.
    read = _read(HvacState(False, mode, 10.0))
    assert (read["power"], read["mode"], read["temperature"]) == (0, "auto", 18)


def test_swing_sets_the_documented_value():
    assert _read(HvacState(True, "cool", 24.0, swing_v="swing"))["swing_v"] == "swing"


@pytest.mark.parametrize(
    "features, expected",
    [
        ({"powerful": True, "quiet": True}, (1, 0, 0)),
        ({"powerful": True, "economy": True}, (0, 0, 1)),
        ({"quiet": True, "economy": True}, (0, 1, 1)),
        ({"powerful": True, "quiet": True, "economy": True}, (0, 0, 1)),
    ],
)
def test_feature_interplay_follows_the_c_path(features, expected):
    # IRac sets quiet, then powerful (clears quiet), then econo (clears
    # powerful).
    read = _read(HvacState(True, "cool", 24.0, features=features))
    assert (read["powerful"], read["quiet"], read["economy"]) == expected


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(
        r for r in load_oracle("DAIKIN152") if r["state"].get("swing") == "on"
    )
    with pytest.raises(AssertionError, match="swing_v"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("DAIKIN152")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:1], DEFECTS)
