import pytest

from oracle import load_oracle
from port_oracle import assert_matches_oracle, oracle_params, state_from_record
from pyhvac.ir.model import Frame
from pyhvac.protocols.hitachi import (
    HITACHI264,
    HITACHI264_LAYOUT,
    HITACHI264_MODELS,
    Hitachi264Device,
)
from pyhvac.state import HvacState
from pyhvac.ir.codec import decode

# No declared defects: the C path sends the documented values for every
# field it writes. Swing and the features have no bits (IRac::hitachi264
# sets none of them) and are no longer offered, so the oracle's swing and
# feature "on" keys are dropped (state_from_record reads only offered
# controls) and its mode "auto" records normalise to cool, which is what C
# sends for them (IRHitachiAc424::convertMode): C's frames stay the expected
# ones.


def device():
    return Hitachi264Device("hitachi", "RAR-2P2 remote")


def read(state, previous=None):
    dev = device()
    (frame,) = dev.frames(previous, dev.normalise(state), ())
    return HITACHI264_LAYOUT.read(frame.data)


@pytest.mark.parametrize("record", oracle_params("HITACHI_AC264"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("HITACHI_AC264"):
        state = state_from_record(dev, record["state"])
        (frame,) = dev.frames(None, state, ())
        values = HITACHI264_LAYOUT.read(frame.data)
        assert HITACHI264_LAYOUT.build(**values) == bytearray(frame.data)


def test_bytes_3_to_32_are_inverted_pairs():
    (frame,) = device().frames(None, HvacState(True, "heat", 21.0), ())
    data = frame.data
    assert len(data) == 33
    assert all(data[i + 1] == data[i] ^ 0xFF for i in range(3, 33, 2))
    assert data[:3] == bytes.fromhex("011000")


def test_no_field_sits_on_an_inverted_byte():
    inverted = HITACHI264_LAYOUT.checksum.positions()
    for name, field in HITACHI264_LAYOUT.fields.items():
        assert not {bit // 8 for bit in field.bits} & inverted, name


@pytest.mark.parametrize("mode", ["auto", "cool", "fan", "dry", "heat"])
def test_off_carries_mode_cool_in_every_mode(mode):
    # IRac passes the off mode through IRHitachiAc424::convertMode: cool.
    for t in (16.0, 24.0, 32.0):
        values = read(HvacState(False, mode, t, fan="2"))
        assert (values["power"], values["mode"]) == (0, "cool")
        assert (values["temperature"], values["fan"]) == (int(t), "2")


def test_auto_mode_is_sent_as_cool():
    # IRHitachiAc424::convertMode has no auto; kHitachiAc264* has none either.
    # Auto is not offered: normalise maps it to cool, the first mode.
    assert device().normalise(HvacState(True, "auto", 24.0)).mode == "cool"
    assert read(HvacState(True, "auto", 24.0))["mode"] == "cool"


@pytest.mark.parametrize("mode", ["cool", "fan", "dry", "heat"])
def test_modes_use_their_documented_values(mode):
    assert read(HvacState(True, mode, 24.0))["mode"] == mode


def test_fan_mode_keeps_the_setpoint():
    # setMode(kHitachiAc424Fan) sets kHitachiAc424FanTemp (27), but IRac calls
    # setTemp(degrees) after setMode, so the setpoint wins.
    for t in (16.0, 20.0, 32.0):
        assert read(HvacState(True, "fan", t))["temperature"] == int(t)


def test_setpoint_is_clamped_to_16_32():
    assert read(HvacState(True, "cool", 5.0))["temperature"] == 16
    assert read(HvacState(True, "heat", 40.0))["temperature"] == 32


@pytest.mark.parametrize("fan, raw", [("auto", 5), ("1", 1), ("2", 3), ("3", 4)])
@pytest.mark.parametrize("mode", ["cool", "fan", "dry", "heat"])
def test_every_fan_level_uses_its_documented_value_in_every_mode(mode, fan, raw):
    # IRHitachiAc264::setFan has no per-mode clamp (unlike IRHitachiAc424's).
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(HvacState(True, mode, 24.0, fan=fan)), ())
    assert HITACHI264_LAYOUT.read_raw(frame.data, "fan") == raw


def test_button_is_always_power_mode():
    # IRac::hitachi264 calls setPower last on a fresh object: the button is
    # kHitachiAc264ButtonPowerMode whatever changed; previous is ignored.
    previous = HvacState(True, "cool", 20.0, fan="1")
    for target in (
        HvacState(True, "cool", 24.0, fan="1"),
        HvacState(True, "cool", 20.0, fan="3"),
        HvacState(True, "cool", 20.0, fan="1", swing_v="swing"),
        HvacState(False, "cool", 20.0),
    ):
        assert read(target)["button"] == "power_mode"
        assert read(target, device().normalise(previous))["button"] == "power_mode"


def test_previous_is_ignored():
    dev = device()
    target = HvacState(True, "heat", 22.0, fan="2")
    fresh = dev.encode(None, target).signal
    assert dev.encode(HvacState(False, "cool", 30.0), target).signal == fresh


def test_swing_and_features_have_no_bits():
    # IRac::hitachi264: "No Swing(V) setting available", no quiet, turbo,
    # light, filter...; IRHitachiAc264::toCommon forces swingv off.
    base = device().frames(None, device().normalise(HvacState(True, "cool", 24.0)), ())
    features = {n: True for n in ("purifier", "powerful", "quiet", "economy", "light")}
    loaded = HvacState(True, "cool", 24.0, swing_v="swing", features=features)
    assert device().frames(None, device().normalise(loaded), ()) == base


def test_message_shape():
    dev = device()
    pulses = dev.encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (3300, 1700)
    assert pulses[-2:] == (400, 100000)
    assert len(pulses) == 2 + 2 * 264 + 2


def test_frame_is_a_single_main_section():
    dev = device()
    frames = dev.frames(None, dev.normalise(HvacState(True, "cool", 22.0)), ())
    assert [type(f) for f in frames] == [Frame]
    assert frames[0].section == "main"


def test_capabilities_are_the_documented_controls():
    # kHitachiAc264{Cool,Fan,Dry,Heat}, kHitachiAc264Min/MaxTemp (16/32),
    # kHitachiAc264Fan{Low,Medium,High,Auto}.
    caps = device().capabilities
    assert caps.modes == ("cool", "fan", "dry", "heat")
    assert (caps.temperature.min, caps.temperature.max) == (16.0, 32.0)
    assert caps.fan.values == ("auto", "1", "2", "3")


def test_no_op_controls_are_not_offered():
    # The legacy entity offered auto mode (sent as cool), swing and five
    # features, none of which has a bit in HitachiAC264Protocol.
    caps = device().capabilities
    assert "auto" not in caps.modes
    assert caps.swing_v is None and caps.swing_h is None
    assert dict(caps.features) == {}


def test_undeclared_deviation_is_reported():
    # A port that sends the wrong mode in an off message must fail the check.
    class Wrong(Hitachi264Device):
        def frames(self, previous, target, actions):
            data = HITACHI264_LAYOUT.build(
                button="power_mode",
                temperature=target.temperature,
                mode="heat",
                fan=target.fan,
                power=target.power,
            )
            return [Frame("main", bytes(data))]

    dev = Wrong("hitachi", "RAR-2P2 remote")
    record = next(
        r for r in load_oracle("HITACHI_AC264") if r["state"]["mode"] == "off"
    )
    with pytest.raises(AssertionError, match="mode"):
        assert_matches_oracle(dev, record, dev.LAYOUTS)


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("HITACHI_AC264")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, ())


# ir_Hitachi_test.cpp DecodeHitachiAc264.RealExample: decodeHitachiAC
# matches with _tolerance + 5 (30 %) and kMarkExcess; this capture has bit
# marks as short as 294 µs for 400.
REAL_RAW = (
    "3392 1752 372 1356 344 504 344 504 344 480 370 480 370 478 370 478 372 "
    "480 370 478 370 480 370 478 370 480 370 1330 370 478 370 480 370 478 "
    "370 478 370 480 370 478 370 480 370 504 346 504 344 480 370 504 346 "
    "478 370 478 370 478 372 480 370 480 370 504 346 1330 370 480 370 1356 "
    "346 1330 370 1354 346 1328 370 1330 370 1328 370 478 372 1330 370 1328 "
    "370 1356 346 1354 344 1328 372 1354 344 1356 344 1330 370 1328 372 480 "
    "370 478 370 504 346 478 372 476 372 504 346 480 370 504 344 478 372 "
    "504 344 1328 372 1328 372 478 370 504 346 1330 370 1328 372 1328 370 "
    "1356 344 478 370 478 370 1356 344 1328 372 480 370 478 372 504 346 "
    "1330 370 478 370 480 370 1330 370 478 370 480 370 1328 370 1330 370 "
    "480 372 1352 346 1328 372 504 346 1328 370 1328 370 480 370 1328 372 "
    "1328 370 504 344 478 372 1330 370 478 370 480 370 480 370 478 370 480 "
    "370 1356 346 1328 370 480 370 1330 370 1330 370 1330 370 478 370 506 "
    "344 1328 372 1328 372 478 372 1330 370 1328 372 478 370 1330 370 1328 "
    "372 504 344 480 370 1330 370 504 344 504 346 1354 346 504 346 478 372 "
    "478 370 480 370 478 370 492 358 478 370 478 370 1328 372 1330 370 1328 "
    "372 1354 346 1328 372 1328 370 1330 370 1328 372 476 372 504 346 478 "
    "372 480 370 480 370 504 344 478 370 480 370 1328 370 1330 372 1328 370 "
    "1330 370 1330 370 1330 368 1330 370 1330 370 480 370 480 370 478 370 "
    "504 344 480 370 478 370 504 344 478 372 1328 370 1330 370 1330 370 "
    "1330 370 1328 372 1356 344 1330 370 1330 370 480 370 478 370 482 368 "
    "480 370 480 370 480 370 480 370 480 370 1330 370 1354 346 1330 370 "
    "1354 346 1330 370 1330 370 1330 370 1330 370 504 346 480 370 478 372 "
    "478 372 504 344 480 370 480 370 504 344 1330 370 1328 370 1330 372 "
    "1328 370 1354 346 1328 370 1330 370 1330 370 478 370 1330 370 1328 372 "
    "480 370 1330 370 480 370 480 370 480 370 1356 344 478 370 506 344 1330 "
    "370 478 370 1330 372 1354 346 1354 346 1328 370 478 372 478 370 480 "
    "370 504 346 480 370 1328 370 1330 370 478 370 1330 370 1328 370 1330 "
    "372 1354 344 1328 372 504 346 478 370 504 346 504 346 478 370 478 370 "
    "482 368 480 370 478 370 480 370 1328 372 1328 370 1330 370 1328 370 "
    "1328 370 1330 370 1354 346 1328 372 478 370 478 370 478 372 478 372 "
    "478 372 478 372 478 370 478 372 1330 370 1328 370 1328 372 1328 372 "
    "1330 444 1256 370 1330 370 1330 442"
)


def test_real_raw_capture_decodes():
    (frame,) = decode(HITACHI264, [int(x) for x in REAL_RAW.split()])
    assert frame.data == bytes.fromhex(
        "01100040bfff00cc33926d13ec6c9300ff00ff00ff00ff00ff16e9c13e00ff00ff"
    )
