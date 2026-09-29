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
from pyhvac import registry
from pyhvac.plugins.samsung import (
    SAMSUNG_AC_LAYOUT_1,
    SAMSUNG_AC_LAYOUT_2,
    SAMSUNG_AC_LAYOUT_3,
    SAMSUNG_AC_MODELS,
    SamsungAcDevice,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Samsung values here (pyhvac's glue,
# not IRremoteESP8266): IRGHVAC.trans_swing and trans_hswing have no "on"
# key, so IRac keeps swingv and swingh at kOff and IRac::samsung calls
# setSwing(false) and setSwingH(false): Swing is kSamsungAcSwingOff (0b111).
# The port sends kSamsungAcSwingV, SwingH or SwingBoth. With economy on,
# setEcono turns vertical swing on in C too, so there only the horizontal
# part is lost (both -> vertical).
SWING_V = Defect("swing", "vertical", "off", "C path drops swing 'on'")
SWING_H = Defect("swing", "horizontal", "off", "C path drops hswing 'on'")
SWING_BOTH = Defect("swing", "both", "off", "C path drops swing and hswing 'on'")
SWING_H_ECONO = Defect("swing", "both", "vertical", "C path drops hswing 'on'")
DEFECTS = (SWING_V, SWING_H, SWING_BOTH, SWING_H_ECONO)

MODES = ("auto", "cool", "dry", "heat", "fan")
FEATURES = ("cleaning", "quiet", "powerful", "economy", "light", "purifier")

# ir_Samsung_test.cpp real captures, as sections. Standard (14-byte)
# messages are sections 1 and 3 of the extended one; each section carries its
# own checksum.
REAL_EXAMPLE = "02920f000000f0", "0102af710015f0"  # DecodeRealExample
REAL_EXAMPLE_2 = "02920f000000f0", "01e2fe718011f0"  # DecodeRealExample2
HEAT_SAMPLE = "02920f000000f0", "0102af711041f0"  # DecodeHeatSample
COOL_SAMPLE = "02920f000000f0", "01e2fe714011f0"  # DecodeCoolSample
QUIET_ON = "02820f000020f0", "01f2fe710011f0"  # Issue734QuietSetting
POWERFUL_OFF = "02920f000000f0", "01f2fe710011f0"  # Issue734PowerfulOff
POWERFUL_ON = "02920f000000f0", "01a2fe77001ff0"  # SetAndGetPowerful
ECONO_ON = "02920f000000f0", "01d2ae7f8011f0"  # SetAndGetEcono (row 33)
MIDDLE = "01d20f00000000"  # sendExtended's extended_middle_section
POWER_ON_SAMPLE = "02920f000000f0", MIDDLE, "01e2fe718011f0"  # DecodePowerOnSample
POWER_OFF_SAMPLE = "02b20f000000c0", MIDDLE, "0102ff718011c0"  # DecodePowerOffSample
ISSUE_1648_ON = "02920f000000f0", MIDDLE, "01c2fe719015f0"  # Issue1648 onState


def wire(record):
    """``record`` with the pulses the C library puts on the wire.

    sendSamsungAC ends the last section with space(kSamsungAcSectionGap) and
    then space(kDefaultMessageGap - kSamsungAcSectionGap). IRac's timing log
    keeps them as two entries, so the fixture's last entry sits at a mark
    position; on the wire they are one 100 000 µs space.
    """
    pulses = record["pulses"]
    assert len(pulses) % 2 and pulses[-2:] == [2886, 97114]
    return {**record, "pulses": pulses[:-2] + [100000]}


def device(model="generic"):
    return SamsungAcDevice("samsung", model)


def state(power=True, mode="cool", temperature=22.0, **kw):
    return device().normalise(HvacState(power, mode, temperature, **kw))


def sections(target, previous=None):
    leader, *rest = device().frames(previous, target, ())
    assert (leader.section, leader.data) == ("leader", b"")
    return [f.data for f in rest]


def read(target, previous=None):
    first, middle, last = sections(target, previous)
    return {
        **SAMSUNG_AC_LAYOUT_1.read(first),
        **{f"middle_{k}": v for k, v in SAMSUNG_AC_LAYOUT_2.read(middle).items()},
        **{f"last_{k}": v for k, v in SAMSUNG_AC_LAYOUT_3.read(last).items()},
    }


def last(target, previous=None):
    return SAMSUNG_AC_LAYOUT_3.read(sections(target, previous)[2])


def features(**on):
    return {k: on.get(k, False) for k in FEATURES}


@pytest.mark.parametrize("record", oracle_params("SAMSUNG_AC"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, wire(record), dev.LAYOUTS, DEFECTS)


@pytest.mark.parametrize("record, states", sequence_params("SAMSUNG_AC"))
def test_sequence_matches_a_persistent_c_object(record, states):
    # The clean toggle depends on the message before, which C's IRac keeps.
    dev = device()
    assert_sequence_matches_c(dev, record, states, dev.LAYOUTS, DEFECTS, adapt=wire)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    layouts = dev.LAYOUTS[1:]
    for record in load_oracle("SAMSUNG_AC"):
        target = state_from_record(dev, record["state"])
        for data, layout in zip(sections(target), layouts):
            values = layout.read(data)
            assert layout.build(**values) == bytearray(data)


# States the oracle grid lacks: off in every mode, every setpoint edge and
# fan, every swing combination (with and without economy), and every
# combination of the six features, on and off. Each is sent from a fresh C
# object, as the fixtures were recorded.
def _old(target):
    old = {
        "mode": target.mode if target.power else "off",
        "temperature": int(target.temperature),
        "fan": {"auto": "auto", "1": "low", "2": "medium", "3": "high"}[target.fan],
        "swing": "on" if target.swing_v == "swing" else "off",
        "hswing": "on" if target.swing_h == "swing" else "off",
    }
    old.update({k: "on" if v else "off" for k, v in target.features.items()})
    return old


EXTRA_STATES = (
    [
        HvacState(power, mode, t, fan=fan)
        for mode in MODES
        for power in (True, False)
        for t in (16.0, 17.0, 29.0, 30.0)
        for fan in ("auto", "1", "2", "3")
    ]
    + [
        HvacState(
            power,
            mode,
            22.0,
            fan="2",
            swing_v=sv,
            swing_h=sh,
            features={"economy": econo},
        )
        for mode in MODES
        for power in (True, False)
        for sv, sh in itertools.product(("off", "swing"), repeat=2)
        for econo in (False, True)
    ]
    + [
        HvacState(power, mode, 24.0, fan="3", features=dict(zip(FEATURES, flags)))
        for power in (True, False)
        for mode in ("auto", "cool")
        for flags in itertools.product((False, True), repeat=len(FEATURES))
    ]
    + [
        HvacState(True, mode, 24.0, fan=fan, features=features(**{feature: True}))
        for mode in ("dry", "heat", "fan")
        for fan in ("1", "3")
        for feature in ("quiet", "powerful", "economy")
    ]
)


def test_states_beyond_the_oracle_grid_match_the_c_path():
    pytest.importorskip("pyhvac.irhvac")
    dev = device()
    record = load_oracle("SAMSUNG_AC")[0]
    for target in EXTRA_STATES:
        (rec,) = c_sequence(record, [_old(dev.normalise(target))])
        assert_matches_oracle(dev, wire(rec), dev.LAYOUTS, DEFECTS)


def test_checksum_holds_on_the_real_captures():
    checksum = SAMSUNG_AC_LAYOUT_1.checksum
    captures = (
        REAL_EXAMPLE
        + REAL_EXAMPLE_2
        + HEAT_SAMPLE
        + COOL_SAMPLE
        + QUIET_ON
        + POWERFUL_OFF
        + POWERFUL_ON
        + ECONO_ON
        + POWER_ON_SAMPLE
        + POWER_OFF_SAMPLE
        # Issue604DecodeExtended, and the timer middle sections of
        # TestIRSamsungAcClass's timer tests.
        + ("02a90f000000c0", "01c90f00000000", "01f9ce71e041c0")
        + ("01a20f30000200", "01928f10000600", "01628f05030600")
    )
    for section in captures:
        assert checksum.check(bytes.fromhex(section)), section
    broken = bytearray.fromhex(REAL_EXAMPLE[1])
    broken[4] ^= 0x10
    assert not checksum.check(broken)


def test_checksum_writes_only_bits_12_to_19():
    # Sum<n>Lower (high nibble of byte 1), Sum<n>Upper (low nibble of byte 2).
    checksum = SAMSUNG_AC_LAYOUT_3.checksum
    assert checksum.bits() == set(range(12, 20))
    data = bytearray.fromhex(REAL_EXAMPLE[1])
    data[1] &= 0x0F
    data[2] &= 0xF0
    checksum.apply(data)
    assert data.hex() == REAL_EXAMPLE[1]


@pytest.mark.parametrize(
    "capture, target",
    [
        # cool, 16C, fan low, swing(V), light on
        (REAL_EXAMPLE, dict(fan="1", swing_v="swing", temperature=16.0)),
        # cool, 24C, fan auto, light on
        (REAL_EXAMPLE_2, dict(temperature=24.0)),
        # heat, 17C, fan auto, swing(V), light on
        (HEAT_SAMPLE, dict(mode="heat", temperature=17.0, swing_v="swing")),
        # cool, 20C, fan auto, light on
        (COOL_SAMPLE, dict(temperature=20.0)),
        # cool, 16C, quiet (fan auto), light on
        (QUIET_ON, dict(temperature=16.0, quiet=True)),
        # cool, 16C, fan auto, light on
        (POWERFUL_OFF, dict(temperature=16.0)),
        # cool, 16C, powerful (fan turbo), light on
        (POWERFUL_ON, dict(temperature=16.0, fan="3", powerful=True)),
        # cool, 24C, econo (fan auto, swing(V)), light on
        (ECONO_ON, dict(temperature=24.0, fan="2", economy=True)),
        # the extended power-on message: cool, 24C, fan auto, light on
        (POWER_ON_SAMPLE, dict(temperature=24.0)),
        # Issue 1648's on state: cool, 25C, fan low, light on
        (ISSUE_1648_ON, dict(temperature=25.0, fan="1")),
    ],
)
def test_port_reproduces_the_real_captures(capture, target):
    kw = dict(mode="cool", fan="auto")
    kw.update(target)
    flags = {k: kw.pop(k) for k in FEATURES if k in kw}
    ours = sections(state(True, features=features(light=True, **flags), **kw))
    if len(capture) == 2:  # a standard message: sections 1 and 3
        ours = [ours[0], ours[2]]
    assert [s.hex() for s in ours] == list(capture)


def test_off_differs_from_the_real_capture_only_in_the_mode_irac_gives_it():
    # DecodePowerOffSample: the remote keeps cool and fan auto in its off
    # message; IRac passes mode "off", which convertMode maps to
    # kSamsungAcAuto, and setMode then sets fan Auto2.
    ours = sections(state(False, "cool", 24.0, features=features(light=True)))
    assert [s.hex() for s in ours[:2]] == list(POWER_OFF_SAMPLE[:2])
    capture = bytearray.fromhex(POWER_OFF_SAMPLE[2])
    SAMSUNG_AC_LAYOUT_3.write_raw(capture, "mode", 0)
    SAMSUNG_AC_LAYOUT_3.write_raw(capture, "fan", 6)
    SAMSUNG_AC_LAYOUT_3.checksum.apply(capture)
    assert ours[2] == bytes(capture)


@pytest.mark.parametrize(
    "data, fields",
    [
        (
            bytes.fromhex(POWER_OFF_SAMPLE[2]),
            {
                "power": False,
                "mode": "cool",
                "fan": "auto",
                "temperature": 24,
                "swing": "off",
                "display": 1,
                "fan_special": "off",
            },
        ),
        (
            bytes.fromhex(POWERFUL_ON[1]),
            {"fan": "turbo", "fan_special": "powerful", "temperature": 16},
        ),
        (
            bytes.fromhex(ECONO_ON[1]),
            {"fan": "auto", "fan_special": "econo", "swing": "vertical"},
        ),
    ],
)
def test_layout_reads_the_real_captures(data, fields):
    values = SAMSUNG_AC_LAYOUT_3.read(data)
    assert {k: values[k] for k in fields} == fields
    assert SAMSUNG_AC_LAYOUT_3.build(**values) == bytearray(data)


def test_layout_reads_the_issue_604_capture():
    # Issue604DecodeExtended (off, heat, 30C, swing both). Its byte 1 low
    # nibble is 9, where every other capture (and kReset) has 2, so it is
    # read, not rebuilt.
    values = SAMSUNG_AC_LAYOUT_3.read(bytes.fromhex("01f9ce71e041c0"))
    fields = {"mode": "heat", "temperature": 30, "swing": "both", "power": False}
    assert {k: values[k] for k in fields} == fields


def test_middle_layout_reads_the_timer_captures():
    # TestIRSamsungAcClass timers: on timer 30 min; off 11 h, on 6 h;
    # sleep 8 h (an off timer with Sleep12).
    on_30m = SAMSUNG_AC_LAYOUT_2.read(bytes.fromhex("01a20f30000200"))
    assert (on_30m["on_time_mins"], on_30m["on_time_hours"]) == (3, 0)
    assert on_30m["on_timer_enable"] == 1
    both = SAMSUNG_AC_LAYOUT_2.read(bytes.fromhex("01628f05030600"))
    assert (both["off_time_hours"], both["on_time_hours"]) == (11, 6)
    sleep = SAMSUNG_AC_LAYOUT_2.read(bytes.fromhex("01a20f04000c00"))
    assert (sleep["off_time_hours"], sleep["sleep"], sleep["off_timer_enable"]) == (
        8,
        1,
        1,
    )


def test_message_is_always_extended():
    # IRac.h: samsung()'s forceextended defaults to true, so every message
    # is sendExtended's three sections, on or off.
    for target in (state(True), state(False), state(True, "auto")):
        leader, *rest = device().frames(None, target, ())
        assert [f.section for f in rest] == ["section", "section", "last"]
        assert rest[1].data.hex() == MIDDLE


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:4] == (690, 17844, 3086, 8864)
    assert pulses[-2:] == (586, 100000)
    assert len(pulses) == 2 + 3 * (2 + 2 * 56 + 2)
    # Sections 1 and 2 end with kSamsungAcSectionGap.
    section = 2 + 2 * 56 + 2
    assert pulses[1 + section] == pulses[1 + 2 * section] == 2886


@pytest.mark.parametrize("mode", MODES)
def test_mode_uses_its_documented_value(mode):
    codes = {"auto": 0, "cool": 1, "dry": 2, "fan": 3, "heat": 4}
    data = sections(state(True, mode))[2]
    assert SAMSUNG_AC_LAYOUT_3.read_raw(data, "mode") == codes[mode]


@pytest.mark.parametrize("mode", ["cool", "dry", "heat", "fan"])
@pytest.mark.parametrize("fan, raw", [("auto", 0), ("1", 2), ("2", 4), ("3", 5)])
def test_every_fan_level_uses_its_documented_code(mode, fan, raw):
    # kSamsungAcFanAuto / Low / Med / High, as convertFan maps them.
    data = sections(state(True, mode, fan=fan))[2]
    assert SAMSUNG_AC_LAYOUT_3.read_raw(data, "fan") == raw


@pytest.mark.parametrize("fan", ["auto", "1", "2", "3"])
def test_mode_auto_always_sends_fan_auto2(fan):
    # setMode(kSamsungAcAuto) sets kSamsungAcFanAuto2; setFan refuses the
    # other codes in auto.
    assert last(state(True, "auto", fan=fan))["fan"] == "auto2"


@pytest.mark.parametrize("t", [16, 17, 23, 29, 30])
def test_setpoint_is_sent_as_degrees_above_16(t):
    data = sections(state(True, "cool", float(t)))[2]
    assert SAMSUNG_AC_LAYOUT_3.read_raw(data, "temperature") == t - 16


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("t", [16.0, 23.0, 30.0])
def test_off_carries_mode_auto(mode, t):
    # IRac passes mode "off"; convertMode maps it to kSamsungAcAuto, so the
    # fan is Auto2 (the C-only test above checks off against C).
    off = state(False, mode, t, fan="3")
    assert sections(off) == sections(state(False, "auto", t, fan="3"))
    values = read(off)
    assert (values["power"], values["last_power"]) == (False, False)
    assert (values["last_mode"], values["last_fan"]) == ("auto", "auto2")
    assert values["last_temperature"] == int(t)


def test_power_sets_both_power_fields():
    for power, raw in ((True, 0b11), (False, 0b00)):
        first, _, third = sections(state(power))
        assert SAMSUNG_AC_LAYOUT_1.read_raw(first, "power") == raw
        assert SAMSUNG_AC_LAYOUT_3.read_raw(third, "power") == raw


@pytest.mark.parametrize(
    "sv, sh, expected",
    [
        ("off", "off", "off"),
        ("swing", "off", "vertical"),
        ("off", "swing", "horizontal"),
        ("swing", "swing", "both"),
    ],
)
def test_swing_uses_its_documented_code(sv, sh, expected):
    assert last(state(swing_v=sv, swing_h=sh))["swing"] == expected


@pytest.mark.parametrize("mode", ["cool", "dry", "heat", "fan"])
def test_quiet_sets_the_fan_to_auto(mode):
    values = read(state(True, mode, fan="3", features=features(quiet=True)))
    assert (values["quiet"], values["last_fan"]) == (1, "auto")
    assert values["last_fan_special"] == "off"


@pytest.mark.parametrize("mode", ["cool", "dry", "heat", "fan"])
def test_powerful_sets_turbo_and_clears_quiet(mode):
    target = state(True, mode, fan="1", features=features(powerful=True, quiet=True))
    values = read(target)
    assert (values["last_fan_special"], values["last_fan"]) == ("powerful", "turbo")
    assert values["quiet"] == 0


@pytest.mark.parametrize("mode", ["cool", "dry", "heat", "fan"])
def test_economy_sets_fan_auto_and_vertical_swing(mode):
    target = state(True, mode, fan="3", features=features(economy=True))
    values = last(target)
    assert (values["fan_special"], values["fan"]) == ("econo", "auto")
    assert values["swing"] == "vertical"


def test_economy_wins_over_powerful():
    # setEcono comes after setPowerful in IRac::samsung.
    values = last(state(True, "cool", features=features(economy=True, powerful=True)))
    assert (values["fan_special"], values["fan"]) == ("econo", "auto")


def test_quiet_stays_with_economy():
    values = read(state(True, "cool", features=features(economy=True, quiet=True)))
    assert (values["quiet"], values["last_fan_special"]) == (1, "econo")


def test_powerful_sends_nothing_in_mode_auto():
    # The fan cannot be Turbo in auto (setFan refuses it), so getPowerful is
    # false and setEcono(false) clears FanSpecial; quiet is still cleared.
    target = state(True, "auto", features=features(powerful=True, quiet=True))
    assert sections(target) == sections(state(True, "auto"))


def test_economy_in_mode_auto_keeps_fan_auto2():
    values = last(state(True, "auto", features=features(economy=True)))
    assert (values["fan_special"], values["fan"], values["swing"]) == (
        "econo",
        "auto2",
        "vertical",
    )


def test_light_sets_display_and_purifier_sets_ion():
    assert last(state(features=features(light=True)))["display"] == 1
    assert last(state(features=features(light=False)))["display"] == 0
    assert last(state(features=features(purifier=True)))["ion"] == 1
    assert last(state(features=features(purifier=False)))["ion"] == 0


def test_beep_sleep_and_timers_are_never_sent():
    for target in (state(True), state(False, "heat", 30.0, fan="3")):
        values = read(target)
        assert values["sleep"] == values["middle_sleep"] == 0
        assert values["last_beep"] == 0
        assert {k: v for k, v in values.items() if k.startswith("middle_")} == {
            f"middle_{k}": 0 for k in SAMSUNG_AC_LAYOUT_2.fields
        }


def test_cleaning_without_previous_is_sent_as_is():
    # A fresh C object's previous state is not a SAMSUNG_AC one, so
    # IRac::handleToggles leaves clean alone.
    assert last(state(features=features(cleaning=True)))["clean"] is True
    assert last(state(features=features(cleaning=False)))["clean"] is False


@pytest.mark.parametrize(
    "before, now, toggled",
    [
        (False, False, False),
        (False, True, True),
        (True, True, False),
        (True, False, True),
    ],
)
def test_cleaning_toggles_only_when_it_changes(before, now, toggled):
    # IRac::handleToggles: result.clean = desired.clean ^ prev->clean.
    previous = state(True, "heat", 30.0, features=features(cleaning=before))
    target = state(True, "cool", 22.0, features=features(cleaning=now))
    assert last(target, previous)["clean"] is toggled


def test_previous_changes_nothing_but_the_clean_toggle():
    target = state(True, "cool", 22.0, fan="2", features=features(cleaning=True))
    for previous in (state(False, "heat", 30.0), state(True, "auto", 16.0, fan="3")):
        values = last(target, previous)
        assert values["clean"] is True
        assert sections(target, previous) == sections(target)
    assert last(target, target)["clean"] is False


@pytest.mark.parametrize("model", SAMSUNG_AC_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("samsung", model), SamsungAcDevice)


@pytest.mark.parametrize("model", SAMSUNG_AC_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.samsung import Samsung

    legacy = LegacyDevice("samsung", model, Samsung)
    assert device(model).capabilities == legacy.capabilities


def _record(**match):
    return next(
        r
        for r in load_oracle("SAMSUNG_AC")
        if all(r["state"].get(k) == v for k, v in match.items())
    )


@pytest.mark.parametrize(
    "defect, match",
    [
        (SWING_V, {"mode": "cool", "swing": "on"}),
        (SWING_H, {"hswing": "on"}),
    ],
)
def test_undeclared_deviation_is_reported(defect, match):
    dev = device()
    record = wire(_record(**match))
    defects = [d for d in DEFECTS if d != defect]
    with pytest.raises(AssertionError, match="swing"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects)


@pytest.mark.parametrize(
    "defect, old",
    [
        (
            SWING_BOTH,
            {"mode": "cool", "temperature": 22, "swing": "on", "hswing": "on"},
        ),
        (
            SWING_H_ECONO,
            {"mode": "cool", "temperature": 22, "hswing": "on", "economy": "on"},
        ),
    ],
)
def test_undeclared_c_only_deviation_is_reported(defect, old):
    pytest.importorskip("pyhvac.irhvac")
    dev = device()
    (rec,) = c_sequence(load_oracle("SAMSUNG_AC")[0], [old])
    defects = [d for d in DEFECTS if d != defect]
    with pytest.raises(AssertionError, match="swing"):
        assert_matches_oracle(dev, wire(rec), dev.LAYOUTS, defects)


def test_layouts_must_cover_every_frame():
    dev = device()
    record = wire(_record(mode="cool", swing="on"))
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)
