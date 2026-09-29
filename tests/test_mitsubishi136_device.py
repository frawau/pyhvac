import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac.ir.codec import decode
from pyhvac.protocols.mitsubishi_electric import (
    MITSUBISHI136,
    MITSUBISHI136_LAYOUT,
    MITSUBISHI136_MODELS,
    Mitsubishi136Device,
)
from pyhvac.state import HvacState

# Fan lowest: convertFan(kMin) gives kMitsubishi136FanMin, but IRac then calls
# setQuiet(false), and IRMitsubishi136::setQuiet turns FanMin (which is also
# kMitsubishi136FanQuiet) into kMitsubishi136FanLow. The port sends FanMin.
FAN_MIN = Defect("fan", 0, 1, "IRac's setQuiet(false) turns FanMin into FanLow")
# Swing positions count down from kMitsubishi136SwingVHighest. The legacy
# labels 90° and 60° reach C as kHigh and kUpperMiddle, which
# IRMitsubishi136::convertSwingV maps to SwingVHigh and SwingVAuto.
SWING_HIGHEST = Defect("swing_v", 3, 2, "C maps 90° (kHigh) to SwingVHigh")
SWING_HIGH = Defect("swing_v", 2, 12, "C maps 60° (kUpperMiddle) to SwingVAuto")
DEFECTS = (FAN_MIN, SWING_HIGHEST, SWING_HIGH)

# PEAD-RP71JAA capture (ir_Mitsubishi_test.cpp, DecodeRealExample):
# power on, cool, 20 C, fan Max, swing Highest, quiet off.
REAL_EXAMPLE = bytes.fromhex("23cb262100404137040000bfbec8fbffff")


# The oracle records use the legacy vocabulary, which offered values the
# protocol has no code for: fan "auto" (C sends kMitsubishi136FanMed), fan
# "high" (C sends kMitsubishi136FanMax, as "highest") and swing "off" (C sends
# kMitsubishi136SwingVAuto). They are read as the value C sent for them.
AS_SENT = {"fan": {"auto": "medium", "high": "highest"}, "swing": {"off": "auto"}}


def as_sent(record):
    state = {k: AS_SENT.get(k, {}).get(v, v) for k, v in record["state"].items()}
    return {**record, "state": state}


def device(model="PEAD-RP71JAA Ducted"):
    return Mitsubishi136Device("mitsubishi_electric", model)


def frame(state):
    dev = device()
    (main,) = dev.frames(None, dev.normalise(state), ())
    return main.data


def read(state):
    return MITSUBISHI136_LAYOUT.read(frame(state))


@pytest.mark.parametrize("record", oracle_params("MITSUBISHI136"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, as_sent(record), dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("MITSUBISHI136"):
        state = state_from_record(dev, as_sent(record)["state"])
        (main,) = dev.frames(None, state, ())
        values = MITSUBISHI136_LAYOUT.read(main.data)
        assert MITSUBISHI136_LAYOUT.build(**values) == bytearray(main.data)
        assert MITSUBISHI136_LAYOUT.checksum.check(main.data)


def test_every_oracle_frame_has_the_inverted_section():
    # IRMitsubishi136::checksum: bytes 11-16 are ~bytes 5-10.
    for record in load_oracle("MITSUBISHI136"):
        (main,) = decode(MITSUBISHI136, record["pulses"], expected=["main"])
        assert all(main.data[11 + i] == ~main.data[5 + i] & 0xFF for i in range(6))
        assert MITSUBISHI136_LAYOUT.checksum.check(main.data)


def test_no_field_overlaps_the_inverted_section():
    checked = {
        b for byte in (11, 12, 13, 14, 15, 16) for b in range(8 * byte, 8 * byte + 8)
    }
    assert MITSUBISHI136_LAYOUT.checksum.positions() == set(range(11, 17))
    for name, field in MITSUBISHI136_LAYOUT.fields.items():
        assert not checked & set(field.bits), name


def test_checksum_rejects_a_broken_frame():
    data = bytearray(frame(HvacState(True, "cool", 20.0)))
    data[14] ^= 0x01
    assert not MITSUBISHI136_LAYOUT.checksum.check(data)


def test_the_real_capture_is_reproduced():
    # With swing "1" as the documented Highest (the C path would send High).
    assert frame(HvacState(True, "cool", 20.0, fan="4", swing_v="1")) == (REAL_EXAMPLE)


def test_skeleton_keeps_the_reset_bytes():
    # stateReset: 23 CB 26 21 00 then zeros from byte 9; byte 7 bit 0 set.
    data = MITSUBISHI136_LAYOUT.build(checksum=False)
    assert data[:5] == bytes.fromhex("23cb262100")
    assert data[7] & 1 and data[8] == 0x04
    assert data[9:11] == b"\x00\x00"


@pytest.mark.parametrize("mode", ["auto", "cool", "fan", "dry", "heat"])
@pytest.mark.parametrize("temp", [16.0, 20.0, 25.0])
def test_off_carries_mode_auto_in_every_mode(mode, temp):
    # IRac passes mode "off"; IRMitsubishi136::convertMode maps it to auto.
    values = read(HvacState(False, mode, temp))
    assert (values["power"], values["mode"]) == (0, "auto")
    assert values["temperature"] == max(int(temp), 17) - 16


@pytest.mark.parametrize(
    "mode, raw", [("fan", 0), ("cool", 1), ("heat", 2), ("auto", 3), ("dry", 5)]
)
def test_mode_codes(mode, raw):
    values = read(HvacState(True, mode, 20.0))
    assert values["power"] == 1
    assert (
        MITSUBISHI136_LAYOUT.read_raw(frame(HvacState(True, mode, 20.0)), "mode") == raw
    )


@pytest.mark.parametrize(
    "temp, raw",
    [(10.0, 1), (16.0, 1), (17.0, 1), (20.0, 4), (25.0, 9), (30.0, 14), (35.0, 14)],
)
def test_setpoint_is_whole_degrees_clamped_to_17_30(temp, raw):
    # setTemp clamps to kMitsubishi136MinTemp/MaxTemp (17-30) and stores
    # degrees - 16.
    assert read(HvacState(True, "cool", temp))["temperature"] == raw


def test_capabilities_are_the_documented_values():
    caps = device().capabilities
    # kMitsubishi136MinTemp / kMitsubishi136MaxTemp, whole degrees.
    assert (caps.temperature.min, caps.temperature.max) == (17.0, 30.0)
    assert caps.temperature.decimals == (0,)
    # kMitsubishi136FanMin/Low/Med/Max: no auto code.
    assert caps.fan.values == ("1", "2", "3", "4")
    # kMitsubishi136SwingVAuto and four positions: no off code.
    assert caps.swing_v.values == ("auto", "1", "2", "3", "4")
    assert caps.swing_h is None
    assert set(caps.features) == {"quiet"}


@pytest.mark.parametrize("fan", ["auto", "5"])
def test_fans_without_a_code_are_not_offered(fan):
    # Removed: auto (C sent kMitsubishi136FanMed) and a fifth speed (C sent
    # kMitsubishi136FanMax, as "4").
    assert fan not in device().capabilities.fan.values


def test_swing_off_is_not_offered():
    # There is no kMitsubishi136SwingV off code; C sent SwingVAuto.
    assert "off" not in device().capabilities.swing_v.values
    assert device().normalise(HvacState(True, "cool", 22.0)).swing_v == "auto"


def test_setpoint_is_kept_in_every_mode():
    for mode in ("auto", "cool", "fan", "dry", "heat"):
        assert read(HvacState(True, mode, 22.0))["temperature"] == 6


@pytest.mark.parametrize("fan, raw", [("1", 0), ("2", 1), ("3", 2), ("4", 3)])
def test_every_fan_level(fan, raw):
    # kMitsubishi136FanMin, FanLow, FanMed, FanMax.
    assert read(HvacState(True, "cool", 22.0, fan=fan))["fan"] == raw


@pytest.mark.parametrize("fan", ["1", "2", "3", "4"])
def test_quiet_forces_the_quiet_fan(fan):
    state = HvacState(True, "cool", 22.0, fan=fan, features={"quiet": True})
    assert read(state)["fan"] == 0  # kMitsubishi136FanQuiet
    off = HvacState(False, "heat", 22.0, fan=fan, features={"quiet": True})
    assert read(off)["fan"] == 0


@pytest.mark.parametrize(
    "swing, raw",
    [("auto", 12), ("1", 3), ("2", 2), ("3", 1), ("4", 0)],
)
def test_every_swing_value(swing, raw):
    # SwingVAuto, then the positions counting down from SwingVHighest.
    assert read(HvacState(True, "cool", 22.0, swing_v=swing))["swing_v"] == raw


def test_previous_is_ignored():
    dev = device()
    on = HvacState(True, "cool", 22.0, swing_v="1")
    off = HvacState(False, "cool", 22.0)
    assert dev.encode(off, on).signal == dev.encode(None, on).signal
    assert dev.encode(on, on).signal == dev.encode(None, on).signal


def test_message_shape():
    signal = device().encode(None, HvacState(True, "cool", 22.0)).signal
    assert signal.carrier == 38000
    assert signal.pulses[:2] == (3324, 1474)
    assert signal.pulses[-2:] == (467, 100000)
    assert len(signal.pulses) == 2 + 2 * 136 + 2


def _record(swing=None, fan=None):
    return next(
        as_sent(r)
        for r in load_oracle("MITSUBISHI136")
        if (swing is None or r["state"].get("swing") == swing)
        and (fan is None or r["state"].get("fan") == fan)
        and "quiet" not in r["state"]
    )


@pytest.mark.parametrize(
    "record_kw, missing",
    [
        ({"fan": "lowest"}, FAN_MIN),
        ({"swing": "90°"}, SWING_HIGHEST),
        ({"swing": "60°"}, SWING_HIGH),
    ],
)
def test_undeclared_deviation_is_reported(record_kw, missing):
    dev = device()
    record = _record(**record_kw)
    declared = tuple(d for d in DEFECTS if d != missing)
    with pytest.raises(AssertionError, match=missing.field):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=declared)


def test_layouts_must_cover_every_frame():
    dev = device()
    record = _record(swing="90°")
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)


# No real capture in ir_Mitsubishi_test.cpp needs it, but
# decodeMitsubishi136 matches with _tolerance (25 %) and no mark excess.
def test_decode_tolerance_is_the_c_decoders():
    assert (MITSUBISHI136.tolerance, MITSUBISHI136.mark_excess) == (0.25, 0)


@pytest.mark.parametrize("fan", ["auto", "5"])
def test_a_fan_the_protocol_lacks_sends_medium(fan):
    # No auto fan: IRac's default fan (kAuto) reached C, which sent
    # kMitsubishi136FanMed, so an unoffered fan normalises to medium.
    dev = device()
    state = dev.normalise(HvacState(True, "cool", 24.0, fan=fan))
    assert state.fan == "3"
