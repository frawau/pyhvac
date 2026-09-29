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
def test_max_is_clear_without_powerful(mode, t):
    # IRac::amcor never calls setMax, even at Max's own setpoints.
    assert read(HvacState(True, mode, t))["max"] == 0


def test_powerful_is_offered():
    assert device().capabilities.features["powerful"].values == (False, True)


@pytest.mark.parametrize("mode, sent", [("cool", 12), ("heat", 32)])
@pytest.mark.parametrize("t", [12.0, 22.0, 32.0])
def test_powerful_sets_max_and_its_setpoint(mode, t, sent):
    # IRAmcorAc::setMax: kAmcorMax (0b11), with Temp = kAmcorMinTemp in cool
    # and kAmcorMaxTemp in heat (TestAmcorAcClass.Max).
    data = frame(HvacState(True, mode, t, features={"powerful": True}))
    values = AMCOR_LAYOUT.read(data)
    assert (values["max"], values["temp"]) == (0b11, sent)
    assert AMCOR_LAYOUT.checksum.check(data)


@pytest.mark.parametrize("mode", ["auto", "fan", "dry"])
def test_powerful_is_not_sent_outside_cool_and_heat(mode):
    # setMax: "Not allowed in all other operating modes" (Temp unchanged).
    on = HvacState(True, mode, 25.0, features={"powerful": True})
    assert frame(on) == frame(HvacState(True, mode, 25.0))


@pytest.mark.parametrize("mode", ["cool", "heat"])
def test_powerful_is_not_sent_with_power_off(mode):
    # An off message carries mode auto, where setMax does nothing.
    off = HvacState(False, mode, 25.0, features={"powerful": True})
    assert frame(off) == frame(HvacState(False, mode, 25.0))


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


# ir_Amcor_test.cpp DecodeAmcor.RealExample: two real captures, each the
# frame sent twice. decodeAmcor matches them with kAmcorTolerance (40 %) and
# no mark excess; their marks run as short as 360 µs for 600.
REAL_RAW = [
    (
        [
            8210,
            4276,
            1544,
            480,
            596,
            1510,
            596,
            1510,
            596,
            1692,
            388,
            1534,
            596,
            1510,
            596,
            1510,
            596,
            1684,
            1450,
            480,
            596,
            1510,
            570,
            1534,
            570,
            1718,
            386,
            1536,
            594,
            1500,
            1632,
            482,
            596,
            1694,
            362,
            1550,
            1632,
            472,
            1658,
            456,
            596,
            1684,
            1474,
            446,
            1634,
            480,
            572,
            1534,
            572,
            1718,
            362,
            1558,
            572,
            1534,
            570,
            1534,
            570,
            1720,
            360,
            1558,
            572,
            1534,
            570,
            1534,
            570,
            1718,
            360,
            1560,
            572,
            1534,
            570,
            1534,
            570,
            1718,
            362,
            1560,
            572,
            1532,
            572,
            1534,
            570,
            1718,
            362,
            1558,
            572,
            1532,
            572,
            1534,
            570,
            1710,
            1448,
            472,
            1634,
            480,
            572,
            1534,
            570,
            1718,
            362,
            1558,
            572,
            1534,
            570,
            1534,
            572,
            1716,
            362,
            1560,
            572,
            1534,
            572,
            1534,
            570,
            1718,
            362,
            1550,
            1634,
            480,
            570,
            1536,
            570,
            1710,
            1448,
            482,
            570,
            1534,
            570,
            1536,
            570,
            1508,
            1856,
            34298,
            8218,
            4314,
            1502,
            522,
            530,
            1576,
            504,
            1602,
            504,
            1786,
            392,
            1528,
            504,
            1600,
            504,
            1600,
            504,
            1770,
            1414,
            522,
            528,
            1578,
            502,
            1602,
            504,
            1784,
            394,
            1528,
            504,
            1584,
            1574,
            548,
            528,
            1762,
            392,
            1512,
            1572,
            530,
            1600,
            524,
            528,
            1744,
            1390,
            530,
            1574,
            546,
            506,
            1600,
            504,
            1784,
            394,
            1528,
            504,
            1600,
            578,
            1528,
            504,
            1784,
            394,
            1526,
            504,
            1600,
            504,
            1600,
            506,
            1784,
            394,
            1528,
            504,
            1602,
            504,
            1602,
            504,
            1784,
            394,
            1526,
            506,
            1600,
            504,
            1600,
            506,
            1784,
            392,
            1526,
            506,
            1600,
            504,
            1602,
            502,
            1768,
            1390,
            530,
            1574,
            548,
            504,
            1600,
            504,
            1786,
            392,
            1530,
            504,
            1600,
            504,
            1600,
            504,
            1786,
            392,
            1528,
            504,
            1600,
            504,
            1600,
            506,
            1784,
            394,
            1512,
            1574,
            548,
            504,
            1602,
            504,
            1768,
            1388,
            548,
            504,
            1602,
            504,
            1602,
            502,
            1574,
            1792,
        ],
        "0141360000300012",
    ),
    (
        [
            8252,
            4294,
            1518,
            508,
            544,
            1560,
            546,
            1560,
            570,
            1718,
            416,
            1504,
            546,
            1560,
            570,
            1532,
            572,
            1718,
            1414,
            506,
            544,
            1560,
            570,
            1534,
            570,
            1718,
            416,
            1506,
            544,
            1558,
            1598,
            508,
            544,
            1746,
            416,
            1504,
            546,
            1560,
            570,
            1534,
            1598,
            690,
            1414,
            508,
            544,
            1560,
            546,
            1560,
            544,
            1746,
            416,
            1504,
            546,
            1560,
            546,
            1560,
            570,
            1718,
            416,
            1504,
            544,
            1560,
            570,
            1536,
            544,
            1744,
            416,
            1506,
            570,
            1534,
            546,
            1558,
            546,
            1744,
            418,
            1502,
            572,
            1534,
            544,
            1560,
            570,
            1720,
            416,
            1506,
            544,
            1560,
            546,
            1560,
            544,
            1744,
            1414,
            506,
            1572,
            534,
            544,
            1560,
            570,
            1720,
            416,
            1504,
            570,
            1536,
            544,
            1560,
            572,
            1718,
            416,
            1504,
            570,
            1542,
            592,
            1504,
            570,
            1720,
            416,
            1502,
            1572,
            534,
            544,
            1560,
            572,
            1718,
            1414,
            508,
            544,
            1560,
            570,
            1534,
            570,
            1508,
            1840,
            34174,
            8230,
            4292,
            1546,
            480,
            546,
            1560,
            572,
            1534,
            570,
            1718,
            416,
            1502,
            572,
            1532,
            572,
            1532,
            572,
            1718,
            1440,
            480,
            570,
            1534,
            572,
            1534,
            572,
            1716,
            418,
            1504,
            572,
            1532,
            1626,
            480,
            572,
            1718,
            418,
            1502,
            574,
            1534,
            572,
            1530,
            1626,
            662,
            1442,
            480,
            572,
            1534,
            572,
            1534,
            572,
            1716,
            418,
            1502,
            574,
            1542,
            592,
            1504,
            598,
            1692,
            418,
            1504,
            572,
            1532,
            574,
            1530,
            574,
            1716,
            418,
            1502,
            598,
            1508,
            572,
            1532,
            598,
            1692,
            418,
            1502,
            598,
            1508,
            572,
            1532,
            574,
            1716,
            418,
            1504,
            598,
            1508,
            572,
            1532,
            574,
            1716,
            1442,
            478,
            1626,
            480,
            572,
            1534,
            572,
            1718,
            392,
            1526,
            574,
            1532,
            572,
            1532,
            572,
            1716,
            418,
            1502,
            598,
            1508,
            574,
            1532,
            598,
            1700,
            408,
            1504,
            1624,
            480,
            572,
            1532,
            574,
            1716,
            1440,
            480,
            572,
            1532,
            572,
            1532,
            572,
            1506,
            1814,
        ],
        "0141180000300012",
    ),
]


@pytest.mark.parametrize("pulses, state", REAL_RAW)
def test_real_raw_captures_decode(pulses, state):
    frames = decode(AMCOR, pulses, expected=["main", "main"])
    assert [f.data.hex() for f in frames] == [state, state]
