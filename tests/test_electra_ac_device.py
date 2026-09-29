import pytest

from c_oracle import c_encode

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
from pyhvac.ir.codec import decode
from pyhvac.plugins.electra import (
    ELECTRA_AC,
    ELECTRA_AC_AEG_MODELS,
    ELECTRA_AC_AUX_MODELS,
    ELECTRA_AC_CENTEK_MODELS,
    ELECTRA_AC_DELONGHI_MODELS,
    ELECTRA_AC_ELECTROLUX_MODELS,
    ELECTRA_AC_FRIGIDAIRE_MODELS,
    ELECTRA_AC_LAYOUT,
    ELECTRA_AC_MODELS,
    ELECTRA_AC_SUBTROPIC_MODELS,
    ElectraAcDevice,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Electra values here: the legacy
# glue (IRGHVAC.trans_swing / trans_hswing) has no "on" key, so IRac's swingv
# and swingh stay kOff and IRElectraAc::setSwingV / setSwingH write
# kElectraAcSwingOff (0b111) instead of kElectraAcSwingOn (0b000).
DEFECTS = (
    Defect("swing_v", "swing", "off", "legacy glue never passes swing on"),
    Defect("swing_h", "swing", "off", "legacy glue never passes hswing on"),
)

SERVED = (
    [("electra", m) for m in ELECTRA_AC_MODELS]
    + [("aeg", m) for m in ELECTRA_AC_AEG_MODELS]
    + [("aux", m) for m in ELECTRA_AC_AUX_MODELS]
    + [("centek", m) for m in ELECTRA_AC_CENTEK_MODELS]
    + [("delonghi", m) for m in ELECTRA_AC_DELONGHI_MODELS]
    + [("electrolux", m) for m in ELECTRA_AC_ELECTROLUX_MODELS]
    + [("frigidaire", m) for m in ELECTRA_AC_FRIGIDAIRE_MODELS]
    + [("subtropic", m) for m in ELECTRA_AC_SUBTROPIC_MODELS]
)
MODES = ("auto", "cool", "fan", "dry", "heat")
FEATURES = ("light", "cleaning", "powerful", "quiet")


def device():
    return ElectraAcDevice("electra", "generic")


def features(**on):
    return {f: bool(on.get(f)) for f in FEATURES}


def state(power=True, mode="cool", temperature=24.0, **kw):
    return device().normalise(HvacState(power, mode, temperature, **kw))


def read(target, previous=None):
    (main,) = device().frames(previous, target, ())
    return ELECTRA_AC_LAYOUT.read(main.data)


@pytest.mark.parametrize("record", oracle_params("ELECTRA_AC"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


@pytest.mark.parametrize("record, states", sequence_params("ELECTRA_AC"))
def test_sequence_matches_a_persistent_c_object(record, states):
    # The light toggle depends on the message before, which C's IRac keeps.
    dev = device()
    assert_sequence_matches_c(dev, record, states, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("ELECTRA_AC"):
        (main,) = dev.frames(None, state_from_record(dev, record["state"]), ())
        values = ELECTRA_AC_LAYOUT.read(main.data)
        assert ELECTRA_AC_LAYOUT.build(**values) == bytearray(main.data)


# Real captures from ir_Electra_test.cpp.
ISSUE_527 = "c387f62860002000002000050d"  # RealExampleDecode
COOL_32_AUTO = "c3c7e000a0002000002000408a"  # HumanReadable (issue 778)
COOL_16_AUTO = "c347e000a0002000002000410b"  # HumanReadable
COOL_16_LOW = "c347e0006000200000200041cb"  # HumanReadable
CLEAN_LIGHT = "c387e0006000200000240019e7"  # Clean / LightToggle (issue 1033)
TURBO = "c387e000604020000020000812"  # Turbo (issue 1033)
IFEEL = "c36fe000a00028640020001e7c"  # IFeelAndSensor
SENSOR_UPDATE = "c39fe040a00088660030001e5e"  # IFeelAndSensor


def raw(text):
    return bytes.fromhex(text)


@pytest.mark.parametrize(
    "capture, fields",
    [
        (
            ISSUE_527,
            {"power": 1, "mode": "cool", "temperature": 24, "fan": "1"},
        ),
        (COOL_32_AUTO, {"mode": "cool", "temperature": 32, "fan": "auto"}),
        (COOL_16_AUTO, {"temperature": 16, "fan": "auto", "light_toggle": 0x41}),
        (COOL_16_LOW, {"temperature": 16, "fan": "1", "swing_v": "off"}),
        (CLEAN_LIGHT, {"clean": 1, "light_toggle": 0x19, "swing_h": "off"}),
        (TURBO, {"turbo": 1, "quiet": 0, "light_toggle": 0x08}),
        (IFEEL, {"ifeel": 1, "sensor_temp": 26 + 0x4A, "temperature": 21}),
        (SENSOR_UPDATE, {"sensor_update": 1, "sensor_temp": 28 + 0x4A}),
    ],
)
def test_layout_reads_the_real_captures(capture, fields):
    data = raw(capture)
    values = ELECTRA_AC_LAYOUT.read(data)
    assert {k: values[k] for k in fields} == fields
    assert ELECTRA_AC_LAYOUT.checksum.check(data)


@pytest.mark.parametrize(
    "capture",
    [COOL_32_AUTO, COOL_16_AUTO, COOL_16_LOW, CLEAN_LIGHT, TURBO, IFEEL],
)
def test_layout_round_trips_the_real_captures(capture):
    data = raw(capture)
    assert ELECTRA_AC_LAYOUT.build(**ELECTRA_AC_LAYOUT.read(data)) == data


def test_issue_527_capture_has_undocumented_bits():
    # Bytes 2 and 3 carry bits the header leaves unnamed (0xF6, 0x28), so
    # the layout reads the capture but cannot rebuild it.
    data = raw(ISSUE_527)
    rebuilt = ELECTRA_AC_LAYOUT.build(**ELECTRA_AC_LAYOUT.read(data))
    assert (rebuilt[2], rebuilt[3]) == (0xE0, 0x00)
    assert rebuilt[4:12] == data[4:12]


def test_port_reproduces_the_turbo_capture():
    # Cool, 24C, fan low, turbo, swings off, light unchanged.
    target = state(True, "cool", 24.0, fan="1", features=features(powerful=1))
    (main,) = device().frames(None, target, ())
    assert main.data == raw(TURBO)


@pytest.mark.parametrize(
    "capture, target",
    [
        (COOL_32_AUTO, dict(temperature=32.0, fan="auto", features=features())),
        (COOL_16_AUTO, dict(temperature=16.0, fan="auto", features=features())),
        (COOL_16_LOW, dict(temperature=16.0, fan="1", features=features())),
        (
            CLEAN_LIGHT,
            dict(temperature=24.0, fan="1", features=features(light=1, cleaning=1)),
        ),
    ],
)
def test_port_reproduces_captures_up_to_the_light_code(capture, target):
    # These remotes sent other LightToggle codes than the header's constants
    # (0x40/0x41 for off, 0x19 for on; the header lists 0x15/0x19 on and
    # 0x08/0x05 off). The port sends kElectraAcLightToggleOn (0x15) and
    # kElectraAcLightToggleOff (0x08), which the mask 0x11 reads the same.
    data = raw(capture)
    (main,) = device().frames(None, state(True, "cool", **target), ())
    ours = main.data
    assert ours[:11] == data[:11]
    assert (ours[11] & 0x11 == 0x11) == (data[11] & 0x11 == 0x11)


def test_checksum_is_the_sum_of_bytes_0_to_11():
    for capture in (ISSUE_527, TURBO, CLEAN_LIGHT, SENSOR_UPDATE):
        data = bytearray(raw(capture))
        assert data[12] == sum(data[:12]) & 0xFF
        data[12] = 0
        ELECTRA_AC_LAYOUT.checksum.apply(data)
        assert bytes(data) == raw(capture)


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("t", [16.0, 17.0, 24.0, 31.0, 32.0])
def test_setpoint_is_sent_in_every_mode(mode, t):
    values = read(state(True, mode, t))
    assert (values["mode"], values["temperature"]) == (mode, int(t))


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("t", [16.0, 32.0])
def test_off_carries_mode_auto_and_the_setpoint(mode, t):
    # IRac passes mode "off"; convertMode maps it to kElectraAcAuto.
    values = read(state(False, mode, t, fan="2", swing_v="swing"))
    assert (values["power"], values["mode"], values["temperature"]) == (
        0,
        "auto",
        int(t),
    )
    assert (values["fan"], values["swing_v"]) == ("2", "swing")


@pytest.mark.parametrize("mode", MODES)
def test_off_matches_the_c_path_in_every_mode(mode):
    for t in (16.0, 25.0, 32.0):
        for fan in ("auto", "1", "2", "3"):
            target = state(False, mode, t, fan=fan, features=features(quiet=1))
            pulses = c_encode("electra", "generic", "Electra", target)
            (theirs,) = decode(device().PROTOCOL, list(pulses), expected=["main"])
            (ours,) = device().frames(None, target, ())
            assert ours.data == theirs.data


@pytest.mark.parametrize(
    "fan, code", [("auto", 0b101), ("1", 0b011), ("2", 0b010), ("3", 0b001)]
)
def test_every_fan_level_uses_its_documented_code(fan, code):
    (main,) = device().frames(None, state(fan=fan), ())
    assert ELECTRA_AC_LAYOUT.read_raw(main.data, "fan") == code


@pytest.mark.parametrize("swing, code", [("off", 0b111), ("swing", 0b000)])
def test_swings_use_the_documented_codes(swing, code):
    (main,) = device().frames(None, state(swing_v=swing, swing_h=swing), ())
    assert ELECTRA_AC_LAYOUT.read_raw(main.data, "swing_v") == code
    assert ELECTRA_AC_LAYOUT.read_raw(main.data, "swing_h") == code


@pytest.mark.parametrize(
    "feature, field", [("powerful", "turbo"), ("quiet", "quiet"), ("cleaning", "clean")]
)
def test_features_set_their_bits(feature, field):
    assert read(state(features=features(**{feature: 1})))[field] == 1
    assert read(state(features=features()))[field] == 0


def test_all_features_together():
    values = read(state(features=features(powerful=1, quiet=1, cleaning=1, light=1)))
    assert (values["turbo"], values["quiet"], values["clean"]) == (1, 1, 1)
    assert values["light_toggle"] == 0x15


def test_unset_fields_stay_clear():
    values = read(state(True, "heat", 30.0, fan="3", features=features(quiet=1)))
    assert (values["ifeel"], values["sensor_update"], values["sensor_temp"]) == (
        0,
        0,
        0,
    )


def test_light_toggle_without_previous_is_the_target_light():
    # A fresh IRac's previous state is protocol UNKNOWN: handleToggles does
    # nothing, so LightToggle follows light.
    assert read(state(features=features(light=1)))["light_toggle"] == 0x15
    assert read(state(features=features()))["light_toggle"] == 0x08


@pytest.mark.parametrize(
    "before, after, code",
    [
        (True, True, 0x08),
        (True, False, 0x15),
        (False, False, 0x08),
        (False, True, 0x15),
    ],
)
def test_light_toggle_with_previous_toggles_on_change(before, after, code):
    # IRac::handleToggles' ELECTRA_AC rule (light ^ prev.light), which a
    # persistent IRac applies (test_sequence_matches_a_persistent_c_object).
    previous = state(features=features(light=before))
    target = state(features=features(light=after))
    assert read(target, previous)["light_toggle"] == code


def test_previous_only_affects_the_light_toggle():
    previous = state(False, "heat", 16.0, fan="3", features=features(quiet=1))
    target = state(True, "cool", 24.0, fan="1", features=features(powerful=1))
    assert read(target, previous) == read(target)


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 24.0)).signal.pulses
    assert pulses[:2] == (9166, 4470)
    assert pulses[-2:] == (646, 100000)
    assert len(pulses) == 2 + 2 * 104 + 2


@pytest.mark.parametrize("plugin, model", SERVED)
def test_registry_serves_the_port(plugin, model):
    assert isinstance(registry.get_device(plugin, model), ElectraAcDevice)


@pytest.mark.parametrize("field, key", [("swing_v", "swing"), ("swing_h", "hswing")])
def test_undeclared_swing_deviation_is_reported(field, key):
    dev = device()
    record = next(r for r in load_oracle("ELECTRA_AC") if r["state"].get(key) == "on")
    defects = [d for d in DEFECTS if d.field != field]
    with pytest.raises(AssertionError, match=field):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects)


def test_swing_off_needs_no_defect():
    dev = device()
    for record in load_oracle("ELECTRA_AC"):
        if "on" not in (record["state"].get("swing"), record["state"].get("hswing")):
            assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = next(
        r for r in load_oracle("ELECTRA_AC") if r["state"].get("swing") == "on"
    )
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)


# No real capture in ir_Electra_test.cpp needs it, but
# decodeElectraAC matches with _tolerance (25 %) and no mark excess.
def test_decode_tolerance_is_the_c_decoders():
    assert (ELECTRA_AC.tolerance, ELECTRA_AC.mark_excess) == (0.25, 0)


def test_capabilities_are_the_headers():
    # ir_Electra.h: kElectraAcMinTemp/MaxTemp 16-32; kElectraAcFan{Auto,Low,
    # Med,High}; kElectraAcSwingOn/Off for SwingV and SwingH; LightToggle,
    # Clean, Turbo and Quiet (IFeel and SensorTemp are sensor readings).
    caps = device().capabilities
    assert set(caps.modes) == {"auto", "cool", "fan", "dry", "heat"}
    assert (caps.temperature.min, caps.temperature.max) == (16.0, 32.0)
    assert caps.fan.values == ("auto", "1", "2", "3")
    assert caps.swing_v.values == caps.swing_h.values == ("off", "swing")
    assert set(caps.features) == {"light", "cleaning", "powerful", "quiet"}
