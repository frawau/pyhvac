import pytest

from c_oracle import c_frozen

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac.ir.codec import decode
from pyhvac.protocols.eurom import EUROM, EUROM_LAYOUT, EUROM_MODELS, EuromDevice
from pyhvac.state import HvacState

# The C path deviates from the documented Eurom values here:
# - swing: IRGHVAC.trans_swing has no "on" key, so the lookup error is
#   swallowed, IRac::eurom gets swingv kOff and convertSwing gives false. The
#   port sets kEuromSwingOn.
# - sleep: IRac::eurom declares sleep as a bool, so IRac's int16 "off" (-1)
#   becomes true and every C message carries kEuromSleepEnabled (the old glue
#   never passes sleep, so IRac always has -1). The port sends
#   kEuromSleepOnTimerDisabled for sleep off.
DEFECTS = (
    Defect("swing_v", "swing", "off", "C glue has no swing 'on' key"),
    Defect("sleep", 0, 1, "IRac::eurom turns sleep -1 (off) into true"),
)

# Real captures from ir_Eurom_test.cpp.
SEND_DATA_ONLY = bytes.fromhex("1827718000000080008010" "21")  # on, cool 23
REAL_EXAMPLE = bytes.fromhex("182771c000000080008010" "25")  # + swing on
REAL_EXAMPLE_NO_REPEAT = bytes.fromhex("1827510000000080008010" "17")  # off
CHECKSUM_INITIAL = bytes.fromhex("1827710000000080008010" "19")  # stateReset
CHECKSUM_HIGH = bytes.fromhex("18270cc05e6400a4808040" "57")  # every max


def device(model="Polar 16CH"):
    return EuromDevice("eurom", model)


def data(state, previous=None):
    dev = device()
    if previous is not None:
        previous = dev.normalise(previous)
    (main,) = dev.frames(previous, dev.normalise(state), ())
    return main.data


def read(state):
    return EUROM_LAYOUT.read(data(state))


def on(mode="cool", t=24.0, fan="1", swing="off", sleep=False, power=True):
    return HvacState(power, mode, t, fan=fan, swing_v=swing, features={"sleep": sleep})


@pytest.mark.parametrize("record", oracle_params("EUROM"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("EUROM"):
        (main,) = dev.frames(None, state_from_record(dev, record["state"]), ())
        values = EUROM_LAYOUT.read(main.data)
        assert EUROM_LAYOUT.build(**values) == bytearray(main.data)
        assert EUROM_LAYOUT.checksum.check(main.data)


def test_every_oracle_message_is_one_frame():
    for record in load_oracle("EUROM"):
        (main,) = decode(EUROM, record["pulses"], ["main"])
        assert main.data[:2] == b"\x18\x27"  # Sum1, Sum2


def test_port_reproduces_the_send_data_only_capture():
    assert data(on("cool", 23.0)) == SEND_DATA_ONLY


def test_port_reproduces_the_real_example_capture():
    # "Power: On, Mode: 1 (Cool), Temp: 23C, Fan: 16 (Low), Swing(V): On".
    assert data(on("cool", 23.0, swing="swing")) == REAL_EXAMPLE


@pytest.mark.parametrize(
    "capture, expected",
    [
        (
            REAL_EXAMPLE_NO_REPEAT,
            {"power": 0, "mode": "cool", "temperature": 21 - 16, "fan": "1"},
        ),
        (
            CHECKSUM_INITIAL,
            {"power": 0, "mode": "cool", "temperature": 23 - 16, "sleep": 0},
        ),
        (
            CHECKSUM_HIGH,
            {
                "power": 1,
                "mode": "heat",
                "max_temperature": 1,
                "temperature": 0,
                "swing_v": "swing",
                "fahrenheit": 0x04 + 90,  # kEuromFahrenheitEnabled + 90 F
                "sleep": 1,
                "on_timer": 0x24,  # BCD 24 h
                "off_timer": 0x24,
                "off_timer_enabled": 1,
                "fan": "3",
            },
        ),
    ],
)
def test_real_captures_read_back(capture, expected):
    # The remote's off frame keeps cool at 21 C (the C path, and so the port,
    # sends fan mode: see test_off_carries_mode_fan); the Fahrenheit and
    # timer frame is beyond the entity. The checksum matches calcChecksum.
    values = EUROM_LAYOUT.read(capture)
    assert {k: values[k] for k in expected} == expected
    assert EUROM_LAYOUT.checksum.check(capture)
    assert EUROM_LAYOUT.build(**values) == bytearray(capture)


def test_message_shape():
    signal = device().encode(None, on()).signal
    assert signal.carrier == 38000
    assert signal.pulses[:2] == (3257, 3187)  # kEuromHdrMark/HdrSpace
    assert signal.pulses[-2:] == (454, 50058)  # kEuromBitMark, kEuromSpaceGap
    assert len(signal.pulses) == 2 + 2 * 96 + 2


@pytest.mark.parametrize("mode", ["cool", "heat", "fan", "dry"])
@pytest.mark.parametrize("t", [16.0, 24.0, 32.0])
def test_off_carries_mode_fan(mode, t):
    # IRac passes mode "off"; convertMode maps it to kEuromVentilate (0x73).
    raw = data(on(mode, t, fan="3", swing="swing", sleep=True, power=False))
    assert raw[2] == 0x73
    values = EUROM_LAYOUT.read(raw)
    assert (values["power"], values["fan"], values["swing_v"], values["sleep"]) == (
        0,
        "3",
        "swing",
        1,
    )


@pytest.mark.parametrize("mode, code", [("cool", 0x01), ("heat", 0x04)])
@pytest.mark.parametrize("t", range(16, 32))
def test_setpoint_goes_in_the_high_nibble(mode, code, t):
    # getModeCelsiusByte: mode | (celsius - kEuromMinTempC) << 4.
    assert data(on(mode, float(t)))[2] == code | (t - 16) << 4


@pytest.mark.parametrize("mode, byte", [("cool", 0x09), ("heat", 0x0C)])
def test_32_is_the_max_temperature_flag(mode, byte):
    # getModeCelsiusByte: mode | kEuromMaxTempFlag at kEuromMaxTempC.
    assert data(on(mode, 32.0))[2] == byte


@pytest.mark.parametrize("mode, byte", [("dry", 0x72), ("fan", 0x73)])
@pytest.mark.parametrize("t", [16.0, 24.0, 32.0])
def test_dry_and_fan_carry_no_setpoint(mode, byte, t):
    # kEuromDehumidify / kEuromVentilate; setTemp returns early in them.
    assert data(on(mode, t))[2] == byte


@pytest.mark.parametrize("mode", ["cool", "heat", "fan", "dry"])
def test_on_sets_the_power_bit(mode):
    assert read(on(mode))["power"] == 1


@pytest.mark.parametrize("fan, raw", [("1", 0x10), ("2", 0x20), ("3", 0x40)])
def test_every_fan_level(fan, raw):
    assert data(on(fan=fan))[10] == raw  # kEuromFan{Low,Med,High}


@pytest.mark.parametrize("power", [True, False])
@pytest.mark.parametrize("swing, bits", [("off", 0x00), ("swing", 0x40)])
def test_every_swing_value(power, swing, bits):
    # Power_Swing: kEuromPowerOn | kEuromSwingOn.
    assert data(on(swing=swing, power=power))[3] == (0x80 if power else 0) | bits


@pytest.mark.parametrize("sleep, byte", [(False, 0x00), (True, 0x40)])
def test_sleep_sends_the_documented_byte(sleep, byte):
    # kEuromSleepOnTimerDisabled / kEuromSleepEnabled, no on timer.
    assert data(on(sleep=sleep))[5] == byte


def test_fahrenheit_and_timers_are_never_set():
    # IRac passes celsius, and IRac::eurom sets no timer.
    values = read(on("heat", 32.0, fan="3", swing="swing", sleep=True))
    assert values["fahrenheit"] == 0
    assert (values["on_timer"], values["off_timer"], values["off_timer_enabled"]) == (
        0,
        0,
        0,
    )


@pytest.mark.parametrize(
    "previous",
    [
        None,
        on(power=False),
        on("heat", 30.0, fan="3", swing="swing"),
        on(sleep=True),
    ],
)
def test_previous_is_ignored(previous):
    # No toggle bits, and IRac::handleToggles has no EUROM case.
    dev = device()
    target = on("cool", 22.0, fan="2", swing="swing")
    assert dev.encode(previous, target).signal == dev.encode(None, target).signal


@pytest.mark.parametrize("sleep, bit", [(-1, 1), (0, 0), (30, 1)])
def test_c_path_turns_irac_sleep_into_a_bool(sleep, bit):
    # IRac::eurom's bool sleep: IRac's "off" (-1) sends kEuromSleepEnabled,
    # and sleep from minute 0 sends it disabled.
    def live():
        from pyhvac.protocols.eurom import Eurom

        legacy = Eurom()
        legacy.irac.next.sleep = sleep
        legacy.to_set = {"mode": "cool", "temperature": 24, "fan": "low"}
        return [int(x) for x in legacy.to_lirc(legacy.build_ircode())]

    pulses = c_frozen(["irac sleep", sleep], live)
    (main,) = decode(EUROM, pulses, ["main"])
    assert EUROM_LAYOUT.read(main.data)["sleep"] == bit


def test_undeclared_swing_deviation_is_reported():
    dev = device()
    record = next(r for r in load_oracle("EUROM") if r["state"].get("swing") == "on")
    defects = [d for d in DEFECTS if d.field != "swing_v"]
    with pytest.raises(AssertionError, match="swing_v"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects)


def test_undeclared_sleep_deviation_is_reported():
    dev = device()
    record = next(r for r in load_oracle("EUROM") if r["state"].get("sleep") != "on")
    defects = [d for d in DEFECTS if d.field != "sleep"]
    with pytest.raises(AssertionError, match="sleep"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects)


def test_sleep_on_needs_no_sleep_defect():
    # C's sleep bit is always set, so the sleep "on" record matches it.
    dev = device()
    record = next(r for r in load_oracle("EUROM") if r["state"].get("sleep") == "on")
    assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("EUROM")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)


def test_capabilities_are_the_headers():
    # ir_Eurom.h: kEuromMinTempC/MaxTempC 16-32; kEuromFan{Low,Med,High} (no
    # auto); kEuromCool/Heat/Dehumidify/Ventilate; kEuromSwingOn;
    # kEuromSleepEnabled.
    caps = device().capabilities
    assert set(caps.modes) == {"cool", "heat", "fan", "dry"}
    assert (caps.temperature.min, caps.temperature.max) == (16.0, 32.0)
    assert caps.fan.values == ("1", "2", "3")
    assert caps.swing_v.values == ("off", "swing")
    assert set(caps.features) == {"sleep"}
