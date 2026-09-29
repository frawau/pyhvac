import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.ir.codec import decode
from pyhvac.plugins.trotech import (
    TROTEC,
    TROTEC_LAYOUT,
    TROTEC_MODELS,
    TrotecDevice,
)
from pyhvac.state import HvacState

# The C path never sends sleep: IRGHVAC.build_ircode's key map has no
# "sleep", so IRac::trotec gets sleep -1 and setSleep(sleep >= 0) clears the
# Sleep bit. The port sends the documented bit.
DEFECTS = (Defect("sleep", 1, 0, "C glue has no 'sleep' key"),)

# ir_Trotec_test.cpp (MessageConstructon / SendDataOnly): power on, cool,
# 20 °C, fan medium, sleep on. A synthetic frame built by the C class, not a
# remote capture (the test file has no Trotec remote capture).
ON_COOL_20_MED_SLEEP = bytes.fromhex("1234298200000000ab")


def _with_c_defaults(record):
    # A record without "fan" relied on IRac's default (kAuto), which
    # IRTrotecESP::convertFan sends as kTrotecFanMed, labelled "medium".
    return {**record, "state": {"fan": "medium", **record["state"]}}


def device(model="PAC 3200"):
    return TrotecDevice("trotech", model)


def read(state, previous=None):
    dev = device()
    if previous is not None:
        previous = dev.normalise(previous)
    main, _ = dev.frames(previous, dev.normalise(state), ())
    return TROTEC_LAYOUT.read(main.data)


def data(state):
    dev = device()
    main, _ = dev.frames(None, dev.normalise(state), ())
    return main.data


@pytest.mark.parametrize("record", oracle_params("TROTEC"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, _with_c_defaults(record), dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("TROTEC"):
        state = state_from_record(dev, _with_c_defaults(record)["state"])
        main, end = dev.frames(None, state, ())
        values = TROTEC_LAYOUT.read(main.data)
        assert TROTEC_LAYOUT.build(**values) == bytearray(main.data)
        assert TROTEC_LAYOUT.checksum.check(main.data)
        assert end.data == b""


def test_every_oracle_message_is_a_frame_and_the_end_burst():
    for record in load_oracle("TROTEC"):
        main, end = decode(TROTEC, record["pulses"], ["main", "end"])
        assert main.data[:2] == b"\x12\x34"  # kTrotecIntro1, kTrotecIntro2
        assert end.data == b""


def test_the_port_reproduces_the_c_test_frame():
    state = HvacState(True, "cool", 20.0, fan="2", features={"sleep": True})
    assert data(state) == ON_COOL_20_MED_SLEEP


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0, fan="1"))
    pulses = pulses.signal.pulses
    assert pulses[:2] == (5952, 7364)  # kTrotecHdrMark, kTrotecHdrSpace
    # sendGeneric's footer, then sendTrotec's extra mark + kTrotecGapEnd.
    assert pulses[-4:] == (592, 6184, 592, 1500)
    assert len(pulses) == 2 + 2 * 72 + 4


def test_carrier_is_36_khz():
    signal = device().encode(None, HvacState(True, "cool", 22.0, fan="1")).signal
    assert signal.carrier == 36000  # sendTrotec's enableIROut(36)


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan"])
@pytest.mark.parametrize("t", [16.0, 23.0, 30.0])
def test_off_carries_mode_auto_and_power_off(mode, t):
    # IRac passes mode "off"; convertMode maps it to kTrotecAuto.
    values = read(HvacState(False, mode, t, fan="3", features={"sleep": True}))
    assert (values["power"], values["mode"]) == (0, "auto")
    assert (values["temperature"], values["fan"], values["sleep"]) == (
        max(int(t), 18),
        "3",
        1,
    )


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan"])
def test_on_sends_the_mode(mode):
    values = read(HvacState(True, mode, 25.0, fan="2"))
    assert (values["power"], values["mode"]) == (1, mode)


@pytest.mark.parametrize(
    "t, sent", [(16.0, 18), (17.0, 18), (18.0, 18), (25.0, 25), (30.0, 30)]
)
def test_setpoint_is_clamped_to_18_32(t, sent):
    # The entity offers 16-30 °C, but IRTrotecESP::setTemp clamps to
    # kTrotecMinTemp (18)..kTrotecMaxTemp (32), as the C path sends.
    assert read(HvacState(True, "cool", t, fan="1"))["temperature"] == sent
    assert (
        TROTEC_LAYOUT.read_raw(data(HvacState(True, "cool", t, fan="1")), "temperature")
        == sent - 18
    )


@pytest.mark.parametrize("fan, raw", [("1", 1), ("2", 2), ("3", 3)])
def test_every_fan_level(fan, raw):
    # low/medium/high -> kTrotecFanLow/Med/High (convertFan).
    raw_read = TROTEC_LAYOUT.read_raw(
        data(HvacState(True, "cool", 22.0, fan=fan)), "fan"
    )
    assert raw_read == raw


def test_sleep_sends_the_documented_sleep_bit():
    raw = data(HvacState(True, "cool", 22.0, fan="1", features={"sleep": True}))
    assert raw[3] & 0x80  # Sleep: byte 3 bit 7
    assert read(HvacState(True, "cool", 22.0, fan="1"))["sleep"] == 0


def test_timer_is_never_set():
    # IRac::trotec has no timer: stateReset's zeros are sent.
    values = read(HvacState(True, "dry", 18.0, fan="3", features={"sleep": True}))
    assert (values["timer"], values["hours"]) == (0, 0)


@pytest.mark.parametrize(
    "previous",
    [
        None,
        HvacState(False, "cool", 22.0, fan="3"),
        HvacState(True, "cool", 26.0, fan="1"),
        HvacState(True, "cool", 22.0, fan="3", features={"sleep": True}),
    ],
)
def test_previous_is_ignored(previous):
    # No toggle bits, and IRac::handleToggles has no TROTEC case.
    dev = device()
    target = HvacState(True, "cool", 22.0, fan="3", features={"sleep": True})
    assert dev.encode(previous, target).signal == dev.encode(None, target).signal


@pytest.mark.parametrize("model", TROTEC_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("trotech", model), TrotecDevice)


@pytest.mark.parametrize("model", TROTEC_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.trotech import Trotech

    legacy = LegacyDevice("trotech", model, Trotech)
    assert device(model).capabilities == legacy.capabilities


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(r for r in load_oracle("TROTEC") if r["state"].get("sleep") == "on")
    with pytest.raises(AssertionError, match="sleep"):
        assert_matches_oracle(dev, _with_c_defaults(record), dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("TROTEC")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)


# No real capture in ir_Trotec_test.cpp needs it, but
# decodeTrotec matches with _tolerance (25 %) and no mark excess.
def test_decode_tolerance_is_the_c_decoders():
    assert (TROTEC.tolerance, TROTEC.mark_excess) == (0.25, 0)
