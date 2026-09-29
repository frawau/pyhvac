import pytest

from oracle import load_oracle
from port_oracle import assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.carrier import (
    CARRIER_AC64_LAYOUT,
    CARRIER_AC64_MODELS,
    CarrierAc64Checksum,
    CarrierAc64Device,
)
from pyhvac.state import HvacState

# The C path follows the header throughout: no Defect is declared. The
# fixture was generated from the fixed C path (the released one had
# Carrier's "fan" "heat" typo, so it held no fan or heat record).


def device(model="generic"):
    return CarrierAc64Device("carrier", model)


def state(power=True, mode="cool", temperature=22.0, **kw):
    return device().normalise(HvacState(power, mode, temperature, **kw))


def read(target, previous=None):
    (main,) = device().frames(previous, target, ())
    return CARRIER_AC64_LAYOUT.read(main.data)


def raw(target):
    (main,) = device().frames(None, target, ())
    return int.from_bytes(main.data, "little")


@pytest.mark.parametrize("record", oracle_params("CARRIER_AC64"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS)


def test_oracle_covers_every_mode():
    modes = {r["state"]["mode"] for r in load_oracle("CARRIER_AC64")}
    assert modes == {"off", "cool", "fan", "heat"}


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("CARRIER_AC64"):
        (main,) = dev.frames(None, state_from_record(dev, record["state"]), ())
        values = CARRIER_AC64_LAYOUT.read(main.data)
        assert CARRIER_AC64_LAYOUT.build(**values) == bytearray(main.data)


# Real and known-good words from ir_Carrier_test.cpp and IRac_test.cpp.
CAPTURES = [
    # TestDecodeCarrierAC64.RealExample: heat 30C fan low, swing on, power on.
    (
        0x404000102E5E5584,
        {
            "power": 1,
            "mode": "heat",
            "temperature": 30,
            "fan": "1",
            "swing_v": 1,
            "sleep": 0,
            "on_timer_enable": 0,
            "off_timer_enable": 0,
        },
    ),
    # ChecksumAndSetGetRaw "valid": off timer 9 h enabled.
    (0x90900030205C5584, {"off_timer_enable": 1, "off_timer": 9}),
    # The stateReset word (HumanReadable: off, cool, 28C, fan auto, swing on)
    # and the same powered on.
    (
        0x109000002C2A5584,
        {"power": 0, "mode": "cool", "temperature": 28, "fan": "auto"},
    ),
    (0x109000102C2B5584, {"power": 1, "mode": "cool", "temperature": 28}),
    # ReconstructKnownState: heat 16C low, swing, sleep (timers disabled).
    (
        0x2030009020555584,
        {"mode": "heat", "temperature": 16, "sleep": 1, "on_timer_enable": 0},
    ),
]


@pytest.mark.parametrize("word, fields", CAPTURES)
def test_layout_reads_the_real_captures(word, fields):
    data = word.to_bytes(8, "little")
    values = CARRIER_AC64_LAYOUT.read(data)
    assert {k: values[k] for k in fields} == fields
    assert CARRIER_AC64_LAYOUT.build(**values) == bytearray(data)


@pytest.mark.parametrize("word, _", CAPTURES)
def test_checksum_holds_on_the_real_captures(word, _):
    data = word.to_bytes(8, "little")
    assert CARRIER_AC64_LAYOUT.checksum.check(data)
    broken = bytearray(data)
    broken[2] ^= 0x01
    assert not CARRIER_AC64_LAYOUT.checksum.check(broken)
    CARRIER_AC64_LAYOUT.checksum.apply(broken)
    assert bytes(broken) == data


def test_checksum_matches_the_known_sum():
    # ChecksumAndSetGetRaw: calcChecksum(0x90900030205C5584) == 0x0C.
    data = (0x90900030205C5584).to_bytes(8, "little")
    assert CarrierAc64Checksum(3, 8, 2).compute(data) == 0x0C


def test_checksum_writes_only_the_low_nibble():
    assert CarrierAc64Checksum(3, 8, 2).bits() == {16, 17, 18, 19}


def test_port_reproduces_the_real_capture_but_swing_and_timers():
    # RealExample (heat, 30C, fan low, power on) with what the entity cannot
    # express reset: swing off, and the timer hours of stateReset.
    capture = CARRIER_AC64_LAYOUT.read((0x404000102E5E5584).to_bytes(8, "little"))
    capture.update(swing_v=0, on_timer=9, off_timer=1)
    expected = CARRIER_AC64_LAYOUT.build(**capture)
    assert raw(state(True, "heat", 30.0, fan="1")) == int.from_bytes(expected, "little")


@pytest.mark.parametrize("mode, code", [("heat", 1), ("cool", 2), ("fan", 3)])
def test_mode_uses_its_documented_value(mode, code):
    (main,) = device().frames(None, state(True, mode), ())
    assert CARRIER_AC64_LAYOUT.read_raw(main.data, "mode") == code


@pytest.mark.parametrize("mode", ["cool", "fan", "heat"])
@pytest.mark.parametrize("t", [16.0, 23.0, 30.0])
def test_setpoint_is_sent_in_every_mode(mode, t):
    assert read(state(True, mode, t))["temperature"] == int(t)


@pytest.mark.parametrize("t, sent", [(10.0, 16), (35.0, 30)])
def test_setpoint_is_clamped_to_the_documented_range(t, sent):
    # setTemp clamps to kCarrierAc64MinTemp..kCarrierAc64MaxTemp.
    assert read(state(True, "cool", t))["temperature"] == sent


@pytest.mark.parametrize("fan, code", [("auto", 0), ("1", 1), ("2", 2), ("3", 3)])
def test_every_fan_level_uses_its_documented_code(fan, code):
    (main,) = device().frames(None, state(fan=fan), ())
    assert CARRIER_AC64_LAYOUT.read_raw(main.data, "fan") == code


@pytest.mark.parametrize("mode", ["cool", "fan", "heat"])
@pytest.mark.parametrize("fan", ["auto", "1", "3"])
def test_off_carries_cool_with_the_setpoint_and_fan(mode, fan):
    # IRac's "off" mode falls to convertMode's default, kCarrierAc64Cool.
    values = read(state(False, mode, 25.0, fan=fan))
    assert (values["power"], values["mode"]) == (0, "cool")
    assert (values["temperature"], values["fan"]) == (25, fan)


def test_unset_fields_keep_their_reset_values():
    for target in (state(True, "heat", 30.0, fan="3"), state(False, "fan", 16.0)):
        values = read(target)
        assert (values["swing_v"], values["sleep"]) == (0, 0)
        assert (values["on_timer_enable"], values["off_timer_enable"]) == (0, 0)
        # stateReset: OnTimer 9, OffTimer 1.
        assert (values["on_timer"], values["off_timer"]) == (9, 1)


def test_previous_is_ignored():
    target = state(True, "heat", 21.0, fan="2")
    for previous in (None, state(False, "cool", 16.0), target):
        assert device().frames(previous, target, ()) == device().frames(
            None, target, ()
        )


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (8940, 4556)
    assert pulses[-2:] == (503, 100000)
    assert len(pulses) == 2 + 2 * 64 + 2


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("CARRIER_AC64")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, ())


@pytest.mark.parametrize("model", CARRIER_AC64_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("carrier", model), CarrierAc64Device)


@pytest.mark.parametrize("model", CARRIER_AC64_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.carrier import Carrier

    legacy = LegacyDevice("carrier", model, Carrier)
    assert device(model).capabilities == legacy.capabilities


@pytest.mark.parametrize("mode", ["cool", "fan", "heat"])
@pytest.mark.parametrize("t", [16.0, 30.0])
@pytest.mark.parametrize("fan", ["auto", "1", "2", "3"])
def test_off_in_every_mode_matches_the_c_path(mode, t, fan):
    # The oracle's off records only say "off" (read as cool); the C path
    # sends the same off message whatever the target mode.
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.ir.codec import decode
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.carrier import Carrier

    legacy = LegacyDevice("carrier", "generic", Carrier)
    target = HvacState(False, mode, t, fan=fan)
    pulses = legacy.encode(None, target).signal.pulses
    theirs = decode(device().PROTOCOL, pulses, expected=["main"])
    assert device().frames(None, device().normalise(target), ()) == theirs
