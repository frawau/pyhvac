import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.ir.codec import decode
from pyhvac.plugins.mitsubishi_heavy_industries import (
    MITSUBISHI_HEAVY152,
    MITSUBISHI_HEAVY152_LAYOUT,
    MITSUBISHI_HEAVY152_MODELS,
    MitsubishiHeavy152Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Mitsubishi152Protocol values here:
# - fan lowest: IRMitsubishiHeavy152Ac::convertFan maps kMin to
#   kMitsubishiHeavy152FanEcono (0x6), then IRac::mitsubishiHeavy152 calls
#   setEcono(false), which sees getEcono() and resets the fan to Auto (0x0);
# - swing "90°"/"60°" (canonical "1"/"2"): IRGHVAC.trans_swing maps them to
#   kHigh and kUpperMiddle; convertSwingV sends kHigh as
#   kMitsubishiHeavy152SwingVHigh (2) and has no kUpperMiddle case, so it
#   sends kMitsubishiHeavy152SwingVOff (6). The port counts the documented
#   positions from the top: Highest (1), High (2);
# - sleep: IRGHVAC.build_ircode's key map has no "sleep", so IRac's sleep
#   stays -1 and setNight(sleep >= 0) never sets Night (byte 15 bit 6).
FAN_LOWEST = Defect("fan", "econo", "auto", "IRac's setEcono(false) resets Econo")
SWING_HIGHEST = Defect("swing_v", "highest", "high", "glue sends kHigh for 90°")
SWING_HIGH = Defect("swing_v", "high", "off", "convertSwingV: no kUpperMiddle")
NIGHT = Defect("night", 1, 0, "legacy glue never passes sleep")
DEFECTS = (FAN_LOWEST, SWING_HIGHEST, SWING_HIGH, NIGHT)

# ir_MitsubishiHeavy_test.cpp, ZmsRealExample (issue #660): power on, heat,
# 24 C, fan Max, swing(V) and swing(H) auto.
REAL_EXAMPLE = bytes.fromhex("ad513ce51a0cf307f804fb00ff00ff00ff807f")
# ZmsSyntheticExample: the same settings with the power off.
OFF_EXAMPLE = bytes.fromhex("ad513ce51a04fb07f804fb00ff00ff00ff807f")


def device(model="RLA502A700B remote"):
    return MitsubishiHeavy152Device("mitsubishi_heavy_industries", model)


def with_hswing(record):
    # A record without "hswing" leaves IRac's swingh at kOff, which
    # convertSwingH sends as kMitsubishiHeavy152SwingHOff (8). The legacy
    # entity has no "off" swing_h; its "wide" (canonical "6") is the value
    # the C path sends as 8 (convertSwingH has no kWide case), so the record
    # is read as "wide" (the oracle records match only so).
    if "hswing" in record["state"]:
        return record
    return {**record, "state": {**record["state"], "hswing": "wide"}}


def frame(state, previous=None):
    dev = device()
    if previous is not None:
        previous = dev.normalise(previous)
    (main,) = dev.frames(previous, dev.normalise(state), ())
    return main.data


def read(state, previous=None):
    return MITSUBISHI_HEAVY152_LAYOUT.read(frame(state, previous))


@pytest.mark.parametrize("record", oracle_params("MITSUBISHI_HEAVY_152"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, with_hswing(record), dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("MITSUBISHI_HEAVY_152"):
        state = state_from_record(dev, with_hswing(record)["state"])
        (main,) = dev.frames(None, state, ())
        values = MITSUBISHI_HEAVY152_LAYOUT.read(main.data)
        assert MITSUBISHI_HEAVY152_LAYOUT.build(**values) == bytearray(main.data)


def test_every_oracle_frame_has_inverted_pairs_from_byte_3():
    # portkit checksum only tries InvertedPairs(0, n) on even lengths.
    for record in load_oracle("MITSUBISHI_HEAVY_152"):
        (main,) = decode(MITSUBISHI_HEAVY152, record["pulses"], expected=["main"])
        assert MITSUBISHI_HEAVY152_LAYOUT.checksum.check(main.data)
        assert main.data[:5] == bytes.fromhex("ad513ce51a")  # kMitsubishiHeavyZmsSig


def test_no_field_sits_in_a_complement_byte():
    complements = MITSUBISHI_HEAVY152_LAYOUT.checksum.positions()
    for name, f in MITSUBISHI_HEAVY152_LAYOUT.fields.items():
        assert not {b // 8 for b in f.bits} & complements, name


def test_the_real_capture_is_reproduced():
    state = HvacState(True, "heat", 24.0, fan="5", swing_v="auto", swing_h="auto")
    assert frame(state) == REAL_EXAMPLE


def test_the_off_capture_differs_only_by_the_mode_an_off_message_carries():
    # The C path (and the port) send mode auto when off; the remote kept heat.
    state = HvacState(False, "heat", 24.0, fan="5", swing_v="auto", swing_h="auto")
    ours = frame(state)
    assert {i for i, (a, b) in enumerate(zip(ours, OFF_EXAMPLE)) if a != b} == {5, 6}
    values = MITSUBISHI_HEAVY152_LAYOUT.read(OFF_EXAMPLE)
    assert {**values, "mode": "auto"} == MITSUBISHI_HEAVY152_LAYOUT.read(ours)


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan", "heat"])
@pytest.mark.parametrize("t", [17.0, 31.0])
def test_off_carries_mode_auto_in_every_mode(mode, t):
    # IRac passes mode "off"; convertMode maps it to kMitsubishiHeavyAuto.
    values = read(HvacState(False, mode, t))
    assert (values["power"], values["mode"], values["temp"]) == (0, "auto", t - 17)


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan", "heat"])
def test_mode_codes_and_the_setpoint_in_every_mode(mode):
    for t in (17.0, 24.0, 31.0):
        values = read(HvacState(True, mode, t))
        assert (values["power"], values["mode"], values["temp"]) == (1, mode, t - 17)


def test_setpoint_is_clamped_to_17_31():
    assert read(HvacState(True, "cool", 10.0))["temp"] == 0
    assert read(HvacState(True, "cool", 40.0))["temp"] == 14


@pytest.mark.parametrize(
    "fan, raw", [("auto", 0), ("1", 6), ("2", 1), ("3", 2), ("4", 3), ("5", 4)]
)
def test_every_fan_level(fan, raw):
    data = frame(HvacState(True, "cool", 22.0, fan=fan))
    assert MITSUBISHI_HEAVY152_LAYOUT.read_raw(data, "fan") == raw


@pytest.mark.parametrize("fan", ["auto", "1", "2", "3", "4", "5"])
def test_powerful_is_turbo_and_economy_is_econo_and_wins(fan):
    def fan_of(**features):
        return read(HvacState(True, "cool", 22.0, fan=fan, features=features))["fan"]

    assert fan_of(powerful=True) == "turbo"
    assert fan_of(economy=True) == "econo"
    # setEcono runs after setTurbo.
    assert fan_of(powerful=True, economy=True) == "econo"


@pytest.mark.parametrize(
    "swing_v, raw",
    [("off", 6), ("auto", 0), ("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 5)],
)
def test_every_swing_v_value(swing_v, raw):
    data = frame(HvacState(True, "cool", 22.0, swing_v=swing_v))
    assert MITSUBISHI_HEAVY152_LAYOUT.read_raw(data, "swing_v") == raw


@pytest.mark.parametrize(
    "swing_h, raw",
    [("auto", 0), ("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 5), ("6", 8)],
)
def test_every_swing_h_value(swing_h, raw):
    # "wide" (canonical "6") is sent as kMitsubishiHeavy152SwingHOff, as C.
    data = frame(HvacState(True, "cool", 22.0, swing_h=swing_h))
    assert MITSUBISHI_HEAVY152_LAYOUT.read_raw(data, "swing_h") == raw


@pytest.mark.parametrize(
    "features, bits",
    [
        ({}, (0, 0, 0, 0)),
        ({"cleaning": True}, (1, 0, 0, 0)),
        ({"purifier": True}, (0, 1, 0, 0)),
        ({"cleaning": True, "purifier": True}, (1, 1, 0, 0)),
        ({"sleep": True}, (0, 0, 1, 0)),
        ({"quiet": True}, (0, 0, 0, 1)),
    ],
)
def test_feature_bits(features, bits):
    # setClean writes Clean and Filter, then setFilter(purifier) rewrites
    # Filter: cleaning alone leaves Filter clear.
    values = read(HvacState(True, "cool", 22.0, features=features))
    assert (
        values["clean"],
        values["filter"],
        values["night"],
        values["silent"],
    ) == bits
    assert (values["three"], values["d"]) == (0, 0)  # IRac never calls set3D


def test_previous_is_ignored():
    dev = device()
    on = HvacState(True, "cool", 22.0, swing_v="auto", features={"quiet": True})
    off = HvacState(False, "heat", 30.0)
    assert dev.encode(off, on).signal == dev.encode(None, on).signal
    assert dev.encode(on, on).signal == dev.encode(None, on).signal


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (3140, 1630)
    assert pulses[-2:] == (370, 100000)
    assert len(pulses) == 2 + 2 * 152 + 2


@pytest.mark.parametrize("model", MITSUBISHI_HEAVY152_MODELS)
def test_registry_serves_the_port(model):
    dev = registry.get_device("mitsubishi_heavy_industries", model)
    assert isinstance(dev, MitsubishiHeavy152Device)


@pytest.mark.parametrize("model", MITSUBISHI_HEAVY152_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.mitsubishi_heavy_industries import Mitsubishi152

    legacy = LegacyDevice("mitsubishi_heavy_industries", model, Mitsubishi152)
    assert device(model).capabilities == legacy.capabilities


@pytest.mark.parametrize(
    "select, defect, field",
    [
        (lambda s: s.get("fan") == "lowest", FAN_LOWEST, "fan"),
        (lambda s: s.get("swing") == "90°", SWING_HIGHEST, "swing_v"),
        (lambda s: s.get("swing") == "60°", SWING_HIGH, "swing_v"),
        (lambda s: s.get("sleep") == "on", NIGHT, "night"),
    ],
)
def test_undeclared_deviation_is_reported(select, defect, field):
    dev = device()
    record = next(r for r in load_oracle("MITSUBISHI_HEAVY_152") if select(r["state"]))
    others = tuple(d for d in DEFECTS if d != defect)
    with pytest.raises(AssertionError, match=field):
        assert_matches_oracle(dev, with_hswing(record), dev.LAYOUTS, defects=others)


def test_missing_hswing_is_not_silently_accepted():
    dev = device()
    record = next(
        r for r in load_oracle("MITSUBISHI_HEAVY_152") if "hswing" not in r["state"]
    )
    with pytest.raises(AssertionError, match="swing_h"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)
