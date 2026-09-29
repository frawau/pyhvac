import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac.protocols.mitsubishi_heavy import (
    MITSUBISHI_HEAVY88,
    MITSUBISHI_HEAVY88_LAYOUT,
    MITSUBISHI_HEAVY88_MODELS,
    MitsubishiHeavy88Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Mitsubishi88 values here:
# - IRac::mitsubishiHeavy88 calls setFan(convertFan(fan)), then setTurbo(turbo)
#   and setEcono(econo). With powerful/economy off, they reset the
#   kMitsubishiHeavy88FanTurbo (kMax, "highest") and kMitsubishiHeavy88FanEcono
#   (kMin, "lowest") that convertFan returned to kMitsubishiHeavy88FanAuto.
#   A state with no fan at all is IRac's default, auto, which the port now
#   offers and sends as auto too.
# - the legacy glue maps "90°" to kHigh (convertSwingV: High) and "60°" to
#   kUpperMiddle, which convertSwingV has no case for (Off). The port counts
#   the positions down from the topmost documented one (Highest).
FAN_LOWEST = Defect("fan", "1", "auto", "IRac setEcono(false) resets Econo: auto")
FAN_HIGHEST = Defect("fan", "5", "auto", "IRac setTurbo(false) resets Turbo: auto")
SWING_1 = Defect("swing_v", "1", "2", "C sends High (kHigh) for '90°'")
SWING_2 = Defect("swing_v", "2", "off", "C has no upper-middle case: sends off")
DEFECTS = (FAN_LOWEST, FAN_HIGHEST, SWING_1, SWING_2)

# ir_MitsubishiHeavy_test.cpp (ZjsSyntheticExample): power on, dry, 25 C,
# fan auto, swing V off, swing H LeftRight.
SYNTHETIC_EXAMPLE = bytes.fromhex("ad513cd92648b700ff8a75")


def device(model="RKX502A001C remote"):
    return MitsubishiHeavy88Device("mitsubishi_heavy_industries", model)


def read(state):
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(state), ())
    return MITSUBISHI_HEAVY88_LAYOUT.read(frame.data)


def raw(state, field):
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(state), ())
    return MITSUBISHI_HEAVY88_LAYOUT.read_raw(frame.data, field)


@pytest.mark.parametrize("record", oracle_params("MITSUBISHI_HEAVY_88"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("MITSUBISHI_HEAVY_88"):
        state = state_from_record(dev, record["state"])
        (frame,) = dev.frames(None, state, ())
        values = MITSUBISHI_HEAVY88_LAYOUT.read(frame.data)
        assert MITSUBISHI_HEAVY88_LAYOUT.build(**values) == bytearray(frame.data)
        assert MITSUBISHI_HEAVY88_LAYOUT.checksum.check(frame.data)


def test_the_synthetic_capture_reads_as_documented():
    layout = MITSUBISHI_HEAVY88_LAYOUT
    assert layout.checksum.check(SYNTHETIC_EXAMPLE)
    values = layout.read(SYNTHETIC_EXAMPLE)
    assert values == {
        "swing_v": "off",
        "swing_h": "7",  # kMitsubishiHeavy88SwingHLeftRight
        "clean": 0,
        "fan": "auto",
        "mode": "dry",
        "power": 1,
        "temperature": 25 - 17,
    }


def test_the_synthetic_capture_is_reproduced():
    # Fan auto and swing H LeftRight, which the legacy entity lacked.
    state = HvacState(True, "dry", 25.0, fan="auto", swing_v="off", swing_h="7")
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(state), ())
    assert frame.data == SYNTHETIC_EXAMPLE


def test_capabilities_are_the_documented_values():
    caps = device().capabilities
    # kMitsubishiHeavyMinTemp / kMitsubishiHeavyMaxTemp, whole degrees.
    assert (caps.temperature.min, caps.temperature.max) == (17.0, 31.0)
    # setMode accepts kMitsubishiHeavyFan.
    assert caps.modes == ("auto", "cool", "dry", "fan", "heat")
    # kMitsubishiHeavy88Fan{Auto,Econo,Low,Med,High,Turbo}.
    assert caps.fan.values == ("auto", "1", "2", "3", "4", "5")
    assert caps.swing_v.values == ("off", "auto", "1", "2", "3", "4", "5")
    assert caps.swing_h.values == (("off", "auto") + tuple(str(n) for n in range(1, 9)))
    assert caps.swing_h.label("8") == "3D"
    assert set(caps.features) == {"cleaning", "powerful", "economy"}


def test_split_swing_fields_use_the_struct_bits():
    # SwingV5 = byte 5 bit 1, SwingV7 = byte 7 bits 3-4;
    # SwingH1 = byte 5 bits 2-3, SwingH2 = byte 5 bits 6-7.
    layout = MITSUBISHI_HEAVY88_LAYOUT
    assert tuple(layout.fields["swing_v"].bits) == (41, 59, 60)
    assert tuple(layout.fields["swing_h"].bits) == (42, 43, 46, 47)
    lowest = layout.build(swing_v="5")  # 0b111
    assert (lowest[5] & 0x02, lowest[7] & 0x18) == (0x02, 0x18)
    right = layout.build(swing_h="4")  # 0b1101: SwingH1 = 0b01, SwingH2 = 0b11
    assert right[5] & 0xCC == 0b11000100


def test_no_field_overlaps_the_inverted_bytes():
    parity = {8 * b + i for b in (4, 6, 8, 10) for i in range(8)}
    for name, field in MITSUBISHI_HEAVY88_LAYOUT.fields.items():
        assert not parity & set(field.bits), name


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan", "heat"])
def test_off_carries_mode_auto(mode):
    # IRac passes mode "off"; convertMode maps it to kMitsubishiHeavyAuto.
    for t in (17.0, 24.0, 31.0):
        values = read(HvacState(False, mode, t))
        assert (values["power"], values["mode"], values["temperature"]) == (
            0,
            "auto",
            int(t) - 17,
        )


def test_mode_codes():
    # kMitsubishiHeavy{Auto,Cool,Dry,Fan,Heat}; fan is new (setMode takes it).
    for mode, code in (
        ("auto", 0),
        ("cool", 1),
        ("dry", 2),
        ("fan", 3),
        ("heat", 4),
    ):
        assert raw(HvacState(True, mode, 22.0), "mode") == code


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan", "heat"])
def test_setpoint_is_whole_degrees_offset_from_17(mode):
    assert read(HvacState(True, mode, 10.0))["temperature"] == 0
    assert read(HvacState(True, mode, 21.0))["temperature"] == 4
    assert read(HvacState(True, mode, 21.5))["temperature"] == 4
    assert read(HvacState(True, mode, 40.0))["temperature"] == 14


@pytest.mark.parametrize(
    "fan, code",
    [("auto", 0), ("1", 7), ("2", 2), ("3", 3), ("4", 4), ("5", 6)],
)
def test_every_fan_level_uses_its_documented_code(fan, code):
    # convertFan: kAuto -> Auto, kMin -> Econo, kLow, kMedium, kHigh -> High,
    # kMax -> Turbo. Auto and High are new.
    assert raw(HvacState(True, "cool", 22.0, fan=fan), "fan") == code


@pytest.mark.parametrize("fan", ["auto", "1", "2", "3", "4", "5"])
def test_powerful_and_economy_are_fan_codes(fan):
    # setTurbo(true) stores Turbo, then setEcono(true) stores Econo: economy
    # wins over powerful, and both win over the requested speed.
    def code(powerful, economy):
        features = {"powerful": powerful, "economy": economy}
        return raw(HvacState(True, "cool", 22.0, fan=fan, features=features), "fan")

    assert code(True, False) == 6
    assert code(False, True) == 7
    assert code(True, True) == 7


def test_cleaning_sets_the_clean_bit():
    on = HvacState(True, "cool", 22.0, features={"cleaning": True})
    assert (read(on)["clean"], read(HvacState(True, "cool", 22.0))["clean"]) == (
        1,
        0,
    )


@pytest.mark.parametrize(
    "position, code",
    [("off", 0), ("auto", 4), ("1", 6), ("2", 1), ("3", 3), ("4", 5), ("5", 7)],
)
def test_vertical_swing_counts_down_from_highest(position, code):
    assert raw(HvacState(True, "cool", 22.0, swing_v=position), "swing_v") == code


@pytest.mark.parametrize(
    "position, code",
    [
        ("off", 0),
        ("auto", 8),
        ("1", 1),
        ("2", 5),
        ("3", 9),
        ("4", 13),
        ("5", 2),
        ("6", 0b1010),  # kMitsubishiHeavy88SwingHRightLeft
        ("7", 0b0110),  # kMitsubishiHeavy88SwingHLeftRight
        ("8", 0b1110),  # kMitsubishiHeavy88SwingH3D
    ],
)
def test_horizontal_swing_runs_left_to_right(position, code):
    assert raw(HvacState(True, "cool", 22.0, swing_h=position), "swing_h") == code


def test_previous_is_ignored():
    dev = device()
    on = HvacState(True, "cool", 22.0, swing_v="auto")
    off = HvacState(False, "heat", 30.0)
    assert dev.encode(off, on).signal == dev.encode(None, on).signal
    assert dev.encode(on, on).signal == dev.encode(None, on).signal


def test_message_shape():
    signal = device().encode(None, HvacState(True, "cool", 22.0)).signal
    assert signal.carrier == 38000
    pulses = signal.pulses
    assert pulses[:2] == (3140, 1630)
    assert pulses[2:4] == (370, 420)  # 0xAD sent LSB first: a one first
    assert pulses[4:6] == (370, 1220)
    assert pulses[-2:] == (370, 100000)
    assert len(pulses) == 2 + 2 * 88 + 2


def _record(**state):
    return next(
        r
        for r in load_oracle("MITSUBISHI_HEAVY_88")
        if all(r["state"].get(k) == v for k, v in state.items())
    )


@pytest.mark.parametrize(
    "state, defect",
    [
        ({"mode": "cool", "fan": "lowest", "swing": "off"}, FAN_LOWEST),
        ({"mode": "cool", "fan": "highest", "swing": "off"}, FAN_HIGHEST),
        ({"mode": "cool", "fan": "low", "swing": "90°"}, SWING_1),
        ({"mode": "cool", "fan": "low", "swing": "60°"}, SWING_2),
    ],
)
def test_undeclared_deviation_is_reported(state, defect):
    dev = device()
    record = _record(**state)
    assert_matches_oracle(dev, record, dev.LAYOUTS, (defect,))
    others = tuple(d for d in DEFECTS if d is not defect)
    with pytest.raises(AssertionError, match=f"'{defect.field}'"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=others)


def test_layouts_must_cover_every_frame():
    dev = device()
    record = _record(mode="cool", fan="lowest", swing="off")
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)


# No real capture in ir_MitsubishiHeavy_test.cpp needs it, but
# decodeMitsubishiHeavy matches with _tolerance (25 %) and no mark excess.
def test_decode_tolerance_is_the_c_decoders():
    assert (MITSUBISHI_HEAVY88.tolerance, MITSUBISHI_HEAVY88.mark_excess) == (0.25, 0)
