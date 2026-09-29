import re

import pytest

from oracle import load_oracle
from port_oracle import (
    Defect,
    assert_matches_oracle,
    c_sequence,
    oracle_params,
    state_from_record,
)
from pyhvac.fields import Sum8
from pyhvac.ir.codec import decode, encode
from pyhvac.ir.model import Frame
from pyhvac.protocols.argo import (
    ARGO,
    ARGO_MODELS,
    ARGO_WREM2_BITS,
    ARGO_WREM2_LAYOUT,
    ARGO_WREM3_LAYOUT,
    ARGO_CAPABILITIES,
    ArgoChecksum,
    ArgoDevice,
)
from pyhvac.state import HvacState

# A record without "swing" leaves IRac's swingv at kOff, which convertSwingV
# maps to FLAP_FULL (7). The entity has no swing off (the legacy class offers
# none), so such a record is read as swing "auto" (FLAP_AUTO): the port cannot
# express that C default. Scoped to those records only.
NO_SWING_DEFECT = Defect("flap", "auto", "full", "record relies on IRac's swingv kOff")

WREM2_MODEL, WREM3_MODEL = "Ulisse 13 DCI", "Ulisse Eco Mobile"
MODES = ("auto", "cool", "fan", "dry", "heat")


def device(model=WREM2_MODEL):
    return ArgoDevice("argo", model)


def defects_for(record):
    return () if "swing" in record["state"] else (NO_SWING_DEFECT,)


def frame(state, model=WREM2_MODEL, previous=None):
    dev = device(model)
    if previous is not None:
        previous = dev.normalise(previous)
    (main,) = dev.frames(previous, dev.normalise(state), ())
    return main


def read(state, model=WREM2_MODEL):
    (layout,) = device(model).LAYOUTS
    return layout.read(frame(state, model).data)


def wire(text):
    """IRsendTest's "f38000d50m6400s3300..." as pulses."""
    return [int(d) for d in re.findall(r"[ms](\d+)", text)]


@pytest.mark.parametrize("record", oracle_params("ARGO"))
def test_matches_c_library(record):
    dev = device(record["model"])
    assert_matches_oracle(dev, record, dev.LAYOUTS, defects_for(record))


def test_oracle_covers_both_variants():
    models = {r["model"] for r in load_oracle("ARGO")}
    assert {ARGO_MODELS[m] for m in models} == {"WREM2", "WREM3"}


def test_layout_round_trips_every_oracle_state():
    for record in load_oracle("ARGO"):
        dev = device(record["model"])
        (layout,) = dev.LAYOUTS
        (main,) = dev.frames(None, state_from_record(dev, record["state"]), ())
        values = layout.read(main.data)
        assert layout.build(**values) == bytearray(main.data)


def test_every_oracle_frame_has_its_checksum():
    # WREM2: Sum (bits 82-89) = bytes 0-9 + 2; WREM3: Sum (byte 5) = bytes 0-4.
    # portkit checksum only tries whole bytes, so the WREM2 sum is pinned here.
    for record in load_oracle("ARGO"):
        name = "wrem2" if ARGO_MODELS[record["model"]] == "WREM2" else "wrem3"
        (main,) = decode(ARGO, record["pulses"], expected=[name])
        if name == "wrem2":
            assert main.nbits == ARGO_WREM2_BITS
            assert ArgoChecksum().check(main.data)
        else:
            assert main.nbits == 48
            assert Sum8(0, 5, 5).check(main.data)


def test_wrem2_bit_95_is_always_zero_padding():
    # The WREM2 section sends bit 95 as its footer (kArgoBitMark +
    # kArgoZeroSpace): no field or checksum bit may live there, and every C
    # message ends with that zero bit's space.
    owned = {b for f in ARGO_WREM2_LAYOUT.fields.values() for b in f.bits}
    owned |= ArgoChecksum().bits()
    assert 95 not in owned
    for record in load_oracle("ARGO"):
        if ARGO_MODELS[record["model"]] == "WREM2":
            assert record["pulses"][-2:] == [400, 900]
            assert len(record["pulses"]) == 2 + 2 * 96


def test_no_field_sits_in_a_checksum_bit():
    for layout in (ARGO_WREM2_LAYOUT, ARGO_WREM3_LAYOUT):
        sums = layout.checksum.bits()
        for name, f in layout.fields.items():
            assert not set(f.bits) & sums, name


def test_wrem2_framing_reproduces_send_data_only():
    # TestSendArgo.SendDataOnly: sendArgo sends no footer and no gap, so the
    # message ends on the last bit's space.
    data = bytes.fromhex("acf500240200000000acd601")
    expected = wire(
        "f38000d50"
        "m6400s3300"
        "m400s900m400s900m400s2200m400s2200m400s900m400s2200m400s900m400s2200"
        "m400s2200m400s900m400s2200m400s900m400s2200m400s2200m400s2200m400s2200"
        "m400s900m400s900m400s900m400s900m400s900m400s900m400s900m400s900"
        "m400s900m400s900m400s2200m400s900m400s900m400s2200m400s900m400s900"
        "m400s900m400s2200m400s900m400s900m400s900m400s900m400s900m400s900"
        "m400s900m400s900m400s900m400s900m400s900m400s900m400s900m400s900"
        "m400s900m400s900m400s900m400s900m400s900m400s900m400s900m400s900"
        "m400s900m400s900m400s900m400s900m400s900m400s900m400s900m400s900"
        "m400s900m400s900m400s900m400s900m400s900m400s900m400s900m400s900"
        "m400s900m400s900m400s2200m400s2200m400s900m400s2200m400s900m400s2200"
        "m400s900m400s2200m400s2200m400s900m400s2200m400s900m400s2200m400s2200"
        "m400s2200m400s900m400s900m400s900m400s900m400s900m400s900"
        "m400s900"
    )
    ours = Frame("wrem2", data, ARGO_WREM2_BITS)
    assert list(encode(ARGO, [ours]).pulses) == expected
    assert decode(ARGO, expected, expected=["wrem2"]) == [ours]
    # TestArgoACClass.MessageConstructon's frame: its sum is ArgoChecksum's.
    assert ArgoChecksum().check(data)
    values = ARGO_WREM2_LAYOUT.read(data)
    assert (values["mode"], values["temperature"], values["room_temp"]) == (
        "cool",
        20,
        21 - 4,
    )
    assert (values["power"], values["max"], values["night"], values["ifeel"]) == (
        1,
        1,
        1,
        1,
    )


def test_wrem3_framing_reproduces_send_data_only():
    # TestSendArgoWrem3.SendDataOnly: a kArgoBitMark footer and kArgoGap.
    data = bytes.fromhex("0b3135fec02f")
    expected = wire(
        "f38000d50"
        "m6400s3300"
        "m400s2200m400s2200m400s900m400s2200m400s900m400s900m400s900m400s900"
        "m400s2200m400s900m400s900m400s900m400s2200m400s2200m400s900m400s900"
        "m400s2200m400s900m400s2200m400s900m400s2200m400s2200m400s900m400s900"
        "m400s900m400s2200m400s2200m400s2200m400s2200m400s2200m400s2200m400s2200"
        "m400s900m400s900m400s900m400s900m400s900m400s900m400s2200m400s2200"
        "m400s2200m400s2200m400s2200m400s2200m400s900m400s2200m400s900m400s900"
        "m400s100000"
    )
    ours = Frame("wrem3", data)
    assert list(encode(ARGO, [ours]).pulses) == expected
    assert decode(ARGO, expected, expected=["wrem3"]) == [ours]
    assert ARGO_WREM3_LAYOUT.checksum.check(data)


def test_wrem3_real_capture_except_what_the_entity_cannot_express():
    # TestArgoE2E.RealExampleCommands, first case (a real WREM3 remote): cool,
    # 22 °C, fan auto, power on, Light on. The port's frame for that state
    # differs only in what the entity cannot set: the remote's room sensor
    # (26 °C) and its swing FLAP_FULL ("Breeze").
    raw = (
        "6468 3150 456 2154 428 2152 462 874 422 2158 424 882 424 880 428 876 "
        "430 874 454 850 424 2154 460 2150 430 874 422 2156 458 2152 430 874 "
        "420 884 454 850 424 2152 462 874 422 882 424 2154 428 876 430 874 "
        "476 828 478 2098 462 2148 424 2156 458 2150 430 874 432 872 422 882 "
        "424 880 482 822 430 2148 454 852 488 816 480 826 482 852 454 2126 "
        "424 2154 458 876 454 852 454 2124 426 880 426 878 428 2150 486 848 "
        "426 878 428"
    )
    capture = bytes([0x0B, 0x36, 0x12, 0x0F, 0xC2, 0x24])
    (main,) = decode(ARGO, [int(x) for x in raw.split()], expected=["wrem3"])
    assert main.data == capture
    target = HvacState(True, "cool", 22.0, features={"light": True})
    ours = bytearray(frame(target, WREM3_MODEL).data)
    assert ARGO_WREM3_LAYOUT.read(ours)["light"] == 1
    for name, raw_value in (("room_temp", 26 - 4), ("flap", 7)):
        ARGO_WREM3_LAYOUT.write_raw(ours, name, raw_value)
    ARGO_WREM3_LAYOUT.checksum.apply(ours)
    assert bytes(ours) == capture


@pytest.mark.parametrize(
    "model, variant, section",
    [(m, v, v.lower()) for m, v in ARGO_MODELS.items()],
)
def test_variant_comes_from_the_model(model, variant, section):
    dev = device(model)
    assert dev.variant == variant
    assert dev.LAYOUTS == (
        (ARGO_WREM2_LAYOUT,) if variant == "WREM2" else (ARGO_WREM3_LAYOUT,)
    )
    assert frame(HvacState(True, "cool", 22.0), model).section == section


def test_unknown_model_gets_wrem2_and_bad_variant_raises():
    assert ArgoDevice("argo", "whatever").variant == "WREM2"
    assert ArgoDevice("argo", "whatever", variant="WREM3").variant == "WREM3"
    with pytest.raises(ValueError):
        ArgoDevice("argo", "whatever", variant="WREM4")


@pytest.mark.parametrize(
    "mode, wrem2, wrem3",
    [
        ("cool", 0b000, 0b001),
        ("dry", 0b001, 0b010),
        ("auto", 0b010, 0b101),
        ("fan", 0b011, 0b100),  # WREM2: kArgoOff, as setMode stores FAN
        ("heat", 0b100, 0b011),
    ],
)
def test_every_mode(mode, wrem2, wrem3):
    state = HvacState(True, mode, 22.0)
    assert ARGO_WREM2_LAYOUT.read_raw(frame(state).data, "mode") == wrem2
    assert ARGO_WREM3_LAYOUT.read_raw(frame(state, WREM3_MODEL).data, "mode") == wrem3


@pytest.mark.parametrize("model", [WREM2_MODEL, WREM3_MODEL])
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("temp", [16.0, 25.0])
def test_off_carries_mode_auto_in_every_mode(model, mode, temp):
    # IRac passes mode "off"; convertMode maps it to argoMode_t::AUTO.
    state = HvacState(False, mode, temp, fan="3", swing_v="2")
    values = read(state, model)
    assert (values["power"], values["mode"], values["temperature"]) == (
        0,
        "auto",
        int(temp),
    )
    assert (values["fan"], values["flap"]) == ("3", "2")


@pytest.mark.parametrize("model", [WREM2_MODEL, WREM3_MODEL])
@pytest.mark.parametrize("temp", range(10, 33))
def test_every_setpoint(model, temp):
    # Temp: celsius - kArgoTempDelta, kArgoMinTemp (10) to kArgoMaxTemp (32).
    (layout,) = device(model).LAYOUTS
    data = frame(HvacState(True, "heat", float(temp)), model).data
    assert layout.read_raw(data, "temperature") == temp - 4


@pytest.mark.parametrize("model", [WREM2_MODEL, WREM3_MODEL])
def test_setpoint_is_clamped_to_the_header_range(model):
    # setTemp clamps to kArgoMinTemp / kArgoMaxTemp; so does normalise.
    caps = device(model).capabilities.temperature
    assert (caps.min, caps.max, caps.decimals) == (10.0, 32.0, (0,))
    assert read(HvacState(True, "cool", 5.0), model)["temperature"] == 10
    assert read(HvacState(True, "cool", 40.0), model)["temperature"] == 32


@pytest.mark.parametrize(
    "fan, raw",
    [("auto", 0), ("1", 1), ("2", 2), ("3", 3)],  # kArgoFanAuto, kArgoFan1..3
)
@pytest.mark.parametrize("mode", MODES)
def test_every_wrem2_fan_level(mode, fan, raw):
    state = HvacState(True, mode, 22.0, fan=fan)
    assert ARGO_WREM2_LAYOUT.read_raw(frame(state).data, "fan") == raw


@pytest.mark.parametrize(
    "fan, raw, label",
    [
        ("auto", 0, "auto"),  # FAN_AUTO
        ("1", 1, "lowest"),  # FAN_LOWEST
        ("2", 2, "low"),  # FAN_LOWER: the legacy "low"
        ("3", 3, "medium"),  # FAN_LOW: the legacy "medium"
        ("4", 4, "midhigh"),  # FAN_MEDIUM ("Med-High")
        ("5", 5, "high"),  # FAN_HIGH: the legacy "high"
        ("6", 6, "highest"),  # FAN_HIGHEST
    ],
)
@pytest.mark.parametrize("mode", MODES)
def test_every_wrem3_fan_level(mode, fan, raw, label):
    # argoFan_t: IRArgoACBase<ArgoProtocolWREM3>::setFan stores every speed.
    state = HvacState(True, mode, 22.0, fan=fan)
    assert ARGO_WREM3_LAYOUT.read_raw(frame(state, WREM3_MODEL).data, "fan") == raw
    assert device(WREM3_MODEL).capabilities.fan.label(fan) == label


def test_wrem3_med_high_fan_is_the_class_built_message():
    # TestArgoAC_WREM3Class.MessageConstructon_ACControl_2:
    # setFan(argoFan_t::FAN_MEDIUM) is byte 2's top bits 0b100, "Fan: 4
    # (Med-High)", the port's fan "4".
    built = bytes([0x2B, 0xB8, 0x93, 0xFC, 0xC3, 0x35])
    assert ARGO_WREM3_LAYOUT.checksum.check(built)
    assert ARGO_WREM3_LAYOUT.read(built)["fan"] == "4"
    values = ARGO_WREM3_LAYOUT.read(built)
    assert (values["temperature"], values["light"], values["max"]) == (23, 1, 1)


@pytest.mark.parametrize("model", [WREM2_MODEL, WREM3_MODEL])
@pytest.mark.parametrize(
    "swing, raw",
    [("auto", 0), ("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 5), ("6", 6)],
)
def test_every_swing_value(model, swing, raw):
    # convertSwingV: ceiling (kHighest) FLAP_1 ... 0° (kLowest) FLAP_6.
    (layout,) = device(model).LAYOUTS
    data = frame(HvacState(True, "cool", 22.0, swing_v=swing), model).data
    assert layout.read_raw(data, "flap") == raw


@pytest.mark.parametrize("power", [True, False])
@pytest.mark.parametrize("mode", MODES)
def test_powerful_sets_max_in_every_mode(power, mode):
    for model in (WREM2_MODEL, WREM3_MODEL):
        assert read(HvacState(power, mode, 22.0), model)["max"] == 0
        on = HvacState(power, mode, 22.0, features={"powerful": True})
        assert read(on, model)["max"] == 1


def test_wrem2_offers_no_quiet():
    # IRac::argo: "No Quiet setting available". A quiet the caller still
    # passes is dropped by normalise and sends nothing.
    assert "quiet" not in ARGO_CAPABILITIES["WREM2"].features
    plain = frame(HvacState(True, "cool", 22.0))
    quiet = frame(HvacState(True, "cool", 22.0, features={"quiet": True}))
    assert quiet == plain
    assert ARGO_WREM2_LAYOUT.read(quiet.data)["night"] == 0


@pytest.mark.parametrize("power", [True, False])
@pytest.mark.parametrize("mode", MODES)
def test_wrem2_sleep_sets_night(mode, power):
    # ArgoProtocol's Night bit (byte 9 bit 2), IRac::argo's
    # setNight(sleep >= 0). TestArgoACClass.MessageConstructon's frame has it.
    off = read(HvacState(power, mode, 22.0))
    on = read(HvacState(power, mode, 22.0, features={"sleep": True}))
    assert off["night"] == 0 and on["night"] == 1
    assert {k for k in on if on[k] != off[k]} == {"night"}
    assert (
        ARGO_WREM2_LAYOUT.read(bytes.fromhex("acf500240200000000acd601"))["night"] == 1
    )


@pytest.mark.parametrize(
    "feature, field",
    [
        ("quiet", "night"),
        ("economy", "eco"),
        ("purifier", "filter"),
        ("light", "light"),
    ],
)
@pytest.mark.parametrize("power", [True, False])
def test_wrem3_features(feature, field, power):
    # IRac::argoWrem3_ACCommand gets quiet as night, econo, filter and light
    # (ArgoProtocolWREM3's Light, byte 4 bit 1).
    off = read(HvacState(power, "heat", 22.0), WREM3_MODEL)
    on = read(HvacState(power, "heat", 22.0, features={feature: True}), WREM3_MODEL)
    assert off[field] == 0 and on[field] == 1
    assert {k for k in on if on[k] != off[k]} == {field}


def test_all_features_together():
    feats = {"powerful": True, "quiet": True, "economy": True, "purifier": True}
    values = read(HvacState(True, "cool", 22.0, features=feats), WREM3_MODEL)
    assert (values["max"], values["night"], values["eco"], values["filter"]) == (
        1,
        1,
        1,
        1,
    )
    assert (values["light"], values["ifeel"], values["channel"]) == (0, 0, 0)
    feats["light"] = True
    values = read(HvacState(True, "cool", 22.0, features=feats), WREM3_MODEL)
    assert values["light"] == 1


@pytest.mark.parametrize("model", [WREM2_MODEL, WREM3_MODEL])
@pytest.mark.parametrize("power", [True, False])
def test_room_temp_is_the_reset_25_and_ifeel_is_off(model, power):
    feats = {"powerful": True, "quiet": True}
    values = read(HvacState(power, "cool", 18.0, features=feats), model)
    assert values["room_temp"] == 25 - 4
    assert values["ifeel"] == 0


@pytest.mark.parametrize("model", [WREM2_MODEL, WREM3_MODEL])
def test_previous_is_ignored(model):
    # No toggle bits: IRac::handleToggles has no Argo case.
    dev = device(model)
    target = HvacState(True, "cool", 22.0, fan="2", swing_v="3")
    for previous in (
        None,
        target,
        HvacState(False, "heat", 25.0),
        HvacState(True, "cool", 22.0, fan="3", features={"powerful": True}),
    ):
        assert dev.encode(previous, target).signal == dev.encode(None, target).signal


def test_skeletons_are_the_reset_states():
    # The oracle's first record of each class: off, 16 °C, fan auto, swing
    # auto.
    for record in load_oracle("ARGO"):
        if record["state"] == {
            "mode": "off",
            "temperature": 16,
            "fan": "auto",
            "swing": "auto",
        }:
            wrem2 = ARGO_MODELS[record["model"]] == "WREM2"
            layout = ARGO_WREM2_LAYOUT if wrem2 else ARGO_WREM3_LAYOUT
            name = "wrem2" if wrem2 else "wrem3"
            (main,) = decode(ARGO, record["pulses"], expected=[name])
            data = layout.build(
                mode="auto", temperature=16, fan="auto", room_temp=21, flap="auto"
            )
            assert bytes(data) == main.data


@pytest.mark.parametrize(
    "model, length, tail",
    [
        (WREM2_MODEL, 2 + 2 * 96, (400, 900)),
        (WREM3_MODEL, 2 + 2 * 48 + 2, (400, 100000)),
    ],
)
def test_message_shape(model, length, tail):
    signal = device(model).encode(None, HvacState(True, "cool", 22.0)).signal
    assert signal.pulses[:2] == (6400, 3300)
    assert signal.pulses[-2:] == tail
    assert len(signal.pulses) == length
    assert signal.carrier == 38000


@pytest.mark.parametrize("variant", ["WREM2", "WREM3"])
def test_capabilities_are_the_documented_ones(variant):
    caps = ARGO_CAPABILITIES[variant]
    assert caps.modes == MODES
    assert (caps.temperature.min, caps.temperature.max) == (10.0, 32.0)
    assert caps.swing_v.values == ("auto", "1", "2", "3", "4", "5", "6")
    assert caps.swing_h is None
    fans = {"WREM2": 3, "WREM3": 6}[variant]
    assert caps.fan.values == ("auto",) + tuple(str(n) for n in range(1, fans + 1))
    assert (
        set(caps.features)
        == {
            "WREM2": {"powerful", "sleep"},
            "WREM3": {"powerful", "quiet", "economy", "purifier", "light"},
        }[variant]
    )


# The new WREM3 values against the C path (the old glue passes the stdAc
# speeds lowest/midhigh/highest, the setpoint and light straight through):
# the setpoint edges, every fan speed, light, in every mode.
WREM3_EXTRA_STATES = [
    {"mode": m, "temperature": t, "fan": fan, "swing": "45°"}
    for m in MODES + ("off",)
    for t in (10, 11, 26, 32)
    for fan in ("auto", "lowest", "low", "medium", "midhigh", "high", "highest")
] + [
    {"mode": m, "temperature": 22, "fan": "high", "swing": "auto", "light": "on"}
    for m in MODES + ("off",)
]
WREM2_EXTRA_STATES = [
    {"mode": m, "temperature": t, "fan": fan, "swing": "45°"}
    for m in MODES + ("off",)
    for t in (10, 11, 26, 32)
    for fan in ("auto", "low", "medium", "high")
]


@pytest.mark.parametrize(
    "model, states",
    [(WREM2_MODEL, WREM2_EXTRA_STATES), (WREM3_MODEL, WREM3_EXTRA_STATES)],
    ids=["WREM2", "WREM3"],
)
def test_new_values_match_the_c_path(model, states):
    record = next(r for r in load_oracle("ARGO") if r["model"] == model)
    dev = device(model)
    for rec in c_sequence(record, states):
        assert_matches_oracle(dev, rec, dev.LAYOUTS)


def test_undeclared_deviation_is_reported():
    record = next(r for r in load_oracle("ARGO") if "swing" not in r["state"])
    dev = device(record["model"])
    with pytest.raises(AssertionError, match="flap"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_the_defect_is_scoped_to_records_without_swing():
    for record in load_oracle("ARGO"):
        assert (NO_SWING_DEFECT in defects_for(record)) == (
            "swing" not in record["state"]
        )


def test_layouts_must_cover_every_frame():
    record = load_oracle("ARGO")[0]
    dev = device(record["model"])
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), defects_for(record))


# No real capture in ir_Argo_test.cpp needs it, but
# decodeArgo and decodeArgoWREM3 match with _tolerance (25 %) and no mark
# excess.
def test_decode_tolerance_is_the_c_decoders():
    assert (ARGO.tolerance, ARGO.mark_excess) == (0.25, 0)
