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
from pyhvac.fields import Sum8
from pyhvac.ir.codec import decode
from pyhvac.plugins import panasonic
from pyhvac.plugins.panasonic import (
    PANASONIC_AC,
    PANASONIC_AC_FIRST,
    PANASONIC_AC_MODELS,
    PANASONIC_AC_SECOND,
    PANASONIC_AC_SECOND_CKP,
    PanasonicAcDevice,
)
from pyhvac.state import HvacState

# The C path deviates from the documented PanasonicAc values here:
# - swing "90°" and "60°": the old glue maps them to kHigh and kUpperMiddle;
#   IRPanasonicAc::convertSwingV has no kUpperMiddle (-> kPanasonicAcSwingVAuto).
#   Canonical "1" is the topmost documented position: the port sends
#   kPanasonicAcSwingVHighest for "1" and kPanasonicAcSwingVHigh for "2".
# - Ion (DKE): IRac::sendAc calls IRac::panasonic(..., send.quiet, send.turbo,
#   send.clock), so send.clock (-1, true) lands in the ``filter`` argument and
#   setIon(true) runs on every DKE message; send.filter never reaches C. The
#   port sends the documented purifier value in the kPanasonicAcIonFilterByte
#   bit.
DEFECTS = (
    Defect("swing_v", "1", "2", "glue sends kHigh for 90°"),
    Defect("swing_v", "2", "auto", "glue sends kUpperMiddle for 60°"),
    Defect("ion", 0, 1, "IRac::sendAc passes send.clock as filter"),
)

LEGACY_CLASS = {
    "NKE": "PanasonicNke",
    "DKE": "PanasonicDke",
    "JKE": "PanasonicJke",
    "CKP": "PanasonicCkp",
    "RKR": "PanasonicRkr",
}
MODEL_OF = {  # one model per variant
    "NKE": "NKE series",
    "DKE": "DKE series",
    "JKE": "JKE series",
    "CKP": "CKP series",
    "RKR": "RKR series",
}


def device(variant="DKE"):
    return PanasonicAcDevice("panasonic", MODEL_OF[variant])


def device_for(record):
    return PanasonicAcDevice("panasonic", record["model"])


def frames(state, previous=None, variant="DKE"):
    dev = device(variant)
    if previous is not None:
        previous = dev.normalise(previous)
    return dev.frames(previous, dev.normalise(state), ())


def read(state, previous=None, variant="DKE"):
    dev = device(variant)
    first, second = frames(state, previous, variant)
    return dev.LAYOUTS[1].read(second.data)


@pytest.mark.parametrize("record", oracle_params("PANASONIC_AC"))
def test_matches_c_library(record):
    dev = device_for(record)
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


@pytest.mark.parametrize("record, states", sequence_params("PANASONIC_AC"))
def test_sequence_matches_a_persistent_c_object(record, states):
    # The CKP power toggle depends on the message before, which C's IRac keeps.
    dev = device_for(record)
    assert_sequence_matches_c(dev, record, states, dev.LAYOUTS, DEFECTS)


def test_oracle_covers_every_variant():
    models = {r["model"] for r in load_oracle("PANASONIC_AC")}
    assert {PANASONIC_AC_MODELS[m] for m in models} == set(LEGACY_CLASS)


def test_models_are_the_legacy_ones():
    # Every PluginObject.MODELS key served by the five classes, with the
    # variant of its class. PanasonicLke is in no MODELS entry: unreachable.
    legacy = {
        m: cls.__name__
        for m, cls in panasonic.PluginObject.MODELS.items()
        if cls.__name__ in LEGACY_CLASS.values() or cls.__name__ == "PanasonicLke"
    }
    assert legacy == {m: LEGACY_CLASS[v] for m, v in PANASONIC_AC_MODELS.items()}


def test_layout_round_trips_every_oracle_state():
    for record in load_oracle("PANASONIC_AC"):
        dev = device_for(record)
        state = state_from_record(dev, record["state"])
        for f, layout in zip(dev.frames(None, state, ()), dev.LAYOUTS):
            values = layout.read(f.data)
            assert layout.build(**values) == bytearray(f.data)


def test_checksum_is_a_plain_sum_of_the_second_section():
    # IRPanasonicAc::calcChecksum sums state bytes 0-25 from
    # kPanasonicAcChecksumInit (0xF4). The constant first section sums to
    # 0x0C, and 0xF4 + 0x0C = 0x100: a plain Sum8 over the second section.
    assert (0xF4 + sum(PANASONIC_AC_FIRST.skeleton)) & 0xFF == 0
    for record in load_oracle("PANASONIC_AC"):
        first, second = decode(
            PANASONIC_AC, record["pulses"], expected=["first", "second"]
        )
        assert first.data == PANASONIC_AC_FIRST.skeleton
        state = first.data + second.data
        assert state[26] == (0xF4 + sum(state[:26])) & 0xFF
        assert Sum8(0, 18, 18).check(second.data)


def test_no_field_sits_in_the_checksum_byte():
    for layout in (PANASONIC_AC_SECOND, PANASONIC_AC_SECOND_CKP):
        assert layout.checksum.positions() == {18}
        for name, f in layout.fields.items():
            assert 18 not in {b // 8 for b in f.bits}, name


def test_skeleton_is_the_known_good_state():
    # The oracle's first record: NKE, off, 16 °C, fan auto, swing auto.
    record = load_oracle("PANASONIC_AC")[0]
    assert record["model"] == "NKE series"
    assert record["state"] == {
        "mode": "off",
        "temperature": 16,
        "fan": "auto",
        "swing": "auto",
    }
    _, second = decode(PANASONIC_AC, record["pulses"], expected=["first", "second"])
    data = PANASONIC_AC_SECOND.build(
        mode="auto",
        temperature=16,
        fan="auto",
        swing_v="auto",
        swing_h=0x6,
        model_23=0x81,
    )
    assert bytes(data) == second.data


@pytest.mark.parametrize(
    "variant, model_13, model_21, model_23, clock",
    [
        ("NKE", 0, 0, 0x81, 0),
        ("DKE", 0, 0, 0x01, 0x600),  # byte 25 = 0x06: kPanasonicAcTimeSpecial
        ("JKE", 0, 0, 0x81, 0),
        ("CKP", 0, 1, 0x01, 0),
        ("RKR", 1, 0, 0x89, 0),
    ],
)
def test_model_bytes_are_those_setmodel_writes(
    variant, model_13, model_21, model_23, clock
):
    for power in (True, False):
        values = read(HvacState(power, "cool", 22.0), variant=variant)
        assert (
            values["model_13"],
            values["model_21"],
            values["model_23"],
            values["clock"],
        ) == (model_13, model_21, model_23, clock)
        # Timers: disabled, kPanasonicAcTimeSpecial, as the known good state.
        assert values["on_timer_enabled"] == values["off_timer_enabled"] == 0
        assert values["on_timer"] == values["off_timer"] == 0x600


@pytest.mark.parametrize("variant", sorted(LEGACY_CLASS))
@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat", "fan"])
def test_off_message_carries_mode_auto(variant, mode):
    values = read(HvacState(False, mode, 27.0), variant=variant)
    assert (values["power"], values["mode"], values["temperature"]) == (0, "auto", 27)
    on = read(HvacState(True, mode, 27.0), variant=variant)
    assert (on["power"], on["mode"]) == (1, mode)


def test_fan_mode_keeps_the_requested_temperature():
    # setMode(Fan) writes kPanasonicAcFanModeTemp (27), but IRac::panasonic
    # calls setTemp(degrees) after it.
    assert read(HvacState(True, "fan", 18.0))["temperature"] == 18


def test_temperatures_clamp_to_the_documented_range():
    assert read(HvacState(True, "cool", 16.0))["temperature"] == 16
    assert read(HvacState(True, "cool", 30.0))["temperature"] == 30
    assert frames(HvacState(True, "cool", 16.0))[1].data[6] == 16 << 1
    assert frames(HvacState(True, "cool", 30.0))[1].data[6] == 30 << 1


@pytest.mark.parametrize(
    "fan, code",
    [("auto", 0xA), ("1", 0x3), ("2", 0x4), ("3", 0x5), ("4", 0x6), ("5", 0x7)],
)
def test_fan_codes(fan, code):
    # kPanasonicAcFan{Auto,Min,Low,Med,High,Max} + kPanasonicAcFanDelta
    assert frames(HvacState(True, "cool", 22.0, fan=fan))[1].data[8] >> 4 == code


@pytest.mark.parametrize(
    "swing, code",
    [("auto", 0xF), ("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 5)],
)
def test_swing_v_sends_the_documented_positions_top_down(swing, code):
    data = frames(HvacState(True, "cool", 22.0, swing_v=swing))[1].data
    assert data[8] & 0x0F == code


@pytest.mark.parametrize("variant", ["DKE", "RKR"])
@pytest.mark.parametrize(
    "swing, code",
    [("auto", 0xD), ("1", 0x9), ("2", 0xA), ("3", 0x6), ("4", 0xB), ("5", 0xC)],
)
def test_swing_h_positions(variant, swing, code):
    state = HvacState(True, "cool", 22.0, swing_h=swing)
    assert frames(state, variant=variant)[1].data[9] == code


@pytest.mark.parametrize("swing", ["off", "swing"])
def test_nke_swing_h_is_always_middle(swing):
    # IRPanasonicAc::setSwingHorizontal forces Middle on NKE (and LKE).
    state = HvacState(True, "cool", 22.0, swing_h=swing)
    assert frames(state, variant="NKE")[1].data[9] == 0x06


@pytest.mark.parametrize("variant", ["JKE", "CKP"])
def test_jke_and_ckp_have_no_swing_h(variant):
    # setSwingHorizontal ignores them: byte 17 stays 0.
    assert device(variant).capabilities.swing_h is None
    assert frames(HvacState(True, "cool", 22.0), variant=variant)[1].data[9] == 0


@pytest.mark.parametrize(
    "variant, quiet_bit, powerful_bit",
    [
        ("NKE", 0, 5),
        ("DKE", 0, 5),
        ("JKE", 0, 5),
        ("CKP", 5, 0),  # kPanasonicAcQuietCkpOffset / PowerfulCkpOffset
        ("RKR", 5, 0),
    ],
)
@pytest.mark.parametrize("power", [True, False])
@pytest.mark.parametrize("mode", ["auto", "cool", "heat"])
def test_quiet_and_powerful(variant, quiet_bit, powerful_bit, power, mode):
    def byte21(**features):
        state = HvacState(power, mode, 22.0, features=features)
        return frames(state, variant=variant)[1].data[13] & ~0x10

    assert byte21() == 0
    assert byte21(quiet=True) == 1 << quiet_bit
    assert byte21(powerful=True) == 1 << powerful_bit
    # setQuiet then setPowerful: Powerful on clears Quiet.
    assert byte21(quiet=True, powerful=True) == 1 << powerful_bit


@pytest.mark.parametrize("power", [True, False])
def test_purifier_sets_the_dke_ion_bit(power):
    assert read(HvacState(power, "heat", 25.0))["ion"] == 0
    on = HvacState(power, "heat", 25.0, features={"purifier": True})
    assert read(on)["ion"] == 1
    assert frames(on)[1].data[14] == 0x01


@pytest.mark.parametrize("variant", ["NKE", "JKE", "CKP", "RKR"])
def test_only_dke_has_a_purifier(variant):
    dev = device(variant)
    assert "purifier" not in dev.capabilities.features
    assert read(HvacState(True, "cool", 22.0), variant=variant)["ion"] == 0


def test_dke_ion_real_messages():
    # TestDecodePanasonicAC.DkeIonRealMessages (issue 1024), a real DKE
    # remote: heat, 25 °C, fan auto, swing auto/auto, Ion off then on. The
    # remote also sets byte 13 bits 1-3 (both timer flags and the bit
    # setModel uses for RKR) and clears two constant bits (byte 19 bit 3,
    # byte 20 bit 7) that IRPanasonicAc never touches, so only the settings
    # and model bytes are compared; Ion is the only bit the captures differ in.
    ion_off = bytes.fromhex("0220e004004f3280af0d000660000001000630")
    ion_on = bytes.fromhex("0220e004004f3280af0d000660000101000631")
    settings = ("power", "mode", "temperature", "fan", "swing_v", "swing_h")
    settings += ("quiet", "powerful", "ion", "model_21", "model_23")
    settings += ("clock",)
    assert (
        bytes(a ^ b for a, b in zip(ion_off, ion_on)).hex()
        == "00" * 14 + "01" + "00" * 3 + "01"
    )
    for capture, purifier in ((ion_off, False), (ion_on, True)):
        assert PANASONIC_AC_SECOND.checksum.check(capture)
        state = HvacState(
            True,
            "heat",
            25.0,
            swing_v="auto",
            swing_h="auto",
            features={"purifier": purifier},
        )
        ours = read(state)
        theirs = PANASONIC_AC_SECOND.read(capture)
        assert {k: ours[k] for k in settings} == {k: theirs[k] for k in settings}


def test_real_capture_decodes():
    # TestDecodePanasonicAC.RealExample (issue 525): the port's timings and
    # checksum hold on a real remote's message (cool, 25 °C, power off).
    raw = (
        "3582 1686 488 378 488 1238 488 378 488 378 488 378 488 378 488 378 488 "
        "384 488 378 488 378 488 378 488 378 488 378 488 1242 486 378 488 384 "
        "488 378 488 378 488 380 486 382 484 382 484 1264 464 1266 460 1272 462 "
        "378 488 406 460 1266 462 380 488 382 484 388 478 406 462 410 462 404 "
        "462 406 462 396 470 406 462 404 462 406 460 404 462 410 462 404 462 "
        "404 462 406 464 406 462 404 462 406 462 404 462 410 462 404 462 406 "
        "462 404 462 404 462 404 462 406 460 406 462 410 462 404 462 1264 484 "
        "1244 486 382 482 382 486 382 486 378 486 382 488 9924 3554 1686 488 "
        "378 490 1240 486 378 488 378 488 378 488 378 488 382 484 386 486 378 "
        "488 382 486 378 488 382 486 382 484 1242 486 380 488 386 484 382 486 "
        "380 486 382 486 380 486 380 486 1242 486 1242 484 1248 484 380 488 382 "
        "484 1242 486 382 484 382 484 382 484 382 486 386 484 382 486 382 484 "
        "382 486 382 486 380 484 382 486 382 488 380 486 382 484 380 462 406 "
        "488 376 484 1246 482 1246 460 404 480 392 484 386 482 1244 484 382 484 "
        "382 484 1242 482 1244 484 382 464 410 460 404 462 406 462 404 462 404 "
        "470 396 462 406 462 404 462 1286 460 1268 458 1268 460 1266 460 1266 "
        "460 406 460 1266 462 406 460 1272 462 406 460 406 460 406 460 406 462 "
        "404 462 406 460 406 462 410 462 404 462 406 460 406 460 406 462 404 "
        "462 406 460 406 460 410 462 406 460 1268 460 1266 460 404 460 406 462 "
        "406 460 406 460 412 456 410 460 410 438 428 460 410 456 410 456 1272 "
        "436 1288 438 434 438 428 438 428 438 428 438 428 438 428 438 428 438 "
        "428 438 434 438 428 438 428 438 428 438 428 438 428 440 428 438 428 "
        "438 432 438 428 438 428 438 428 438 428 438 428 438 428 438 430 438 "
        "1294 438 428 438 428 438 428 438 428 438 428 438 428 438 428 438 434 "
        "438 428 438 1288 438 1290 438 428 438 428 438 428 438 428 438 432 438 "
        "1288 438 1290 438 430 438 428 438 428 438 428 438 428 438 1292 438"
    )
    pulses = [int(x) for x in raw.split()] + [100000]
    first, second = decode(PANASONIC_AC, pulses, expected=["first", "second"])
    assert first.data == PANASONIC_AC_FIRST.skeleton
    assert second.data.hex() == "0220e00400303280af00000660000080000683"
    assert PANASONIC_AC_SECOND.checksum.check(second.data)
    values = PANASONIC_AC_SECOND.read(second.data)
    assert (values["power"], values["mode"], values["temperature"]) == (0, "cool", 25)
    assert (values["fan"], values["swing_v"]) == ("auto", "auto")


def test_ckp_power_toggles_only_on_a_change():
    # IRac::handleToggles: for kPanasonicCkp, power = desired ^ prev->power
    # (test_sequence_matches_a_persistent_c_object checks it against C).
    on, off = HvacState(True, "cool", 22.0), HvacState(False, "cool", 22.0)
    assert read(on, previous=off, variant="CKP")["power"] == 1
    assert read(off, previous=on, variant="CKP")["power"] == 1
    assert read(on, previous=on, variant="CKP")["power"] == 0
    assert read(off, previous=off, variant="CKP")["power"] == 0
    # A setting change alone does not toggle.
    warmer = HvacState(True, "heat", 26.0, fan="3")
    assert read(warmer, previous=on, variant="CKP")["power"] == 0


def test_ckp_without_previous_sends_what_a_fresh_irac_sends():
    # A fresh IRac's _prev has protocol UNKNOWN: handleToggles does nothing,
    # the Power bit is the target power.
    assert read(HvacState(True, "cool", 22.0), variant="CKP")["power"] == 1
    assert read(HvacState(False, "cool", 22.0), variant="CKP")["power"] == 0


@pytest.mark.parametrize("variant", ["NKE", "DKE", "JKE", "RKR"])
def test_previous_is_ignored_except_on_ckp(variant):
    dev = device(variant)
    target = HvacState(True, "cool", 22.0, fan="2", swing_v="3")
    for previous in (
        None,
        target,
        HvacState(False, "heat", 30.0),
        HvacState(True, "cool", 22.0, fan="5", swing_v="auto"),
    ):
        assert dev.encode(previous, target).signal == dev.encode(None, target).signal


def test_message_shape():
    dev = device()
    signal = dev.encode(None, HvacState(True, "cool", 22.0)).signal
    pulses = signal.pulses
    assert signal.carrier == 36700  # kPanasonicFreq
    assert pulses[:2] == (3456, 1728)
    first = 2 + 2 * 64 + 2
    assert pulses[first - 2 : first] == (432, 10000)
    assert pulses[first : first + 2] == (3456, 1728)
    assert pulses[-2:] == (432, 100000)
    assert len(pulses) == first + 2 + 2 * 152 + 2


def test_unknown_model_is_jke_and_unknown_variant_fails():
    # setModel ignores an unknown model; getModel reads the untouched
    # kPanasonicKnownGoodState as JKE.
    assert PanasonicAcDevice("panasonic", "nope").variant == "JKE"
    assert PanasonicAcDevice("panasonic", "nope", variant="RKR").variant == "RKR"
    with pytest.raises(ValueError, match="variant"):
        PanasonicAcDevice("panasonic", "nope", variant="LKE")


@pytest.mark.parametrize("model", PANASONIC_AC_MODELS)
def test_registry_serves_the_port(model):
    dev = registry.get_device("panasonic", model)
    assert isinstance(dev, PanasonicAcDevice)
    assert dev.variant == PANASONIC_AC_MODELS[model]


@pytest.mark.parametrize("model", PANASONIC_AC_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice

    cls = getattr(panasonic, LEGACY_CLASS[PANASONIC_AC_MODELS[model]])
    legacy = LegacyDevice("panasonic", model, cls)
    assert PanasonicAcDevice("panasonic", model).capabilities == legacy.capabilities


@pytest.mark.parametrize(
    "defect, pick",
    [
        (DEFECTS[0], lambda s: s.get("swing") == "90°"),
        (DEFECTS[1], lambda s: s.get("swing") == "60°"),
        (DEFECTS[2], lambda s: s.get("purifier", "off") == "off"),
    ],
)
def test_undeclared_deviation_is_reported(defect, pick):
    records = [
        r
        for r in load_oracle("PANASONIC_AC")
        if pick(r["state"])
        and (defect.field != "ion" or PANASONIC_AC_MODELS[r["model"]] == "DKE")
    ]
    assert records
    others = tuple(d for d in DEFECTS if d != defect)
    for record in records[:3]:
        dev = device_for(record)
        with pytest.raises(AssertionError, match=defect.field):
            assert_matches_oracle(dev, record, dev.LAYOUTS, others)


def test_layouts_must_cover_every_frame():
    record = load_oracle("PANASONIC_AC")[0]
    dev = device_for(record)
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:1], DEFECTS)


# ir_Panasonic_test.cpp DecodePanasonicAC.Issue540: decodePanasonicAC matches
# with kPanasonicAcTolerance (40 %) and kPanasonicAcExcess (0); this capture
# has spaces as long as 558 µs for 432.
REAL_RAW = (
    "3512 1714 466 408 466 1280 470 408 466 412 466 408 466 412 462 412 466 "
    "414 466 408 466 412 462 412 466 412 466 408 466 1280 466 412 462 416 "
    "462 412 466 408 466 412 462 416 462 412 462 1282 462 1284 462 1288 466 "
    "412 462 412 462 1284 462 416 440 438 462 412 462 412 462 416 466 412 "
    "462 412 462 412 440 442 462 412 462 412 460 418 462 416 462 412 462 "
    "418 462 412 462 416 462 412 436 442 462 412 460 418 462 416 462 412 "
    "460 412 462 420 436 438 462 412 462 416 432 448 436 438 436 1310 436 "
    "1310 462 420 432 442 436 438 462 416 432 444 432 10008 3480 1744 492 "
    "382 492 1254 492 386 488 390 492 382 492 386 488 386 492 386 492 386 "
    "488 386 488 386 492 386 492 382 492 1258 488 386 488 390 492 386 488 "
    "386 488 386 492 390 488 386 488 1256 488 1258 488 1262 488 390 488 386 "
    "488 1258 488 390 488 392 488 386 488 386 488 394 488 386 488 386 488 "
    "390 488 390 488 386 488 390 462 412 488 390 462 1282 488 390 456 416 "
    "458 1292 456 1288 488 1258 488 392 456 422 488 390 484 392 484 1262 "
    "458 420 484 1262 482 1262 488 392 484 394 484 416 436 442 458 416 458 "
    "422 430 448 432 442 458 416 458 1296 432 1314 458 1288 432 1312 432 "
    "1322 428 446 428 1318 432 442 432 1318 432 1318 428 446 428 1318 428 "
    "1322 430 448 426 448 428 452 426 452 426 448 428 472 400 478 402 478 "
    "402 472 402 476 402 472 402 478 402 472 402 1348 398 1348 398 1352 398 "
    "508 370 478 398 476 398 512 366 508 370 502 372 508 340 538 372 504 "
    "344 1400 344 1400 346 1434 314 560 316 588 290 560 314 564 396 400 474 "
    "400 480 394 480 404 474 400 454 446 454 426 448 430 424 450 428 452 "
    "448 426 426 452 424 1322 454 426 450 424 426 452 428 452 450 424 428 "
    "446 426 1322 454 426 422 450 454 426 448 430 454 426 448 426 428 446 "
    "454 430 454 422 452 424 424 452 452 430 424 452 452 426 448 426 426 "
    "456 448 426 448 1296 424 1322 426 1326 450 1270 478 422 454 424 424 "
    "450 454"
)


def test_real_raw_capture_decodes():
    pulses = [int(x) for x in REAL_RAW.split()]
    first, second = decode(PANASONIC_AC, pulses, expected=["first", "second"])
    assert first.data + second.data == bytes.fromhex(
        "0220e00400000006" "0220e00400393480af0d000ee000008100001e"
    )
