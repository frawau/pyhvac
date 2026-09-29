import gzip
import json
from pathlib import Path

import pytest

from pyhvac import registry
from pyhvac.ir.codec import decode
from pyhvac.protocols.lg import (
    LG_NATIVE,
    LG_NATIVE_COMMAND_LAYOUT,
    LG_NATIVE_LAYOUT,
    LG_NATIVE_VARIANTS,
    LgNativeDevice,
)
from pyhvac.state import HvacState
from port_oracle import assert_matches_golden

GOLDEN = Path(__file__).parent / "fixtures" / "golden" / "lg.json.gz"
# The status of a fresh 0.1.x object of each legacy class (what the golden
# records were built from).
_LG_COMMON = {"mode": "off", "temperature": 25}
_LG_INVERTER = {
    **_LG_COMMON,
    "fan": "auto",
    "swing": "off",
    "auto_bias": "default",
    "powerful": "off",
    "cleaning": "off",
    "economy": "off",
}
LEGACY = {
    "LG": _LG_COMMON,
    "InverterV": _LG_INVERTER,
    "DualInverter": {**_LG_INVERTER, "purifier": "off", "diagnostic": "off"},
}
VARIANT = {"LG": "generic", "InverterV": "inverter v", "DualInverter": "dual inverter"}

FAN = {"auto": "auto", "lowest": "1", "low": "2", "medium": "3"}
FAN.update({"high": "4", "highest": "5"})


def _canonical(choice, old):
    """Old-vocabulary value -> canonical value, through the choice's labels."""
    if choice is None:
        return None
    for value in choice.values:
        if choice.label(value) == old:
            return value
    raise ValueError(old)


def from_old(cls_name, old):
    """The HvacState and actions an old-vocabulary state stands for, on a
    fresh object of the legacy class ``cls_name``."""
    old = {**LEGACY[cls_name], **old}
    caps = LG_NATIVE_VARIANTS[VARIANT[cls_name]]
    features = {}
    for name, choice in caps.features.items():
        value = old.get(name, choice.values[0])
        features[name] = value == "on" if choice.values == (False, True) else value
    kwargs = {}
    if caps.fan is not None:
        kwargs["fan"] = FAN[old["fan"]]
    if caps.swing_v is not None:
        kwargs["swing_v"] = _canonical(caps.swing_v, old["swing"])
    if caps.swing_h is not None:
        kwargs["swing_h"] = _canonical(caps.swing_h, old.get("hswing", "off"))
    state = HvacState(
        power=old["mode"] != "off",
        mode=caps.modes[0] if old["mode"] == "off" else old["mode"],
        temperature=old["temperature"],
        features=features,
        **kwargs,
    )
    actions = ("diagnostic",) if old.get("diagnostic") == "on" else ()
    return state, actions


def device(variant):
    return LgNativeDevice("lg", variant)


def _records():
    records = json.loads(gzip.decompress(GOLDEN.read_bytes()))
    for n, rec in enumerate(records):
        state = rec["state"]
        reason = None
        if rec["class"] == "DualInverter" and state.get("hswing", "off") != "off":
            reason = (
                "DualInverter.status has no 'hswing' key: set_hswing raised a "
                "KeyError that set_value swallowed, so hswing was never sent; "
                "the port sends the swing_h frame code_hswing encodes"
            )
        marks = [pytest.mark.skip(reason=reason)] if reason else []
        yield pytest.param(rec, id=f"{rec['class']}-{n}", marks=marks)


RECORDS = list(_records())


@pytest.mark.parametrize("record", RECORDS)
def test_reproduces_golden(record):
    cls_name = record["class"]
    dev = device(VARIANT[cls_name])
    # The records were built from a fresh legacy object: that is "previous".
    previous, _ = from_old(cls_name, {})
    state, actions = from_old(cls_name, record["state"])
    if actions:
        # assert_matches_golden encodes without actions: check them here.
        cmd = dev.encode(previous, state, actions)
        assert list(cmd.signal.pulses) == record["pulses"]
        return
    assert_matches_golden(dev, record, state, previous)


# ------------------------------------------------------------------ helpers

ON = HvacState(True, "cool", 24.0)
OFF = HvacState(False, "cool", 24.0)


def words(variant, previous, target, actions=()):
    """The frames' data as hex, through the full encode and a decode."""
    cmd = device(variant).encode(previous, target, actions)
    n = len(cmd.signal.pulses) // 68  # header 2, 32 bits * 2, footer and gap 2
    frames = decode(LG_NATIVE, cmd.signal.pulses, expected=["main"] * n)
    return [f.data.hex() for f in frames]


def state(**kw):
    base = dict(power=True, mode="cool", temperature=24.0)
    base.update(kw)
    return HvacState(**base)


# ------------------------------------------------------------------- layout


def test_state_layout_round_trip():
    data = LG_NATIVE_LAYOUT.build(
        power=True, change=1, mode="dry", temp=24 - 15, fan="high"
    )
    assert data.hex() == "88099ac0"
    assert LG_NATIVE_LAYOUT.read(data) == {
        "power": True,
        "change": 1,
        "mode": "dry",
        "temp": 9,
        "fan": "high",
    }


def test_off_frame_is_kLgAcOffCommand():
    data = LG_NATIVE_LAYOUT.build(
        power=False, change=0, mode="cool", temp=0, fan="auto"
    )
    assert data.hex() == "88c00510"  # 0x88C0051, plus the unsent nibble


@pytest.mark.parametrize(
    "name", list(LG_NATIVE_COMMAND_LAYOUT.fields["command"].values)
)
def test_command_layout_round_trip(name):
    data = LG_NATIVE_COMMAND_LAYOUT.build(command=name)
    assert LG_NATIVE_COMMAND_LAYOUT.read(data) == {"command": name}
    assert LG_NATIVE_COMMAND_LAYOUT.checksum.check(data)


def test_frames_decode_with_the_layouts():
    dev = device("dual inverter")
    target = dev.normalise(state(swing_v="3", features={"economy": "60"}))
    frames = dev.frames(None, target, ())
    assert LG_NATIVE_LAYOUT.read(frames[0].data)["mode"] == "cool"
    commands = [LG_NATIVE_COMMAND_LAYOUT.read(f.data)["command"] for f in frames[1:]]
    assert commands == [
        "swing_v 60°",
        "swing_h off",
        "purifier off",
        "cleaning off",
        "economy 60",
    ]


# -------------------------------------------------------------------- rules


@pytest.mark.parametrize("previous", [None, ON, OFF])
@pytest.mark.parametrize("variant", list(LG_NATIVE_VARIANTS))
def test_power_off_is_the_off_frame_alone(variant, previous):
    target = HvacState(False, "dry", 20.0, features={"cleaning": True})
    assert words(variant, previous, target) == ["88c00510"]


@pytest.mark.parametrize(
    "previous, change", [(None, 0), (OFF, 0), (ON, 1)], ids=["none", "off", "on"]
)
def test_change_bit_follows_previous_power(previous, change):
    dev = device("generic")
    frame = dev.frames(previous and dev.normalise(previous), dev.normalise(ON), ())[0]
    assert LG_NATIVE_LAYOUT.read(frame.data)["change"] == change


@pytest.mark.parametrize(
    "mode, bias, celsius",
    [
        ("cool", "default", 21),
        ("fan", "default", 18),
        ("dry", "default", 24),
        ("auto", "default", 17),
        ("auto", "-2", 15),
        ("auto", "-1", 16),
        ("auto", "+1", 18),
        ("auto", "+2", 19),
    ],
)
def test_temperature_depends_on_the_mode(mode, bias, celsius):
    dev = device("inverter v")
    target = dev.normalise(
        state(mode=mode, temperature=21.0, features={"auto_bias": bias})
    )
    frame = dev.frames(None, target, ())[0]
    assert LG_NATIVE_LAYOUT.read(frame.data)["temp"] == celsius - 15


def test_generic_auto_temperature_without_bias():
    # LG (generic) offers no auto mode; code_temperature's 17 without bias
    dev = device("generic")
    assert dev._temperature(state(mode="auto")) == 17


def test_fan_forced_auto_in_auto_mode():
    dev = device("inverter v")
    assert dev.normalise(state(mode="auto", fan="3")).fan == "auto"
    assert dev.normalise(state(mode="cool", fan="3")).fan == "3"


def test_generic_sends_fan_auto():
    dev = device("generic")
    frame = dev.frames(None, dev.normalise(state(fan="3")), ())[0]
    assert LG_NATIVE_LAYOUT.read(frame.data)["fan"] == "auto"


def test_unknown_previous_sends_every_setting():
    frames = words("inverter v", None, state())
    # state, swing off, cleaning off, economy off; powerful off sends nothing
    assert frames == ["880095e0", "881315a0", "88c00b70", "88c07f20"]


def test_unknown_previous_sends_powerful_on():
    frames = words("inverter v", None, state(features={"powerful": True}))
    assert "88100890" in frames


def test_only_changed_settings_are_sent():
    prev = state(swing_v="1")
    assert words("inverter v", prev, state(swing_v="2")) == ["88130480"]


def test_unchanged_state_resends_the_state_frame():
    assert words("inverter v", ON, ON) == ["88089560"]


def test_state_change_with_specials():
    frames = words("inverter v", ON, state(temperature=25.0, swing_v="swing"))
    assert frames == ["8808a570", "88131490"]


def test_powerful_off_resends_the_state_frame():
    prev = state(features={"powerful": True})
    assert words("inverter v", prev, ON) == ["88089560"]


def test_powerful_off_with_a_special_still_sends_the_state_frame():
    prev = state(features={"powerful": True})
    frames = words("inverter v", prev, state(swing_v="1"))
    assert frames == ["88089560", "881308c0"]


def test_auto_bias_change_alone_sends_the_state_frame():
    # LG.build_code sent nothing here (it tests mode, temperature, fan only)
    prev = state(mode="auto")
    target = state(mode="auto", features={"auto_bias": "+1"})
    expected = LG_NATIVE_LAYOUT.build(
        power=True, change=1, mode="auto", temp=18 - 15, fan="auto"
    )
    assert words("inverter v", prev, target) == [expected.hex()]


def test_hswing_is_sent():
    # The golden records skipped for the hswing bug: from a fresh object,
    # the port sends the state frame and the code_hswing frame.
    prev, _ = from_old("DualInverter", {})
    for old, code in [("swing", "16"), ("left", "0b"), ("swing right", "11")]:
        target, _ = from_old(
            "DualInverter", {"mode": "auto", "temperature": 23, "hswing": old}
        )
        frames = words("dual inverter", prev, target)
        assert frames[0] == "880325a0"
        assert frames[1][:6] == "8813" + code
        assert len(frames) == 2


def test_diagnostic_is_an_action_sent_last():
    frames = words("dual inverter", ON, ON, ["diagnostic"])
    assert frames == ["88c0ce60"]
    frames = words("dual inverter", ON, state(temperature=25.0), ["diagnostic"])
    assert frames[-1] == "88c0ce60" and len(frames) == 2


def test_diagnostic_only_on_dual_inverter():
    with pytest.raises(ValueError):
        device("inverter v").encode(None, ON, ["diagnostic"])


def test_diagnostic_is_not_sent_with_power_off():
    assert words("dual inverter", ON, OFF, ["diagnostic"]) == ["88c00510"]


# ------------------------------------------------------------- capabilities


def test_generic_capabilities():
    caps = LG_NATIVE_VARIANTS["generic"]
    assert caps.modes == ("cool", "fan", "dry")
    assert (caps.temperature.min, caps.temperature.max) == (18.0, 29.0)
    assert caps.fan is caps.swing_v is caps.swing_h is None
    assert dict(caps.features) == {} and dict(caps.actions) == {}


def test_inverter_v_capabilities():
    caps = LG_NATIVE_VARIANTS["inverter v"]
    assert caps.modes == ("auto", "cool", "fan", "dry")
    assert (caps.temperature.min, caps.temperature.max) == (16.0, 29.0)
    assert caps.swing_v.values == ("off", "swing", "1", "2")
    assert caps.swing_h is None
    assert set(caps.features) == {"auto_bias", "powerful", "cleaning", "economy"}
    assert dict(caps.actions) == {}


def test_dual_inverter_capabilities():
    caps = LG_NATIVE_VARIANTS["dual inverter"]
    assert caps.swing_v.values == ("off", "swing", "1", "2", "3", "4", "5", "6")
    assert caps.swing_h.values == ("off", "swing") + tuple("1234567")
    assert set(caps.features) == {
        "auto_bias",
        "powerful",
        "purifier",
        "cleaning",
        "economy",
    }
    assert set(caps.actions) == {"diagnostic"}


def _offered(variant):
    """(target, expected fragment) for every value each capability offers."""
    caps = LG_NATIVE_VARIANTS[variant]
    for mode in caps.modes:
        yield state(mode=mode)
    t = caps.temperature
    for celsius in range(int(t.min), int(t.max) + 1):
        yield state(temperature=float(celsius))
    for fan in caps.fan.values if caps.fan else ():
        yield state(fan=fan)
    for swing in caps.swing_v.values if caps.swing_v else ():
        yield state(swing_v=swing)
    for swing in caps.swing_h.values if caps.swing_h else ():
        yield state(swing_h=swing)
    for name, choice in caps.features.items():
        for value in choice.values:
            yield state(features={name: value})


@pytest.mark.parametrize("variant", list(LG_NATIVE_VARIANTS))
def test_every_offered_value_encodes_as_itself(variant):
    dev = device(variant)
    caps = dev.capabilities
    for target in _offered(variant):
        norm = dev.normalise(target)
        frames = dev.frames(None, norm, ())
        head = LG_NATIVE_LAYOUT.read(frames[0].data)
        assert head["mode"] == norm.mode
        if norm.mode == "cool":
            assert head["temp"] == int(norm.temperature) - 15
        if caps.fan is not None and norm.mode != "auto":
            assert head["fan"] == caps.fan.label(norm.fan)
        commands = {
            LG_NATIVE_COMMAND_LAYOUT.read(f.data)["command"] for f in frames[1:]
        }
        if caps.swing_v is not None:
            assert f"swing_v {caps.swing_v.label(norm.swing_v)}" in commands
        if caps.swing_h is not None:
            assert f"swing_h {caps.swing_h.label(norm.swing_h)}" in commands
        for name, value in norm.features.items():
            if name == "auto_bias" or (name == "powerful" and not value):
                continue
            label = caps.features[name].label(value)
            assert f"{name} {label}" in commands


def test_temperatures_clamp_to_the_variant_range():
    assert device("generic").normalise(state(temperature=16.0)).temperature == 18.0
    assert device("inverter v").normalise(state(temperature=16.0)).temperature == 16
    assert device("inverter v").normalise(state(temperature=30.0)).temperature == 29


def test_heat_is_not_offered():
    for caps in LG_NATIVE_VARIANTS.values():
        assert "heat" not in caps.modes


# ----------------------------------------------------------------- registry


@pytest.fixture
def fresh_registry():
    registry._factories.cache_clear()
    yield
    registry._factories.cache_clear()


def test_unknown_variant():
    with pytest.raises(ValueError):
        LgNativeDevice("lg", "generic", variant="nope")
