import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.airton import (
    AIRTON_LAYOUT,
    AIRTON_MODELS,
    AirtonDevice,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Airton values here:
# - the legacy glue's IRGHVAC.trans_swing has no "on" key, so swing "on"
#   never reached IRac (swingv stayed kOff) and SwingV stayed clear.
DEFECTS = (Defect("swing_v", 1, 0, "legacy trans_swing has no 'on' key"),)

FEATURES = ("purifier", "powerful", "economy", "light", "sleep")
MODES = ("auto", "cool", "dry", "fan", "heat")


def device():
    return AirtonDevice("airton", "generic")


def state(power=True, mode="cool", temperature=22.0, **kw):
    return device().normalise(HvacState(power, mode, temperature, **kw))


def read(target, previous=None):
    (main,) = device().frames(previous, target, ())
    return AIRTON_LAYOUT.read(main.data)


def raw(target):
    (main,) = device().frames(None, target, ())
    return int.from_bytes(main.data, "little")


@pytest.mark.parametrize("record", oracle_params("AIRTON"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("AIRTON"):
        (main,) = dev.frames(None, state_from_record(dev, record["state"]), ())
        values = AIRTON_LAYOUT.read(main.data)
        assert AIRTON_LAYOUT.build(**values) == bytearray(main.data)


# ir_Airton_test.cpp captures.
CAPTURES = [
    # RealExample / ConstructKnownExamples: heat 25C, fan auto, power on.
    (
        0x5E1400090C11D3,
        {"mode": "heat", "power": 1, "temperature": 25, "heat_on": 1},
    ),
    # SwingV: cool 21C, powered off, swing on.
    (0xBC0401050111D3, {"mode": "cool", "power": 0, "swing_v": 1}),
    # Light: cool 20C, swing, light; NotAutoOn clear, unknown bit 5.3 set.
    (
        0x298801040911D3,
        {"temperature": 20, "light": 1, "not_auto_on": 0, "unknown5_3": 1},
    ),
    # Turbo: cool 16C, turbo with fan max.
    (0x92040000D911D3, {"turbo": 1, "fan": "5", "temperature": 16}),
    # Sleep: cool 16C, sleep on.
    (0xA00600000911D3, {"sleep": 1, "mode": "cool", "not_auto_on": 1}),
    # Health / Econo: cool 16C, econo, health, light, unknown bit 5.3 set.
    (
        0xE5C900000911D3,
        {"econo": 1, "health": 1, "light": 1, "not_auto_on": 0, "unknown5_3": 1},
    ),
    # Checksums: cool 22C swing light; dry 18C fan min light.
    (0x2F8801060911D3, {"mode": "cool", "temperature": 22, "unknown5_3": 1}),
    (0xDB8800021A11D3, {"mode": "dry", "temperature": 18, "fan": "1"}),
]


@pytest.mark.parametrize("value, fields", CAPTURES)
def test_layout_reads_the_real_captures(value, fields):
    data = value.to_bytes(7, "little")
    values = AIRTON_LAYOUT.read(data)
    assert {k: values[k] for k in fields} == fields
    assert AIRTON_LAYOUT.build(**values) == bytearray(data)
    assert AIRTON_LAYOUT.checksum.check(data)


def test_checksum_rejects_the_bad_capture():
    # TestIRAirtonAcClass.Checksums: 0x551400090C11D3 is invalid, 0x5E valid.
    assert not AIRTON_LAYOUT.checksum.check((0x551400090C11D3).to_bytes(7, "little"))
    good = (0x5E1400090C11D3).to_bytes(7, "little")
    assert AIRTON_LAYOUT.checksum.compute(good) == 0x5E


@pytest.mark.parametrize(
    "target, value",
    [
        # RealExample: heat 25C, fan auto.
        (dict(mode="heat", temperature=25.0), 0x5E1400090C11D3),
        # Turbo: cool 16C, powerful (fan forced to max).
        (dict(temperature=16.0, features={"powerful": True}), 0x92040000D911D3),
    ],
)
def test_port_reproduces_the_real_captures(target, value):
    assert raw(state(**target)) == value


@pytest.mark.parametrize(
    "target, value",
    [
        # Light: cool 20C, swing, light.
        (
            dict(temperature=20.0, swing_v="swing", features={"light": True}),
            0x298801040911D3,
        ),
        # Health/Econo: cool 16C, economy, purifier, light.
        (
            dict(
                temperature=16.0,
                features={"economy": True, "purifier": True, "light": True},
            ),
            0xE5C900000911D3,
        ),
        # Checksums: cool 22C swing light; dry 18C, fan lowest, light.
        (
            dict(temperature=22.0, swing_v="swing", features={"light": True}),
            0x2F8801060911D3,
        ),
        (
            dict(mode="dry", temperature=18.0, fan="1", features={"light": True}),
            0xDB8800021A11D3,
        ),
    ],
)
def test_light_captures_differ_only_in_the_undocumented_bits(target, value):
    # These remotes set the Unknown bit 5.3 and clear NotAutoOn; the port
    # follows IRAirtonAc::setMode (NotAutoOn set outside auto, bit 5.3 clear).
    ours = read(state(**target))
    theirs = AIRTON_LAYOUT.read(value.to_bytes(7, "little"))
    assert (ours["not_auto_on"], ours["unknown5_3"]) == (1, 0)
    assert (theirs["not_auto_on"], theirs["unknown5_3"]) == (0, 1)
    assert {
        k: v for k, v in ours.items() if k not in ("not_auto_on", "unknown5_3")
    } == {k: v for k, v in theirs.items() if k not in ("not_auto_on", "unknown5_3")}


@pytest.mark.parametrize("mode", ["cool", "dry", "fan", "heat"])
@pytest.mark.parametrize("t", [16.0, 20.0, 25.0])
def test_setpoint_is_sent_outside_auto(mode, t):
    assert read(state(True, mode, t))["temperature"] == int(t)


@pytest.mark.parametrize("power", [True, False])
@pytest.mark.parametrize("t", [16.0, 25.0])
def test_auto_sends_31c(power, t):
    # IRAirtonAc::setTemp forces kAirtonMaxTemp in mode auto.
    assert read(state(power, "auto", t))["temperature"] == 31


@pytest.mark.parametrize("mode", MODES)
def test_off_carries_mode_auto(mode):
    # The glue sends opmode kOff; convertMode maps it to kAirtonAuto.
    values = read(state(False, mode, 20.0, features={"economy": True}))
    assert (values["mode"], values["power"], values["temperature"]) == ("auto", 0, 31)
    assert (values["not_auto_on"], values["heat_on"], values["econo"]) == (1, 0, 0)


@pytest.mark.parametrize("mode", MODES)
def test_mode_bits_when_powered(mode):
    values = read(state(True, mode))
    assert (values["mode"], values["power"]) == (mode, 1)
    assert values["not_auto_on"] == (mode != "auto")
    assert values["heat_on"] == (mode == "heat")


@pytest.mark.parametrize("fan", ["auto", "1", "2", "3", "4", "5"])
def test_every_fan_level_uses_its_documented_code(fan):
    codes = {"auto": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5}
    assert AIRTON_LAYOUT.read_raw(
        device().frames(None, state(fan=fan), ())[0].data, "fan"
    ) == (codes[fan])


@pytest.mark.parametrize("fan", ["auto", "1", "3", "5"])
def test_powerful_sets_turbo_and_fan_max(fan):
    values = read(state(fan=fan, features={"powerful": True}))
    assert (values["turbo"], values["fan"]) == (1, "5")


@pytest.mark.parametrize("mode", MODES)
def test_economy_is_sent_in_cool_only(mode):
    assert read(state(True, mode, features={"economy": True}))["econo"] == (
        mode == "cool"
    )


def test_purifier_and_light_set_their_bits():
    values = read(state(features={"purifier": True, "light": True}))
    assert (values["health"], values["light"]) == (1, 1)
    values = read(state())
    assert (values["health"], values["light"]) == (0, 0)


def test_swing_sets_swing_v():
    assert read(state(swing_v="swing"))["swing_v"] == 1
    assert read(state(swing_v="off"))["swing_v"] == 0


def test_quiet_is_not_offered():
    # ir_Airton.h has no quiet bit (IRac::airton: "No Quiet setting
    # available"): a control that did nothing is removed.
    assert "quiet" not in device().capabilities.features
    assert "quiet" not in state(features={"quiet": True}).features


def test_setpoint_range_is_the_headers():
    # kAirtonMinTemp = 16, kAirtonMaxTemp = 31.
    rng = device().capabilities.temperature
    assert (rng.min, rng.max, rng.decimals) == (16.0, 31.0, (0,))


@pytest.mark.parametrize("t", [26.0, 28.0, 31.0])
def test_setpoints_up_to_31_are_sent(t):
    # IRAirtonAc::setTemp clamps to kAirtonMaxTemp (31).
    assert read(state(True, "cool", t))["temperature"] == int(t)
    assert read(state(True, "heat", 32.0))["temperature"] == 31


@pytest.mark.parametrize("mode", MODES)
def test_sleep_sets_its_bit_outside_auto_and_fan(mode):
    # IRAirtonAc::setSleep: "Sleep not available in fan or auto mode".
    assert read(state(True, mode, features={"sleep": True}))["sleep"] == (
        mode not in ("auto", "fan")
    )
    assert read(state(True, mode))["sleep"] == 0


@pytest.mark.parametrize("mode", MODES)
def test_off_clears_sleep(mode):
    # An off message carries mode auto, where setSleep clears it.
    assert read(state(False, mode, features={"sleep": True}))["sleep"] == 0


def test_port_reproduces_the_real_sleep_capture():
    # ir_Airton_test.cpp Sleep: cool 16C, fan auto, sleep on.
    assert raw(state(temperature=16.0, features={"sleep": True})) == 0xA00600000911D3


def test_previous_is_ignored():
    target = state(True, "heat", 22.0)
    other = state(False, "cool", 16.0)
    assert device().frames(other, target, ()) == device().frames(None, target, ())


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (6630, 3350)
    assert pulses[-2:] == (400, 100000)
    assert len(pulses) == 2 + 2 * 56 + 2


@pytest.mark.parametrize("model", AIRTON_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("airton", model), AirtonDevice)


def test_undeclared_swing_deviation_is_reported():
    dev = device()
    record = next(
        r
        for r in load_oracle("AIRTON")
        if r["state"].get("swing") == "on" and r["state"]["mode"] != "off"
    )
    with pytest.raises(AssertionError, match="swing_v"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("AIRTON")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)
