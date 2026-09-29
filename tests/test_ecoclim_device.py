import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.ir.codec import decode
from pyhvac.plugins.ecoclim import ECOCLIM_LAYOUT, ECOCLIM_MODELS, EcoclimDevice
from pyhvac.state import HvacState

# The C path deviates from the documented EcoClim values here:
# - IRac::sendAc passes send.iFeel (false, 0) as IRac::ecoclim's sleep
#   minutes, and sleep >= 0 selects kEcoclimSleep: every C message is mode
#   sleep (7), whatever the requested mode, off messages included. Oracle off
#   records read as mode auto, so they are covered by the auto entry.
DEFECTS = tuple(
    Defect("mode", mode, "sleep", "IRac::sendAc passes iFeel as sleep")
    for mode in ("auto", "cool", "dry", "fan", "heat")
)


def device():
    return EcoclimDevice("ecoclim", "generic")


def state(power=True, mode="cool", temperature=22.0, **kw):
    return device().normalise(HvacState(power, mode, temperature, **kw))


def frames(target, previous=None):
    return device().frames(previous, target, ())


def read(target, previous=None):
    return ECOCLIM_LAYOUT.read(frames(target, previous)[0].data)


@pytest.mark.parametrize("record", oracle_params("ECOCLIM"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("ECOCLIM"):
        for frame in dev.frames(None, state_from_record(dev, record["state"]), ()):
            values = ECOCLIM_LAYOUT.read(frame.data)
            assert ECOCLIM_LAYOUT.build(**values) == bytearray(frame.data)


def test_the_three_copies_are_identical():
    # sendEcoclim sends the same word in every section.
    first, second, last = frames(state(True, "heat", 27.0, fan="2"))
    assert [f.section for f in (first, second, last)] == ["first", "second", "last"]
    assert first.data == second.data == last.data


# ir_Ecoclim_test.cpp, RealExample: the two 56-bit captures, and
# kEcoclimDefaultState (HumanReadable).
CAPTURES = [
    (
        0x110673AEFFFF72,
        {
            "power": 1,
            "mode": "auto",
            "temperature": 11,
            "sensor_temperature": 22,
            "fan": "auto",
            "clock": 15 * 60 + 42,
            "on_hours": 0x1F,
            "on_ten_minutes": 7,
            "off_hours": 0x1F,
            "off_ten_minutes": 7,
            "dip_config": "slave",
        },
    ),
    (
        0x15594507FFFF0A,
        {
            "power": 1,
            "mode": "dry",
            "temperature": 30,
            "sensor_temperature": 26,
            "fan": "1",
            "clock": 21 * 60 + 27,
            "on_hours": 0x1F,
            "off_hours": 0x1F,
            "dip_config": "master",
        },
    ),
    (
        0x11063000FFFF02,
        {
            "power": 0,
            "mode": "auto",
            "temperature": 11,
            "sensor_temperature": 22,
            "fan": "auto",
            "clock": 0,
            "dip_config": "master",
        },
    ),
]


@pytest.mark.parametrize("raw, fields", CAPTURES)
def test_layout_reads_the_real_captures(raw, fields):
    data = raw.to_bytes(7, "big")
    values = ECOCLIM_LAYOUT.read(data)
    assert {k: values[k] for k in fields} == fields
    assert ECOCLIM_LAYOUT.build(**values) == bytearray(data)


@pytest.mark.parametrize(
    "raw, target, differing",
    [
        # The entity has no sensor reading, clock or DIP setting: the port
        # sends the setpoint, 00:00 and master there.
        (
            0x110673AEFFFF72,
            state(True, "auto", 11.0, fan="auto"),
            {"sensor_temperature", "clock", "dip_config"},
        ),
        # The unknown bit next to DipConfig is set in this capture only.
        (
            0x15594507FFFF0A,
            state(True, "dry", 30.0, fan="1"),
            {"sensor_temperature", "clock", "unknown_type"},
        ),
    ],
)
def test_port_reproduces_the_real_captures_but_what_it_cannot_express(
    raw, target, differing
):
    capture = raw.to_bytes(7, "big")
    ours = frames(target)[0].data
    a, b = ECOCLIM_LAYOUT.read(ours), ECOCLIM_LAYOUT.read(capture)
    assert {k for k in a if a[k] != b[k]} == differing
    patched = bytearray(ours)
    for name in differing:
        ECOCLIM_LAYOUT.write_raw(patched, name, ECOCLIM_LAYOUT.read_raw(capture, name))
    assert bytes(patched) == capture


def test_port_reproduces_the_default_state_but_the_setpoint():
    # kEcoclimDefaultState: off, auto, 11C, sensor 22C, fan auto. The port
    # sends the setpoint as the sensor temperature.
    ours = frames(state(False, "auto", 11.0, fan="auto"))[0].data
    expected = bytearray((0x11063000FFFF02).to_bytes(7, "big"))
    ECOCLIM_LAYOUT.write_raw(expected, "sensor_temperature", 11 - 5)
    assert ours == bytes(expected)


@pytest.mark.parametrize("power", [True, False])
@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan", "heat"])
@pytest.mark.parametrize("t", [float(x) for x in range(5, 32)])
def test_setpoint_and_sensor_temperature_are_the_target(power, mode, t):
    # IRac::ecoclim sets SensorTemp to the setpoint without a sensor reading
    # (the oracle records show it at 5, 18 and 31C in every mode, on and off).
    values = read(state(power, mode, t))
    assert values["temperature"] == int(t)
    assert values["sensor_temperature"] == int(t)


@pytest.mark.parametrize(
    "mode, code", [("auto", 0), ("cool", 1), ("dry", 2), ("fan", 4), ("heat", 5)]
)
def test_mode_uses_its_documented_value(mode, code):
    first, _, _ = frames(state(True, mode))
    assert ECOCLIM_LAYOUT.read_raw(first.data, "mode") == code


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan", "heat"])
def test_off_carries_mode_auto_and_power_off(mode):
    values = read(state(False, mode, 25.0))
    assert (values["power"], values["mode"]) == (0, "auto")


def test_on_sets_the_power_bit():
    assert read(state(True, "cool"))["power"] == 1


@pytest.mark.parametrize("fan, raw", [("1", 0), ("2", 1), ("3", 2), ("auto", 3)])
def test_every_fan_level_uses_its_documented_code(fan, raw):
    # kEcoclimFanMin/Med/Max/Auto; the oracle records show the same codes.
    first, _, _ = frames(state(fan=fan))
    assert ECOCLIM_LAYOUT.read_raw(first.data, "fan") == raw


@pytest.mark.parametrize("power", [True, False])
def test_unset_fields_keep_the_default_state(power):
    # Clock 00:00, both timers disabled, DIP master, as in
    # kEcoclimDefaultState and every oracle record.
    values = read(state(power, "heat", 30.0, fan="3"))
    assert values["clock"] == 0
    assert (values["on_hours"], values["on_ten_minutes"]) == (0x1F, 7)
    assert (values["off_hours"], values["off_ten_minutes"]) == (0x1F, 7)
    assert values["dip_config"] == "master"
    for name in ("unknown_clock", "unknown_type", "clear"):
        assert values[name] == 0, name


def test_previous_is_ignored():
    target = state(True, "cool", 22.0)
    for previous in (None, state(False, "heat", 30.0, fan="1"), target):
        assert frames(target, previous) == frames(target)


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (5730, 1935)
    assert pulses[-2:] == (7820, 100000)
    assert len(pulses) == 3 * (2 + 2 * 56) + 2
    record = load_oracle("ECOCLIM")[0]
    assert len(pulses) == len(record["pulses"])


@pytest.mark.parametrize("model", ECOCLIM_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("ecoclim", model), EcoclimDevice)


@pytest.mark.parametrize("model", ECOCLIM_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.ecoclim import Ecoclim

    legacy = LegacyDevice("ecoclim", model, Ecoclim)
    assert EcoclimDevice("ecoclim", model).capabilities == legacy.capabilities


@pytest.mark.parametrize("mode", ["off", "auto", "cool", "dry", "fan", "heat"])
def test_undeclared_mode_deviation_is_reported(mode):
    dev = device()
    record = next(r for r in load_oracle("ECOCLIM") if r["state"]["mode"] == mode)
    with pytest.raises(AssertionError, match="mode"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_every_c_message_is_mode_sleep():
    # The mode defect: C's frames read as sleep in every oracle record.
    dev = device()
    for record in load_oracle("ECOCLIM"):
        names = [f.section for f in dev.frames(None, state(), ())]
        for frame in decode(dev.PROTOCOL, record["pulses"], expected=names):
            assert ECOCLIM_LAYOUT.read(frame.data)["mode"] == "sleep"


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("ECOCLIM")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)
