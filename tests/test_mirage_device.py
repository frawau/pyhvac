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
from pyhvac.plugins.mirage import (
    MIRAGE_KKG29AC1_LAYOUT,
    MIRAGE_KKG9AC1_LAYOUT,
    MIRAGE_MAXELL_MODELS,
    MIRAGE_MODEL_VARIANT,
    MIRAGE_MODELS,
    MIRAGE_TRONITECHNIK_MODELS,
    MirageDevice,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Mirage values here:
# - the legacy glue (IRGHVAC.build_ircode) has no "sleep" key, so IRac gets
#   sleep -1 and fromCommon's setSleep(sleep >= 0) clears Sleep_Kkg9ac1 /
#   Sleep_Kkg29ac1;
# - the legacy glue (IRGHVAC.trans_hswing) has no "on", so IRac's swingh
#   stays kOff and setSwingH(false) clears SwingH (KKG29AC1);
# - swing positions (KKG9AC1): the glue sends kHigh for 90° and
#   kUpperMiddle for 60°; IRMirageAc::convertSwingV maps kHigh to
#   kMirageAcSwingVHigh (so kMirageAcSwingVHighest is never sent) and has no
#   kUpperMiddle case (it falls to kMirageAcSwingVAuto). The port sends
#   Highest for "1" (90°) and High for "2" (60°), with or without the
#   kMirageAcPowerOff offset.
SLEEP = Defect("sleep", 1, 0, "legacy glue never passes sleep")
SWING_H = Defect("swing_h", "swing", "off", "legacy glue has no swing_h 'on'")
SWING_1 = Defect(
    "swing_power", ("highest", True), ("high", True), "convertSwingV: 90° -> High"
)
SWING_1_OFF = Defect(
    "swing_power", ("highest", False), ("high", False), "convertSwingV: 90° -> High"
)
SWING_2 = Defect(
    "swing_power", ("high", True), ("auto", True), "convertSwingV: 60° -> Auto"
)
SWING_2_OFF = Defect(
    "swing_power", ("high", False), ("auto", False), "convertSwingV: 60° -> Auto"
)
DEFECTS = (SLEEP, SWING_H, SWING_1, SWING_1_OFF, SWING_2, SWING_2_OFF)

# ir_Mirage_test.cpp captures.
# KKG9AC1: the spreadsheet capture in HumanReadable (cool, 21C, fan auto,
# swing auto, clock 00:01:26).
KKG9AC1_COOL_21_AUTO = bytes.fromhex("56710000201a00000c000c26010041")
# KKG9AC1: RealExample (cool, 25C, fan auto, swing off, clock 14:16).
KKG9AC1_REAL = bytes.fromhex("567500002001000000000000161426")
# KKG29AC1: getModel, issue 1573 comments 955722044 (heat, 24C, fan low,
# RecycleHeat) and 962362540 (cool, 22C, fan medium).
KKG29AC1_HEAT = bytes.fromhex("56740000120040000000000000001d")
KKG29AC1_COOL = bytes.fromhex("567200002300000000000000000019")

# KKG29AC1's SwingV is one bit (IRMirageAc::setSwingV: SwingV = position !=
# kMirageAcSwingVOff), so its capabilities offer swing_v off and auto only.
# The legacy Miragev2 entity offered the five angles too; C sends each of
# them as the auto bit, so a Miragev2 record's angle is read as "auto".
KKG29AC1_ANGLES = ("90°", "60°", "45°", "30°", "0°")


def adapt(record):
    """The record as the port's capabilities read it (see KKG29AC1_ANGLES)."""
    old = record["state"]
    if record["class"] == "Miragev2" and old.get("swing") in KKG29AC1_ANGLES:
        return {**record, "state": {**old, "swing": "auto"}}
    return record


MODES = ("cool", "fan", "dry", "heat")
VARIANTS = ("KKG9AC1", "KKG29AC1")
LAYOUT = {"KKG9AC1": MIRAGE_KKG9AC1_LAYOUT, "KKG29AC1": MIRAGE_KKG29AC1_LAYOUT}
MODEL = {"KKG9AC1": "generic", "KKG29AC1": "generic 2"}


def device(variant="KKG9AC1"):
    return MirageDevice("mirage", MODEL[variant])


def state(variant="KKG9AC1", power=True, mode="cool", temperature=22.0, **kw):
    return device(variant).normalise(HvacState(power, mode, temperature, **kw))


def frame(variant, target, previous=None):
    (main,) = device(variant).frames(previous, target, ())
    return main.data


def read(variant, target, previous=None):
    return LAYOUT[variant].read(frame(variant, target, previous))


def device_for(record):
    return MirageDevice(record["plugin"], record["model"])


@pytest.mark.parametrize("record", oracle_params("MIRAGE"))
def test_matches_c_library(record):
    dev = device_for(record)
    assert_matches_oracle(dev, adapt(record), dev.LAYOUTS, DEFECTS)


@pytest.mark.parametrize("record, states", sequence_params("MIRAGE"))
def test_sequence_matches_a_persistent_c_object(record, states):
    # KKG29AC1's light and clean toggles depend on the message before, which
    # C's IRac keeps (IRac::handleToggles).
    dev = device_for(record)
    assert_sequence_matches_c(dev, record, states, dev.LAYOUTS, DEFECTS, adapt=adapt)


def test_every_oracle_record_names_its_variant():
    for record in load_oracle("MIRAGE"):
        expected = {"Miragev1": "KKG9AC1", "Miragev2": "KKG29AC1"}[record["class"]]
        assert device_for(record).variant == expected


def test_layout_round_trips_every_oracle_state():
    for record in map(adapt, load_oracle("MIRAGE")):
        dev = device_for(record)
        (main,) = dev.frames(None, state_from_record(dev, record["state"]), ())
        layout = dev.LAYOUTS[0]
        assert layout.build(**layout.read(main.data)) == bytearray(main.data)


# States the oracle grid lacks, sent to a fresh C object each: off in every
# mode, both setpoint ends in every mode, every fan and swing, and the
# feature combinations (powerful outside cool too).
def _extra_states(variant):
    features = ["powerful", "sleep", "light"]
    if variant == "KKG29AC1":
        features += ["quiet", "cleaning", "purifier"]
    swings = ("off", "auto", "90°", "60°", "45°", "30°", "0°")
    states = [
        {"mode": m, "temperature": t, "fan": "medium", "swing": "45°"}
        for m in MODES + ("off",)
        for t in (16, 32)
    ]
    states += [
        {"mode": m, "temperature": 24, "fan": f, "swing": s}
        for m in ("cool", "off")
        for f in ("auto", "low", "medium", "high")
        for s in swings
    ]
    for mode in ("cool", "heat", "off"):
        for n in range(1 << len(features)):
            old = {"mode": mode, "temperature": 20, "fan": "low", "swing": "30°"}
            old.update(
                {k: "on" if n >> i & 1 else "off" for i, k in enumerate(features)}
            )
            if variant == "KKG29AC1":
                old["hswing"] = "on" if n & 1 else "off"
            states.append(old)
    return states


@pytest.mark.parametrize("variant", VARIANTS)
def test_states_beyond_the_oracle_grid_match_the_c_path(variant):
    dev = device(variant)
    cls = {"KKG9AC1": "Miragev1", "KKG29AC1": "Miragev2"}[variant]
    record = next(r for r in load_oracle("MIRAGE") if r["class"] == cls)
    for old in _extra_states(variant):
        # One fresh C object per state: no toggle carries over.
        (rec,) = c_sequence(record, [old])
        assert_matches_oracle(dev, adapt(rec), dev.LAYOUTS, DEFECTS)


@pytest.mark.parametrize("variant", VARIANTS)
def test_checksum_holds_on_the_real_captures(variant):
    checksum = LAYOUT[variant].checksum
    for data in (KKG9AC1_COOL_21_AUTO, KKG9AC1_REAL, KKG29AC1_HEAT, KKG29AC1_COOL):
        assert checksum.check(data)
        broken = bytearray(data)
        broken[1] ^= 0x01
        assert not checksum.check(broken)


def test_checksum_is_the_nibble_sum_of_bytes_0_to_13():
    # IRMirageAc::calculateChecksum; SyntheticExample's sum is 0x26.
    data = bytearray(KKG9AC1_REAL)
    data[14] = 0
    MIRAGE_KKG9AC1_LAYOUT.checksum.apply(data)
    assert data[14] == 0x26


@pytest.mark.parametrize(
    "variant, data, fields",
    [
        (
            "KKG9AC1",
            KKG9AC1_COOL_21_AUTO,
            {
                "temperature": 21,
                "mode": "cool",
                "fan": "auto",
                "swing_power": ("auto", True),
                "seconds": 0x26,
                "minutes": 0x01,
                "hours": 0,
            },
        ),
        (
            "KKG9AC1",
            KKG9AC1_REAL,
            {
                "temperature": 25,
                "mode": "cool",
                "fan": "auto",
                "swing_power": ("off", True),
                "pad5": 1,
                "pad8": 0,
                "pad10": 0,
                "minutes": 0x16,
                "hours": 0x14,
            },
        ),
        (
            "KKG29AC1",
            KKG29AC1_HEAT,
            {
                "temperature": 24,
                "mode": "heat",
                "fan": "1",
                "power": True,
                "swing_v": 0,
                "recycle_heat": 1,
                "pad5": 0,
            },
        ),
        (
            "KKG29AC1",
            KKG29AC1_COOL,
            {
                "temperature": 22,
                "mode": "cool",
                "fan": "2",
                "power": True,
                "swing_v": 0,
                "pad5": 0,
            },
        ),
    ],
)
def test_layout_reads_the_real_captures(variant, data, fields):
    layout = LAYOUT[variant]
    values = layout.read(data)
    assert {k: values[k] for k in fields} == fields
    assert layout.build(**values) == bytearray(data)


def test_port_reproduces_the_spreadsheet_capture_but_its_clock():
    # Cool 21C, fan auto, swing auto; the entity has no clock (IRac sends
    # 00:00:00). With the capture's clock, the port's frame is the capture.
    ours = bytearray(
        frame("KKG9AC1", state("KKG9AC1", True, "cool", 21.0, swing_v="auto"))
    )
    MIRAGE_KKG9AC1_LAYOUT.write_raw(ours, "seconds", 0x26)
    MIRAGE_KKG9AC1_LAYOUT.write_raw(ours, "minutes", 0x01)
    MIRAGE_KKG9AC1_LAYOUT.checksum.apply(ours)
    assert bytes(ours) == KKG9AC1_COOL_21_AUTO


def test_port_reproduces_the_kkg29ac1_cool_capture_but_pad5():
    # Cool 22C, fan medium, swing off. C sends kReset's 0b011 in the three
    # unnamed bits of byte 5 (pad5); the real remote sends 0 there.
    ours = bytearray(frame("KKG29AC1", state("KKG29AC1", True, "cool", 22.0, fan="2")))
    assert MIRAGE_KKG29AC1_LAYOUT.read_raw(ours, "pad5") == 0b011
    MIRAGE_KKG29AC1_LAYOUT.write_raw(ours, "pad5", 0)
    MIRAGE_KKG29AC1_LAYOUT.checksum.apply(ours)
    assert bytes(ours) == KKG29AC1_COOL


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("mode", MODES)
def test_mode_uses_its_documented_value(variant, mode):
    codes = {"heat": 1, "cool": 2, "dry": 3, "fan": 5}
    raw = LAYOUT[variant].read_raw(frame(variant, state(variant, True, mode)), "mode")
    assert raw == codes[mode]


@pytest.mark.parametrize(
    "variant, fan, raw",
    [
        # kMirageAcFan*, as convertFan maps kLow/kMedium/kHigh.
        ("KKG9AC1", "auto", 0),
        ("KKG9AC1", "1", 3),
        ("KKG9AC1", "2", 2),
        ("KKG9AC1", "3", 1),
        # kMirageAcKKG29AC1Fan*.
        ("KKG29AC1", "auto", 0),
        ("KKG29AC1", "1", 2),
        ("KKG29AC1", "2", 3),
        ("KKG29AC1", "3", 1),
    ],
)
def test_every_fan_level_uses_its_documented_code(variant, fan, raw):
    data = frame(variant, state(variant, fan=fan))
    assert LAYOUT[variant].read_raw(data, "fan") == raw


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("t", [16, 17, 24, 31, 32])
def test_temperature_is_offset_by_0x5c(variant, t):
    data = frame(variant, state(variant, True, "heat", float(t)))
    assert data[1] == t + 0x5C


@pytest.mark.parametrize(
    "swing, position, raw",
    [
        ("off", "off", 0),
        ("auto", "auto", 13),
        ("1", "highest", 11),
        ("2", "high", 9),
        ("3", "middle", 7),
        ("4", "low", 5),
        ("5", "lowest", 3),
    ],
)
def test_kkg9ac1_swing_and_power_share_a_field(swing, position, raw):
    # The documented position, plus kMirageAcPowerOff when off.
    layout = MIRAGE_KKG9AC1_LAYOUT
    on = frame("KKG9AC1", state("KKG9AC1", True, swing_v=swing))
    off = frame("KKG9AC1", state("KKG9AC1", False, swing_v=swing))
    assert layout.read(on)["swing_power"] == (position, True)
    assert layout.read(off)["swing_power"] == (position, False)
    assert layout.read_raw(on, "swing_power") == raw
    assert layout.read_raw(off, "swing_power") == raw + 0x5F


@pytest.mark.parametrize("swing, bit", [("off", 0), ("auto", 1)])
def test_kkg29ac1_swing_v_is_one_bit(swing, bit):
    assert read("KKG29AC1", state("KKG29AC1", swing_v=swing))["swing_v"] == bit


def test_kkg29ac1_offers_no_swing_v_position():
    # Removed no-op: the fixed positions set the same SwingV bit as auto.
    assert device("KKG29AC1").capabilities.swing_v.values == ("off", "auto")
    # KKG9AC1's SwingAndPower holds every documented position.
    assert device("KKG9AC1").capabilities.swing_v.values == (
        "off",
        "auto",
        "1",
        "2",
        "3",
        "4",
        "5",
    )


@pytest.mark.parametrize("angle", KKG29AC1_ANGLES)
def test_a_legacy_kkg29ac1_angle_is_sent_as_c_sends_it(angle):
    # C (setSwingV on a KKG29AC1) sends every angle as the auto bit: the
    # adapted record ("auto") is byte for byte the C record.
    record = next(
        r
        for r in load_oracle("MIRAGE")
        if r["class"] == "Miragev2"
        and r["state"].get("swing") == angle
        and r["state"].get("sleep") != "on"
        and r["state"].get("hswing") != "on"
    )
    dev = device_for(record)
    assert adapt(record)["state"]["swing"] == "auto"
    assert_matches_oracle(dev, adapt(record), dev.LAYOUTS)


def test_kkg29ac1_power_bits():
    assert read("KKG29AC1", state("KKG29AC1", True))["power"] is True
    off = frame("KKG29AC1", state("KKG29AC1", False))
    assert MIRAGE_KKG29AC1_LAYOUT.read_raw(off, "power") == 0b11


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("t", [16.0, 32.0])
def test_off_carries_mode_cool(variant, mode, t):
    # IRac's kOff mode falls to convertMode's default, kMirageAcCool (the
    # C-only grid test above checks off against C).
    off = state(variant, False, mode, t, fan="3")
    assert frame(variant, off) == frame(
        variant, state(variant, False, "cool", t, fan="3")
    )
    values = read(variant, off)
    assert (values["mode"], values["temperature"], values["fan"]) == ("cool", t, "3")


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("mode", MODES)
def test_powerful_sets_turbo_in_cool_only(variant, mode):
    # IRMirageAc::setTurbo: "Only works in Cool mode".
    target = state(variant, True, mode, features={"powerful": True})
    assert read(variant, target)["turbo"] == (mode == "cool")
    # An off message carries cool, so turbo stays.
    off = state(variant, False, mode, features={"powerful": True})
    assert read(variant, off)["turbo"] == 1


@pytest.mark.parametrize("variant", VARIANTS)
def test_sleep_sets_the_documented_bit(variant):
    assert read(variant, state(variant, features={"sleep": True}))["sleep"] == 1
    assert read(variant, state(variant, features={"sleep": False}))["sleep"] == 0


def test_kkg9ac1_light_is_a_state():
    for light in (False, True):
        target = state("KKG9AC1", features={"light": light})
        for previous in (None, state("KKG9AC1", features={"light": light})):
            assert read("KKG9AC1", target, previous)["light"] == light


@pytest.mark.parametrize(
    "feature, field",
    [("quiet", "quiet"), ("purifier", "filter")],
)
def test_kkg29ac1_state_features(feature, field):
    assert read("KKG29AC1", state("KKG29AC1", features={feature: True}))[field] == 1
    assert read("KKG29AC1", state("KKG29AC1", features={feature: False}))[field] == 0


def test_kkg29ac1_swing_h_sets_the_documented_bit():
    assert read("KKG29AC1", state("KKG29AC1", swing_h="swing"))["swing_h"] == "swing"
    assert read("KKG29AC1", state("KKG29AC1"))["swing_h"] == "off"


@pytest.mark.parametrize(
    "feature, field", [("light", "light_toggle"), ("cleaning", "clean_toggle")]
)
def test_kkg29ac1_toggle_without_previous_is_the_target(feature, field):
    # A fresh IRac's _prev has protocol UNKNOWN: handleToggles does nothing.
    for on in (False, True):
        target = state("KKG29AC1", features={feature: on})
        assert read("KKG29AC1", target)[field] == on


@pytest.mark.parametrize(
    "feature, field", [("light", "light_toggle"), ("cleaning", "clean_toggle")]
)
@pytest.mark.parametrize(
    "before, after, toggle",
    [(False, False, 0), (False, True, 1), (True, True, 0), (True, False, 1)],
)
def test_kkg29ac1_toggle_with_previous_on_change(feature, field, before, after, toggle):
    # IRac::handleToggles: light ^ prev->light (KKG29AC1), clean ^ prev->clean.
    previous = state("KKG29AC1", features={feature: before})
    target = state("KKG29AC1", features={feature: after})
    assert read("KKG29AC1", target, previous)[field] == toggle


def test_kkg9ac1_ignores_previous():
    target = state("KKG9AC1", features={"light": True, "sleep": True})
    for previous in (
        state("KKG9AC1", False, "heat", 30.0),
        state("KKG9AC1", features={"light": False}),
        target,
    ):
        assert frame("KKG9AC1", target, previous) == frame("KKG9AC1", target)


def test_kkg29ac1_previous_only_drives_the_toggles():
    target = state("KKG29AC1", features={"light": True, "cleaning": True})
    previous = state(
        "KKG29AC1",
        False,
        "heat",
        30.0,
        swing_v="auto",
        features={"light": True, "cleaning": True},
    )
    ours = bytearray(frame("KKG29AC1", target, previous))
    for field in ("light_toggle", "clean_toggle"):
        assert MIRAGE_KKG29AC1_LAYOUT.read_raw(ours, field) == 0
        MIRAGE_KKG29AC1_LAYOUT.write_raw(ours, field, 1)
    MIRAGE_KKG29AC1_LAYOUT.checksum.apply(ours)
    assert bytes(ours) == frame("KKG29AC1", target)


@pytest.mark.parametrize("variant", VARIANTS)
def test_unused_fields_stay_as_the_skeleton(variant):
    target = state(variant, False, "heat", 16.0, fan="3", swing_v="auto")
    values = read(variant, target)
    if variant == "KKG9AC1":
        assert (values["seconds"], values["minutes"], values["hours"]) == (0, 0, 0)
        assert (values["pad5"], values["pad8"], values["pad9"], values["pad10"]) == (
            0,
            0x0C,
            0,
            0x0C,
        )
    else:
        for field in (
            "off_timer_enable",
            "on_timer_enable",
            "recycle_heat",
            "sensor_temp",
            "ifeel",
            "on_timer_hours",
            "on_timer_mins",
            "off_timer_hours",
            "off_timer_mins",
        ):
            assert values[field] == 0, field
        assert values["pad5"] == 0b011


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (8360, 4248)
    assert pulses[-2:] == (554, 100000)
    assert len(pulses) == 2 + 2 * 120 + 2


def test_unknown_variant_is_rejected():
    with pytest.raises(ValueError, match="variant"):
        MirageDevice("mirage", "generic", variant="KKG1")


def test_unknown_model_gets_kkg9ac1():
    assert MirageDevice("mirage", "something else").variant == "KKG9AC1"


@pytest.mark.parametrize(
    "plugin, models",
    [
        ("mirage", MIRAGE_MODELS),
        ("maxell", MIRAGE_MAXELL_MODELS),
        ("tronitechnik", MIRAGE_TRONITECHNIK_MODELS),
    ],
)
def test_registry_serves_the_port(plugin, models):
    for model in models:
        dev = registry.get_device(plugin, model)
        assert isinstance(dev, MirageDevice)
        assert dev.variant == MIRAGE_MODEL_VARIANT[model]


def _legacy_classes():
    from pyhvac.plugins import maxell, mirage, tronitechnik

    for module in (mirage, maxell, tronitechnik):
        brand = module.PluginObject().brand
        for model, cls in module.PluginObject.MODELS.items():
            yield brand, model, cls


def test_every_legacy_model_is_ported():
    served = {(b, m) for b, m, _ in _legacy_classes()}
    assert served == (
        {("mirage", m) for m in MIRAGE_MODELS}
        | {("maxell", m) for m in MIRAGE_MAXELL_MODELS}
        | {("tronitechnik", m) for m in MIRAGE_TRONITECHNIK_MODELS}
    )


def _record(cls, **match):
    return next(
        r
        for r in load_oracle("MIRAGE")
        if r["class"] == cls and all(r["state"].get(k) == v for k, v in match.items())
    )


@pytest.mark.parametrize(
    "defect, cls, match",
    [
        (SLEEP, "Miragev1", {"sleep": "on"}),
        (SLEEP, "Miragev2", {"sleep": "on"}),
        (SWING_H, "Miragev2", {"hswing": "on"}),
        (SWING_1, "Miragev1", {"swing": "90°", "mode": "cool"}),
        (SWING_1_OFF, "Miragev1", {"swing": "90°", "mode": "off"}),
        (SWING_2, "Miragev1", {"swing": "60°", "mode": "cool"}),
        (SWING_2_OFF, "Miragev1", {"swing": "60°", "mode": "off"}),
    ],
)
def test_undeclared_deviation_is_reported(defect, cls, match):
    record = adapt(_record(cls, **match))
    dev = device_for(record)
    defects = [d for d in DEFECTS if d != defect]
    with pytest.raises(AssertionError, match=defect.field):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects)


def test_layouts_must_cover_every_frame():
    record = _record("Miragev1", swing="90°")
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(device_for(record), record, (), DEFECTS)
