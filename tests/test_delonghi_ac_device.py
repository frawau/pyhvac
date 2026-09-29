import pytest

from c_oracle import c_encode

from oracle import load_oracle
from port_oracle import assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.delonghi import (
    DELONGHI_AC_LAYOUT,
    DELONGHI_AC_MODELS,
    DelonghiAcDevice,
)
from pyhvac.state import HvacState

# The port matches every oracle record byte for byte: no Defect is declared.


def device():
    return DelonghiAcDevice("delonghi", "PAC A95")


def state(power=True, mode="cool", temperature=22.0, **kw):
    return device().normalise(HvacState(power, mode, temperature, **kw))


def read(target, previous=None):
    (main,) = device().frames(previous, target, ())
    return DELONGHI_AC_LAYOUT.read(main.data)


def raw(target):
    (main,) = device().frames(None, target, ())
    return int.from_bytes(main.data, "little")


@pytest.mark.parametrize("record", oracle_params("DELONGHI_AC"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("DELONGHI_AC"):
        (main,) = dev.frames(None, state_from_record(dev, record["state"]), ())
        values = DELONGHI_AC_LAYOUT.read(main.data)
        assert DELONGHI_AC_LAYOUT.build(**values) == bytearray(main.data)


@pytest.mark.parametrize(
    "value, fields",
    [
        # ir_Delonghi_test.cpp RealExample: cool, fan low, 90F, on timer 6:13.
        (
            0x6900000D0D01FB53,
            {
                "power": 1,
                "mode": "cool",
                "fan": "1",
                "fahrenheit": 1,
                "temperature": 27,  # 90F - kDelonghiAcTempMinF + 1
                "on_timer": 1,
                "on_hours": 6,
                "on_mins": 13,
                "off_timer": 0,
            },
        ),
        # Power: power on / power off (the stateReset word).
        (0x5500000000010153, {"power": 1, "mode": "cool", "temperature": 1}),
        (0x5400000000000153, {"power": 0, "mode": "cool", "temperature": 1}),
        # Real off timer: 16 h 46 min, on timer off.
        (
            0xB12E210000000F53,
            {"off_timer": 1, "off_hours": 16, "off_mins": 46, "on_timer": 0},
        ),
    ],
)
def test_layout_reads_the_real_captures(value, fields):
    data = value.to_bytes(8, "little")
    values = DELONGHI_AC_LAYOUT.read(data)
    assert {k: values[k] for k in fields} == fields
    assert DELONGHI_AC_LAYOUT.build(**values) == bytearray(data)
    assert DELONGHI_AC_LAYOUT.checksum.check(data)


def test_port_reproduces_the_power_on_capture():
    # 0x5500000000010153 (ir_Delonghi_test.cpp, Power): on, cool, 18C, fan auto.
    assert raw(state(True, "cool", 18.0)) == 0x5500000000010153


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan"])
def test_off_carries_mode_auto(mode):
    # Oracle "off" records: convertMode maps IRac's off to kDelonghiAcAuto.
    values = read(state(False, mode, 20.0))
    assert (values["power"], values["mode"], values["fan"]) == (0, "auto", "auto")
    assert values["temperature"] == 20 - 17


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan"])
@pytest.mark.parametrize(
    "t, sent",
    [(16.0, 18), (17.0, 18), (20.0, 20), (25.0, 25), (26.0, 26), (32.0, 32), (33, 32)],
)
def test_setpoint_is_sent_in_every_mode_clamped_to_18_32(mode, t, sent):
    # IRac calls setTemp after setMode, so the setpoint replaces the special
    # auto/dry/fan temperatures (oracle records at 16, 20 and 25 C).
    # Temp is degrees - kDelonghiAcTempMinC + 1.
    assert read(state(True, mode, t))["temperature"] == sent - 17


@pytest.mark.parametrize(
    "mode, fan", [("auto", "auto"), ("cool", "auto"), ("dry", "auto"), ("fan", "3")]
)
def test_fan_is_high_in_fan_mode_else_auto(mode, fan):
    # setFan: fan mode can't have auto; auto and dry only allow auto.
    assert read(state(True, mode))["fan"] == fan


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan"])
def test_mode_uses_its_documented_value(mode):
    codes = {"cool": 0, "dry": 1, "fan": 2, "auto": 4}
    (main,) = device().frames(None, state(True, mode), ())
    assert DELONGHI_AC_LAYOUT.read_raw(main.data, "mode") == codes[mode]


@pytest.mark.parametrize("power", [True, False])
def test_powerful_sets_the_boost_bit(power):
    on = state(power, "cool", features={"powerful": True})
    off = state(power, "cool", features={"powerful": False})
    assert (read(on)["boost"], read(off)["boost"]) == (1, 0)


def test_quiet_is_not_offered():
    # No quiet bit in ir_Delonghi.h: the control that did nothing is removed.
    assert "quiet" not in device().capabilities.features
    base = state(True, "auto", 20.0)
    quiet = state(True, "auto", 20.0, features={"quiet": True})
    assert "quiet" not in quiet.features
    assert raw(quiet) == raw(base)


def test_setpoint_range_is_the_headers():
    # kDelonghiAcTempMinC = 18, kDelonghiAcTempMaxC = 32.
    rng = device().capabilities.temperature
    assert (rng.min, rng.max, rng.decimals) == (18.0, 32.0, (0,))
    assert state(True, "cool", 16.0).temperature == 18.0


def test_fan_offers_the_headers_speeds_and_auto():
    # kDelonghiAcFanAuto/Low/Medium/High.
    fan = device().capabilities.fan
    assert fan.values == ("auto", "1", "2", "3")
    assert [fan.label(v) for v in fan.values] == ["auto", "low", "medium", "high"]


@pytest.mark.parametrize("fan, code", [("1", 3), ("2", 2), ("3", 1)])
@pytest.mark.parametrize("mode", ["cool", "fan"])
def test_every_fan_speed_uses_its_documented_code(mode, fan, code):
    # kDelonghiAcFanLow = 0b11, kDelonghiAcFanMedium = 0b10,
    # kDelonghiAcFanHigh = 0b01.
    target = state(True, mode, fan=fan)
    assert target.fan == fan
    (main,) = device().frames(None, target, ())
    assert DELONGHI_AC_LAYOUT.read_raw(main.data, "fan") == code


@pytest.mark.parametrize("mode", ["auto", "dry"])
@pytest.mark.parametrize("fan", ["1", "2", "3"])
def test_auto_and_dry_allow_fan_auto_only(mode, fan):
    # setFan: "Auto & Dry modes only allows auto fan speed".
    target = state(True, mode, fan=fan)
    assert target.fan == "auto"
    assert read(target)["fan"] == "auto"


def test_fan_mode_turns_auto_into_high():
    # setFan: "Fan mode can't have auto fan speed" (stateReset's auto -> high).
    assert state(True, "fan", fan="auto").fan == "3"
    assert read(state(True, "fan", fan="auto"))["fan"] == "3"


@pytest.mark.parametrize("fan", ["1", "3"])
def test_off_sends_fan_auto(fan):
    # An off message is mode auto, where setFan forces auto.
    assert read(state(False, "cool", fan=fan))["fan"] == "auto"


@pytest.mark.parametrize("power", [True, False])
@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan"])
def test_sleep_sets_the_sleep_bit(power, mode):
    # IRDelonghiAc::setSleep: the Sleep bit, in every mode.
    assert read(state(power, mode, features={"sleep": True}))["sleep"] == 1
    assert read(state(power, mode))["sleep"] == 0


def test_unset_fields_stay_clear():
    values = read(state(True, "fan", 25.0, features={"powerful": True}))
    for name in (
        "fahrenheit",
        "on_timer",
        "on_hours",
        "on_mins",
        "off_timer",
        "off_hours",
        "off_mins",
    ):
        assert values[name] == 0, name


def test_previous_is_ignored():
    dev = device()
    on = HvacState(True, "cool", 22.0)
    off = HvacState(False, "dry", 18.0)
    assert dev.encode(None, on).signal == dev.encode(off, on).signal


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (8984, 4200)
    assert pulses[-2:] == (572, 100000)
    assert len(pulses) == 2 + 2 * 64 + 2


@pytest.mark.parametrize("model", DELONGHI_AC_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("delonghi", model), DelonghiAcDevice)


@pytest.mark.parametrize(
    "power, mode, t, powerful",
    [
        (False, "cool", 22.0, True),
        (False, "fan", 17.0, True),
        (False, "dry", 25.0, False),
        (True, "fan", 21.0, True),
        (True, "dry", 17.0, True),
        (True, "cool", 18.0, True),
    ],
)
def test_states_outside_the_oracle_match_the_c_path(power, mode, t, powerful):
    # C-only: off messages with boost, 17 C and boost in every mode, which the
    # oracle grid lacks, against the legacy C encoder.
    from pyhvac.ir.codec import decode

    dev = device()
    target = HvacState(power, mode, t, features={"powerful": powerful})
    pulses = c_encode("delonghi", "PAC A95", "Delonghi", target)
    (theirs,) = decode(dev.PROTOCOL, pulses, expected=["main"])
    (ours,) = dev.frames(None, dev.normalise(target), ())
    assert ours.data == theirs.data


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("DELONGHI_AC")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, ())
