import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.ir.codec import decode
from pyhvac.plugins.neoclima import (
    NEOCLIMA,
    NEOCLIMA_LAYOUT,
    NEOCLIMA_MODELS,
    NEOCLIMA_SOLEUS_MODELS,
    NeoclimaDevice,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Neoclima values here:
# - the old glue (IRGHVAC.trans_swing / trans_hswing) has no "on" entry, so
#   IRac's swingv/swingh stay kOff: setSwingV(false) sends kNeoclimaSwingVOff
#   and setSwingH(false) sets the SwingH bit. The port sends kNeoclimaSwingVOn
#   and clears the SwingH bit (the header's "Cleared when on").
# - the old glue (IRGHVAC.build_ircode) has no "sleep" key, so IRac gets
#   sleep -1 and setSleep(sleep >= 0) always clears the Sleep bit.
DEFECTS = (
    Defect("swing_v", "swing", "off", "legacy trans_swing has no 'on'"),
    Defect("swing_h", "swing", "off", "legacy trans_hswing has no 'on'"),
    Defect("sleep", 1, 0, "legacy glue never passes sleep"),
)

ALL_MODELS = [("neoclima", m) for m in NEOCLIMA_MODELS] + [
    ("soleus", m) for m in NEOCLIMA_SOLEUS_MODELS
]
FEATURES = ("sleep", "powerful", "purifier", "economy", "light")


def device():
    return NeoclimaDevice("neoclima", "NS-09AHTI")


def state(power=True, mode="cool", temperature=22.0, **kw):
    return device().normalise(HvacState(power, mode, temperature, **kw))


def data(target, previous=None):
    (main,) = device().frames(previous, target, ())
    return main.data


def read(target, previous=None):
    return NEOCLIMA_LAYOUT.read(data(target, previous))


@pytest.mark.parametrize("record", oracle_params("NEOCLIMA"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_oracle_covers_the_legacy_class():
    seen = {(r["plugin"], r["model"], r["class"]) for r in load_oracle("NEOCLIMA")}
    assert seen == {("neoclima", "NS-09AHTI", "Neoclima")}


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("NEOCLIMA"):
        (main,) = dev.frames(None, state_from_record(dev, record["state"]), ())
        values = NEOCLIMA_LAYOUT.read(main.data)
        assert NEOCLIMA_LAYOUT.build(**values) == bytearray(main.data)
        assert NEOCLIMA_LAYOUT.checksum.check(main.data)


def test_every_oracle_frame_has_the_sum8_checksum_and_the_fixed_bytes():
    for record in load_oracle("NEOCLIMA"):
        (frame,) = decode(NEOCLIMA, record["pulses"], expected=["main"])
        assert frame.data[11] == sum(frame.data[:11]) & 0xFF
        assert frame.data[10] == 0xA5  # kReset's byte 10
        assert NEOCLIMA_LAYOUT.read(frame.data)["button"] == "power"


def test_checksum_known_values():
    # TestIRNeoclimaAcClass.ChecksumCalculation.
    frame = bytearray.fromhex("000000000000006a002aa539")
    assert NEOCLIMA_LAYOUT.checksum.check(frame)
    frame[8] = 0x01
    assert NEOCLIMA_LAYOUT.checksum.compute(frame) == 0x3A


def test_skeleton_is_the_reset_state():
    # IRNeoclimaAc::stateReset (and SendDataOnly's state): cool, 26 C, fan
    # low, swing_v off, swing_h on, power on, button power.
    values = NEOCLIMA_LAYOUT.read(NEOCLIMA_LAYOUT.skeleton)
    assert (values["mode"], values["temp"], values["fan"]) == ("cool", 26, "1")
    assert (values["swing_v"], values["swing_h"]) == ("off", "swing")
    assert (values["power"], values["button"]) == (1, "power")
    assert NEOCLIMA_LAYOUT.checksum.check(NEOCLIMA_LAYOUT.skeleton)


def test_port_reproduces_the_real_example():
    # TestDecodeNeoclima.RealExample (issue 764): a real remote's cool,
    # 26 C, fan low, swing_v off, swing_h on, button power.
    raw = (
        "6112 7392 540 602 516 578 522 604 540 554 540 554 540 576 518 576 "
        "516 554 540 608 542 554 540 554 540 576 518 604 516 556 540 576 546 "
        "580 542 578 542 602 518 554 542 554 568 582 540 554 540 582 540 578 "
        "518 582 542 576 544 530 566 534 562 534 562 552 542 582 540 604 518 "
        "608 542 554 540 582 540 604 518 580 540 606 544 554 542 554 542 580 "
        "542 576 520 554 540 578 518 578 518 582 544 552 570 580 544 580 542 "
        "554 542 604 520 576 520 580 540 556 540 556 542 584 566 580 542 1622 "
        "542 554 542 1620 544 604 520 1642 518 1674 548 560 564 580 544 554 "
        "544 552 544 554 542 556 542 576 522 554 542 556 542 580 542 1670 520 "
        "578 520 1622 542 580 518 1646 520 558 568 552 546 1628 566 580 544 "
        "1668 522 576 520 578 520 1670 522 576 522 1670 496 1676 570 560 566 "
        "532 564 1648 544 1670 522 1650 544 552 544 576 520 7390 544"
    )
    pulses = [int(x) for x in raw.split()] + [100000]
    (frame,) = decode(NEOCLIMA, pulses, expected=["main"])
    expected = bytes.fromhex("000000000000006a002aa539")
    assert frame.data == expected
    target = state(True, "cool", 26.0, fan="1", swing_h="swing")
    assert data(target) == expected


def test_message_shape_matches_send_data_only():
    # TestSendNeoclima.SendDataOnly: header, 96 bits, the sendGeneric footer
    # (mark + kNeoclimaHdrSpace), the extra mark and kNeoclimaMinGap.
    target = state(True, "cool", 26.0, fan="1", swing_h="swing")
    signal = device().encode(None, target).signal
    assert signal.carrier == 38000
    assert signal.pulses[:2] == (6112, 7391)
    assert signal.pulses[-4:] == (537, 7391, 537, 100000)
    assert len(signal.pulses) == 2 + 2 * 96 + 4


@pytest.mark.parametrize(
    "capture, mode, temp, fan, button",
    [
        # TestIRNeoclimaAcClass.FanSpeed: cool 25 C, button fan speed.
        ("00 00 00 00 00 05 00 6A 00 29 A5 3D", "cool", 25, "1", "fan_speed"),
        ("00 00 00 00 00 05 00 4A 00 29 A5 1D", "cool", 25, "2", "fan_speed"),
        ("00 00 00 00 00 05 00 2A 00 29 A5 FD", "cool", 25, "3", "fan_speed"),
        ("00 00 00 00 00 05 00 0A 00 29 A5 DD", "cool", 25, "auto", "fan_speed"),
    ],
)
def test_real_fan_captures_except_the_button(capture, mode, temp, fan, button):
    # The real remote names the key pressed (FanSpeed); IRac always sends
    # kNeoclimaButtonPower, and so does the port. Everything else matches.
    capture = bytes.fromhex(capture)
    ours = data(state(True, mode, float(temp), fan=fan, swing_h="swing"))
    assert NEOCLIMA_LAYOUT.read(ours)["button"] == "power"
    patched = bytearray(ours)
    NEOCLIMA_LAYOUT.write_raw(
        patched, "button", NEOCLIMA_LAYOUT.fields["button"].values[button]
    )
    NEOCLIMA_LAYOUT.checksum.apply(patched)
    assert bytes(patched) == capture


@pytest.mark.parametrize(
    "capture, turbo",
    [
        # TestIRNeoclimaAcClass.Turbo: heat 24 C, fan low, button turbo.
        ("00 00 00 08 00 0A 00 6A 00 88 A5 A9", True),
        ("00 00 00 00 00 0A 00 6A 00 88 A5 A1", False),
    ],
)
def test_real_turbo_captures_except_the_button(capture, turbo):
    capture = bytes.fromhex(capture)
    target = state(
        True, "heat", 24.0, fan="1", swing_h="swing", features={"powerful": turbo}
    )
    patched = bytearray(data(target))
    NEOCLIMA_LAYOUT.write_raw(patched, "button", 0x0A)  # kNeoclimaButtonTurbo
    NEOCLIMA_LAYOUT.checksum.apply(patched)
    assert bytes(patched) == capture


@pytest.mark.parametrize(
    "capture, fields",
    [
        # Econo (issue 1260): cool 16 C, fan high, SwingV 0b00, button econo.
        (
            "00 00 00 10 00 0D 00 22 00 20 A5 04",
            {"econo": 1, "button": "econo", "swing_v": 0, "fan": "3", "temp": 16},
        ),
        # Temperature (issue 1260): 68 F, UseFah set, button temp unit.
        ("00 00 00 10 00 1E 00 A2 00 27 A5 9C", {"use_fah": 1, "button": "temp_unit"}),
        # Fresh: the Fresh bit with button fresh.
        ("00 00 00 00 00 95 00 6A 00 29 A5 CD", {"fresh": 1, "button": "fresh"}),
        # Follow: follow me 0x5F / 0x5D; follow off, with Ion, Eye and Sleep.
        ("00 00 00 00 00 13 00 0A 5F 89 A5 AA", {"follow": 0x5F, "mode": "heat"}),
        ("00 00 00 00 00 13 00 6A 5D 29 A5 A8", {"follow": 0x5D, "button": "follow"}),
        ("00 04 00 40 00 13 00 6B 00 29 A5 90", {"ion": 1, "eye": 1, "sleep": 1}),
    ],
)
def test_layout_reads_the_real_captures(capture, fields):
    frame = bytes.fromhex(capture)
    values = NEOCLIMA_LAYOUT.read(frame)
    assert {k: values[k] for k in fields} == fields
    assert NEOCLIMA_LAYOUT.checksum.check(frame)
    # Every set bit is a named field: the rest is the skeleton's.
    rebuilt = bytearray(NEOCLIMA_LAYOUT.skeleton)
    for name in NEOCLIMA_LAYOUT.fields:
        NEOCLIMA_LAYOUT.write_raw(rebuilt, name, NEOCLIMA_LAYOUT.read_raw(frame, name))
    NEOCLIMA_LAYOUT.checksum.apply(rebuilt)
    assert bytes(rebuilt) == frame


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat"])
@pytest.mark.parametrize("fan", ["auto", "1", "2", "3"])
@pytest.mark.parametrize("t", [16.0, 24.0, 32.0])
def test_off_carries_mode_auto(mode, fan, t):
    # IRac passes kOff; convertMode's default is kNeoclimaAuto. The setpoint
    # and fan are sent as asked (no dry fan rule: the mode is auto).
    values = read(state(False, mode, t, fan=fan))
    assert (values["power"], values["mode"]) == (0, "auto")
    assert (values["temp"], values["fan"]) == (int(t), fan)
    assert values["button"] == "power"


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat"])
def test_every_mode_uses_its_documented_code(mode):
    codes = {"auto": 0, "cool": 1, "dry": 2, "heat": 4}
    assert NEOCLIMA_LAYOUT.read_raw(data(state(True, mode)), "mode") == codes[mode]
    assert read(state(True, mode))["power"] == 1


@pytest.mark.parametrize("t", range(16, 33))
@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat"])
def test_every_setpoint_in_every_mode(t, mode):
    # setTemp: Temp = degrees - kNeoclimaMinTempC, in Celsius.
    values = read(state(True, mode, float(t)))
    assert NEOCLIMA_LAYOUT.read_raw(data(state(True, mode, float(t))), "temp") == (
        t - 16
    )
    assert (values["temp"], values["use_fah"]) == (t, 0)


def test_setpoint_is_clamped():
    # setTemp clamps to kNeoclimaMinTempC..kNeoclimaMaxTempC; the entity's
    # range is the same, so encode snaps out-of-range setpoints to it.
    dev = device()
    for asked, sent in ((10.0, 16), (40.0, 32)):
        pulses = dev.encode(None, HvacState(True, "cool", asked)).signal.pulses
        (frame,) = decode(NEOCLIMA, pulses, expected=["main"])
        assert NEOCLIMA_LAYOUT.read(frame.data)["temp"] == sent


@pytest.mark.parametrize("mode", ["auto", "cool", "heat"])
@pytest.mark.parametrize("fan, raw", [("auto", 0), ("1", 3), ("2", 2), ("3", 1)])
def test_every_fan_level_uses_its_documented_code(mode, fan, raw):
    # kNeoclimaFanAuto/Low/Med/High.
    assert NEOCLIMA_LAYOUT.read_raw(data(state(True, mode, fan=fan)), "fan") == raw


@pytest.mark.parametrize("fan", ["auto", "1", "2", "3"])
def test_dry_forces_fan_low(fan):
    # IRNeoclimaAc::setFan: "Dry mode only allows low speed".
    assert read(state(True, "dry", fan=fan))["fan"] == "1"


@pytest.mark.parametrize("power", [True, False])
@pytest.mark.parametrize("swing, raw", [("off", 0b10), ("swing", 0b01)])
def test_swing_v_uses_its_documented_code(power, swing, raw):
    frame = data(state(power, "cool", swing_v=swing))
    assert NEOCLIMA_LAYOUT.read_raw(frame, "swing_v") == raw


@pytest.mark.parametrize("power", [True, False])
@pytest.mark.parametrize("swing, raw", [("off", 1), ("swing", 0)])
def test_swing_h_bit_is_cleared_when_on(power, swing, raw):
    frame = data(state(power, "cool", swing_h=swing))
    assert NEOCLIMA_LAYOUT.read_raw(frame, "swing_h") == raw


@pytest.mark.parametrize(
    "feature, field",
    [
        ("sleep", "sleep"),
        ("powerful", "turbo"),
        ("purifier", "ion"),
        ("economy", "econo"),
        ("light", "light"),
    ],
)
@pytest.mark.parametrize("power", [True, False])
def test_each_feature_sets_its_bit_only(feature, field, power):
    base = read(state(power, "cool"))
    values = read(state(power, "cool", features={feature: True}))
    assert values[field] == 1 and base[field] == 0
    assert {k for k in values if values[k] != base[k]} == {field}


def test_all_features_together():
    values = read(state(True, "heat", features={f: True for f in FEATURES}))
    for field in ("sleep", "turbo", "ion", "econo", "light"):
        assert values[field] == 1


def test_fields_irac_never_sets_stay_clear():
    for power in (True, False):
        target = state(power, "heat", features={f: True for f in FEATURES})
        values = read(target)
        for field in ("hold", "eye", "fresh", "c_heat", "follow", "use_fah"):
            assert values[field] == 0, field
        assert values["button"] == "power"
        assert data(target)[10] == 0xA5


def test_previous_is_ignored():
    dev = device()
    target = dev.normalise(
        HvacState(True, "cool", 22.0, fan="2", swing_v="swing", swing_h="swing")
    )
    for previous in (
        HvacState(False, "heat", 25.0),
        HvacState(True, "dry", 16.0, fan="3", swing_v="swing"),
        target,
    ):
        assert dev.encode(previous, target).signal == dev.encode(None, target).signal


@pytest.mark.parametrize("brand, model", ALL_MODELS)
def test_registry_serves_the_port(brand, model):
    assert isinstance(registry.get_device(brand, model), NeoclimaDevice)


@pytest.mark.parametrize("brand, model", ALL_MODELS)
def test_capabilities_match_the_legacy_entity(brand, model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.neoclima import Neoclima

    legacy = LegacyDevice(brand, model, Neoclima)
    assert NeoclimaDevice(brand, model).capabilities == legacy.capabilities


@pytest.mark.parametrize(
    "key, value, field",
    [("swing", "on", "swing_v"), ("hswing", "on", "swing_h"), ("sleep", "on", "sleep")],
)
def test_undeclared_deviation_is_reported(key, value, field):
    record = next(
        r
        for r in load_oracle("NEOCLIMA")
        if r["state"].get(key) == value and r["state"]["mode"] != "off"
    )
    others = tuple(d for d in DEFECTS if d.field != field)
    with pytest.raises(AssertionError, match=field):
        assert_matches_oracle(device(), record, device().LAYOUTS, others)
