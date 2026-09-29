import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.ir.codec import decode
from pyhvac.plugins.technibel import (
    TECHNIBEL_AC,
    TECHNIBEL_AC_ALASKA_MODELS,
    TECHNIBEL_AC_CAPABILITIES,
    TECHNIBEL_AC_LAYOUT,
    TECHNIBEL_AC_MODELS,
    TECHNIBEL_AC_RESET_STATE,
    TECHNIBEL_AC_TECO_MODELS,
    TechnibelAcDevice,
)
from pyhvac.state import HvacState

# The C path never sends swing on or sleep: IRGHVAC.trans_swing has no "on"
# key and IRGHVAC.build_ircode has no "sleep" key, so the errors are
# swallowed, and IRac::technibel gets swingv kOff and sleep -1 and clears
# the Swing and Sleep bits. The port sets the documented bits
# (test_swing_and_sleep_match_c_with_the_glue_bypassed shows C sets them
# too once they reach it).
DEFECTS = (
    Defect("swing_v", "swing", "off", "C glue has no swing 'on' key"),
    Defect("sleep", 1, 0, "C glue never passes sleep"),
)

# ir_Technibel_test.cpp RealExample, SyntheticSelfDecode and
# ConstructKnownState: 0x1881221200004B, "Power: On, Mode: 1 (Cool), Fan: 2
# (Medium), Temp: 18C, Sleep: Off, Swing(V): On, Timer: Off".
KNOWN_STATE = (0x1881221200004B).to_bytes(7, "big")
# fmt: off
REAL_EXAMPLE = (
    8812, 4376,
    534, 560, 530, 562, 530, 562, 532, 1668, 532, 1634, 560, 560, 530, 562,
    528, 566, 530, 1668, 532, 560, 504, 588, 526, 568, 530, 562, 530, 562,
    528, 564, 530, 1670, 530, 562, 530, 564, 528, 1670, 530, 564, 532, 560,
    530, 562, 532, 1636, 560, 564, 530, 562, 528, 564, 528, 564, 526, 1672,
    528, 538, 554, 564, 528, 1640, 558, 564, 530, 562, 526, 564, 504, 586,
    504, 592, 526, 564, 504, 588, 526, 564, 504, 592, 528, 562, 526, 566,
    526, 564, 504, 592, 526, 566, 530, 562, 530, 562, 528, 568, 528, 564,
    504, 1662, 558, 564, 528, 566, 528, 1668, 528, 562, 528, 1666, 532, 1664,
    582,
)
# fmt: on

SERVED = (
    [("technibel", m) for m in TECHNIBEL_AC_MODELS]
    + [("teco", m) for m in TECHNIBEL_AC_TECO_MODELS]
    + [("alaska", m) for m in TECHNIBEL_AC_ALASKA_MODELS]
)


def device(brand="technibel", model="generic"):
    return TechnibelAcDevice(brand, model)


def data(state, previous=None, brand="technibel"):
    dev = device(brand)
    if previous is not None:
        previous = dev.normalise(previous)
    (main,) = dev.frames(previous, dev.normalise(state), ())
    return main.data


def read(state, brand="technibel"):
    return TECHNIBEL_AC_LAYOUT.read(data(state, brand=brand))


def on(mode="cool", t=22.0, fan="2", swing="off", sleep=False, power=True, **kw):
    return HvacState(
        power, mode, t, fan=fan, swing_v=swing, features={"sleep": sleep, **kw}
    )


def record_device(record):
    return device(record["plugin"], record["model"])


# ------------------------------------------------------------------ oracle


@pytest.mark.parametrize("record", oracle_params("TECHNIBEL_AC"))
def test_matches_c_library(record):
    dev = record_device(record)
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    for record in load_oracle("TECHNIBEL_AC"):
        dev = record_device(record)
        (main,) = dev.frames(None, state_from_record(dev, record["state"]), ())
        values = TECHNIBEL_AC_LAYOUT.read(main.data)
        assert TECHNIBEL_AC_LAYOUT.build(**values) == bytearray(main.data)
        assert TECHNIBEL_AC_LAYOUT.checksum.check(main.data)


def test_every_oracle_message_is_one_word_with_a_valid_sum():
    for record in load_oracle("TECHNIBEL_AC"):
        (main,) = decode(TECHNIBEL_AC, record["pulses"], ["main"])
        assert main.data[0] == 0x18 and main.data[5] == 0x00  # Header, Footer
        assert TECHNIBEL_AC_LAYOUT.checksum.check(main.data)


def test_oracle_records_use_the_variant_of_their_legacy_class():
    classes = {r["class"]: r["plugin"] for r in load_oracle("TECHNIBEL_AC")}
    assert device(classes["Teco"]).variant == "teco"
    assert device(classes["Technibel"]).variant == "technibel"


# ------------------------------------------------------------ real captures


def test_real_capture_decodes_to_the_port_word():
    # RealExample: the capture ends on its last mark; the gap is appended.
    (main,) = decode(TECHNIBEL_AC, REAL_EXAMPLE + (100000,), ["main"])
    assert main.data == KNOWN_STATE
    values = TECHNIBEL_AC_LAYOUT.read(main.data)
    assert (values["mode"], values["power"], values["fan"], values["temp"]) == (
        "cool",
        1,
        "2",
        18,
    )
    assert (values["swing_v"], values["sleep"]) == ("swing", 0)


@pytest.mark.parametrize("brand", ["technibel", "teco"])
def test_port_reproduces_the_known_state(brand):
    assert data(on("cool", 18.0, fan="2", swing="swing"), brand=brand) == KNOWN_STATE


def test_port_reproduces_the_known_state_pulses():
    # SyntheticSelfDecode: sendTechnibelAc(0x1881221200004B), MSB first.
    expected = (
        [8836, 4380]
        + [
            p
            for bit in f"{0x1881221200004B:056b}"
            for p in (523, 1696 if bit == "1" else 564)
        ]
        + [523, 100000]
    )
    signal = device().encode(None, on("cool", 18.0, fan="2", swing="swing")).signal
    assert signal.carrier == 38000
    assert list(signal.pulses) == expected


def test_reset_state_is_the_skeleton():
    # stateReset: "Mode:Cool, Power:Off, fan:Low, temp:20, swing:Off,
    # sleep:Off", with its sum.
    skeleton = TECHNIBEL_AC_LAYOUT.skeleton
    assert skeleton == TECHNIBEL_AC_RESET_STATE.to_bytes(7, "big")
    assert TECHNIBEL_AC_LAYOUT.checksum.check(skeleton)
    values = TECHNIBEL_AC_LAYOUT.read(skeleton)
    assert (values["mode"], values["power"], values["fan"], values["temp"]) == (
        "cool",
        0,
        "1",
        20,
    )
    assert (values["swing_v"], values["sleep"]) == ("off", 0)


def test_checksum_is_the_negated_sum_of_bytes_1_to_4():
    # calcChecksum: ~sum + 1 over TimerHours, Temp, the fan and mode bytes;
    # the Header and Footer are left out.
    assert TECHNIBEL_AC_LAYOUT.checksum.compute(KNOWN_STATE) == 0x4B
    word = bytearray(KNOWN_STATE)
    word[0] = word[5] = 0xFF
    assert TECHNIBEL_AC_LAYOUT.checksum.check(word)


# ------------------------------------------------------------------- rules


@pytest.mark.parametrize("brand", ["technibel", "teco"])
@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan", "heat"])
def test_off_carries_mode_cool(brand, mode):
    # IRac::technibel: convertMode maps IRac's mode "off" to its default,
    # kTechnibelAcCool; the rest is sent as requested.
    values = read(on(mode, 25.0, fan="3", power=False), brand=brand)
    assert (values["mode"], values["power"]) == ("cool", 0)
    assert (values["temp"], values["fan"]) == (25, "3")


@pytest.mark.parametrize(
    "mode, raw", [("cool", 0b0001), ("dry", 0b0010), ("fan", 0b0100), ("heat", 0b1000)]
)
def test_every_mode_uses_its_documented_code(mode, raw):
    word = data(on(mode))
    assert TECHNIBEL_AC_LAYOUT.read_raw(word, "mode") == raw
    assert TECHNIBEL_AC_LAYOUT.read_raw(word, "power") == 1


def test_auto_is_sent_as_cool():
    # The teco entity's auto: convertMode's default, kTechnibelAcCool.
    assert data(on("auto"), brand="teco") == data(on("cool"), brand="teco")


@pytest.mark.parametrize("mode", ["cool", "fan", "heat"])
@pytest.mark.parametrize("fan, raw", [("1", 0b001), ("2", 0b010), ("3", 0b100)])
def test_every_fan_level_uses_its_documented_code(mode, fan, raw):
    word = data(on(mode, fan=fan))
    assert TECHNIBEL_AC_LAYOUT.read_raw(word, "fan") == raw


@pytest.mark.parametrize("mode", ["auto", "cool", "fan", "heat"])
def test_fan_auto_is_sent_as_low(mode):
    # The teco entity's fan auto: convertFan's default, kTechnibelAcFanLow.
    assert read(on(mode, fan="auto"), brand="teco")["fan"] == "1"


@pytest.mark.parametrize("brand", ["technibel", "teco"])
@pytest.mark.parametrize("fan", ["auto", "1", "2", "3"])
def test_dry_always_sends_fan_low(brand, fan):
    # IRTechnibelAc::setFan: dry mode forces kTechnibelAcFanLow.
    assert read(on("dry", fan=fan), brand=brand)["fan"] == "1"


@pytest.mark.parametrize("mode", ["cool", "dry", "fan", "heat"])
@pytest.mark.parametrize("t", range(16, 32))
def test_every_setpoint_is_sent_in_celsius(mode, t):
    values = read(on(mode, float(t)))
    assert (values["temp"], values["use_fah"]) == (t, 0)
    assert TECHNIBEL_AC_LAYOUT.read_raw(data(on(mode, float(t))), "temp") == t


def test_teco_setpoints_stop_at_30():
    # The teco entity's range; the word itself takes 16-31.
    assert read(on("cool", 31.0), brand="teco")["temp"] == 30


@pytest.mark.parametrize("power", [True, False])
def test_swing_sets_the_documented_bit(power):
    assert read(on(swing="swing", power=power))["swing_v"] == "swing"
    assert read(on(swing="off", power=power))["swing_v"] == "off"


@pytest.mark.parametrize("power", [True, False])
def test_sleep_sets_the_documented_bit(power):
    assert read(on(sleep=True, power=power))["sleep"] == 1
    assert read(on(sleep=False, power=power))["sleep"] == 0


def test_light_sends_nothing():
    # The teco entity offers light; TECHNIBEL_AC has no light field. (Legacy
    # parity: the Teco class drove TECHNIBEL_AC, though ir_Teco.h lists
    # its Alaska models under TECO, which has a light.)
    assert data(on(light=True), brand="teco") == data(on(light=False), brand="teco")


def test_unused_fields_stay_clear():
    values = read(on("heat", 31.0, fan="3", swing="swing", sleep=True))
    for name in (
        "fan_change",
        "temp_change",
        "timer_change",
        "use_fah",
        "timer_enable",
        "timer_hours",
    ):
        assert values[name] == 0, name


def test_previous_is_ignored():
    # A full-state word; IRac::handleToggles has no TECHNIBEL_AC case.
    dev = device()
    target = on("heat", 24.0, fan="3")
    for previous in (
        on("cool", 20.0, fan="1", swing="swing", sleep=True),
        on("heat", 24.0, fan="3", power=False),
        target,
    ):
        assert dev.encode(previous, target).signal == dev.encode(None, target).signal


def test_message_shape():
    pulses = device().encode(None, on()).signal.pulses
    assert pulses[:2] == (8836, 4380)
    assert pulses[-2:] == (523, 100000)
    assert len(pulses) == 2 + 2 * 56 + 2


# ------------------------------------------------------------------ variants


def test_variant_comes_from_the_brand():
    assert device("technibel", "generic").variant == "technibel"
    assert device("teco", "generic").variant == "teco"
    assert device("alaska", "SAC9010QC").variant == "teco"
    assert TechnibelAcDevice("teco", "generic", "technibel").variant == "technibel"


@pytest.mark.parametrize("variant", sorted(TECHNIBEL_AC_CAPABILITIES))
def test_variant_picks_the_capabilities(variant):
    dev = TechnibelAcDevice("technibel", "generic", variant)
    assert dev.capabilities == TECHNIBEL_AC_CAPABILITIES[variant]


def test_unknown_variant_is_rejected():
    with pytest.raises(ValueError, match="variant"):
        TechnibelAcDevice("technibel", "generic", "nope")


# ------------------------------------------------------------ registration


@pytest.mark.parametrize("brand, model", SERVED)
def test_registry_serves_the_port(brand, model):
    assert isinstance(registry.get_device(brand, model), TechnibelAcDevice)


def _legacy_class(brand):
    from pyhvac.plugins.teco import Teco
    from pyhvac.plugins.technibel import Technibel

    return Technibel if brand == "technibel" else Teco


@pytest.mark.parametrize("brand, model", SERVED)
def test_capabilities_match_the_legacy_entity(brand, model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice

    legacy = LegacyDevice(brand, model, _legacy_class(brand))
    assert device(brand, model).capabilities == legacy.capabilities


# -------------------------------------------------------------- the C path


def _c_word(pulses):
    (main,) = decode(TECHNIBEL_AC, list(pulses), ["main"])
    return main.data


@pytest.mark.parametrize("brand", ["technibel", "teco"])
def test_matches_the_c_path_beyond_the_oracle_grid(brand):
    # The oracle has no off message and only 16/23/30-31 C: check off in
    # every mode, every setpoint, every fan (dry included) and light
    # against the C path. Swing and sleep stay off (DEFECTS).
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice

    legacy = LegacyDevice(brand, "generic", _legacy_class(brand))
    dev = device(brand)
    caps = dev.capabilities
    for power in (True, False):
        for mode in caps.modes:
            for t in range(16, 32):
                for fan in caps.fan.values:
                    features = {"light": True} if "light" in caps.features else {}
                    target = HvacState(
                        power, mode, float(t), fan=fan, features=features
                    )
                    theirs = _c_word(legacy.encode(None, target).signal.pulses)
                    assert data(target, brand=brand) == theirs, target


def test_swing_and_sleep_match_c_with_the_glue_bypassed():
    # With swing and sleep set on IRac directly (the glue drops them), C
    # sets the Swing and Sleep bits exactly as the port does.
    irhvac = pytest.importorskip("pyhvac.irhvac")
    from pyhvac.plugins.technibel import Technibel

    for swing in ("off", "swing"):
        for sleep in (False, True):
            legacy = Technibel()
            legacy.irac.next.swingv = (
                irhvac.swingv_t_kAuto if swing == "swing" else irhvac.swingv_t_kOff
            )
            legacy.irac.next.sleep = 0 if sleep else -1
            legacy.to_set = {"mode": "heat", "temperature": 24, "fan": "high"}
            pulses = [int(x) for x in legacy.to_lirc(legacy.build_ircode())]
            if len(pulses) % 2:
                pulses.append(100000)
            target = on("heat", 24.0, fan="3", swing=swing, sleep=sleep)
            assert _c_word(pulses) == data(target)


# ------------------------------------------------------ declared deviations


def test_undeclared_swing_deviation_is_reported():
    record = next(
        r for r in load_oracle("TECHNIBEL_AC") if r["state"].get("swing") == "on"
    )
    dev = record_device(record)
    defects = [d for d in DEFECTS if d.field != "swing_v"]
    with pytest.raises(AssertionError, match="swing_v"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects)


@pytest.mark.parametrize("cls", ["Teco", "Technibel"])
def test_undeclared_sleep_deviation_is_reported(cls):
    record = next(
        r
        for r in load_oracle("TECHNIBEL_AC")
        if r["class"] == cls and r["state"].get("sleep") == "on"
    )
    dev = record_device(record)
    defects = [d for d in DEFECTS if d.field != "sleep"]
    with pytest.raises(AssertionError, match="sleep"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects)


def test_records_without_swing_or_sleep_need_no_defect():
    for record in load_oracle("TECHNIBEL_AC"):
        state = record["state"]
        if state.get("swing") != "on" and state.get("sleep") != "on":
            dev = record_device(record)
            assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    record = load_oracle("TECHNIBEL_AC")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(record_device(record), record, (), DEFECTS)
