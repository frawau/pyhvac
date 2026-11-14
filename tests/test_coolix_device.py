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
from pyhvac.ir.codec import decode
from pyhvac.protocols.coolix import (
    COOLIX,
    COOLIX_AIRWELL_MODELS,
    COOLIX_BEKO_MODELS,
    COOLIX_BOSCH_MODELS,
    COOLIX_CLEAN,
    COOLIX_DEFAULT_STATE,
    COOLIX_KASTRON_MODELS,
    COOLIX_KAYSUN_MODELS,
    COOLIX_LAYOUT,
    COOLIX_LED,
    COOLIX_MIDEA_MODELS,
    COOLIX_MODELS,
    COOLIX_OFF,
    COOLIX_SWING,
    COOLIX_TOKIO_MODELS,
    COOLIX_TOSHIBA_MODELS,
    COOLIX_TURBO,
    CoolixDevice,
    coolix_word,
)
from pyhvac.state import HvacState

SERVED = [
    ("coolix", COOLIX_MODELS),
    ("airwell", COOLIX_AIRWELL_MODELS),
    ("beko", COOLIX_BEKO_MODELS),
    ("bosch", COOLIX_BOSCH_MODELS),
    ("kastron", COOLIX_KASTRON_MODELS),
    ("kaysun", COOLIX_KAYSUN_MODELS),
    ("midea", COOLIX_MIDEA_MODELS),
    ("tokio", COOLIX_TOKIO_MODELS),
    ("toshiba", COOLIX_TOSHIBA_MODELS),
]
MODELS = [(plugin, model) for plugin, models in SERVED for model in models]

# The C path deviates from the documented Coolix messages here: the old glue
# (IRGHVAC.trans_swing / trans_hswing) has no "on" entry, so IRac keeps
# swingv and swingh kOff and IRac::coolix never sends kCoolixSwing. The port
# sends the documented toggle word after the state word. The defect is a
# whole extra word, not a field, so assert_matches below checks it rather
# than a layout field diff.
# SWING_TOGGLE (and _WithoutSwingWord and the tests that serve it) exists
# only because the oracle was recorded through the 0.1.7 Python glue.
# Remove them when the fixtures are regenerated from a C path with main's
# glue fixes (test_matches_c_with_the_glue_fixed shows C then sends the
# toggle word too).
SWING_TOGGLE = Defect(
    "swing_toggle_word", "sent", "absent", "C glue has no 'on' swing: no toggle"
)
DEFECTS = (SWING_TOGGLE,)

OFF = coolix_word(COOLIX_OFF)
SWING = coolix_word(COOLIX_SWING)
TURBO = coolix_word(COOLIX_TURBO)
LED = coolix_word(COOLIX_LED)
CLEAN = coolix_word(COOLIX_CLEAN)


def wire(record):
    """``record`` with the pulses the C library puts on the wire.

    sendCOOLIX ends each word with space(kCoolixMinGap) then
    space(kDefaultMessageGap). IRac's timing log keeps them as two entries;
    IRremoteESP8266's own SendWithRepeats test shows them merged
    ("m552s105244").
    """
    out, pulses, i = [], record["pulses"], 0
    while i < len(pulses):
        if pulses[i : i + 2] == [5244, 100000]:
            out.append(5244 + 100000)
            i += 2
        else:
            out.append(pulses[i])
            i += 1
    assert len(out) % 2 == 0
    return {**record, "pulses": out}


def device(plugin="coolix", model="generic"):
    return CoolixDevice(plugin, model)


def state(power=True, mode="cool", temperature=22.0, **kw):
    return device().normalise(HvacState(power, mode, temperature, **kw))


def frames(target, previous=None):
    return device().frames(previous, target, ())


def words(target, previous=None):
    """The words of a message; each frame pair is a word and its repeat."""
    sent = frames(target, previous)
    assert [f.section for f in sent] == ["main", "repeat"] * (len(sent) // 2)
    for a, b in zip(sent[::2], sent[1::2]):
        assert a.data == b.data
    return [f.data for f in sent[::2]]


def read(target, previous=None):
    return COOLIX_LAYOUT.read(words(target, previous)[0])


def layouts(sent):
    return (COOLIX_LAYOUT,) * len(sent)


def c_words(pulses):
    pulses = list(pulses)
    if pulses[-2:-1] == [100000]:
        # LegacyDevice.encode's TRAILER_GAP, after the timing log's separate
        # kDefaultMessageGap (see wire).
        pulses.pop()
    pulses = wire({"pulses": pulses})["pulses"]
    n = pulses.count(4692) // 2
    sent = decode(COOLIX, pulses, expected=["main", "repeat"] * n)
    return [f.data for f in sent[::2]]


class _WithoutSwingWord:
    """The device, minus the swing toggle word.

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
        sent = self.dev.frames(previous, target, actions)
        return [f for f in sent if f.data != SWING]


def assert_matches(dev, record, defects=DEFECTS, previous=None):
    """assert_matches_oracle, with the swing toggle word accepted only when
    its Defect is declared (and only as exactly kCoolixSwing, right after
    the state word)."""
    record = wire(record)
    ours = dev.frames(previous, state_from_record(dev, record["state"]), ())
    if any(f.data == SWING for f in ours):
        assert [f.data for f in ours[2:4]] == [SWING, SWING], record["state"]
        declared = {(d.field, d.ours, d.theirs) for d in defects}
        assert (
            SWING_TOGGLE.field,
            SWING_TOGGLE.ours,
            SWING_TOGGLE.theirs,
        ) in declared, f"undeclared swing toggle word for {record['state']}"
        dev = _WithoutSwingWord(dev)
    assert_matches_oracle(dev, record, layouts, defects, previous=previous)


@pytest.mark.parametrize("record", oracle_params("COOLIX"))
def test_matches_c_library(record):
    assert_matches(device(record["plugin"], record["model"]), record)


@pytest.mark.parametrize("record, states", sequence_params("COOLIX"))
def test_sequence_matches_a_persistent_c_object(record, states):
    # The turbo, light and clean words depend on the message before
    # (IRac::handleToggles' COOLIX rule): the grid's single-feature states
    # switch them on and off in turn. The 0.1.7 glue never passes swing on
    # (SWING_TOGGLE); test_swing_toggle_matches_a_persistent_c_object checks
    # the swing toggle with the glue fixed.
    dev = device(record["plugin"], record["model"])
    previous = None
    for rec in c_sequence(record, states):
        assert_matches(dev, rec, previous=previous)
        previous = state_from_record(dev, rec["state"])


def test_layout_round_trips_every_oracle_state():
    # The state word; the command words are fixed constants.
    dev = device()
    for record in load_oracle("COOLIX"):
        target = state_from_record(dev, record["state"])
        if target.power:
            data = words(target)[0]
            values = COOLIX_LAYOUT.read(data)
            assert COOLIX_LAYOUT.build(**values) == bytearray(data)


def test_every_oracle_word_is_sent_with_its_complements():
    for record in load_oracle("COOLIX"):
        for data in c_words(record["pulses"]):
            assert COOLIX_LAYOUT.checksum.check(data)


def test_word_bytes_are_msb_first_each_followed_by_its_complement():
    assert coolix_word(0xB21FC8) == bytes.fromhex("b24d1fe0c837")


def test_default_state_is_the_skeleton():
    # stateReset loads kCoolixDefaultState: auto, 25 C, fan auto0, sensor
    # temperature ignored, zone follow off.
    assert COOLIX_LAYOUT.skeleton == coolix_word(COOLIX_DEFAULT_STATE)
    assert COOLIX_LAYOUT.read(COOLIX_LAYOUT.skeleton) == {
        "zone_follow2": 0,
        "sensor_temp": 0b11111,
        "fan": "auto0",
        "zone_follow1": 0,
        "mode": "auto",
        "temp": 25,
    }


def test_command_words_have_valid_complements():
    for word in (OFF, SWING, TURBO, LED, CLEAN):
        assert COOLIX_LAYOUT.checksum.check(word)


# ------------------------------------------------------------ real captures


ISSUE_579_OFF = [
    4444, 4434, 590, 1578, 698,  446,  590, 1578, 622, 1596, 622, 500,
    644,  476,  644, 1548, 588,  532,  594, 530,  612, 1578, 590, 532,
    588,  534,  672, 1518, 594,  1598, 590, 510,  612, 1580, 644, 480,
    612,  1578, 644, 1548, 644,  1548, 594, 1598, 642, 506,  644, 1550,
    644,  1548, 594, 1600, 644,  478,  644, 478,  642, 480,  644, 478,
    642,  1548, 594, 530,  590,  532,  614, 1578, 644, 1548, 594, 1600,
    588,  534,  566, 556,  588,  530,  590, 532,  586, 514,  612, 532,
    588,  532,  590, 534,  588,  1578, 642, 1576, 642, 1550, 588, 1602,
    588,  1580, 642, 4712, 4546, 4406, 588, 1606, 642, 478,  644, 1550,
    590,  1604, 588, 534,  586,  532,  586, 1582, 642, 480,  642, 480,
    668,  1550, 642, 480,  642,  478,  642, 1552, 612, 1578, 586, 538,
    588,  1580, 674, 472,  590,  1602, 586, 1580, 618, 1576, 642, 1548,
    594,  530,  590, 1584, 608,  1578, 644, 1550, 642, 480,  642, 478,
    642,  480,  642, 480,  642,  1550, 590, 530,  592, 528,  592, 1602,
    642,  1548, 592, 1604, 586,  584,  642, 480,  640, 480,  640, 480,
    642,  480,  642, 480,  642,  480,  642, 480,  642, 1552, 590, 1604,
    588,  1578, 642, 1552, 640,  1550, 592,
]  # fmt: skip

ISSUE_1748_OFF = [
    4642, 4502, 514, 1706, 516, 624, 488, 1704, 514, 1702, 516, 624, 488, 624,
    488, 1702, 514, 626, 488, 620, 488, 1702, 490, 620, 512, 620, 488, 1728,
    488, 1704, 514, 624, 488, 1704, 514, 620, 488, 1702, 490, 1722, 488, 1724,
    514, 1728, 488, 600, 512, 1728, 490, 1706, 512, 1698, 488, 646, 486, 622,
    462, 646, 488, 624, 488, 1704, 514, 626, 488, 628, 460, 1724, 514, 1702,
    514, 1724, 462, 646, 488, 624, 488, 624, 488, 626, 486, 602, 488, 646,
    460, 648, 486, 626, 488, 1704, 486, 1724, 488, 1748, 488, 1704, 514, 1708,
    488, 5312, 4648, 4494, 488, 1704, 486, 646, 486, 1698, 512, 1700, 488,
    646, 462, 646, 486, 1728, 462, 648, 484, 622, 462, 1724, 510, 622, 488,
    626, 488, 1702, 514, 1728, 490, 626, 488, 1730, 462, 646, 488, 1704, 512,
    1724, 486, 1698, 514, 1728, 488, 626, 488, 1728, 488, 1704, 514, 1700,
    512, 620, 486, 620, 488, 620, 486, 626, 490, 1728, 488, 626, 488, 628,
    460, 1750, 488, 1728, 488, 1704, 488, 646, 488, 620, 488, 624, 488, 626,
    488, 626, 462, 646, 462, 644, 488, 626, 488, 1728, 490, 1704, 486, 1724,
    514, 1724, 488, 1728, 488,
]  # fmt: skip

# ir_Coolix_test.cpp Issue722: the raw data @mariusmotea supplied (in the
# comments), fan mode, fan max: 0xB23FE4.
ISSUE_722_FAN_MAX = [
    4434, 4376, 566, 1614, 592, 504, 566, 1618, 566, 1616, 568, 528, 564, 532,
    564, 1616, 568, 532, 566, 530, 566, 1620, 568, 528, 566, 530, 566, 1618,
    564, 1618, 566, 530, 564, 1624, 538, 560, 566, 530, 564, 1620, 566, 1618,
    566, 1618, 566, 1616, 566, 1616, 566, 1620, 568, 1620, 566, 1616, 566, 530,
    566, 530, 564, 530, 562, 532, 564, 530, 566, 530, 566, 1622, 566, 1616,
    540, 1642, 566, 528, 566, 530, 566, 1616, 566, 530, 566, 532, 564, 532,
    564, 530, 566, 530, 566, 1614, 566, 1616, 562, 532, 564, 1620, 566, 1618,
    538, 5254, 4432, 4364, 566, 1616, 568, 530, 564, 1620, 568, 1616, 564, 532,
    564, 530, 566, 1616, 566, 532, 564, 532, 566, 1620, 568, 528, 566, 530,
    566, 1616, 564, 1618, 566, 530, 566, 1622, 566, 532, 566, 528, 566, 1620,
    568, 1614, 566, 1618, 566, 1618, 566, 1614, 568, 1618, 566, 1622, 568, 1616,
    566, 530, 564, 530, 566, 530, 566, 528, 564, 530, 566, 532, 566, 1622,
    564, 1616, 566, 1616, 564, 532, 564, 530, 564, 1616, 564, 530, 564, 532,
    566, 530, 564, 530, 566, 528, 564, 1618, 564, 1618, 564, 532, 564, 1620,
    566, 1618, 562,
]  # fmt: skip


@pytest.mark.parametrize("raw", [ISSUE_579_OFF, ISSUE_1748_OFF], ids=["579", "1748"])
def test_real_off_captures_decode_to_the_port_off_message(raw):
    # ir_Coolix_test.cpp RealCaptureExample (issue 579) and Issue1748Example:
    # a remote's power off, kCoolixOff sent twice. The captures end on their
    # last mark. Issue 1748's zero spaces run up to 17 % long (with its
    # short marks), within decodeCOOLIX's 30 % (the protocol's tolerance).
    sent = decode(COOLIX, raw + [100000], expected=["main", "repeat"])
    assert sent == frames(state(False, "cool", 22.0))
    assert [f.data for f in sent] == [OFF, OFF]


def test_real_fan_mode_capture_decodes_to_the_port_frames():
    # ir_Coolix_test.cpp Issue722: "Raw data supplied by @mariusmotea",
    # 0xB23FE4: fan mode (Dry + kCoolixFanTempCode), fan max.
    sent = decode(COOLIX, ISSUE_722_FAN_MAX + [100000], expected=["main", "repeat"])
    assert [f.data for f in sent] == [coolix_word(0xB23FE4)] * 2
    assert sent == frames(state(True, "fan", 18.0, fan="3"))


@pytest.mark.parametrize(
    "mode, temperature, fan, raw",
    [
        # ir_Coolix_test.cpp Issue722
        ("auto", 17.0, "auto", 0xB21F08),
        ("auto", 18.0, "auto", 0xB21F18),
        ("cool", 18.0, "auto", 0xB2BF10),
        ("dry", 18.0, "auto", 0xB21F14),
        ("heat", 18.0, "auto", 0xB2BF1C),
        ("fan", 18.0, "auto", 0xB2BFE4),
        ("fan", 18.0, "1", 0xB29FE4),
        ("fan", 18.0, "2", 0xB25FE4),
        ("fan", 18.0, "3", 0xB23FE4),
        # ir_Coolix_test.cpp KnownExamples and Issue579FanAuto0
        ("cool", 17.0, "1", 0xB29F00),
        ("auto", 20.0, "auto", 0xB21F28),
        # ir_Coolix_test.cpp Issue2012
        ("auto", 26.0, "auto", 0xB21FD8),
        ("auto", 27.0, "auto", 0xB21F98),
        ("auto", 28.0, "auto", 0xB21F88),
    ],
)
def test_port_reproduces_the_documented_state_words(mode, temperature, fan, raw):
    assert words(state(True, mode, temperature, fan=fan)) == [coolix_word(raw)]


def test_port_reproduces_the_send_with_repeats_pulses():
    # ir_Coolix_test.cpp SendWithRepeats / Issue722: the word, its repeat
    # after kCoolixMinGap, and "m552s105244" at the end.
    bits = [
        p
        for bit in f"{int.from_bytes(coolix_word(0xB23FE4), 'big'):048b}"
        for p in (552, 1656 if bit == "1" else 552)
    ]
    expected = [4692, 4416] + bits + [552, 5244] + [4692, 4416] + bits + [552, 105244]
    signal = device().encode(None, HvacState(True, "fan", 18.0, fan="3")).signal
    assert signal.carrier == 38000
    assert list(signal.pulses) == expected


# ------------------------------------------------------------------- rules


@pytest.mark.parametrize("mode", ["cool", "dry", "auto", "heat", "fan"])
@pytest.mark.parametrize("temperature", [17.0, 24.0, 30.0])
@pytest.mark.parametrize("fan", ["auto", "1", "2", "3"])
@pytest.mark.parametrize("swing", ["off", "swing"])
@pytest.mark.parametrize("on", [False, True])
def test_off_is_the_off_command_alone(mode, temperature, fan, swing, on):
    # IRac::coolix: setPower(false), send() and return: kCoolixOff, whatever
    # the mode, setpoint, fan, swing or features (no toggle word).
    features = {k: on for k in ("powerful", "cleaning", "light")}
    target = state(
        False,
        mode,
        temperature,
        fan=fan,
        swing_v=swing,
        swing_h=swing,
        features=features,
    )
    assert words(target) == [OFF]
    before = state(True, "cool", 22.0, swing_v="swing", features={"light": True})
    assert words(target, before) == [OFF]


@pytest.mark.parametrize("mode", ["cool", "dry", "auto", "heat"])
@pytest.mark.parametrize(
    "t, raw",
    list(
        zip(
            range(17, 31),
            [0, 1, 3, 2, 6, 7, 5, 4, 12, 13, 9, 8, 10, 11],  # kCoolixTempMap
        )
    ),
)
def test_every_setpoint(mode, t, raw):
    data = words(state(True, mode, float(t)))[0]
    assert COOLIX_LAYOUT.read_raw(data, "temp") == raw
    assert read(state(True, mode, float(t)))["temp"] == t


@pytest.mark.parametrize(
    "mode, raw", [("cool", 0b00), ("dry", 0b01), ("auto", 0b10), ("heat", 0b11)]
)
def test_every_mode(mode, raw):
    assert COOLIX_LAYOUT.read_raw(words(state(True, mode))[0], "mode") == raw


@pytest.mark.parametrize("t", [17.0, 22.0, 30.0])
def test_fan_mode_is_dry_with_the_fan_temp_code(t):
    # kCoolixFanTempCode "Part of Fan Mode"; setMode: "Fan mode is a special
    # case of Dry". IRac::coolix sets the temperature before the mode, so
    # the code stays.
    data = words(state(True, "fan", t))[0]
    assert COOLIX_LAYOUT.read_raw(data, "mode") == 0b01
    assert COOLIX_LAYOUT.read_raw(data, "temp") == 0b1110


@pytest.mark.parametrize(
    "mode, raw",
    [
        ("auto", 0b000),  # kCoolixFanAuto0
        ("dry", 0b000),
        ("cool", 0b101),  # kCoolixFanAuto
        ("heat", 0b101),
        ("fan", 0b101),
    ],
)
def test_fan_auto_follows_the_mode(mode, raw):
    # IRCoolixAC::setFan: "Dry & Auto mode can't have this speed".
    data = words(state(True, mode, fan="auto"))[0]
    assert COOLIX_LAYOUT.read_raw(data, "fan") == raw


@pytest.mark.parametrize("mode", ["cool", "dry", "auto", "heat", "fan"])
@pytest.mark.parametrize("fan, raw", [("1", 0b100), ("2", 0b010), ("3", 0b001)])
def test_every_fan_level(mode, fan, raw):
    # convertFan: kLow -> kCoolixFanMin, kMedium -> Med, kHigh -> Max.
    data = words(state(True, mode, fan=fan))[0]
    assert COOLIX_LAYOUT.read_raw(data, "fan") == raw


@pytest.mark.parametrize("mode", ["cool", "dry", "auto", "heat", "fan"])
def test_sensor_temperature_is_ignored_and_zone_follow_off(mode):
    # IRac passes no sensor temperature and iFeel off: clearSensorTemp and
    # setZoneFollow(false).
    values = read(state(True, mode, fan="2"))
    assert values["sensor_temp"] == 0b11111
    assert values["zone_follow1"] == values["zone_follow2"] == 0


def test_quiet_is_not_offered():
    # IRac::coolix: "No Quiet setting available", and ir_Coolix.h has no
    # quiet word: the old quiet did nothing. A quiet passed anyway is
    # dropped by normalise.
    assert "quiet" not in CoolixDevice.capabilities.features
    plain = state(True, "cool", 22.0)
    quiet = state(True, "cool", 22.0, features={"quiet": True})
    assert quiet == plain
    assert words(quiet) == words(plain)


def test_capabilities_are_the_documented_ones():
    caps = CoolixDevice.capabilities
    assert caps.modes == ("cool", "dry", "auto", "heat", "fan")
    # kCoolixTempMin / kCoolixTempMax
    assert (caps.temperature.min, caps.temperature.max) == (17.0, 30.0)
    assert caps.fan.values == ("auto", "1", "2", "3")  # kCoolixFan{Min,Med,Max}
    assert caps.swing_v.values == caps.swing_h.values == ("off", "swing")
    assert set(caps.features) == {"powerful", "cleaning", "light"}


@pytest.mark.parametrize("swing_v", ["off", "swing"])
@pytest.mark.parametrize("swing_h", ["off", "swing"])
@pytest.mark.parametrize("powerful", [False, True])
@pytest.mark.parametrize("light", [False, True])
@pytest.mark.parametrize("cleaning", [False, True])
def test_without_previous_each_feature_on_sends_its_word(
    swing_v, swing_h, powerful, light, cleaning
):
    # A fresh IRac: handleToggles does nothing (previous protocol UNKNOWN),
    # so IRac::coolix sends the state word, then kCoolixSwing (swingv or
    # swingh not off), kCoolixTurbo, kCoolixLed and kCoolixClean for each
    # feature on, in that order.
    features = {"powerful": powerful, "light": light, "cleaning": cleaning}
    target = state(
        True, "heat", 25.0, swing_v=swing_v, swing_h=swing_h, features=features
    )
    expected = words(state(True, "heat", 25.0))
    if "swing" in (swing_v, swing_h):
        expected.append(SWING)
    expected += [
        w for w, on in ((TURBO, powerful), (LED, light), (CLEAN, cleaning)) if on
    ]
    assert words(target) == expected


@pytest.mark.parametrize(
    "feature, word", [("powerful", TURBO), ("light", LED), ("cleaning", CLEAN)]
)
@pytest.mark.parametrize("before", [False, True])
@pytest.mark.parametrize("after", [False, True])
@pytest.mark.parametrize("was_on", [True, False])
def test_with_previous_features_toggle_on_change(feature, word, before, after, was_on):
    # IRac::handleToggles' COOLIX rule: turbo, light and clean are the
    # desired value XOR the previous one; the previous value counts even if
    # the previous message was an off.
    previous = state(was_on, "cool", 22.0, features={feature: before})
    target = state(True, "heat", 23.0, features={feature: after})
    sent = words(target, previous)
    assert sent[0] == words(state(True, "heat", 23.0))[0]
    assert sent[1:] == ([word] if before != after else [])


@pytest.mark.parametrize(
    "before, after, toggle",
    [
        (("off", "off"), ("off", "off"), False),
        (("off", "off"), ("swing", "off"), True),
        (("swing", "off"), ("off", "off"), True),
        (("swing", "off"), ("swing", "off"), False),
        # The one swing word serves both axes: it toggles when "swinging"
        # (either axis on) changes, a deliberate deviation for swing_h
        # (handleToggles leaves swingh alone, so a persistent IRac sends
        # kCoolixSwing on every message while swing_h is on).
        (("off", "off"), ("off", "swing"), True),
        (("off", "swing"), ("off", "swing"), False),
        (("off", "swing"), ("off", "off"), True),
        (("swing", "off"), ("swing", "swing"), False),
        (("swing", "swing"), ("off", "swing"), False),
        (("swing", "swing"), ("off", "off"), True),
    ],
)
@pytest.mark.parametrize("was_on", [True, False])
def test_with_previous_swing_toggles_on_change(before, after, toggle, was_on):
    previous = state(was_on, "cool", 22.0, swing_v=before[0], swing_h=before[1])
    target = state(True, "heat", 23.0, swing_v=after[0], swing_h=after[1])
    sent = words(target, previous)
    assert sent[0] == words(state(True, "heat", 23.0))[0]
    assert sent[1:] == ([SWING] if toggle else [])


def test_previous_is_ignored_except_for_the_toggles():
    target = state(True, "cool", 22.0, fan="2", features={"light": True})
    for previous in (
        state(False, "heat", 25.0, features={"light": True}),
        state(True, "dry", 18.0, fan="3", features={"light": True}),
        target,
    ):
        assert words(target, previous) == words(state(True, "cool", 22.0, fan="2"))


def test_message_shape():
    dev = device()
    one = dev.encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert len(one) == 2 * (2 + 2 * 48 + 2)
    assert one[:2] == (4692, 4416)
    assert one[-2:] == (552, 105244)
    target = HvacState(True, "cool", 22.0, features={"light": True})
    two = dev.encode(None, target).signal.pulses
    assert len(two) == 2 * len(one)
    assert two[: len(one)] == one


# ------------------------------------------------------------ registration


# ------------------------------------------------------ the C swing toggle


def test_matches_c_with_the_glue_fixed():
    # With swing and swing_h "on" reaching C (glue="fixed"), a fresh IRac
    # sends exactly what the port sends without previous.
    for power in (True, False):
        for mode in ("cool", "dry", "auto", "heat", "fan"):
            for swing_v in ("off", "swing"):
                for swing_h in ("off", "swing"):
                    for on in (False, True):
                        features = {"powerful": on, "light": on, "cleaning": on}
                        target = state(
                            power,
                            mode,
                            24.0,
                            fan="2",
                            swing_v=swing_v,
                            swing_h=swing_h,
                            features=features,
                        )
                        c = c_words(
                            c_encode(
                                "coolix", "generic", "Coolix", target, glue="fixed"
                            )
                        )
                        assert words(target) == c, target


def test_swing_toggle_matches_a_persistent_c_object():
    # With the glue fixed, a persistent IRac applies handleToggles' COOLIX
    # rule: the swing word only when swing_v changes, never with an off.
    walk = [
        (True, "off", "off"),
        (True, "on", "on"),
        (True, "on", "on"),
        (False, "on", "off"),
        (True, "on", "on"),
        (False, "off", "on"),
        (True, "on", "off"),
        (True, "off", "on"),
        (True, "off", "off"),
        (False, "off", "on"),
        (True, "off", "off"),
    ]
    old = [
        {
            "mode": "heat" if power else "off",
            "temperature": 23,
            "fan": "low",
            "swing": swing,
            "light": light,
        }
        for power, swing, light in walk + walk[::-1]
    ]
    record = load_oracle("COOLIX")[0]
    dev = device()
    previous = None
    for rec in c_sequence(record, old, glue="fixed"):
        target = state_from_record(dev, rec["state"])
        assert words(target, previous) == c_words(rec["pulses"]), rec["state"]
        previous = target


def test_swing_h_toggle_deviates_from_a_persistent_c_object():
    # The deliberate deviation: a persistent IRac sends kCoolixSwing on
    # every message while swing_h is on (handleToggles leaves swingh alone);
    # the port sends it only when swinging changes.
    old = [{"mode": "cool", "temperature": 22, "hswing": "on"}] * 2
    record = load_oracle("COOLIX")[0]
    first, second = c_sequence(record, old, glue="fixed")
    target = state_from_record(device(), second["state"])
    assert c_words(second["pulses"]) == words(target, None)
    assert c_words(second["pulses"]) == words(target, target) + [SWING]


# ------------------------------------------------------ declared deviations


def _swing_on_records():
    return [
        r
        for r in load_oracle("COOLIX")
        if r["state"]["mode"] != "off"
        and "on" in (r["state"].get("swing"), r["state"].get("hswing"))
    ]


def test_undeclared_swing_deviation_is_reported():
    records = _swing_on_records()
    assert any("hswing" in r["state"] for r in records)
    for record in records:
        with pytest.raises(AssertionError, match="swing toggle"):
            assert_matches(device(), record, defects=())


def test_swing_word_is_not_silently_dropped_by_the_plain_helper():
    # Without the _WithoutSwingWord view, the C pulses hold one word, not two.
    record = wire(_swing_on_records()[0])
    with pytest.raises(Exception):
        assert_matches_oracle(device(), record, layouts, DEFECTS)


def test_other_records_need_no_defect():
    swinging = _swing_on_records()
    for record in load_oracle("COOLIX"):
        if record not in swinging:
            assert_matches(device(), record, defects=())


# No real capture in ir_Coolix_test.cpp needs it, but
# decodeCOOLIX matches the bits with _tolerance +
# kCoolixExtraTolerance (30 %) and no mark excess.
def test_decode_tolerance_is_the_c_decoders():
    assert (COOLIX.tolerance, COOLIX.mark_excess) == (0.30, 0)


# ---------------------------------------------------------------- variants
# Variants beyond IRremoteESP8266, from SmartIR captures (crowd-sourced:
# the labels are indicative, the words are what the remotes sent).


def variant_words(variant, target, previous=None):
    dev = CoolixDevice("Test", "unit", variant=variant)
    sent = dev.frames(previous, dev.normalise(target), ())
    return [f.data for f in sent[::2]]


def raw(word):
    return int.from_bytes(bytes(word[0::2]), "big")


@pytest.mark.parametrize(
    "mode, fan, captured",
    [  # SmartIR climate 1941/1943 (Electra), 16 °C
        ("heat", "auto", 0xB2BFEC),
        ("heat", "1", 0xB29FEC),
        ("heat", "2", 0xB25FEC),
        ("heat", "3", 0xB23FEC),
        ("cool", "auto", 0xB2BFE8),
        ("cool", "1", 0xB29FE8),
        ("cool", "2", 0xB25FE8),
        ("cool", "3", 0xB23FE8),
    ],
)
def test_16c_variant_sends_16_degrees_as_captured(mode, fan, captured):
    (word,) = variant_words("16C", HvacState(True, mode, 16.0, fan=fan))
    assert raw(word) == captured


def test_16c_variant_offers_16_to_30():
    caps = CoolixDevice("Test", "unit", variant="16C").capabilities
    assert (caps.temperature.min, caps.temperature.max) == (16.0, 30.0)


@pytest.mark.parametrize("mode", ["dry", "auto"])
def test_16c_variant_sends_17_where_no_capture_shows_16(mode):
    assert variant_words("16C", HvacState(True, mode, 16.0)) == variant_words(
        "16C", HvacState(True, mode, 17.0)
    )


@pytest.mark.parametrize("t", range(17, 31))
def test_16c_variant_sends_the_documented_words_from_17(t):
    for mode in ("cool", "heat", "dry", "auto", "fan"):
        target = HvacState(True, mode, float(t), fan="2")
        assert variant_words("16C", target) == variant_words(None, target)


def test_quiet_variant_offers_quiet_and_sends_its_word():
    # SmartIR climate 1740 (Kelvinator KSV25HRG): 0xB5F5B6 alone under the
    # "silent" fan label, read as the quiet toggle word.
    dev = CoolixDevice("Test", "unit", variant="quiet")
    assert "quiet" in dev.capabilities.features
    quiet = HvacState(True, "cool", 22.0, features={"quiet": True})
    sent = variant_words("quiet", quiet)
    assert sent == variant_words("quiet", HvacState(True, "cool", 22.0)) + [
        coolix_word(0xB5F5B6)
    ]
    assert variant_words("quiet", quiet, previous=dev.normalise(quiet)) == sent[:1]


def test_unknown_variant_is_refused():
    with pytest.raises(ValueError):
        CoolixDevice("Test", "unit", variant="nope")
