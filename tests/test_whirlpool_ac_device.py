import pytest

from oracle import load_oracle
from port_oracle import (
    Defect,
    assert_matches_oracle,
    assert_sequence_matches_c,
    c_sequence,
    oracle_params,
    sequence_params,
    state_from_record,
)
from pyhvac import registry
from pyhvac.ir.codec import decode
from pyhvac.plugins.whirlpool import (
    WHIRLPOOL_AC,
    WHIRLPOOL_AC_LAYOUT,
    WHIRLPOOL_AC_MODELS,
    WhirlpoolAcDevice,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Whirlpool values here:
# - the legacy glue (IRGHVAC.trans_swing) has no "on", so IRac's swingv stays
#   kOff and setSwing(false) clears Swing1/Swing2;
# - the legacy glue (IRGHVAC.build_ircode) has no "sleep" key, so IRac gets
#   sleep -1: setSleep(false) clears Sleep and leaves the fan as requested,
#   where setSleep(true) sets kWhirlpoolAcFanLow;
# - IRac::whirlpool calls setPowerToggle(on) last, and setPowerToggle calls
#   setSuper(false): C never sends Super1/Super2 (setSuper(true)'s fan,
#   mode and setpoint changes stay).
SWING = Defect("swing", "swing", "off", "legacy glue has no swing 'on'")
SLEEP = Defect("sleep", 1, 0, "legacy glue never passes sleep")
SLEEP_FAN = tuple(
    Defect("fan", "1", fan, "setSleep(true) sets fan low; sleep never reaches C")
    for fan in ("auto", "2", "3")
)
SUPER = Defect("super", True, False, "setPowerToggle calls setSuper(false)")
DEFECTS = (SWING, SLEEP, SUPER) + SLEEP_FAN

LAYOUTS = WhirlpoolAcDevice.LAYOUTS
SECTIONS = ["first", "second", "third"]
MODES = ("auto", "cool", "dry", "fan", "heat")
V1, V2 = "generic", "generic 2"  # DG11J13A, DG11J191


def first_record(model):
    """The first oracle record of the legacy class serving ``model``."""
    cls = {V1: "Whirlpool", V2: "Whirlpoolv2"}[model]
    return next(r for r in load_oracle("WHIRLPOOL_AC") if r["class"] == cls)


def device(model=V1):
    return WhirlpoolAcDevice("whirlpool", model)


def state(power=True, mode="cool", temperature=22.0, model=V1, **kw):
    return device(model).normalise(HvacState(power, mode, temperature, **kw))


def data(target, model=V1, previous=None):
    return b"".join(f.data for f in device(model).frames(previous, target, ()))


def read(target, model=V1, previous=None):
    return WHIRLPOOL_AC_LAYOUT.read(data(target, model, previous))


def c_data(pulses):
    return b"".join(
        f.data for f in decode(WHIRLPOOL_AC, list(pulses), expected=SECTIONS)
    )


def _state(*hexbytes):
    return bytes.fromhex(" ".join(hexbytes))


# ir_Whirlpool_test.cpp, as the 21 logical bytes.
# RealExampleDecode (issue 509): auto, 25C, fan auto, clock 17:31, Cmd Temp.
REAL_EXAMPLE = _state("83 06 10 71 00 00 91 1F 00 00 00 00 00 EF 00 02 00 00 00 00 02")
# Real26CFanAutoCoolingSwingOnClock1918: cool, 26C, fan auto, swing, Cmd Swing.
REAL_SWING = _state("83 06 80 82 00 00 93 12 40 00 00 00 00 C3 00 07 00 00 00 00 07")
# RealTimerExample: dry, 25C, on timer 07:40, off timer 08:05, Cmd On Timer.
REAL_TIMER = _state("83 06 00 73 00 00 87 A3 08 85 07 28 00 F5 00 05 00 00 00 00 05")
# Known states in the IRWhirlpoolAc class tests:
# SetAndGetPowerToggle: DG11J191, power toggle, cool, 24C, fan low.
KNOWN_POWER = _state("83 06 07 82 00 00 93 04 00 00 00 00 00 12 00 01 00 00 08 00 09")
# SetAndGetFan: DG11J191, sleep, cool, 24C, fan low, Cmd Sleep.
KNOWN_SLEEP = _state("83 06 0B 82 00 00 93 04 00 00 00 00 00 1E 00 03 00 00 08 00 0B")
# SetAndGetSuper: DG11J191, Super, cool, 16C, fan high, timers, Cmd Super.
KNOWN_SUPER = _state("83 06 01 02 00 90 90 9F 00 A0 17 3A 00 11 00 04 00 00 08 00 0C")
# SetAndGetModel state_1 (DG11J191, heat, 19C, fan high) and state_2
# (DG11J13A, heat, 21C, fan auto), both Cmd Temp.
KNOWN_MODEL_1 = _state("83 06 01 30 00 00 92 36 00 00 00 00 00 95 00 02 00 00 08 00 0A")
KNOWN_MODEL_2 = _state("83 06 00 30 00 00 8B 35 00 00 00 00 00 8E 00 02 00 00 00 00 02")
CAPTURES = (
    REAL_EXAMPLE,
    REAL_SWING,
    REAL_TIMER,
    KNOWN_POWER,
    KNOWN_SLEEP,
    KNOWN_SUPER,
    KNOWN_MODEL_1,
    KNOWN_MODEL_2,
)


@pytest.mark.parametrize("record", oracle_params("WHIRLPOOL_AC"))
def test_matches_c_library(record):
    dev = device(record["model"])
    assert_matches_oracle(dev, record, LAYOUTS, DEFECTS)


@pytest.mark.parametrize("record, states", sequence_params("WHIRLPOOL_AC"))
def test_sequence_matches_a_persistent_c_object(record, states):
    # The power toggle depends on the message before, which C's IRac keeps.
    dev = device(record["model"])
    assert_sequence_matches_c(dev, record, states, LAYOUTS, DEFECTS)


@pytest.mark.parametrize("model", [V1, V2])
def test_power_sequence_matches_a_persistent_c_object(model):
    # The grid has no off state: switch on and off, in several modes.
    record = first_record(model)
    steps = [
        ("cool", 22),
        ("heat", 22),
        ("off", 22),
        ("off", 25),
        ("dry", 25),
        ("off", 25),
        ("fan", 30),
        ("auto", 30),
        ("off", 18),
        ("cool", 18),
    ]
    states = [{"mode": m, "temperature": t, "fan": "medium"} for m, t in steps]
    assert_sequence_matches_c(device(model), record, states, LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    for record in load_oracle("WHIRLPOOL_AC"):
        dev = device(record["model"])
        raw = data(state_from_record(dev, record["state"]), record["model"])
        values = WHIRLPOOL_AC_LAYOUT.read(raw)
        assert WHIRLPOOL_AC_LAYOUT.build(**values) == bytearray(raw)


# States the oracle grid lacks: off in every mode, every setpoint edge in
# every mode, every fan and swing, and the feature combinations.
EXTRA_STATES = (
    [
        {"mode": "off", "temperature": t, "fan": fan, "swing": swing}
        for t in (18, 25, 31, 32)
        for fan in ("auto", "low", "medium", "high")
        for swing in ("off", "on")
    ]
    + [
        {"mode": m, "temperature": t, "fan": "medium", "swing": "off"}
        for m in MODES
        for t in (18, 19, 29, 30, 31, 32)
    ]
    + [
        {
            "mode": mode,
            "temperature": 22,
            "fan": fan,
            "swing": "on",
            "light": light,
            "sleep": sleep,
            "powerful": powerful,
        }
        for mode in MODES + ("off",)
        for fan in ("auto", "low", "high")
        for light in ("off", "on")
        for sleep in ("off", "on")
        for powerful in ("off", "on")
    ]
)


@pytest.mark.parametrize("model", [V1, V2])
def test_states_beyond_the_oracle_grid_match_the_c_path(model):
    pytest.importorskip("pyhvac.irhvac")
    dev = device(model)
    record = first_record(model)
    for old in EXTRA_STATES:
        # One fresh C object per state, as the oracle records.
        (rec,) = c_sequence(record, [old])
        assert_matches_oracle(dev, rec, LAYOUTS, DEFECTS)


def _glue_fixed_c(model, cls, target):
    """C's bytes for ``target`` with sleep and swing "on" set on IRac
    directly (the two keys the legacy glue drops)."""
    from pyhvac import irhvac
    from pyhvac.legacy import LegacyDevice

    legacy = cls()
    old = LegacyDevice("whirlpool", model, cls).to_old(target)
    legacy.to_set = {k: v for k, v in old.items() if k not in ("swing", "sleep")}
    legacy.irac.next.sleep = 0 if target.features["sleep"] else -1
    legacy.irac.next.swingv = (
        irhvac.swingv_t_kAuto if target.swing_v == "swing" else irhvac.swingv_t_kOff
    )
    return c_data(int(x) for x in legacy.to_lirc(legacy.build_ircode()))


@pytest.mark.parametrize("model", [V1, V2])
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("fan", ["auto", "1", "2", "3"])
def test_sleep_and_swing_match_c_once_they_reach_it(model, mode, fan):
    # SWING, SLEEP and SLEEP_FAN are glue defects: with sleep and swing set
    # on IRac directly, C sends exactly the port's frames (Sleep, fan low,
    # Swing1/Swing2).
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.plugins.whirlpool import Whirlpool, Whirlpoolv2

    cls = {V1: Whirlpool, V2: Whirlpoolv2}[model]
    for sleep in (False, True):
        for swing in ("off", "swing"):
            target = state(
                True,
                mode,
                24.0,
                model,
                fan=fan,
                swing_v=swing,
                features={"sleep": sleep, "light": True},
            )
            assert data(target, model) == _glue_fixed_c(model, cls, target)


def test_checksums_hold_on_every_capture():
    checksum = WHIRLPOOL_AC_LAYOUT.checksum
    for capture in CAPTURES:
        assert checksum.check(capture)
    broken = bytearray(REAL_SWING)
    broken[11] ^= 0x01  # the last byte Sum1 covers
    assert not checksum.check(broken)
    broken = bytearray(REAL_SWING)
    broken[12] ^= 0x01  # Sum1 does not cover byte 12
    assert checksum.check(broken)
    broken[19] ^= 0x01  # the last byte Sum2 covers
    assert not checksum.check(broken)


@pytest.mark.parametrize(
    "capture, fields",
    [
        (
            REAL_EXAMPLE,
            {
                "mode": "auto",
                "temperature": 25 - 18,
                "fan": "auto",
                "swing": "off",
                "power": 0,
                "light_off": 0,
                "clock_hours": 17,
                "clock_mins": 31,
                "pad2": 0b001,
                "command": "temp",
                "model": "DG11J13A",
            },
        ),
        (
            REAL_TIMER,
            {
                "mode": "dry",
                "on_timer": 1,
                "on_hours": 7,
                "on_mins": 40,
                "off_timer": 1,
                "off_hours": 8,
                "off_mins": 5,
                "command": "on_timer",
            },
        ),
        (
            KNOWN_SUPER,
            {
                "mode": "cool",
                "temperature": 0,
                "fan": "3",
                "super": True,
                "command": "super",
                "model": "DG11J191",
            },
        ),
    ],
)
def test_layout_reads_the_captures(capture, fields):
    values = WHIRLPOOL_AC_LAYOUT.read(capture)
    assert {k: values[k] for k in fields} == fields
    assert WHIRLPOOL_AC_LAYOUT.build(**values) == bytearray(capture)


def _with(ours, capture, *fields):
    """``ours`` with ``fields`` copied from ``capture`` (checksums redone)."""
    out = bytearray(ours)
    for name in fields:
        WHIRLPOOL_AC_LAYOUT.write_raw(
            out, name, WHIRLPOOL_AC_LAYOUT.read_raw(capture, name)
        )
    WHIRLPOOL_AC_LAYOUT.checksum.apply(out)
    return bytes(out)


CLOCK = ("clock_hours", "clock_mins")
TIMERS = ("off_timer", "off_hours", "off_mins", "on_timer", "on_hours", "on_mins")
ON = {"light": True}


@pytest.mark.parametrize(
    "capture, model, target, previous, foreign",
    [
        # A setpoint change while running (and the capture's unnamed bit).
        (
            REAL_EXAMPLE,
            V1,
            HvacState(True, "auto", 25.0, fan="auto", features=ON),
            HvacState(True, "auto", 22.0, features=ON),
            CLOCK + ("command", "pad2"),
        ),
        # Swing on while running: no power toggle.
        (
            REAL_SWING,
            V1,
            HvacState(True, "cool", 26.0, fan="auto", swing_v="swing", features=ON),
            HvacState(True, "cool", 26.0, features=ON),
            CLOCK + ("command",),
        ),
        # Switched on from a fresh object: the power toggle, Cmd Power.
        (
            KNOWN_POWER,
            V2,
            HvacState(True, "cool", 24.0, fan="1", features=ON),
            None,
            CLOCK,
        ),
        # Sleep: fan low, as setSleep sets it.
        (
            KNOWN_SLEEP,
            V2,
            HvacState(True, "cool", 24.0, fan="3", features={**ON, "sleep": True}),
            HvacState(True, "cool", 24.0, features=ON),
            CLOCK + ("command",),
        ),
        # Super on DG11J191: cool, 16C, fan high, Super1/Super2.
        (
            KNOWN_SUPER,
            V2,
            HvacState(True, "dry", 25.0, features={**ON, "powerful": True}),
            HvacState(True, "dry", 25.0, features=ON),
            CLOCK + TIMERS + ("command",),
        ),
        (
            KNOWN_MODEL_1,
            V2,
            HvacState(True, "heat", 19.0, fan="3", features=ON),
            HvacState(True, "heat", 22.0, features=ON),
            CLOCK + ("command",),
        ),
        (
            KNOWN_MODEL_2,
            V1,
            HvacState(True, "heat", 21.0, fan="auto", features=ON),
            HvacState(True, "heat", 22.0, features=ON),
            CLOCK + ("command",),
        ),
    ],
)
def test_port_reproduces_the_captures_but_clock_timers_and_button(
    capture, model, target, previous, foreign
):
    # The entity sets no clock or timers, and C's button is always Power.
    dev = device(model)
    target = dev.normalise(target)
    previous = None if previous is None else dev.normalise(previous)
    assert _with(data(target, model, previous), capture, *foreign) == capture


@pytest.mark.parametrize("model, j191", [(V1, "DG11J13A"), (V2, "DG11J191")])
def test_model_sets_j191(model, j191):
    assert read(state(model=model), model)["model"] == j191


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize(
    "model, t, raw",
    [
        (V1, 16, 0),  # clamped to kWhirlpoolAcMinTemp
        (V1, 18, 0),
        (V1, 25, 7),
        (V1, 32, 14),
        # New: DG11J191 starts at 16C (kWhirlpoolAcMinTemp - 2).
        (V2, 16, 0),
        (V2, 17, 1),
        (V2, 18, 2),
        (V2, 25, 9),
        (V2, 30, 14),
        # DG11J191's range ends at 30C (kWhirlpoolAcMaxTemp - 2).
        (V2, 31, 14),
        (V2, 32, 14),
    ],
)
def test_setpoint_counts_from_the_models_minimum(mode, model, t, raw):
    values = read(state(True, mode, float(t), model), model)
    assert values["temperature"] == raw


@pytest.mark.parametrize("mode", MODES)
def test_mode_uses_its_documented_value(mode):
    codes = {"heat": 0, "auto": 1, "cool": 2, "dry": 3, "fan": 4}
    assert WHIRLPOOL_AC_LAYOUT.read_raw(data(state(True, mode)), "mode") == codes[mode]


@pytest.mark.parametrize("fan, raw", [("auto", 0), ("1", 3), ("2", 2), ("3", 1)])
def test_every_fan_level_uses_its_documented_code(fan, raw):
    # kWhirlpoolAcFanAuto/Low/Medium/High, as convertFan maps them.
    assert WHIRLPOOL_AC_LAYOUT.read_raw(data(state(fan=fan)), "fan") == raw


@pytest.mark.parametrize("swing, raw", [("off", 0), ("swing", 0b11)])
def test_swing_sets_swing1_and_swing2(swing, raw):
    ours = data(state(swing_v=swing))
    assert WHIRLPOOL_AC_LAYOUT.read_raw(ours, "swing") == raw
    assert (ours[2] >> 7, (ours[8] >> 6) & 1) == (raw & 1, raw >> 1)


@pytest.mark.parametrize("model", [V1, V2])
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("t", [18.0, 25.0, 32.0])
def test_off_carries_mode_cool_and_the_rest_of_the_state(model, mode, t):
    # IRac passes mode "off", which convertMode maps to its default, cool.
    off = state(False, mode, t, model, fan="2", swing_v="swing")
    assert data(off, model) == data(
        state(False, "cool", t, model, fan="2", swing_v="swing"), model
    )
    values = read(off, model)
    assert (values["mode"], values["fan"], values["swing"]) == ("cool", "2", "swing")
    low, high = (18, 32) if model == V1 else (16, 30)
    assert values["temperature"] == min(int(t), high) - low


def test_power_bit_without_previous_is_the_target_power():
    # A fresh IRac has no previous state: Power = on (a toggle for "on").
    assert read(state(True))["power"] == 1
    assert read(state(False))["power"] == 0


@pytest.mark.parametrize(
    "before, after, toggle",
    [(True, True, 0), (True, False, 1), (False, False, 0), (False, True, 1)],
)
def test_power_bit_with_previous_toggles_on_change(before, after, toggle):
    # As IRac::handleToggles: power = desired ^ previous.
    previous = state(before, "heat", 30.0)
    assert read(state(after), previous=previous)["power"] == toggle


def test_previous_only_decides_the_power_bit():
    target = state(True, "cool", 22.0, fan="2", swing_v="swing")
    fresh = read(target)
    for previous in (state(True, "heat", 30.0), state(True, "cool", 22.0)):
        assert read(target, previous=previous) == {**fresh, "power": 0}


def test_encode_passes_previous_to_the_toggle():
    dev = device()
    on = HvacState(True, "cool", 22.0)
    fresh = dev.encode(None, on).signal
    running = dev.encode(on, on).signal
    assert fresh != running
    assert c_data(fresh.pulses)[2] & 0b100
    assert not c_data(running.pulses)[2] & 0b100


@pytest.mark.parametrize("previous", [None, state(False)])
def test_button_is_always_power(previous):
    # IRac::whirlpool calls setPowerToggle last: Cmd = kWhirlpoolAcCommandPower.
    for target in (
        state(True, "auto"),
        state(False, "heat"),
        state(features={"sleep": True}),
        state(features={"powerful": True}),
        state(swing_v="swing"),
    ):
        assert read(target, previous=previous)["command"] == "power"


def test_unnamed_bits_of_byte_2_stay_clear():
    # stateReset clears them and no setter writes them, as C sends them.
    for target in (state(True), state(False, "heat", fan="3", swing_v="swing")):
        assert read(target)["pad2"] == 0


def test_light_clears_light_off():
    assert read(state(features={"light": True}))["light_off"] == 0
    assert read(state(features={"light": False}))["light_off"] == 1


@pytest.mark.parametrize("model", [V1, V2])
@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan"])
def test_powerful_is_cool_at_the_lowest_setpoint_and_fan_high(model, mode):
    # setSuper(true) outside heat: setFan(High), setTemp(min), setMode(Cool).
    values = read(
        state(True, mode, 25.0, model, fan="1", features={"powerful": True}), model
    )
    assert (values["mode"], values["temperature"], values["fan"]) == ("cool", 0, "3")
    assert values["super"] is True


@pytest.mark.parametrize("model", [V1, V2])
def test_powerful_in_heat_is_the_highest_setpoint_and_fan_high(model):
    # setSuper(true) in heat: setFan(High), setTemp(max).
    values = read(state(True, "heat", 20.0, model, features={"powerful": True}), model)
    assert (values["mode"], values["temperature"], values["fan"]) == ("heat", 14, "3")
    assert values["super"] is True


@pytest.mark.parametrize("fan", ["auto", "1", "2", "3"])
def test_sleep_sets_fan_low(fan):
    values = read(state(True, "heat", 22.0, fan=fan, features={"sleep": True}))
    assert (values["sleep"], values["fan"]) == (1, "1")


def test_sleep_cancels_super_but_keeps_its_mode_and_setpoint():
    # setSleep(true) runs after setSuper(true): its setFan(Low) cancels Super.
    both = {"sleep": True, "powerful": True}
    values = read(state(True, "dry", 25.0, fan="2", features=both))
    assert values["super"] is False
    assert (values["sleep"], values["fan"]) == (1, "1")
    assert (values["mode"], values["temperature"]) == ("cool", 0)


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (8950, 4484)
    first, second = 2 + 2 * 48, 2 + 2 * 48 + 2 + 2 * 64
    assert pulses[first : first + 2] == (597, 7920)
    assert pulses[second : second + 2] == (597, 7920)
    assert pulses[-2:] == (597, 100000)
    assert len(pulses) == 2 + 2 * 168 + 3 * 2


@pytest.mark.parametrize("model", sorted(WHIRLPOOL_AC_MODELS))
def test_registry_serves_the_port(model):
    dev = registry.get_device("whirlpool", model)
    assert isinstance(dev, WhirlpoolAcDevice)
    assert dev.variant == WHIRLPOOL_AC_MODELS[model]


def test_every_legacy_model_is_served_by_the_port():
    from pyhvac.plugins.whirlpool import PluginObject

    assert set(WHIRLPOOL_AC_MODELS) == set(PluginObject.MODELS)
    variant = {"Whirlpool": "DG11J13A", "Whirlpoolv2": "DG11J191"}
    for model, cls in PluginObject.MODELS.items():
        assert WHIRLPOOL_AC_MODELS[model] == variant[cls.__name__]


@pytest.mark.parametrize(
    "model, low, high",
    [
        (V1, 18.0, 32.0),  # kWhirlpoolAcMinTemp..kWhirlpoolAcMaxTemp
        (V2, 16.0, 30.0),  # the same, DG11J191's -2 offset (getTempOffset)
    ],
)
def test_capabilities_offer_the_variants_setpoint_range(model, low, high):
    caps = device(model).capabilities
    assert (caps.temperature.min, caps.temperature.max) == (low, high)
    assert caps.temperature.decimals == (0,)
    # The rest is the same for both remotes.
    assert caps.modes == ("auto", "cool", "dry", "fan", "heat")
    assert caps.fan.values == ("auto", "1", "2", "3")
    assert caps.swing_v.values == ("off", "swing")
    assert caps.swing_h is None
    assert set(caps.features) == {"light", "sleep", "powerful"}


@pytest.mark.parametrize("model", sorted(WHIRLPOOL_AC_MODELS))
def test_every_model_gets_its_variants_capabilities(model):
    low, high = {"DG11J13A": (18.0, 32.0), "DG11J191": (16.0, 30.0)}[
        WHIRLPOOL_AC_MODELS[model]
    ]
    temperature = device(model).capabilities.temperature
    assert (temperature.min, temperature.max) == (low, high)


def test_dg11j191_normalises_31_and_32_to_30_as_c_clamps():
    # _setTemp clamps to kWhirlpoolAcMaxTemp + offset: the legacy 31-32 C
    # states (in the oracle) normalise to what C sent.
    for t in (31.0, 32.0):
        assert state(True, "cool", t, V2).temperature == 30.0
    assert state(True, "cool", 16.0, V2).temperature == 16.0
    assert state(True, "cool", 16.0, V1).temperature == 18.0


def _record(**match):
    return next(
        r
        for r in load_oracle("WHIRLPOOL_AC")
        if all(r["state"].get(k) == v for k, v in match.items())
    )


@pytest.mark.parametrize(
    "defect, match",
    [
        (SWING, {"swing": "on"}),
        (SLEEP, {"sleep": "on"}),
        (SLEEP_FAN[0], {"sleep": "on"}),
        (SUPER, {"powerful": "on"}),
    ],
)
def test_undeclared_deviation_is_reported(defect, match):
    record = _record(**match)
    dev = device(record["model"])
    defects = [d for d in DEFECTS if d != defect]
    with pytest.raises(AssertionError, match=defect.field):
        assert_matches_oracle(dev, record, LAYOUTS, defects)


@pytest.mark.parametrize("defect", SLEEP_FAN[1:])
def test_undeclared_sleep_fan_deviation_is_reported(defect):
    pytest.importorskip("pyhvac.irhvac")
    record = load_oracle("WHIRLPOOL_AC")[0]
    fan = {"2": "medium", "3": "high"}[defect.theirs]
    old = {"mode": "cool", "temperature": 22, "fan": fan, "sleep": "on"}
    (rec,) = c_sequence(record, [old])
    defects = [d for d in DEFECTS if d != defect]
    with pytest.raises(AssertionError, match="fan"):
        assert_matches_oracle(device(), rec, LAYOUTS, defects)


def test_joined_layout_must_cover_every_frame():
    record = _record(swing="on")
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(device(), record, (WHIRLPOOL_AC_LAYOUT,), DEFECTS)
