import pytest

from oracle import load_oracle
from port_oracle import assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.bosch import (
    BOSCH144_MODELS,
    BOSCH144_OFF_LAYOUT,
    BOSCH144_SECTION3_LAYOUT,
    BOSCH144_SECTION_LAYOUT,
    Bosch144Device,
)
from pyhvac.state import HvacState

# No Defect: the C path sends the documented Bosch144 values for every state
# the entity can express (quiet is in the legacy glue's key map, and the
# entity has no swing or sleep).

# ir_Bosch_test.cpp, TestDecodeBosch144: RealExample (issue 1787: cool, fan
# 100 %, 16 C) and the two DURASTAR DRAW09F2A captures (heat, fan auto, 73 F;
# heat, fan high, 61 F), as their three sections.
REAL_EXAMPLE = ("b24d3fc000ff", "b24d3fc000ff", "d56400100049")
DURASTAR_73F = ("b24dbf405ca3", "b24dbf405ca3", "d5660001003c")
DURASTAR_61F = ("b24d3fc00cf3", "b24d3fc00cf3", "d5642011006a")
# kBosch144Off, one section.
OFF = bytes.fromhex("b24d7b84e01f")


def device(model="generic"):
    return Bosch144Device("bosch", model)


def state(power=True, mode="cool", temperature=22.0, fan="auto", quiet=False):
    return device().normalise(
        HvacState(power, mode, temperature, fan=fan, features={"quiet": quiet})
    )


def frames(target):
    return device().frames(None, target, ())


def read(target):
    """The fields of a state message: sections 1-2 and section 3 merged."""
    s1, s2, s3, _ = frames(target)
    assert s1 == s2
    return {
        **BOSCH144_SECTION_LAYOUT.read(s1.data),
        **BOSCH144_SECTION3_LAYOUT.read(s3.data),
    }


def codes(target):
    """The (mode, fan, setpoint) codes a state message carries, rejoined."""
    v = read(target)
    return (
        v["mode_s1"] << 1 | v["mode_s3"],
        v["fan_s1"] << 6 | v["fan_s3"],
        v["temp_s1"] << 2 | v["temp_s3"],
    )


def wire(record):
    """``record`` with the pulses the C library puts on the wire.

    sendBosch144 ends the last section with space(kBoschFooterSpace) and then
    space(kDefaultMessageGap); IRac's timing log keeps them as two entries,
    so the fixture's last entry (100 000 µs) sits at a mark position.
    """
    pulses = record["pulses"]
    assert len(pulses) % 2 and pulses[-2:] == [5235, 100000]
    return {**record, "pulses": pulses[:-2] + [5235 + 100000]}


def layouts(dev, record):
    return dev.LAYOUTS if record["state"]["mode"] != "off" else dev.OFF_LAYOUTS


@pytest.mark.parametrize("record", oracle_params("BOSCH144"))
def test_matches_c_library(record):
    dev = device(record["model"])
    assert_matches_oracle(dev, wire(record), layouts(dev, record))


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("BOSCH144"):
        *sections, end = dev.frames(None, state_from_record(dev, record["state"]), ())
        assert (end.section, end.data, end.nbits) == ("end", b"", 0)
        for f, layout in zip(sections, layouts(dev, record)):
            values = layout.read(f.data)
            assert layout.build(**values) == bytearray(f.data)
            assert layout.checksum.check(f.data)


@pytest.mark.parametrize(
    "capture, fields",
    [
        (
            REAL_EXAMPLE,
            {"mode": 0b000, "fan": 0b001110010, "temp": 0b000010, "fahrenheit": 0},
        ),
        # kBosch144FahrenheitMap: 73F is 0b010100, 61F is 0b000011.
        (
            DURASTAR_73F,
            {"mode": 0b110, "fan": 0b101110011, "temp": 0b010100, "fahrenheit": 1},
        ),
        (
            DURASTAR_61F,
            {"mode": 0b110, "fan": 0b001110010, "temp": 0b000011, "fahrenheit": 1},
        ),
    ],
)
def test_layouts_read_the_real_captures(capture, fields):
    s1, s2, s3 = (bytes.fromhex(h) for h in capture)
    assert s1 == s2
    a = BOSCH144_SECTION_LAYOUT.read(s1)
    b = BOSCH144_SECTION3_LAYOUT.read(s3)
    assert {
        "mode": a["mode_s1"] << 1 | b["mode_s3"],
        "fan": a["fan_s1"] << 6 | b["fan_s3"],
        "temp": a["temp_s1"] << 2 | b["temp_s3"],
        "fahrenheit": b["fahrenheit"],
    } == fields
    assert BOSCH144_SECTION_LAYOUT.build(**a) == bytearray(s1)
    assert BOSCH144_SECTION3_LAYOUT.build(**b) == bytearray(s3)


def test_port_reproduces_the_real_example():
    # Cool, fan 100 % (kMax: "highest"), 16 C, quiet off.
    ours = frames(state(True, "cool", 16.0, fan="5"))
    assert tuple(f.data.hex() for f in ours[:3]) == REAL_EXAMPLE


@pytest.mark.parametrize("mode", ["auto", "cool", "fan", "dry", "heat"])
@pytest.mark.parametrize("quiet", [False, True])
def test_off_is_the_fixed_off_message(mode, quiet):
    # IRac::bosch144 sends kBosch144Off and returns: mode, setpoint, fan and
    # quiet are not sent.
    ours = frames(state(False, mode, 30.0, fan="5", quiet=quiet))
    assert [f.section for f in ours] == ["section", "section", "end"]
    assert ours[0].data == ours[1].data == OFF
    assert BOSCH144_OFF_LAYOUT.checksum.check(OFF)


@pytest.mark.parametrize(
    "mode, code",
    [("cool", 0b000), ("dry", 0b011), ("auto", 0b101), ("heat", 0b110), ("fan", 0b010)],
)
def test_every_mode_uses_its_documented_code(mode, code):
    assert codes(state(True, mode))[0] == code


@pytest.mark.parametrize(
    "t, code",
    [
        (16, 0b000010),
        (17, 0b000000),
        (18, 0b000100),
        (19, 0b001100),
        (20, 0b001000),
        (21, 0b011000),
        (22, 0b011100),
        (23, 0b010100),
        (24, 0b010000),
        (25, 0b110000),
        (26, 0b110100),
        (27, 0b100100),
        (28, 0b100000),
        (29, 0b101000),
        (30, 0b101100),
    ],
)
@pytest.mark.parametrize("mode", ["auto", "cool", "fan", "dry", "heat"])
def test_every_setpoint_uses_the_celsius_map_in_every_mode(mode, t, code):
    # kBosch144CelsiusMap, UseFahrenheit clear (IRac passes celsius).
    assert codes(state(True, mode, float(t)))[2] == code
    assert read(state(True, mode, float(t)))["fahrenheit"] == 0


@pytest.mark.parametrize(
    "fan, code",
    [
        ("auto", 0b101110011),  # kBosch144FanAuto
        ("1", 0b111001010),  # kBosch144Fan20
        ("2", 0b100010100),  # kBosch144Fan40
        ("3", 0b010011110),  # kBosch144Fan60
        ("4", 0b001101000),  # kBosch144Fan80
        ("5", 0b001110010),  # kBosch144Fan100
    ],
)
@pytest.mark.parametrize("mode", ["cool", "fan", "heat"])
def test_every_fan_level_uses_its_documented_code(mode, fan, code):
    assert codes(state(True, mode, fan=fan))[1] == code


@pytest.mark.parametrize("fan", ["auto", "1", "2", "3", "4", "5"])
@pytest.mark.parametrize("mode", ["auto", "dry"])
def test_auto_and_dry_send_fan_auto0(mode, fan):
    # IRBosch144AC::setMode (called after setFan) writes kBosch144FanAuto0.
    assert codes(state(True, mode, fan=fan))[1] == 0b000110011


@pytest.mark.parametrize("fan", ["auto", "1", "2", "3", "4", "5"])
@pytest.mark.parametrize("mode", ["auto", "cool", "fan", "dry", "heat"])
def test_quiet_sets_the_quiet_bit_and_fan_auto(mode, fan):
    # IRBosch144AC::setQuiet (called last) sets Quiet and kBosch144FanAuto.
    target = state(True, mode, fan=fan, quiet=True)
    assert read(target)["quiet"] == 1
    assert codes(target)[1] == 0b101110011
    assert read(state(True, mode, fan=fan))["quiet"] == 0


def test_previous_is_ignored():
    dev = device()
    on = HvacState(True, "cool", 22.0)
    off = HvacState(False, "heat", 30.0, fan="5")
    assert dev.encode(None, on).signal == dev.encode(off, on).signal
    assert dev.encode(on, on).signal == dev.encode(None, on).signal


def test_message_shape():
    dev = device()
    on = dev.encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    off = dev.encode(None, HvacState(False, "cool", 22.0)).signal.pulses
    for pulses, sections in ((on, 3), (off, 2)):
        assert pulses[:2] == (4366, 4415)
        assert pulses[-2:] == (456, 5235 + 100000)
        assert len(pulses) == sections * (2 + 2 * 48 + 2)


@pytest.mark.parametrize("model", BOSCH144_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("bosch", model), Bosch144Device)


def test_layouts_must_cover_every_frame():
    dev = device()
    record = wire(load_oracle("BOSCH144")[-1])
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.OFF_LAYOUTS)


def test_capabilities_are_the_headers():
    # ir_Bosch.h: kBosch144CelsiusMin/Max 16-30; kBosch144Fan20..Fan100 and
    # kBosch144FanAuto; kBosch144{Cool,Dry,Auto,Heat,Fan}; the Quiet bit.
    caps = device().capabilities
    assert set(caps.modes) == {"auto", "cool", "fan", "dry", "heat"}
    assert (caps.temperature.min, caps.temperature.max) == (16.0, 30.0)
    assert caps.fan.values == ("auto", "1", "2", "3", "4", "5")
    assert (caps.swing_v, caps.swing_h) == (None, None)
    assert set(caps.features) == {"quiet"}
