import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.fields import Sum8
from pyhvac.ir.codec import decode
from pyhvac.plugins.haier import (
    HAIER_YRW02,
    HAIER_YRW02_LAYOUT,
    HAIER_YRW02_MODELS,
    HaierYrw02Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented HaierAc176Protocol values here:
# - model: IRac::haierYrwo2, unlike IRac::haier176, never calls setModel, so
#   every message carries stateReset's kHaierAcYrw02ModelA (0xA6), variant B
#   included. The port sends kHaierAcYrw02ModelB (0x59) for variant B;
# - sleep: IRGHVAC.build_ircode's key map has no "sleep", so IRac's sleep
#   stays -1 and setSleep(sleep >= 0) never sets Sleep (byte 8 bit 7).
MODEL_B = Defect("model", "B", "A", "IRac::haierYrwo2 never calls setModel")
SLEEP = Defect("sleep", 1, 0, "legacy glue never passes sleep")
DEFECTS = (MODEL_B, SLEEP)

# ir_Haier_test.cpp, TestDecodeHaierAC_YRW02.RealExample (issue #485): power
# on, cool, 17 C, fan high, swing(V) Middle, swing(H) Middle, health on,
# button Power.
REAL_EXAMPLE = bytes.fromhex("a61200024020002000000000053f")
# Its raw capture (rawData, 229 durations, ending on the footer mark).
REAL_CAPTURE = (
    2998,
    3086,
    2998,
    4460,
    568,
    1640,
    596,
    492,
    514,
    1690,
    590,
    496,
    566,
    532,
    592,
    1596,
    570,
    1618,
    518,
    584,
    590,
    538,
    524,
    536,
    568,
    532,
    590,
    1596,
    516,
    612,
    568,
    538,
    522,
    1638,
    586,
    500,
    512,
    614,
    568,
    538,
    520,
    538,
    586,
    538,
    566,
    540,
    520,
    538,
    586,
    538,
    522,
    538,
    588,
    538,
    568,
    538,
    520,
    538,
    586,
    538,
    566,
    538,
    520,
    540,
    588,
    1596,
    590,
    536,
    568,
    538,
    520,
    1592,
    640,
    538,
    520,
    540,
    588,
    538,
    568,
    538,
    516,
    562,
    566,
    538,
    518,
    542,
    586,
    540,
    566,
    1596,
    590,
    538,
    566,
    538,
    516,
    544,
    586,
    538,
    516,
    542,
    588,
    540,
    564,
    540,
    468,
    590,
    588,
    538,
    566,
    540,
    466,
    590,
    588,
    538,
    514,
    544,
    588,
    538,
    566,
    538,
    468,
    1692,
    606,
    526,
    466,
    592,
    588,
    538,
    568,
    490,
    588,
    538,
    566,
    540,
    466,
    592,
    588,
    538,
    566,
    538,
    466,
    592,
    588,
    538,
    568,
    492,
    586,
    540,
    566,
    540,
    468,
    590,
    588,
    538,
    568,
    516,
    488,
    590,
    588,
    538,
    568,
    492,
    588,
    538,
    566,
    518,
    488,
    590,
    588,
    540,
    564,
    518,
    490,
    590,
    588,
    538,
    562,
    496,
    588,
    538,
    566,
    518,
    488,
    590,
    588,
    538,
    562,
    522,
    488,
    588,
    590,
    538,
    560,
    498,
    588,
    540,
    564,
    522,
    486,
    590,
    590,
    538,
    560,
    524,
    488,
    588,
    588,
    1598,
    514,
    608,
    564,
    1600,
    548,
    536,
    586,
    538,
    568,
    1594,
    590,
    1618,
    578,
    1606,
    606,
    1582,
    590,
    1596,
    590,
    1616,
    580,
)


def device(model="YR-W02 remote"):
    return HaierYrw02Device("haier", model)


def with_hswing(record):
    # A record without "hswing" leaves IRac's swingh at kOff, which
    # convertSwingH sends as kHaierAcYrw02SwingHMiddle (0). The legacy entity
    # has no "off" swing_h; its "middle" (canonical "3") is the value the C
    # path sends as 0, so the record is read as "middle" (checked against
    # the C path in cpath_check.py).
    if "hswing" in record["state"]:
        return record
    return {**record, "state": {**record["state"], "hswing": "middle"}}


def _device_for(record):
    return HaierYrw02Device("haier", record["model"])


def frame(state, previous=None, dev=None):
    dev = dev or device()
    if previous is not None:
        previous = dev.normalise(previous)
    (main,) = dev.frames(previous, dev.normalise(state), ())
    return main.data


def read(state, previous=None, dev=None):
    return HAIER_YRW02_LAYOUT.read(frame(state, previous, dev))


@pytest.mark.parametrize("record", oracle_params("HAIER_AC_YRW02"))
def test_matches_c_library(record):
    dev = _device_for(record)
    assert_matches_oracle(dev, with_hswing(record), dev.LAYOUTS, DEFECTS)


def test_oracle_covers_both_variants():
    classes = {(r["class"], r["variant"]) for r in load_oracle("HAIER_AC_YRW02")}
    assert classes == {("HaierYRW02A", "1"), ("HaierYRW02B", "2")}
    for record in load_oracle("HAIER_AC_YRW02"):
        expected = {"HaierYRW02A": "A", "HaierYRW02B": "B"}[record["class"]]
        assert _device_for(record).variant == expected


def test_layout_round_trips_every_oracle_state():
    for record in load_oracle("HAIER_AC_YRW02"):
        dev = _device_for(record)
        state = state_from_record(dev, with_hswing(record)["state"])
        (main,) = dev.frames(None, state, ())
        values = HAIER_YRW02_LAYOUT.read(main.data)
        assert HAIER_YRW02_LAYOUT.build(**values) == bytearray(main.data)


def test_checksum_is_the_sum_of_bytes_0_to_12():
    # IRHaierAC176::checksum: Sum = sumBytes(raw, kHaierACYRW02StateLength - 1).
    for record in load_oracle("HAIER_AC_YRW02"):
        (main,) = decode(HAIER_YRW02, record["pulses"], expected=["main"])
        assert Sum8(0, 13, 13).check(main.data)


def test_reproduces_the_upstream_real_example():
    state = HvacState(
        True,
        "cool",
        17.0,
        fan="3",
        swing_v="2",
        swing_h="3",
        features={"purifier": True},
    )
    assert frame(state) == REAL_EXAMPLE
    assert HAIER_YRW02_LAYOUT.checksum.check(REAL_EXAMPLE)


def test_decodes_the_upstream_real_capture():
    (main,) = decode(HAIER_YRW02, REAL_CAPTURE, expected=["main"])
    assert main.data == REAL_EXAMPLE


def test_model_byte_follows_the_variant():
    assert frame(HvacState(True, "cool", 22.0))[0] == 0xA6
    dev_b = device("YR-W02 Code B")
    assert frame(HvacState(True, "cool", 22.0), dev=dev_b)[0] == 0x59
    explicit = HaierYrw02Device("haier", "YR-W02 remote", variant="B")
    assert read(HvacState(True, "cool", 22.0), dev=explicit)["model"] == "B"
    assert HaierYrw02Device("haier", "unknown").variant == "A"
    with pytest.raises(ValueError):
        HaierYrw02Device("haier", "x", variant="C")


def test_every_model_maps_to_its_variant():
    assert HAIER_YRW02_MODELS == {
        "YR-W02 remote": "A",
        "HSU-09HMC203": "A",
        "YR-W02 Code A": "A",
        "YR-W02 Code B": "B",
    }
    for model, variant in HAIER_YRW02_MODELS.items():
        assert device(model).variant == variant


@pytest.mark.parametrize("t", range(16, 31))
def test_temperature_is_offset_from_16(t):
    data = frame(HvacState(True, "cool", float(t)))
    assert data[1] >> 4 == t - 16
    assert read(HvacState(True, "cool", float(t)))["temperature"] == t


def test_setpoint_is_clamped_to_16_30():
    assert read(HvacState(True, "cool", 10.0))["temperature"] == 16
    assert read(HvacState(True, "heat", 40.0))["temperature"] == 30


@pytest.mark.parametrize("mode", ("auto", "cool", "dry", "heat", "fan"))
@pytest.mark.parametrize("t", (16.0, 23.0, 30.0))
def test_off_carries_mode_auto_and_the_setpoint(mode, t):
    # IRac passes mode "off"; convertMode maps it to auto. setTemp still runs.
    values = read(HvacState(False, mode, t, fan="2"))
    assert (values["power"], values["mode"], values["temperature"]) == (
        0,
        "auto",
        int(t),
    )
    assert values["fan"] == "2"
    assert values["button"] == "power"


@pytest.mark.parametrize(
    "mode, raw", [("auto", 0), ("cool", 1), ("dry", 2), ("heat", 4), ("fan", 6)]
)
def test_every_mode_uses_its_documented_value(mode, raw):
    data = frame(HvacState(True, mode, 22.0))
    assert HAIER_YRW02_LAYOUT.read_raw(data, "mode") == raw
    assert HAIER_YRW02_LAYOUT.read(data)["power"] == 1


@pytest.mark.parametrize("fan, raw", [("auto", 5), ("1", 3), ("2", 2), ("3", 1)])
@pytest.mark.parametrize("mode", ("auto", "cool", "dry", "heat", "fan"))
def test_every_fan_level_in_every_mode(mode, fan, raw):
    # IRHaierAC176::setFan has no per-mode limit.
    data = frame(HvacState(True, mode, 22.0, fan=fan))
    assert HAIER_YRW02_LAYOUT.read_raw(data, "fan") == raw


@pytest.mark.parametrize(
    "swing, mode, raw",
    [
        ("off", "cool", 0x0),
        ("auto", "cool", 0xC),
        ("1", "cool", 0x1),  # ceiling: Top
        ("2", "cool", 0x2),  # 45°: Middle
        ("3", "cool", 0xA),  # 30°: Down
        ("4", "cool", 0x2),  # 0°: Bottom is heat only, Middle instead
        ("1", "heat", 0x1),
        ("2", "heat", 0x3),  # heat has no Middle, Bottom instead
        ("3", "heat", 0xA),
        ("4", "heat", 0x3),
        ("auto", "heat", 0xC),
    ],
)
def test_swing_v_positions_and_the_heat_rule(swing, mode, raw):
    data = frame(HvacState(True, mode, 22.0, swing_v=swing))
    assert HAIER_YRW02_LAYOUT.read_raw(data, "swing_v") == raw


def test_swing_v_in_an_off_message_follows_mode_auto():
    assert read(HvacState(False, "heat", 22.0, swing_v="4"))["swing_v"] == "middle"


@pytest.mark.parametrize(
    "swing, raw",
    [("auto", 7), ("1", 3), ("2", 4), ("3", 0), ("4", 5), ("5", 6)],
)
def test_swing_h_positions(swing, raw):
    data = frame(HvacState(True, "cool", 22.0, swing_h=swing))
    assert HAIER_YRW02_LAYOUT.read_raw(data, "swing_h") == raw


@pytest.mark.parametrize("mode", ("cool", "heat"))
def test_turbo_and_quiet_in_cool_and_heat(mode):
    def feats(powerful, quiet):
        values = read(
            HvacState(True, mode, 22.0, features={"powerful": powerful, "quiet": quiet})
        )
        return values["turbo"], values["quiet"]

    assert feats(False, False) == (0, 0)
    assert feats(True, False) == (1, 0)
    assert feats(False, True) == (0, 1)
    assert feats(True, True) == (1, 0)  # setTurbo(true) after setQuiet clears it


@pytest.mark.parametrize("mode", ("auto", "dry", "fan"))
def test_turbo_and_quiet_only_in_cool_and_heat(mode):
    values = read(
        HvacState(True, mode, 22.0, features={"powerful": True, "quiet": True})
    )
    assert (values["turbo"], values["quiet"]) == (0, 0)


def test_turbo_and_quiet_in_an_off_message_follow_mode_auto():
    values = read(
        HvacState(False, "cool", 22.0, features={"powerful": True, "quiet": True})
    )
    assert (values["turbo"], values["quiet"]) == (0, 0)


@pytest.mark.parametrize("power", (True, False))
@pytest.mark.parametrize("mode", ("auto", "cool", "dry", "heat", "fan"))
def test_health_follows_purifier_in_every_mode(mode, power):
    on = HvacState(power, mode, 22.0, features={"purifier": True})
    assert read(on)["health"] == 1
    assert read(HvacState(power, mode, 22.0))["health"] == 0


@pytest.mark.parametrize("power", (True, False))
@pytest.mark.parametrize("mode", ("auto", "cool", "dry", "heat", "fan"))
def test_sleep_bit_in_every_mode(mode, power):
    # Documented Sleep bit (declared Defect: the C path never sets it).
    data = frame(HvacState(power, mode, 22.0, features={"sleep": True}))
    assert data[8] == 0x80
    assert frame(HvacState(power, mode, 22.0))[8] == 0x00


def test_timers_lock_and_units_stay_clear():
    values = read(
        HvacState(
            True,
            "heat",
            30.0,
            fan="3",
            swing_v="auto",
            swing_h="auto",
            features={"purifier": True, "sleep": True, "powerful": True},
        )
    )
    for key in (
        "timer_mode",
        "off_timer_hrs",
        "off_timer_mins",
        "on_timer_hrs",
        "on_timer_mins",
        "extra_degree_f",
        "use_fahrenheit",
        "lock",
    ):
        assert values[key] == 0, key


def test_button_is_always_power():
    # IRac::haierYrwo2 calls setPower last on a fresh object.
    for state in (
        HvacState(True, "cool", 22.0),
        HvacState(False, "heat", 30.0),
        HvacState(True, "heat", 16.0, fan="1", swing_v="1", swing_h="1"),
        HvacState(True, "cool", 25.0, features={"sleep": True, "powerful": True}),
    ):
        assert frame(state)[12] == 0x05


@pytest.mark.parametrize(
    "before",
    [
        HvacState(False, "cool", 22.0),
        HvacState(True, "heat", 25.0, fan="3", swing_v="auto"),
        HvacState(True, "cool", 22.0, features={"sleep": True}),
    ],
)
def test_previous_is_ignored(before):
    # No toggle bits, and IRac::sendAc/handleToggles use no previous state
    # for HAIER_AC_YRW02.
    target = HvacState(True, "cool", 22.0, swing_v="2")
    assert frame(target, before) == frame(target)
    dev = device()
    assert dev.encode(before, target).signal == dev.encode(None, target).signal


def test_message_shape():
    dev = device()
    pulses = dev.encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:4] == (3000, 3000, 3000, 4300)
    assert pulses[-2:] == (520, 150000)
    assert len(pulses) == 4 + 2 * 112 + 2


@pytest.mark.parametrize("model", HAIER_YRW02_MODELS)
def test_registry_serves_the_port(model):
    dev = registry.get_device("haier", model)
    assert isinstance(dev, HaierYrw02Device)
    assert dev.variant == HAIER_YRW02_MODELS[model]


@pytest.mark.parametrize("model", HAIER_YRW02_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.haier import PluginObject

    legacy = LegacyDevice("haier", model, PluginObject.MODELS[model])
    assert HaierYrw02Device("haier", model).capabilities == legacy.capabilities


def _first(pred):
    return next(r for r in load_oracle("HAIER_AC_YRW02") if pred(r))


@pytest.mark.parametrize(
    "pred, field",
    [
        (lambda r: r["class"] == "HaierYRW02B", "model"),
        (lambda r: r["state"].get("sleep") == "on", "sleep"),
    ],
)
def test_undeclared_deviation_is_reported(pred, field):
    record = with_hswing(_first(pred))
    dev = _device_for(record)
    with pytest.raises(AssertionError, match=field):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    record = with_hswing(load_oracle("HAIER_AC_YRW02")[0])
    dev = _device_for(record)
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)
