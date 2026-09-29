import pytest

from c_oracle import c_encode

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
from pyhvac.plugins.transcold import (
    TRANSCOLD,
    TRANSCOLD_KNOWN_GOOD_STATE,
    TRANSCOLD_LAYOUT,
    TRANSCOLD_MODELS,
    TRANSCOLD_OFF,
    TRANSCOLD_SWING,
    TranscoldDevice,
    transcold_word,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Transcold values here:
# - fan mode: the header documents it as Dry with Temp kTranscoldFanTempCode
#   (IRTranscoldAc::setMode writes both, and kTranscoldFan's fan auto,
#   kTranscoldFanAuto). IRac::transcold then calls setTemp(degrees), which
#   overwrites the temp code, so C sends dry mode at the setpoint, and
#   setFan (seeing dry) turns fan auto into kTranscoldFanAuto0. The oracle
#   holds 17 C (sent as 18 C), 23 C and 30 C;
# - the old glue (IRGHVAC.trans_swing) has no "on" entry, so IRac keeps
#   swingv kOff and IRac::transcold never sends kTranscoldSwing. The port
#   sends the documented toggle word before the state word. The defect is a
#   whole extra word, not a field, so assert_matches below checks it rather
#   than a layout field diff.
# SWING_TOGGLE (and _StateWordOnly, test_undeclared_swing_deviation_is_reported
# and test_toggle_word_is_not_silently_dropped_by_the_plain_helper, which
# serve it) exists only because the oracle was recorded through the 0.1.7
# Python glue. Remove them when the fixtures are regenerated from a C path
# with main's glue fixes (test_swing_matches_c_with_the_glue_fixed shows C
# then sends the toggle word too).
FAN_MODE_DEFECTS = (
    Defect("temp", "fan", 18, "IRac::transcold's setTemp overwrites fan mode"),
    Defect("temp", "fan", 23, "IRac::transcold's setTemp overwrites fan mode"),
    Defect("temp", "fan", 30, "IRac::transcold's setTemp overwrites fan mode"),
    Defect("fan", "auto", "auto0", "C's fan mode reads as dry in setFan"),
)
SWING_TOGGLE = Defect(
    "swing_toggle_word", "sent", "absent", "C glue has no 'on' swing: no toggle"
)
DEFECTS = FAN_MODE_DEFECTS + (SWING_TOGGLE,)

SWING = transcold_word(TRANSCOLD_SWING)
OFF = transcold_word(TRANSCOLD_OFF)


def device(model="generic"):
    return TranscoldDevice("transcold", model)


def state(power=True, mode="cool", temperature=22.0, **kw):
    return device().normalise(HvacState(power, mode, temperature, **kw))


def words(target, previous=None):
    return [f.data for f in device().frames(previous, target, ())]


def read(target, previous=None):
    return TRANSCOLD_LAYOUT.read(words(target, previous)[-1])


class _StateWordOnly:
    """The device, minus the leading swing toggle word.

    A 0.1.7-glue artifact (see SWING_TOGGLE): remove it when the fixtures
    are regenerated with swing "on" passed through to C."""

    def __init__(self, dev):
        self.dev = dev
        self.PROTOCOL = dev.PROTOCOL
        self.LAYOUTS = dev.LAYOUTS
        self.capabilities = dev.capabilities

    def normalise(self, state):
        return self.dev.normalise(state)

    def frames(self, previous, target, actions):
        return self.dev.frames(previous, target, actions)[-1:]


def assert_matches(dev, record, defects=DEFECTS, previous=None):
    """assert_matches_oracle, with the swing toggle word accepted only when
    its Defect is declared (and only as exactly kTranscoldSwing)."""
    ours = dev.frames(previous, state_from_record(dev, record["state"]), ())
    if len(ours) > 1:
        assert [f.data for f in ours[:-1]] == [SWING], record["state"]
        declared = {(d.field, d.ours, d.theirs) for d in defects}
        assert (
            SWING_TOGGLE.field,
            SWING_TOGGLE.ours,
            SWING_TOGGLE.theirs,
        ) in declared, f"undeclared swing toggle word for {record['state']}"
        dev = _StateWordOnly(dev)
    assert_matches_oracle(dev, record, dev.LAYOUTS, defects, previous=previous)


@pytest.mark.parametrize("record", oracle_params("TRANSCOLD"))
def test_matches_c_library(record):
    assert_matches(device(record["model"]), record)


@pytest.mark.parametrize("record, states", sequence_params("TRANSCOLD"))
def test_sequence_matches_a_persistent_c_object(record, states):
    # The swing toggle word depends on the message before, but the 0.1.7
    # glue never passes swing on (SWING_TOGGLE), so this cannot catch a
    # wrong toggle: it checks that nothing else depends on the message
    # before. test_swing_matches_c_with_the_glue_fixed checks the toggle.
    dev = device(record["model"])
    previous = None
    for rec in c_sequence(record, states):
        assert_matches(dev, rec, previous=previous)
        previous = state_from_record(dev, rec["state"])


def test_layout_round_trips_every_oracle_state():
    # The state word; the command words are fixed constants.
    dev = device()
    for record in load_oracle("TRANSCOLD"):
        data = words(state_from_record(dev, record["state"]))[-1]
        values = TRANSCOLD_LAYOUT.read(data)
        assert TRANSCOLD_LAYOUT.build(**values) == bytearray(data)


def test_every_oracle_word_is_sent_with_its_complements():
    dev = device()
    for record in load_oracle("TRANSCOLD"):
        (frame,) = decode(TRANSCOLD, record["pulses"], expected=["main"])
        assert TRANSCOLD_LAYOUT.checksum.check(frame.data)


def test_word_bytes_are_msb_first_each_followed_by_its_complement():
    assert transcold_word(0xE96554) == bytes.fromhex("e916659a54ab")


# ------------------------------------------------------------ real captures


def test_port_reproduces_the_synthetic_example_pulses():
    # ir_Transcold_test.cpp SyntheticExample: sendTranscold(0xE96554), the
    # RealExample state (cool, 22 C, fan min).
    expected = (
        [5944, 7563]
        + [
            p
            for bit in f"{0xE916659A54AB:048b}"
            for p in (555, 3556 if bit == "1" else 1526)
        ]
        + [555, 7563, 555, 100000]
    )
    signal = device().encode(None, HvacState(True, "cool", 22.0, fan="1")).signal
    assert signal.carrier == 38000
    assert list(signal.pulses) == expected


def test_real_capture_decodes_to_the_port_frame():
    # ir_Transcold_test.cpp RealExample (issue 1256): 0xE96554, "Mode: 6
    # (Cool), Fan: 9 (Min), Temp: 22C". The capture ends on its last mark.
    raw = [
        5944, 7612,
        558, 3556, 556, 3556, 556, 3556, 556, 1526, 554, 3556, 556, 1528,
        554, 1526, 556, 3558, 554, 1524, 556, 1528, 556, 1526, 556, 3556,
        554, 1528, 556, 3556, 554, 3556, 556, 1528, 554, 1526, 556, 3556,
        556, 3556, 554, 1528, 554, 1526, 554, 3558, 554, 1528, 554, 3556,
        556, 3556, 556, 1526, 554, 1526, 556, 3556, 554, 3556, 554, 1526,
        554, 3556, 556, 1526, 556, 1526, 554, 3558, 554, 1526, 556, 3556,
        556, 1526, 556, 3554, 556, 1524, 556, 1526, 556, 3556, 556, 1526,
        554, 3556, 556, 1524, 558, 3556, 554, 1526, 556, 3556, 554, 3556,
        556, 7514,
        556,
    ]  # fmt: skip
    (frame,) = decode(TRANSCOLD, raw + [100000], expected=["main"])
    assert frame.data == transcold_word(0xE96554)
    assert words(state(True, "cool", 22.0, fan="1")) == [frame.data]
    values = TRANSCOLD_LAYOUT.read(frame.data)
    assert (values["mode"], values["temp"], values["fan"]) == ("cool", 22, "1")


def test_port_reproduces_the_build_known_state_capture():
    # ir_Transcold_test.cpp BuildKnownState: 0xEF6B54, "temp down, 19,
    # Auto, cool" from the protocol's capture sheet.
    assert words(state(True, "cool", 19.0)) == [transcold_word(0xEF6B54)]


def test_known_good_state_is_the_skeleton():
    # stateReset loads kTranscoldKnownGoodState: cool, 22 C, fan min.
    assert TRANSCOLD_LAYOUT.skeleton == transcold_word(TRANSCOLD_KNOWN_GOOD_STATE)
    values = TRANSCOLD_LAYOUT.read(TRANSCOLD_LAYOUT.skeleton)
    assert values == {"fan": "1", "temp": 22, "mode": "cool"}


def test_command_words_read_through_the_layout():
    # kTranscoldOff and kTranscoldSwing are fixed words with valid
    # complements. Off's mode nibble (7) and swing's fan nibble (7) are no
    # state value.
    assert TRANSCOLD_LAYOUT.checksum.check(OFF)
    assert TRANSCOLD_LAYOUT.checksum.check(SWING)
    assert TRANSCOLD_LAYOUT.read(OFF) == {"fan": "auto", "temp": 23, "mode": 7}
    assert TRANSCOLD_LAYOUT.read(SWING) == {"fan": 7, "temp": 24, "mode": "cool"}


# ------------------------------------------------------------------- rules


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan", "heat"])
@pytest.mark.parametrize("temperature", [17.0, 24.0, 30.0])
@pytest.mark.parametrize("fan", ["auto", "1", "2", "3"])
@pytest.mark.parametrize("swing", ["off", "swing"])
def test_off_is_the_off_command_alone(mode, temperature, fan, swing):
    # IRac::transcold: setPower(false), send() and return: kTranscoldOff,
    # whatever the mode, setpoint, fan or swing (and no swing toggle).
    target = state(False, mode, temperature, fan=fan, swing_v=swing)
    assert words(target) == [OFF]
    for before in ("off", "swing"):
        assert words(target, state(True, "cool", 22.0, swing_v=before)) == [OFF]


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat"])
@pytest.mark.parametrize("t", range(18, 31))
def test_every_setpoint(mode, t):
    # setTemp: (celsius - 17), inverted and bit-reversed in 4 bits.
    raw = int(f"{~(t - 17) & 0xF:04b}"[::-1], 2)
    data = words(state(True, mode, float(t)))[0]
    assert TRANSCOLD_LAYOUT.read_raw(data, "temp") == raw
    assert read(state(True, mode, float(t)))["temp"] == t


def test_setpoint_range_is_the_headers():
    # kTranscoldTempMin = 18, kTranscoldTempMax = 30 (the legacy entity
    # offered 17, which setTemp sent as 18).
    rng = device().capabilities.temperature
    assert (rng.min, rng.max, rng.decimals) == (18.0, 30.0, (0,))


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat"])
def test_setpoint_17_is_clamped_to_kTranscoldTempMin(mode):
    # A 17 C request (the oracle's) normalises to kTranscoldTempMin (18 C),
    # what setTemp sent for it.
    assert state(True, mode, 17.0).temperature == 18.0
    assert words(state(True, mode, 17.0)) == words(state(True, mode, 18.0))


@pytest.mark.parametrize(
    "mode, raw",
    [("auto", 0b1110), ("cool", 0b0110), ("dry", 0b1100), ("heat", 0b1010)],
)
def test_every_mode(mode, raw):
    data = words(state(True, mode))[0]
    assert TRANSCOLD_LAYOUT.read_raw(data, "mode") == raw


@pytest.mark.parametrize("t", [17.0, 22.0, 30.0])
def test_fan_mode_is_dry_with_the_fan_temp_code(t):
    # The header: kTranscoldFanTempCode "Part of Fan Mode"; setMode: "Fan
    # mode is a special case of Dry". Declared as a Defect (FAN_MODE_DEFECTS).
    data = words(state(True, "fan", t))[0]
    assert TRANSCOLD_LAYOUT.read_raw(data, "mode") == 0b1100
    assert TRANSCOLD_LAYOUT.read_raw(data, "temp") == 0b1111


@pytest.mark.parametrize(
    "mode, raw",
    [
        ("auto", 0b0110),  # kTranscoldFanAuto0
        ("dry", 0b0110),
        ("cool", 0b1111),  # kTranscoldFanAuto
        ("heat", 0b1111),
        ("fan", 0b1111),  # setMode(kTranscoldFan)'s value (a Defect)
    ],
)
def test_fan_auto_follows_the_mode(mode, raw):
    # IRTranscoldAc::setFan: "Dry & Auto mode can't have speed Auto".
    data = words(state(True, mode, fan="auto"))[0]
    assert TRANSCOLD_LAYOUT.read_raw(data, "fan") == raw


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan", "heat"])
@pytest.mark.parametrize("fan, raw", [("1", 0b1001), ("2", 0b1101), ("3", 0b1011)])
def test_every_fan_level(mode, fan, raw):
    # convertFan: kLow -> kTranscoldFanMin, kMedium -> Med, kHigh -> Max.
    data = words(state(True, mode, fan=fan))[0]
    assert TRANSCOLD_LAYOUT.read_raw(data, "fan") == raw


def test_swing_without_previous_sends_the_toggle_word_first():
    # A fresh IRac: handleToggles does nothing (previous protocol UNKNOWN),
    # so IRac::transcold sends kTranscoldSwing, then the state word.
    on = words(state(True, "cool", 22.0, swing_v="swing"))
    off = words(state(True, "cool", 22.0))
    assert on == [SWING] + off
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
    # IRac::handleToggles' TRANSCOLD rule: swingv kAuto when (swingv == kOff)
    # changed from the previous state, kOff otherwise; the previous swing
    # counts even if the previous message was an off.
    previous = state(was_on, "cool", 22.0, swing_v=before)
    target = state(True, "heat", 23.0, swing_v=after)
    sent = words(target, previous)
    assert sent[:-1] == ([SWING] if toggle else [])
    assert sent[-1] == words(state(True, "heat", 23.0))[0]


def test_previous_is_ignored_except_for_the_swing():
    target = state(True, "cool", 22.0, fan="2", swing_v="swing")
    for previous in (
        state(False, "heat", 25.0, swing_v="swing"),
        state(True, "dry", 18.0, fan="3", swing_v="swing"),
        target,
    ):
        assert words(target, previous) == words(target)[1:]


def test_message_shape():
    dev = device()
    one = dev.encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert len(one) == 2 + 2 * 48 + 4
    assert one[:2] == (5944, 7563)
    assert one[-4:] == (555, 7563, 555, 100000)
    two = dev.encode(None, HvacState(True, "cool", 22.0, swing_v="swing")).signal
    assert len(two.pulses) == 2 * len(one)
    assert two.pulses[len(one) :] == one


# ------------------------------------------------------------ registration


@pytest.mark.parametrize("model", TRANSCOLD_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("transcold", model), TranscoldDevice)


# ------------------------------------------------------ the C swing toggle


def _c_words(pulses):
    return [
        f.data
        for f in decode(TRANSCOLD, pulses, expected=["main"] * (len(pulses) // 102))
    ]


def test_swing_matches_c_with_the_glue_fixed():
    # With swing "on" reaching C (glue="fixed"), a fresh and a persistent IRac send exactly
    # what the port sends: the toggle word when the swing changes (with
    # previous) or is on (without), never with an off.
    dev = device()
    for power in (True, False):
        for swing in ("off", "swing"):
            target = state(power, "cool", 22.0, fan="2", swing_v=swing)
            pulses = c_encode("transcold", "generic", "Transcold", target, glue="fixed")
            assert words(target) == _c_words(pulses)
    walk = [
        (True, "off"),
        (True, "on"),
        (True, "on"),
        (False, "on"),
        (True, "on"),
        (False, "off"),
        (True, "on"),
        (True, "off"),
        (True, "off"),
        (False, "off"),
        (True, "off"),
    ]
    old = [
        {
            "mode": "heat" if power else "off",
            "temperature": 23,
            "fan": "low",
            "swing": swing,
        }
        for power, swing in walk + walk[::-1]
    ]
    record = load_oracle("TRANSCOLD")[0]
    previous = None
    for rec in c_sequence(record, old, glue="fixed"):
        target = state_from_record(dev, rec["state"])
        assert words(target, previous) == _c_words(rec["pulses"]), rec["state"]
        previous = target


# ------------------------------------------------------ declared deviations


@pytest.mark.parametrize("temperature", [17, 23, 30])
def test_undeclared_fan_mode_deviation_is_reported(temperature):
    record = next(
        r
        for r in load_oracle("TRANSCOLD")
        if r["state"]["mode"] == "fan"
        and r["state"]["temperature"] == temperature
        and r["state"]["swing"] == "off"
    )
    defects = [d for d in DEFECTS if d.field != "temp"]
    with pytest.raises(AssertionError, match="temp"):
        assert_matches(device(), record, defects=defects)


def test_undeclared_fan_mode_auto_deviation_is_reported():
    record = next(
        r
        for r in load_oracle("TRANSCOLD")
        if r["state"]["mode"] == "fan"
        and r["state"]["fan"] == "auto"
        and r["state"]["swing"] == "off"
    )
    defects = [d for d in DEFECTS if d.field != "fan"]
    with pytest.raises(AssertionError, match="fan"):
        assert_matches(device(), record, defects=defects)


def test_undeclared_swing_deviation_is_reported():
    record = next(
        r
        for r in load_oracle("TRANSCOLD")
        if r["state"]["mode"] == "cool" and r["state"]["swing"] == "on"
    )
    with pytest.raises(AssertionError, match="swing toggle"):
        assert_matches(device(), record, defects=FAN_MODE_DEFECTS)


def test_toggle_word_is_not_silently_dropped_by_the_plain_helper():
    # Without the _StateWordOnly view, the C pulses hold one word, not two.
    record = next(
        r
        for r in load_oracle("TRANSCOLD")
        if r["state"]["mode"] == "cool" and r["state"]["swing"] == "on"
    )
    with pytest.raises(Exception):
        assert_matches_oracle(device(), record, (TRANSCOLD_LAYOUT,) * 2, DEFECTS)


def test_other_modes_need_no_fan_mode_defect():
    for record in load_oracle("TRANSCOLD"):
        if record["state"]["mode"] != "fan":
            assert_matches(device(), record, defects=(SWING_TOGGLE,))
