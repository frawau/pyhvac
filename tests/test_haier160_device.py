import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac.fields import Sum8
from pyhvac.ir.codec import decode
from pyhvac.protocols.haier import (
    HAIER160,
    HAIER160_LAYOUT,
    HAIER160_MODELS,
    Haier160Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented HaierAc160Protocol here:
# - sleep: IRGHVAC.build_ircode's key map has no "sleep", so IRac's sleep
#   stays -1 and IRac::haier160's setSleep(sleep >= 0) always clears Sleep
#   (byte 8 bit 7). The port sets it.
SLEEP = Defect("sleep", 1, 0, "legacy glue never passes sleep")
DEFECTS = (SLEEP,)

# ir_Haier_test.cpp, TestDecodeHaierAC160.RealExample (issue #1804): power
# on, cool, 26 C, fan low, swing(V) auto, button Power.
REAL_EXAMPLE = bytes.fromhex("a6ac0000406000200000000005 17 b50060000015")
# TestHaierAC160Class.Light: the same settings with the Light button.
LIGHT_PRESS = bytes.fromhex("a6ac00004060002000000000 15 27 b50060000015")
# TestHaierAC160Class.CleanMode: clean on, pressed with the Clean button.
CLEAN_ON = bytes.fromhex("a6ac00004060002000001000 19 3b b54060000055")

ALL_FEATURES = ("purifier", "sleep", "powerful", "quiet", "cleaning", "light")


def device(model="KFR-26GW/83@UI-Ge"):
    return Haier160Device("haier", model)


def frame(state, previous=None):
    dev = device()
    if previous is not None:
        previous = dev.normalise(previous)
    (main,) = dev.frames(previous, dev.normalise(state), ())
    return main.data


def read(state, previous=None):
    return HAIER160_LAYOUT.read(frame(state, previous))


def features(**on):
    return {k: True for k in on}


@pytest.mark.parametrize("record", oracle_params("HAIER_AC160"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("HAIER_AC160"):
        state = state_from_record(dev, record["state"])
        (main,) = dev.frames(None, state, ())
        values = HAIER160_LAYOUT.read(main.data)
        assert HAIER160_LAYOUT.build(**values) == bytearray(main.data)


def test_every_oracle_frame_has_both_section_sums():
    # IRHaierAC160::checksum: sumBytes(raw, 13) at 13, sumBytes(raw + 14, 5)
    # at 19. (portkit checksum only tries the last two bytes, so it finds
    # Sum2 but not Sum.)
    for record in load_oracle("HAIER_AC160"):
        (main,) = decode(HAIER160, record["pulses"], expected=["main"])
        assert Sum8(0, 13, 13).check(main.data)
        assert Sum8(14, 19, 19).check(main.data)
        assert HAIER160_LAYOUT.checksum.check(main.data)


def test_checksum_bytes_are_not_fields():
    assert HAIER160_LAYOUT.checksum.positions() == {13, 19}
    for name, f in HAIER160_LAYOUT.fields.items():
        assert not {b // 8 for b in f.bits} & {13, 19}, name


def test_real_example_is_reproduced():
    state = HvacState(True, "cool", 26.0, fan="1", swing_v="auto")
    assert frame(state) == REAL_EXAMPLE


def test_light_press_capture_is_reproduced_without_previous():
    # A fresh IRac: prevlight is its default state's light (off), so light
    # on presses kHaierAc160ButtonLight.
    state = HvacState(True, "cool", 26.0, fan="1", swing_v="auto")
    lit = HvacState(
        True, "cool", 26.0, fan="1", swing_v="auto", features={"light": True}
    )
    assert frame(lit) == LIGHT_PRESS
    assert frame(lit, previous=state) == LIGHT_PRESS


def test_clean_capture_matches_except_the_button():
    # The remote sends the Clean button; IRac::haier160 calls setClean
    # before setPower, so the C path (and the port) send Power.
    state = HvacState(
        True, "cool", 26.0, fan="1", swing_v="auto", features={"cleaning": True}
    )
    data = frame(state)
    assert HAIER160_LAYOUT.read(data) == {
        **HAIER160_LAYOUT.read(CLEAN_ON),
        "button": "power",
    }
    assert HAIER160_LAYOUT.read(CLEAN_ON)["button"] == "clean"


def test_skeleton_is_the_reset_state_with_fields_cleared():
    record = load_oracle("HAIER_AC160")[0]
    assert record["state"] == {
        "fan": "auto",
        "mode": "off",
        "swing": "off",
        "temperature": 16,
    }
    (main,) = decode(HAIER160, record["pulses"], expected=["main"])
    data = HAIER160_LAYOUT.build(button="power", fan="auto", temperature=16)
    assert bytes(data) == main.data


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat", "fan"])
@pytest.mark.parametrize("temp", [16.0, 23.0, 30.0])
def test_off_carries_mode_auto_in_every_mode(mode, temp):
    # IRac passes mode "off"; convertMode maps it to kHaierAcYrw02Auto,
    # which also clears turbo, quiet and AuxHeating.
    state = HvacState(False, mode, temp, features=features(powerful=1, quiet=1))
    values = read(state)
    assert (values["power"], values["mode"], values["temperature"]) == (
        0,
        "auto",
        int(temp),
    )
    assert (values["turbo"], values["quiet"], values["aux_heating"]) == (0, 0, 0)
    assert values["button"] == "power"


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat", "fan"])
def test_aux_heating_follows_heat_mode(mode):
    # IRHaierAC160::setMode: AuxHeating = (Mode == kHaierAcYrw02Heat).
    assert read(HvacState(True, mode, 24.0))["aux_heating"] == (mode == "heat")


def test_setpoint_is_clamped_to_16_30():
    assert read(HvacState(True, "cool", 10.0))["temperature"] == 16
    assert read(HvacState(True, "heat", 40.0))["temperature"] == 30
    assert read(HvacState(True, "cool", 22.0))["use_fahrenheit"] == 0


@pytest.mark.parametrize(
    "fan, raw, raw2",
    [("auto", 0b101, 0), ("1", 0b011, 0b011), ("2", 0b010, 0b010), ("3", 0b001, 1)],
)
def test_every_fan_level_and_fan2(fan, raw, raw2):
    # setFan: Fan2 is 0 for auto, else the Fan code.
    data = frame(HvacState(True, "cool", 24.0, fan=fan))
    assert HAIER160_LAYOUT.read_raw(data, "fan") == raw
    assert HAIER160_LAYOUT.read_raw(data, "fan2") == raw2


@pytest.mark.parametrize(
    "swing, raw",
    [
        ("off", 0b0000),
        ("auto", 0b1100),
        ("1", 0b0001),  # ceiling: kHighest -> Top
        ("2", 0b0010),  # kHaierAc160SwingVHighest (not reached by convertSwingV)
        ("3", 0b0100),  # 90°: kHigh -> High
        ("4", 0b0110),  # 45°: kMiddle -> Middle
        ("5", 0b1000),  # 30°: kLow -> Low
        ("6", 0b0011),  # 0°: kLowest -> Lowest
    ],
)
def test_every_swing_value(swing, raw):
    data = frame(HvacState(True, "cool", 24.0, swing_v=swing))
    assert HAIER160_LAYOUT.read_raw(data, "swing_v") == raw


@pytest.mark.parametrize("mode", ["cool", "heat"])
def test_turbo_and_quiet_in_cool_and_heat(mode):
    # setQuiet(quiet), then setTurbo(turbo): turbo on clears Quiet.
    assert (
        read(HvacState(True, mode, 24.0, features=features(powerful=1)))["turbo"] == 1
    )
    values = read(HvacState(True, mode, 24.0, features=features(quiet=1)))
    assert (values["turbo"], values["quiet"]) == (0, 1)
    values = read(HvacState(True, mode, 24.0, features=features(powerful=1, quiet=1)))
    assert (values["turbo"], values["quiet"]) == (1, 0)


@pytest.mark.parametrize("mode", ["auto", "dry", "fan"])
def test_no_turbo_or_quiet_outside_cool_and_heat(mode):
    values = read(HvacState(True, mode, 24.0, features=features(powerful=1, quiet=1)))
    assert (values["turbo"], values["quiet"]) == (0, 0)


def test_purifier_cleaning_and_sleep_bits():
    values = read(
        HvacState(
            True, "cool", 24.0, features=features(purifier=1, cleaning=1, sleep=1)
        )
    )
    assert (values["health"], values["clean"], values["clean2"]) == (1, 1, 1)
    assert values["sleep"] == 1  # the documented Sleep bit (a Defect vs C)
    assert values["button"] == "power"


def test_every_feature_leaves_the_power_button():
    # Every IRac setter writes the button, but setPower comes last (before
    # the light toggle).
    state = HvacState(
        True,
        "cool",
        24.0,
        features={k: True for k in ALL_FEATURES if k != "light"},
    )
    assert read(state)["button"] == "power"


def test_light_without_previous_presses_the_light_button():
    assert read(HvacState(True, "cool", 24.0))["button"] == "power"
    lit = HvacState(True, "cool", 24.0, features=features(light=1))
    assert read(lit)["button"] == "light"
    assert frame(lit)[12] == 0x15


@pytest.mark.parametrize(
    "before, after, button",
    [
        (False, False, "power"),
        (False, True, "light"),
        (True, True, "power"),
        (True, False, "light"),
    ],
)
def test_light_button_with_previous_only_on_change(before, after, button):
    # IRac::sendAc: setLightToggle(light ^ prev->light).
    previous = HvacState(True, "cool", 24.0, features={"light": before})
    target = HvacState(True, "heat", 25.0, features={"light": after})
    assert read(target, previous)["button"] == button


def test_encode_passes_previous_to_the_light_button():
    dev = device()
    lit = HvacState(True, "cool", 22.0, features=features(light=1))
    assert dev.encode(None, lit).signal != dev.encode(lit, lit).signal


def test_message_shape():
    dev = device()
    pulses = dev.encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:4] == (3000, 3000, 3000, 4300)
    assert pulses[-2:] == (520, 150000)
    assert len(pulses) == 4 + 2 * 160 + 2


def test_swing_v_offers_every_documented_position():
    # ir_Haier.h kHaierAc160SwingV{Off,Auto,Top,Highest,High,Middle,Low,
    # Lowest}: Highest (0b0010) is new, the legacy entity had the other seven.
    swing_v = device().capabilities.swing_v
    assert swing_v.values == ("off", "auto", "1", "2", "3", "4", "5", "6")
    assert swing_v.label("2") == "highest"


def test_legacy_swing_labels_keep_their_positions():
    # The oracle's old-vocabulary swings still reach the same codes.
    dev = device()
    for label, raw in (
        ("ceiling", 0b0001),
        ("90°", 0b0100),
        ("45°", 0b0110),
        ("30°", 0b1000),
        ("0°", 0b0011),
    ):
        state = state_from_record(dev, {"mode": "cool", "swing": label})
        assert HAIER160_LAYOUT.read_raw(frame(state), "swing_v") == raw


def test_capabilities():
    caps = device().capabilities
    assert caps.modes == ("auto", "cool", "dry", "heat", "fan")
    assert (caps.temperature.min, caps.temperature.max) == (16.0, 30.0)
    assert caps.fan.values == ("auto", "1", "2", "3")
    assert caps.swing_h is None  # IRHaierAC160 has no SwingH setter
    assert set(caps.features) == set(ALL_FEATURES)


def test_undeclared_sleep_deviation_is_reported():
    dev = device()
    record = next(
        r for r in load_oracle("HAIER_AC160") if r["state"].get("sleep") == "on"
    )
    with pytest.raises(AssertionError, match="sleep"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())
