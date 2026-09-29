import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac.protocols.hitachi import (
    HITACHI296,
    HITACHI296_LAYOUT,
    HITACHI296_MODELS,
    Hitachi296Device,
)
from pyhvac.state import HvacState

# The C path reads uninitialised memory for the unnamed padding bits of
# HitachiAC296Protocol that IRHitachiAc296::stateReset never writes, because
# IRac::sendAc builds the object on the stack:
# - byte 25 bit 7 ("unset", after Fan) changes from process to process (its
#   parity bit, byte 26 bit 7, follows); the committed fixture holds 1;
# - byte 13 bits 0-1 ("unset_low", before Temp) came out 0b11 in every
#   process tried, by accident; the fixture holds 0b11;
# - byte 13 bit 7 ("unset_high", after Temp) came out 0 so far.
# The port sends 0 for all four bits, as in the library's RAR-3U3 captures
# (ir_Hitachi_test.cpp: byte 13 = 0x04 / 0x60, byte 25 = 0x57 / 0x13).
UNSET = Defect("unset", 0, 1, "C sends stale memory in byte 25 bit 7")
UNSET_LOW = Defect("unset_low", 0, 3, "C sends stale memory in byte 13 bits 0-1")
UNSET_HIGH = Defect("unset_high", 0, 1, "C sends stale memory in byte 13 bit 7")
DEFECTS = (UNSET, UNSET_LOW, UNSET_HIGH)

# The two RAR-3U3 messages of ir_Hitachi_test.cpp (TestDecodeHitachiAc296).
REAL_EXAMPLE = bytes.fromhex(  # power on, auto, fan auto
    "01100040bfff00cc33926d44bb04fb00ff00ff00ff00ff00ff57a8f10e00ff00ff00ff03fc"
)
SYNTHETIC_EXAMPLE = bytes.fromhex(  # power on, cool, 24 C, fan quiet
    "01100040bfff00cc33986742bd609f00ff00ff00ff00ff00ff13ecf10e00ff00ff00ff03fc"
)


# The legacy entity offered a fifth fan level, "highest", which C sends as
# kHitachiAc296FanHigh like "high" (convertFan maps kMax and kHigh alike).
# The port offers the four documented speeds only, so the oracle's "highest"
# records are read as "high": same code, so C's frames are the expected ones.
def adapt(record):
    if record["state"].get("fan") != "highest":
        return record
    return {**record, "state": {**record["state"], "fan": "high"}}


def records():
    return [adapt(r) for r in load_oracle("HITACHI_AC296")]


def device(model="RAR-3U3 remote"):
    return Hitachi296Device("hitachi", model)


def read(state):
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(state), ())
    return HITACHI296_LAYOUT.read(frame.data)


@pytest.mark.parametrize("record", oracle_params("HITACHI_AC296"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, adapt(record), dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in records():
        state = state_from_record(dev, record["state"])
        (frame,) = dev.frames(None, state, ())
        values = HITACHI296_LAYOUT.read(frame.data)
        assert HITACHI296_LAYOUT.build(**values) == bytearray(frame.data)
        assert HITACHI296_LAYOUT.checksum.check(frame.data)


@pytest.mark.parametrize(
    "capture, state, differing",
    [
        # stateReset sends byte 11 = 0x43; this capture has 0x44.
        (REAL_EXAMPLE, HvacState(True, "auto", 24.0), {11, 12}),
        # stateReset sends bytes 9/11 = 0x92/0x43; this capture has 0x98/0x42.
        (SYNTHETIC_EXAMPLE, HvacState(True, "cool", 24.0, fan="1"), {9, 10, 11, 12}),
    ],
)
def test_the_rar_3u3_captures_are_reproduced_but_for_the_reset_bytes(
    capture, state, differing
):
    # Both captures are expressible as HvacStates, but neither can match
    # exactly: bytes 9 and 11 are fixed by stateReset (no field in
    # HitachiAC296Protocol, no IRac setter) and differ from the remote's.
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(state), ())
    diff = {i for i, (a, b) in enumerate(zip(frame.data, capture)) if a != b}
    assert diff == differing
    assert HITACHI296_LAYOUT.read(frame.data) == HITACHI296_LAYOUT.read(capture)


def test_unset_bit_is_always_zero():
    for mode in ("auto", "cool", "dry", "heat"):
        for power in (True, False):
            values = read(HvacState(power, mode, 20.0))
            assert (values["unset"], values["unset_low"]) == (0, 0)


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat"])
def test_off_carries_mode_auto_and_the_auto_temperature(mode):
    # IRac passes mode "off"; convertMode maps it to auto, where setTemp
    # stores kHitachiAc296TempAuto.
    for t in (16.0, 25.0):
        values = read(HvacState(False, mode, t))
        assert (values["power"], values["mode"], values["temperature"]) == (
            0,
            "auto",
            1,
        )


def test_auto_ignores_the_setpoint():
    assert read(HvacState(True, "auto", 22.0))["temperature"] == 1


@pytest.mark.parametrize("mode", ["cool", "dry", "heat"])
def test_setpoint_is_whole_degrees_clamped_to_16_31(mode):
    # kHitachiAc296MinTemp = 16, kHitachiAc296MaxTemp = 31 (the legacy
    # entity stopped at 25).
    assert read(HvacState(True, mode, 10.0))["temperature"] == 16
    assert read(HvacState(True, mode, 21.0))["temperature"] == 21
    assert read(HvacState(True, mode, 26.0))["temperature"] == 26
    assert read(HvacState(True, mode, 31.0))["temperature"] == 31
    assert read(HvacState(True, mode, 40.0))["temperature"] == 31


def test_setpoint_range_is_the_headers():
    temperature = device().capabilities.temperature
    assert (temperature.min, temperature.max, temperature.decimals) == (
        16.0,
        31.0,
        (0,),
    )


def test_frames_clamp_the_setpoint_to_the_header_maximum():
    # setTemp clamps to kHitachiAc296MaxTemp even without normalise.
    (frame,) = device().frames(None, HvacState(True, "cool", 40.0), ())
    assert HITACHI296_LAYOUT.read(frame.data)["temperature"] == 31


@pytest.mark.parametrize(
    "fan, raw", [("auto", 5), ("1", 1), ("2", 2), ("3", 3), ("4", 4)]
)
def test_every_fan_level_uses_convert_fan(fan, raw):
    # kHitachiAc296Fan{Auto,Silent,Low,Medium,High}.
    assert read(HvacState(True, "cool", 22.0, fan=fan))["fan"] == raw


def test_no_fan_level_duplicates_high():
    # The legacy "highest" (fan "5") sent kHitachiAc296FanHigh, as "4" does:
    # a control with no code of its own, removed.
    assert device().capabilities.fan.values == ("auto", "1", "2", "3", "4")


def test_the_oracles_highest_records_match_as_high():
    dev = device()
    highest = [
        r for r in load_oracle("HITACHI_AC296") if r["state"].get("fan") == "highest"
    ]
    assert highest
    for record in highest:
        assert_matches_oracle(dev, adapt(record), dev.LAYOUTS, DEFECTS)


def test_mode_codes():
    for mode, raw in (("auto", 7), ("cool", 3), ("dry", 5), ("heat", 6)):
        assert (
            HITACHI296_LAYOUT.read_raw(HITACHI296_LAYOUT.build(mode=mode), "mode")
            == raw
        )


def test_previous_is_ignored():
    dev = device()
    on = HvacState(True, "cool", 22.0)
    off = HvacState(False, "cool", 22.0)
    assert dev.encode(off, on).signal == dev.encode(None, on).signal
    assert dev.encode(on, on).signal == dev.encode(None, on).signal


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (3300, 1700)
    assert pulses[-2:] == (400, 100000)
    assert len(pulses) == 2 + 2 * 296 + 2


@pytest.mark.parametrize(
    "declared, field", [((UNSET_LOW,), "'unset'"), ((UNSET,), "'unset_low'")]
)
def test_undeclared_deviation_is_reported(declared, field):
    dev = device()
    record = load_oracle("HITACHI_AC296")[0]
    with pytest.raises(AssertionError, match=field):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=declared)


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("HITACHI_AC296")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)


def test_stale_high_padding_bit_is_a_declared_defect():
    # Byte 13 bit 7 is also never written by stateReset: C sends whatever
    # memory holds there. A C frame with a 1 in it must be accepted as that
    # declared defect, not fail as an unexplained byte difference.
    from pyhvac.ir.codec import encode
    from pyhvac.ir.model import Frame
    from pyhvac.protocols.hitachi import HITACHI296_LAYOUT

    assert "unset_high" in HITACHI296_LAYOUT.fields
    dev = device()
    record = load_oracle("HITACHI_AC296")[0]
    ours = dev.frames(None, state_from_record(dev, record["state"]), ())
    stale = bytearray(ours[0].data)
    HITACHI296_LAYOUT.write_raw(stale, "unset_high", 1)
    HITACHI296_LAYOUT.checksum.apply(stale)
    theirs = encode(dev.PROTOCOL, [Frame(ours[0].section, bytes(stale))])
    stale_record = {"state": record["state"], "pulses": list(theirs.pulses)}
    assert_matches_oracle(dev, stale_record, dev.LAYOUTS, DEFECTS)


# No real capture in ir_Hitachi_test.cpp needs it, but decodeHitachiAc296
# matches with kUseDefTol (25 %) and no mark excess.
def test_decode_tolerance_is_the_c_decoders():
    assert (HITACHI296.tolerance, HITACHI296.mark_excess) == (0.25, 0)
