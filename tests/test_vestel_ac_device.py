import pytest

from oracle import load_oracle
from port_oracle import (
    Defect,
    assert_matches_oracle,
    c_sequence,
    oracle_params,
    state_from_record,
)
from pyhvac import registry
from pyhvac.plugins.vestel import (
    VESTEL_AC,
    VESTEL_AC_LAYOUT,
    VESTEL_AC_MODELS,
    VestelAcDevice,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Vestel values here:
# - the legacy glue (IRGHVAC.trans_swing) has no "on", so IRac's swingv stays
#   kOff and IRac::vestel's setSwing(false) writes 0xF (stop), not
#   kVestelAcSwing (0xA);
# - the legacy glue (IRGHVAC.build_ircode) has no "sleep" key, so IRac gets
#   sleep -1 and setSleep(sleep >= 0) writes kVestelAcNormal;
# - powerful reaches C as turbo, but IRac::vestel calls setSleep(sleep >= 0)
#   after setTurbo(turbo); the two share TurboSleep, so with sleep off
#   kVestelAcNormal overwrites kVestelAcTurbo: C never sends turbo;
# - IRVestelAc::setTemp clamps to kVestelAcMinTempC (18) in every mode; the
#   Temp field counts from kVestelAcMinTempH (16) and the real heat capture
#   (RealNormalExample) carries 16C, so the port sends 16 and 17 in heat.
SWING = Defect("swing", "swing", "off", "legacy glue has no swing 'on'")
SLEEP = Defect("turbo_sleep", "sleep", "normal", "legacy glue never passes sleep")
TURBO = Defect("turbo_sleep", "turbo", "normal", "IRac setSleep(false) after turbo")
HEAT_16 = Defect("temperature", 16, 18, "setTemp clamps to kVestelAcMinTempC")
HEAT_17 = Defect("temperature", 17, 18, "setTemp clamps to kVestelAcMinTempC")
DEFECTS = (SWING, SLEEP, TURBO, HEAT_16, HEAT_17)

# A record without "fan" leaves IRac's fanspeed at its default, kAuto
# (kVestelAcFanAuto): the port's fan auto, so no declaration is needed.

# ir_Vestel_test.cpp, as 7 logical bytes (the uint64 sent LSB first).
DEFAULT_STATE = (0x0F00D9001FEF201).to_bytes(7, "little")  # kVestelAcStateDefault
REAL_NORMAL = (0xF4410001FF1201).to_bytes(7, "little")  # RealNormalExample

MODES = ("auto", "cool", "dry", "fan", "heat")


def device(model="generic"):
    return VestelAcDevice("vestel", model)


def state(power=True, mode="cool", temperature=22.0, **kw):
    return device().normalise(HvacState(power, mode, temperature, **kw))


def frame(target, previous=None):
    (main,) = device().frames(previous, target, ())
    return main.data


def read(target):
    return VESTEL_AC_LAYOUT.read(frame(target))


@pytest.mark.parametrize("record", oracle_params("VESTEL_AC"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("VESTEL_AC"):
        data = frame(state_from_record(dev, record["state"]))
        values = VESTEL_AC_LAYOUT.read(data)
        assert VESTEL_AC_LAYOUT.build(**values) == bytearray(data)


# States the oracle grid lacks: off, setpoints below 18C and at 17-19C in
# every mode, and the feature combinations.
EXTRA_STATES = (
    [{"mode": "off", "temperature": t, "fan": "medium"} for t in (16, 17, 19, 30)]
    + [
        {"mode": m, "temperature": t, "fan": "medium", "swing": "off"}
        for m in MODES
        for t in (16, 17, 18, 19)
    ]
    + [
        {
            "mode": mode,
            "temperature": 22,
            "fan": "high",
            "swing": "on",
            "sleep": sleep,
            "powerful": powerful,
            "purifier": purifier,
        }
        for mode in ("cool", "off")
        for sleep in ("off", "on")
        for powerful in ("off", "on")
        for purifier in ("off", "on")
    ]
)


def test_states_beyond_the_oracle_grid_match_the_c_path():
    dev = device()
    record = load_oracle("VESTEL_AC")[0]
    for rec in c_sequence(record, EXTRA_STATES):
        assert_matches_oracle(dev, rec, dev.LAYOUTS, DEFECTS)


def test_checksum_holds_on_the_real_captures():
    checksum = VESTEL_AC_LAYOUT.checksum
    assert checksum.check(DEFAULT_STATE)
    assert checksum.check(REAL_NORMAL)
    # RealTimerExample, a time message (UseCmd clear), shares the rule.
    assert checksum.check((0x2D6570B8EE201).to_bytes(7, "little"))
    broken = bytearray(REAL_NORMAL)
    broken[5] ^= 0x01
    assert not checksum.check(broken)


def test_checksum_writes_only_bits_12_to_19():
    assert VESTEL_AC_LAYOUT.checksum.bits() == set(range(12, 20))
    data = bytearray(REAL_NORMAL)
    data[1] &= 0x0F
    data[2] &= 0xF0
    VESTEL_AC_LAYOUT.checksum.apply(data)
    assert bytes(data) == REAL_NORMAL


@pytest.mark.parametrize(
    "data, fields",
    [
        # kVestelAcStateDefault: power on, auto, 25C, fan auto heat.
        (
            DEFAULT_STATE,
            {
                "power": True,
                "mode": "auto",
                "temperature": 25,
                "fan": "auto heat",
                "swing": "off",
                "turbo_sleep": "normal",
                "ion": 0,
                "use_cmd": 1,
                "pad4": 1,
            },
        ),
        # RealNormalExample: power on, heat, 16C, fan auto, ion on.
        (
            REAL_NORMAL,
            {
                "power": True,
                "mode": "heat",
                "temperature": 16,
                "fan": "auto",
                "swing": "off",
                "turbo_sleep": "normal",
                "ion": 1,
                "use_cmd": 1,
                "pad4": 1,
            },
        ),
    ],
)
def test_layout_reads_the_real_captures(data, fields):
    values = VESTEL_AC_LAYOUT.read(data)
    assert {k: values[k] for k in fields} == fields
    assert VESTEL_AC_LAYOUT.build(**values) == bytearray(data)


def test_port_reproduces_the_real_heat_capture():
    # RealNormalExample: heat, 16C, ion on, fan auto (kVestelAcFanAuto).
    target = state(True, "heat", 16.0, fan="auto", features={"purifier": True})
    assert frame(target) == REAL_NORMAL


def test_fan_offers_auto_and_the_three_speeds():
    # kVestelAcFanAuto/Low/Med/High (the legacy entity had no auto).
    fan = device().capabilities.fan
    assert fan.values == ("auto", "1", "2", "3")
    assert [fan.label(v) for v in fan.values] == ["auto", "low", "medium", "high"]


def test_fan_auto_uses_its_documented_code():
    # kVestelAcFanAuto = 1.
    assert VESTEL_AC_LAYOUT.read_raw(frame(state(fan="auto")), "fan") == 1


def test_fanless_records_are_fan_auto():
    # IRac's default fanspeed kAuto is the port's fan auto.
    dev = device()
    for record in load_oracle("VESTEL_AC"):
        if "fan" not in record["state"]:
            assert state_from_record(dev, record["state"]).fan == "auto"
            assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan"])
@pytest.mark.parametrize("t, kept", [(16.0, 18.0), (17.0, 18.0), (18.0, 18.0)])
def test_normalise_clamps_to_18_outside_heat(mode, t, kept):
    # kVestelAcMinTempC outside heat; capabilities give the union 16-30.
    assert state(True, mode, t).temperature == kept
    assert state(True, "heat", t).temperature == t
    rng = device().capabilities.temperature
    assert (rng.min, rng.max) == (16.0, 30.0)


@pytest.mark.parametrize("mode", MODES)
def test_mode_uses_its_documented_value(mode):
    codes = {"auto": 0, "cool": 1, "dry": 2, "fan": 3, "heat": 4}
    assert VESTEL_AC_LAYOUT.read_raw(frame(state(True, mode)), "mode") == codes[mode]


@pytest.mark.parametrize("fan, raw", [("1", 5), ("2", 9), ("3", 0xB)])
def test_every_fan_level_uses_its_documented_code(fan, raw):
    # kVestelAcFanLow / Med / High, as convertFan maps kLow/kMedium/kHigh.
    assert VESTEL_AC_LAYOUT.read_raw(frame(state(fan=fan)), "fan") == raw


@pytest.mark.parametrize("swing, raw", [("off", 0xF), ("swing", 0xA)])
def test_swing_uses_its_documented_code(swing, raw):
    assert VESTEL_AC_LAYOUT.read_raw(frame(state(swing_v=swing)), "swing") == raw


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan"])
@pytest.mark.parametrize("t, sent", [(16, 18), (17, 18), (18, 18), (19, 19), (30, 30)])
def test_setpoint_is_clamped_to_18_outside_heat(mode, t, sent):
    # IRVestelAc::setTemp's kVestelAcMinTempC clamp.
    assert read(state(True, mode, float(t)))["temperature"] == sent


@pytest.mark.parametrize("t", [16, 17, 18, 23, 30])
def test_heat_sends_setpoints_down_to_16(t):
    # kVestelAcMinTempH, as the real heat capture carries (HEAT_16/HEAT_17).
    assert read(state(True, "heat", float(t)))["temperature"] == t


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("t", [16.0, 22.0, 30.0])
def test_off_carries_mode_auto_and_its_clamp(mode, t):
    # IRac's kOff mode falls to convertMode's default, kVestelAcAuto, so the
    # target mode never reaches an off message (the C-only test above checks
    # off against C).
    off = state(False, mode, t, fan="3")
    assert frame(off) == frame(state(False, "auto", t, fan="3"))
    values = read(off)
    assert (values["power"], values["mode"]) == (False, "auto")
    assert values["temperature"] == max(int(t), 18)
    assert values["fan"] == "3"


def test_power_sets_both_power_bits_and_use_cmd():
    on, off = frame(state(True)), frame(state(False))
    assert VESTEL_AC_LAYOUT.read_raw(on, "power") == 0b11
    assert VESTEL_AC_LAYOUT.read_raw(off, "power") == 0b00
    for data in (on, off):
        assert VESTEL_AC_LAYOUT.read_raw(data, "use_cmd") == 1


@pytest.mark.parametrize(
    "sleep, powerful, expected",
    [
        (False, False, "normal"),
        (True, False, "sleep"),
        (False, True, "turbo"),
        # setSleep comes after setTurbo in IRac::vestel: sleep wins.
        (True, True, "sleep"),
    ],
)
def test_sleep_and_powerful_share_turbo_sleep(sleep, powerful, expected):
    target = state(features={"sleep": sleep, "powerful": powerful})
    assert read(target)["turbo_sleep"] == expected


def test_purifier_sets_ion():
    assert read(state(features={"purifier": True}))["ion"] == 1
    assert read(state(features={"purifier": False}))["ion"] == 0


def test_padding_keeps_the_default_state_bits():
    for target in (state(True), state(False, "heat", 16.0, fan="3")):
        values = read(target)
        assert (values["pad1"], values["pad2"], values["pad3"]) == (0, 0, 0)
        assert values["pad4"] == 1


def test_previous_is_ignored():
    # No toggles: IRac::handleToggles has no VESTEL_AC rule.
    target = state(True, "cool", 22.0)
    for previous in (None, state(False, "heat", 30.0), target):
        assert frame(target, previous) == frame(target)


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (3110, 9066)
    assert pulses[-2:] == (520, 100000)
    assert len(pulses) == 2 + 2 * 56 + 2


@pytest.mark.parametrize("model", VESTEL_AC_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("vestel", model), VestelAcDevice)


def _record(**match):
    return next(
        r
        for r in load_oracle("VESTEL_AC")
        if all(r["state"].get(k) == v for k, v in match.items())
    )


@pytest.mark.parametrize(
    "defect, match",
    [
        (SWING, {"swing": "on"}),
        (SLEEP, {"sleep": "on"}),
        (TURBO, {"powerful": "on"}),
        (HEAT_16, {"mode": "heat", "temperature": 16}),
    ],
)
def test_undeclared_deviation_is_reported(defect, match):
    dev = device()
    record = _record(**match)
    defects = [d for d in DEFECTS if d != defect]
    with pytest.raises(AssertionError, match=defect.field):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects)


def test_undeclared_heat_17_deviation_is_reported():
    dev = device()
    record = load_oracle("VESTEL_AC")[0]
    old = {"mode": "heat", "temperature": 17, "fan": "medium", "swing": "off"}
    (rec,) = c_sequence(record, [old])
    defects = [d for d in DEFECTS if d != HEAT_17]
    with pytest.raises(AssertionError, match="temperature"):
        assert_matches_oracle(dev, rec, dev.LAYOUTS, defects)


def test_layouts_must_cover_every_frame():
    dev = device()
    record = _record(mode="heat", swing="on")
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)


# No real capture in ir_Vestel_test.cpp needs it, but
# decodeVestelAc matches with kVestelAcTolerance (30 %) and kMarkExcess.
def test_decode_tolerance_is_the_c_decoders():
    assert (VESTEL_AC.tolerance, VESTEL_AC.mark_excess) == (0.30, 50)
