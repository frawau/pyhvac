import dataclasses

import pytest

from oracle import load_oracle
from port_oracle import (
    Defect,
    assert_matches_oracle,
    c_sequence,
    oracle_params,
    sequence_params,
    state_from_record,
)
from pyhvac import registry
from pyhvac.ir.codec import DecodeError, decode
from pyhvac.plugins.lg import (
    LG2,
    LG2_COMMAND_LAYOUT,
    LG2_COMMANDS,
    LG2_LAYOUT,
    LG2_MODELS,
    Lg2Device,
)
from pyhvac.state import HvacState

V1, V2, V3 = "AKB75215403", "AKB74955603", "AKB73757604"
MODEL = {V1: "AKB75215403  remote", V2: "AKB74955603  remote", V3: "AMNW24GTPA1"}
LEGACY_CLASS = {V1: "LG2v1", V2: "LG2v2", V3: "LG2v3"}
MODES = ("auto", "cool", "fan", "dry", "heat")

# The C path deviates from the documented LG2 words here:
# - swing "90°"/"60°": IRGHVAC.trans_swing maps them to kHigh/kUpperMiddle.
#   AKB74955603: IRLgAc::convertSwingV sends kLgAcSwingVHigh for kHigh (so
#   kLgAcSwingVHighest is never sent) and has no kUpperMiddle case, so it
#   returns kLgAcSwingVOff, equal to the previous swing: no swing word at all
#   (see C_DROPS). AKB73757604: convertVaneSwingV sends High for kHigh and
#   its default, Highest, for kUpperMiddle. The port sends Highest for "1"
#   and High for "2", on every vane.
# - swing_h "swing" (the legacy "on"): IRGHVAC.trans_hswing has no "on", so
#   IRac's swingh stays kOff and AKB73757604 sends kLgAcSwingHOff. The port
#   sends kLgAcSwingHAuto.
DEFECTS = (
    Defect("command", "swing_v_highest", "swing_v_high", "C sends High for 90°"),
    Defect("command", "swing_h_auto", "swing_h_off", "C glue has no 'on' hswing"),
) + tuple(
    Defect("command", f"vane{v}_{ours}", f"vane{v}_{theirs}", reason)
    for v in range(4)
    for ours, theirs, reason in (
        ("highest", "high", "convertVaneSwingV(kHigh) for 90°"),
        ("high", "highest", "convertVaneSwingV has no kUpperMiddle (60°)"),
    )
)
# Words the port sends that C drops altogether, as (canonical swing_v,
# command): AKB74955603's swing "2" (60°), which C turns into
# kLgAcSwingVOff and so never sends.
C_DROPS = {("2", "swing_v_high")}
# ... unless C's previous swing was another position: then it sends Off.
SWING_60_AFTER_SWING = (
    Defect("command", "swing_v_high", "swing_v_off", "C sends Off for 60°"),
)

# Real captures (ir_LG_test.cpp).
ISSUE_548 = 0x880094D  # TestDecodeLG2.RealLG2Example: cool, 24 C, fan max
ISSUE_1008 = 0x8800347  # TestDecodeLG2.Issue1008: AKB75215403, cool, 18 C, max
AKB74955603_LOW = 0x880A396  # FanSpeedIssue1513: fan mode, 18 C, LowAlt
AKB74955603_HIGH = 0x880A3A7  # FanSpeedIssue1513: fan mode, 18 C, High
SWINGV_MIDDLE = 0x881306A  # TestIRLgAcClass.SwingV (AKB74955603)
VANE2_MIDDLE = 0x881334B  # AKB73757604: vane 2, Middle
VANE3_UPPER_MIDDLE = 0x88133B2  # AKB73757604: vane 3, Upper Middle
VANE2_UPPER_MIDDLE = 0x881333A  # DetectAKB73757604


def device(variant=V1):
    return Lg2Device("lg", MODEL[variant])


def word(frame):
    """A frame back to the 28-bit word ir_LG.h writes."""
    assert frame.nbits == 28
    return int.from_bytes(frame.data, "big") >> 4


def words(state, variant=V1, previous=None):
    dev = device(variant)
    if previous is not None:
        previous = dev.normalise(previous)
    return [word(f) for f in dev.frames(previous, dev.normalise(state), ())]


def as_frame(code):
    return (code << 4).to_bytes(4, "big")


def command(code):
    return LG2_COMMAND_LAYOUT.read(as_frame(code))["command"]


def variant_of(record):
    return LG2_MODELS[record["model"]]


def layouts(frames):
    """The state layout for a power-on message's first word, else commands."""
    first = LG2_LAYOUT if frames[0].data[1] not in (0xC0, 0x13) else None
    return tuple(
        LG2_LAYOUT if i == 0 and first else LG2_COMMAND_LAYOUT
        for i in range(len(frames))
    )


class AsC:
    """The device minus the words C drops (C_DROPS): C's frame list."""

    def __init__(self, dev, drops=C_DROPS):
        self.dev, self.drops = dev, drops
        self.PROTOCOL, self.capabilities = dev.PROTOCOL, dev.capabilities

    def normalise(self, state):
        return self.dev.normalise(state)

    def frames(self, previous, target, actions):
        return [
            f
            for f in self.dev.frames(previous, target, actions)
            if (target.swing_v, LG2_COMMAND_LAYOUT.read(f.data)["command"])
            not in self.drops
        ]


def check(record, defects=DEFECTS, drops=C_DROPS, previous=None):
    dev = AsC(device(variant_of(record)), drops)
    state = state_from_record(dev, record["state"])
    assert_matches_oracle(
        dev,
        record,
        layouts(dev.frames(previous, state, ())),
        defects,
        previous=previous,
    )


@pytest.mark.parametrize("record", oracle_params("LG2"))
def test_matches_c_library(record):
    check(record)


@pytest.mark.parametrize("record, states", sequence_params("LG2"))
def test_sequence_matches_a_persistent_c_object(record, states):
    # The swing words depend on the message before, which C's IRac keeps.
    variant = variant_of(record)
    dev = device(variant)
    previous = None
    for rec in c_sequence(record, states):
        state = state_from_record(dev, rec["state"])
        if variant == V3 and previous is not None:
            # previous only decides the swing_h word (the last one): C sends
            # it every time (stale _swingh_prev), the port only on a change
            # (see Lg2Device). Nothing else may depend on it.
            fresh = dev.frames(None, state, ())
            ours = dev.frames(previous, state, ())
            kept = previous.swing_h != state.swing_h or not state.power
            assert ours == (fresh if kept else fresh[:-1]), rec["state"]
            check(rec)
        elif previous is not None and previous.swing_v != "off":
            # C turns 60° into kLgAcSwingVOff: after another swing, where
            # the port sends swing_v_high, C sends the Off word.
            check(rec, DEFECTS + SWING_60_AFTER_SWING, drops=(), previous=previous)
        else:
            check(rec, previous=previous)
        previous = state
        if variant == V2 and state.swing_v == "2":
            # ... and C's previous swing after 60° is off (C_DROPS), so a
            # change from "2" to "off" sends no word.
            previous = dataclasses.replace(state, swing_v="off")


def test_every_oracle_record_is_served_by_its_variant():
    for record in load_oracle("LG2"):
        assert LEGACY_CLASS[variant_of(record)] == record["class"]


def test_layouts_round_trip_every_oracle_state():
    for record in load_oracle("LG2"):
        dev = device(variant_of(record))
        state = state_from_record(dev, record["state"])
        frames = dev.frames(None, state, ())
        for layout, frame in zip(layouts(frames), frames):
            values = layout.read(frame.data)
            assert layout.build(**values) == bytearray(frame.data)
            assert layout.checksum.check(frame.data)


def test_every_oracle_word_has_the_signature_and_checksum():
    for record in load_oracle("LG2"):
        n = len(record["pulses"]) // 60
        for frame in decode(LG2, record["pulses"], expected=["main"] * n):
            assert frame.data[0] == 0x88  # kLgAcSignature
            assert frame.data[3] & 0x0F == 0  # 28 bits: the last nibble unsent
            assert LG2_LAYOUT.checksum.check(frame.data)


def test_checksum_is_the_nibble_sum_below_the_signature():
    # ir_LG_test.cpp: calcChecksum(0x88C0051) == 1, calcChecksum(0x88C0354) == 4.
    for code, total in ((0x88C0051, 1), (0x88C0354, 4)):
        data = bytearray(as_frame(code))
        assert LG2_LAYOUT.checksum.check(data)
        data[3] = 0
        LG2_LAYOUT.checksum.apply(data)
        assert data[3] >> 4 == total


def test_checksum_bits_are_not_fields():
    assert LG2_LAYOUT.checksum.positions() == {3}
    for layout in (LG2_LAYOUT, LG2_COMMAND_LAYOUT):
        for name, f in layout.fields.items():
            assert not {b // 8 for b in f.bits} & {0, 3}, name


def test_every_documented_special_word_is_checksummed():
    # The header's constants carry their Sum: the table rebuilds each one.
    for code in (
        0x88C0051,
        0x88C00A6,
        0x8810001,
        0x8813048,
        0x8813059,
        0x881306A,
        0x881307B,
        0x881308C,
        0x881309D,
        0x8813149,
        0x881315A,
        0x881316B,
        0x881317C,
        VANE2_MIDDLE,
        VANE3_UPPER_MIDDLE,
        VANE2_UPPER_MIDDLE,
    ):
        name = command(code)
        assert name in LG2_COMMANDS
        assert bytes(LG2_COMMAND_LAYOUT.build(command=name)) == as_frame(code)


def test_vane_words():
    assert command(VANE2_MIDDLE) == "vane2_middle"
    assert command(VANE3_UPPER_MIDDLE) == "vane3_upper_middle"
    assert command(VANE2_UPPER_MIDDLE) == "vane2_upper_middle"


@pytest.mark.parametrize("variant", [V1, V2, V3])
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("temperature", [16.0, 20.0, 25.0])
def test_off_is_the_off_command_in_every_mode(variant, mode, temperature):
    # IRLgAc::send: power off always sends kLgAcOffCommand alone.
    state = HvacState(
        False,
        mode,
        temperature,
        fan="3",
        swing_v="auto",
        swing_h="swing",
        features={"light": False},
    )
    assert words(state, variant) == [0x88C0051]


@pytest.mark.parametrize("variant", [V1, V2, V3])
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("temperature", [16.0, 21.0, 25.0])
def test_state_word_carries_mode_and_setpoint(variant, mode, temperature):
    dev = device(variant)
    first = dev.frames(None, dev.normalise(HvacState(True, mode, temperature)), ())[0]
    values = LG2_LAYOUT.read(first.data)
    assert (values["power"], values["mode"], values["temperature"]) == (
        True,
        mode,
        int(temperature),
    )


def test_setpoint_is_clamped_to_16_25():
    assert (
        words(HvacState(True, "cool", 10.0))[0]
        == words(HvacState(True, "cool", 16.0))[0]
    )
    assert (
        words(HvacState(True, "cool", 30.0))[0]
        == words(HvacState(True, "cool", 25.0))[0]
    )


@pytest.mark.parametrize(
    "variant, fans",
    [
        # setFan: kLgAcFanHigh becomes kLgAcFanMax except on AKB74955603,
        # which also turns low into kLgAcFanLowAlt.
        (V1, {"auto": 5, "1": 0, "2": 1, "3": 2, "4": 4, "5": 4}),
        (V2, {"auto": 5, "1": 0, "2": 9, "3": 2, "4": 10}),
        (V3, {"auto": 5, "1": 0, "2": 1, "3": 2, "4": 4}),
    ],
)
def test_every_fan_level(variant, fans):
    for fan, code in fans.items():
        first = as_frame(words(HvacState(True, "cool", 22.0, fan=fan), variant)[0])
        assert LG2_LAYOUT.read_raw(first, "fan") == code


def test_real_captures_are_reproduced():
    assert words(HvacState(True, "cool", 24.0, fan="5"), V1) == [ISSUE_548]
    assert words(HvacState(True, "cool", 18.0, fan="5"), V1) == [ISSUE_1008]
    # TestIRLgAcClass.SwingV / Light (AKB74955603): the state word, then
    # kLgAcSwingVMiddle, then (light off) kLgAcLightToggle, last.
    state = HvacState(True, "fan", 18.0, fan="2", swing_v="3")
    assert words(state, V2)[1:] == [SWINGV_MIDDLE, 0x88C00A6]


@pytest.mark.parametrize(
    "capture, fan", [(AKB74955603_LOW, "2"), (AKB74955603_HIGH, "4")]
)
def test_akb74955603_captures_match_but_for_the_unnamed_bit(capture, fan):
    # These AKB74955603 remote words set bit 3 of byte 1 (in LGProtocol's
    # unnamed 3 bits). IRLgAc starts from kLgAcOffCommand, where those bits
    # are 0, and no setter writes them, so the C path (and the port) send 0.
    lit = {"light": True}
    (ours,) = words(HvacState(True, "fan", 18.0, fan=fan, features=lit), V2)
    theirs = LG2_LAYOUT.read(as_frame(capture))
    assert theirs["unnamed"] == 0b001
    assert LG2_LAYOUT.read(as_frame(ours)) == {**theirs, "unnamed": 0}
    assert LG2_LAYOUT.build(**theirs) == bytearray(as_frame(capture))


def test_swing_off_after_auto_capture():
    # TestIRLgAcClass.SwingVOffAfterAuto (AKB74955603): heat, 26 C (25 here,
    # the legacy maximum), fan lowest, light on; swing auto, then off: the
    # state word and kLgAcSwingVOff, nothing else.
    lit = {"light": True}
    before = HvacState(True, "heat", 25.0, fan="1", swing_v="auto", features=lit)
    after = HvacState(True, "heat", 25.0, fan="1", swing_v="off", features=lit)
    sent = words(after, V2, previous=before)
    assert len(sent) == 2 and sent[1] == 0x881315A
    assert LG2_LAYOUT.read(as_frame(sent[0])) == {
        "power": True,
        "mode": "heat",
        "temperature": 25,
        "fan": "lowest",
        "unnamed": 0,
    }


@pytest.mark.parametrize("swing", ["off", "auto", "1", "2", "3", "4", "5"])
def test_akb75215403_sends_the_state_word_only(swing):
    state = HvacState(True, "cool", 22.0, swing_v=swing, swing_h="swing")
    assert len(words(state, V1)) == 1
    assert words(state, V1) == words(HvacState(True, "cool", 22.0), V1)


@pytest.mark.parametrize(
    "swing, sent",
    [
        ("off", None),  # equal to a fresh IRac's previous swing (off)
        ("auto", "swing_v_swing"),
        ("1", "swing_v_highest"),
        ("2", "swing_v_high"),
        ("3", "swing_v_middle"),
        ("4", "swing_v_low"),
        ("5", "swing_v_lowest"),
    ],
)
def test_akb74955603_swing_word_without_previous(swing, sent):
    state = HvacState(True, "cool", 22.0, swing_v=swing, features={"light": True})
    names = [command(w) for w in words(state, V2)[1:]]
    assert names == ([] if sent is None else [sent])


@pytest.mark.parametrize("before", ["off", "auto", "1", "3", "5"])
@pytest.mark.parametrize("after", ["off", "auto", "1", "3", "5"])
def test_akb74955603_swing_word_with_previous_only_on_change(before, after):
    # IRac::lg seeds the previous swing from prev->swingv; IRLgAc::send sends
    # the swing word only when it differs.
    lit = {"light": True}
    previous = HvacState(True, "cool", 22.0, swing_v=before, features=lit)
    target = HvacState(True, "heat", 23.0, swing_v=after, features=lit)
    sent = words(target, V2, previous=previous)
    assert len(sent) == (1 if before == after else 2)


@pytest.mark.parametrize("light", [False, True])
def test_akb74955603_light_toggle_whenever_light_is_off(light):
    # No previous state is used, as C: IRLgAc::send sends the toggle after a
    # state word, which always turns the light on, whenever light is off.
    for previous in (None, HvacState(True, "cool", 22.0, features={"light": light})):
        sent = words(
            HvacState(True, "cool", 22.0, features={"light": light}), V2, previous
        )
        assert (sent[-1] == 0x88C00A6) == (not light)


def test_akb74955603_sends_no_swing_h():
    state = HvacState(True, "cool", 22.0, swing_h="swing", features={"light": True})
    assert len(words(state, V2)) == 1


@pytest.mark.parametrize(
    "swing, position",
    [
        ("off", "highest"),
        ("auto", "highest"),
        ("1", "highest"),
        ("2", "high"),
        ("3", "middle"),
        ("4", "low"),
        ("5", "lowest"),
    ],
)
def test_akb73757604_sends_every_vane_then_swing_h(swing, position):
    # IRac::lg never seeds the previous vanes: every vane goes, with or
    # without previous. Without previous the swing_h word goes too.
    state = HvacState(True, "cool", 22.0, swing_v=swing)
    vanes = [f"vane{v}_{position}" for v in range(4)]
    assert [command(w) for w in words(state, V3)[1:]] == vanes + ["swing_h_off"]
    previous = HvacState(True, "heat", 25.0, swing_v=swing)
    assert [command(w) for w in words(state, V3, previous)[1:]] == vanes


@pytest.mark.parametrize("before", ["off", "swing"])
@pytest.mark.parametrize("after", ["off", "swing"])
def test_akb73757604_swing_h_with_previous_only_on_change(before, after):
    # IRLgAc::send's rule (_swingh != _swingh_prev); C compares with stale
    # memory (_swingh_prev is never written), the port with previous.
    previous = HvacState(True, "cool", 22.0, swing_h=before)
    sent = words(HvacState(True, "cool", 22.0, swing_h=after), V3, previous)
    expected = (
        []
        if before == after
        else ["swing_h_auto" if after == "swing" else "swing_h_off"]
    )
    assert [command(w) for w in sent[5:]] == expected


def test_akb73757604_swing_h_and_no_light():
    sent = words(HvacState(True, "cool", 22.0, swing_h="swing"), V3)
    assert command(sent[-1]) == "swing_h_auto"
    assert len(words(HvacState(True, "cool", 22.0, features={"light": True}), V3)) == 6


def test_encode_is_one_burst_per_word():
    dev = device(V3)
    pulses = dev.encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert len(pulses) == 6 * (2 + 2 * 28 + 2)
    assert pulses[:2] == (3200, 9900)
    assert pulses[-2:] == (480, 108050)


def test_variant_argument_and_unknown_models():
    assert Lg2Device("lg", "whatever").variant == V1
    assert Lg2Device("lg", "whatever", variant=V3).variant == V3
    with pytest.raises(ValueError):
        Lg2Device("lg", "whatever", variant="GE6711AR2853M")


@pytest.mark.parametrize("model", LG2_MODELS)
def test_registry_serves_the_port(model):
    dev = registry.get_device("lg", model)
    assert isinstance(dev, Lg2Device)
    assert dev.variant == LG2_MODELS[model]


@pytest.mark.parametrize("model", LG2_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins import lg

    old = lg.PluginObject.MODELS[model]
    assert old.__name__ == LEGACY_CLASS[LG2_MODELS[model]]
    legacy = LegacyDevice("lg", model, old)
    assert Lg2Device("lg", model).capabilities == legacy.capabilities


def _record(variant, **state):
    return next(
        r
        for r in load_oracle("LG2")
        if variant_of(r) == variant
        and all(r["state"].get(k) == v for k, v in state.items())
    )


def test_undeclared_swing_highest_deviation_is_reported():
    record = _record(V2, mode="cool", swing="90°")
    with pytest.raises(AssertionError, match="command"):
        check(record, defects=())


def test_undeclared_vane_deviations_are_reported():
    for swing in ("90°", "60°"):
        record = _record(V3, mode="cool", swing=swing)
        with pytest.raises(AssertionError, match="vane0"):
            check(record, defects=())


def test_undeclared_swing_h_deviation_is_reported():
    record = _record(V3, hswing="on")
    with pytest.raises(AssertionError, match="swing_h"):
        check(record, defects=())


def test_undeclared_dropped_swing_word_is_reported():
    record = _record(V2, mode="cool", swing="60°")
    # The port sends one word more than C: C's pulses end a word early.
    with pytest.raises(DecodeError, match="end of signal"):
        check(record, drops=set())
    check(record)  # with C_DROPS declared it matches
