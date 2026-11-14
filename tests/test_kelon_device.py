import pytest

from oracle import load_oracle
from port_oracle import (
    Defect,
    assert_matches_oracle,
    assert_sequence_matches_c,
    oracle_params,
    sequence_params,
    state_from_record,
)
from pyhvac.protocols.kelon import KELON_LAYOUT, KELON_MODELS, KelonDevice, KELON
from pyhvac.state import HvacState

# The C path deviates from the documented Kelon values here:
# - IRac::kelon calls setSupercool(false) after setMode; its else branch calls
#   setMode(_previousMode), and _previousMode is kKelonModeHeat (0) from
#   stateReset, so every C message is mode heat. That includes off messages
#   (convertMode maps them to kKelonModeSmart, 26C), which carry the target
#   mode in the port. Oracle off records read as mode auto, so they are
#   covered by the auto entry.
# - the legacy glue (IRGHVAC.build_ircode) has no "sleep" key, so IRac gets
#   sleep -1 and setSleep(sleep >= 0) always clears SleepEnabled.
DEFECTS = (
    Defect("mode", "auto", "heat", "setSupercool(false) reverts to heat"),
    Defect("mode", "cool", "heat", "setSupercool(false) reverts to heat"),
    Defect("mode", "dry", "heat", "setSupercool(false) reverts to heat"),
    Defect("mode", "fan", "heat", "setSupercool(false) reverts to heat"),
    Defect("sleep", 1, 0, "legacy glue never passes sleep"),
)


def device():
    return KelonDevice("kelon", "remote")


def state(power=True, mode="cool", temperature=22.0, **kw):
    return device().normalise(HvacState(power, mode, temperature, **kw))


def read(target, previous=None):
    (main,) = device().frames(previous, target, ())
    return KELON_LAYOUT.read(main.data)


@pytest.mark.parametrize("record", oracle_params("KELON"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


@pytest.mark.parametrize("record, states", sequence_params("KELON"))
def test_sequence_matches_a_persistent_c_object(record, states):
    # The power toggle depends on the message before, which C's IRac keeps.
    dev = device()
    assert_sequence_matches_c(dev, record, states, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("KELON"):
        (main,) = dev.frames(None, state_from_record(dev, record["state"]), ())
        values = KELON_LAYOUT.read(main.data)
        assert KELON_LAYOUT.build(**values) == bytearray(main.data)


@pytest.mark.parametrize(
    "raw, fields",
    [
        # ir_Kelon_test.cpp: 26C cool auto; 23C heat with power toggle;
        # dry with swing toggle (26C); dry at grade -2.
        (0x82000683, {"mode": "cool", "temperature": 26, "fan": "auto"}),
        (0x50040683, {"mode": "heat", "temperature": 23, "power_toggle": 1}),
        (0x83800683, {"mode": "dry", "temperature": 26, "swing_toggle": 1}),
        (0x83600683, {"mode": "dry", "dry_grade": 0b110}),
        # Timer12HSmartMode: smart mode, SmartModeEnabled clear, 12 h timer.
        (
            0x1679030683,
            {"mode": "auto", "smart": 0, "timer": 1, "timer_hours": 11, "fan": "1"},
        ),
        # SendDataOnly: 18C cool, super cool (both bits), raw fan 1 (max).
        (0x900002010683, {"super_cool1": 1, "super_cool2": 1, "fan": "3"}),
        # Timer5_5hSuperCoolMode: only SuperCoolEnabled1 is set here.
        (0x100B0A010683, {"super_cool1": 1, "super_cool2": 0, "timer_hours": 5}),
    ],
)
def test_layout_reads_the_real_captures(raw, fields):
    data = raw.to_bytes(6, "little")
    values = KELON_LAYOUT.read(data)
    assert {k: values[k] for k in fields} == fields
    assert KELON_LAYOUT.build(**values) == bytearray(data)


def test_port_reproduces_the_cool_capture():
    # 0x82000683: 26C, cool, fan auto, no toggle (a change while on).
    on = state(True, "cool", 26.0)
    (main,) = device().frames(on, on, ())
    assert main.data == (0x82000683).to_bytes(6, "little")


def test_port_reproduces_the_heat_power_toggle_capture():
    # 0x50040683: 23C, heat, fan auto, power toggle.
    (main,) = device().frames(None, state(True, "heat", 23.0), ())
    assert main.data == (0x50040683).to_bytes(6, "little")


@pytest.mark.parametrize("mode", ["cool", "heat"])
@pytest.mark.parametrize("t", [18.0, 25.0, 32.0])
def test_setpoint_is_sent_in_cool_and_heat(mode, t):
    assert read(state(True, mode, t))["temperature"] == int(t)


@pytest.mark.parametrize("mode, fixed", [("auto", 26), ("dry", 25), ("fan", 25)])
@pytest.mark.parametrize("t", [18.0, 25.0, 32.0])
def test_setmode_forces_the_temperature(mode, fixed, t):
    # IRKelonAc::setMode forces 26C (smart) and 25C (dry, fan); C sends it.
    assert read(state(True, mode, t))["temperature"] == fixed


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan", "heat"])
@pytest.mark.parametrize("t", [18.0, 32.0])
def test_off_carries_the_target_mode_and_its_temperature(mode, t):
    # Ruling: not kKelonModeSmart (convertMode's "off"), which would risk
    # switching the unit on; the same temperature rules as when powered.
    values = read(state(False, mode, t))
    expected = {"auto": 26, "dry": 25, "fan": 25}.get(mode, int(t))
    assert (values["mode"], values["temperature"]) == (mode, expected)
    assert values["power_toggle"] == 0


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan", "heat"])
def test_mode_uses_its_documented_value(mode):
    codes = {"heat": 0, "auto": 1, "cool": 2, "dry": 3, "fan": 4}
    (main,) = device().frames(None, state(True, mode), ())
    assert KELON_LAYOUT.read_raw(main.data, "mode") == codes[mode]


def test_smart_bit_stays_clear():
    # As the C output and the real smart mode capture 0x1679030683.
    for power in (True, False):
        assert read(state(power, "auto"))["smart"] == 0


@pytest.mark.parametrize("fan, raw", [("auto", 0), ("1", 3), ("2", 2), ("3", 1)])
def test_every_fan_level_uses_its_documented_raw_code(fan, raw):
    # The header: raw 0 auto, 1 max, 2 medium, 3 min.
    (main,) = device().frames(None, state(fan=fan), ())
    assert KELON_LAYOUT.read_raw(main.data, "fan") == raw


def test_sleep_sets_the_sleep_bit():
    on = state(features={"sleep": True})
    off = state(features={"sleep": False})
    assert (read(on)["sleep"], read(off)["sleep"]) == (1, 0)


def test_unset_features_stay_clear():
    values = read(state(True, "cool", 22.0, fan="3", features={"sleep": True}))
    for name in (
        "dry_grade",
        "swing_toggle",
        "timer",
        "timer_half_hour",
        "timer_hours",
        "super_cool1",
        "super_cool2",
    ):
        assert values[name] == 0, name


def test_power_toggle_without_previous_is_the_target_power():
    # A fresh IRac's previous state is protocol UNKNOWN: handleToggles does
    # nothing, so PowerToggle = power.
    assert read(state(True, "heat", 20.0))["power_toggle"] == 1
    assert read(state(False, "heat", 20.0))["power_toggle"] == 0


@pytest.mark.parametrize(
    "before, after, toggle",
    [(True, True, 0), (True, False, 1), (False, False, 0), (False, True, 1)],
)
def test_power_toggle_with_previous_toggles_on_change(before, after, toggle):
    # IRac::handleToggles' KELON rule (power ^ prev.power), which a persistent
    # IRac applies (test_sequence_matches_a_persistent_c_object checks it).
    previous = state(before, "cool", 22.0)
    target = state(after, "cool", 22.0)
    assert read(target, previous)["power_toggle"] == toggle


def test_encode_passes_previous_to_the_toggle():
    dev = device()
    on = HvacState(True, "cool", 22.0)
    assert dev.encode(None, on).signal != dev.encode(on, on).signal


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (9000, 4600)
    assert pulses[-2:] == (560, 200000)
    assert len(pulses) == 2 + 2 * 48 + 2


def test_capabilities_are_the_documented_values():
    caps = device().capabilities
    # kKelonMinTemp / kKelonMaxTemp, whole degrees.
    assert (caps.temperature.min, caps.temperature.max) == (18.0, 32.0)
    assert caps.modes == ("auto", "cool", "fan", "dry", "heat")
    assert caps.fan.values == ("auto", "1", "2", "3")  # kKelonFan{Auto,Min..Max}
    assert caps.swing_v.values == ("off", "swing")  # SwingVToggle: new
    assert caps.swing_h is None
    # SleepEnabled; SuperCoolEnabled1/2 as powerful (new).
    assert set(caps.features) == {"sleep", "powerful"}


def test_swing_toggle_without_previous_is_the_target_swing():
    # A fresh IRac: sendAc passes swingv != kOff as the toggle.
    assert read(state(swing_v="swing"))["swing_toggle"] == 1
    assert read(state(swing_v="off"))["swing_toggle"] == 0


@pytest.mark.parametrize(
    "before, after, toggle",
    [
        ("off", "off", 0),
        ("off", "swing", 1),
        ("swing", "swing", 0),
        ("swing", "off", 1),
    ],
)
def test_swing_toggle_with_previous_toggles_on_change(before, after, toggle):
    # IRac::handleToggles' KELON case: toggle when off <-> not-off changes.
    previous = state(True, "cool", 22.0, swing_v=before)
    target = state(True, "cool", 22.0, swing_v=after)
    values = read(target, previous)
    assert (values["swing_toggle"], values["power_toggle"]) == (toggle, 0)


def test_port_reproduces_the_swing_toggle_capture_but_for_its_dry_setpoint():
    # TestSwingToggleDryMode, 0x83800683: dry, fan auto, swing toggle, no
    # power toggle. The remote sent 26C in dry; the port (as the C path,
    # IRKelonAc::setMode) sends 25C there (see KELON_FIXED_TEMPERATURE).
    on = state(True, "dry", 22.0)
    target = state(True, "dry", 22.0, swing_v="swing")
    (main,) = device().frames(on, target, ())
    capture = (0x83800683).to_bytes(6, "little")
    assert KELON_LAYOUT.read(main.data) == {
        **KELON_LAYOUT.read(capture),
        "temperature": 25,
    }


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan", "heat"])
@pytest.mark.parametrize("fan", ["auto", "1", "3"])
def test_powerful_is_super_cool(mode, fan):
    # IRKelonAc::setSupercool(true): kKelonMinTemp, cool, kKelonFanMax and
    # both SuperCoolEnabled bits, whatever the target's mode, setpoint, fan.
    values = read(state(True, mode, 27.0, fan=fan, features={"powerful": True}))
    assert (values["mode"], values["temperature"], values["fan"]) == ("cool", 18, "3")
    assert (values["super_cool1"], values["super_cool2"]) == (1, 1)


def test_port_reproduces_the_super_cool_capture():
    # SendDataOnly, 0x900002010683: 18C cool, fan max, super cool, no toggle.
    on = state(True, "heat", 24.0, features={"powerful": True})
    (main,) = device().frames(on, on, ())
    assert main.data == (0x900002010683).to_bytes(6, "little")


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan"])
def test_undeclared_mode_deviation_is_reported(mode):
    dev = device()
    record = next(r for r in load_oracle("KELON") if r["state"]["mode"] == mode)
    defects = [d for d in DEFECTS if d.field != "mode"]
    with pytest.raises(AssertionError, match="mode"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects)


def test_undeclared_sleep_deviation_is_reported():
    dev = device()
    record = next(r for r in load_oracle("KELON") if r["state"].get("sleep") == "on")
    defects = [d for d in DEFECTS if d.field != "sleep"]
    with pytest.raises(AssertionError, match="sleep"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects)


def test_heat_needs_no_defect():
    # C's mode revert lands on heat, so heat records match exactly.
    dev = device()
    for record in load_oracle("KELON"):
        if record["state"]["mode"] == "heat":
            assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("KELON")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)


# No real capture in ir_Kelon_test.cpp needs it, but
# decodeKelon matches with _tolerance (25 %) and no mark excess.
def test_decode_tolerance_is_the_c_decoders():
    assert (KELON.tolerance, KELON.mark_excess) == (0.25, 0)


# ------------------------------------------------------ "dry-grade" variant
# Dry mode's setpoint sets the dehumidifier grade (-2..+2), relative to the
# 25 °C dry mode sends: SmartIR climate 1522, 2200, 2500, 5520 (Hisense,
# IGC, Endesa) step the grade with the temperature keys.


@pytest.mark.parametrize(
    "t, grade",
    [(20.0, 6), (23.0, 6), (24.0, 5), (25.0, 0), (26.0, 1), (27.0, 2), (30.0, 2)],
)
def test_dry_grade_variant_maps_the_dry_setpoint_to_the_grade(t, grade):
    dev = KelonDevice("Test", "unit", variant="dry-grade")
    (frame,) = dev.frames(None, dev.normalise(HvacState(True, "dry", t)), ())
    values = KELON_LAYOUT.read(frame.data)
    assert KELON_LAYOUT.read_raw(frame.data, "dry_grade") == grade
    assert values["temperature"] == 25


def test_dry_grade_variant_leaves_other_modes_alone():
    plain, graded = KelonDevice("T", "u"), KelonDevice("T", "u", variant="dry-grade")
    for mode in ("cool", "heat", "auto", "fan"):
        st = HvacState(True, mode, 22.0)
        assert plain.frames(None, plain.normalise(st), ()) == graded.frames(
            None, graded.normalise(st), ()
        )


# ------------------------------------------------------------ "16C" variant
# 16-30 °C, the setpoint field holding degrees - 16 (kKelonMinTemp is 18):
# SmartIR climate 1621 and 1624 (Tornado) send for each setpoint what the
# default sends for two degrees more.


@pytest.mark.parametrize("t", range(16, 31))
@pytest.mark.parametrize("mode", ["cool", "heat"])
def test_16c_variant_offsets_the_setpoint_by_two(mode, t):
    plain = KelonDevice("T", "u")
    low = KelonDevice("T", "u", variant="16C")
    target = HvacState(True, mode, float(t), fan="1")
    shifted = HvacState(True, mode, float(t + 2), fan="1")
    assert low.frames(None, low.normalise(target), ()) == plain.frames(
        None, plain.normalise(shifted), ()
    )


def test_16c_variant_offers_16_to_30():
    caps = KelonDevice("T", "u", variant="16C").capabilities.temperature
    assert (caps.min, caps.max) == (16.0, 30.0)
