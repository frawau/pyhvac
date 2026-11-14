import itertools

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
from pyhvac.ir.codec import decode
from pyhvac.protocols.sharp import (
    SHARP_AC_LAYOUT,
    SHARP_AC_MODEL_VARIANT,
    SHARP_AC_MODELS,
    SharpAcDevice,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Sharp values here:
# - fan "high" on the A903/A705: the old glue maps it to kHigh, which
#   IRSharpAc::convertFan sends as kSharpAcFanHigh (5), the same code as
#   kSharpAcFanA705Med, so high and medium are one speed. The port sends
#   kSharpAcFanMax (7), which toString names "High" for these remotes and
#   which the real A903 captures below carry.
FAN_HIGH = Defect("fan", 7, 5, "convertFan sends A705/A903 high as medium")
DEFECTS = (FAN_HIGH,)

# - cleaning: IRac::sharp calls setPower(on, prev_power) after
#   setClean(clean), and IRSharpAc::setPower calls setClean(false) when Clean
#   is set, restoring the mode, setpoint and fan. So C's second message is a
#   plain "on" message. The port sends the clean message setClean(true)
#   builds (dry, fan auto, no setpoint, Clean, PowerSpecial OnFromOff), as
#   the real A903 capture below. Scoped to the clean message only
#   (assert_only_the_clean_message_deviates checks every other message).
CLEAN_DEFECTS = (
    (
        Defect("clean", 1, 0, "setPower clears Clean"),
        Defect("temp_flags", 0, 0b110, "setPower restores the setpoint"),
        Defect("model", 0, 1, "setPower restores the setpoint (A705 bit)"),
        Defect("power_special", "on_from_off", "on", "setClean's setPower"),
    )
    + tuple(Defect("mode", 3, m, "setPower restores the mode") for m in (0, 1, 2))
    + tuple(
        Defect("temperature", 0, t, "setPower restores the setpoint")
        for t in range(1, 16)
    )
    + tuple(Defect("fan", 2, f, "setPower restores the fan") for f in (3, 4, 5, 7))
)

# - swing, with a persistent C object only: IRac::handleToggles turns a
#   SHARP_AC swing change between off and not-off into kAuto and anything
#   else into kOff, and IRac::sharp then calls setSwingV(convertSwingV(...))
#   when that differs from the previous swing: kSharpAcSwingVToggle (7) or
#   kSharpAcSwingVOff (2) instead of the requested position. The port sends
#   the position (or kSharpAcSwingVIgnore for off), as a fresh object does.
SWING_SEQUENCE = tuple(
    Defect("swing", ours, theirs, "handleToggles treats positions as a toggle")
    for ours, theirs in [(0, 7)] + [(p, c) for p in (1, 3, 4) for c in (2, 7)]
)

FEATURES = {
    "A907": ("cleaning", "powerful", "purifier"),
    "A903": ("cleaning", "powerful", "purifier"),
    "A705": ("cleaning", "powerful", "purifier"),
}
MODEL = {
    "A907": "Sharp AY-ZP40KR",
    "A903": "AH-PR13-GL",
    "A705": "CRMC-A705 JBEZ remote",
}

# ir_Sharp_test.cpp captures the entity can express.
ON_AUTO_AUTO = "aa5acf10001120000880" "00e001"  # KnownStates: A907 on, auto
OFF_AUTO_AUTO = "aa5acf10002120000880" "00e031"  # KnownStates: A907 off, auto
DRY_AUTO = "aa5acf10003123000880" "00e011"  # KnownStates: A907 dry (on, was on)
ON_PREV_OFF = "aa5acf10cb1122000880" "00e051"  # Power: A907 cool 26, from off
COLLECT2 = "aa5acf10c71122000880" "00e091"  # Power: A907 cool 22, from off
COLLECT6 = "aa5acf10c73122000880" "00e0b1"  # Power: A907 cool 22, was on
ISSUE_1309_ON = "aa5acf10d11122000880" "00f0f1"  # A705 cool 16, from off
A903_ON = "aa5acf10cc1132000880" "00f461"  # Models / Issue1387Power real_on
CLEAN_ON = "aa5acf1000112b000880" "00f0a1"  # Clean: clean_on_state (A903)
CLEAN_OFF = "aa5acf10ca1172000880" "00f001"  # Clean: clean_off_state (A903)
TURBO_ON = "aa5acf10c66172000880" "01f4e1"  # Turbo: on_state (A903)
# KnownStates: A907 cool 28, PowerSpecial On, Special Fan (setFan's), with
# the fan at FAN1 (kSharpAcFanMin), FAN2 (FanMed), FAN3 (FanHigh) and FAN4
# (kSharpAcFanMax, which toString names "High" for the A907).
COOL_FAN1_28 = "aa5acf10cd3142000880" "05e021"
COOL_FAN2_28 = "aa5acf10cd3132000880" "05e051"
COOL_FAN3_28 = "aa5acf10cd3152000880" "05e031"
COOL_FAN4_28 = "aa5acf10cd3172000880" "05e011"


def device(variant="A907"):
    return SharpAcDevice("sharp", MODEL[variant])


def device_for(record):
    return SharpAcDevice(record["plugin"], record["model"])


def features(variant="A907", **on):
    return {k: on.get(k, False) for k in FEATURES[variant]}


def state(power=True, mode="cool", temperature=22.0, variant="A907", **kw):
    kw.setdefault("features", features(variant))
    return device(variant).normalise(HvacState(power, mode, temperature, **kw))


def messages(target, variant="A907", previous=None):
    return [f.data for f in device(variant).frames(previous, target, ())]


def read(target, variant="A907", previous=None):
    return [SHARP_AC_LAYOUT.read(m) for m in messages(target, variant, previous)]


def defects_for(record):
    if record["state"].get("cleaning") == "on":
        return DEFECTS + CLEAN_DEFECTS
    return DEFECTS


def assert_only_the_clean_message_deviates(dev, record, previous=None):
    """CLEAN_DEFECTS excuse the clean message only: with cleaning on and the
    unit on, the port's second message. Every other message must be C's."""
    target = state_from_record(dev, record["state"])
    if not (target.power and target.features["cleaning"]):
        return
    ours = dev.frames(previous, target, ())
    theirs = decode(dev.PROTOCOL, record["pulses"], expected=["main"] * len(ours))
    for i, (a, b) in enumerate(zip(ours, theirs)):
        if i != 1:
            assert a.data == b.data, f"message {i} of {record['state']}"


@pytest.mark.parametrize("record", oracle_params("SHARP_AC"))
def test_matches_c_library(record):
    dev = device_for(record)
    assert_matches_oracle(dev, record, dev.layouts, defects_for(record))
    assert_only_the_clean_message_deviates(dev, record)


@pytest.mark.parametrize("variant", ["A907", "A903", "A705"])
def test_cleaning_with_powerful_sends_cs_turbo_frame(variant):
    # IRac::sharp: setClean(clean); setPower(on, prev) (which clears Clean
    # and restores mode, setpoint and fan); if (turbo) {send(); setTurbo();}
    # send(). The turbo frame is built from the plain state, not the clean
    # message the port sends before it.
    dev = device(variant)
    record = next(
        r for r in load_oracle("SHARP_AC") if dev.variant == device_for(r).variant
    )
    old = {"mode": "cool", "temperature": 24, "fan": "auto"}
    old.update(cleaning="on", powerful="on")
    (rec,) = c_sequence(record, [old])
    assert_only_the_clean_message_deviates(dev, rec)


@pytest.mark.parametrize("record, states", sequence_params("SHARP_AC"))
def test_sequence_matches_a_persistent_c_object(record, states):
    # PowerSpecial (OnFromOff / On) and the swing depend on the message
    # before, which C's IRac keeps.
    dev = device_for(record)
    assert_sequence_matches_c(
        dev, record, states, dev.layouts, DEFECTS + CLEAN_DEFECTS + SWING_SEQUENCE
    )


def test_layout_round_trips_every_oracle_state():
    for record in load_oracle("SHARP_AC"):
        dev = device_for(record)
        target = state_from_record(dev, record["state"])
        for frame in dev.frames(None, target, ()):
            values = SHARP_AC_LAYOUT.read(frame.data)
            assert SHARP_AC_LAYOUT.build(**values) == bytearray(frame.data)


# States the oracle grid lacks, per variant: off in every mode, the setpoint
# edges with every fan and swing, and every feature combination, on and off,
# in every mode. Each is sent from a fresh C object, as the fixtures were.
def _old(target):
    fan = {"auto": "auto", "1": "low", "2": "medium", "3": "high", "4": "highest"}
    swing = {"off": "off", "1": "90°", "2": "45°", "3": "30°"}
    old = {
        "mode": target.mode if target.power else "off",
        "temperature": int(target.temperature),
        "fan": fan[target.fan],
        "swing": swing[target.swing_v],
    }
    old.update({k: "on" if v else "off" for k, v in target.features.items()})
    return old


def _extra_states(variant):
    caps = device(variant).capabilities
    names = FEATURES[variant]
    return (
        [
            HvacState(power, mode, t, fan=fan, swing_v=sv)
            for mode in caps.modes
            for power in (True, False)
            for t in (15.0, 16.0, 29.0, 30.0)
            for fan in caps.fan.values
            for sv in caps.swing_v.values
        ]
        + [
            HvacState(
                power, mode, 24.0, fan="3", swing_v="2", features=dict(zip(names, f))
            )
            for mode in caps.modes
            for power in (True, False)
            for f in itertools.product((False, True), repeat=len(names))
        ]
        + [
            HvacState(True, mode, 20.0, fan=fan, features={"cleaning": True})
            for mode in caps.modes
            for fan in caps.fan.values
        ]
    )


@pytest.mark.parametrize("variant", ["A907", "A903", "A705"])
def test_states_beyond_the_oracle_grid_match_the_c_path(variant):
    dev = device(variant)
    record = next(r for r in load_oracle("SHARP_AC") if r["model"] == MODEL[variant])
    for target in _extra_states(variant):
        target = dev.normalise(target)
        (rec,) = c_sequence(record, [_old(target)])
        assert_matches_oracle(dev, rec, dev.layouts, defects_for(rec))


def test_checksum_holds_on_the_real_captures():
    checksum = SHARP_AC_LAYOUT.checksum
    captures = (
        ON_AUTO_AUTO,
        OFF_AUTO_AUTO,
        DRY_AUTO,
        ON_PREV_OFF,
        COLLECT2,
        COLLECT6,
        ISSUE_1309_ON,
        A903_ON,
        CLEAN_ON,
        CLEAN_OFF,
        TURBO_ON,
        # RealExample (cool-auto-27), the swing and ion captures.
        "aa5acf10cc3122000880" "04e041",
        "aa5acf10ca3122000f80" "06f421",
        "aa5acf10c831210a0e80" "06f481",
        "aa5acf10ca6122080880" "00f4e1",
    )
    for capture in captures:
        assert checksum.check(bytes.fromhex(capture)), capture
    broken = bytearray.fromhex(A903_ON)
    broken[6] ^= 0x10
    assert not checksum.check(broken)


def test_checksum_writes_only_the_high_nibble_of_byte_12():
    checksum = SHARP_AC_LAYOUT.checksum
    assert checksum.bits() == set(range(100, 104))
    data = bytearray.fromhex(TURBO_ON)
    data[12] &= 0x0F
    checksum.apply(data)
    assert data.hex() == TURBO_ON


@pytest.mark.parametrize(
    "capture, variant, target, previous",
    [
        (ON_AUTO_AUTO, "A907", dict(mode="auto", temperature=15.0), None),
        (DRY_AUTO, "A907", dict(mode="dry", temperature=15.0), True),
        (ON_PREV_OFF, "A907", dict(temperature=26.0), None),
        (COLLECT2, "A907", dict(temperature=22.0), None),
        (COLLECT6, "A907", dict(temperature=22.0), True),
        (ISSUE_1309_ON, "A705", dict(temperature=16.0), None),
        # fan 3 is kSharpAcFanA705Low; Ion on.
        (A903_ON, "A903", dict(temperature=27.0, fan="1", purifier=True), None),
        # fan 7 (kSharpAcFanMax) is the A903's "High".
        (CLEAN_OFF, "A903", dict(temperature=25.0, fan="3"), None),
    ],
)
def test_port_reproduces_the_real_captures(capture, variant, target, previous):
    kw = dict(target)
    flags = {k: kw.pop(k) for k in FEATURES[variant] if k in kw}
    target = state(True, variant=variant, features=features(variant, **flags), **kw)
    before = None
    if previous:
        before = state(True, "cool", 24.0, variant=variant)
    (ours,) = messages(target, variant, before)
    assert ours.hex() == capture


def test_port_reproduces_the_off_capture():
    # KnownStates off_auto_auto: A907 off, auto (the mode every off carries).
    (ours,) = messages(state(False, "auto", 15.0))
    assert ours.hex() == OFF_AUTO_AUTO


def test_clean_message_is_the_real_capture():
    # Clean: clean_on_state (A903); setClean(true) builds it from any mode.
    for mode in ("auto", "cool", "dry", "fan"):
        target = state(
            True,
            mode,
            25.0,
            variant="A903",
            fan="3",
            features=features("A903", cleaning=True),
        )
        off, clean = messages(target, "A903")
        assert clean.hex() == CLEAN_ON
        assert SHARP_AC_LAYOUT.read(off)["power_special"] == "off"


def test_turbo_message_is_the_real_capture():
    # Turbo: on_state (A903, cool 21, Ion on): the second message.
    target = state(
        True,
        "cool",
        21.0,
        variant="A903",
        features=features("A903", powerful=True, purifier=True),
    )
    main, turbo = messages(target, "A903")
    assert turbo.hex() == TURBO_ON
    assert SHARP_AC_LAYOUT.read(main)["power_special"] == "on_from_off"


def test_off_differs_from_the_real_capture_only_in_the_mode_irac_gives_it():
    # Power off_prev_on: the remote keeps cool 26 in its off message; IRac
    # passes mode "off", which convertMode maps to kSharpAcAuto, so no
    # setpoint either.
    (ours,) = messages(state(False, "cool", 26.0))
    capture = bytearray.fromhex("aa5acf10cb2122000880" "00e061")
    for name, raw in (("mode", 0), ("temperature", 0), ("temp_flags", 0)):
        SHARP_AC_LAYOUT.write_raw(capture, name, raw)
    SHARP_AC_LAYOUT.checksum.apply(capture)
    assert ours == bytes(capture)


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (3800, 1900)
    assert pulses[-2:] == (470, 100000)
    assert len(pulses) == 2 + 2 * 104 + 2
    assert device().PROTOCOL.carrier == 38000


@pytest.mark.parametrize(
    "variant, mode, code",
    [
        ("A907", "auto", 0),
        ("A907", "heat", 1),
        ("A907", "cool", 2),
        ("A907", "dry", 3),
        ("A903", "auto", 0),
        ("A903", "fan", 0),  # no A903 fan mode: convertMode's default
        ("A903", "cool", 2),
        ("A903", "dry", 3),
        ("A705", "fan", 0),
        ("A705", "cool", 2),
        ("A705", "dry", 3),
    ],
)
def test_mode_uses_its_documented_value(variant, mode, code):
    (values,) = read(state(True, mode, variant=variant), variant)
    assert values["mode"] == code


@pytest.mark.parametrize("variant", ["A907", "A903", "A705"])
@pytest.mark.parametrize("t", [15, 16, 22, 29, 30])
def test_setpoint_modes_send_degrees_above_15(variant, t):
    modes = ("cool", "heat") if variant == "A907" else ("cool",)
    for mode in modes:
        (values,) = read(state(True, mode, float(t), variant=variant), variant)
        assert values["temperature"] == t - 15
        assert values["temp_flags"] == 0b110
        assert values["model"] == (variant == "A705")


@pytest.mark.parametrize("variant", ["A907", "A903", "A705"])
def test_modes_without_setpoint_send_byte_4_as_zero(variant):
    for mode in ("auto", "fan", "dry"):
        if mode not in device(variant).capabilities.modes:
            continue
        (ours,) = messages(state(True, mode, 27.0, variant=variant), variant)
        assert ours[4] == 0


@pytest.mark.parametrize(
    "variant, codes",
    [
        ("A907", {"auto": 2, "1": 4, "2": 3, "3": 5, "4": 7}),
        ("A903", {"auto": 2, "1": 3, "2": 5, "3": 7}),
        ("A705", {"auto": 2, "1": 3, "2": 5, "3": 7}),
    ],
)
def test_every_fan_level_uses_its_documented_code_in_every_mode(variant, codes):
    # The fan is sent in auto and dry too: IRac's setClean(false) restores it.
    for mode in device(variant).capabilities.modes:
        for power in (True, False):
            for fan, code in codes.items():
                target = state(power, mode, variant=variant, fan=fan)
                (values,) = read(target, variant)
                assert values["fan"] == code


@pytest.mark.parametrize("swing, code", [("off", 0), ("1", 1), ("2", 3), ("3", 4)])
def test_swing_positions_use_their_documented_codes(swing, code):
    for power in (True, False):
        (values,) = read(state(power, swing_v=swing))
        assert values["swing"] == code
        assert values["special"] == "power"


@pytest.mark.parametrize("variant", ["A907", "A903", "A705"])
def test_model_bits(variant):
    for mode in device(variant).capabilities.modes:
        (values,) = read(state(True, mode, variant=variant), variant)
        assert values["model2"] == (variant != "A907")
        setpoint = mode in ("cool", "heat")
        assert values["model"] == (variant == "A705" and setpoint)


@pytest.mark.parametrize("variant", ["A907", "A903", "A705"])
def test_off_carries_mode_auto(variant):
    for mode in device(variant).capabilities.modes:
        off = state(False, mode, 27.0, variant=variant, fan="2")
        assert messages(off, variant) == messages(
            state(False, "auto", 15.0, variant=variant, fan="2"), variant
        )
        (values,) = read(off, variant)
        assert (values["power_special"], values["mode"]) == ("off", 0)


@pytest.mark.parametrize(
    "power, before, expected",
    [
        (True, None, "on_from_off"),
        (True, False, "on_from_off"),
        (True, True, "on"),
        (False, None, "off"),
        (False, True, "off"),
        (False, False, "off"),
    ],
)
def test_power_special_follows_the_previous_power(power, before, expected):
    # IRac::sendAc passes prev->power; a fresh object's previous is off.
    previous = None if before is None else state(before, "heat", 30.0)
    (values,) = read(state(power), previous=previous)
    assert values["power_special"] == expected
    assert values["special"] == "power"


def test_previous_changes_nothing_but_power_special():
    target = state(True, "cool", 24.0, fan="2", swing_v="3")
    for previous in (state(True, "heat", 30.0, swing_v="1"), state(True, "dry")):
        (ours,) = messages(target, previous=previous)
        (fresh,) = messages(target, previous=state(False))
        a, b = SHARP_AC_LAYOUT.read(ours), SHARP_AC_LAYOUT.read(fresh)
        assert {k for k in a if a[k] != b[k]} == {"power_special"}


def test_purifier_sets_ion():
    for on in (False, True):
        (values,) = read(state(features=features(purifier=on)))
        assert values["ion"] == on


@pytest.mark.parametrize("variant", ["A907", "A903", "A705"])
def test_economy_and_light_are_not_offered(variant):
    # IRac::sharp never sends setEconoToggle, and setLightToggle's Special
    # is overwritten by setMode/setPower: both did nothing, so they are not
    # capabilities. A caller passing them anyway sends the plain state.
    caps = device(variant).capabilities
    assert "economy" not in caps.features and "light" not in caps.features
    for power in (True, False):
        plain = state(power, variant=variant)
        on = state(power, variant=variant, features={"economy": True, "light": True})
        assert on == plain
        assert messages(on, variant) == messages(plain, variant)


@pytest.mark.parametrize(
    "fan, capture",
    [
        ("1", COOL_FAN1_28),
        ("2", COOL_FAN2_28),
        ("3", COOL_FAN3_28),
        ("4", COOL_FAN4_28),
    ],
)
def test_a907_fan_levels_are_the_real_captures(fan, capture):
    # The A907 remote's four speeds (FAN1..FAN4: kSharpAcFanMin, FanMed,
    # FanHigh, FanMax). The captures are single-button presses (Special
    # kSharpAcSpecialFan); IRac's message carries Special Power.
    (ours,) = messages(state(True, "cool", 28.0, fan=fan), previous=state(True))
    expected = bytearray.fromhex(capture)
    SHARP_AC_LAYOUT.write_raw(expected, "special", 0x00)  # kSharpAcSpecialPower
    SHARP_AC_LAYOUT.checksum.apply(expected)
    assert ours == bytes(expected)
    assert SHARP_AC_LAYOUT.read(bytes.fromhex(capture))["special"] == "fan"


def test_a907_fan_4_is_the_legacy_highest():
    caps = device("A907").capabilities
    assert caps.fan.values == ("auto", "1", "2", "3", "4")
    assert [caps.fan.label(v) for v in caps.fan.values] == [
        "auto",
        "low",
        "medium",
        "high",
        "highest",
    ]
    for variant in ("A903", "A705"):
        assert device(variant).capabilities.fan.values == ("auto", "1", "2", "3")


def test_capabilities_are_the_documented_ones():
    for variant, modes in (
        ("A907", ("auto", "cool", "dry", "heat")),
        ("A903", ("auto", "cool", "dry", "fan")),
        ("A705", ("cool", "dry", "fan")),
    ):
        caps = device(variant).capabilities
        assert caps.modes == modes
        # kSharpAcMinTemp / kSharpAcMaxTemp
        assert (caps.temperature.min, caps.temperature.max) == (15.0, 30.0)
        assert caps.swing_v.values == ("off", "1", "2", "3")
        assert caps.swing_h is None
        assert set(caps.features) == {"cleaning", "powerful", "purifier"}


@pytest.mark.parametrize("power", [True, False])
def test_powerful_adds_a_turbo_message(power):
    target = state(power, "cool", 24.0, fan="1", features=features(powerful=True))
    main, turbo = read(target)
    assert main == read(state(power, "cool", 24.0, fan="1"))[0]
    expected = dict(main, fan=7, power_special="special_on", special="turbo")
    assert turbo == expected


def test_cleaning_when_off_sends_two_off_messages():
    # IRac's final setPower(false) clears Clean again, as in C. The first is
    # sent before setClean(false) restores the fan, which setMode left at
    # auto (an off message carries mode auto).
    target = state(False, "cool", 24.0, fan="3", features=features(cleaning=True))
    first, second = read(target)
    plain = read(state(False, "cool", 24.0, fan="3"))[0]
    assert second == plain
    assert first == dict(plain, fan=2)


@pytest.mark.parametrize("mode, fan", [("auto", 2), ("dry", 2), ("cool", 5)])
def test_cleaning_off_message_has_fan_auto_without_a_setpoint(mode, fan):
    target = state(True, mode, 24.0, fan="3", features=features(cleaning=True))
    first = read(target)[0]
    assert (first["power_special"], first["fan"]) == ("off", fan)


def test_cleaning_when_on_sends_off_then_the_clean_message():
    target = state(True, "heat", 24.0, fan="3", features=features(cleaning=True))
    for previous in (None, state(True)):
        off, clean = read(target, previous=previous)
        plain = read(state(True, "heat", 24.0, fan="3"), previous=previous)[0]
        assert off == dict(plain, power_special="off")
        assert (clean["mode"], clean["fan"], clean["clean"]) == (3, 2, 1)
        assert (clean["temperature"], clean["temp_flags"]) == (0, 0)
        assert clean["power_special"] == "on_from_off"


def test_cleaning_and_powerful_turbo_follows_the_plain_state():
    # The turbo frame comes from the state setPower restores, not from the
    # clean message (test_cleaning_with_powerful_sends_cs_turbo_frame).
    both = features(cleaning=True, powerful=True)
    off, clean, turbo = read(state(True, "cool", 24.0, features=both))
    _, plain_turbo = read(state(True, "cool", 24.0, features=features(powerful=True)))
    assert clean["clean"] == 1 and turbo["clean"] == 0
    assert turbo == plain_turbo


def test_unknown_model_gets_the_a907_and_bad_variants_are_refused():
    with pytest.raises(ValueError, match="unknown model"):
        SharpAcDevice("sharp", "nope")
    with pytest.raises(ValueError, match="variant"):
        SharpAcDevice("sharp", "nope", variant="A999")


def _record(model, **match):
    return next(
        r
        for r in load_oracle("SHARP_AC")
        if r["model"] == model and all(r["state"].get(k) == v for k, v in match.items())
    )


def test_undeclared_fan_deviation_is_reported():
    record = _record("AH-PR13-GL", mode="cool", fan="high")
    with pytest.raises(AssertionError, match="fan"):
        assert_matches_oracle(device_for(record), record, SHARP_AC_LAYOUT_ONLY, ())


@pytest.mark.parametrize(
    "field", ["clean", "mode", "temperature", "model", "temp_flags"]
)
def test_undeclared_clean_deviation_is_reported(field):
    # A705 cool 22 with cleaning: C's second message is a cool one.
    record = _record("CRMC-A705 JBEZ remote", cleaning="on")
    dev = device_for(record)
    defects = [d for d in DEFECTS + CLEAN_DEFECTS if d.field != field]
    with pytest.raises(AssertionError, match=field):
        assert_matches_oracle(dev, record, dev.layouts, defects)


def test_undeclared_swing_sequence_deviation_is_reported():
    record = _record("Sharp AY-ZP40KR")
    dev = device_for(record)
    states = [
        {"mode": "cool", "temperature": 22, "fan": "auto", "swing": "off"},
        {"mode": "cool", "temperature": 22, "fan": "auto", "swing": "90°"},
    ]
    with pytest.raises(AssertionError, match="swing"):
        assert_sequence_matches_c(dev, record, states, dev.layouts, DEFECTS)


def test_layouts_must_cover_every_frame():
    record = _record("Sharp AY-ZP40KR", powerful="on")
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(device_for(record), record, SHARP_AC_LAYOUT_ONLY, ())


SHARP_AC_LAYOUT_ONLY = (SHARP_AC_LAYOUT,)
