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
from pyhvac.fields import InvertedPairs
from pyhvac.ir.codec import decode
from pyhvac.plugins.corona import (
    CORONA_AC,
    CORONA_AC_MODELS,
    CORONA_AC_OFF_TIMER_LAYOUT,
    CORONA_AC_ON_TIMER_LAYOUT,
    CORONA_AC_SETTINGS_LAYOUT,
    CoronaAcDevice,
)
from pyhvac.state import HvacState

NAMES = ["settings", "on_timer", "off_timer"] * 2

# The C path never sends swing on: the old vocabulary's "on" has no entry in
# IRGHVAC.trans_swing, so build_ircode skips the key, swingv stays kOff, and
# IRac::corona's setSwingVToggle(swingv != kOff) leaves SwingVToggle clear.
DEFECTS = (Defect("swing_toggle", 1, 0, "C glue has no 'on' swing"),)


def device():
    return CoronaAcDevice("corona", "generic")


def state(power=True, mode="cool", temperature=22.0, **kw):
    return device().normalise(HvacState(power, mode, temperature, **kw))


def frames(target, previous=None):
    return device().frames(previous, target, ())


def read(target, previous=None):
    """The settings of the second copy (PowerButton set)."""
    return CORONA_AC_SETTINGS_LAYOUT.read(frames(target, previous)[3].data)


@pytest.mark.parametrize("record", oracle_params("CORONA_AC"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


@pytest.mark.parametrize("record, states", sequence_params("CORONA_AC"))
def test_sequence_matches_a_persistent_c_object(record, states):
    # The swing toggle depends on the message before, but the 0.1.7 glue
    # never passes swing on (DEFECTS), so this cannot catch a wrong swing
    # toggle: it checks that no other field depends on the message before.
    dev = device()
    assert_sequence_matches_c(dev, record, states, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("CORONA_AC"):
        ours = dev.frames(None, state_from_record(dev, record["state"]), ())
        for frame, layout in zip(ours, dev.LAYOUTS):
            values = layout.read(frame.data)
            assert layout.build(**values) == bytearray(frame.data)


def test_every_oracle_section_has_its_constants_and_inverted_pairs():
    # IRCoronaAc::checksum: 0x28, 0x61, getSectionByte(i), then Data0/Data1
    # each followed by its complement.
    for record in load_oracle("CORONA_AC"):
        theirs = decode(CORONA_AC, record["pulses"], expected=NAMES)
        for frame, label in zip(theirs, (0x3D, 0x6D, 0xCD) * 2):
            assert frame.data[:3] == bytes([0x28, 0x61, label])
            assert InvertedPairs(3, 7).check(frame.data)


def test_message_is_sent_twice_power_button_clear_then_set():
    # IRCoronaAc::send without a timer (every oracle record shows it).
    ours = frames(state())
    assert [f.section for f in ours] == NAMES
    first, second = (CORONA_AC_SETTINGS_LAYOUT.read(ours[i].data) for i in (0, 3))
    assert (first["power_button"], second["power_button"]) == (0, 1)
    del first["power_button"], second["power_button"]
    assert first == second
    assert ours[1:3] == ours[4:6]


def test_timer_sections_are_off():
    # stateReset's setOnTimer/setOffTimer(kCoronaAcTimerOff): 0xFFFF.
    ours = frames(state())
    assert CORONA_AC_ON_TIMER_LAYOUT.read(ours[1].data)["timer"] == 0xFFFF
    assert CORONA_AC_OFF_TIMER_LAYOUT.read(ours[2].data)["timer"] == 0xFFFF


def test_skeleton_is_the_reset_state():
    # stateReset: 17 C, cool, fan auto, power off, PowerButton set.
    data = CORONA_AC_SETTINGS_LAYOUT.build(
        temperature=17, mode="cool", fan="auto", power_button=1
    )
    assert bytes(data) == bytes.fromhex("28613d10efa15e")


@pytest.mark.parametrize("mode", ["heat", "dry", "cool", "fan"])
@pytest.mark.parametrize("t", [17.0, 23.0, 30.0])
def test_off_carries_mode_cool_in_every_mode(mode, t):
    # IRac passes mode "off"; IRCoronaAc::convertMode maps it to cool.
    values = read(state(False, mode, t, fan="2", features={"economy": True}))
    assert (values["power"], values["mode"], values["temperature"]) == (
        0,
        "cool",
        int(t),
    )
    assert (values["fan"], values["econo"]) == ("2", 1)


@pytest.mark.parametrize("mode", ["heat", "dry", "cool", "fan"])
@pytest.mark.parametrize("t", [17.0, 18.0, 29.0, 30.0])
def test_setpoint_is_sent_in_every_mode(mode, t):
    values = read(state(True, mode, t))
    assert (values["mode"], values["temperature"], values["power"]) == (
        mode,
        int(t),
        1,
    )


def test_setpoint_is_clamped_to_17_30():
    assert read(state(True, "cool", 10.0))["temperature"] == 17
    assert read(state(True, "heat", 40.0))["temperature"] == 30


@pytest.mark.parametrize(
    "mode, raw", [("heat", 0), ("dry", 1), ("cool", 2), ("fan", 3)]
)
def test_mode_uses_its_documented_value(mode, raw):
    data = frames(state(True, mode))[3].data
    assert CORONA_AC_SETTINGS_LAYOUT.read_raw(data, "mode") == raw


@pytest.mark.parametrize("fan, raw", [("auto", 0), ("1", 1), ("2", 2), ("3", 3)])
def test_every_fan_level_uses_its_documented_code(fan, raw):
    # kCoronaAcFan{Auto,Low,Medium,High}, in every mode.
    for mode in ("heat", "dry", "cool", "fan"):
        data = frames(state(True, mode, fan=fan))[3].data
        assert CORONA_AC_SETTINGS_LAYOUT.read_raw(data, "fan") == raw


def test_economy_sets_the_econo_bit():
    on = read(state(features={"economy": True}))
    off = read(state(features={"economy": False}))
    assert (on["econo"], off["econo"]) == (1, 0)


def test_swing_without_previous_sets_the_toggle():
    # A fresh IRac has no previous state: setSwingVToggle(swingv != kOff).
    assert read(state(swing_v="swing"))["swing_toggle"] == 1
    assert read(state(swing_v="off"))["swing_toggle"] == 0


@pytest.mark.parametrize(
    "before, after, toggle",
    [
        ("off", "off", 0),
        ("off", "swing", 1),
        ("swing", "swing", 0),
        ("swing", "off", 1),
    ],
)
def test_swing_toggle_with_previous_only_on_change(before, after, toggle):
    # IRac::handleToggles (CORONA_AC): toggle only when swing changes.
    previous = state(True, "cool", 24.0, swing_v=before)
    target = state(True, "cool", 25.0, swing_v=after)
    assert read(target, previous)["swing_toggle"] == toggle
    assert (
        CORONA_AC_SETTINGS_LAYOUT.read(frames(target, previous)[0].data)["swing_toggle"]
        == toggle
    )


def test_encode_passes_previous_to_the_swing_toggle():
    dev = device()
    on = HvacState(True, "cool", 22.0, swing_v="swing")
    assert dev.encode(None, on).signal != dev.encode(on, on).signal


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (3500, 1680)
    assert pulses[-2:] == (450, 10800)
    assert len(pulses) == 6 * (2 + 2 * 56 + 2)


# Settings sections of real captures (ir_Corona_test.cpp, RealExample,
# RealExample2, RealExampleShort) and timer sections (RealExample2).
@pytest.mark.parametrize(
    "hex_, fields",
    [
        # expectedState_On: heat 23C, fan low, econo, power and button on.
        (
            "28613d19e637c8",
            {
                "mode": "heat",
                "temperature": 23,
                "fan": "1",
                "econo": 1,
                "power": 1,
                "power_button": 1,
                "swing_toggle": 0,
            },
        ),
        # expectedState_Off: the same, power off. The real remote keeps heat.
        ("28613d19e627d8", {"mode": "heat", "power": 0, "power_button": 1}),
        # expectedState_17C / _30C: button clear.
        ("28613d19e611ee", {"temperature": 17, "power_button": 0}),
        ("28613d19e61ee1", {"temperature": 30, "power_button": 0}),
        # expectedState_Off2: 18C, power off.
        ("28613d19e622dd", {"temperature": 18, "power": 0, "power_button": 1}),
    ],
)
def test_settings_layout_reads_the_real_captures(hex_, fields):
    data = bytes.fromhex(hex_)
    values = CORONA_AC_SETTINGS_LAYOUT.read(data)
    assert {k: values[k] for k in fields} == fields
    assert CORONA_AC_SETTINGS_LAYOUT.build(**values) == bytearray(data)


@pytest.mark.parametrize(
    "hex_, minutes",
    [
        ("28616d28d723dc", 5 * 60),  # expectedState_TOn5: 9000 units
        ("28616d08f707f8", 60),  # expectedState_TOn1
        ("28616d10ef0ef1", 2 * 60),  # expectedState_TOn2
    ],
)
def test_timer_layout_reads_the_real_captures(hex_, minutes):
    # kCoronaAcTimerUnitsPerMin units, Data0 the low byte.
    data = bytes.fromhex(hex_)
    values = CORONA_AC_ON_TIMER_LAYOUT.read(data)
    assert values["timer"] == minutes * 30
    assert CORONA_AC_ON_TIMER_LAYOUT.build(**values) == bytearray(data)


def test_port_reproduces_the_on_capture():
    # expectedState_On: heat 23C, fan low, econo, with PowerButton set.
    target = state(True, "heat", 23.0, fan="1", features={"economy": True})
    ours = frames(target)
    assert ours[3].data == bytes.fromhex("28613d19e637c8")
    assert ours[4].data == bytes.fromhex("28616dff00ff00")
    assert ours[5].data == bytes.fromhex("2861cdff00ff00")


@pytest.mark.parametrize(
    "t, hex_",
    [
        (17.0, "28613d19e611ee"),
        (18.0, "28613d19e612ed"),
        (20.0, "28613d19e614eb"),
        (21.0, "28613d19e615ea"),
        (22.0, "28613d19e616e9"),
        (23.0, "28613d19e617e8"),
        (24.0, "28613d19e618e7"),
        (25.0, "28613d19e619e6"),
        (26.0, "28613d19e61ae5"),
        (29.0, "28613d19e61de2"),
        (30.0, "28613d19e61ee1"),
    ],
)
def test_port_reproduces_the_button_clear_captures(t, hex_):
    # expectedState_<t>C: heat, fan low, econo, PowerButton clear.
    target = state(True, "heat", t, fan="1", features={"economy": True})
    assert frames(target)[0].data == bytes.fromhex(hex_)


def test_port_reproduces_the_19c_capture():
    # expectedState_19C: as above with PowerButton set.
    target = state(True, "heat", 19.0, fan="1", features={"economy": True})
    assert frames(target)[3].data == bytes.fromhex("28613d19e633cc")


@pytest.mark.parametrize("model", CORONA_AC_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("corona", model), CoronaAcDevice)


@pytest.mark.parametrize("model", CORONA_AC_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.corona import Corona

    legacy = LegacyDevice("corona", model, Corona)
    assert CoronaAcDevice("corona", model).capabilities == legacy.capabilities


@pytest.mark.parametrize("mode", ["heat", "dry", "cool", "fan"])
@pytest.mark.parametrize("economy", [False, True])
def test_off_with_economy_matches_the_c_path(mode, economy):
    # The oracle grid has no off record with economy: compare with C directly.
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.corona import Corona

    dev = device()
    target = HvacState(False, mode, 26.0, fan="3", features={"economy": economy})
    pulses = LegacyDevice("corona", "generic", Corona).encode(None, target)
    theirs = decode(CORONA_AC, pulses.signal.pulses, expected=NAMES)
    assert [f.data for f in theirs] == [
        f.data for f in dev.frames(None, dev.normalise(target), ())
    ]


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(
        r for r in load_oracle("CORONA_AC") if r["state"].get("swing") == "on"
    )
    with pytest.raises(AssertionError, match="swing_toggle"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("CORONA_AC")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:3], DEFECTS)


def test_swing_toggle_matches_c_with_the_glue_fixed(monkeypatch):
    # With main's glue fix (IRGHVAC.trans_swing passes "on" as kAuto), swing
    # reaches C and the SwingVToggle rule needs no Defect: fresh and
    # persistent C objects send exactly the port's frames.
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac import irhvac
    from pyhvac.plugins.corona import Corona

    original = Corona.trans_swing

    def trans_swing(self, swing):
        return irhvac.swingv_t_kAuto if swing == "on" else original(self, swing)

    monkeypatch.setattr(Corona, "trans_swing", trans_swing)
    dev = device()
    record = load_oracle("CORONA_AC")[0]
    walk = ["off", "on", "on", "off", "off", "on"]
    states = [
        {"mode": mode, "temperature": 22, "fan": "auto", "swing": swing}
        for mode in ("cool", "heat")
        for swing in walk
    ]
    assert_sequence_matches_c(dev, record, states, dev.LAYOUTS)
    for old in states:
        (rec,) = c_sequence(record, [old])  # a fresh C object
        assert_matches_oracle(dev, rec, dev.LAYOUTS)
