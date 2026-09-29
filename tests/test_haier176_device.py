import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.fields import Sum8
from pyhvac.ir.codec import decode
from pyhvac.plugins.haier import (
    HAIER176,
    HAIER176_LAYOUT,
    HAIER176_MODELS,
    Haier176Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Haier176 values here:
# - the old glue (IRGHVAC.build_ircode) has no "sleep" key, so IRac's sleep
#   stays -1 and IRac::haier176's setSleep(sleep >= 0) clears the Sleep bit
#   (byte 8 bit 7). The port sends the documented bit.
DEFECTS = (Defect("sleep", 1, 0, "C glue never passes sleep: bit clear"),)

LEGACY_CLASS = {"A": "Haier176A", "B": "Haier176B"}


def device(model="V9014557 M47 8D remote"):
    return Haier176Device("haier", model)


def device_for(record):
    return device(record["model"])


def with_hswing(record):
    # A record without "hswing" leaves IRac's swingh at kOff, which
    # IRHaierAC176::convertSwingH maps to its default, SwingHMiddle: canonical
    # "3" (the oracle records match only so). The port has no
    # "off" swing_h (the legacy entity has none), so the record is read as
    # "middle".
    if "hswing" in record["state"]:
        return record
    return {**record, "state": {**record["state"], "hswing": "middle"}}


def frame(state, previous=None, model="V9014557 M47 8D remote"):
    dev = device(model)
    if previous is not None:
        previous = dev.normalise(previous)
    (main,) = dev.frames(previous, dev.normalise(state), ())
    return main.data


def read(state, previous=None, model="V9014557 M47 8D remote"):
    return HAIER176_LAYOUT.read(frame(state, previous, model))


@pytest.mark.parametrize("record", oracle_params("HAIER_AC176"))
def test_matches_c_library(record):
    dev = device_for(record)
    assert_matches_oracle(dev, with_hswing(record), dev.LAYOUTS, DEFECTS)


def test_oracle_covers_both_variants():
    models = {r["model"] for r in load_oracle("HAIER_AC176")}
    assert {HAIER176_MODELS[m] for m in models} == {"A", "B"}


def test_layout_round_trips_every_oracle_state():
    for record in load_oracle("HAIER_AC176"):
        dev = device_for(record)
        state = state_from_record(dev, with_hswing(record)["state"])
        (main,) = dev.frames(None, state, ())
        values = HAIER176_LAYOUT.read(main.data)
        assert HAIER176_LAYOUT.build(**values) == bytearray(main.data)


def test_every_oracle_frame_has_both_section_sums():
    # IRHaierAC176::checksum: Sum over bytes 0-12 at 13, Sum2 over 14-20 at 21.
    # portkit checksum only searches the last two bytes, so Sum is pinned here.
    for record in load_oracle("HAIER_AC176"):
        (main,) = decode(HAIER176, record["pulses"], expected=["main"])
        assert Sum8(0, 13, 13).check(main.data)
        assert Sum8(14, 21, 21).check(main.data)
        assert HAIER176_LAYOUT.checksum.check(main.data)


def test_no_field_sits_in_a_checksum_byte():
    sums = HAIER176_LAYOUT.checksum.positions()
    assert sums == {13, 21}
    for name, f in HAIER176_LAYOUT.fields.items():
        assert not {b // 8 for b in f.bits} & sums, name


def test_real_capture_decodes():
    # TestDecodeHaierAC176.RealExample (issue 1480), a real remote: the
    # port's timings decode it to the expected state.
    raw = (
        "3096 2948 3048 4388 588 1610 614 498 586 1612 612 500 612 500 586 1610 "
        "588 1612 612 502 586 1612 612 500 612 500 614 500 612 498 586 1610 586 "
        "1612 612 502 612 500 612 500 612 500 612 500 612 500 612 500 612 500 "
        "612 504 612 500 612 500 612 500 612 500 612 500 612 500 612 500 612 502 "
        "614 498 586 1612 612 500 612 500 612 500 612 500 612 500 612 502 586 "
        "1612 612 500 586 1610 612 500 612 498 612 500 614 478 634 502 612 500 "
        "612 500 612 500 612 500 612 500 612 500 612 498 614 504 612 500 614 500 "
        "586 1612 612 500 612 500 612 500 612 500 612 502 612 500 612 500 612 "
        "500 612 500 612 500 612 500 612 500 612 504 614 500 612 500 612 498 614 "
        "500 612 500 612 500 612 500 612 482 632 500 612 502 610 500 614 500 612 "
        "500 612 500 612 480 632 504 612 480 632 500 612 500 612 480 632 500 612 "
        "500 612 500 612 502 612 500 612 500 612 500 612 500 612 500 586 1612 "
        "612 500 586 1616 612 500 612 500 586 1610 588 1612 612 502 612 500 614 "
        "498 586 1614 586 1612 612 500 586 1610 586 1592 632 498 586 1610 588 "
        "1610 586 1614 614 500 612 480 632 500 612 500 612 500 612 500 614 498 "
        "612 500 614 500 614 500 612 500 612 500 614 498 614 498 614 500 612 504 "
        "612 500 612 500 612 500 612 498 612 502 612 500 614 498 612 502 612 500 "
        "612 498 614 500 612 500 612 500 612 500 612 500 614 502 612 500 614 478 "
        "634 498 614 500 612 500 612 500 612 500 612 482 634 500 612 500 612 500 "
        "612 500 614 498 614 500 612 480 632 502 586 1610 614 478 608 1610 588 "
        "1610 612 498 586 1610 588 1610 586 1606 612"
    )
    pulses = [int(x) for x in raw.split()] + [150000]
    (main,) = decode(HAIER176, pulses, expected=["main"])
    assert main.data == bytes(
        [0xA6, 0x86, 0x00, 0x00, 0x40, 0xA0, 0x00, 0x20, 0x00, 0x00, 0x00]
        + [0x00, 0x05, 0x31, 0xB7, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xB7]
    )
    assert HAIER176_LAYOUT.checksum.check(main.data)


def test_real_model_b_capture_except_its_button():
    # TestHaierAC176Class.Models, "setmodelb": a real V9014557-B message in
    # fan mode, 24 °C, fan low, swing Middle, pressed with the C/F button.
    # The port reproduces it except Button, which IRac always sets to Power.
    capture = bytes(
        [0x59, 0x82, 0x00, 0x00, 0x40, 0x60, 0x00, 0xC0, 0x00, 0x00, 0x00]
        + [0x00, 0x1A, 0x55, 0xB7, 0x00, 0xC0, 0x00, 0x00, 0x00, 0x00, 0x77]
    )
    state = HvacState(True, "fan", 24.0, fan="1", swing_v="2", swing_h="3")
    ours = bytearray(frame(state, model="generic 176 code b"))
    assert HAIER176_LAYOUT.read(ours)["button"] == "power"
    HAIER176_LAYOUT.write_raw(ours, "button", 0b11010)  # kHaierAcYrw02ButtonCFAB
    HAIER176_LAYOUT.checksum.apply(ours)
    assert bytes(ours) == capture


@pytest.mark.parametrize(
    "model, variant, byte0",
    [
        ("V9014557 M47 8D remote", "A", 0xA6),
        ("Daichi D-H", "A", 0xA6),
        ("generic 176 code a", "A", 0xA6),
        ("generic 176 code b", "B", 0x59),
    ],
)
def test_variant_comes_from_the_model(model, variant, byte0):
    assert device(model).variant == variant
    assert frame(HvacState(True, "cool", 22.0), model=model)[0] == byte0


def test_unknown_model_gets_variant_a_and_bad_variant_raises():
    assert Haier176Device("haier", "whatever").variant == "A"
    assert Haier176Device("haier", "whatever", variant="B").variant == "B"
    with pytest.raises(ValueError):
        Haier176Device("haier", "whatever", variant="C")


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat", "fan"])
@pytest.mark.parametrize("temp", [16.0, 23.0, 30.0])
def test_off_carries_mode_auto_in_every_mode(mode, temp):
    # IRac passes mode "off"; IRHaierAC176::convertMode maps it to auto.
    values = read(HvacState(False, mode, temp, fan="3"))
    assert (values["power"], values["mode"], values["temperature"]) == (
        0,
        "auto",
        int(temp),
    )
    assert values["fan"] == "3"
    assert values["button"] == "power"


def test_setpoint_is_clamped_to_16_30():
    assert read(HvacState(True, "cool", 10.0))["temperature"] == 16
    assert read(HvacState(True, "heat", 40.0))["temperature"] == 30


@pytest.mark.parametrize("temp", range(16, 31))
def test_every_setpoint(temp):
    assert frame(HvacState(True, "cool", float(temp)))[1] >> 4 == temp - 16


@pytest.mark.parametrize(
    "fan, raw, fan2",
    [("auto", 5, 0), ("1", 3, 3), ("2", 2, 2), ("3", 1, 1)],
)
@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat", "fan"])
def test_every_fan_level_and_fan2(mode, fan, raw, fan2):
    # setFan: Fan2 is 0 for FanAuto, otherwise the Fan code; no mode limits.
    data = frame(HvacState(True, mode, 24.0, fan=fan))
    assert HAIER176_LAYOUT.read_raw(data, "fan") == raw
    assert HAIER176_LAYOUT.read_raw(data, "fan2") == fan2


@pytest.mark.parametrize(
    "swing, other, heat",
    [
        ("off", 0x0, 0x0),
        ("auto", 0xC, 0xC),
        ("1", 0x1, 0x1),  # ceiling: Top
        ("2", 0x2, 0x3),  # 45°: Middle, Bottom in heat
        ("3", 0xA, 0xA),  # 30°: Down
        ("4", 0x2, 0x3),  # 0°: Bottom, only in heat, else Middle
    ],
)
def test_swing_v_per_mode(swing, other, heat):
    for mode in ("auto", "cool", "dry", "fan"):
        data = frame(HvacState(True, mode, 24.0, swing_v=swing))
        assert HAIER176_LAYOUT.read_raw(data, "swing_v") == other, mode
    data = frame(HvacState(True, "heat", 24.0, swing_v=swing))
    assert HAIER176_LAYOUT.read_raw(data, "swing_v") == heat
    # An off message carries mode auto, so heat's Bottom becomes Middle.
    data = frame(HvacState(False, "heat", 24.0, swing_v=swing))
    assert HAIER176_LAYOUT.read_raw(data, "swing_v") == other


@pytest.mark.parametrize(
    "swing_h, raw",
    [("auto", 7), ("1", 3), ("2", 4), ("3", 0), ("4", 5), ("5", 6)],
)
def test_every_swing_h_value(swing_h, raw):
    data = frame(HvacState(True, "cool", 22.0, swing_h=swing_h))
    assert HAIER176_LAYOUT.read_raw(data, "swing_h") == raw


@pytest.mark.parametrize(
    "mode, powerful, quiet, turbo_bit, quiet_bit",
    [
        ("cool", True, False, 1, 0),
        ("cool", False, True, 0, 1),
        ("cool", True, True, 1, 0),  # setTurbo(true) comes last, clears quiet
        ("heat", True, False, 1, 0),
        ("heat", False, True, 0, 1),
        ("heat", True, True, 1, 0),
        ("auto", True, True, 0, 0),  # only in cool and heat
        ("dry", True, True, 0, 0),
        ("fan", True, True, 0, 0),
    ],
)
def test_turbo_and_quiet_only_in_cool_and_heat(
    mode, powerful, quiet, turbo_bit, quiet_bit
):
    features = {"powerful": powerful, "quiet": quiet}
    values = read(HvacState(True, mode, 24.0, features=features))
    assert (values["turbo"], values["quiet"]) == (turbo_bit, quiet_bit)
    off = read(HvacState(False, mode, 24.0, features=features))
    assert (off["turbo"], off["quiet"]) == (0, 0)  # an off message is in auto


@pytest.mark.parametrize("mode", ["auto", "cool", "heat"])
def test_purifier_sets_health_in_every_mode(mode):
    assert read(HvacState(True, mode, 24.0))["health"] == 0
    on = HvacState(True, mode, 24.0, features={"purifier": True})
    assert read(on)["health"] == 1
    off = HvacState(False, mode, 24.0, features={"purifier": True})
    assert read(off)["health"] == 1


def test_sleep_sends_the_documented_bit():
    assert read(HvacState(True, "cool", 24.0))["sleep"] == 0
    on = HvacState(True, "cool", 24.0, features={"sleep": True})
    assert read(on)["sleep"] == 1
    assert frame(on)[8] == 0x80


@pytest.mark.parametrize("power", [True, False])
@pytest.mark.parametrize("mode", ["auto", "cool", "heat"])
def test_button_is_always_power(power, mode):
    state = HvacState(
        power,
        mode,
        24.0,
        fan="2",
        swing_v="1",
        swing_h="2",
        features={"purifier": True, "powerful": True, "sleep": True},
    )
    assert read(state)["button"] == "power"
    assert frame(state)[12] == 0x05


def test_previous_is_ignored():
    # No toggle bits: IRac::handleToggles has no Haier case and
    # IRac::haier176 takes no previous state.
    dev = device()
    target = HvacState(True, "cool", 22.0, swing_v="auto", swing_h="1")
    for previous in (
        None,
        target,
        HvacState(False, "heat", 30.0),
        HvacState(True, "cool", 22.0, swing_v="off", swing_h="auto"),
    ):
        assert dev.encode(previous, target).signal == dev.encode(None, target).signal


def test_skeleton_is_the_reset_state():
    # The oracle's first record: off, 16 °C, fan auto, swing off (hswing
    # absent: Middle).
    record = load_oracle("HAIER_AC176")[0]
    assert record["state"] == {
        "mode": "off",
        "temperature": 16,
        "fan": "auto",
        "swing": "off",
    }
    (main,) = decode(HAIER176, record["pulses"], expected=["main"])
    data = HAIER176_LAYOUT.build(
        model="A", fan="auto", mode="auto", button="power", swing_h="3"
    )
    assert bytes(data) == main.data


def test_message_shape():
    dev = device()
    pulses = dev.encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:4] == (3000, 3000, 3000, 4300)
    assert pulses[-2:] == (520, 150000)
    assert len(pulses) == 4 + 2 * 176 + 2
    assert dev.encode(None, HvacState(True, "cool", 22.0)).signal.carrier == 38000


@pytest.mark.parametrize("model", HAIER176_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("haier", model), Haier176Device)


@pytest.mark.parametrize("model", HAIER176_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins import haier

    cls = getattr(haier, LEGACY_CLASS[HAIER176_MODELS[model]])
    legacy = LegacyDevice("haier", model, cls)
    assert Haier176Device("haier", model).capabilities == legacy.capabilities


def test_undeclared_deviation_is_reported():
    record = next(
        r for r in load_oracle("HAIER_AC176") if r["state"].get("sleep") == "on"
    )
    dev = device_for(record)
    with pytest.raises(AssertionError, match="sleep"):
        assert_matches_oracle(dev, with_hswing(record), dev.LAYOUTS, defects=())


def test_missing_hswing_is_not_silently_accepted():
    # Read as "auto" (the entity's first value), a record without hswing
    # would differ from C's Middle: the rewrite in with_hswing is needed.
    record = next(r for r in load_oracle("HAIER_AC176") if "hswing" not in r["state"])
    dev = device_for(record)
    with pytest.raises(AssertionError, match="swing_h"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layouts_must_cover_every_frame():
    record = load_oracle("HAIER_AC176")[0]
    dev = device_for(record)
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, with_hswing(record), (), DEFECTS)
