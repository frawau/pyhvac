import itertools

import pytest

from oracle import load_oracle
from port_oracle import (
    Defect,
    assert_matches_oracle,
    c_sequence,
    oracle_params,
    state_from_record,
)
from pyhvac import registry
from pyhvac.plugins.toshiba import (
    TOSHIBA_AC_CARRIER_MODELS,
    TOSHIBA_AC_LAYOUT,
    TOSHIBA_AC_LONG_LAYOUT,
    TOSHIBA_AC_MODELS,
    TOSHIBA_AC_SWING_LAYOUT,
    ToshibaAcDevice,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Toshiba values here: the legacy
# glue (IRGHVAC.trans_swing) has no "on", so IRac's swingv stays kOff and
# IRac::toshiba's setSwing writes kToshibaAcSwingOff into the swing message;
# the port sends kToshibaAcSwingOn.
SWING = Defect("swing", "on", "off", "legacy glue has no swing 'on'")
DEFECTS = (SWING,)

# ir_Toshiba_test.cpp: the state messages of the real captures, and the
# class-built states, as logical bytes (sent MSB first).
REAL_AUTO_23 = bytes.fromhex("f20d03fc0160000061")  # RealExamples rawData1
REAL_COOL_17 = bytes.fromhex("f20d03fc0100810080")  # RealExamples rawData2
REAL_HEAT_24 = bytes.fromhex("f20d03fc0170c300b2")  # RealExamples rawData3
REAL_OFF_22 = bytes.fromhex("f20d03fc0150a700f6")  # RealExamples rawData4
REAL_HIGH_POWER = bytes.fromhex("f20d04fb095000000158")  # RealLongExample
REAL_WHUB03NJ_OFF = bytes.fromhex("f20d03fc0130070036")  # RealExample_WHUB03NJ
REAL_AIR_DIRECTION = bytes.fromhex("f20d01fe210021")  # RealShortExample (step)
PURE_ON = bytes.fromhex("f20d03fc0140031052")  # Filter: pure_on
PURE_OFF = bytes.fromhex("f20d03fc0140030042")  # Filter: pure_off
LONG_ECONO = bytes.fromhex("f20d04fb09c0620003a8")  # ConstructLongState
SWING_ON = bytes.fromhex("f20d01fe210120")  # SwingCodes: swingOnState
SWING_OFF = bytes.fromhex("f20d01fe210223")  # SwingCodes: swingOffState
SWING_TOGGLE = bytes.fromhex("f20d01fe210425")  # SwingCodes: swingToggleState

MODES = ("auto", "cool", "dry", "fan", "heat")
FANS = ("auto", "1", "2", "3", "4", "5")


def device(model="generic"):
    return ToshibaAcDevice("toshiba", model)


def state(power=True, mode="cool", temperature=22.0, **kw):
    return device().normalise(HvacState(power, mode, temperature, **kw))


def features(powerful=False, economy=False, purifier=False):
    return {"powerful": powerful, "economy": economy, "purifier": purifier}


def frames(target, previous=None):
    return device().frames(previous, target, ())


def message(target):
    """The state message (the first frame)."""
    return frames(target)[0].data


def read(target):
    data = message(target)
    layout = TOSHIBA_AC_LONG_LAYOUT if len(data) == 10 else TOSHIBA_AC_LAYOUT
    return layout.read(data)


def layouts(dev, record):
    return dev.layouts(state_from_record(dev, record["state"]))


@pytest.mark.parametrize("record", oracle_params("TOSHIBA_AC"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, layouts(dev, record), DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("TOSHIBA_AC"):
        target = state_from_record(dev, record["state"])
        for frame, layout in zip(dev.frames(None, target, ()), dev.layouts(target)):
            values = layout.read(frame.data)
            assert layout.build(**values) == bytearray(frame.data)


# States the oracle grid lacks: off in every mode, every setpoint edge and
# fan level in every mode, and every combination of swing and features, on
# and off.
EXTRA_STATES = [
    {"mode": mode, "temperature": t, "fan": fan, "swing": "off"}
    for mode in MODES + ("off",)
    for t in (17, 18, 22, 29, 30)
    for fan in ("auto", "lowest", "low", "medium", "high", "highest")
] + [
    {
        "mode": mode,
        "temperature": 25,
        "fan": "medium",
        "swing": swing,
        "powerful": powerful,
        "economy": economy,
        "purifier": purifier,
    }
    for mode in MODES + ("off",)
    for swing in ("off", "on")
    for powerful, economy, purifier in itertools.product(("off", "on"), repeat=3)
]


def test_states_beyond_the_oracle_grid_match_the_c_path():
    pytest.importorskip("pyhvac.irhvac")
    dev = device()
    record = load_oracle("TOSHIBA_AC")[0]
    for rec in c_sequence(record, EXTRA_STATES):
        assert_matches_oracle(dev, rec, layouts(dev, rec), DEFECTS)


def test_checksums_hold_on_the_real_captures():
    for data, layout in (
        (REAL_AUTO_23, TOSHIBA_AC_LAYOUT),
        (REAL_COOL_17, TOSHIBA_AC_LAYOUT),
        (REAL_HEAT_24, TOSHIBA_AC_LAYOUT),
        (REAL_OFF_22, TOSHIBA_AC_LAYOUT),
        (REAL_WHUB03NJ_OFF, TOSHIBA_AC_LAYOUT),
        (PURE_ON, TOSHIBA_AC_LAYOUT),
        (REAL_HIGH_POWER, TOSHIBA_AC_LONG_LAYOUT),
        (LONG_ECONO, TOSHIBA_AC_LONG_LAYOUT),
        (REAL_AIR_DIRECTION, TOSHIBA_AC_SWING_LAYOUT),
        (SWING_TOGGLE, TOSHIBA_AC_SWING_LAYOUT),
    ):
        assert layout.checksum.check(data)
        broken = bytearray(data)
        broken[5] ^= 0x10
        assert not layout.checksum.check(broken)
        broken = bytearray(data)
        broken[2] ^= 0x10
        assert not layout.checksum.check(broken)


@pytest.mark.parametrize(
    "data, layout, fields",
    [
        (REAL_AUTO_23, TOSHIBA_AC_LAYOUT, {"mode": "auto", "temperature": 23}),
        (REAL_HEAT_24, TOSHIBA_AC_LAYOUT, {"mode": "heat", "fan": "5"}),
        (REAL_OFF_22, TOSHIBA_AC_LAYOUT, {"mode": "off", "fan": "4", "length": 3}),
        (
            REAL_HIGH_POWER,
            TOSHIBA_AC_LONG_LAYOUT,
            {"eco_turbo": "turbo", "length": 4, "long_msg": 1, "short_msg": 0},
        ),
        (
            REAL_AIR_DIRECTION,
            TOSHIBA_AC_SWING_LAYOUT,
            {"swing": "step", "temperature": 17, "length": 1, "short_msg": 1},
        ),
        (PURE_ON, TOSHIBA_AC_LAYOUT, {"filter": 1, "mode": "heat"}),
    ],
)
def test_layout_reads_the_real_captures(data, layout, fields):
    values = layout.read(data)
    assert {k: values[k] for k in fields} == fields
    assert layout.build(**values) == bytearray(data)


@pytest.mark.parametrize(
    "target, expected",
    [
        # RealExamples rawData1: auto, 23 C, fan auto.
        (lambda: state(True, "auto", 23.0), REAL_AUTO_23),
        # rawData2: cool, 17 C, getFan 3 (medium).
        (lambda: state(True, "cool", 17.0, fan="3"), REAL_COOL_17),
        # rawData3: heat, 24 C, getFan kToshibaAcFanMax (highest).
        (lambda: state(True, "heat", 24.0, fan="5"), REAL_HEAT_24),
        # rawData4: power off, 22 C, getFan 4 (high).
        (lambda: state(False, "auto", 22.0, fan="4"), REAL_OFF_22),
        # RealExample_WHUB03NJ: power off, 20 C, fan auto.
        (lambda: state(False, "cool", 20.0), REAL_WHUB03NJ_OFF),
        # RealLongExample: auto, 22 C, fan auto, turbo.
        (
            lambda: state(True, "auto", 22.0, features=features(powerful=True)),
            REAL_HIGH_POWER,
        ),
        # Filter: pure_on / pure_off (heat, 21 C, fan auto).
        (lambda: state(True, "heat", 21.0, features=features(purifier=True)), PURE_ON),
        (lambda: state(True, "heat", 21.0), PURE_OFF),
        # ConstructLongState: dry, 29 C, setFan(2) (low), econo.
        (
            lambda: state(True, "dry", 29.0, fan="2", features=features(economy=True)),
            LONG_ECONO,
        ),
    ],
)
def test_port_reproduces_the_captures(target, expected):
    assert message(target()) == expected


@pytest.mark.parametrize("swing, expected", [("swing", SWING_ON), ("off", SWING_OFF)])
def test_swing_message_is_the_documented_swing_state(swing, expected):
    # SwingCodes: swingOnState / swingOffState, whatever the setpoint.
    for target in (state(swing_v=swing), state(False, "heat", 30.0, swing_v=swing)):
        assert frames(target)[2].data == expected


def test_message_is_the_state_twice_then_the_swing_message_twice():
    for target in (
        state(True),
        state(False),
        state(True, features=features(powerful=True)),
    ):
        a, b, c, d = frames(target)
        assert a == b and c == d
        assert len(c.data) == 7


@pytest.mark.parametrize("mode", MODES)
def test_mode_uses_its_documented_value(mode):
    codes = {"auto": 0, "cool": 1, "dry": 2, "heat": 3, "fan": 4}
    assert TOSHIBA_AC_LAYOUT.read_raw(message(state(True, mode)), "mode") == codes[mode]


@pytest.mark.parametrize("fan, raw", zip(FANS, (0, 2, 3, 4, 5, 6)))
def test_fan_is_the_speed_plus_one(fan, raw):
    # convertFan (kToshibaAcFanMax - 4 .. kToshibaAcFanMax), then setFan's +1,
    # as rawData2 (3 -> 4), rawData3 (max -> 6) and rawData4 (4 -> 5) carry.
    assert TOSHIBA_AC_LAYOUT.read_raw(message(state(fan=fan)), "fan") == raw


@pytest.mark.parametrize("t", range(17, 31))
def test_setpoint_is_sent_in_the_state_message(t):
    assert read(state(True, "cool", float(t)))["temperature"] == t


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("t", [17.0, 25.0, 30.0])
def test_off_carries_mode_off_and_the_target_settings(mode, t):
    off = state(False, mode, t, fan="3", features=features(purifier=True))
    assert message(off) == message(
        state(False, "auto", t, fan="3", features=features(purifier=True))
    )
    values = read(off)
    assert (values["mode"], values["temperature"]) == ("off", int(t))
    assert (values["fan"], values["filter"]) == ("3", 1)


@pytest.mark.parametrize(
    "powerful, economy, eco_turbo",
    [(True, False, "turbo"), (False, True, "econo"), (True, True, "econo")],
)
def test_powerful_and_economy_make_the_long_message(powerful, economy, eco_turbo):
    target = state(features=features(powerful=powerful, economy=economy))
    data = message(target)
    assert len(data) == 10
    values = TOSHIBA_AC_LONG_LAYOUT.read(data)
    assert values["eco_turbo"] == eco_turbo
    assert (values["length"], values["long_msg"], values["short_msg"]) == (4, 1, 0)


@pytest.mark.parametrize("powerful, economy", [(True, False), (False, True)])
def test_purifier_and_off_drop_powerful_and_economy(powerful, economy):
    extra = features(powerful=powerful, economy=economy)
    with_purifier = {**extra, "purifier": True}
    assert message(state(features=with_purifier)) == message(
        state(features=features(purifier=True))
    )
    assert message(state(False, features=extra)) == message(state(False))


def test_previous_is_ignored():
    target = state(True, "cool", 22.0, swing_v="swing")
    for previous in (None, state(False, "heat", 30.0), target):
        assert frames(target, previous) == frames(target)


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (4400, 4300)
    assert pulses[-2:] == (580, 7400)
    assert len(pulses) == 2 * (2 + 2 * 72 + 2) + 2 * (2 + 2 * 56 + 2)


@pytest.mark.parametrize(
    "plugin, model",
    [("toshiba", m) for m in TOSHIBA_AC_MODELS]
    + [("carrier", m) for m in TOSHIBA_AC_CARRIER_MODELS],
)
def test_registry_serves_the_port(plugin, model):
    assert isinstance(registry.get_device(plugin, model), ToshibaAcDevice)


def test_capabilities_are_the_documented_ones():
    # Unchanged by the capability audit: every value ir_Toshiba.h documents
    # that the port sends (kToshibaAcSwingStep / Toggle are button presses).
    caps = ToshibaAcDevice.capabilities
    assert caps.modes == MODES
    # kToshibaAcMinTemp / kToshibaAcMaxTemp, whole degrees (Temp is 4 bits).
    assert (caps.temperature.min, caps.temperature.max) == (17.0, 30.0)
    assert caps.temperature.decimals == (0,)
    assert caps.fan.values == FANS  # kToshibaAcFanAuto, 1 .. kToshibaAcFanMax
    assert caps.swing_v.values == ("off", "swing")  # SwingOff / SwingOn
    assert caps.swing_h is None
    assert set(caps.features) == {"powerful", "economy", "purifier"}


def test_undeclared_swing_deviation_is_reported():
    dev = device()
    record = next(
        r for r in load_oracle("TOSHIBA_AC") if r["state"].get("swing") == "on"
    )
    with pytest.raises(AssertionError, match="swing"):
        assert_matches_oracle(dev, record, layouts(dev, record), ())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("TOSHIBA_AC")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:2], DEFECTS)
