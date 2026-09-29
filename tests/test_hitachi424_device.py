import pytest

from oracle import load_oracle
from port_oracle import (
    Defect,
    assert_matches_oracle,
    assert_sequence_matches_c,
    oracle_params,
    sequence_params,
    state_from_record,
)
from pyhvac import registry
from pyhvac.fields import InvertedPairs
from pyhvac.ir.codec import decode
from pyhvac.plugins.hitachi import (
    HITACHI424,
    HITACHI424_LAYOUT,
    HITACHI424_MODELS,
    Hitachi424Device,
)
from pyhvac.state import HvacState

# The C path never sends swing on: the old vocabulary's "on" has no entry in
# IRGHVAC.trans_swing, so build_ircode skips the key, swingv stays kOff, and
# IRac::hitachi424's setSwingVToggle(false) leaves the button at
# kHitachiAc424ButtonPowerMode instead of kHitachiAc424ButtonSwingV.
DEFECTS = (Defect("button", "swing_v", "power_mode", "C glue has no 'on' swing"),)


def device():
    return Hitachi424Device("hitachi", "RAR-8P2 remote")


def read(state, previous=None):
    dev = device()
    if previous is not None:
        previous = dev.normalise(previous)
    _, main = dev.frames(previous, dev.normalise(state), ())
    return HITACHI424_LAYOUT.read(main.data)


@pytest.mark.parametrize("record", oracle_params("HITACHI_AC424"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


@pytest.mark.parametrize("record, states", sequence_params("HITACHI_AC424"))
def test_sequence_matches_a_persistent_c_object(record, states):
    # The swing button depends on the message before, but the 0.1.7 glue
    # never passes swing on (DEFECTS), so this cannot catch a wrong swing
    # toggle: it checks that no other field depends on the message before.
    dev = device()
    assert_sequence_matches_c(dev, record, states, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("HITACHI_AC424"):
        state = state_from_record(dev, record["state"])
        _, main = dev.frames(None, state, ())
        values = HITACHI424_LAYOUT.read(main.data)
        assert HITACHI424_LAYOUT.build(**values) == bytearray(main.data)


def test_every_oracle_frame_has_inverted_pairs_from_byte_3():
    # IRHitachiAc424::setInvertedStates: invertBytePairs(raw + 3, 50).
    for record in load_oracle("HITACHI_AC424"):
        _, main = decode(HITACHI424, record["pulses"], expected=["leader", "main"])
        assert InvertedPairs(3, 53).check(main.data)


def test_skeleton_is_the_reset_state():
    # stateReset, then off in cool at 16 °C with fan auto: the whole frame
    # of the oracle's first record (which is that state).
    record = load_oracle("HITACHI_AC424")[0]
    assert record["state"] == {
        "mode": "off",
        "temperature": 16,
        "fan": "auto",
        "swing": "off",
    }
    _, main = decode(HITACHI424, record["pulses"], expected=["leader", "main"])
    data = HITACHI424_LAYOUT.build(
        fan_aux9=0x92,
        button="power_mode",
        temperature=16,
        mode="cool",
        fan="auto",
        power=0,
        fan_aux29=0,
    )
    assert bytes(data) == main.data


@pytest.mark.parametrize("mode", ["fan", "heat", "cool", "dry"])
@pytest.mark.parametrize("temp", [16.0, 23.0, 32.0])
def test_off_carries_mode_cool_in_every_mode(mode, temp):
    # IRac passes mode "off"; IRHitachiAc424::convertMode maps it to cool.
    values = read(HvacState(False, mode, temp))
    assert (values["power"], values["mode"], values["temperature"]) == (
        0,
        "cool",
        int(temp),
    )
    assert values["fan"] == "auto"


def test_fan_mode_keeps_the_setpoint():
    # setMode(fan) writes kHitachiAc424FanTemp, but IRac's setTemp follows.
    assert read(HvacState(True, "fan", 18.0, fan="2"))["temperature"] == 18


def test_setpoint_is_clamped_to_16_32():
    assert read(HvacState(True, "cool", 10.0))["temperature"] == 16
    assert read(HvacState(True, "heat", 40.0))["temperature"] == 32


@pytest.mark.parametrize(
    "mode, fan, sent",
    [
        ("cool", "auto", "auto"),
        ("cool", "5", "5"),
        ("heat", "1", "1"),
        ("dry", "auto", "auto"),  # dry keeps auto
        ("dry", "1", "1"),
        ("dry", "2", "2"),
        ("dry", "3", "2"),  # kHitachiAc424FanMaxDry
        ("dry", "4", "2"),
        ("dry", "5", "2"),
        ("fan", "auto", "1"),  # fan mode has no auto: Min
        ("fan", "5", "5"),
    ],
)
def test_fan_is_limited_per_mode(mode, fan, sent):
    assert read(HvacState(True, mode, 24.0, fan=fan))["fan"] == sent


@pytest.mark.parametrize(
    "fan, raw, aux9, aux29",
    [
        ("auto", 5, 0x92, 0x00),
        ("1", 1, 0x98, 0x00),
        ("2", 2, 0x92, 0x00),
        ("3", 3, 0x92, 0x00),
        ("4", 4, 0x92, 0x00),
        ("5", 6, 0xA9, 0x30),
    ],
)
def test_every_fan_level_and_its_extra_bytes(fan, raw, aux9, aux29):
    dev = device()
    _, main = dev.frames(
        None, dev.normalise(HvacState(True, "cool", 24.0, fan=fan)), ()
    )
    assert HITACHI424_LAYOUT.read_raw(main.data, "fan") == raw
    assert (main.data[9], main.data[29]) == (aux9, aux29)


def test_button_is_power_mode_without_swing():
    assert read(HvacState(True, "cool", 24.0))["button"] == "power_mode"
    assert read(HvacState(False, "cool", 24.0))["button"] == "power_mode"


def test_swing_without_previous_presses_the_swing_button():
    # A fresh IRac has no previous state: swing on -> setSwingVToggle(true).
    state = HvacState(True, "cool", 24.0, swing_v="swing")
    assert read(state)["button"] == "swing_v"
    dev = device()
    _, main = dev.frames(None, dev.normalise(state), ())
    assert main.data[11] == 0x81


@pytest.mark.parametrize(
    "before, after, button",
    [
        ("off", "off", "power_mode"),
        ("off", "swing", "swing_v"),
        ("swing", "swing", "power_mode"),
        ("swing", "off", "swing_v"),
    ],
)
def test_swing_button_with_previous_only_on_change(before, after, button):
    # IRac::handleToggles (HITACHI_AC424): toggle only when swing changes.
    previous = HvacState(True, "cool", 24.0, swing_v=before)
    target = HvacState(True, "cool", 25.0, swing_v=after)
    assert read(target, previous)["button"] == button


def test_encode_passes_previous_to_the_swing_button():
    dev = device()
    on = HvacState(True, "cool", 22.0, swing_v="swing")
    assert dev.encode(None, on).signal != dev.encode(on, on).signal


def test_message_shape():
    dev = device()
    pulses = dev.encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:4] == (29784, 49290, 3416, 1604)
    assert pulses[-2:] == (463, 100000)
    assert len(pulses) == 2 + 2 + 2 * 424 + 2


@pytest.mark.parametrize("model", HITACHI424_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("hitachi", model), Hitachi424Device)


@pytest.mark.parametrize("model", HITACHI424_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.hitachi import Hitachi424

    legacy = LegacyDevice("hitachi", model, Hitachi424)
    assert Hitachi424Device("hitachi", model).capabilities == legacy.capabilities


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(
        r for r in load_oracle("HITACHI_AC424") if r["state"].get("swing") == "on"
    )
    with pytest.raises(AssertionError, match="button"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("HITACHI_AC424")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:1], DEFECTS)
