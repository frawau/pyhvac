import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac.ir.codec import decode
from pyhvac.protocols.rhoss import RHOSS, RHOSS_LAYOUT, RHOSS_MODELS, RhossDevice
from pyhvac.state import HvacState

# The C path never sends swing on: IRGHVAC.trans_swing has no "on" key, so
# the lookup error is swallowed, IRac::rhoss gets swingv kOff and
# setSwing(swing != kOff) clears the Swing bit (kRhossSwingOn is documented).
# The port sends the bit.
DEFECTS = (Defect("swing_v", "swing", "off", "C glue has no swing 'on' key"),)

# Real captures from ir_Rhoss_test.cpp.
# RawData: "Power: On, Mode: 2 (Cool), Temp: 20C, Fan: 0 (Auto), Swing(V): Off".
ON_COOL_20_AUTO = bytes.fromhex("aa0460002080540000000002")
# The RawData pulses, as recorded.
# fmt: off
RAW_DATA = (
    3044, 4248, 648, 458, 650, 1540, 646, 458, 650, 1538, 650, 458, 650, 1538,
    650, 458, 650, 1540, 648, 458, 650, 458, 650, 1540, 646, 484, 624, 456,
    650, 456, 650, 456, 650, 456, 650, 456, 650, 456, 650, 456, 650, 456,
    650, 458, 650, 1540, 650, 1538, 650, 456, 650, 456, 650, 456, 650, 456,
    650, 458, 650, 456, 650, 456, 650, 456, 650, 458, 650, 458, 650, 456,
    650, 458, 650, 458, 650, 458, 650, 1538, 650, 458, 650, 458, 650, 458,
    648, 458, 674, 434, 648, 458, 672, 434, 648, 458, 650, 458, 648, 1540,
    672, 434, 650, 458, 672, 1518, 644, 488, 622, 1540, 644, 464, 672, 1516,
    672, 434, 672, 434, 672, 434, 650, 458, 648, 458, 672, 434, 674, 434,
    672, 434, 650, 458, 672, 434, 648, 458, 650, 458, 672, 434, 672, 436,
    648, 458, 648, 456, 650, 458, 650, 458, 650, 456, 674, 434, 650, 458,
    650, 456, 650, 458, 674, 432, 650, 458, 650, 456, 650, 456, 650, 458,
    648, 458, 674, 432, 650, 456, 674, 434, 650, 458, 650, 458, 650, 1538,
    650, 458, 650, 458, 650, 456, 650, 458, 650, 456, 650, 458, 650, 456,
    650,
)
# fmt: on
# SendDataOnly / SyntheticSelfDecode: on, auto, 21C, fan auto, swing off.
ON_AUTO_21_AUTO = bytes.fromhex("aa0560005080540000000033")
# Checksums' knownGood1..3: auto 22C and 23C, fan auto; auto 23C fan max.
KNOWN_GOOD = (
    (bytes.fromhex("aa0660005080540000000034"), HvacState(True, "auto", 22.0)),
    (bytes.fromhex("aa0760005080540000000035"), HvacState(True, "auto", 23.0)),
    (bytes.fromhex("aa0760005380540000000038"), HvacState(True, "auto", 23.0, "3")),
)


def device(model="generic"):
    return RhossDevice("rhoss", model)


def data(state, previous=None):
    dev = device()
    if previous is not None:
        previous = dev.normalise(previous)
    (main,) = dev.frames(previous, dev.normalise(state), ())
    return main.data


def read(state, previous=None):
    return RHOSS_LAYOUT.read(data(state, previous))


@pytest.mark.parametrize("record", oracle_params("RHOSS"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("RHOSS"):
        state = state_from_record(dev, record["state"])
        (main,) = dev.frames(None, state, ())
        values = RHOSS_LAYOUT.read(main.data)
        assert RHOSS_LAYOUT.build(**values) == bytearray(main.data)
        assert RHOSS_LAYOUT.checksum.check(main.data)


def test_every_oracle_message_is_one_frame():
    for record in load_oracle("RHOSS"):
        (main,) = decode(RHOSS, record["pulses"], ["main"])
        assert main.data[0] == 0xAA


def test_port_reproduces_the_raw_data_capture():
    assert data(HvacState(True, "cool", 20.0)) == ON_COOL_20_AUTO


def test_port_reproduces_the_send_data_only_capture():
    assert data(HvacState(True, "auto", 21.0)) == ON_AUTO_21_AUTO


@pytest.mark.parametrize("capture, state", KNOWN_GOOD)
def test_port_reproduces_the_known_good_states(capture, state):
    assert data(state) == capture


@pytest.mark.parametrize("capture", [ON_COOL_20_AUTO, ON_AUTO_21_AUTO])
def test_layout_reads_the_real_captures(capture):
    values = RHOSS_LAYOUT.read(capture)
    assert values["power"] is True and values["swing_v"] == "off"
    assert RHOSS_LAYOUT.build(**values) == bytearray(capture)


def test_raw_capture_decodes_with_the_port_protocol():
    # ir_Rhoss_test.cpp RawData: the real remote's 197 pulses (ending on the
    # extra footer mark); the port's gap is appended.
    (main,) = decode(RHOSS, RAW_DATA + (100000,), ["main"])
    assert main.data == ON_COOL_20_AUTO


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat", "fan"])
def test_off_carries_mode_cool(mode):
    # IRac::rhoss: convertMode maps IRac's mode "off" to kRhossDefaultMode
    # (kRhossModeCool); the power field is kRhossPowerOff.
    values = read(HvacState(False, mode, 25.0, fan="2"))
    assert (values["mode"], values["power"]) == ("cool", False)
    assert (values["temperature"], values["fan"]) == (25, "2")
    assert RHOSS_LAYOUT.read_raw(data(HvacState(False, mode, 25.0)), "power") == 1


@pytest.mark.parametrize(
    "mode, raw", [("heat", 1), ("cool", 2), ("dry", 3), ("fan", 4), ("auto", 5)]
)
def test_every_mode_uses_its_documented_code(mode, raw):
    assert RHOSS_LAYOUT.read_raw(data(HvacState(True, mode, 22.0)), "mode") == raw
    assert RHOSS_LAYOUT.read_raw(data(HvacState(True, mode, 22.0)), "power") == 2


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat", "fan"])
@pytest.mark.parametrize("t", [16.0, 17.0, 21.0, 29.0, 30.0])
def test_setpoint_is_sent_in_every_mode(mode, t):
    assert read(HvacState(True, mode, t))["temperature"] == int(t)


@pytest.mark.parametrize("fan, raw", [("auto", 0), ("1", 1), ("2", 2), ("3", 3)])
def test_every_fan_level_uses_its_documented_code(fan, raw):
    # lowest/medium/highest: convertFan's kRhossFanMin/Med/Max.
    assert RHOSS_LAYOUT.read_raw(data(HvacState(True, "cool", 22.0, fan)), "fan") == raw


@pytest.mark.parametrize("power", [True, False])
def test_swing_sets_the_documented_swing_bit(power):
    on = HvacState(power, "cool", 22.0, swing_v="swing")
    off = HvacState(power, "cool", 22.0, swing_v="off")
    assert RHOSS_LAYOUT.read_raw(data(on), "swing_v") == 1
    assert RHOSS_LAYOUT.read_raw(data(off), "swing_v") == 0


def test_previous_is_ignored():
    # No toggle bits: IRac::handleToggles has no RHOSS case.
    dev = device()
    target = HvacState(False, "cool", 20.0)
    previous = HvacState(True, "heat", 25.0, fan="3", swing_v="swing")
    assert dev.encode(previous, target).signal == dev.encode(None, target).signal


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (3042, 4248)
    # sendGeneric's footer mark and zero space, sendRhoss's extra mark, the gap.
    assert pulses[-4:] == (648, 457, 648, 100000)
    assert len(pulses) == 2 + 2 * 96 + 4


def test_undeclared_swing_deviation_is_reported():
    dev = device()
    record = next(
        r
        for r in load_oracle("RHOSS")
        if r["state"].get("swing") == "on" and r["state"]["mode"] != "off"
    )
    with pytest.raises(AssertionError, match="swing_v"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_swing_off_needs_no_defect():
    dev = device()
    for record in load_oracle("RHOSS"):
        if record["state"].get("swing") != "on":
            assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("RHOSS")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)


def test_capabilities_are_the_headers():
    # ir_Rhoss.h: kRhossTempMin/Max 16-30; kRhossFan{Auto,Min,Med,Max};
    # kRhossMode{Heat,Cool,Dry,Fan,Auto}; kRhossSwingOn. No feature bits.
    caps = device().capabilities
    assert set(caps.modes) == {"auto", "cool", "dry", "heat", "fan"}
    assert (caps.temperature.min, caps.temperature.max) == (16.0, 30.0)
    assert caps.fan.values == ("auto", "1", "2", "3")
    assert caps.swing_v.values == ("off", "swing")
    assert dict(caps.features) == {}
