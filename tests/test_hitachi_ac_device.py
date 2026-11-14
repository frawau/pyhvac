import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac.protocols.hitachi import (
    HITACHI_AC,
    HITACHI_AC_LAYOUT,
    HITACHI_AC_MODELS,
    HitachiAcChecksum,
    HitachiAcDevice,
)
from pyhvac.state import HvacState
from pyhvac.ir.codec import decode

# The C path never sends swing on: the old vocabulary's "on" has no entry in
# IRGHVAC.trans_swing / trans_hswing, so build_ircode skips the key, swingv and
# swingh stay kOff, and IRac::hitachi never sets the SwingV / SwingH bits
# (HitachiProtocol byte 14 bit 7, byte 15 bit 7).
DEFECTS = (
    Defect("swing_v", "swing", "off", "C glue has no 'on' swing: sends off"),
    Defect("swing_h", "swing", "off", "C glue has no 'on' hswing: sends off"),
)

MODES = ("auto", "heat", "cool", "dry", "fan")


def device():
    return HitachiAcDevice("hitachi", "RAS-35THA6 remote")


def read(state, previous=None):
    dev = device()
    (frame,) = dev.frames(previous, dev.normalise(state), ())
    return HITACHI_AC_LAYOUT.read(frame.data)


def raw(state, name):
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(state), ())
    return HITACHI_AC_LAYOUT.read_raw(frame.data, name)


@pytest.mark.parametrize("record", oracle_params("HITACHI_AC"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("HITACHI_AC"):
        state = state_from_record(dev, record["state"])
        (frame,) = dev.frames(None, state, ())
        values = HITACHI_AC_LAYOUT.read(frame.data)
        assert HITACHI_AC_LAYOUT.build(**values) == bytearray(frame.data)


def test_checksum_matches_a_c_frame():
    # Off, cool, 16 °C, fan auto, as sent by the C library.
    data = bytearray.fromhex("80080c02fd807f8848904004008060600000000000000000800000c5")
    assert HitachiAcChecksum(0, 27, 27, reverse=True).check(data)
    data[27] = 0
    HITACHI_AC_LAYOUT.checksum.apply(data)
    assert data[27] == 0xC5


def test_fields_are_stored_bit_reversed():
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(HvacState(True, "cool", 24.0)), ())
    # kHitachiAcCool = 4, 24 °C << 1 = 48, kHitachiAcFanAuto = 1, all reversed.
    assert (frame.data[10], frame.data[11], frame.data[13]) == (0x20, 0x0C, 0x80)


@pytest.mark.parametrize("mode", MODES)
def test_off_carries_mode_auto_in_every_mode(mode):
    # IRac passes mode "off"; IRHitachiAc::convertMode maps it to auto.
    for t in (16.0, 32.0):
        values = read(HvacState(False, mode, t))
        assert (values["power"], values["mode"]) == (0, "auto")
        sent = raw(HvacState(False, mode, t), "temperature")
        assert sent == int(f"{int(t) << 1:08b}"[::-1], 2)


@pytest.mark.parametrize("mode", MODES)
def test_setpoint_is_sent_in_every_mode_even_fan(mode):
    # setMode(kHitachiAcFan) writes the special temperature 64, but IRac calls
    # setTemp(degrees) afterwards, so the C path always sends the setpoint.
    for t in (16, 23, 32):
        (frame,) = device().frames(None, HvacState(True, mode, float(t)), ())
        assert frame.data[11] == int(f"{t << 1:08b}"[::-1], 2)


def test_setpoint_is_clamped_to_16_32():
    assert raw(HvacState(True, "cool", 10.0), "temperature") == raw(
        HvacState(True, "cool", 16.0), "temperature"
    )
    assert raw(HvacState(True, "cool", 40.0), "temperature") == raw(
        HvacState(True, "cool", 32.0), "temperature"
    )


@pytest.mark.parametrize("mode", MODES)
def test_byte_9_flags_the_minimum_setpoint(mode):
    # IRHitachiAc::setTemp: byte 9 is 0x90 at kHitachiAcMinTemp, else 0x10.
    for power in (False, True):
        for t, byte in ((16.0, 0x90), (17.0, 0x10), (32.0, 0x10)):
            dev = device()
            (frame,) = dev.frames(None, dev.normalise(HvacState(power, mode, t)), ())
            assert frame.data[9] == byte


@pytest.mark.parametrize(
    "fan, code", [("auto", 1), ("1", 2), ("2", 3), ("3", 4), ("4", 5)]
)
def test_fan_levels_follow_convert_fan(fan, code):
    # kLow -> kHitachiAcFanLow, kMedium -> +1, kHigh -> kHitachiAcFanHigh - 1,
    # kMax -> kHitachiAcFanHigh (5, the "4" the legacy entity did not offer).
    state = HvacState(True, "cool", 24.0, fan=fan)
    assert raw(state, "fan") == int(f"{code:08b}"[::-1], 2)
    assert read(state)["fan"] == fan


@pytest.mark.parametrize(
    "fan, sent", [("auto", "1"), ("1", "1"), ("2", "2"), ("3", "2"), ("4", "2")]
)
def test_dry_has_only_low_and_medium(fan, sent):
    assert read(HvacState(True, "dry", 24.0, fan=fan))["fan"] == sent


@pytest.mark.parametrize(
    "fan, sent", [("auto", "1"), ("1", "1"), ("2", "2"), ("3", "3"), ("4", "4")]
)
def test_fan_mode_has_no_auto(fan, sent):
    assert read(HvacState(True, "fan", 24.0, fan=fan))["fan"] == sent


def test_off_keeps_the_requested_fan():
    # An off message is in mode auto, so no dry / fan clamp applies.
    assert read(HvacState(False, "dry", 24.0, fan="3"))["fan"] == "3"
    assert read(HvacState(False, "fan", 24.0))["fan"] == "auto"


def test_swing_on_sets_the_documented_bits():
    state = HvacState(True, "cool", 24.0, swing_v="swing", swing_h="swing")
    assert (read(state)["swing_v"], read(state)["swing_h"]) == ("swing", "swing")
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(state), ())
    assert (frame.data[14], frame.data[15]) == (0xE0, 0xE0)


def test_previous_is_ignored():
    dev = device()
    on = HvacState(True, "cool", 22.0)
    off = HvacState(False, "cool", 22.0)
    assert dev.encode(None, on).signal == dev.encode(off, on).signal
    assert dev.encode(on, on).signal == dev.encode(None, on).signal


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (3300, 1700)
    assert pulses[-2:] == (400, 100000)
    assert len(pulses) == 2 + 2 * 224 + 2


def test_fan_offers_the_four_speeds_set_fan_allows():
    # IRHitachiAc::setFan: kHitachiAcFanAuto (1) .. kHitachiAcFanHigh (5).
    fan = device().capabilities.fan
    assert fan.values == ("auto", "1", "2", "3", "4")
    # The legacy labels keep their codes: the oracle's "high" is still 4.
    assert [fan.label(v) for v in fan.values] == [
        "auto",
        "low",
        "medium",
        "high",
        "highest",
    ]


def test_capabilities():
    caps = device().capabilities
    assert caps.modes == MODES
    assert (caps.temperature.min, caps.temperature.max) == (16.0, 32.0)
    assert caps.swing_v.values == caps.swing_h.values == ("off", "swing")
    assert dict(caps.features) == {}


# ir_Hitachi_test.cpp DecodeHitachiAC.NormalRealExample2 (issue #417): on,
# heat, 32 C, fan kHitachiAcFanHigh (5), no swing.
REAL_EXAMPLE_2 = bytes.fromhex(
    "80080c02fd807f884810c00200a000000001000000000000800000d0"
)


def test_real_capture_with_fan_high_is_reproduced_but_for_the_reset_bytes():
    # Every field matches. Bytes 14 and 15 hold 0x60 below the swing bits in
    # IRHitachiAc::stateReset (as C sends), 0x00 in this capture (and in
    # NormalRealExample1); the checksum follows.
    dev = device()
    state = dev.normalise(HvacState(True, "heat", 32.0, fan="4"))
    (frame,) = dev.frames(None, state, ())
    assert HITACHI_AC_LAYOUT.read(frame.data) == HITACHI_AC_LAYOUT.read(REAL_EXAMPLE_2)
    assert HITACHI_AC_LAYOUT.read_raw(REAL_EXAMPLE_2, "fan") == 0xA0  # 5 reversed
    diff = {i for i, (a, b) in enumerate(zip(frame.data, REAL_EXAMPLE_2)) if a != b}
    assert diff == {14, 15, 27}


def test_undeclared_swing_v_deviation_is_reported():
    dev = device()
    record = next(
        r for r in load_oracle("HITACHI_AC") if r["state"].get("swing") == "on"
    )
    with pytest.raises(AssertionError, match="swing_v"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_undeclared_swing_h_deviation_is_reported():
    dev = device()
    record = next(
        r for r in load_oracle("HITACHI_AC") if r["state"].get("hswing") == "on"
    )
    with pytest.raises(AssertionError, match="swing_h"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=DEFECTS[:1])


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("HITACHI_AC")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)


# ir_Hitachi_test.cpp DecodeHitachiAC.NormalRealExample1: decodeHitachiAC
# matches with _tolerance + 5 (30 %) and kMarkExcess; this capture has bit
# marks as short as 296 µs for 400.
REAL_RAW = (
    "3318 1720 400 1276 400 432 398 434 398 434 400 432 398 432 398 432 398 "
    "434 398 432 398 434 400 432 398 434 398 1278 398 434 398 434 396 434 "
    "398 434 398 432 398 434 398 432 398 1276 426 1252 424 408 424 406 424 "
    "408 426 406 398 432 398 434 398 432 400 432 398 1276 426 408 424 1252 "
    "426 1252 424 1250 426 1252 428 1250 426 1252 424 406 426 1248 428 1252 "
    "426 406 426 406 424 408 400 432 400 430 400 432 400 430 400 432 400 "
    "1276 400 1276 402 1276 400 1276 400 1276 400 1278 400 1276 402 1276 "
    "402 428 402 430 400 430 402 1276 400 430 402 430 400 432 402 428 402 "
    "1278 400 430 402 430 402 1276 402 428 402 430 402 430 400 1276 402 430 "
    "402 430 402 430 402 430 402 428 402 430 404 430 402 428 402 430 402 "
    "1276 402 430 402 428 402 430 400 428 402 430 402 430 402 430 402 430 "
    "402 428 402 430 402 1274 402 428 402 430 402 430 402 430 402 430 402 "
    "428 402 428 402 428 404 428 404 428 402 1276 400 430 402 430 400 432 "
    "400 456 374 432 400 456 404 428 404 426 404 428 402 428 402 430 402 "
    "430 400 432 398 434 376 454 378 454 380 452 378 452 404 428 406 424 "
    "432 398 406 426 430 402 404 428 428 402 400 430 400 432 398 434 398 "
    "432 398 434 372 460 374 434 398 432 398 434 396 434 376 456 376 456 "
    "376 456 376 1300 378 454 378 452 378 454 378 454 378 454 378 452 378 "
    "454 400 432 402 430 402 430 402 430 402 428 402 430 402 430 400 430 "
    "402 430 400 432 400 430 400 432 400 430 402 430 400 432 398 432 400 "
    "430 400 432 398 432 398 434 398 432 398 432 400 434 398 432 398 432 "
    "398 434 398 434 396 434 398 434 398 432 398 434 398 432 398 456 376 "
    "454 376 436 396 454 376 454 378 454 376 454 376 456 374 458 374 1302 "
    "374 456 374 458 374 458 376 456 374 456 374 456 374 456 376 456 376 "
    "456 374 458 374 458 374 458 372 458 372 460 374 458 372 460 372 460 "
    "372 460 370 462 372 460 372 460 370 462 370 462 356 1320 368 464 346 "
    "1332 356 476 368 1310 366 1312 366 464 366 466 366"
)


def test_real_raw_capture_decodes():
    (frame,) = decode(HITACHI_AC, [int(x) for x in REAL_RAW.split()])
    assert frame.data == bytes.fromhex(
        "80080c02fd807f8848802004008000000001000000000000800000ac"
    )
