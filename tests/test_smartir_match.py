import dataclasses
import random

import pytest

from pyhvac import brands, registry
from pyhvac.ir.codec import encode as ir_encode
from pyhvac.protocols.coolix import COOLIX, COOLIX_TURBO, coolix_message
from pyhvac.protocols.electra import ELECTRA_AC_LAYOUT
from pyhvac.state import HvacState
from smartir.codes import Code, Key, SmartIRFile
from smartir.match import candidates, match

CANDIDATES = candidates()
FANS = {"low": "1", "mid": "2", "high": "3", "auto": "auto"}


def synthetic(brand, model, keys_in_f=False, features=None, tamper=None, dev=None):
    """A SmartIR file the way someone would learn it from this device
    (``dev``, else the registry's); ``tamper`` may rewrite each frame's
    bytes first."""
    dev = dev or registry.get_device(brand, model)

    def pulses(state):
        if tamper is None:
            return dev.encode(None, state).signal.pulses
        frames = dev.frames(None, dev.normalise(state), ())
        frames = [dataclasses.replace(f, data=tamper(f.data)) for f in frames]
        return ir_encode(dev.PROTOCOL, frames).pulses

    codes = []
    temps = range(61, 86, 2) if keys_in_f else range(17, 30)
    for mode in ("cool", "heat"):
        for label, fan in FANS.items():
            for t in temps:
                c = round((t - 32) * 5 / 9, 1) if keys_in_f else float(t)
                state = HvacState(True, mode, c, fan=fan, features=features or {})
                codes.append(
                    Code(Key(mode, label, None, float(t)), tuple(pulses(state)))
                )
    off = HvacState(False, "cool", 24.0, features=features or {})
    codes.append(Code(Key("off", None, None, None), tuple(pulses(off))))
    return SmartIRFile(
        1,
        brand,
        (model,),
        "Broadlink",
        "Base64",
        min(temps),
        max(temps),
        1,
        ("cool", "heat"),
        tuple(FANS),
        (),
        tuple(codes),
        0,
    )


def test_a_file_learned_from_a_pyhvac_device_is_covered():
    m = match(synthetic("Electra", registry.models("Electra")[0]), CANDIDATES)
    assert m.verdict == "covered" and m.candidate == "ElectraAcDevice"
    assert m.fans == FANS and m.units == "C"


def test_constant_features_are_found():
    f = synthetic("Electra", registry.models("Electra")[0], features={"light": True})
    m = match(f, CANDIDATES)
    assert m.verdict == "covered" and m.features["light"] is True


def test_fahrenheit_keys_are_recognised():
    m = match(
        synthetic("Electra", registry.models("Electra")[0], keys_in_f=True), CANDIDATES
    )
    assert m.verdict == "covered" and m.units == "F"


def test_random_pulses_are_unknown():
    rng = random.Random(1)
    codes = tuple(
        Code(
            Key("cool", "low", None, float(t)),
            tuple(rng.randrange(300, 3000) for _ in range(60)),
        )
        for t in range(17, 27)
    )
    f = SmartIRFile(
        2,
        "X",
        ("Y",),
        "Broadlink",
        "Base64",
        17,
        26,
        1,
        ("cool",),
        ("low",),
        (),
        codes,
        0,
    )
    assert match(f, CANDIDATES).verdict == "unknown"


def test_the_remote_variant_is_identified():
    brand, model = next(
        (b, m)
        for b, m, k, c, v in brands.MODELS
        if c.__name__ == "Haier176Device" and v == "B"
    )
    m = match(synthetic(brand, model), CANDIDATES)
    assert m.verdict == "covered" and m.candidate == "Haier176Device/B"


def coolix_file(**kw):
    brand, model = next(
        (b, m) for b, m, k, c, v in brands.MODELS if c.__name__ == "CoolixDevice"
    )
    return synthetic(brand, model, **kw)


def test_a_mislabelled_code_is_explained_by_another_state():
    f = coolix_file()
    first, second = f.codes[0], f.codes[1]  # cool, low, 17 and 18
    swapped = (
        dataclasses.replace(first, pulses=second.pulses),
        dataclasses.replace(second, pulses=first.pulses),
    )
    f = dataclasses.replace(f, codes=swapped + f.codes[2:])
    m = match(f, CANDIDATES)
    assert m.verdict == "covered" and m.candidate == "CoolixDevice"
    assert (m.verified, m.relabelled) == (len(f.codes) - 2, 2)
    assert [k for k, _ in m.relabels] == [first.key, second.key]


def test_the_off_code_filed_under_an_on_state_is_explained():
    f = coolix_file()
    off = f.codes[-1]
    misfiled = dataclasses.replace(f.codes[0], pulses=off.pulses)
    f = dataclasses.replace(f, codes=(misfiled,) + f.codes[1:])
    m = match(f, CANDIDATES)
    assert m.verdict == "covered" and m.relabelled == 1
    assert m.relabels[0][1] == "off"


def test_codes_that_do_not_decode_do_not_block_covered():
    f = coolix_file()
    cut = dataclasses.replace(f.codes[3], pulses=f.codes[3].pulses[:9])
    f = dataclasses.replace(f, codes=f.codes[:3] + (cut,) + f.codes[4:])
    m = match(f, CANDIDATES)
    assert m.verdict == "covered"
    assert (m.decoded, m.usable) == (len(f.codes) - 1, len(f.codes))


def test_a_toggle_word_alone_is_explained():
    f = coolix_file()
    word = ir_encode(COOLIX, coolix_message(COOLIX_TURBO)).pulses
    f = dataclasses.replace(
        f, codes=f.codes + (Code(Key("fan_only", "silent", None, 24.0), word),)
    )
    m = match(f, CANDIDATES)
    assert m.verdict == "covered" and m.relabelled == 1


def test_another_protocol_with_the_same_timing_is_not_matched():
    def no_complements(data):
        return bytes(data[i - i % 2] for i in range(len(data)))

    m = match(coolix_file(tamper=no_complements), CANDIDATES)
    assert m.verdict == "unknown"


def test_a_field_pyhvac_never_sets_is_named_as_the_gap():
    def sensor(data):
        data = bytearray(data)
        ELECTRA_AC_LAYOUT.write_raw(data, "sensor_temp", 0x19)
        ELECTRA_AC_LAYOUT.checksum.apply(data)
        return bytes(data)

    f = synthetic("Electra", registry.models("Electra")[0], tamper=sensor)
    m = match(f, CANDIDATES)
    assert m.verdict == "near" and m.candidate == "ElectraAcDevice"
    assert m.gaps == {"sensor_temp": len(f.codes)}


def test_declared_variants_without_rows_are_candidates():
    names = {c.name for c in CANDIDATES}
    assert {"CoolixDevice", "CoolixDevice/16C", "CoolixDevice/quiet"} <= names


def test_a_key_pressed_field_is_not_compared():
    from pyhvac.protocols.electra import ElectraAcDevice

    keys = iter([0x00, 0x01, 0x04, 0x05, 0x02, 0x08] * 50)

    def pressed(data):
        data = bytearray(data)
        data[11] = next(keys)
        data[12] = sum(data[:12]) & 0xFF
        return bytes(data)

    dev = ElectraAcDevice("AUX", "unit", variant="aux")
    m = match(synthetic("AUX", "unit", tamper=pressed, dev=dev), CANDIDATES)
    assert m.verdict == "covered" and m.candidate == "ElectraAcDevice/aux"


def test_a_swing_label_may_mean_horizontal_swing():
    dev = registry.get_device("Electra", registry.models("Electra")[0])
    labels = {"stop": ("off", "off"), "hSwing": ("off", "swing")}
    codes = []
    for label, (v, h) in labels.items():
        for t in range(17, 30):
            st = HvacState(True, "cool", float(t), swing_v=v, swing_h=h)
            pulses = dev.encode(None, st).signal.pulses
            codes.append(Code(Key("cool", "auto", label, float(t)), tuple(pulses)))
    f = SmartIRFile(
        3,
        "Electra",
        ("X",),
        "Broadlink",
        "Base64",
        17,
        29,
        1,
        ("cool",),
        ("auto",),
        tuple(labels),
        tuple(codes),
        0,
    )
    m = match(f, CANDIDATES)
    assert m.verdict == "covered" and m.candidate.startswith("ElectraAcDevice")
    assert m.verified == len(codes)


def test_key_pressed_fields_are_not_named_as_gaps():
    from pyhvac.protocols.electra import ELECTRA_AUX_LAYOUT, ElectraAcDevice

    keys = iter([0x00, 0x04, 0x05, 0x08] * 80)

    def pressed_with_sensor(data):
        data = bytearray(data)
        data[11] = next(keys)
        ELECTRA_AUX_LAYOUT.write_raw(data, "sensor_temp", 0x19)
        ELECTRA_AUX_LAYOUT.checksum.apply(data)
        return bytes(data)

    dev = ElectraAcDevice("AUX", "unit", variant="aux")
    f = synthetic("AUX", "unit", tamper=pressed_with_sensor, dev=dev)
    m = match(f, CANDIDATES)
    assert m.verdict == "near" and m.gaps == {"sensor_temp": len(f.codes)}
