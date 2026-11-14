import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac.ir.codec import decode
from pyhvac.protocols.mitsubishi_electric import (
    MITSUBISHI_AC,
    MITSUBISHI_AC_LAYOUT,
    MITSUBISHI_AC_MODELS,
    MitsubishiAcDevice,
)
from pyhvac.state import HvacState

# The C path deviates from the documented kMitsubishiAcVane* positions here:
# the old labels go through IRGHVAC.trans_swing ("90°" -> kHigh, "60°" ->
# kUpperMiddle) into IRMitsubishiAC::convertSwingV, which maps kHigh to
# kMitsubishiAcVaneHigh (so kMitsubishiAcVaneHighest is never sent) and has
# no kUpperMiddle case (it falls back to kMitsubishiAcVaneAuto). IRac writes
# the same value into Vane and VaneLeft.
DEFECTS = tuple(
    Defect(field, ours, theirs, reason)
    for field in ("swing_v", "swing_v_left")
    for ours, theirs, reason in (
        ("1", "2", "C sends VaneHigh (0b010) for the highest position"),
        ("2", "off", "C has no upper-middle case: sends VaneAuto (0b000)"),
    )
)

# The library's reset state (kReset, ir_Mitsubishi_test.cpp): power on, heat,
# 22 C, fan 5 (FanAuto clear), Vane auto with VaneBit, WideVane middle,
# Clock 0x67, checksum 0x1F.
RESET_CAPTURE = bytes.fromhex("23cb2601002008063045670000000000001f")


def device(model="MSZ-GV2519"):
    return MitsubishiAcDevice("mitsubishi_electric", model)


def with_hswing(record):
    # A record without "hswing" leaves IRac's swingh at kOff, which
    # IRMitsubishiAC::convertSwingH maps to its default, WideVane Middle:
    # canonical "3" (the oracle records match only so). The port
    # has no "off" swing_h (the legacy entity has none), so the record is
    # read as "middle".
    if "hswing" in record["state"]:
        return record
    return {**record, "state": {**record["state"], "hswing": "middle"}}


def read(state):
    dev = device()
    first, second = dev.frames(None, dev.normalise(state), ())
    assert first == second
    return MITSUBISHI_AC_LAYOUT.read(first.data)


@pytest.mark.parametrize("record", oracle_params("MITSUBISHI_AC"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, with_hswing(record), dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("MITSUBISHI_AC"):
        state = state_from_record(dev, with_hswing(record)["state"])
        for frame in dev.frames(None, state, ()):
            values = MITSUBISHI_AC_LAYOUT.read(frame.data)
            assert MITSUBISHI_AC_LAYOUT.build(**values) == bytearray(frame.data)
            assert MITSUBISHI_AC_LAYOUT.checksum.check(frame.data)


def test_every_oracle_message_is_one_frame_sent_twice():
    for record in load_oracle("MITSUBISHI_AC"):
        first, second = decode(MITSUBISHI_AC, record["pulses"], ["main", "main"])
        assert first == second


def test_reset_state_capture_reads_back():
    # The known-good state of stateReset, as captured in the library's tests.
    values = MITSUBISHI_AC_LAYOUT.read(RESET_CAPTURE)
    assert MITSUBISHI_AC_LAYOUT.checksum.check(RESET_CAPTURE)
    assert (values["power"], values["mode"], values["temperature"]) == (1, "heat", 22)
    assert (values["swing_h"], values["swing_v"], values["vane_bit"]) == ("3", "off", 1)
    assert (values["fan"], values["fan_auto"], values["clock"]) == (5, 0, 0x67)


def test_the_port_reproduces_the_reset_capture_but_for_its_fan():
    # kReset has Fan 5 without FanAuto; setFan never stores 5 unless asked for
    # silent, so the nearest state is lowest (Fan 5, FanAuto clear).
    state = HvacState(True, "heat", 22.0, fan="1", swing_h="3")
    dev = device()
    first, _ = dev.frames(None, dev.normalise(state), ())
    assert first.data == RESET_CAPTURE


@pytest.mark.parametrize("mode", ["auto", "cool", "fan", "dry", "heat"])
@pytest.mark.parametrize("t", [16.0, 31.0])
def test_off_carries_mode_auto_and_the_rest_of_the_state(mode, t):
    # IRac passes mode "off"; convertMode maps it to kMitsubishiAcAuto, and
    # setMode writes byte 8's low nibble for auto (0).
    values = read(HvacState(False, mode, t, fan="3", swing_v="4", swing_h="6"))
    assert (values["power"], values["mode"], values["mode_aux"]) == (0, "auto", 0)
    assert (values["temperature"], values["fan"]) == (int(t), 2)
    assert (values["swing_v"], values["swing_v_left"], values["swing_h"]) == (
        "4",
        "4",
        "6",
    )


@pytest.mark.parametrize(
    "mode, code, aux",
    [("auto", 4, 0), ("cool", 3, 6), ("dry", 2, 2), ("heat", 1, 0), ("fan", 7, 7)],
)
def test_mode_codes_and_the_byte_8_nibble_set_mode_writes(mode, code, aux):
    values = read(HvacState(True, mode, 22.0))
    assert MITSUBISHI_AC_LAYOUT.fields["mode"].values[values["mode"]] == code
    assert (values["mode"], values["mode_aux"]) == (mode, aux)


@pytest.mark.parametrize(
    "t, whole, half",
    [(16.0, 16, 0), (16.5, 16, 1), (22.5, 22, 1), (30.5, 30, 1), (31.0, 31, 0)],
)
def test_setpoint_has_half_degrees(t, whole, half):
    values = read(HvacState(True, "cool", t))
    assert (values["temperature"], values["half_degree"]) == (whole, half)


def test_setpoint_is_clamped_to_16_31():
    assert read(HvacState(True, "cool", 10.0))["temperature"] == 16
    assert read(HvacState(True, "heat", 35.0))["temperature"] == 31
    assert read(HvacState(True, "heat", 35.0))["half_degree"] == 0


@pytest.mark.parametrize(
    "fan, raw, auto",
    [("auto", 0, 1), ("1", 5, 0), ("2", 1, 0), ("3", 2, 0), ("4", 3, 0), ("5", 4, 0)],
)
def test_every_fan_level_uses_set_fan(fan, raw, auto):
    # convertFan: lowest -> kMitsubishiAcFanSilent (6), which setFan stores as
    # 5; low..highest -> kMitsubishiAcFanRealMax - 3 .. RealMax.
    values = read(HvacState(True, "cool", 22.0, fan=fan))
    assert (values["fan"], values["fan_auto"]) == (raw, auto)


@pytest.mark.parametrize(
    "swing_v, raw",
    [("off", 0), ("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 5), ("auto", 7)],
)
def test_every_swing_v_position_drives_both_vanes(swing_v, raw):
    dev = device()
    first, _ = dev.frames(
        None, dev.normalise(HvacState(True, "cool", 22.0, swing_v=swing_v)), ()
    )
    raws = {
        k: MITSUBISHI_AC_LAYOUT.read_raw(first.data, k)
        for k in ("swing_v", "swing_v_left", "vane_bit")
    }
    assert raws == {"swing_v": raw, "swing_v_left": raw, "vane_bit": 1}


@pytest.mark.parametrize(
    "swing_h, raw",
    [("auto", 8), ("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 5), ("6", 6)],
)
def test_every_swing_h_position(swing_h, raw):
    dev = device()
    first, _ = dev.frames(
        None, dev.normalise(HvacState(True, "cool", 22.0, swing_h=swing_h)), ()
    )
    assert MITSUBISHI_AC_LAYOUT.read_raw(first.data, "swing_h") == raw


def test_unset_features_stay_clear():
    values = read(HvacState(True, "heat", 16.0))
    for name in (
        "isee",
        "stop_clock",
        "start_clock",
        "timer",
        "weekly_timer",
        "ecocool",
        "direct_indirect",
        "absense_detect",
        "isave_10c",
        "natural_flow",
    ):
        assert values[name] == 0, name
    assert values["clock"] == 0x67  # kReset's clock: IRac never sets one


def test_previous_is_ignored():
    dev = device()
    on = HvacState(True, "cool", 22.0)
    off = HvacState(False, "cool", 22.0)
    assert dev.encode(off, on).signal == dev.encode(None, on).signal
    assert dev.encode(on, on).signal == dev.encode(None, on).signal


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    one = 2 + 2 * 144 + 2
    assert len(pulses) == 2 * one
    for start in (0, one):
        assert pulses[start : start + 2] == (3400, 1750)
        assert pulses[start + one - 2 : start + one] == (440, 15500)


def test_capabilities_are_the_documented_values():
    caps = device().capabilities
    # kMitsubishiAcMinTemp/MaxTemp, HalfDegree bit.
    assert (caps.temperature.min, caps.temperature.max) == (16.0, 31.0)
    assert caps.temperature.decimals == (0, 5)
    assert caps.modes == ("auto", "cool", "fan", "dry", "heat")
    assert caps.fan.values == ("auto", "1", "2", "3", "4", "5")
    assert caps.swing_v.values == ("off", "auto", "1", "2", "3", "4", "5")
    assert caps.swing_h.values == ("auto", "1", "2", "3", "4", "5", "6")
    # Quiet has no bit (kMitsubishiAcFanQuiet = FanSilent = fan "1").
    assert set(caps.features) == {"economy"}


@pytest.mark.parametrize("economy", [False, True])
def test_economy_is_the_ecocool_bit(economy):
    # Mitsubishi144Protocol byte 14 bit 5 (Ecocool, IRMitsubishiAC::setEcocool;
    # toString's "Econo"). Nothing else changes.
    state = HvacState(True, "cool", 22.0, features={"economy": economy})
    values = read(state)
    assert values["ecocool"] == economy
    plain = read(HvacState(True, "cool", 22.0))
    assert {**values, "ecocool": 0} == plain
    dev = device()
    first, _ = dev.frames(None, dev.normalise(state), ())
    assert (first.data[14] >> 5) & 1 == economy
    assert MITSUBISHI_AC_LAYOUT.checksum.check(first.data)


@pytest.mark.parametrize("label, field", [("90°", "swing_v"), ("60°", "swing_v")])
def test_undeclared_deviation_is_reported(label, field):
    dev = device()
    record = next(
        r for r in load_oracle("MITSUBISHI_AC") if r["state"].get("swing") == label
    )
    with pytest.raises(AssertionError, match=field):
        assert_matches_oracle(dev, with_hswing(record), dev.LAYOUTS, defects=())


def test_left_vane_deviation_must_be_declared_too():
    dev = device()
    record = next(
        r for r in load_oracle("MITSUBISHI_AC") if r["state"].get("swing") == "90°"
    )
    right_only = tuple(d for d in DEFECTS if d.field == "swing_v")
    with pytest.raises(AssertionError, match="swing_v_left"):
        assert_matches_oracle(dev, with_hswing(record), dev.LAYOUTS, right_only)


def test_missing_hswing_is_not_silently_accepted():
    dev = device()
    record = next(r for r in load_oracle("MITSUBISHI_AC") if "hswing" not in r["state"])
    with pytest.raises(AssertionError, match="swing_h"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("MITSUBISHI_AC")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, with_hswing(record), dev.LAYOUTS[:1], DEFECTS)


# ir_Mitsubishi_test.cpp DecodeMitsubishiAC.Issue891 and .Issue1759:
# decodeMitsubishiAC matches with _tolerance + kMitsubishiAcExtraTolerance
# (30 %) and no mark excess. Issue891 has bit marks as short as 336 µs for
# 450; Issue1759 a repeat space of 11330 µs for kMitsubishiAcRptSpace 15500.
RAW_891 = (
    "3418 1742 386 1342 398 1324 366 498 342 524 384 482 366 1354 340 528 "
    "366 500 396 1328 366 1354 340 522 340 1384 342 528 366 496 340 1382 "
    "398 1324 386 482 338 1386 420 1320 340 526 366 500 396 1324 398 466 "
    "384 480 340 1382 340 530 340 526 380 486 366 500 384 480 424 452 398 "
    "466 380 488 366 500 396 470 340 526 366 496 366 502 396 468 342 522 "
    "384 482 342 530 386 482 340 524 396 468 366 500 382 486 366 500 366 "
    "502 396 468 366 502 366 1356 340 1380 382 484 386 482 342 526 362 506 "
    "340 526 338 526 340 1388 366 500 380 486 366 500 366 498 380 488 416 "
    "1308 412 1316 368 500 384 1338 396 1324 382 488 368 498 380 488 340 "
    "524 366 502 384 480 418 452 396 468 340 1382 366 498 366 500 366 496 "
    "340 528 366 506 342 528 340 526 340 524 412 458 340 528 366 502 340 "
    "526 338 528 396 466 396 466 366 496 366 500 366 502 366 498 366 500 "
    "396 470 396 470 386 484 366 498 382 496 396 470 368 498 366 500 396 "
    "474 342 524 342 524 366 500 396 470 366 502 366 498 380 488 340 522 "
    "412 460 396 468 396 468 366 496 340 522 366 504 396 466 396 470 340 "
    "526 396 468 412 470 396 470 366 502 384 482 366 498 418 452 424 450 "
    "366 496 342 524 340 524 366 1356 396 1326 366 496 340 1382 396 470 366 "
    "1356 342 526 396 1322 386 17100 3524 1772 366 1358 396 1326 364 506 "
    "366 500 384 482 396 1324 340 526 340 524 342 1380 342 1382 342 526 338 "
    "1382 386 484 428 450 364 1356 366 1358 366 498 412 1312 382 1346 368 "
    "500 384 482 398 1326 366 500 396 466 412 1314 342 526 380 490 340 526 "
    "384 484 396 466 366 498 340 522 342 524 382 488 366 494 340 524 366 "
    "496 352 520 340 522 380 486 366 498 340 526 340 524 382 488 366 498 "
    "396 470 342 524 340 524 366 500 366 498 366 498 414 1312 366 1354 362 "
    "508 340 524 340 528 422 454 422 452 396 468 384 1340 366 502 412 460 "
    "426 450 396 466 382 486 366 1358 382 1344 414 458 366 1356 382 1342 "
    "386 482 366 494 386 482 342 524 342 524 380 484 366 500 384 480 428 "
    "1306 366 502 396 472 340 526 366 496 420 456 380 486 366 498 366 496 "
    "398 466 340 524 382 490 366 494 342 524 396 466 380 490 340 524 396 "
    "470 394 478 422 452 396 466 362 508 396 466 396 466 364 498 340 528 "
    "412 454 342 522 416 450 366 498 340 530 366 498 396 466 366 500 396 "
    "468 340 530 366 502 412 458 396 468 384 482 366 498 340 522 380 488 "
    "366 498 340 528 342 534 396 472 380 484 380 486 386 484 342 526 396 "
    "470 366 500 396 466 366 502 412 460 426 450 396 468 380 1344 340 1380 "
    "414 460 380 1342 386 482 366 1354 340 526 340 1386 396"
)
RAW_1759 = (
    "3392 1638 456 1220 456 1220 456 382 454 382 456 380 456 1222 454 380 "
    "456 382 456 1220 456 1220 456 382 454 1222 454 382 456 384 454 1222 "
    "454 1220 454 382 456 1220 456 1220 456 382 456 382 456 1220 456 380 "
    "456 382 456 1220 456 380 456 382 456 382 456 380 456 382 456 380 458 "
    "382 456 380 456 382 456 382 456 382 456 382 456 382 456 382 456 382 "
    "456 382 456 382 456 380 458 382 456 380 456 1220 456 380 456 382 456 "
    "382 456 382 456 382 456 1220 456 382 456 382 456 382 456 380 456 382 "
    "456 382 456 1220 456 382 456 382 456 382 456 382 454 382 456 382 456 "
    "382 456 382 454 384 454 382 456 380 456 382 456 382 456 382 456 382 "
    "454 382 456 382 456 382 456 382 456 1222 454 1220 456 382 456 382 456 "
    "382 454 1220 456 1220 454 1222 454 1220 454 382 456 382 456 382 454 "
    "382 454 382 456 382 456 382 456 382 454 382 456 380 456 382 454 382 "
    "454 384 454 382 456 382 454 384 454 382 456 382 456 382 456 384 454 "
    "384 454 382 456 382 454 382 454 384 454 382 456 1220 456 382 456 382 "
    "454 382 456 382 456 382 454 1220 456 382 456 382 456 382 456 382 454 "
    "382 456 382 456 382 454 382 456 382 454 382 456 382 456 382 456 382 "
    "456 382 456 382 456 382 454 1220 456 1220 456 380 456 1220 456 1220 "
    "456 1222 454 1220 456 1220 456 11280 3392 1638 454 1220 456 1220 456 "
    "382 456 382 456 382 456 1220 456 380 456 382 456 1220 456 1220 454 382 "
    "456 1220 456 382 456 382 456 1220 456 1222 454 382 456 1220 456 1220 "
    "454 382 456 382 456 1220 454 382 456 382 456 1220 456 382 456 382 454 "
    "382 456 382 454 382 456 382 456 382 456 382 456 382 454 382 456 382 "
    "456 382 456 382 456 382 456 382 456 382 454 382 456 382 456 382 456 "
    "382 456 1220 456 382 456 382 456 382 454 382 456 382 456 1220 456 380 "
    "456 382 456 382 456 382 456 382 456 382 456 1220 456 382 454 382 456 "
    "382 454 382 456 382 456 382 456 382 456 382 456 382 456 380 456 382 "
    "456 380 456 382 456 382 456 382 454 382 456 382 454 382 456 382 456 "
    "1220 454 1220 456 382 456 382 456 382 454 1220 456 1220 454 1222 454 "
    "1220 454 382 456 382 456 382 456 382 456 382 456 382 456 382 454 382 "
    "456 382 456 382 456 382 456 382 456 382 456 382 456 382 454 382 456 "
    "382 456 382 456 382 456 382 456 382 456 382 456 380 456 382 456 382 "
    "456 382 456 1220 456 382 456 382 456 382 454 382 456 382 456 1222 454 "
    "380 456 382 456 382 456 382 456 380 456 382 456 382 454 382 454 382 "
    "456 382 456 382 456 382 456 382 456 382 456 382 456 382 456 1220 456 "
    "1220 454 382 456 1222 454 1220 454 1220 454 1222 454 1220 456"
)


@pytest.mark.parametrize(
    "raw, state",
    [
        (RAW_891, "23cb260100001808364000000000000000ab"),
        (RAW_1759, "23cb26010020080400c078000000820000fb"),
    ],
    ids=["Issue891", "Issue1759"],
)
def test_real_raw_captures_decode(raw, state):
    pulses = [int(x) for x in raw.split()]
    frames = decode(MITSUBISHI_AC, pulses, expected=["main", "main"])
    assert [f.data.hex() for f in frames] == [state, state]


# ---------------------------------------------------------- "remote" variant
# As the remotes SmartIR captured send it (climate 1120-1138, 4124; e.g.
# KM09D): byte 9 bits 6-7 follow the key pressed (0b01 after a temperature
# key, 0b10 often after the others) and FanAuto is never set: fan auto is
# Fan 0 alone.


def remote_byte9(target):
    from pyhvac.protocols.mitsubishi_electric import MitsubishiAcDevice

    dev = MitsubishiAcDevice("Test", "unit", variant="remote")
    frame, _ = dev.frames(None, dev.normalise(target), ())
    return frame.data[9]


@pytest.mark.parametrize("fan", ["auto", "1", "2", "3", "4", "5"])
def test_remote_variant_fan_auto_is_fan_0_without_fanauto(fan):
    from pyhvac.protocols.mitsubishi_electric import MITSUBISHI_AC_FAN

    byte9 = remote_byte9(HvacState(True, "cool", 25.0, fan=fan))
    assert byte9 & 0b111 == MITSUBISHI_AC_FAN[fan][0]
    assert byte9 >> 6 == 0b01  # the temperature-key form, FanAuto clear


def test_remote_variant_names_bits_6_7_button():
    from pyhvac.protocols.mitsubishi_electric import (
        MITSUBISHI_AC_REMOTE_LAYOUT,
        MitsubishiAcDevice,
    )

    dev = MitsubishiAcDevice("Test", "unit", variant="remote")
    assert dev.LAYOUTS == (MITSUBISHI_AC_REMOTE_LAYOUT,) * 2
    assert "button" in MITSUBISHI_AC_REMOTE_LAYOUT.fields
    assert "fan_auto" not in MITSUBISHI_AC_REMOTE_LAYOUT.fields


@pytest.mark.parametrize(
    "mode, aux", [("auto", 6), ("cool", 6), ("dry", 2), ("heat", 0), ("fan", 0)]
)
def test_remote_variant_mode_aux_and_untouched_left_vane(mode, aux):
    from pyhvac.protocols.mitsubishi_electric import (
        MITSUBISHI_AC_REMOTE_LAYOUT,
        MitsubishiAcDevice,
    )

    dev = MitsubishiAcDevice("Test", "unit", variant="remote")
    target = HvacState(True, mode, 24.0, swing_v="2")
    frame, _ = dev.frames(None, dev.normalise(target), ())
    values = MITSUBISHI_AC_REMOTE_LAYOUT.read(frame.data)
    assert values["mode_aux"] == aux
    assert values["swing_v"] == "2" and values["swing_v_left"] == "off"
