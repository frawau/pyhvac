import re

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
from pyhvac.fields import Joined
from pyhvac.ir.codec import decode, encode
from pyhvac.ir.model import Frame
from pyhvac.plugins.kelvinator import (
    KELVINATOR,
    KELVINATOR_GREE_MODELS,
    KELVINATOR_LAYOUT,
    KELVINATOR_MODELS,
    KELVINATOR_SHARP_MODELS,
    KelvinatorBlockSum,
    KelvinatorDevice,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Kelvinator values here:
# - swing_v 90°, 60° and 30°: the old glue passes kHigh, kUpperMiddle and
#   kLow; convertSwingV gives kKelvinatorSwingVHighAuto, its default
#   kKelvinatorSwingVAuto and kKelvinatorSwingVLowAuto, auto codes that
#   setSwingVertical(false, ...) replaces with kKelvinatorSwingVOff. The port
#   sends the documented positions Highest, UpperMiddle and LowerMiddle.
# - swing_h "on": the old glue (IRGHVAC.trans_hswing) has no "on", so IRac's
#   swingh stays kOff and setSwingHorizontal(false) clears SwingH (and
#   SwingAuto, unless swing_v is auto). The port sets both.
DEFECTS = (
    Defect("swing_v", "1", "off", "90° is kHigh: kKelvinatorSwingVHighAuto"),
    Defect("swing_v", "2", "off", "60° is kUpperMiddle: convertSwingV's default"),
    Defect("swing_v", "4", "off", "30° is kLow: kKelvinatorSwingVLowAuto"),
    Defect("swing_h", "swing", "off", "legacy trans_hswing has no 'on'"),
    Defect("swing_auto", 1, 0, "legacy trans_hswing has no 'on'"),
)

ALL_MODELS = (
    [("kelvinator", m) for m in KELVINATOR_MODELS]
    + [("gree", m) for m in KELVINATOR_GREE_MODELS]
    + [("sharp", m) for m in KELVINATOR_SHARP_MODELS]
)
MODES = ("auto", "cool", "fan", "dry", "heat")
FEATURES = ("purifier", "powerful", "quiet", "cleaning", "light")
FEATURE_FIELDS = {
    "purifier": "ion_filter",
    "powerful": "turbo",
    "quiet": "quiet",
    "cleaning": "xfan",
    "light": "light",
}
NAMES = ["command", "options", "command", "options"]


def device():
    return KelvinatorDevice("kelvinator", "generic")


def state(power=True, mode="cool", temperature=22.0, **kw):
    return device().normalise(HvacState(power, mode, temperature, **kw))


def data(target, previous=None):
    frames = device().frames(previous, target, ())
    assert [f.section for f in frames] == NAMES
    return b"".join(f.data for f in frames)


def read(target, previous=None):
    return KELVINATOR_LAYOUT.read(data(target, previous))


def message(pulses):
    return b"".join(f.data for f in decode(KELVINATOR, pulses, expected=NAMES))


def wire(text):
    """IRsendTest's "f38000d50m9010s4505..." as pulses."""
    return [int(d) for d in re.findall(r"[ms](\d+)", text)]


# TestSendKelvinator.SendDataOnly: the typical message and what IRsendTest
# records for it.
TYPICAL = bytes.fromhex("190b8050000000e0" "190b8070000010f0")
TYPICAL_WIRE = wire(
    "f38000d50"
    "m9010s4505"
    "m680s1530m680s510m680s510m680s1530m680s1530m680s510m680s510m680s510"
    "m680s1530m680s1530m680s510m680s1530m680s510m680s510m680s510m680s510"
    "m680s510m680s510m680s510m680s510m680s510m680s510m680s510m680s1530"
    "m680s510m680s510m680s510m680s510m680s1530m680s510m680s1530m680s510"
    "m680s510m680s1530m680s510"
    "m680s19975"
    "m680s510m680s510m680s510m680s510m680s510m680s510m680s510m680s510"
    "m680s510m680s510m680s510m680s510m680s510m680s510m680s510m680s510"
    "m680s510m680s510m680s510m680s510m680s510m680s510m680s510m680s510"
    "m680s510m680s510m680s510m680s510m680s510m680s1530m680s1530m680s1530"
    "m680s39950"
    "m9010s4505"
    "m680s1530m680s510m680s510m680s1530m680s1530m680s510m680s510m680s510"
    "m680s1530m680s1530m680s510m680s1530m680s510m680s510m680s510m680s510"
    "m680s510m680s510m680s510m680s510m680s510m680s510m680s510m680s1530"
    "m680s510m680s510m680s510m680s510m680s1530m680s1530m680s1530m680s510"
    "m680s510m680s1530m680s510"
    "m680s19975"
    "m680s510m680s510m680s510m680s510m680s510m680s510m680s510m680s510"
    "m680s510m680s510m680s510m680s510m680s510m680s510m680s510m680s510"
    "m680s510m680s510m680s510m680s510m680s1530m680s510m680s510m680s510"
    "m680s510m680s510m680s510m680s510m680s1530m680s1530m680s1530m680s1530"
    "m680s39950"
)


@pytest.mark.parametrize("record", oracle_params("KELVINATOR"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_oracle_covers_the_legacy_class():
    seen = {(r["plugin"], r["model"], r["class"]) for r in load_oracle("KELVINATOR")}
    assert seen == {("gree", "YAPOF3 remote", "Kelvinator")}


def test_layouts_cover_the_four_frames():
    assert device().LAYOUTS == (Joined(KELVINATOR_LAYOUT, 4),)
    assert len(KELVINATOR_LAYOUT.skeleton) == 16  # kKelvinatorStateLength


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("KELVINATOR"):
        raw = data(state_from_record(dev, record["state"]))
        values = KELVINATOR_LAYOUT.read(raw)
        assert KELVINATOR_LAYOUT.build(**values) == bytearray(raw)
        assert KELVINATOR_LAYOUT.checksum.check(raw)


def test_every_oracle_message_has_the_checksums_and_the_fixed_bytes():
    for record in load_oracle("KELVINATOR"):
        raw = message(record["pulses"])
        assert KELVINATOR_LAYOUT.checksum.check(raw)
        assert raw[8:11] == raw[0:3]  # fixup: bytes 8-10 repeat bytes 0-2
        assert (raw[3], raw[11]) == (0x50, 0x70)  # stateReset's bytes 3 and 11


def test_skeleton_is_the_reset_state():
    # TestKelvinatorClass.SetAndGetRaw: getRaw on a reset object.
    assert KELVINATOR_LAYOUT.skeleton == bytes.fromhex(
        "00000050000000a0" "00000070000000a0"
    )
    assert KELVINATOR_LAYOUT.checksum.check(KELVINATOR_LAYOUT.skeleton)


def test_checksum_known_values():
    # TestKelvinatorClass.Checksums and SetAndGetRaw's expected state.
    assert KELVINATOR_LAYOUT.checksum.check(TYPICAL)
    assert KELVINATOR_LAYOUT.checksum.check(
        bytes.fromhex("0805205000000070" "0805207000000070")
    )
    for i in (0, 4, 8, 14):
        broken = bytearray(TYPICAL)
        broken[i] ^= 0x11
        assert not KELVINATOR_LAYOUT.checksum.check(broken), i


def test_block_sum_writes_only_the_high_nibble_of_byte_7():
    block = KelvinatorBlockSum(8)
    assert block.positions() == {15}
    assert block.bits() == set(range(124, 128))
    raw = bytearray(TYPICAL)
    raw[15] = 0x0A
    block.apply(raw)
    assert raw[15] == 0xFA  # Sum2 0xF, the low nibble kept


def test_layout_reads_the_typical_message():
    # SendDataOnly's state, as TestDecodeKelvinator.NormalSynthetic reads it:
    # power on, cool, 27 C, fan 1, XFan on.
    values = KELVINATOR_LAYOUT.read(TYPICAL)
    assert (values["power"], values["mode"], values["temp"]) == (1, "cool", 27)
    assert (values["fan"], values["basic_fan"], values["xfan"]) == ("1", 1, 1)
    # Every set bit is a named field or the skeleton's.
    rebuilt = bytearray(KELVINATOR_LAYOUT.skeleton)
    for name in KELVINATOR_LAYOUT.fields:
        KELVINATOR_LAYOUT.write_raw(
            rebuilt, name, KELVINATOR_LAYOUT.read_raw(TYPICAL, name)
        )
    KELVINATOR_LAYOUT.checksum.apply(rebuilt)
    assert bytes(rebuilt) == TYPICAL


def test_message_shape_matches_send_data_only():
    # The protocol's timings, command footer (b010) and gaps reproduce
    # IRsendTest's record of the typical message.
    frames = [Frame(n, TYPICAL[i : i + 4]) for n, i in zip(NAMES, range(0, 16, 4))]
    signal = encode(KELVINATOR, frames)
    assert signal.carrier == 38000
    assert list(signal.pulses) == TYPICAL_WIRE
    assert message(TYPICAL_WIRE) == TYPICAL


def test_port_reproduces_the_irac_example():
    # TestIRac.Kelvinator: cool, 19 C, fan medium, swing off, light, filter
    # and clean on: "Fan: 3 (Medium) ... XFan: On, Ion: On, Light: On".
    # kMedium is Fan 3: canonical "3" (FAN_5's "medium").
    target = state(
        True,
        "cool",
        19.0,
        fan="3",
        features={"light": True, "purifier": True, "cleaning": True},
    )
    raw = data(target)
    assert raw == bytes.fromhex("3903e05000000060" "3903e07000003090")
    values = KELVINATOR_LAYOUT.read(raw)
    assert (values["mode"], values["temp"], values["fan"]) == ("cool", 19, "3")
    assert (values["xfan"], values["ion_filter"], values["light"]) == (1, 1, 1)
    assert (values["turbo"], values["quiet"], values["swing_h"]) == (0, 0, "off")
    assert values["swing_v"] == "off"


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("t", [16.0, 23.0, 30.0])
def test_off_carries_mode_auto(mode, t):
    # IRac passes kOff; convertMode's default is kKelvinatorAuto. setTemp
    # runs after setMode, so the setpoint is the one asked for.
    target = state(False, mode, t, fan="3", features={"cleaning": True})
    values = read(target)
    assert (values["power"], values["mode"], values["temp"]) == (0, "auto", int(t))
    assert values["fan"] == "3"
    assert values["xfan"] == 0  # fixup clears XFan outside cool and dry


@pytest.mark.parametrize("mode", MODES)
def test_every_mode_uses_its_documented_code(mode):
    codes = {"auto": 0, "cool": 1, "dry": 2, "fan": 3, "heat": 4}
    raw = data(state(True, mode))
    assert KELVINATOR_LAYOUT.read_raw(raw, "mode") == codes[mode]
    assert raw[8] == raw[0]  # the second command repeats the mode and power
    assert read(state(True, mode))["power"] == 1


@pytest.mark.parametrize("t", range(16, 31))
@pytest.mark.parametrize("mode", MODES)
def test_every_setpoint_in_every_mode(t, mode):
    # setTemp after setMode: auto and dry send the requested setpoint too,
    # not setMode's kKelvinatorAutoTemp.
    raw = data(state(True, mode, float(t)))
    assert KELVINATOR_LAYOUT.read_raw(raw, "temp") == t - 16
    assert raw[9] == raw[1]


def test_setpoint_is_clamped():
    # setTemp clamps to kKelvinatorMinTemp..kKelvinatorMaxTemp, the entity's
    # range: encode snaps out-of-range setpoints to it.
    dev = device()
    for asked, sent in ((10.0, 16), (40.0, 30)):
        pulses = dev.encode(None, HvacState(True, "cool", asked)).signal.pulses
        assert KELVINATOR_LAYOUT.read(message(pulses))["temp"] == sent


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize(
    "fan, raw, basic",
    [
        ("auto", 0, 0),  # kKelvinatorFanAuto
        ("1", 1, 1),  # kKelvinatorFanMin
        ("2", 2, 2),
        ("3", 3, 3),
        ("4", 4, 3),
        ("5", 5, 3),  # kKelvinatorFanMax
    ],
)
def test_every_fan_level(mode, fan, raw, basic):
    # setFan: "0 is auto, 1-5 is the speed" (kKelvinatorFanMin..FanMax);
    # it caps BasicFan at kKelvinatorBasicFanMax.
    raw_data = data(state(True, mode, fan=fan))
    assert KELVINATOR_LAYOUT.read_raw(raw_data, "fan") == raw
    assert KELVINATOR_LAYOUT.read_raw(raw_data, "basic_fan") == basic


@pytest.mark.parametrize(
    "swing, code",
    [
        ("off", 0b0000),  # kKelvinatorSwingVOff
        ("auto", 0b0001),  # kKelvinatorSwingVAuto
        ("1", 0b0010),  # Highest (90°)
        ("2", 0b0011),  # UpperMiddle (60°)
        ("3", 0b0100),  # Middle (45°)
        ("4", 0b0101),  # LowerMiddle (30°)
        ("5", 0b0110),  # Lowest (0°)
    ],
)
@pytest.mark.parametrize("power", [True, False])
def test_swing_v_uses_its_documented_code(swing, code, power):
    raw = data(state(power, "cool", swing_v=swing))
    assert KELVINATOR_LAYOUT.read_raw(raw, "swing_v") == code
    # SwingAuto only for the auto swing (setSwingVertical), not for the odd
    # fixed positions UpperMiddle and LowerMiddle.
    assert KELVINATOR_LAYOUT.read_raw(raw, "swing_auto") == (swing == "auto")


@pytest.mark.parametrize("swing_v", ["off", "auto", "1", "3", "5"])
@pytest.mark.parametrize("power", [True, False])
def test_swing_h_sets_swing_h_and_swing_auto(swing_v, power):
    values = read(state(power, "heat", swing_v=swing_v, swing_h="swing"))
    assert (values["swing_h"], values["swing_auto"]) == ("swing", 1)
    assert values["swing_v"] == swing_v
    off = read(state(power, "heat", swing_v=swing_v))
    assert (off["swing_h"], off["swing_auto"]) == ("off", int(swing_v == "auto"))


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("power", [True, False])
def test_cleaning_only_in_cool_and_dry(mode, power):
    # fixup: "X-Fan mode is only valid in COOL or DRY modes"; an off message
    # is mode auto.
    values = read(state(power, mode, features={"cleaning": True}))
    assert values["xfan"] == int(power and mode in ("cool", "dry"))


@pytest.mark.parametrize("feature", FEATURES)
@pytest.mark.parametrize("power", [True, False])
def test_each_feature_sets_its_bit_only(feature, power):
    mode = "cool"
    base = read(state(power, mode))
    values = read(state(power, mode, features={feature: True}))
    field = FEATURE_FIELDS[feature]
    expected = 0 if (feature == "cleaning" and not power) else 1
    assert values[field] == expected and base[field] == 0
    changed = {k for k in values if values[k] != base[k]}
    assert changed == ({field} if expected else set())


def test_all_features_together():
    values = read(state(True, "dry", fan="3", features={f: True for f in FEATURES}))
    for field in FEATURE_FIELDS.values():
        assert values[field] == 1, field
    # setFan runs before setTurbo, so powerful survives the fan change.
    assert (values["fan"], values["turbo"]) == ("3", 1)


def test_fields_irac_never_sets_stay_clear():
    for power in (True, False):
        for mode in MODES:
            target = state(
                power,
                mode,
                fan="3",
                swing_v="auto",
                swing_h="swing",
                features={f: True for f in FEATURES},
            )
            values = read(target)
            for field in ("sleep_1_3", "sleep_2", "timer"):
                assert values[field] == 0, field
            # Every other unnamed bit keeps stateReset's value.
            raw = data(target)
            rebuilt = bytearray(KELVINATOR_LAYOUT.skeleton)
            for name in KELVINATOR_LAYOUT.fields:
                KELVINATOR_LAYOUT.write_raw(
                    rebuilt, name, KELVINATOR_LAYOUT.read_raw(raw, name)
                )
            KELVINATOR_LAYOUT.checksum.apply(rebuilt)
            assert bytes(rebuilt) == raw


def test_previous_is_ignored():
    dev = device()
    target = dev.normalise(
        HvacState(True, "cool", 22.0, fan="2", swing_v="3", features={"powerful": True})
    )
    for previous in (
        HvacState(False, "heat", 25.0),
        HvacState(True, "dry", 16.0, fan="3", swing_v="auto", swing_h="swing"),
        target,
    ):
        assert dev.encode(previous, target).signal == dev.encode(None, target).signal


@pytest.mark.parametrize("brand, model", ALL_MODELS)
def test_registry_serves_the_port(brand, model):
    assert isinstance(registry.get_device(brand, model), KelvinatorDevice)


def test_fan_offers_the_five_documented_speeds():
    # kKelvinatorFanAuto, then kKelvinatorFanMin (1) .. kKelvinatorFanMax (5).
    fan = device().capabilities.fan
    assert fan.values == ("auto", "1", "2", "3", "4", "5")
    # The legacy entity's low/medium/high (the stdAc kLow/kMedium/kHigh that
    # IRac passes unconverted, Fan 2/3/4) keep their meaning.
    assert {fan.label(v): v for v in ("2", "3", "4")} == {
        "low": "2",
        "medium": "3",
        "high": "4",
    }


# TestKelvinatorClass.MessageConstuction: setFan(1), cool, 27 C, SwingV off,
# SwingH on, IonFilter and XFan on, Quiet, Light and Turbo off, as
# IRsendTest records it.
MESSAGE_CONSTRUCTION_WIRE = wire(
    "f38000d50"
    "m9010s4505"
    "m680s1530m680s510m680s510m680s1530m680s1530m680s510m680s1530m680s510"
    "m680s1530m680s1530m680s510m680s1530m680s510m680s510m680s510m680s510"
    "m680s510m680s510m680s510m680s510m680s510m680s510m680s1530m680s1530"
    "m680s510m680s510m680s510m680s510m680s1530m680s510m680s1530m680s510"
    "m680s510m680s1530m680s510"
    "m680s19975"
    "m680s510m680s510m680s510m680s510m680s1530m680s510m680s510m680s510"
    "m680s510m680s510m680s510m680s510m680s510m680s510m680s510m680s510"
    "m680s510m680s510m680s510m680s510m680s510m680s510m680s510m680s510"
    "m680s510m680s510m680s510m680s510m680s1530m680s1530m680s1530m680s1530"
    "m680s39950"
    "m9010s4505"
    "m680s1530m680s510m680s510m680s1530m680s1530m680s510m680s1530m680s510"
    "m680s1530m680s1530m680s510m680s1530m680s510m680s510m680s510m680s510"
    "m680s510m680s510m680s510m680s510m680s510m680s510m680s1530m680s1530"
    "m680s510m680s510m680s510m680s510m680s1530m680s1530m680s1530m680s510"
    "m680s510m680s1530m680s510"
    "m680s19975"
    "m680s510m680s510m680s510m680s510m680s510m680s510m680s510m680s510"
    "m680s510m680s510m680s510m680s510m680s510m680s510m680s510m680s510"
    "m680s510m680s510m680s510m680s510m680s1530m680s510m680s510m680s510"
    "m680s510m680s510m680s510m680s510m680s1530m680s1530m680s1530m680s1530"
    "m680s39950"
)


def test_port_reproduces_the_fan_1_message_construction():
    # Fan "1" (kKelvinatorFanMin), which the legacy entity could not send.
    target = state(
        True,
        "cool",
        27.0,
        fan="1",
        swing_h="swing",
        features={"purifier": True, "cleaning": True},
    )
    signal = device().encode(None, target).signal
    assert list(signal.pulses) == MESSAGE_CONSTRUCTION_WIRE
    values = read(target)
    assert (values["fan"], values["basic_fan"]) == ("1", 1)
    # SendDataOnly's typical message is also fan 1: cool, 27 C, XFan on.
    assert data(state(True, "cool", 27.0, fan="1", features={"cleaning": True})) == (
        TYPICAL
    )


def test_fan_5_is_kelvinator_fan_max():
    # TestKelvinatorClass.HumanReadable: setFan(kKelvinatorFanMax) reads
    # "Fan: 5 (High)"; BasicFan is capped at kKelvinatorBasicFanMax.
    values = read(state(True, "cool", 25.0, fan="5"))
    assert (values["fan"], values["basic_fan"]) == ("5", 3)
    raw = data(state(True, "cool", 25.0, fan="5"))
    assert KELVINATOR_LAYOUT.read_raw(raw, "fan") == 5  # kKelvinatorFanMax


# States the oracle grid lacks: off in every mode with every feature, every
# setpoint in every mode, every fan level in every mode, every swing_v with
# swing_h, and the features in cool and dry (where cleaning is kept).
_ALL_ON = {f: "on" for f in FEATURES}
EXTRA_STATES = (
    [
        {"mode": "off", "temperature": t, "fan": fan, "swing": "auto", **_ALL_ON}
        for t in (16, 23, 30)
        for fan in ("auto", "low", "medium", "high")
    ]
    + [
        {"mode": m, "temperature": t, "fan": "medium", "swing": "off"}
        for m in MODES
        for t in range(16, 31)
    ]
    + [
        {"mode": m, "temperature": 22, "fan": fan, "swing": "45°"}
        for m in MODES
        for fan in ("auto", "low", "medium", "high")
    ]
    + [
        {"mode": m, "temperature": 22, "fan": "low", "swing": s, "hswing": h}
        for m in ("cool", "off")
        for s in ("off", "auto", "90°", "60°", "45°", "30°", "0°")
        for h in ("off", "on")
    ]
    + [
        {"mode": m, "temperature": 24, "fan": "high", "swing": "0°", **_ALL_ON}
        for m in MODES
    ]
    + [
        {"mode": m, "temperature": 20, "fan": "low", "swing": "off", f: "on"}
        for m in ("cool", "dry", "heat")
        for f in FEATURES
    ]
)


def test_states_beyond_the_oracle_grid_match_the_c_path():
    dev = device()
    record = load_oracle("KELVINATOR")[0]
    for rec in c_sequence(record, EXTRA_STATES):
        assert_matches_oracle(dev, rec, dev.LAYOUTS, DEFECTS)


def test_swing_h_matches_c_once_the_glue_passes_it():
    # With an "on" in trans_hswing (IRac's kAuto, glue="fixed"), C sets
    # SwingH, and setSwingHorizontal sets SwingAuto: the swing_h Defects are
    # the glue's.
    dev = device()
    record = load_oracle("KELVINATOR")[0]
    states = [
        {"mode": m, "temperature": 22, "fan": "low", "swing": s, "hswing": "on"}
        for m in ("cool", "heat", "off")
        for s in ("off", "auto", "45°", "0°")
    ]
    others = tuple(d for d in DEFECTS if d.field not in ("swing_h", "swing_auto"))
    for rec in c_sequence(record, states, glue="fixed"):
        assert_matches_oracle(dev, rec, dev.LAYOUTS, others)


def _record(**match):
    return next(
        r
        for r in load_oracle("KELVINATOR")
        if all(r["state"].get(k) == v for k, v in match.items())
        and r["state"]["mode"] != "off"
    )


@pytest.mark.parametrize(
    "match, defect",
    [
        ({"swing": "90°"}, DEFECTS[0]),
        ({"swing": "60°"}, DEFECTS[1]),
        ({"swing": "30°"}, DEFECTS[2]),
        ({"hswing": "on"}, DEFECTS[3]),
        ({"hswing": "on"}, DEFECTS[4]),
    ],
    ids=["swing_v-1", "swing_v-2", "swing_v-4", "swing_h", "swing_auto"],
)
def test_undeclared_deviation_is_reported(match, defect):
    others = tuple(d for d in DEFECTS if d != defect)
    with pytest.raises(AssertionError, match=defect.field):
        assert_matches_oracle(device(), _record(**match), device().LAYOUTS, others)
