import pytest

from oracle import load_oracle
from port_oracle import (
    Defect,
    assert_matches_oracle,
    c_sequence,
    oracle_params,
    state_from_record,
)
from pyhvac import registry
from pyhvac.plugins.voltas import (
    VOLTAS_LAYOUT,
    VOLTAS_MODELS,
    VoltasDevice,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Voltas values here:
# - the legacy glue (IRGHVAC.trans_swing) has no "on", so IRac's swingv stays
#   kOff and IRVoltas::setSwingV(false) writes 0, not 0b111;
# - likewise IRGHVAC.trans_hswing: IRac's swingh stays kOff and
#   IRVoltas::setSwingH(false) writes SwingH 0 (variant Unknown);
# - the legacy glue (IRGHVAC.build_ircode) has no "sleep" key, so IRac gets
#   sleep -1 and setSleep(sleep >= 0) clears Sleep.
SWING = Defect("swing_v", "swing", "off", "legacy glue has no swing 'on'")
SWING_H = Defect("swing_h", 1, 0, "legacy glue has no hswing 'on'")
SLEEP = Defect("sleep", 1, 0, "legacy glue never passes sleep")
DEFECTS = (SWING, SWING_H, SLEEP)

# ir_Voltas_test.cpp, as logical bytes (sent MSB first).
RESET = bytes.fromhex("332800173b3b3b1100cb")  # stateReset's kReset
REAL_EXAMPLE = bytes.fromhex("338488183b3b3b1100e6")  # RealExample
LIGHT_ON = bytes.fromhex("338488183b3b3b1120c6")  # Light: light_on
OFF_7HRS = bytes.fromhex("332880" "1b3b3b3b7140a7")  # Timers: off_7hrs (real)
OFF_16HRS = bytes.fromhex("332880" "1b3bbb3b414057")  # Timers: off_16hrs (real)
OFF_24HRS = bytes.fromhex("332880" "1b3a3a3b014019")  # Timers: off_24hrs (real)

MODES = ("cool", "dry", "fan", "heat")
MODE_CODES = {"fan": 0b0001, "heat": 0b0010, "dry": 0b0100, "cool": 0b1000}
FEATURES = ("economy", "powerful", "light", "sleep")


def device(model="generic"):
    return VoltasDevice("voltas", model)


def state(power=True, mode="cool", temperature=23.0, model="generic", **kw):
    return device(model).normalise(HvacState(power, mode, temperature, **kw))


def frame(target, previous=None, model="generic"):
    (main,) = device(model).frames(previous, target, ())
    return main.data


def read(target, model="generic"):
    return VOLTAS_LAYOUT.read(frame(target, model=model))


@pytest.mark.parametrize("record", oracle_params("VOLTAS"))
def test_matches_c_library(record):
    dev = device(record["model"])
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_oracle_covers_both_variants():
    models = {r["model"] for r in load_oracle("VOLTAS")}
    assert {VOLTAS_MODELS[m] for m in models} == {"Unknown", "122LZF"}


def test_layout_round_trips_every_oracle_state():
    for record in load_oracle("VOLTAS"):
        dev = device(record["model"])
        (main,) = dev.frames(None, state_from_record(dev, record["state"]), ())
        values = VOLTAS_LAYOUT.read(main.data)
        assert VOLTAS_LAYOUT.build(**values) == bytearray(main.data)


# States the oracle grid lacks: off in every mode, low/high and dry-relevant
# setpoints in every mode, every fan level in every mode, swing and feature
# combinations, in both variants.
EXTRA_STATES = [
    {"mode": m, "temperature": t, "fan": f, "swing": "off"}
    for m in MODES + ("off",)
    for t in (16, 17, 24, 29, 30)
    for f in ("auto", "low", "medium", "high")
] + [
    {
        "mode": mode,
        "temperature": 22,
        "fan": "low",
        "swing": swing,
        **{k: ("on" if k in on else "off") for k in FEATURES},
    }
    for mode in MODES + ("off",)
    for swing in ("off", "on")
    for on in ((), FEATURES, ("economy",), ("powerful",), ("light",), ("sleep",))
]
EXTRA_HSWING = [
    {"mode": m, "temperature": 22, "fan": "high", "hswing": h}
    for m in MODES + ("off",)
    for h in ("off", "on")
]


@pytest.mark.parametrize("model", ["generic", "122LZF 4011252"])
def test_states_beyond_the_oracle_grid_match_the_c_path(model):
    pytest.importorskip("pyhvac.irhvac")
    dev = device(model)
    record = next(r for r in load_oracle("VOLTAS") if r["model"] == model)
    extra = EXTRA_STATES + (EXTRA_HSWING if model == "generic" else [])
    for rec in c_sequence(record, extra):
        assert_matches_oracle(dev, rec, dev.LAYOUTS, DEFECTS)


def test_checksum_holds_on_the_real_captures():
    checksum = VOLTAS_LAYOUT.checksum
    for data in (RESET, REAL_EXAMPLE, LIGHT_ON, OFF_7HRS, OFF_16HRS, OFF_24HRS):
        assert checksum.check(data)
    broken = bytearray(REAL_EXAMPLE)
    broken[3] ^= 0x01
    assert not checksum.check(broken)
    # TestIRVoltasClass.Checksums: a bad sum is recomputed as 0xE6.
    bad = bytearray(REAL_EXAMPLE[:9] + b"\x00")
    checksum.apply(bad)
    assert bytes(bad) == REAL_EXAMPLE


@pytest.mark.parametrize(
    "data, fields",
    [
        # kReset: power off, cool, 23C, fan high, 122LZF (no change).
        (
            RESET,
            {
                "swing_h_change": "no change",
                "swing_h": 1,
                "power": 0,
                "mode": "cool",
                "temperature": 23,
                "fan": "3",
                "wifi": 0,
                "on_timer_enable": 0,
                "off_timer_enable": 0,
            },
        ),
        # RealExample: power on, dry, 24C, fan low, WiFi on.
        (
            REAL_EXAMPLE,
            {
                "swing_h_change": "no change",
                "power": 1,
                "mode": "dry",
                "temperature": 24,
                "fan": "1",
                "swing_v": "off",
                "wifi": 1,
                "light": 0,
            },
        ),
        (LIGHT_ON, {"mode": "dry", "light": 1}),
        # off_7hrs: cool, 27C, fan high, off timer 06:59.
        (
            OFF_7HRS,
            {
                "power": 1,
                "mode": "cool",
                "temperature": 27,
                "fan": "3",
                "off_timer_enable": 1,
                "off_timer_hrs": 7,
                "off_timer_12hr": 0,
                "off_timer_mins": 59,
                "on_timer_enable": 0,
            },
        ),
        # off_16hrs: off timer 15:59 ((1 * 12 + 4) - 1 hours).
        (OFF_16HRS, {"off_timer_12hr": 1, "off_timer_hrs": 4, "off_timer_mins": 59}),
    ],
)
def test_layout_reads_the_real_captures(data, fields):
    values = VOLTAS_LAYOUT.read(data)
    assert {k: values[k] for k in fields} == fields
    assert VOLTAS_LAYOUT.build(**values) == bytearray(data)


@pytest.mark.parametrize("model", ["122LZF 4011252", "generic 2"])
def test_port_reproduces_the_reset_state(model):
    # kReset is an off message: cool, 23C, fan high, as the 122LZF sends it.
    assert frame(state(False, "cool", 23.0, model, fan="3"), model=model) == RESET


@pytest.mark.parametrize("data", [REAL_EXAMPLE, LIGHT_ON])
def test_port_reproduces_the_real_dry_captures_but_wifi(data):
    # RealExample (and the Light test's light_on): dry, 24C, fan low, on a
    # 122LZF with WiFi on. IRac never sets WiFi; with the capture's WiFi
    # bit, the port's frame is the capture.
    light = VOLTAS_LAYOUT.read(data)["light"] == 1
    target = state(
        True, "dry", 24.0, "122LZF 4011252", fan="1", features={"light": light}
    )
    ours = bytearray(frame(target, model="122LZF 4011252"))
    VOLTAS_LAYOUT.write_raw(ours, "wifi", 1)
    VOLTAS_LAYOUT.checksum.apply(ours)
    assert bytes(ours) == data


def test_port_reproduces_the_real_timer_capture_but_its_timer():
    # off_7hrs: cool, 27C, fan high, power on, with an off timer the entity
    # cannot set; with the capture's timer fields, the port's frame is it.
    ours = bytearray(
        frame(
            state(True, "cool", 27.0, "122LZF 4011252", fan="3"),
            model="122LZF 4011252",
        )
    )
    capture = VOLTAS_LAYOUT.read(OFF_7HRS)
    for name in ("off_timer_enable", "off_timer_hrs", "off_timer_mins"):
        VOLTAS_LAYOUT.write_raw(ours, name, capture[name])
    VOLTAS_LAYOUT.checksum.apply(ours)
    assert bytes(ours) == OFF_7HRS


@pytest.mark.parametrize(
    "model, variant",
    [("generic", "Unknown"), ("122LZF 4011252", "122LZF"), ("generic 2", "122LZF")],
)
def test_variant_comes_from_the_model(model, variant):
    assert VOLTAS_MODELS[model] == variant
    assert device(model).variant == variant


def test_unknown_model_gets_122lzf_and_bad_variant_raises():
    assert VoltasDevice("voltas", "whatever").variant == "122LZF"
    assert VoltasDevice("voltas", "whatever", variant="Unknown").variant == "Unknown"
    with pytest.raises(ValueError, match="variant"):
        VoltasDevice("voltas", "whatever", variant="Other")


@pytest.mark.parametrize("swing_h", ["off", "swing"])
def test_unknown_variant_sends_swing_h_as_a_change(swing_h):
    # IRVoltas::setSwingH: SwingH, and SwingHChange = kVoltasSwingHChange.
    values = read(state(swing_h=swing_h))
    assert values["swing_h_change"] == "change"
    assert values["swing_h"] == (swing_h == "swing")
    assert frame(state(swing_h=swing_h))[0] == (0xF9 if swing_h == "swing" else 0xF8)


@pytest.mark.parametrize("model", ["122LZF 4011252", "generic 2"])
def test_122lzf_sends_no_swing_h_change(model):
    # IRVoltas::setModel(kVoltas122LZF): kVoltasSwingHNoChange, SwingH set.
    assert device(model).capabilities.swing_h is None
    values = read(state(model=model), model=model)
    assert (values["swing_h_change"], values["swing_h"]) == ("no change", 1)
    assert frame(state(model=model), model=model)[0] == 0x33


@pytest.mark.parametrize("mode", MODES)
def test_mode_uses_its_documented_value(mode):
    assert VOLTAS_LAYOUT.read_raw(frame(state(True, mode)), "mode") == MODE_CODES[mode]


@pytest.mark.parametrize("mode", ["cool", "dry", "heat"])
@pytest.mark.parametrize("fan, raw", [("auto", 7), ("1", 4), ("2", 2), ("3", 1)])
def test_every_fan_level_uses_its_documented_code(mode, fan, raw):
    # kVoltasFanAuto / Low / Med / High, as convertFan maps them.
    assert VOLTAS_LAYOUT.read_raw(frame(state(True, mode, fan=fan)), "fan") == raw


@pytest.mark.parametrize(
    "fan, sent", [("auto", "3"), ("1", "1"), ("2", "2"), ("3", "3")]
)
def test_fan_mode_has_no_auto_speed(fan, sent):
    # IRVoltas::setFan: "Auto speed is not available in fan mode" -> high.
    assert read(state(True, "fan", fan=fan))["fan"] == sent


@pytest.mark.parametrize("t", [16, 17, 24, 29, 30])
@pytest.mark.parametrize("fan", ["auto", "1", "2", "3"])
def test_dry_keeps_the_requested_setpoint_and_fan(t, fan):
    # setMode(kVoltasDry)'s kVoltasDryTemp and kVoltasFanLow are overwritten
    # by IRac::voltas' setTemp and setFan after it.
    values = read(state(True, "dry", float(t), fan=fan))
    assert (values["temperature"], values["fan"]) == (t, fan)


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("t", [16, 23, 30])
def test_setpoint_is_sent_in_every_mode(mode, t):
    assert read(state(True, mode, float(t)))["temperature"] == t


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("t", [16.0, 23.0, 30.0])
def test_off_carries_mode_cool(mode, t):
    # IRac's kOff mode falls to convertMode's default, kVoltasCool, so the
    # target mode never reaches an off message (the C-only test above checks
    # off against C).
    off = state(False, mode, t, fan="2")
    assert frame(off) == frame(state(False, "cool", t, fan="2"))
    values = read(off)
    assert (values["power"], values["mode"]) == (0, "cool")
    assert (values["temperature"], values["fan"]) == (int(t), "2")


@pytest.mark.parametrize(
    "feature, field", [("powerful", "turbo"), ("economy", "econo"), ("sleep", "sleep")]
)
@pytest.mark.parametrize("mode", MODES)
def test_cool_only_features(feature, field, mode):
    # IRVoltas::setTurbo / setEcono / setSleep: only in cool. An off message
    # carries cool, so they are sent there too.
    on = read(state(True, mode, features={feature: True}))[field]
    assert on == (mode == "cool")
    assert read(state(False, mode, features={feature: True}))[field] == 1
    assert read(state(True, mode, features={feature: False}))[field] == 0


@pytest.mark.parametrize("mode", MODES)
def test_light_sets_light_in_every_mode(mode):
    assert read(state(True, mode, features={"light": True}))["light"] == 1
    assert read(state(True, mode, features={"light": False}))["light"] == 0


@pytest.mark.parametrize("swing, raw", [("off", 0), ("swing", 0b111)])
def test_swing_uses_its_documented_code(swing, raw):
    assert VOLTAS_LAYOUT.read_raw(frame(state(swing_v=swing)), "swing_v") == raw


def test_power_bit():
    assert read(state(True))["power"] == 1
    assert read(state(False))["power"] == 0


def test_wifi_temp_set_and_timers_keep_the_reset_values():
    reset = VOLTAS_LAYOUT.read(RESET)
    kept = (
        "wifi",
        "temp_set",
        "on_timer_mins",
        "on_timer_12hr",
        "off_timer_mins",
        "off_timer_12hr",
        "on_timer_hrs",
        "off_timer_hrs",
        "off_timer_enable",
        "on_timer_enable",
    )
    all_on = {k: True for k in FEATURES}
    for target in (state(True), state(False, "heat", 30.0, features=all_on)):
        values = read(target)
        assert {k: values[k] for k in kept} == {k: reset[k] for k in kept}
        data = frame(target)
        assert (data[3] >> 4) & 0b11 == 0b01  # "Typically 0b01"
        assert data[6] == 0x3B  # "Typically 0x3B"


def test_previous_is_ignored():
    # No toggles: IRac::handleToggles has no VOLTAS rule and IRac builds a
    # fresh IRVoltas for every message.
    for model in ("generic", "122LZF 4011252"):
        target = state(True, "cool", 22.0, model)
        for previous in (None, state(False, "heat", 30.0, model), target):
            assert frame(target, previous, model) == frame(target, model=model)


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] in ((1026, 554), (1026, 2553))  # no header
    assert pulses[-2:] == (1026, 100000)
    assert len(pulses) == 2 * 80 + 2


@pytest.mark.parametrize("model", VOLTAS_MODELS)
def test_registry_serves_the_port(model):
    dev = registry.get_device("voltas", model)
    assert isinstance(dev, VoltasDevice)
    assert dev.variant == VOLTAS_MODELS[model]


@pytest.mark.parametrize("model", VOLTAS_MODELS)
def test_capabilities_are_what_the_protocol_documents(model):
    # The audit found nothing to add or remove: kVoltas{Cool,Dry,Fan,Heat}
    # (no auto), kVoltasMinTemp..kVoltasMaxTemp, kVoltasFan{Auto,Low,Med,
    # High}, SwingV on/off (0b111/0b000), SwingH (Unknown only; 122LZF
    # ignores setSwingH), Econo, Turbo, Light and Sleep bits.
    caps = device(model).capabilities
    assert caps.modes == ("cool", "dry", "fan", "heat")
    assert (caps.temperature.min, caps.temperature.max) == (16.0, 30.0)
    assert caps.fan.values == ("auto", "1", "2", "3")
    assert caps.swing_v.values == ("off", "swing")
    has_swing_h = VOLTAS_MODELS[model] == "Unknown"
    assert (caps.swing_h is not None) == has_swing_h
    assert set(caps.features) == {"economy", "powerful", "light", "sleep"}


def _record(model, **match):
    return next(
        r
        for r in load_oracle("VOLTAS")
        if r["model"] == model and all(r["state"].get(k) == v for k, v in match.items())
    )


@pytest.mark.parametrize(
    "defect, model, match",
    [
        (SWING, "generic", {"swing": "on"}),
        (SWING, "122LZF 4011252", {"swing": "on"}),
        (SWING_H, "generic", {"hswing": "on"}),
        (SLEEP, "generic", {"sleep": "on"}),
        (SLEEP, "122LZF 4011252", {"sleep": "on"}),
    ],
)
def test_undeclared_deviation_is_reported(defect, model, match):
    dev = device(model)
    record = _record(model, **match)
    defects = [d for d in DEFECTS if d != defect]
    with pytest.raises(AssertionError, match=defect.field):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects)


def test_layouts_must_cover_every_frame():
    dev = device()
    record = _record("generic", swing="on")
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)
