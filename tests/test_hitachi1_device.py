import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.hitachi import (
    HITACHI1_LAYOUT,
    HITACHI1_MODELS,
    Hitachi1Checksum,
    Hitachi1Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Hitachi1 values here:
# - the legacy glue (IRGHVAC.trans_swing/trans_hswing) has no "on" key, so
#   swingv/swingh stay kOff: the SwingV/SwingH bits are never set, and the
#   swing toggle IRac::sendAc derives from them (against a fresh IRac's
#   all-off previous state) is never set either;
# - the legacy glue (IRGHVAC.build_ircode's key map) has no "sleep" key, so
#   sleep stays -1 and IRac::hitachi1 never sends kHitachiAc1Sleep2;
# - IRHitachiAc1::setFan, in heat and fan, returns without storing the
#   requested speed once the current one is not auto, and setMode (called
#   first by IRac::hitachi1) has already forced it to kHitachiAc1FanLow: C
#   sends low for every speed there. The port sends kHitachiAc1FanMed/High.
DEFECTS = (
    Defect("swing_v", "swing", "off", "legacy glue never passes swing on"),
    Defect("swing_h", "swing", "off", "legacy glue never passes hswing on"),
    Defect("swing_toggle", 1, 0, "follows swing_v/swing_h, never passed on"),
    Defect("sleep", 2, 0, "legacy glue never passes sleep"),
    Defect("fan", "2", "1", "IRHitachiAc1::setFan drops medium in heat/fan"),
    Defect("fan", "3", "1", "IRHitachiAc1::setFan drops high in heat/fan"),
)


def device(model="LT0541-HTA remote"):
    return Hitachi1Device("hitachi", model)


def read(state, previous=None, dev=None):
    dev = dev or device()
    (main,) = dev.frames(previous, dev.normalise(state), ())
    return HITACHI1_LAYOUT.read(main.data)


def _device_for(record):
    return Hitachi1Device("hitachi", record["model"])


@pytest.mark.parametrize("record", oracle_params("HITACHI_AC1"))
def test_matches_c_library(record):
    dev = _device_for(record)
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_oracle_covers_both_variants():
    classes = {(r["class"], r["variant"]) for r in load_oracle("HITACHI_AC1")}
    assert classes == {("Hitachi1A", "1"), ("Hitachi1B", "2")}
    for record in load_oracle("HITACHI_AC1"):
        expected = {"Hitachi1A": "A", "Hitachi1B": "B"}[record["class"]]
        assert _device_for(record).variant == expected


def test_layout_round_trips_every_oracle_state():
    for record in load_oracle("HITACHI_AC1"):
        dev = _device_for(record)
        state = state_from_record(dev, record["state"])
        (main,) = dev.frames(None, state, ())
        values = HITACHI1_LAYOUT.read(main.data)
        assert HITACHI1_LAYOUT.build(**values) == bytearray(main.data)


def test_checksum_matches_the_reset_state():
    # IRHitachiAc1::stateReset's known good state, Sum = 0x24.
    data = bytearray.fromhex("b2ae4d91f0e1a4000000006124")
    assert Hitachi1Checksum(5, 12, 12).check(data)
    data[12] = 0
    Hitachi1Checksum(5, 12, 12).apply(data)
    assert data[12] == 0x24


def test_checksum_matches_the_upstream_cool_32_example():
    # ir_Hitachi_test.cpp HumanReadable: cool, 32 °C, auto fan, power on.
    data = bytes.fromhex("b2ae4d91f061cc0000000030" "04")
    assert Hitachi1Checksum(5, 12, 12).check(data)
    dev = device()
    (main,) = dev.frames(None, dev.normalise(HvacState(True, "cool", 32.0)), ())
    assert main.data == data


def test_model_bits_follow_the_variant():
    assert read(HvacState(True, "cool", 22.0))["model"] == "A"
    dev_b = device("generic 1 code b")
    assert read(HvacState(True, "cool", 22.0), dev=dev_b)["model"] == "B"
    explicit = Hitachi1Device("hitachi", "LT0541-HTA remote", variant="B")
    assert read(HvacState(True, "cool", 22.0), dev=explicit)["model"] == "B"
    with pytest.raises(ValueError):
        Hitachi1Device("hitachi", "x", variant="C")


def test_every_model_maps_to_its_variant():
    assert HITACHI1_MODELS == {
        "LT0541-HTA remote": "A",
        "Series VI": "A",
        "KAZE-312KSDP": "A",
        "R-LT0541-HTA/Y.K.1.1-1 V2.3 remote": "A",
        "generic 1 code a": "A",
        "generic 1 code b": "B",
    }
    for model, variant in HITACHI1_MODELS.items():
        assert device(model).variant == variant


@pytest.mark.parametrize("t", range(16, 33))
def test_temperature_is_reversed_offset(t):
    raw = HITACHI1_LAYOUT.build(temperature=t)
    stored = (raw[6] >> 2) & 0x1F
    assert int(f"{stored:05b}"[::-1], 2) + 7 == t
    assert read(HvacState(True, "cool", float(t)))["temperature"] == t


def test_off_carries_mode_auto_at_25_in_every_mode():
    # IRac passes mode "off"; convertMode maps it to auto, and setTemp is a
    # no-op in auto, leaving the reset kHitachiAc1TempAuto.
    dev = device()
    for mode in dev.capabilities.modes:
        for t in (16.0, 32.0):
            for fan in dev.capabilities.fan.values:
                values = read(HvacState(False, mode, t, fan=fan))
                assert (values["mode"], values["temperature"], values["fan"]) == (
                    "auto",
                    25,
                    "auto",
                )
                assert values["power"] == 0


@pytest.mark.parametrize("t", (16.0, 24.0, 32.0))
def test_auto_mode_is_locked_to_25_and_auto_fan(t):
    for fan in ("auto", "1", "2", "3"):
        values = read(HvacState(True, "auto", t, fan=fan))
        assert (values["temperature"], values["fan"]) == (25, "auto")


def test_dry_is_locked_to_low_fan():
    for fan in ("auto", "1", "2", "3"):
        assert read(HvacState(True, "dry", 22.0, fan=fan))["fan"] == "1"


@pytest.mark.parametrize("mode", ("heat", "fan"))
def test_heat_and_fan_replace_auto_fan_with_low(mode):
    assert read(HvacState(True, mode, 22.0, fan="auto"))["fan"] == "1"
    # Documented speeds otherwise (declared Defect: C sends low).
    for fan in ("1", "2", "3"):
        assert read(HvacState(True, mode, 22.0, fan=fan))["fan"] == fan


@pytest.mark.parametrize("fan, raw", [("auto", 1), ("1", 8), ("2", 4), ("3", 2)])
def test_every_fan_level_uses_its_documented_value_in_cool(fan, raw):
    dev = device()
    (main,) = dev.frames(
        None, dev.normalise(HvacState(True, "cool", 22.0, fan=fan)), ()
    )
    assert HITACHI1_LAYOUT.read_raw(main.data, "fan") == raw


@pytest.mark.parametrize("mode", ("auto", "cool"))
def test_sleep_sends_sleep2_in_auto_and_cool(mode):
    on = HvacState(True, mode, 22.0, features={"sleep": True})
    assert read(on)["sleep"] == 2
    assert read(HvacState(True, mode, 22.0))["sleep"] == 0


@pytest.mark.parametrize("mode", ("heat", "dry", "fan"))
def test_sleep_is_off_outside_auto_and_cool(mode):
    assert read(HvacState(True, mode, 22.0, features={"sleep": True}))["sleep"] == 0


def test_sleep_in_an_off_message_follows_mode_auto():
    assert read(HvacState(False, "heat", 22.0, features={"sleep": True}))["sleep"] == 2


def test_swing_bits_are_states():
    values = read(HvacState(True, "cool", 22.0, swing_v="swing"))
    assert (values["swing_v"], values["swing_h"]) == ("swing", "off")
    values = read(HvacState(True, "cool", 22.0, swing_h="swing"))
    assert (values["swing_v"], values["swing_h"]) == ("off", "swing")


def test_toggles_without_previous_compare_against_a_fresh_irac():
    # A fresh IRac's _prev is the stdAc default: power off, swings off.
    on = read(HvacState(True, "cool", 22.0))
    assert (on["power"], on["power_toggle"], on["swing_toggle"]) == (1, 1, 0)
    off = read(HvacState(False, "cool", 22.0))
    assert (off["power"], off["power_toggle"], off["swing_toggle"]) == (0, 0, 0)
    for kw in ({"swing_v": "swing"}, {"swing_h": "swing"}):
        assert read(HvacState(True, "cool", 22.0, **kw))["swing_toggle"] == 1


@pytest.mark.parametrize(
    "before, after, toggle",
    [(True, True, 0), (True, False, 1), (False, False, 0), (False, True, 1)],
)
def test_power_toggle_with_previous_toggles_on_change(before, after, toggle):
    # As IRac::sendAc for HITACHI_AC1: power_toggle = send.power != prev->power.
    previous = HvacState(before, "cool", 22.0)
    values = read(HvacState(after, "cool", 22.0), previous)
    assert (values["power"], values["power_toggle"]) == (int(after), toggle)


@pytest.mark.parametrize(
    "before, after, toggle",
    [
        (("off", "off"), ("off", "off"), 0),
        (("off", "off"), ("swing", "off"), 1),
        (("swing", "off"), ("swing", "off"), 0),
        (("swing", "off"), ("off", "off"), 1),
        (("off", "off"), ("off", "swing"), 1),
        (("swing", "swing"), ("swing", "swing"), 0),
        (("swing", "off"), ("off", "swing"), 1),
    ],
)
def test_swing_toggle_with_previous_toggles_on_change(before, after, toggle):
    # As IRac::sendAc: swingv or swingh differs from the previous state.
    previous = HvacState(True, "cool", 22.0, swing_v=before[0], swing_h=before[1])
    target = HvacState(True, "cool", 22.0, swing_v=after[0], swing_h=after[1])
    values = read(target, previous)
    assert values["swing_toggle"] == toggle
    assert (values["swing_v"], values["swing_h"]) == after


def test_encode_passes_previous_to_the_toggles():
    dev = device()
    on = HvacState(True, "cool", 22.0)
    fresh = dev.encode(None, on).signal
    again = dev.encode(on, on).signal
    assert fresh != again


def test_message_shape():
    dev = device()
    signal = dev.encode(None, HvacState(True, "cool", 22.0)).signal
    assert signal.pulses[:2] == (3400, 3400)
    assert signal.pulses[-2:] == (400, 100000)
    assert len(signal.pulses) == 2 + 2 * 104 + 2


@pytest.mark.parametrize("model", HITACHI1_MODELS)
def test_registry_serves_the_port(model):
    dev = registry.get_device("hitachi", model)
    assert isinstance(dev, Hitachi1Device)
    assert dev.variant == HITACHI1_MODELS[model]


@pytest.mark.parametrize("model", HITACHI1_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.hitachi import PluginObject

    legacy = LegacyDevice("hitachi", model, PluginObject.MODELS[model])
    assert Hitachi1Device("hitachi", model).capabilities == legacy.capabilities


def _first(pred):
    return next(r for r in load_oracle("HITACHI_AC1") if pred(r))


@pytest.mark.parametrize(
    "pred, field",
    [
        (
            lambda r: r["state"].get("swing") == "on" and r["state"]["mode"] != "off",
            "swing_v",
        ),
        (lambda r: r["state"].get("hswing") == "on", "swing_h"),
        (lambda r: r["state"].get("sleep") == "on", "sleep"),
        (
            lambda r: r["state"]["mode"] == "heat" and r["state"].get("fan") == "high",
            "fan",
        ),
        (
            lambda r: r["state"]["mode"] == "fan" and r["state"].get("fan") == "medium",
            "fan",
        ),
    ],
)
def test_undeclared_deviation_is_reported(pred, field):
    record = _first(pred)
    dev = _device_for(record)
    with pytest.raises(AssertionError, match=field):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_swing_toggle_deviation_is_declared_separately():
    record = _first(lambda r: r["state"].get("hswing") == "on")
    dev = _device_for(record)
    only_swing_h = [d for d in DEFECTS if d.field == "swing_h"]
    with pytest.raises(AssertionError, match="swing_toggle"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, only_swing_h)


def test_layouts_must_cover_every_frame():
    record = load_oracle("HITACHI_AC1")[0]
    dev = _device_for(record)
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)
