import gzip
import json
from pathlib import Path

import pytest

from pyhvac import registry
from pyhvac.ir.codec import decode
from pyhvac.protocols.panasonic import (
    PANASONIC_NATIVE,
    PANASONIC_NATIVE_MAIN,
    PANASONIC_NATIVE_SHORT,
    PANASONIC_NATIVE_VARIANTS,
    PanasonicNativeDevice,
)
from pyhvac.state import HvacState
from port_oracle import assert_matches_golden

GOLDEN = Path(__file__).parent / "fixtures" / "golden" / "panasonic.json.gz"
# The status of a fresh 0.1.x object of each legacy class (what the golden
# records were built from).
LEGACY = {
    "Panasonic": {"mode": "off", "temperature": 25},
    "PanaCassette": {
        "mode": "off",
        "temperature": 25,
        "fan": "auto",
        "swing": "auto",
        "purifier": "off",
        "economy": "off",
        "cleaning": "off",
    },
}
VARIANT = {"Panasonic": "generic", "PanaCassette": "4 way cassette"}


def _canonical(choice, old):
    for value in choice.values:
        if choice.label(value) == old:
            return value
    raise ValueError(old)


def from_old(cls_name, old):
    """The HvacState an old-vocabulary state stands for, on a fresh object
    of the legacy class ``cls_name``."""
    old = {**LEGACY[cls_name], **old}
    caps = PANASONIC_NATIVE_VARIANTS[VARIANT[cls_name]]
    kwargs = {}
    if caps.fan is not None:
        kwargs["fan"] = _canonical(caps.fan, old["fan"])
    if caps.swing_v is not None:
        kwargs["swing_v"] = _canonical(caps.swing_v, old["swing"])
    return HvacState(
        power=old["mode"] != "off",
        mode=caps.modes[0] if old["mode"] == "off" else old["mode"],
        temperature=old["temperature"],
        features={name: old[name] == "on" for name in caps.features},
        **kwargs,
    )


RECORDS = json.loads(gzip.decompress(GOLDEN.read_bytes()))


@pytest.mark.parametrize(
    "record", RECORDS, ids=[f"{r['class']}-{n}" for n, r in enumerate(RECORDS)]
)
def test_reproduces_golden(record):
    cls_name = record["class"]
    dev = PanasonicNativeDevice("panasonic", VARIANT[cls_name])
    # The records were built from a fresh legacy object: that is "previous".
    previous = from_old(cls_name, {})
    assert_matches_golden(dev, record, from_old(cls_name, record["state"]), previous)


# ------------------------------------------------------------------ helpers

ON = HvacState(True, "cool", 24.0)
OFF = HvacState(False, "cool", 24.0)


def device(variant="4 way cassette"):
    return PanasonicNativeDevice("panasonic", variant)


def state(**kw):
    base = dict(power=True, mode="cool", temperature=24.0)
    base.update(kw)
    return HvacState(**base)


def frames(previous, target, variant="4 way cassette"):
    """The frames' data, through the full encode and a decode."""
    dev = device(variant)
    cmd = dev.encode(previous, target)
    prev = None if previous is None else dev.normalise(previous)
    count = len(dev.frames(prev, cmd.state, ()))
    decoded = decode(PANASONIC_NATIVE, cmd.signal.pulses, expected=["main"] * count)
    return [f.data for f in decoded]


def main_frame(previous, target, variant="4 way cassette"):
    return PANASONIC_NATIVE_MAIN.read(frames(previous, target, variant)[-1])


def shorts(previous, target):
    return [
        PANASONIC_NATIVE_SHORT.read(f)["frame"] for f in frames(previous, target)[:-1]
    ]


# ------------------------------------------------------------------- layout


def test_main_layout_round_trip():
    values = dict(
        power=1,
        mode="dry",
        temperature=22,
        fan="medium",
        swing="45°",
        profile=None,
        purifier=1,
    )
    data = PANASONIC_NATIVE_MAIN.build(**values)
    assert PANASONIC_NATIVE_MAIN.read(data) == values
    assert PANASONIC_NATIVE_MAIN.checksum.check(data)


def test_main_layout_matches_the_legacy_bytes():
    # Panasonic.build_code for cool 24 on a fresh object (golden record 7)
    data = PANASONIC_NATIVE_MAIN.build(
        power=1, mode="cool", temperature=24, fan=None, swing=None, profile=None
    )
    assert data.hex() == "40040720009c0c010000007007000091000066"


@pytest.mark.parametrize("name", ["first", "economy", "cleaning"])
def test_short_layout_round_trip(name):
    data = PANASONIC_NATIVE_SHORT.build(frame=name)
    assert PANASONIC_NATIVE_SHORT.read(data) == {"frame": name}
    # What the 0.1.x Panasonic class sent (FHEADER + F1BODY, FECON, FODOUR,
    # each with its crc byte).
    legacy = {
        "first": "4004072000000060",
        "economy": "4004072001a1ac02",
        "cleaning": "4004072001d94cca",
    }[name]
    assert bytes(data).hex() == legacy


# The 0.1.x Panasonic.code_temperature() for 16..31 °C.
LEGACY_TEMPERATURE_CODE = "04 44 24 64 14 54 34 74 0c 4c 2c 6c 1c 5c 3c 7c".split()


def test_every_legacy_temperature_code():
    for celsius in range(16, 32):
        data = PANASONIC_NATIVE_MAIN.build(
            power=1, mode="cool", temperature=celsius, fan=None, swing=None
        )
        assert data[6:7].hex() == LEGACY_TEMPERATURE_CODE[celsius - 16]


# -------------------------------------------------------------------- rules


def test_message_is_the_first_frame_then_the_main_frame():
    data = frames(ON, ON)
    assert len(data) == 2
    assert PANASONIC_NATIVE_SHORT.read(data[0]) == {"frame": "first"}


@pytest.mark.parametrize("celsius", [16.0, 24.0, 31.0])
def test_fan_mode_sends_27(celsius):
    assert main_frame(None, state(mode="fan", temperature=celsius))["temperature"] == 27


def test_off_sends_the_previous_settings():
    prev = state(temperature=20.0, fan="3", swing_v="2", features={"purifier": True})
    target = HvacState(False, "dry", 30.0, fan="1", swing_v="4")
    read = main_frame(prev, target)
    assert read["power"] == 0 and read["mode"] == "auto"
    assert (read["temperature"], read["fan"], read["swing"]) == (20, "highest", "60°")
    assert read["purifier"] == 1


def test_off_after_fan_mode_sends_27():
    prev = state(mode="fan", temperature=20.0)
    assert main_frame(prev, OFF)["temperature"] == 27


def test_off_without_previous_sends_the_target_settings():
    target = HvacState(False, "dry", 30.0, fan="1", swing_v="4")
    read = main_frame(None, target)
    assert read["power"] == 0 and read["mode"] == "auto"
    assert (read["temperature"], read["fan"], read["swing"]) == (30, "lowest", "30°")


def test_generic_sends_no_fan_and_no_swing():
    read = main_frame(None, state(fan="3", swing_v="2"), variant="generic")
    assert read["fan"] is None and read["swing"] is None
    assert read["profile"] is None and read["purifier"] == 0


def test_main_frame_ignores_previous_when_on():
    target = state(temperature=22.0, fan="2", swing_v="5")
    ours = {bytes(f) for f in frames(None, target)}
    for prev in (ON, OFF, state(mode="dry", fan="1")):
        assert frames(prev, target)[-1] in ours


@pytest.mark.parametrize("name", ["economy", "cleaning"])
def test_toggle_only_on_change(name):
    on = state(features={name: True})
    assert shorts(None, on) == ["first", name, "first"]
    assert shorts(ON, on) == ["first", name, "first"]
    assert shorts(on, on) == ["first"]
    assert shorts(on, ON) == ["first", name, "first"]
    assert shorts(ON, ON) == ["first"]
    assert shorts(None, ON) == ["first"]  # a fresh unit has them off


def test_toggles_in_legacy_order():
    both = state(features={"economy": True, "cleaning": True})
    assert shorts(ON, both) == ["first", "cleaning", "first", "economy", "first"]


def test_no_toggle_with_power_off():
    target = HvacState(False, "cool", 24.0, features={"economy": True})
    assert shorts(ON, target) == ["first"]


# ------------------------------------------------------------- capabilities


def test_generic_capabilities():
    caps = PANASONIC_NATIVE_VARIANTS["generic"]
    assert caps.modes == ("auto", "cool", "fan", "dry")
    assert (caps.temperature.min, caps.temperature.max) == (16.0, 31.0)
    assert caps.fan is caps.swing_v is caps.swing_h is None
    assert dict(caps.features) == {} and dict(caps.actions) == {}


def test_cassette_capabilities():
    caps = PANASONIC_NATIVE_VARIANTS["4 way cassette"]
    assert caps.modes == ("auto", "cool", "fan", "dry")
    assert (caps.temperature.min, caps.temperature.max) == (16.0, 31.0)
    assert caps.fan.values == ("auto", "1", "2", "3")
    assert caps.swing_v.values == ("auto",) + tuple("123456")
    assert caps.swing_h is None
    assert set(caps.features) == {"purifier", "economy", "cleaning"}


@pytest.mark.parametrize("variant", list(PANASONIC_NATIVE_VARIANTS))
def test_every_offered_value_encodes_as_itself(variant):
    caps = PANASONIC_NATIVE_VARIANTS[variant]
    for mode in caps.modes:
        assert main_frame(None, state(mode=mode), variant)["mode"] == mode
    for celsius in range(int(caps.temperature.min), int(caps.temperature.max) + 1):
        read = main_frame(None, state(temperature=float(celsius)), variant)
        assert read["temperature"] == celsius
    for fan in caps.fan.values if caps.fan else ():
        read = main_frame(None, state(fan=fan), variant)
        assert read["fan"] == caps.fan.label(fan)
    for swing in caps.swing_v.values if caps.swing_v else ():
        read = main_frame(None, state(swing_v=swing), variant)
        assert read["swing"] == caps.swing_v.label(swing)
    if "purifier" in caps.features:
        for value in (False, True):
            read = main_frame(None, state(features={"purifier": value}), variant)
            assert read["purifier"] == int(value)


def test_heat_and_profile_are_not_offered():
    for caps in PANASONIC_NATIVE_VARIANTS.values():
        assert "heat" not in caps.modes
        assert not {"powerful", "quiet"} & set(caps.features)


# ----------------------------------------------------------------- registry


@pytest.fixture
def fresh_registry():
    registry._factories.cache_clear()
    yield
    registry._factories.cache_clear()


def test_unknown_variant():
    with pytest.raises(ValueError):
        PanasonicNativeDevice("panasonic", "generic", variant="nope")
