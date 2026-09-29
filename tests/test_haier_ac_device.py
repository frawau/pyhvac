import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac.ir.codec import decode
from pyhvac.protocols.haier import (
    HAIER_AC,
    HAIER_AC_LAYOUT,
    HAIER_AC_MODELS,
    HaierAcDevice,
)
from pyhvac.state import HvacState

# The C path never sends sleep: IRGHVAC.build_ircode's key map has no
# "sleep", so IRac::haier gets sleep -1 and setSleep(sleep >= 0) clears
# kHaierAcSleepBit. The port sends the documented bit.
DEFECTS = (Defect("sleep", 1, 0, "C glue has no 'sleep' key"),)

# Real captures from ir_Haier_test.cpp.
ON_COOL_25 = bytes.fromhex("a59120000cc0200042")  # issue #668
ISSUE_404_ON_COOL_16 = bytes.fromhex("a501200100c02000a7")
ISSUE_404_TEMP_UP_22 = bytes.fromhex("a566200100c020000c")
ISSUE_404_HEALTH_30 = bytes.fromhex("a5ec200920c02000ba")
ISSUE_668_TEMP_UP_26 = bytes.fromhex("a5a620000cc0200057")


def device(model="HSU07-HEA03 remote"):
    return HaierAcDevice("haier", model)


def read(state, previous=None):
    dev = device()
    if previous is not None:
        previous = dev.normalise(previous)
    (main,) = dev.frames(previous, dev.normalise(state), ())
    return HAIER_AC_LAYOUT.read(main.data)


def data(state):
    dev = device()
    (main,) = dev.frames(None, dev.normalise(state), ())
    return main.data


@pytest.mark.parametrize("record", oracle_params("HAIER_AC"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("HAIER_AC"):
        state = state_from_record(dev, record["state"])
        (main,) = dev.frames(None, state, ())
        values = HAIER_AC_LAYOUT.read(main.data)
        assert HAIER_AC_LAYOUT.build(**values) == bytearray(main.data)
        assert HAIER_AC_LAYOUT.checksum.check(main.data)


def test_every_oracle_message_is_one_frame():
    for record in load_oracle("HAIER_AC"):
        (main,) = decode(HAIER_AC, record["pulses"], ["main"])
        assert main.data[0] == 0xA5  # kHaierAcPrefix


def test_the_port_reproduces_the_issue_668_on_capture():
    # "ON" in cool at 25 °C, fan low: the remote's own frame (Command On).
    assert data(HvacState(True, "cool", 25.0, fan="1")) == ON_COOL_25


@pytest.mark.parametrize(
    "capture, expected",
    [
        (
            ISSUE_404_ON_COOL_16,
            {"command": "on", "temperature": 16, "mode": "cool", "fan": "1"},
        ),
        (
            ISSUE_404_TEMP_UP_22,
            {"command": "temp_up", "temperature": 22, "mode": "cool", "fan": "1"},
        ),
        (
            ISSUE_404_HEALTH_30,
            {"command": "health", "temperature": 30, "health": 1, "fan": "1"},
        ),
        (
            ISSUE_668_TEMP_UP_26,
            {"command": "temp_up", "temperature": 26, "mode": "cool", "fan": "1"},
        ),
    ],
)
def test_real_captures_read_back(capture, expected):
    # These carry the key actually pressed and the remote's clock, which the
    # C path (and so the port) never sends; they read back through the layout.
    values = HAIER_AC_LAYOUT.read(capture)
    assert HAIER_AC_LAYOUT.checksum.check(capture)
    assert {k: values[k] for k in expected} == expected
    assert HAIER_AC_LAYOUT.build(**values) == bytearray(capture)


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat", "fan"])
@pytest.mark.parametrize("t", [16.0, 23.0, 30.0])
def test_off_carries_mode_auto_and_command_off(mode, t):
    # IRac passes mode "off"; convertMode maps it to kHaierAcAuto, and the
    # final setCommand writes kHaierAcCmdOff.
    values = read(HvacState(False, mode, t, fan="3", swing_v="2"))
    assert (values["command"], values["mode"]) == ("off", "auto")
    assert (values["temperature"], values["fan"], values["swing_v"]) == (
        int(t),
        "3",
        "2",
    )


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat", "fan"])
def test_on_always_names_the_on_button(mode):
    # IRac::haier ends with setCommand(kHaierAcCmdOn), overwriting the Mode,
    # TempUp/Down, Fan, Swing, Health and Sleep commands the setters wrote.
    values = read(
        HvacState(True, mode, 30.0, fan="2", swing_v="1", features={"sleep": True})
    )
    assert (values["command"], values["mode"]) == ("on", mode)


def test_setpoint_is_clamped_to_16_30():
    assert read(HvacState(True, "cool", 10.0))["temperature"] == 16
    assert read(HvacState(True, "heat", 35.0))["temperature"] == 30


@pytest.mark.parametrize("fan, raw", [("auto", 0), ("1", 3), ("2", 2), ("3", 1)])
def test_every_fan_level_uses_set_fan_raw_values(fan, raw):
    # IRHaierAC::setFan stores Low as 3, Med as 2, High as 1, Auto as 0.
    assert (
        HAIER_AC_LAYOUT.read_raw(data(HvacState(True, "cool", 22.0, fan=fan)), "fan")
        == raw
    )


@pytest.mark.parametrize("swing, raw", [("off", 0), ("auto", 3), ("1", 1), ("2", 2)])
def test_every_swing_position(swing, raw):
    # "auto high" -> kHigh -> kHaierAcSwingVUp; "auto low" -> kLow -> Down;
    # "auto" -> kAuto -> kHaierAcSwingVChg (0b11).
    raw_read = HAIER_AC_LAYOUT.read_raw(
        data(HvacState(True, "cool", 22.0, swing_v=swing)), "swing_v"
    )
    assert raw_read == raw


def test_purifier_is_the_health_bit():
    assert (
        read(HvacState(True, "cool", 22.0, features={"purifier": True}))["health"] == 1
    )
    assert read(HvacState(True, "cool", 22.0))["health"] == 0


def test_sleep_sends_the_documented_sleep_bit():
    raw = data(HvacState(True, "cool", 22.0, features={"sleep": True}))
    assert raw[7] & 0b01000000  # kHaierAcSleepBit
    assert read(HvacState(True, "cool", 22.0))["sleep"] == 0


def test_timers_and_clock_are_never_set():
    # IRac passes clock -1 (no setCurrTime) and has no timers: stateReset's
    # values (OffHours 12, the rest 0) are sent.
    values = read(HvacState(True, "heat", 18.0, fan="2", swing_v="1"))
    assert values["off_hours"] == 12
    for name in (
        "curr_hours",
        "curr_mins",
        "off_timer",
        "on_timer",
        "off_mins",
        "on_hours",
        "on_mins",
    ):
        assert values[name] == 0, name


@pytest.mark.parametrize(
    "previous",
    [
        None,
        HvacState(False, "heat", 18.0),
        HvacState(True, "cool", 26.0, fan="1", swing_v="off"),
        HvacState(True, "cool", 22.0, fan="3", swing_v="1"),
    ],
)
def test_previous_is_ignored(previous):
    # No toggle bits, and IRac::handleToggles has no HAIER_AC case: the C
    # path never derives the button from a previous state.
    dev = device()
    target = HvacState(True, "cool", 22.0, fan="3", swing_v="1")
    assert dev.encode(previous, target).signal == dev.encode(None, target).signal


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:4] == (3000, 3000, 3000, 4300)
    assert pulses[-2:] == (520, 150000)
    assert len(pulses) == 4 + 2 * 72 + 2


@pytest.mark.parametrize("model", HAIER_AC_MODELS)
def test_swing_v_offers_every_documented_value(model):
    # kHaierAcSwingV{Off,Chg,Up,Down}: Chg ("auto", 0b11) is new, the legacy
    # entity had off, "auto high" (Up) and "auto low" (Down).
    swing_v = device(model).capabilities.swing_v
    assert swing_v.values == ("off", "auto", "1", "2")
    assert swing_v.label("1") == "auto high" and swing_v.label("2") == "auto low"


def test_swing_change_matches_the_libraries_message_construction():
    # ir_Haier_test.cpp TestHaierACClass.MessageConstuction: setSwingV(
    # kHaierAcSwingVChg) gives byte 2 = 0xEA there (SwingV 0b11 over the
    # constant bit 5 and the clock); with the clock at 0, byte 2 is 0xE0.
    assert data(HvacState(True, "cool", 21.0, swing_v="auto"))[2] == 0xE0


def test_capabilities():
    caps = device().capabilities
    assert caps.modes == ("auto", "cool", "dry", "heat", "fan")
    assert (caps.temperature.min, caps.temperature.max) == (16.0, 30.0)
    assert caps.fan.values == ("auto", "1", "2", "3")
    assert caps.swing_h is None
    assert set(caps.features) == {"purifier", "sleep"}


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(r for r in load_oracle("HAIER_AC") if r["state"].get("sleep") == "on")
    with pytest.raises(AssertionError, match="sleep"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("HAIER_AC")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)
