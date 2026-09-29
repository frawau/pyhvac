import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.ir.codec import decode
from pyhvac.plugins.mitsubishi_electric import (
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


@pytest.mark.parametrize("model", MITSUBISHI_AC_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(
        registry.get_device("mitsubishi_electric", model), MitsubishiAcDevice
    )


@pytest.mark.parametrize("model", MITSUBISHI_AC_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.mitsubishi_electric import Mitsubishi

    legacy = LegacyDevice("mitsubishi_electric", model, Mitsubishi)
    assert device(model).capabilities == legacy.capabilities


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
