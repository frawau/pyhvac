import pytest

from oracle import load_oracle
from port_oracle import assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.ir.codec import decode
from pyhvac.plugins.amcor import (
    AMCOR,
    AMCOR_LAYOUT,
    AMCOR_MODELS,
    AmcorDevice,
)
from pyhvac.state import HvacState

# No declared Defects: the C path sends the documented AmcorProtocol values
# for every state the entity can express.

# ir_Amcor_test.cpp, DecodeRealExample (issue #834, captured by ldellus):
# "Turn on, cooling, 27 deg C", fan auto; and the second capture of the same
# test (issue #834, comment 515700254): on, cool, 12 C, fan auto.
REAL_EXAMPLE_27 = bytes.fromhex("0141360000300012")
REAL_EXAMPLE_12 = bytes.fromhex("0141180000300012")


def device(model="generic"):
    return AmcorDevice("amcor", model)


def frames(state, previous=None):
    dev = device()
    if previous is not None:
        previous = dev.normalise(previous)
    return dev.frames(previous, dev.normalise(state), ())


def frame(state):
    first, second = frames(state)
    assert first == second
    return first.data


def read(state):
    return AMCOR_LAYOUT.read(frame(state))


@pytest.mark.parametrize("record", oracle_params("AMCOR"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("AMCOR"):
        state = state_from_record(dev, record["state"])
        for f in dev.frames(None, state, ()):
            values = AMCOR_LAYOUT.read(f.data)
            assert AMCOR_LAYOUT.build(**values) == bytearray(f.data)


def test_every_oracle_message_is_one_frame_sent_twice_with_the_nibble_sum():
    for record in load_oracle("AMCOR"):
        first, second = decode(AMCOR, record["pulses"], expected=["main", "main"])
        assert first == second
        assert AMCOR_LAYOUT.checksum.check(first.data)
        assert first.data[0] == 0x01  # stateReset
        assert first.data[3:5] == b"\x00\x00"  # bytes 3-4: never written


@pytest.mark.parametrize(
    "state, capture",
    [
        (HvacState(True, "cool", 27.0, fan="auto"), REAL_EXAMPLE_27),
        (HvacState(True, "cool", 12.0, fan="auto"), REAL_EXAMPLE_12),
    ],
)
def test_real_captures_are_reproduced(state, capture):
    assert frame(state) == capture


def test_wire_matches_the_send_data_only_capture():
    # ir_Amcor_test.cpp, SendDataOnly: the REAL_EXAMPLE_27 state at 38 kHz,
    # m8200 s4200, 64 bits LSB first (one m1500 s600, zero m600 s1500),
    # m1900 s34300, the whole frame twice.
    bits = []
    for byte in REAL_EXAMPLE_27:
        for i in range(8):
            bits += [1500, 600] if byte >> i & 1 else [600, 1500]
    once = (8200, 4200, *bits, 1900, 34300)
    signal = device().encode(None, HvacState(True, "cool", 27.0)).signal
    assert signal.carrier == 38000
    assert signal.pulses == once * 2


@pytest.mark.parametrize("mode", ["auto", "cool", "fan", "dry", "heat"])
@pytest.mark.parametrize("t", [12.0, 32.0])
@pytest.mark.parametrize("fan", ["auto", "1", "2", "3"])
def test_off_carries_mode_auto_and_power_off_in_every_mode(mode, t, fan):
    # IRac passes mode "off"; convertMode maps it to kAmcorAuto, so the Vent
    # bits stay clear; setPower(false) writes kAmcorPowerOff (0b1100). The
    # setpoint and fan are sent as requested.
    values = read(HvacState(False, mode, t, fan=fan))
    assert values == {
        "mode": "auto",
        "fan": fan,
        "temp": t,
        "power": 0b1100,
        "max": 0,
        "vent": 0,
    }


@pytest.mark.parametrize(
    "mode, raw, vent",
    [("cool", 1, 0), ("heat", 2, 0), ("fan", 3, 0b11), ("dry", 4, 0), ("auto", 5, 0)],
)
def test_mode_codes_and_vent_in_mode_fan_only(mode, raw, vent):
    for t in (12.0, 22.0, 32.0):
        data = frame(HvacState(True, mode, t))
        values = AMCOR_LAYOUT.read(data)
        assert AMCOR_LAYOUT.read_raw(data, "mode") == raw
        assert (values["power"], values["temp"], values["vent"]) == (0b0011, t, vent)


@pytest.mark.parametrize("t", range(12, 33))
def test_every_whole_setpoint(t):
    assert read(HvacState(True, "heat", float(t)))["temp"] == t


def test_setpoint_is_clamped_to_12_32():
    assert read(HvacState(True, "cool", 5.0))["temp"] == 12
    assert read(HvacState(True, "cool", 40.0))["temp"] == 32


@pytest.mark.parametrize("fan, raw", [("auto", 4), ("1", 1), ("2", 2), ("3", 3)])
def test_every_fan_level(fan, raw):
    # convertFan: lowest (kMin) -> kAmcorFanMin, highest (kMax) -> kAmcorFanMax.
    for mode in ("auto", "cool", "fan", "dry", "heat"):
        data = frame(HvacState(True, mode, 22.0, fan=fan))
        assert AMCOR_LAYOUT.read_raw(data, "fan") == raw


@pytest.mark.parametrize("mode", ["cool", "heat"])
@pytest.mark.parametrize("t", [12.0, 32.0])
def test_max_is_never_set(mode, t):
    # IRac::amcor never calls setMax, even at Max's own setpoints.
    assert read(HvacState(True, mode, t))["max"] == 0


def test_previous_is_ignored():
    dev = device()
    on = HvacState(True, "cool", 22.0, fan="3")
    off = HvacState(False, "heat", 30.0)
    assert dev.encode(off, on).signal == dev.encode(None, on).signal
    assert dev.encode(on, on).signal == dev.encode(None, on).signal
    assert dev.encode(on, off).signal == dev.encode(None, off).signal


@pytest.mark.parametrize("model", AMCOR_MODELS)
def test_registry_serves_the_port(model):
    dev = registry.get_device("amcor", model)
    assert isinstance(dev, AmcorDevice)


@pytest.mark.parametrize("model", AMCOR_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.amcor import Amcor

    legacy = LegacyDevice("amcor", model, Amcor)
    assert device(model).capabilities == legacy.capabilities
