import dataclasses
import random

import pytest

from pyhvac import brands, registry
from pyhvac.ir.codec import encode as ir_encode
from pyhvac.protocols.electra import ELECTRA_AC_LAYOUT
from pyhvac.state import HvacState
from smartir.codes import Code, Key, SmartIRFile
from smartir.match import candidates, match

CANDIDATES = candidates()
FANS = {"low": "1", "mid": "2", "high": "3", "auto": "auto"}


def synthetic(brand, model, keys_in_f=False, features=None, tamper=None):
    """A SmartIR file the way someone would learn it from this device;
    ``tamper`` may rewrite each frame's bytes first."""
    dev = registry.get_device(brand, model)

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


def test_one_code_no_mapping_explains_is_near():
    f = synthetic("Electra", registry.models("Electra")[0])
    swapped = dataclasses.replace(f.codes[0], pulses=f.codes[5].pulses)
    f = dataclasses.replace(f, codes=(swapped,) + f.codes[1:])
    m = match(f, CANDIDATES)
    assert m.verdict == "near" and m.unexplained == (f.codes[0].key,)


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
