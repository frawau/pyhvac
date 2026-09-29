import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.ir.codec import decode
from pyhvac.plugins.trotech import (
    TROTEC3550,
    TROTEC3550_LAYOUT,
    TROTEC3550_MODELS,
    Trotec3550Device,
)
from pyhvac.state import HvacState

# The C path never sends swing on: IRGHVAC.trans_swing has no "on" key, so
# the lookup error is swallowed, IRac::trotec3550 gets swingv kOff and
# setSwingV(swingv != kOff) clears the SwingV bit. The port sends the bit.
DEFECTS = (Defect("swing_v", "swing", "off", "C glue has no swing 'on' key"),)

# Real captures from ir_Trotec_test.cpp (issue #1563 and its spreadsheet).
ON_COOL_18_HIGH_SWING = bytes.fromhex("552300050000318836")
OFF_COOL_18_HIGH_SWING = bytes.fromhex("552100050000318834")
DEG_79F = bytes.fromhex("55a30014000031407d")
ONE_HOUR_TIMER = bytes.fromhex("55bb01150000310259")
RESET = bytes.fromhex("5560000d000010885a")  # kReset


def device(model="PAC 3550 Pro"):
    return Trotec3550Device("trotech", model)


def read(state, previous=None):
    dev = device()
    if previous is not None:
        previous = dev.normalise(previous)
    (main,) = dev.frames(previous, dev.normalise(state), ())
    return TROTEC3550_LAYOUT.read(main.data)


def data(state):
    dev = device()
    (main,) = dev.frames(None, dev.normalise(state), ())
    return main.data


@pytest.mark.parametrize("record", oracle_params("TROTEC_3550"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("TROTEC_3550"):
        state = state_from_record(dev, record["state"])
        (main,) = dev.frames(None, state, ())
        values = TROTEC3550_LAYOUT.read(main.data)
        assert TROTEC3550_LAYOUT.build(**values) == bytearray(main.data)
        assert TROTEC3550_LAYOUT.checksum.check(main.data)


def test_every_oracle_message_is_one_frame():
    for record in load_oracle("TROTEC_3550"):
        (main,) = decode(TROTEC3550, record["pulses"], ["main"])
        assert main.data[0] == 0x55  # Intro


def test_the_port_reproduces_the_issue_1563_on_capture():
    # "On, Cool, 18C, Fan 3 (High), Swing(V) On": the remote's own frame.
    state = HvacState(True, "cool", 18.0, fan="3", swing_v="swing")
    assert data(state) == ON_COOL_18_HIGH_SWING


@pytest.mark.parametrize(
    "capture, expected",
    [
        (
            OFF_COOL_18_HIGH_SWING,
            {"power": 0, "mode": "cool", "temperature": 18, "swing_v": "swing"},
        ),
        (DEG_79F, {"celsius": 0, "temp_f": 79 - 59, "fan": "3"}),
        (ONE_HOUR_TIMER, {"timer_set": 1, "timer_hours": 1, "celsius": 0}),
    ],
)
def test_real_captures_read_back(capture, expected):
    # The remote's off frame keeps the mode (the C path, and so the port,
    # sends auto), and the Fahrenheit/timer frames are beyond the entity.
    values = TROTEC3550_LAYOUT.read(capture)
    assert TROTEC3550_LAYOUT.checksum.check(capture)
    assert {k: values[k] for k in expected} == expected


def test_reset_state_is_the_skeleton():
    # kReset: the "modeauto" frame of HumanReadable.
    assert TROTEC3550_LAYOUT.build() == bytearray(RESET)


def test_message_shape():
    signal = device().encode(None, HvacState(True, "cool", 22.0, fan="1")).signal
    assert signal.carrier == 38000
    assert signal.pulses[:2] == (12000, 5130)  # kTrotec3550HdrMark/HdrSpace
    assert signal.pulses[-2:] == (550, 100000)  # kDefaultMessageGap
    assert len(signal.pulses) == 2 + 2 * 72 + 2


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan"])
@pytest.mark.parametrize("t", [16.0, 23.0, 30.0])
def test_off_carries_mode_auto_and_power_off(mode, t):
    # IRac passes mode "off"; convertMode maps it to kTrotecAuto.
    values = read(HvacState(False, mode, t, fan="3", swing_v="swing"))
    assert (values["power"], values["mode"]) == (0, "auto")
    assert (values["temperature"], values["fan"], values["swing_v"]) == (
        int(t),
        "3",
        "swing",
    )


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan"])
def test_on_sends_the_mode(mode):
    values = read(HvacState(True, mode, 25.0, fan="2"))
    assert (values["power"], values["mode"]) == (1, mode)


@pytest.mark.parametrize("t", range(16, 31))
def test_setpoint_is_celsius_with_the_truncated_fahrenheit(t):
    # IRac passes celsius true: setTemp stores TempC, sets Celsius, and
    # stores celsiusToFahrenheit(t) - kTrotec3550MinTempF, truncated.
    values = read(HvacState(True, "cool", float(t), fan="1"))
    assert (values["temperature"], values["celsius"]) == (t, 1)
    assert values["temp_f"] == int(t * 1.8 + 32 + 1e-9) - 59


@pytest.mark.parametrize("fan, raw", [("1", 1), ("2", 2), ("3", 3)])
def test_every_fan_level(fan, raw):
    raw_read = TROTEC3550_LAYOUT.read_raw(
        data(HvacState(True, "cool", 22.0, fan=fan)), "fan"
    )
    assert raw_read == raw


@pytest.mark.parametrize("swing, bit", [("off", 0), ("swing", 1)])
def test_every_swing_value(swing, bit):
    raw = data(HvacState(True, "cool", 22.0, fan="2", swing_v=swing))
    assert raw[1] & 0x01 == bit  # SwingV: byte 1 bit 0


def test_timer_is_never_set():
    # IRac::trotec3550 has no timer: kReset's zeros are sent.
    values = read(HvacState(True, "dry", 18.0, fan="3", swing_v="swing"))
    assert (values["timer_set"], values["timer_hours"]) == (0, 0)


@pytest.mark.parametrize(
    "previous",
    [
        None,
        HvacState(False, "cool", 22.0, fan="3"),
        HvacState(True, "cool", 26.0, fan="1", swing_v="swing"),
        HvacState(True, "cool", 22.0, fan="3", swing_v="off"),
    ],
)
def test_previous_is_ignored(previous):
    # No toggle bits, and IRac::handleToggles has no TROTEC_3550 case.
    dev = device()
    target = HvacState(True, "cool", 22.0, fan="3", swing_v="swing")
    assert dev.encode(previous, target).signal == dev.encode(None, target).signal


@pytest.mark.parametrize("model", TROTEC3550_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("trotech", model), Trotec3550Device)


@pytest.mark.parametrize("model", TROTEC3550_MODELS)
def test_capabilities_are_the_documented_values(model):
    # Unchanged by the audit: the legacy entity already offered every
    # documented Trotec3550Protocol value.
    caps = device(model).capabilities
    # kTrotec3550MinTempC / kTrotec3550MaxTempC, whole degrees.
    assert (caps.temperature.min, caps.temperature.max) == (16.0, 30.0)
    assert caps.modes == ("auto", "cool", "dry", "fan")
    assert caps.fan.values == ("1", "2", "3")  # no auto code
    assert caps.swing_v.values == ("off", "swing")  # the SwingV bit
    assert caps.swing_h is None
    assert dict(caps.features) == {}


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(
        r for r in load_oracle("TROTEC_3550") if r["state"].get("swing") == "on"
    )
    with pytest.raises(AssertionError, match="swing_v"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("TROTEC_3550")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)
