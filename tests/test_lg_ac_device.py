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
from pyhvac.ir.codec import decode
from pyhvac.plugins.lg import (
    LG_AC,
    LG_AC_GE_MODELS,
    LG_AC_LAYOUT,
    LG_AC_MODEL_VARIANT,
    LG_AC_MODELS,
    LG_AC_OFF_COMMAND,
    LG_AC_SWINGV_TOGGLE,
    LgAcDevice,
    lg_ac_word,
)
from pyhvac.state import HvacState

# The C path deviates from the documented LG6711A20083V behaviour here:
# - the old glue (IRGHVAC.trans_swing) has no "on" entry, so IRac keeps
#   swingv kOff, IRac::lg sees no off -> not-off change, and IRLgAc::send
#   sends no kLgAcSwingVToggle word. The port sends the documented toggle
#   word after the state word. The defect is a whole extra word, not a
#   field, so it is checked by assert_matches below rather than by a layout
#   field diff.
SWING_TOGGLE = Defect(
    "swing_toggle_word", "sent", "absent", "C glue has no 'on' swing: no toggle"
)
DEFECTS = (SWING_TOGGLE,)

TOGGLE = lg_ac_word(LG_AC_SWINGV_TOGGLE)
OFF = lg_ac_word(LG_AC_OFF_COMMAND)
MODEL = "6711A20083V  remote"
GE_MODEL = "AG1BH09AW101"
ALL_MODELS = LG_AC_MODELS + LG_AC_GE_MODELS
LEGACY = {"LG6711A20083V": ("lg", "LGv2"), "GE6711AR2853M": ("ge", "LGv1")}


def device(model=MODEL):
    return LgAcDevice("lg", model)


def words(state, previous=None, model=MODEL):
    dev = device(model)
    if previous is not None:
        previous = dev.normalise(previous)
    return [f.data for f in dev.frames(previous, dev.normalise(state), ())]


def read(state, previous=None):
    return LG_AC_LAYOUT.read(words(state, previous)[0])


class _StateWordOnly:
    """The device, minus the trailing swing toggle word."""

    def __init__(self, dev):
        self.dev = dev
        self.PROTOCOL = dev.PROTOCOL
        self.capabilities = dev.capabilities

    def normalise(self, state):
        return self.dev.normalise(state)

    def frames(self, previous, target, actions):
        return self.dev.frames(previous, target, actions)[:1]


def assert_matches(dev, record, defects=DEFECTS, previous=None):
    """assert_matches_oracle, with the swing toggle word accepted only when
    its Defect is declared (and only as exactly kLgAcSwingVToggle)."""
    ours = dev.frames(previous, state_from_record(dev, record["state"]), ())
    if len(ours) > 1:
        assert [f.data for f in ours[1:]] == [TOGGLE], record["state"]
        declared = {(d.field, d.ours, d.theirs) for d in defects}
        assert (
            SWING_TOGGLE.field,
            SWING_TOGGLE.ours,
            SWING_TOGGLE.theirs,
        ) in declared, f"undeclared swing toggle word for {record['state']}"
        dev = _StateWordOnly(dev)
    assert_matches_oracle(dev, record, (LG_AC_LAYOUT,), defects, previous=previous)


@pytest.mark.parametrize("record", oracle_params("LG"))
def test_matches_c_library(record):
    assert_matches(device(record["model"]), record)


@pytest.mark.parametrize("record, states", sequence_params("LG"))
def test_sequence_matches_a_persistent_c_object(record, states):
    # The swing toggle word depends on the message before, but the 0.1.7
    # glue never passes swing on (SWING_TOGGLE), so this cannot catch a
    # wrong toggle: it checks that nothing else depends on the message before.
    dev = device(record["model"])
    previous = None
    for rec in c_sequence(record, states):
        assert_matches(dev, rec, previous=previous)
        previous = state_from_record(dev, rec["state"])


def test_oracle_covers_both_variants():
    seen = {(r["plugin"], r["model"], r["class"]) for r in load_oracle("LG")}
    assert seen == {("lg", MODEL, "LGv2"), ("ge", GE_MODEL, "LGv1")}
    assert {LG_AC_MODEL_VARIANT[m] for _, m, _ in seen} == set(LEGACY)


@pytest.mark.parametrize("swing", ["off", "auto", "1", "2", "3", "4", "5"])
def test_ge_sends_no_swing_word(swing):
    # IRLgAc::send: GE6711AR2853M falls in the default case, no swing word,
    # with or without a previous state.
    target = HvacState(True, "cool", 22.0, swing_v=swing)
    plain = HvacState(True, "cool", 22.0)
    assert words(target, model=GE_MODEL) == words(plain, model=GE_MODEL)
    for before in ("off", "auto", "3"):
        previous = HvacState(True, "cool", 22.0, swing_v=before)
        assert len(words(target, previous, model=GE_MODEL)) == 1


@pytest.mark.parametrize("mode", ["auto", "cool", "fan", "dry", "heat"])
@pytest.mark.parametrize("fan", ["auto", "1", "2", "3", "4"])
def test_variants_share_the_state_word(mode, fan):
    state = HvacState(True, mode, 21.0, fan=fan)
    assert words(state, model=GE_MODEL) == words(state)
    off = HvacState(False, mode, 21.0, fan=fan)
    assert words(off, model=GE_MODEL) == words(off) == [OFF]


def test_layout_round_trips_every_oracle_state():
    for record in load_oracle("LG"):
        dev = device(record["model"])
        state = state_from_record(dev, record["state"])
        for word in dev.frames(None, state, ()):
            values = LG_AC_LAYOUT.read(word.data)
            assert LG_AC_LAYOUT.build(**values) == bytearray(word.data)


def test_every_oracle_word_has_the_nibble_checksum():
    for record in load_oracle("LG"):
        (word,) = decode(LG_AC, record["pulses"], expected=["main"])
        assert word.nbits == 28
        assert LG_AC_LAYOUT.checksum.check(word.data)
        assert word.data[3] & 0x0F == 0  # the 4 bits below the word


def test_checksum_nibble_overlaps_no_field():
    # Sum is raw bits 0-3: the top nibble of byte 3. Nothing else lives in
    # byte 3 (its low nibble is not sent).
    checksum = LG_AC_LAYOUT.checksum
    assert checksum.positions() == {3}
    for name, f in LG_AC_LAYOUT.fields.items():
        assert not {b // 8 for b in f.bits} & {3}, name
    covered = {b for f in LG_AC_LAYOUT.fields.values() for b in f.bits}
    assert covered == set(range(24))  # every other sent bit is a field


@pytest.mark.parametrize("raw, total", [(0x88C0051, 0x1), (0x88C0354, 0x4)])
def test_checksum_known_values(raw, total):
    # TestIRLgAcClass.calcChecksum.
    data = bytearray(lg_ac_word(raw))
    assert LG_AC_LAYOUT.checksum.compute(data) == total
    data[3] = 0
    LG_AC_LAYOUT.checksum.apply(data)
    assert data[3] >> 4 == total


@pytest.mark.parametrize("mode", ["auto", "cool", "fan", "dry", "heat"])
@pytest.mark.parametrize("temp", [16.0, 20.0, 25.0])
@pytest.mark.parametrize("swing", ["off", "swing"])
def test_off_is_the_off_command_in_every_mode(mode, temp, swing):
    # IRLgAc::send: power off always sends kLgAcOffCommand alone, whatever
    # the mode, setpoint, fan, swing or light.
    state = HvacState(
        False,
        mode,
        temp,
        fan="4",
        swing_v=swing,
        swing_h=swing,
        features={"light": True},
    )
    assert words(state) == [OFF]
    assert words(state, previous=HvacState(True, mode, temp)) == [OFF]


def test_off_command_is_the_struct_with_power_off():
    values = LG_AC_LAYOUT.read(OFF)
    assert values == {
        "sign": 0x88,
        "power": "off",
        "unused": 0,
        "mode": "cool",
        "temp": 0,
        "fan": "auto",
    }
    assert LG_AC_LAYOUT.checksum.check(OFF)


@pytest.mark.parametrize("temp", range(16, 26))
def test_every_setpoint(temp):
    # setTemp: Temp = celsius - kLgAcTempAdjust.
    values = read(HvacState(True, "cool", float(temp)))
    assert (values["temp"], values["power"], values["sign"]) == (temp - 15, "on", 0x88)


def test_setpoint_is_clamped_to_the_entity_range():
    # The legacy entity offers 16-25 °C (C itself would clamp to 16-30).
    assert read(HvacState(True, "cool", 10.0))["temp"] == 1
    assert read(HvacState(True, "heat", 35.0))["temp"] == 10


@pytest.mark.parametrize(
    "mode, raw", [("cool", 0), ("dry", 1), ("fan", 2), ("auto", 3), ("heat", 4)]
)
def test_every_mode(mode, raw):
    assert LG_AC_LAYOUT.read_raw(words(HvacState(True, mode, 22.0))[0], "mode") == raw


@pytest.mark.parametrize(
    "fan, raw",
    # high: convertFan's kLgAcFanHigh, which setFan stores as kLgAcFanMax
    # on LG6711A20083V (only AKB74955603 keeps kLgAcFanHigh).
    [("auto", 5), ("1", 0), ("2", 1), ("3", 2), ("4", 4)],
)
@pytest.mark.parametrize("mode", ["auto", "cool", "fan", "dry", "heat"])
def test_every_fan_level(mode, fan, raw):
    data = words(HvacState(True, mode, 22.0, fan=fan))[0]
    assert LG_AC_LAYOUT.read_raw(data, "fan") == raw


def test_light_and_swing_h_send_nothing():
    # IRLgAc::send sends the light toggle for AKB74955603 and SwingH words
    # for AKB73757604 only.
    base = HvacState(True, "cool", 22.0)
    for swing_h in ("off", "swing"):
        for light in (False, True):
            state = HvacState(
                True, "cool", 22.0, swing_h=swing_h, features={"light": light}
            )
            assert words(state) == words(base)


def test_swing_without_previous_sends_the_toggle_word():
    # A fresh IRac: sendAc's prev_swingv is kOff, so IRac::lg sends
    # kLgAcSwingVToggle when the target swing is on.
    on = words(HvacState(True, "cool", 22.0, swing_v="swing"))
    off = words(HvacState(True, "cool", 22.0))
    assert on == off + [TOGGLE]
    assert len(off) == 1


@pytest.mark.parametrize(
    "before, after, toggle",
    [
        ("off", "off", False),
        ("off", "swing", True),
        ("swing", "off", True),
        ("swing", "swing", False),
    ],
)
@pytest.mark.parametrize("was_on", [True, False])
def test_swing_with_previous_toggles_on_change(before, after, toggle, was_on):
    # IRac::lg: toggle when (swingv == kOff) != (swingv_prev == kOff); the
    # previous swing counts even if the previous message was an off.
    previous = HvacState(was_on, "cool", 22.0, swing_v=before)
    target = HvacState(True, "heat", 23.0, swing_v=after)
    sent = words(target, previous)
    assert sent[1:] == ([TOGGLE] if toggle else [])


def test_toggle_word_reads_through_the_layout():
    values = LG_AC_LAYOUT.read(TOGGLE)
    assert (values["sign"], values["unused"], values["power"]) == (0x88, 0b010, "on")
    assert LG_AC_LAYOUT.checksum.check(TOGGLE)


def test_previous_is_ignored_except_for_the_swing():
    dev = device()
    target = HvacState(True, "cool", 22.0, fan="2", swing_v="swing")
    for previous in (
        HvacState(False, "heat", 25.0, swing_v="swing"),
        HvacState(True, "dry", 16.0, fan="4", swing_v="swing"),
        target,
    ):
        assert dev.encode(previous, target).signal == dev.encode(target, target).signal


@pytest.mark.parametrize(
    "raw, mode, temp, fan",
    [
        (0x8800347, "cool", 18, "4"),  # issue 1008
        (0x8800459, "cool", 19, "auto"),  # issue 1008
        (0x8800A4E, "cool", 25, "4"),  # MessageConstruction
    ],
)
def test_known_examples(raw, mode, temp, fan):
    # TestIRLgAcClass: the words the port sends for these states.
    assert words(HvacState(True, mode, float(temp), fan=fan)) == [lg_ac_word(raw)]


@pytest.mark.parametrize(
    "raw, mode, temp, fan",
    [
        (0x880C152, "heat", 16, "auto"),
        (0x8808855, "cool", 23, "auto"),
        (0x880870F, "cool", 22, "1"),
        (0x8808721, "cool", 22, "3"),
        (0x8808743, "cool", 22, "4"),
        (0x8808754, "cool", 22, "auto"),
        (0x880A745, "fan", 22, "4"),
        (0x8808440, "cool", 19, "4"),
        (0x880960F, "dry", 21, "1"),
        (0x880C758, "heat", 22, "auto"),
        (0x8809946, "dry", 24, "4"),
        (0x880A341, "fan", 18, "4"),
    ],
)
def test_real_captures_except_the_unnamed_bit_15(raw, mode, temp, fan):
    # TestIRLgAcClass.KnownExamples (issue 1008 captures): the real remote
    # also sets raw bit 15, one of the struct's unnamed bits (the header
    # names no meaning for it). IRLgAc never sets it; neither does the port.
    (ours,) = words(HvacState(True, mode, float(temp), fan=fan))
    assert LG_AC_LAYOUT.read(ours)["unused"] == 0
    capture = bytearray(ours)
    LG_AC_LAYOUT.write_raw(capture, "unused", 0b001)
    LG_AC_LAYOUT.checksum.apply(capture)
    assert bytes(capture) == lg_ac_word(raw)


def test_real_capture_decodes():
    # TestDecodeLG.Issue620: a real remote's 0x8808721 (cool, 22 °C, fan
    # medium, bit 15 set) decodes with the port's timings.
    raw = (
        "8886 4152 560 1538 532 502 532 504 530 484 558 1536 508 516 558 502 "
        "532 484 558 502 532 500 534 508 532 502 532 1518 558 510 532 484 556 "
        "486 556 510 532 1518 558 1560 532 1528 556 504 530 506 530 1520 558 "
        "508 534 500 532 512 530 484 556 1536 532"
    )
    pulses = [int(x) for x in raw.split()] + [108050]
    (word,) = decode(LG_AC, pulses, expected=["main"])
    assert word.data == lg_ac_word(0x8808721)
    values = LG_AC_LAYOUT.read(word.data)
    assert (values["mode"], values["temp"] + 15, values["fan"]) == ("cool", 22, "3")


def test_message_shape():
    dev = device()
    signal = dev.encode(None, HvacState(True, "cool", 22.0)).signal
    assert signal.carrier == 38000
    assert signal.pulses[:2] == (8500, 4250)
    assert signal.pulses[-2:] == (550, 108050)
    assert len(signal.pulses) == 2 + 2 * 28 + 2
    swing = dev.encode(None, HvacState(True, "cool", 22.0, swing_v="swing")).signal
    assert len(swing.pulses) == 2 * (2 + 2 * 28 + 2)
    assert swing.pulses[60:62] == (8500, 4250)


@pytest.mark.parametrize(
    "model, variant",
    [(m, "LG6711A20083V") for m in LG_AC_MODELS]
    + [(m, "GE6711AR2853M") for m in LG_AC_GE_MODELS],
)
def test_variant_comes_from_the_model(model, variant):
    assert LG_AC_MODEL_VARIANT[model] == variant
    assert device(model).variant == variant


def test_unknown_model_gets_lg6711a20083v_and_bad_variant_raises():
    assert LgAcDevice("lg", "whatever").variant == "LG6711A20083V"
    assert LgAcDevice("lg", "whatever", variant="GE6711AR2853M").variant == (
        "GE6711AR2853M"
    )
    with pytest.raises(ValueError):
        LgAcDevice("lg", "whatever", variant="AKB75215403")


@pytest.mark.parametrize(
    "brand, model",
    [("lg", m) for m in LG_AC_MODELS] + [("ge", m) for m in LG_AC_GE_MODELS],
)
def test_registry_serves_the_port(brand, model):
    dev = registry.get_device(brand, model)
    assert isinstance(dev, LgAcDevice)
    assert dev.variant == LG_AC_MODEL_VARIANT[model]


@pytest.mark.parametrize("model", ALL_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins import lg

    brand, cls = LEGACY[LG_AC_MODEL_VARIANT[model]]
    legacy = LegacyDevice(brand, model, getattr(lg, cls))
    assert LgAcDevice(brand, model).capabilities == legacy.capabilities


def test_ge_capabilities_offer_the_legacy_swing_positions():
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.lg import LGv1

    swing = LegacyDevice("ge", GE_MODEL, LGv1).capabilities.swing_v
    assert swing.values == ("off", "auto", "1", "2", "3", "4", "5")
    assert device(GE_MODEL).capabilities.swing_v == swing


def test_undeclared_deviation_is_reported():
    record = next(
        r
        for r in load_oracle("LG")
        if r["class"] == "LGv2"
        and r["state"].get("swing") == "on"
        and r["state"]["mode"] != "off"
    )
    with pytest.raises(AssertionError, match="swing toggle"):
        assert_matches(device(), record, defects=())


def test_toggle_word_is_not_silently_dropped_by_the_plain_helper():
    # Without the _StateWordOnly view, the C pulses hold one word, not two.
    record = next(
        r
        for r in load_oracle("LG")
        if r["class"] == "LGv2"
        and r["state"].get("swing") == "on"
        and r["state"]["mode"] != "off"
    )
    with pytest.raises(Exception):
        assert_matches_oracle(device(), record, (LG_AC_LAYOUT,) * 2, DEFECTS)
