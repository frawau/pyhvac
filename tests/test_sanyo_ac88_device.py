import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.sanyo import (
    SANYO_AC88_LAYOUT,
    SANYO_AC88_MODELS,
    SanyoAc88Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented SanyoAc88 values here (pyhvac's
# glue, not IRremoteESP8266):
# - IRGHVAC.trans_swing has no "on" key, so IRac keeps swingv at kOff and
#   IRac::sanyo88 calls setSwingV(false). The port sends SwingV = 1.
# - IRGHVAC.build_ircode's key map has no "sleep", so IRac keeps sleep at -1
#   and IRac::sanyo88 calls setSleep(false). The port sends Sleep = 1.
SWING = Defect("swing_v", "swing", "off", "C path drops swing 'on' (SwingV)")
SLEEP = Defect("sleep", 1, 0, "C path drops sleep (IRSanyoAc88::setSleep)")
DEFECTS = (SWING, SLEEP)

# ir_Sanyo_test.cpp, DecodeRealExamples ("On", issue 1503): cool, 24 C, fan
# auto, clock 18:42:06. Bytes 1, 7 and 10 are 0x59, 0x00 and 0x80 in the
# capture, where stateReset (and so the C path) has 0x55, 0x01 and 0x10.
REAL_CAPTURE = bytes.fromhex("aa59a018062a1200000080")


def wire(record):
    """``record`` with the pulses the C library puts on the wire.

    sendSanyoAc88 ends with space(kSanyoAc88Gap) then space(kDefaultMessageGap).
    IRac's timing log keeps them as two entries, so the fixture's last entry
    (100 000 µs) sits at a mark position; IRremoteESP8266's own
    SyntheticSelfDecode test shows them merged ("m500s103675").
    """
    pulses = record["pulses"]
    assert len(pulses) % 2 and pulses[-2:] == [3675, 100000]
    return {**record, "pulses": pulses[:-2] + [3675 + 100000]}


def device(model="generic 88"):
    return SanyoAc88Device("sanyo", model)


def frames(state):
    dev = device()
    return dev.frames(None, dev.normalise(state), ())


def read(state):
    return SANYO_AC88_LAYOUT.read(frames(state)[0].data)


def raw(state, field):
    return SANYO_AC88_LAYOUT.read_raw(frames(state)[0].data, field)


@pytest.mark.parametrize("record", oracle_params("SANYO_AC88"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, wire(record), dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("SANYO_AC88"):
        state = state_from_record(dev, record["state"])
        *mains, end = dev.frames(None, state, ())
        assert (end.section, end.data, end.nbits) == ("end", b"", 0)
        assert len(mains) == 3 and len({f.data for f in mains}) == 1
        values = SANYO_AC88_LAYOUT.read(mains[0].data)
        assert SANYO_AC88_LAYOUT.build(**values) == bytearray(mains[0].data)


def test_the_real_capture_reads_as_documented():
    assert SANYO_AC88_LAYOUT.read(REAL_CAPTURE) == {
        "fan": "auto",
        "mode": "cool",
        "power": 1,
        "temperature": 24,
        "filter": 0,
        "swing_v": "off",
        "clock_secs": 6,
        "clock_mins": 42,
        "clock_hours": 18,
        "turbo": 0,
        "start_timer": 0,
        "stop_timer": 0,
        "sleep": 0,
    }


def test_the_real_capture_differs_only_where_the_c_path_does():
    # The clock (never set by IRac) and bytes 1, 7 and 10 (stateReset's 0x55,
    # 0x01 and 0x10) are the only differences.
    frame, *_ = frames(HvacState(True, "cool", 24.0))
    capture = bytearray(REAL_CAPTURE)
    for name in ("clock_secs", "clock_mins", "clock_hours"):
        SANYO_AC88_LAYOUT.write_raw(capture, name, 0)
    capture[1], capture[7], capture[10] = 0x55, 0x01, 0x10
    assert frame.data == bytes(capture)


@pytest.mark.parametrize("mode", ["auto", "cool", "heat", "fan"])
@pytest.mark.parametrize("temperature", [10.0, 20.0, 30.0])
def test_off_carries_mode_auto(mode, temperature):
    # IRac passes mode "off"; convertMode maps it to kSanyoAc88Auto.
    values = read(HvacState(False, mode, temperature))
    assert (values["power"], values["mode"], values["temperature"]) == (
        0,
        "auto",
        int(temperature),
    )


def test_mode_codes():
    for mode, code in (("auto", 0), ("cool", 2), ("heat", 4), ("fan", 5)):
        assert raw(HvacState(True, mode, 22.0), "mode") == code


@pytest.mark.parametrize("mode", ["auto", "cool", "heat", "fan"])
def test_setpoint_is_whole_degrees_clamped_to_10_30(mode):
    assert read(HvacState(True, mode, 5.0))["temperature"] == 10
    assert read(HvacState(True, mode, 21.0))["temperature"] == 21
    assert read(HvacState(True, mode, 21.5))["temperature"] == 21
    assert read(HvacState(True, mode, 40.0))["temperature"] == 30


@pytest.mark.parametrize(
    "fan, code", [("auto", 0), ("1", 1), ("2", 2), ("3", 3), ("4", 3)]
)
def test_fan_codes_as_convert_fan(fan, code):
    # convertFan: kMin and kLow -> FanLow, kHigh and kMax -> FanHigh.
    assert raw(HvacState(True, "cool", 22.0, fan=fan), "fan") == code


@pytest.mark.parametrize(
    "feature, field",
    [("powerful", "turbo"), ("purifier", "filter"), ("sleep", "sleep")],
)
def test_each_feature_sets_its_bit_only(feature, field):
    base = read(HvacState(True, "cool", 22.0))
    on = read(HvacState(True, "cool", 22.0, features={feature: True}))
    assert (base[field], on[field]) == (0, 1)
    assert {k: v for k, v in on.items() if k != field} == {
        k: v for k, v in base.items() if k != field
    }


def test_features_combine():
    feats = {"powerful": True, "purifier": True, "sleep": True}
    values = read(
        HvacState(True, "heat", 26.0, fan="2", swing_v="swing", features=feats)
    )
    assert (values["turbo"], values["filter"], values["sleep"]) == (1, 1, 1)
    assert (values["swing_v"], values["fan"], values["mode"]) == ("swing", "2", "heat")


def test_swing_sends_the_documented_bit():
    assert raw(HvacState(True, "cool", 22.0, swing_v="swing"), "swing_v") == 1
    assert raw(HvacState(True, "cool", 22.0, swing_v="off"), "swing_v") == 0


def test_start_timer_bit_stays_set_as_state_reset():
    assert read(HvacState(True, "cool", 22.0))["start_timer"] == 1


def test_previous_is_ignored():
    dev = device()
    on = HvacState(True, "cool", 22.0, swing_v="swing")
    off = HvacState(False, "heat", 30.0)
    assert dev.encode(off, on).signal == dev.encode(None, on).signal
    assert dev.encode(on, on).signal == dev.encode(None, on).signal


def test_message_shape():
    signal = device().encode(None, HvacState(True, "cool", 22.0)).signal
    assert signal.carrier == 38000
    pulses = signal.pulses
    per_frame = 2 + 2 * 88 + 2
    assert len(pulses) == 3 * per_frame
    for n in range(3):
        start = n * per_frame
        assert pulses[start : start + 2] == (5400, 2000)
        assert pulses[start + 2 : start + 4] == (500, 750)  # 0xAA LSB first
        assert pulses[start + 4 : start + 6] == (500, 1500)
    assert pulses[per_frame - 2 : per_frame] == (500, 3675)
    assert pulses[-2:] == (500, 103675)


def test_the_fixture_ends_on_unmerged_spaces():
    for record in load_oracle("SANYO_AC88"):
        assert len(record["pulses"]) == 3 * (2 + 2 * 88 + 2) + 1
        assert record["pulses"][-2:] == [3675, 100000]


def test_registry_serves_the_port():
    for model in SANYO_AC88_MODELS:
        assert isinstance(registry.get_device("sanyo", model), SanyoAc88Device)


def test_capabilities_match_the_legacy_entity():
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.sanyo import Sanyo88

    for model in SANYO_AC88_MODELS:
        legacy = LegacyDevice("sanyo", model, Sanyo88)
        assert device(model).capabilities == legacy.capabilities


def _record(**state):
    return next(
        r
        for r in load_oracle("SANYO_AC88")
        if all(r["state"].get(k) == v for k, v in state.items())
    )


@pytest.mark.parametrize(
    "state, defect",
    [
        ({"mode": "cool", "fan": "medium", "swing": "on"}, SWING),
        ({"mode": "auto", "sleep": "on"}, SLEEP),
    ],
)
def test_undeclared_deviation_is_reported(state, defect):
    dev = device()
    record = wire(_record(**state))
    assert_matches_oracle(dev, record, dev.LAYOUTS, (defect,))
    others = tuple(d for d in DEFECTS if d is not defect)
    with pytest.raises(AssertionError, match=f"'{defect.field}'"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=others)


def test_layouts_must_cover_every_frame():
    dev = device()
    record = wire(_record(mode="cool", fan="medium", swing="on"))
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:3], DEFECTS)
