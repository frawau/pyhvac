import dataclasses
import itertools
import random

import pytest

from pyhvac import brands, registry
from pyhvac.ir.codec import encode as ir_encode
from pyhvac.protocols.coolix import COOLIX, COOLIX_TURBO, coolix_message
from pyhvac.protocols.electra import ELECTRA_AC_LAYOUT
from pyhvac.state import HvacState
from smartir.codes import Code, Key, SmartIRFile
from smartir.match import candidates, decode_code, match

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
    f = synthetic("Electra", registry.models("Electra")[0], features={"cleaning": True})
    m = match(f, CANDIDATES)
    assert m.verdict == "covered" and m.features["cleaning"] is True


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
    assert m.gaps == {
        "sensor_temp": len(f.codes) - 1
    }  # the off code turns the unit off


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
    assert m.verdict == "near" and m.gaps == {
        "sensor_temp": len(f.codes) - 1
    }  # the off code turns the unit off


def test_an_off_code_carrying_another_state_is_explained():
    # A remote's off message carries the last mode; pyhvac's Electra off
    # carries auto (as IRac sends it). The unit turns off either way.
    f = synthetic("Electra", registry.models("Electra")[0])
    off = f.codes[-1]
    assert off.key.mode == "off"
    dev = registry.get_device("Electra", registry.models("Electra")[0])
    (frame,) = dev.frames(None, dev.normalise(HvacState(False, "cool", 24.0)), ())
    data = bytearray(frame.data)
    ELECTRA_AC_LAYOUT.write_raw(data, "mode", 1)  # kElectraAcCool
    ELECTRA_AC_LAYOUT.checksum.apply(data)
    frames = [dataclasses.replace(frame, data=bytes(data))]
    carried = dataclasses.replace(off, pulses=ir_encode(dev.PROTOCOL, frames).pulses)
    f = dataclasses.replace(f, codes=f.codes[:-1] + (carried,))
    m = match(f, CANDIDATES)
    assert m.verdict == "covered" and m.relabelled == 1


def test_a_toggle_field_is_not_compared():
    # Kelon's power toggle depends on the previous state, which the file
    # does not record: a capture made with the unit on has it clear.
    from pyhvac.protocols.kelon import KELON_LAYOUT

    def no_toggle(data):
        data = bytearray(data)
        KELON_LAYOUT.write_raw(data, "power_toggle", 0)
        return bytes(data)

    m = match(synthetic("Hisense", "unit", tamper=no_toggle, dev=kelon()), CANDIDATES)
    assert m.verdict == "covered" and m.candidate.startswith("KelonDevice")
    assert m.relabelled == 0  # each code verified as its own state, not as off


def kelon():
    from pyhvac.protocols.kelon import KelonDevice

    return KelonDevice("Hisense", "unit")


def test_captures_beyond_the_protocol_tolerance_still_decode():
    # Broadlink learns with jitter: spaces 30 % long are past Coolix's 30 %
    # decoder tolerance once compensated; the checksum and the encoding
    # comparison still decide whether the code is pyhvac's.
    f = coolix_file()
    stretched = tuple(
        dataclasses.replace(
            c,
            pulses=tuple(
                round(d * 1.32) if i % 2 and d < 2000 else d
                for i, d in enumerate(c.pulses)
            ),
        )
        for c in f.codes
    )
    m = match(dataclasses.replace(f, codes=stretched), CANDIDATES)
    assert m.verdict == "covered" and m.candidate.startswith("CoolixDevice")


def test_a_capture_of_the_start_of_a_message_is_explained():
    # pyhvac's Toshiba sends the state message (twice), then a short one; a
    # remote may send the state alone.
    from pyhvac.protocols.toshiba import ToshibaAcDevice

    dev = ToshibaAcDevice("Toshiba", "unit")

    def state_only(frames):
        return frames[:2]

    codes = []
    for t in range(17, 30):
        st = dev.normalise(HvacState(True, "cool", float(t)))
        frames = state_only(dev.frames(None, st, ()))
        codes.append(
            Code(
                Key("cool", "auto", None, float(t)),
                ir_encode(dev.PROTOCOL, frames).pulses,
            )
        )
    f = SmartIRFile(
        4,
        "Toshiba",
        ("X",),
        "Broadlink",
        "Base64",
        17,
        29,
        1,
        ("cool",),
        ("auto",),
        (),
        tuple(codes),
        0,
    )
    m = match(f, CANDIDATES)
    assert m.verdict == "covered" and m.candidate == "ToshibaAcDevice"


def test_a_fifth_of_glitched_captures_does_not_block_covered():
    f = coolix_file()
    glitched = tuple(
        dataclasses.replace(c, pulses=c.pulses[:9]) if i % 5 == 0 else c
        for i, c in enumerate(f.codes)
    )
    m = match(dataclasses.replace(f, codes=glitched), CANDIDATES)
    assert m.verdict == "covered"


def test_short_gaps_between_frames_still_decode():
    f = coolix_file()
    short = tuple(
        dataclasses.replace(
            c, pulses=tuple(3000 if 5000 < d < 6000 else d for d in c.pulses)
        )
        for c in f.codes
    )
    m = match(dataclasses.replace(f, codes=short), CANDIDATES)
    assert m.verdict == "covered" and m.candidate.startswith("CoolixDevice")


def test_codes_explained_only_under_other_labels_are_not_covered():
    # If no label agrees, the candidate is guessing: near, not covered.
    f = coolix_file()
    on = [c for c in f.codes if c.key.mode != "off"]
    shifted = tuple(
        dataclasses.replace(c, pulses=on[(i + 1) % len(on)].pulses)
        for i, c in enumerate(on)
    )
    m = match(dataclasses.replace(f, codes=shifted), CANDIDATES)
    assert m.verdict == "near"


def test_a_decode_without_data_is_no_decode():
    # Airwell's message ends with a bitless section: alone, it would
    # "decode" any capture as an empty frame.
    airwell = next(c for c in CANDIDATES if c.name == "AirwellDevice")
    brand, model = next(
        (b, m) for b, m, k, c, v in brands.MODELS if c.__name__ == "Lg2Device"
    )
    f = synthetic(brand, model)
    assert all(decode_code(airwell, list(c.pulses)) is None for c in f.codes)


def test_a_lead_in_before_the_message_is_skipped():
    # Hitachi captures (1084) start with a 30 ms mark and a 50 ms space.
    f = coolix_file()
    led = tuple(
        dataclasses.replace(c, pulses=(30000, 50000) + tuple(c.pulses)) for c in f.codes
    )
    m = match(dataclasses.replace(f, codes=led), CANDIDATES)
    assert m.verdict == "covered" and m.candidate.startswith("CoolixDevice")


def test_a_clock_field_is_not_compared():
    # A remote sends its time of day: the capture's moment, not the state.
    from pyhvac.protocols.mitsubishi_electric import MITSUBISHI_AC_LAYOUT

    minutes = itertools.cycle(range(0, 1440, 7))

    def clocked(data):
        data = bytearray(data)
        MITSUBISHI_AC_LAYOUT.write_raw(data, "clock", next(minutes) // 10)
        MITSUBISHI_AC_LAYOUT.checksum.apply(data)
        return bytes(data)

    brand, model = next(
        (b, m) for b, m, k, c, v in brands.MODELS if c.__name__ == "MitsubishiAcDevice"
    )
    m = match(synthetic(brand, model, tamper=clocked), CANDIDATES)
    assert m.verdict == "covered" and m.candidate == "MitsubishiAcDevice"


def test_an_off_code_with_its_power_bit_clear_is_explained():
    # Gree remotes keep ModelA (and the last light, display...) in their
    # off message; pyhvac's off clears ModelA. The power bit is clear: the
    # unit turns off.
    from pyhvac.protocols.gree import GREE_LAYOUT

    def model_a_kept(frames):
        data = bytearray(b"".join(f.data for f in frames))
        if not GREE_LAYOUT.read(data)["power"]:
            GREE_LAYOUT.write_raw(data, "model_a", 1)
            GREE_LAYOUT.write_raw(data, "display_temp", 2)
            GREE_LAYOUT.checksum.apply(data)
        return [
            dataclasses.replace(frames[0], data=bytes(data[:4])),
            dataclasses.replace(frames[1], data=bytes(data[4:])),
        ]

    brand, model = next(
        (b, m)
        for b, m, k, c, v in brands.MODELS
        if c.__name__ == "GreeDevice" and v == "YAW1F"
    )
    dev = registry.get_device(brand, model)
    f = synthetic(brand, model)
    off = f.codes[-1]
    frames = model_a_kept(
        dev.frames(None, dev.normalise(HvacState(False, "cool", 24.0)), ())
    )
    kept = dataclasses.replace(off, pulses=ir_encode(dev.PROTOCOL, frames).pulses)
    m = match(dataclasses.replace(f, codes=f.codes[:-1] + (kept,)), CANDIDATES)
    assert m.verdict == "covered" and m.candidate.startswith("GreeDevice")


def test_an_off_message_under_an_on_label_is_explained():
    # A capture with the power bit clear, filed under an on state: an off
    # code in the wrong place.
    f = synthetic("Electra", registry.models("Electra")[0])
    dev = registry.get_device("Electra", registry.models("Electra")[0])
    (frame,) = dev.frames(None, dev.normalise(HvacState(False, "cool", 24.0)), ())
    data = bytearray(frame.data)
    ELECTRA_AC_LAYOUT.write_raw(data, "mode", 1)  # carrying cool
    ELECTRA_AC_LAYOUT.checksum.apply(data)
    frames = [dataclasses.replace(frame, data=bytes(data))]
    misfiled = dataclasses.replace(
        f.codes[0], pulses=ir_encode(dev.PROTOCOL, frames).pulses
    )
    m = match(dataclasses.replace(f, codes=(misfiled,) + f.codes[1:]), CANDIDATES)
    assert m.verdict == "covered"


def test_frames_of_the_same_length_with_different_layouts_are_valid():
    # TCL112's special and normal messages are both 14 bytes, with
    # different checksums.
    from pyhvac.protocols.tcl import Tcl112AcDevice

    dev = Tcl112AcDevice("TCL", "unit", variant="TAC09CHSD-R")
    m = match(synthetic("TCL", "unit", dev=dev), CANDIDATES)
    assert m.verdict == "covered" and m.candidate == "Tcl112AcDevice/TAC09CHSD-R"


def test_a_feature_used_under_one_label_is_explained_on_a_large_device():
    # TCL112 -X: 5 modes, half degrees, 6 fans, 14 swing pairs; the
    # "turbo" label's codes are the powerful feature.
    from pyhvac.protocols.tcl import Tcl112AcDevice

    dev = Tcl112AcDevice("TCL", "unit", variant="TAC09CHSD-X83")
    codes = []
    for mode in ("cool", "heat"):
        for label, fan, powerful in (("low", "1", False), ("turbo", "auto", True)):
            for t in range(16, 31):
                st = HvacState(
                    True, mode, float(t), fan=fan, features={"powerful": powerful}
                )
                pulses = dev.encode(None, st).signal.pulses
                codes.append(Code(Key(mode, label, None, float(t)), tuple(pulses)))
    f = SmartIRFile(
        5,
        "TCL",
        ("X",),
        "Broadlink",
        "Base64",
        16,
        30,
        1,
        ("cool", "heat"),
        ("low", "turbo"),
        (),
        tuple(codes),
        0,
    )
    m = match(f, CANDIDATES)
    assert m.verdict == "covered" and m.candidate == "Tcl112AcDevice/TAC09CHSD-X83"
