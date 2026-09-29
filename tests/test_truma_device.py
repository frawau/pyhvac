import re

import pytest

from oracle import load_oracle
from port_oracle import assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.ir.codec import decode
from pyhvac.plugins.truma import (
    TRUMA,
    TRUMA_LAYOUT,
    TRUMA_MODELS,
    TrumaChecksum,
    TrumaDevice,
)
from pyhvac.state import HvacState

# No Defects: the C path sends the documented Truma values for every state
# the entity can express.

# ir_Truma_test.cpp: RealExample (a remote capture, 16C auto high), the
# HumanReadableOutput frames (from the protocol's capture spreadsheet) and
# the KnownMessageConstuction off frame.
ON_16_AUTO_HIGH = 0x49FFFFFFE6E081
ON_25_AUTO_HIGH = 0x52FFFFFFEFE081
ON_17_COOL_MED = 0x54FFFFFFE7EA81
OFF_16_AUTO_HIGH = 0x50FFFFFFE6E781

# ir_Truma_test.cpp SyntheticExample: sendTruma(0x49ffffffe6e081).
SYNTHETIC_OUTPUT = (
    "m20200s1000"
    "m1800s630"
    "m600s630m1200s630m1200s630m1200s630m1200s630m1200s630m1200s630m600s630"
    "m1200s630m1200s630m1200s630m1200s630m1200s630m600s630m600s630m600s630"
    "m1200s630m600s630m600s630m1200s630m1200s630m600s630m600s630m600s630"
    "m600s630m600s630m600s630m600s630m600s630m600s630m600s630m600s630"
    "m600s630m600s630m600s630m600s630m600s630m600s630m600s630m600s630"
    "m600s630m600s630m600s630m600s630m600s630m600s630m600s630m600s630"
    "m600s630m1200s630m1200s630m600s630m1200s630m1200s630m600s630m1200s630"
    "m600s100000"
)


def _with_c_defaults(record):
    # A record without "fan" relied on IRac's default (kAuto), which
    # IRTrumaAc::convertFan sends as kTrumaFanHigh, labelled "high".
    return {**record, "state": {"fan": "high", **record["state"]}}


def device(model="Aventa"):
    return TrumaDevice("truma", model)


def state(power=True, mode="cool", temperature=22.0, **kw):
    return device().normalise(HvacState(power, mode, temperature, **kw))


def data(target, previous=None):
    (main,) = device().frames(previous, target, ())
    return main.data


def read(target):
    return TRUMA_LAYOUT.read(data(target))


def raw(value):
    return value.to_bytes(7, "little")


@pytest.mark.parametrize("record", oracle_params("TRUMA"))
def test_matches_c_library(record):
    dev = device(record["model"])
    assert_matches_oracle(dev, _with_c_defaults(record), dev.LAYOUTS, defects=())


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("TRUMA"):
        target = state_from_record(dev, _with_c_defaults(record)["state"])
        (main,) = dev.frames(None, target, ())
        values = TRUMA_LAYOUT.read(main.data)
        assert TRUMA_LAYOUT.build(**values) == bytearray(main.data)
        assert TRUMA_LAYOUT.checksum.check(main.data)


def test_every_oracle_message_keeps_the_fixed_bytes():
    for record in load_oracle("TRUMA"):
        (main,) = decode(TRUMA, record["pulses"], ["main"])
        assert main.data[0] == 0x81 and main.data[3:6] == b"\xff\xff\xff"
        assert main.data[1] >> 6 == 0b11 and main.data[2] >> 5 == 0b111


@pytest.mark.parametrize(
    "value, fields",
    [
        (
            ON_16_AUTO_HIGH,
            {"mode": "auto", "power_off": 0, "temperature": 16, "fan": "3"},
        ),
        (
            ON_25_AUTO_HIGH,
            {"mode": "auto", "power_off": 0, "temperature": 25, "fan": "3"},
        ),
        (
            ON_17_COOL_MED,
            {"mode": "cool", "power_off": 0, "temperature": 17, "fan": "2"},
        ),
        (
            OFF_16_AUTO_HIGH,
            {"mode": "fan", "power_off": 1, "temperature": 16, "fan": "3"},
        ),
    ],
)
def test_layout_reads_the_real_captures(value, fields):
    values = TRUMA_LAYOUT.read(raw(value))
    assert values == fields
    assert TRUMA_LAYOUT.build(**values) == bytearray(raw(value))


@pytest.mark.parametrize(
    "target, value",
    [
        (HvacState(True, "auto", 16.0, fan="3"), ON_16_AUTO_HIGH),
        (HvacState(True, "auto", 25.0, fan="3"), ON_25_AUTO_HIGH),
        (HvacState(True, "cool", 17.0, fan="2"), ON_17_COOL_MED),
        (HvacState(False, "auto", 16.0, fan="3"), OFF_16_AUTO_HIGH),
    ],
)
def test_port_reproduces_the_real_captures(target, value):
    assert data(device().normalise(target)) == raw(value)


def test_port_reproduces_the_synthetic_pulses():
    expected = tuple(int(d) for d in re.findall(r"\d+", SYNTHETIC_OUTPUT))
    signal = device().encode(None, HvacState(True, "auto", 16.0, fan="3")).signal
    assert signal.carrier == 38000
    assert signal.pulses == expected


def test_checksum_is_the_byte_sum_plus_five():
    # ir_Truma_test.cpp Checksums: 0x52 for 0x52FFFFFFEFE081.
    checksum = TrumaChecksum(0, 6, 6)
    assert checksum.compute(raw(0x52FFFFFFEFE081)) == 0x52
    assert checksum.check(raw(0x52FFFFFFEFE081))
    assert not checksum.check(raw(0x51FFFFFFEFE081))


@pytest.mark.parametrize("mode", ["auto", "cool", "fan"])
@pytest.mark.parametrize("t", range(16, 32))
def test_every_setpoint_is_sent(mode, t):
    assert read(state(True, mode, float(t)))["temperature"] == t


@pytest.mark.parametrize("t, sent", [(10.0, 16), (15.0, 16), (32.0, 31), (40.0, 31)])
def test_setpoint_is_clamped_to_the_documented_range(t, sent):
    # kTrumaMinTemp/kTrumaMaxTemp, as IRTrumaAc::setTemp clamps.
    assert read(state(True, "cool", t))["temperature"] == sent


@pytest.mark.parametrize("mode", ["auto", "cool", "fan"])
@pytest.mark.parametrize("fan, code", [("1", 6), ("2", 5), ("3", 4)])
def test_every_fan_level_uses_its_documented_code(mode, fan, code):
    # kTrumaFanLow/Med/High.
    target = state(True, mode, fan=fan)
    assert TRUMA_LAYOUT.read_raw(data(target), "fan") == code


@pytest.mark.parametrize("mode, code", [("auto", 0), ("cool", 2), ("fan", 3)])
def test_mode_uses_its_documented_value(mode, code):
    target = state(True, mode)
    assert TRUMA_LAYOUT.read_raw(data(target), "mode") == code
    assert read(target)["power_off"] == 0


@pytest.mark.parametrize("fan", ["1", "2", "3"])
def test_quiet_in_cool_sends_the_quiet_fan_code(fan):
    # IRTrumaAc::setQuiet: kTrumaFanQuiet (3), in cool only.
    target = state(True, "cool", fan=fan, features={"quiet": True})
    assert TRUMA_LAYOUT.read_raw(data(target), "fan") == 3


@pytest.mark.parametrize("mode", ["auto", "fan"])
@pytest.mark.parametrize("fan", ["1", "2", "3"])
def test_quiet_outside_cool_keeps_the_fan_speed(mode, fan):
    target = state(True, mode, fan=fan, features={"quiet": True})
    assert read(target)["fan"] == fan
    quiet_off = state(True, mode, fan=fan, features={"quiet": False})
    assert data(target) == data(quiet_off)


@pytest.mark.parametrize("mode", ["auto", "cool", "fan"])
@pytest.mark.parametrize("fan", ["1", "2", "3"])
@pytest.mark.parametrize("quiet", [False, True])
@pytest.mark.parametrize("t", [16.0, 31.0])
def test_off_carries_mode_fan_and_the_target_setpoint_and_fan(mode, fan, quiet, t):
    # IRTrumaAc::setPower: "Off temporarily sets mode to Fan"; quiet is not
    # sent (setQuiet sees mode fan), as in the real off capture.
    target = state(False, mode, t, fan=fan, features={"quiet": quiet})
    assert read(target) == {
        "mode": "fan",
        "power_off": 1,
        "fan": fan,
        "temperature": int(t),
    }


def test_previous_is_ignored():
    # No toggle bits; IRac builds a fresh IRTrumaAc for every message.
    dev = device()
    target = HvacState(True, "cool", 22.0, fan="2")
    for previous in (
        HvacState(False, "auto", 16.0, fan="1"),
        HvacState(True, "cool", 22.0, fan="2"),
    ):
        assert dev.encode(previous, target).signal == dev.encode(None, target).signal


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0, fan="1")).signal
    pulses = pulses.pulses
    assert pulses[:4] == (20200, 1000, 1800, 630)
    assert pulses[-2:] == (600, 100000)
    assert len(pulses) == 4 + 2 * 56 + 2


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("TRUMA")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, ())


@pytest.mark.parametrize("model", TRUMA_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("truma", model), TrumaDevice)


@pytest.mark.parametrize("model", TRUMA_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.truma import Truma

    legacy = LegacyDevice("truma", model, Truma)
    assert TrumaDevice("truma", model).capabilities == legacy.capabilities
