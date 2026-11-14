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
from pyhvac.fields import Joined
from pyhvac.ir.codec import decode, encode
from pyhvac.ir.model import Frame
from pyhvac.protocols.gree import (
    GREE,
    GREE_AMANA_MODELS,
    GREE_CAPABILITIES,
    GREE_COOPER_HUNTER_MODELS,
    GREE_EKOKAI_MODELS,
    GREE_GREEN_MODELS,
    GREE_LAYOUT,
    GREE_MODEL_VARIANT,
    GREE_MODELS,
    GREE_RUSCLIMATE_MODELS,
    GREE_SOLEUS_MODELS,
    GREE_ULTIMATE_MODELS,
    GREE_VAILLAND_MODELS,
    GreeDevice,
)
from pyhvac.protocols.kelvinator import KelvinatorBlockSum
from pyhvac.state import HvacState

# The C path deviates from the documented Gree values here:
# - fan "1" (low): the old glue passes kLow, which convertFan maps, like
#   kMedium, to kGreeFanMax - 1 (kGreeFanMed); toCommonFanSpeed reads that
#   back as kMedium. The port sends kGreeFanMin, which the real captures
#   below carry and IRGreeAC::toString names "Low".
# - swing_v 90° and 60°: the old glue passes kHigh and kUpperMiddle;
#   convertSwingV gives kGreeSwingMiddleUp and its default kGreeSwingAuto,
#   which setSwingVertical(false, ...) replaces with kGreeSwingLastPos. The
#   port sends the documented positions Up and MiddleUp.
DEFECTS = (
    Defect("fan", "1", "2", "kLow: convertFan gives kGreeFanMax - 1"),
    Defect("swing_v", "1", "2", "90° is kHigh: kGreeSwingMiddleUp"),
    Defect("swing_v", "2", "off", "60° is kUpperMiddle: convertSwingV's default"),
)
# Records without a "swing" key leave IRac's swingv at kOff: C sends
# kGreeSwingLastPos with SwingAuto clear, which is the port's swing "off"
# (state_from_record reads a missing swing as "off"), so they need no
# Defect.

# (plugin, model, legacy class, variant) for every served model.
LEGACY = {"YAW1F": "Greev1", "YBOFB": "Greev2", "YX1FSF": "Greev3"}
PLUGIN_MODELS = {
    "gree": GREE_MODELS,
    "amana": GREE_AMANA_MODELS,
    "cooper_hunter": GREE_COOPER_HUNTER_MODELS,
    "ekokai": GREE_EKOKAI_MODELS,
    "green": GREE_GREEN_MODELS,
    "rusclimate": GREE_RUSCLIMATE_MODELS,
    "soleus": GREE_SOLEUS_MODELS,
    "ultimate": GREE_ULTIMATE_MODELS,
    "vailland": GREE_VAILLAND_MODELS,
}
ALL_MODELS = [(p, m) for p, models in PLUGIN_MODELS.items() for m in models]
VARIANTS = ("YAW1F", "YBOFB", "YX1FSF")
MODES = ("auto", "cool", "dry", "fan", "heat")
FEATURE_FIELDS = {
    "powerful": "turbo",
    "light": "light",
    "cleaning": "xfan",
    "economy": "econo",
    "sleep": "sleep",
}
NAMES = ["block1", "block2"]


def device(variant="YAW1F"):
    return GreeDevice("gree", "gemeric", variant)


def record_device(record):
    return GreeDevice(record["plugin"], record["model"])


def defects_for(record):
    return DEFECTS


def state(power=True, mode="cool", temperature=22.0, variant="YAW1F", **kw):
    return device(variant).normalise(HvacState(power, mode, temperature, **kw))


def data(target, variant="YAW1F", previous=None):
    frames = device(variant).frames(previous, target, ())
    assert [f.section for f in frames] == NAMES
    return b"".join(f.data for f in frames)


def read(target, variant="YAW1F"):
    return GREE_LAYOUT.read(data(target, variant))


def message(pulses):
    return b"".join(f.data for f in decode(GREE, pulses, expected=NAMES))


def wire(text):
    """IRsendTest's "f38000d50m9000s4500..." as pulses."""
    return [int(d) for d in re.findall(r"[ms](\d+)", text)]


# TestSendGreeChars.SendData: the message and what IRsendTest records.
SEND_DATA = bytes.fromhex("12345678" "90abcdef")
SEND_DATA_WIRE = wire(
    "f38000d50"
    "m9000s4500"
    "m620s540m620s1600m620s540m620s540m620s1600m620s540m620s540m620s540"
    "m620s540m620s540m620s1600m620s540m620s1600m620s1600m620s540m620s540"
    "m620s540m620s1600m620s1600m620s540m620s1600m620s540m620s1600m620s540"
    "m620s540m620s540m620s540m620s1600m620s1600m620s1600m620s1600m620s540"
    "m620s540m620s1600m620s540"
    "m620s19980"
    "m620s540m620s540m620s540m620s540m620s1600m620s540m620s540m620s1600"
    "m620s1600m620s1600m620s540m620s1600m620s540m620s1600m620s540m620s1600"
    "m620s1600m620s540m620s1600m620s1600m620s540m620s540m620s1600m620s1600"
    "m620s1600m620s1600m620s1600m620s1600m620s540m620s1600m620s1600m620s1600"
    "m620s19980"
)

# TestDecodeGree.NormalRealExample (issue #386): a real YAW1F capture and
# the state it decodes to: cool, 26 C, "Fan: 1 (Low)", Swing(V) 2 (Up),
# Light on, "Display Temp: 3 (Outside)".
REAL_386 = bytes.fromhex("190a6050" "022300f0")
REAL_386_RAW = [
    9008, 4496, 644, 1660, 676, 530, 648, 558, 672, 1636, 646, 1660,
    644, 556, 650, 584, 626, 560, 644, 580, 628, 1680, 624, 560,
    648, 1662, 644, 582, 648, 536, 674, 530, 646, 580, 628, 560,
    670, 532, 646, 562, 644, 556, 672, 536, 648, 1662, 646, 1660,
    652, 554, 644, 558, 672, 538, 644, 560, 668, 560, 648, 1638,
    668, 536, 644, 1660, 668, 532, 648, 560, 648, 1660, 674, 554,
    622, 19990, 646, 580, 624, 1660, 648, 556, 648, 558, 674, 556,
    622, 560, 644, 564, 668, 536, 646, 1662, 646, 1658, 672, 534,
    648, 558, 644, 562, 648, 1662, 644, 584, 622, 558, 648, 562,
    668, 534, 670, 536, 670, 532, 672, 536, 646, 560, 646, 558,
    648, 558, 670, 534, 650, 558, 646, 560, 646, 560, 668, 1638,
    646, 1662, 646, 1660, 646, 1660, 648,
]  # fmt: skip
# TestGreeClass.Issue814Power (issue #814): real captures of cool, 23 C,
# "Fan: 1 (Low)", swing auto, Light on, from a YBOFB and a YAW1F remote,
# and the off message IRGreeAC sends for them.
REAL_814_YBOFB = bytes.fromhex("59072050" "012000c0")
REAL_814_YAW1F = bytes.fromhex("59076050" "012000c0")
REAL_814_OFF = bytes.fromhex("51072050" "01200040")
# TestGreeClass.Issue1821EnergySaver: a real YX1FSF capture in mode
# kGreeEcono (25 C shown as 77F, fan 1, swing LastPos), Econo bit clear.
REAL_1821 = bytes.fromhex("1d096058" "002000a0")


@pytest.mark.parametrize("record", oracle_params("GREE"))
def test_matches_c_library(record):
    dev = record_device(record)
    assert_matches_oracle(dev, record, dev.LAYOUTS, defects_for(record))


def test_oracle_covers_the_three_legacy_classes():
    seen = {(r["plugin"], r["model"], r["class"]) for r in load_oracle("GREE")}
    assert seen == {
        ("amana", "PBC093G00CC", "Greev1"),
        ("green", "YBOFB remote", "Greev2"),
        ("gree", "YX1F2F remote", "Greev3"),
    }
    for plugin, model, cls in seen:
        assert LEGACY[GreeDevice(plugin, model).variant] == cls


def test_layouts_cover_the_two_blocks():
    assert device().LAYOUTS == (Joined(GREE_LAYOUT, 2),)
    assert len(GREE_LAYOUT.skeleton) == 8  # kGreeStateLength


def test_checksum_is_kelvinators_block_checksum():
    # IRGreeAC::checksum is IRKelvinatorAC::calcBlockChecksum over the
    # 8-byte state: the Kelvinator port's block sum at 0, not a copy.
    assert GREE_LAYOUT.checksum == KelvinatorBlockSum(0)


def test_layout_round_trips_every_oracle_state():
    for record in load_oracle("GREE"):
        dev = record_device(record)
        raw = data(state_from_record(dev, record["state"]), dev.variant)
        values = GREE_LAYOUT.read(raw)
        assert GREE_LAYOUT.build(**values) == bytearray(raw)
        assert GREE_LAYOUT.checksum.check(raw)


def test_every_oracle_message_has_the_checksum_and_the_fixed_bits():
    for record in load_oracle("GREE"):
        raw = message(record["pulses"])
        assert GREE_LAYOUT.checksum.check(raw)
        assert raw[3] == 0x50  # unknown1 0b0101, Celsius
        assert raw[5] & 0b0011_1000 == 0b0010_0000  # unknown2 0b100
        assert raw[6] == 0 and raw[7] & 0x0B == 0


def test_skeleton_is_the_reset_state():
    # TestGreeClass.SetAndGetRaw: getRaw on a reset object.
    assert GREE_LAYOUT.skeleton == bytes.fromhex("00092050" "00200050")
    assert GREE_LAYOUT.checksum.check(GREE_LAYOUT.skeleton)


@pytest.mark.parametrize(
    "raw",
    [
        REAL_386,
        REAL_814_YBOFB,
        REAL_814_YAW1F,
        REAL_814_OFF,
        REAL_1821,
        bytes.fromhex("a905d050" "002000a0"),  # SetAndGetRaw's expected state
        bytes.fromhex("08096050" "004400f0"),  # IFeel on (PR #770)
        bytes.fromhex("4c046050" "010200a0"),  # DisplayTempSource (#1118)
    ],
)
def test_checksum_known_values(raw):
    assert GREE_LAYOUT.checksum.check(raw)
    for i in (0, 3, 4, 6):
        broken = bytearray(raw)
        broken[i] ^= 0x11
        assert not GREE_LAYOUT.checksum.check(broken), i


def test_message_shape_matches_send_data():
    # The timings, the block footer (b010) and the gaps reproduce
    # IRsendTest's record of sendGree.
    frames = [Frame("block1", SEND_DATA[:4]), Frame("block2", SEND_DATA[4:])]
    signal = encode(GREE, frames)
    assert signal.carrier == 38000
    assert list(signal.pulses) == SEND_DATA_WIRE
    assert message(SEND_DATA_WIRE) == SEND_DATA


def test_real_capture_386_decodes():
    assert message(REAL_386_RAW) == REAL_386
    values = GREE_LAYOUT.read(REAL_386)
    assert (values["power"], values["mode"], values["temp"]) == (1, "cool", 26)
    assert (values["fan"], values["swing_v"], values["swing_auto"]) == ("1", "1", 0)
    assert (values["light"], values["model_a"], values["display_temp"]) == (1, 1, 3)


def test_port_reproduces_capture_386_but_its_display_source():
    # Everything the entity can ask for; DisplayTemp (Outside) has no
    # setter in IRac, so it stays clear.
    target = state(True, "cool", 26.0, fan="1", swing_v="1", features={"light": True})
    raw = bytearray(data(target))
    GREE_LAYOUT.write_raw(raw, "display_temp", 3)
    GREE_LAYOUT.checksum.apply(raw)
    assert bytes(raw) == REAL_386


@pytest.mark.parametrize(
    "variant, capture", [("YBOFB", REAL_814_YBOFB), ("YAW1F", REAL_814_YAW1F)]
)
def test_port_reproduces_the_issue_814_captures(variant, capture):
    # ModelA (byte 2 bit 6) is what tells the two remotes apart.
    target = state(
        True,
        "cool",
        23.0,
        variant,
        fan="1",
        swing_v="auto",
        features={"light": True},
    )
    assert data(target, variant) == capture


def test_issue_814_off_message_reads_as_documented():
    # IRGreeAC's off for the capture's settings; IRac's off carries mode
    # auto instead (see test_off_carries_mode_auto_at_25).
    values = GREE_LAYOUT.read(REAL_814_OFF)
    assert (values["power"], values["model_a"], values["mode"]) == (0, 0, "cool")


def test_energy_saver_capture_is_mode_econo():
    # TestGreeClass.Issue1821EnergySaver: the YX1FSF remote's energy saver
    # is mode kGreeEcono. The port (as setEcono) sets the mode and the
    # Econo bit, which this capture leaves clear; its Fahrenheit display
    # is not expressible.
    values = GREE_LAYOUT.read(REAL_1821)
    assert (values["mode"], values["power"], values["model_a"]) == ("econo", 1, 1)
    assert (values["econo"], values["use_fahrenheit"]) == (0, 1)
    ours = read(
        state(True, "cool", 25.0, "YX1FSF", features={"economy": True}), "YX1FSF"
    )
    assert (ours["mode"], ours["econo"], ours["temp"]) == ("econo", 1, 25)


def test_port_reproduces_the_energy_saver_capture_swing_off():
    # The same capture's swing byte is kGreeSwingLastPos with SwingAuto clear
    # and kGreeSwingHOff: the port's swing_v "off". Only what the port
    # cannot or does not send differs: ModelA (a YAW1F-only bit in IRac),
    # the Fahrenheit display and setEcono's Econo bit.
    target = state(
        True,
        "cool",
        25.0,
        "YX1FSF",
        fan="1",
        swing_v="off",
        features={"light": True, "economy": True},
    )
    raw = bytearray(data(target, "YX1FSF"))
    assert raw[4] == REAL_1821[4] == 0x00
    for name, value in (("model_a", 1), ("use_fahrenheit", 1), ("econo", 0)):
        GREE_LAYOUT.write_raw(raw, name, value)
    GREE_LAYOUT.checksum.apply(raw)
    assert bytes(raw) == REAL_1821


@pytest.mark.parametrize("model, variant", sorted(GREE_MODEL_VARIANT.items()))
def test_variant_comes_from_the_model(model, variant):
    assert GreeDevice("any", model).variant == variant
    assert GreeDevice("any", model).capabilities == GREE_CAPABILITIES[variant]


def test_unknown_model_gets_yaw1f_and_bad_variant_raises():
    with pytest.raises(ValueError, match="unknown model"):
        GreeDevice("gree", "nope")
    with pytest.raises(ValueError, match="variant"):
        GreeDevice("gree", "gemeric", "YAA")


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("t", [16.0, 23.0, 30.0])
def test_off_carries_mode_auto_at_25(variant, mode, t):
    # IRac passes kOff; convertMode's default is kGreeAuto, which locks the
    # setpoint at 25 C. The fan is the requested one (no dry lock), and
    # ModelA is clear with the power off.
    target = state(False, mode, t, variant, fan="3", features={"cleaning": True})
    values = read(target, variant)
    assert (values["power"], values["mode"], values["temp"]) == (0, "auto", 25)
    assert (values["fan"], values["model_a"], values["xfan"]) == ("3", 0, 1)


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("mode", MODES)
def test_every_mode_uses_its_documented_code(variant, mode):
    codes = {"auto": 0, "cool": 1, "dry": 2, "fan": 3, "heat": 4}
    raw = data(state(True, mode, variant=variant), variant)
    assert GREE_LAYOUT.read_raw(raw, "mode") == codes[mode]
    values = GREE_LAYOUT.read(raw)
    assert values["power"] == 1
    assert values["model_a"] == (variant == "YAW1F")  # setPower


@pytest.mark.parametrize("t", range(16, 31))
@pytest.mark.parametrize("mode", MODES)
def test_every_setpoint_in_every_mode(t, mode):
    # setTemp: auto locks the setpoint at 25 C; the other modes send it.
    raw = data(state(True, mode, float(t)))
    expected = 25 if mode == "auto" else t
    assert GREE_LAYOUT.read_raw(raw, "temp") == expected - 16
    assert GREE_LAYOUT.read(raw)["temp_extra_degree_f"] == 0


def test_setpoint_is_clamped():
    # setTemp clamps to kGreeMinTempC..kGreeMaxTempC, the entity's range:
    # encode snaps out-of-range setpoints to it.
    dev = device()
    for asked, sent in ((10.0, 16), (40.0, 30)):
        pulses = dev.encode(None, HvacState(True, "cool", asked)).signal.pulses
        assert GREE_LAYOUT.read(message(pulses))["temp"] == sent


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("fan, code", [("auto", 0), ("1", 1), ("2", 2), ("3", 3)])
def test_every_fan_level(mode, fan, code):
    # kGreeFanAuto, Min, Med, Max; setFan locks dry to fan 1.
    raw = data(state(True, mode, fan=fan))
    assert GREE_LAYOUT.read_raw(raw, "fan") == (1 if mode == "dry" else code)


@pytest.mark.parametrize(
    "swing, code, auto",
    [
        ("off", 0b0000, 0),  # kGreeSwingLastPos (convertSwingV's kOff)
        ("auto", 0b0001, 1),  # kGreeSwingAuto, SwingAuto
        ("1", 0b0010, 0),  # Up (90°)
        ("2", 0b0011, 0),  # MiddleUp (60°)
        ("3", 0b0100, 0),  # Middle (45°)
        ("4", 0b0101, 0),  # MiddleDown (30°)
        ("5", 0b0110, 0),  # Down (0°)
    ],
)
@pytest.mark.parametrize("power", [True, False])
def test_swing_v_uses_its_documented_code(swing, code, auto, power):
    raw = data(state(power, "cool", swing_v=swing))
    assert GREE_LAYOUT.read_raw(raw, "swing_v") == code
    assert GREE_LAYOUT.read_raw(raw, "swing_auto") == auto


@pytest.mark.parametrize(
    "swing_h, code",
    [("off", 0), ("auto", 1), ("1", 2), ("2", 3), ("3", 4), ("4", 5), ("5", 6)],
)
@pytest.mark.parametrize("power", [True, False])
def test_every_swing_h_value(swing_h, code, power):
    # convertSwingH: kOff, kAuto, kLeftMax, kLeft, kMiddle, kRight, kRightMax.
    raw = data(state(power, "heat", swing_v="3", swing_h=swing_h))
    assert GREE_LAYOUT.read_raw(raw, "swing_h") == code
    assert GREE_LAYOUT.read(raw)["swing_v"] == "3"


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("power", [True, False])
def test_each_feature_sets_its_bit_only(variant, power):
    caps = GREE_CAPABILITIES[variant].features
    base = read(state(power, "cool", variant=variant), variant)
    for feature in caps:
        values = read(
            state(power, "cool", variant=variant, features={feature: True}), variant
        )
        field = FEATURE_FIELDS[feature]
        assert (values[field], base[field]) == (1, 0), feature
        changed = {k for k in values if values[k] != base[k]}
        if feature == "economy" and variant == "YX1FSF":
            # setEcono: on the YX1FSF, economy is also mode kGreeEcono.
            assert changed == {field, "mode"} and values["mode"] == "econo"
        else:
            assert changed == {field}, feature


def test_yaw1f_has_no_economy():
    assert "economy" not in GREE_CAPABILITIES["YAW1F"].features
    values = read(state(True, "cool", features={"economy": True}))
    assert (values["econo"], values["mode"]) == (0, "cool")


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("power", [True, False])
def test_yx1fsf_economy_is_mode_econo_in_every_mode(mode, power):
    # setEcono runs after setMode, setTemp and setFan: the mode becomes
    # kGreeEcono (off messages too) and the auto setpoint and dry fan
    # locks already applied stay.
    target = state(power, mode, 20.0, "YX1FSF", fan="3", features={"economy": True})
    values = read(target, "YX1FSF")
    sent = mode if power else "auto"
    assert (values["mode"], values["econo"], values["power"]) == ("econo", 1, power)
    assert values["temp"] == (25 if sent == "auto" else 20)
    assert values["fan"] == ("1" if sent == "dry" else "3")
    # YBOFB: the Econo bit alone.
    values = read(
        state(power, mode, 20.0, "YBOFB", features={"economy": True}), "YBOFB"
    )
    assert (values["mode"], values["econo"]) == (sent, 1)


def test_fields_irac_never_sets_stay_clear():
    for variant in VARIANTS:
        for power in (True, False):
            for mode in MODES:
                # Sleep is a feature now (test_each_feature_sets_its_bit_only).
                target = state(
                    power,
                    mode,
                    variant=variant,
                    fan="3",
                    swing_v="auto",
                    swing_h="5",
                    features={f: True for f in GREE_CAPABILITIES[variant].features},
                )
                assert read(target, variant)["sleep"] == 1
                values = read(target, variant)
                for field in (
                    "timer_half_hr",
                    "timer_tens_hr",
                    "timer_enabled",
                    "timer_hours",
                    "temp_extra_degree_f",
                    "use_fahrenheit",
                    "display_temp",
                    "ifeel",
                    "wifi",
                ):
                    assert values[field] == 0, field
                # Every other unnamed bit keeps stateReset's value.
                raw = data(target, variant)
                rebuilt = bytearray(GREE_LAYOUT.skeleton)
                for name in GREE_LAYOUT.fields:
                    GREE_LAYOUT.write_raw(
                        rebuilt, name, GREE_LAYOUT.read_raw(raw, name)
                    )
                GREE_LAYOUT.checksum.apply(rebuilt)
                assert bytes(rebuilt) == raw


def test_previous_is_ignored():
    dev = device("YX1FSF")
    target = dev.normalise(
        HvacState(True, "cool", 22.0, fan="2", swing_v="3", features={"economy": True})
    )
    for previous in (
        HvacState(False, "heat", 25.0),
        HvacState(True, "dry", 16.0, fan="3", swing_v="auto", swing_h="1"),
        target,
    ):
        assert dev.encode(previous, target).signal == dev.encode(None, target).signal


@pytest.mark.parametrize("variant", VARIANTS)
def test_capabilities_are_the_documented_ones(variant):
    caps = GREE_CAPABILITIES[variant]
    assert caps.modes == MODES
    # kGreeMinTempC / kGreeMaxTempC, whole degrees (TempExtraDegreeF is a
    # Fahrenheit bit).
    assert (caps.temperature.min, caps.temperature.max) == (16.0, 30.0)
    assert caps.temperature.decimals == (0,)
    assert caps.fan.values == ("auto", "1", "2", "3")  # kGreeFan{Auto,Min,Med,Max}
    assert caps.swing_v.values == ("off", "auto", "1", "2", "3", "4", "5")
    assert caps.swing_h.values == ("off", "auto", "1", "2", "3", "4", "5")
    expected = {"powerful", "light", "cleaning", "sleep"}
    if variant != "YAW1F":
        expected.add("economy")
    assert set(caps.features) == expected


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("power", [True, False])
def test_sleep_sets_the_sleep_bit(variant, mode, power):
    # GreeProtocol's Sleep (byte 0 bit 7), IRac::gree's setSleep(sleep >= 0).
    # TestGreeClass.HumanReadable: setSleep(true) shows "Sleep: On".
    base = read(state(power, mode, variant=variant), variant)
    on = read(state(power, mode, variant=variant, features={"sleep": True}), variant)
    assert (base["sleep"], on["sleep"]) == (0, 1)
    assert {k for k in on if on[k] != base[k]} == {"sleep"}


# States the oracle grid lacks: off in every mode with every feature, every
# setpoint in every mode, every fan level in every mode, every swing_v with
# every swing_h, the features alone and together in every mode.
def _extra_states(features):
    # The old glue has no sleep to pass to C.
    features = [f for f in features if f != "sleep"]
    all_on = {f: "on" for f in features}
    return (
        [
            {"mode": "off", "temperature": t, "fan": fan, "swing": "0°", **all_on}
            for t in (16, 23, 30)
            for fan in ("auto", "low", "medium", "high")
        ]
        + [
            {"mode": "off", "temperature": 20, "fan": "high", "swing": "45°", f: "on"}
            for f in features
        ]
        + [
            {"mode": m, "temperature": t, "fan": "medium", "swing": "auto"}
            for m in MODES
            for t in range(16, 31)
        ]
        + [
            {"mode": m, "temperature": 22, "fan": fan, "swing": "45°"}
            for m in MODES
            for fan in ("auto", "low", "medium", "high")
        ]
        + [
            {"mode": m, "temperature": 22, "fan": "high", "swing": s, "hswing": h}
            for m in ("cool", "off")
            for s in ("off", "auto", "90°", "60°", "45°", "30°", "0°")
            for h in (
                "off",
                "auto",
                "far left",
                "close left",
                "middle",
                "close right",
                "far right",
            )
        ]
        + [
            {"mode": m, "temperature": 24, "fan": "high", "swing": "0°", **all_on}
            for m in MODES
        ]
        + [
            {"mode": m, "temperature": 20, "fan": "high", "swing": "30°", f: "on"}
            for m in MODES
            for f in features
        ]
    )


def _first_record(cls):
    return next(r for r in load_oracle("GREE") if r["class"] == cls)


@pytest.mark.parametrize("variant", VARIANTS)
def test_states_beyond_the_oracle_grid_match_the_c_path(variant):
    record = _first_record(LEGACY[variant])
    dev = record_device(record)
    for rec in c_sequence(record, _extra_states(dev.capabilities.features)):
        assert_matches_oracle(dev, rec, dev.LAYOUTS, DEFECTS)


def _record(**match):
    return next(
        r
        for r in load_oracle("GREE")
        if all(r["state"].get(k) == v for k, v in match.items())
        and r["state"]["mode"] not in ("off", "dry")
    )


@pytest.mark.parametrize(
    "match, defect",
    [
        ({"fan": "low"}, DEFECTS[0]),
        ({"swing": "90°"}, DEFECTS[1]),
        ({"swing": "60°"}, DEFECTS[2]),
    ],
    ids=["fan-1", "swing_v-1", "swing_v-2"],
)
def test_undeclared_deviation_is_reported(match, defect):
    record = _record(**match)
    others = tuple(d for d in defects_for(record) if d != defect)
    dev = record_device(record)
    with pytest.raises(AssertionError, match=defect.field):
        assert_matches_oracle(dev, record, dev.LAYOUTS, others)


def test_records_without_swing_are_swing_off():
    # 29 records leave IRac's swingv at kOff; the port reads them as swing
    # "off" and sends kGreeSwingLastPos with SwingAuto clear, as C.
    records = [r for r in load_oracle("GREE") if "swing" not in r["state"]]
    assert len(records) == 29
    for record in records:
        dev = record_device(record)
        target = state_from_record(dev, record["state"])
        assert target.swing_v == "off"
        values = GREE_LAYOUT.read(message(record["pulses"]))
        assert (values["swing_v"], values["swing_auto"]) == ("off", 0)
        assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


# ------------------------------------------------------- "YAW1F-wifi" variant
# YAW1F with byte 5's high bits 0b110 (WiFi set, bit 7 set, bit 5 clear) on
# every message: SmartIR climate 1402 (Samsung), 3040 (Viessmann), 3120
# (Cooper & Hunter).


@pytest.mark.parametrize(
    "capture, target",
    [  # SmartIR climate 3040 (Viessmann Vitoclima 300-S)
        (
            "1904605000c00030",
            HvacState(True, "cool", 20.0, fan="1", features={"light": True}),
        ),
        (
            "2c09605000c000b0",
            HvacState(True, "heat", 25.0, fan="2", features={"light": True}),
        ),
    ],
)
def test_yaw1f_wifi_variant_reproduces_the_captures(capture, target):
    dev = GreeDevice("Test", "unit", variant="YAW1F-wifi")
    sent = dev.frames(None, dev.normalise(target), ())
    assert b"".join(f.data for f in sent).hex() == capture


def test_yaw1f_wifi_variant_has_the_yaw1f_capabilities():
    dev = GreeDevice("Test", "unit", variant="YAW1F-wifi")
    assert dev.capabilities == GreeDevice("Test", "unit", variant="YAW1F").capabilities


# ------------------------------------------------------- "YAW1F-0" variant
# YAW1F with byte 5's high bits 0b000: SmartIR climate 1183 (Gree), 1763
# (Daitsu), 1780 (Trotec).


@pytest.mark.parametrize(
    "capture, target",
    [
        (  # 1763 (Daitsu DS-12KIDC)
            "29096050000000c0",
            HvacState(True, "cool", 25.0, fan="2", features={"light": True}),
        ),
        (  # 1183 (Gree)
            "090a6050040000d0",
            HvacState(True, "cool", 26.0, swing_v="3", features={"light": True}),
        ),
    ],
)
def test_yaw1f_0_variant_reproduces_the_captures(capture, target):
    dev = GreeDevice("Test", "unit", variant="YAW1F-0")
    sent = dev.frames(None, dev.normalise(target), ())
    assert b"".join(f.data for f in sent).hex() == capture


# ------------------------------------------------------ "YX1FSF-H" variant
# YX1FSF with byte 7 bit 3 set in heat mode: SmartIR climate 1184, 1185
# (Gree), 2360 (Flouu).


def test_yx1fsf_h_variant_reproduces_a_heat_capture():
    dev = GreeDevice("Test", "unit", variant="YX1FSF-H")
    target = HvacState(True, "heat", 24.0, fan="1", features={"light": True})
    sent = dev.frames(None, dev.normalise(target), ())
    assert b"".join(f.data for f in sent).hex() == "1c08205000200008"  # 1185


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan"])
def test_yx1fsf_h_variant_matches_yx1fsf_outside_heat(mode):
    plain = GreeDevice("Test", "unit", variant="YX1FSF")
    heat = GreeDevice("Test", "unit", variant="YX1FSF-H")
    st = HvacState(True, mode, 24.0)
    assert plain.frames(None, plain.normalise(st), ()) == heat.frames(
        None, heat.normalise(st), ()
    )
