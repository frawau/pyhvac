import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.panasonic import (
    PANASONIC_AC32_HIGH_LAYOUT,
    PANASONIC_AC32_LOW_LAYOUT,
    PANASONIC_AC32_MODELS,
    PANASONIC_AC32_DOUBLED,
    PanasonicAc32Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented values here:
# - the old swing labels go through IRGHVAC.trans_swing ("90°" -> kHigh,
#   "60°" -> kUpperMiddle) into IRPanasonicAc32::convertSwingV, which passes
#   kHigh through as kPanasonicAcSwingVHigh (so kPanasonicAcSwingVHighest is
#   never sent) and has no kUpperMiddle case (it falls back to
#   kPanasonicAc32SwingVAuto);
# - the legacy glue (IRGHVAC.trans_hswing) has no "on" key, so swingh stays
#   kOff and IRac::panasonic32 never sets the SwingH bit.
DEFECTS = (
    Defect("swing_v", "1", "2", "C sends SwingVHigh for highest"),
    Defect("swing_v", "2", "auto", "C has no upper-middle case: sends auto"),
    Defect("swing_h", "swing", "off", "legacy glue never passes hswing on"),
)


def device(model="generic 32"):
    return PanasonicAc32Device("panasonic", model)


def raw(state, previous=None):
    """The 32-bit word (PanasonicAc32Protocol.raw) the port sends."""
    dev = device()
    if previous is not None:
        previous = dev.normalise(previous)
    high, high2, low, low2 = dev.frames(previous, dev.normalise(state), ())
    assert (high.data, low.data) == (high2.data, low2.data)
    return int.from_bytes(
        bytes((low.data[0], low.data[2], high.data[0], high.data[2])), "little"
    )


def read(state, previous=None):
    dev = device()
    if previous is not None:
        previous = dev.normalise(previous)
    high, _, low, _ = dev.frames(previous, dev.normalise(state), ())
    return {
        **PANASONIC_AC32_HIGH_LAYOUT.read(high.data),
        **PANASONIC_AC32_LOW_LAYOUT.read(low.data),
    }


@pytest.mark.parametrize("record", oracle_params("PANASONIC_AC32"))
def test_matches_c_library(record):
    dev = device(record["model"])
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("PANASONIC_AC32"):
        state = state_from_record(dev, record["state"])
        for frame, layout in zip(dev.frames(None, state, ()), dev.LAYOUTS):
            values = layout.read(frame.data)
            assert layout.build(**values) == bytearray(frame.data)


def test_known_good_state():
    # kPanasonicAc32KnownGood = 0x0AF136FC: cool, 16 °C, fan auto, swing V
    # auto, swing H on, PowerToggle 1 ("keep the same": the unit is on).
    on = HvacState(True, "cool", 16.0, swing_v="auto", swing_h="swing")
    assert raw(on, previous=on) == 0x0AF136FC


def test_human_readable_example():
    # ir_Panasonic_test.cpp HumanReadable: power toggle on, heat, 24 °C, fan
    # medium, swing H off, swing V lowest.
    state = HvacState(True, "heat", 24.0, fan="3", swing_v="5", swing_h="off")
    assert raw(state) == 0x044936D4


def test_every_byte_is_sent_twice_in_two_blocks_high_half_first():
    # sendPanasonicAC32: section 0 = bytes 2-3, section 1 = bytes 0-1; each
    # section twice, each byte doubled.
    dev = device()
    frames = dev.frames(None, dev.normalise(HvacState(True, "cool", 16.0)), ())
    assert [f.section for f in frames] == ["block", "repeat", "block", "repeat"]
    assert [f.data.hex() for f in frames] == [
        "f1f10202",
        "f1f10202",
        "f4f43636",
        "f4f43636",
    ]


def test_message_shape():
    # Matches the SyntheticMessage output in ir_Panasonic_test.cpp.
    dev = device()
    pulses = dev.encode(None, HvacState(True, "cool", 16.0)).signal.pulses
    section = 2 + 64 + 2 + 64 + 2 + 2
    assert len(pulses) == 2 * section
    assert pulses[:2] == (3543, 3450)
    assert pulses[66:68] == (3543, 3450)
    assert pulses[132:136] == (3543, 3450, 920, 13946)
    assert pulses[-4:] == (3543, 3450, 920, 13946)
    assert dev.encode(None, HvacState(True, "cool", 16.0)).signal.carrier == 36700


def test_doubled_bytes_hold_no_field():
    for layout in (PANASONIC_AC32_HIGH_LAYOUT, PANASONIC_AC32_LOW_LAYOUT):
        copies = {8 * b + i for b in layout.checksum.positions() for i in range(8)}
        for name, field in layout.fields.items():
            assert not copies & set(field.bits), name


def test_doubled_bytes_check():
    data = bytearray.fromhex("12003400")
    assert not PANASONIC_AC32_DOUBLED.check(data)
    PANASONIC_AC32_DOUBLED.apply(data)
    assert data.hex() == "12123434" and PANASONIC_AC32_DOUBLED.check(data)


def test_off_carries_mode_auto_in_every_mode():
    # IRac passes mode "off"; IRPanasonicAc32::convertMode maps it to auto.
    dev = device()
    for mode in dev.capabilities.modes:
        for t in (16.0, 30.0):
            values = read(HvacState(False, mode, t))
            assert (values["mode"], values["temperature"]) == ("auto", int(t))


@pytest.mark.parametrize(
    "mode, code", [("auto", 6), ("cool", 2), ("dry", 3), ("heat", 4), ("fan", 1)]
)
def test_every_mode_uses_its_documented_value(mode, code):
    dev = device()
    high, *_ = dev.frames(None, dev.normalise(HvacState(True, mode, 22.0)), ())
    assert PANASONIC_AC32_HIGH_LAYOUT.read_raw(high.data, "mode") == code


def test_temperature_is_offset_from_15_and_clamped():
    assert read(HvacState(True, "cool", 16.0))["temperature"] == 16
    assert raw(HvacState(True, "cool", 30.0)) >> 16 & 0x0F == 15
    assert read(HvacState(True, "cool", 10.0))["temperature"] == 16
    assert read(HvacState(True, "cool", 35.0))["temperature"] == 30


@pytest.mark.parametrize(
    "fan, code", [("auto", 0xF), ("1", 2), ("2", 3), ("3", 4), ("4", 5), ("5", 6)]
)
def test_every_fan_level_uses_its_documented_value(fan, code):
    dev = device()
    high, *_ = dev.frames(
        None, dev.normalise(HvacState(True, "cool", 22.0, fan=fan)), ()
    )
    assert PANASONIC_AC32_HIGH_LAYOUT.read_raw(high.data, "fan") == code


@pytest.mark.parametrize(
    "swing, code", [("auto", 7), ("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 5)]
)
def test_swing_positions_follow_the_documented_order(swing, code):
    # Canonical "1" is the topmost documented position (kPanasonicAcSwingV
    # Highest), counting down to "5" = kPanasonicAcSwingVLowest.
    dev = device()
    _, _, low, _ = dev.frames(
        None, dev.normalise(HvacState(True, "cool", 22.0, swing_v=swing)), ()
    )
    assert PANASONIC_AC32_LOW_LAYOUT.read_raw(low.data, "swing_v") == code


def test_horizontal_swing_sets_the_swing_h_bit():
    assert read(HvacState(True, "cool", 22.0, swing_h="swing"))["swing_h"] == "swing"
    assert read(HvacState(True, "cool", 22.0))["swing_h"] == "off"


def test_power_toggle_without_previous_is_the_target_power():
    # A fresh IRac has no previous state: setPowerToggle(on).
    assert read(HvacState(True, "heat", 20.0))["power_toggle"] is True
    assert read(HvacState(False, "heat", 20.0))["power_toggle"] is False


@pytest.mark.parametrize(
    "before, after, toggle",
    [
        (True, True, False),
        (True, False, True),
        (False, False, False),
        (False, True, True),
    ],
)
def test_power_toggle_with_previous_toggles_on_change(before, after, toggle):
    # As the C path from a persistent IRac: handleToggles XORs the power
    # for PANASONIC_AC32 (checked in cpath_check.py).
    previous = HvacState(before, "cool", 22.0)
    target = HvacState(after, "cool", 22.0)
    assert read(target, previous)["power_toggle"] is toggle


def test_encode_passes_previous_to_the_toggle():
    dev = device()
    on = HvacState(True, "cool", 22.0)
    assert dev.encode(None, on).signal != dev.encode(on, on).signal


@pytest.mark.parametrize("model", PANASONIC_AC32_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("panasonic", model), PanasonicAc32Device)


@pytest.mark.parametrize("model", PANASONIC_AC32_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.panasonic import Panasonic32

    legacy = LegacyDevice("panasonic", model, Panasonic32)
    assert PanasonicAc32Device("panasonic", model).capabilities == legacy.capabilities


def test_every_panasonic32_model_is_ported():
    from pyhvac.plugins.panasonic import Panasonic32, PluginObject

    models = {m for m, cls in PluginObject.MODELS.items() if cls is Panasonic32}
    assert models == set(PANASONIC_AC32_MODELS)


@pytest.mark.parametrize(
    "key, value, field",
    [
        ("swing", "90°", "swing_v"),
        ("swing", "60°", "swing_v"),
        ("hswing", "on", "swing_h"),
    ],
)
def test_undeclared_deviation_is_reported(key, value, field):
    dev = device()
    record = next(
        r for r in load_oracle("PANASONIC_AC32") if r["state"].get(key) == value
    )
    with pytest.raises(AssertionError, match=field):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("PANASONIC_AC32")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:3], DEFECTS)
