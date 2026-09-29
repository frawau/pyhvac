import pytest

from oracle import load_oracle
from port_oracle import (
    Defect,
    assert_matches_oracle,
    assert_sequence_matches_c,
    c_sequence,
    oracle_params,
    sequence_params,
    state_from_record,
)
from pyhvac.fields import Sum8
from pyhvac.ir.codec import DecodeError, decode, encode
from pyhvac.ir.model import Frame
from pyhvac.protocols.tcl import (
    TCL112AC,
    TCL112AC_DAEWOO_MODELS,
    TCL112AC_LAYOUT,
    TCL112AC_LEBERG_MODELS,
    TCL112AC_MODELS,
    TCL112AC_QUIET_LAYOUT,
    TCL112AC_TECHNOPOINT_MODELS,
    Tcl112AcDevice,
)
from pyhvac.state import HvacState

# The C path deviates from the documented TCL112AC values here:
# - swing "90°"/"60°": the legacy glue (IRGHVAC.trans_swing) maps them to
#   kHigh and kUpperMiddle; IRTcl112Ac::convertSwingV turns kHigh into
#   kTcl112AcSwingVHigh (so kTcl112AcSwingVHighest is never sent) and has no
#   kUpperMiddle case (its default is kTcl112AcSwingVOn, swing);
# - the legacy glue (IRGHVAC.trans_hswing) has no "on", so IRac's swingh
#   stays kOff and setSwingHorizontal(false) clears SwingH;
# - GZ055BE1 with quiet: IRTcl112Ac::send, after the special message,
#   restores the state and then sets isTcl whenever MsgType is
#   kTcl112AcNormal, whatever the model; the port keeps isTcl as
#   setModel(GZ055BE1) writes it (clear).
SWING_1 = Defect("swing_v", "1", "2", "90° reaches C as kHigh")
SWING_2 = Defect("swing_v", "2", "auto", "60° reaches C as kUpperMiddle")
SWING_H = Defect("swing_h", "swing", "off", "legacy glue has no swing 'on'")
IS_TCL = Defect("model", "GZ055BE1", "TAC09CHSD", "IRTcl112Ac::send sets isTcl")
DEFECTS = (SWING_1, SWING_2, SWING_H, IS_TCL)

LEGACY_CLASS = {"TAC09CHSD": "Tclv1", "GZ055BE1": "Tclv2"}
PLUGIN_MODELS = {
    "tcl": TCL112AC_MODELS,
    "daewoo": TCL112AC_DAEWOO_MODELS,
    "technopoint": TCL112AC_TECHNOPOINT_MODELS,
    "leberg": TCL112AC_LEBERG_MODELS,
}
SERVED = [(p, m) for p, models in PLUGIN_MODELS.items() for m in models]
MODES = ("cool", "dry", "fan", "heat")
V1, V2 = "generic v1", "generic v2"

# IRTcl112Ac::send's quiet_off state (issue 1528): the special message with
# quiet off. C never sends it (see test_sequence_matches_a_persistent_c_object).
QUIET_OFF = bytes([0x23, 0xCB, 0x26, 0x02, 0x00, 0x40, 0x00])
QUIET_OFF += bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x65])

# Real captures from ir_Tcl_test.cpp.
# TestDecodeTcl112Ac.DecodeRealExample (issue 619): TAC09CHSD, on, cool,
# 24 C, fan auto, swing off, light on.
REAL_619 = bytes([0x23, 0xCB, 0x26, 0x01, 0x00, 0x24, 0x03])
REAL_619 += bytes([0x07, 0x40, 0x00, 0x00, 0x00, 0x80, 0x03])
RAW_619 = (
    "3030 1658 494 1066 494 1068 498 320 494 326 498 320 494 1068 500 320 "
    "494 332 494 1068 500 1062 496 324 492 1044 524 322 492 326 498 1062 "
    "494 1074 494 326 500 1062 496 1066 490 328 496 322 492 1070 498 322 "
    "494 332 492 1068 498 320 494 326 498 320 496 324 500 320 494 324 490 "
    "336 500 320 496 324 490 328 496 322 492 328 498 322 492 326 498 328 "
    "496 322 492 328 498 1064 494 326 498 320 494 1066 490 330 496 330 494 "
    "1066 490 1070 498 322 492 328 498 322 492 326 498 322 492 332 492 1068 "
    "498 1062 494 1066 500 318 496 324 490 328 496 324 492 334 490 328 496 "
    "324 492 328 496 322 492 328 498 320 494 1068 500 326 500 320 492 326 "
    "500 320 496 324 500 318 496 324 490 328 496 330 496 324 490 328 496 "
    "324 490 328 498 322 492 328 498 320 492 334 492 328 498 322 494 326 "
    "498 320 494 324 500 322 492 324 490 336 498 320 494 324 500 320 496 "
    "324 490 328 498 322 492 328 496 1070 496 1064 492 1070 498 322 494 326 "
    "500 320 494 324 500 320 494 324 470"
)
# TestDecodeTcl112Ac.Issue1528: the special message, quiet on.
REAL_1528 = bytes([0x23, 0xCB, 0x26, 0x02, 0x00, 0x60, 0x00])
REAL_1528 += bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x85])
# TestDecodeTcl112Ac.Issue744: TAC09CHSD, on, cool, 23 C, fan auto, swing
# off, light on, TimerIndicator clear.
REAL_744 = bytes([0x23, 0xCB, 0x26, 0x01, 0x00, 0x24, 0x03])
REAL_744 += bytes([0x08, 0x00, 0x00, 0x00, 0x00, 0x80, 0xC4])
# TestTcl112AcClass.isTcl, "teknopoint" (a GZ055BE1 recapture): on, cool,
# 16 C, fan auto, swing on, light on, TimerIndicator clear.
REAL_TEKNOPOINT = bytes([0x23, 0xCB, 0x26, 0x01, 0x00, 0x24, 0x03])
REAL_TEKNOPOINT += bytes([0x0F, 0x38, 0x00, 0x00, 0x00, 0x00, 0x83])
# TestTcl112AcClass.Temperature's states (library test states, not
# captures: TAC09CHSD, on, cool, fan auto, swing off, light on,
# TimerIndicator clear): 16.5 C and 19.5 C (HalfDegree set), and its
# "automode" state (mode kTcl112AcAuto, 24 C), whose Sum byte (0x48) is not
# the sum of its bytes (0xC8): setRaw and toString do not check it.
TEMP_16_5 = bytes([0x23, 0xCB, 0x26, 0x01, 0x00, 0x24, 0x03])
TEMP_16_5 += bytes([0x0F, 0x00, 0x00, 0x00, 0x00, 0xA0, 0xEB])
TEMP_19_5 = bytes([0x23, 0xCB, 0x26, 0x01, 0x00, 0x24, 0x03])
TEMP_19_5 += bytes([0x0C, 0x00, 0x00, 0x00, 0x00, 0xA0, 0xE8])
AUTO_MODE = bytes([0x23, 0xCB, 0x26, 0x01, 0x00, 0x24, 0x08])
AUTO_MODE += bytes([0x07, 0x00, 0x00, 0x00, 0x00, 0x80, 0x48])


def device(model=V1, plugin="tcl"):
    return Tcl112AcDevice(plugin, model)


def device_for(record):
    return device(record["model"], record["plugin"])


def layouts(frames):
    """One layout per frame: the special (quiet) message comes first."""
    return (TCL112AC_QUIET_LAYOUT,) * (len(frames) - 1) + (TCL112AC_LAYOUT,)


def check(dev, record, defects=DEFECTS, previous=None):
    assert_matches_oracle(dev, record, layouts, defects, previous=previous)


def state(power=True, mode="cool", temperature=24.0, model=V1, **kw):
    return device(model).normalise(HvacState(power, mode, temperature, **kw))


def frames(target, previous=None, model=V1):
    return device(model).frames(previous, target, ())


def read(target, model=V1):
    return TCL112AC_LAYOUT.read(frames(target, model=model)[-1].data)


def wire(raw):
    # The captures end on the footer mark; the gap is kTcl112AcGap.
    return [int(x) for x in raw.split()] + [100000]


@pytest.mark.parametrize("record", oracle_params("TCL112AC"))
def test_matches_c_library(record):
    check(device_for(record), record)


def test_oracle_covers_both_variants():
    variants = {device_for(r).variant for r in load_oracle("TCL112AC")}
    assert variants == {"TAC09CHSD", "GZ055BE1"}


def test_layout_round_trips_every_oracle_state():
    for record in load_oracle("TCL112AC"):
        dev = device_for(record)
        ours = dev.frames(None, state_from_record(dev, record["state"]), ())
        for frame, layout in zip(ours, layouts(ours)):
            values = layout.read(frame.data)
            assert layout.build(**values) == bytearray(frame.data)


# States the oracle grid lacks: off and low/high setpoints in every mode,
# every fan level and swing position in every mode, and the feature
# combinations, on and off.
EXTRA_STATES = (
    [
        {"mode": m, "temperature": t, "fan": "medium"}
        for m in MODES + ("off",)
        for t in (16, 17, 30, 31)
    ]
    + [
        {"mode": m, "temperature": 22, "fan": f, "swing": s}
        for m in MODES
        for f in ("auto", "lowest", "low", "medium", "high")
        for s in ("off", "auto", "90°", "60°", "45°", "30°", "0°")
    ]
    + [
        {
            "mode": m,
            "temperature": 24,
            "fan": "low",
            "swing": "45°",
            "hswing": "on",
            "quiet": q,
            "purifier": "on",
            "light": li,
            "powerful": pw,
            "economy": ec,
        }
        for m in ("heat", "off")
        for q in ("off", "on")
        for li in ("off", "on")
        for pw in ("off", "on")
        for ec in ("off", "on")
    ]
)


@pytest.mark.parametrize("model", ["DSB-F0934ELH-V", "LBS-TOR07"])
def test_states_beyond_the_oracle_grid_match_the_c_path(model):
    record = next(r for r in load_oracle("TCL112AC") if r["model"] == model)
    dev = device_for(record)
    for rec in c_sequence(record, EXTRA_STATES):
        # A fresh IRTcl112Ac every message (IRac::sendAc), so each C message
        # is the port's with previous=None.
        check(dev, rec)


def quiet_change_rule(dev):
    """``adapt`` for the sequence test: the C record the port sends with
    ``previous``. IRac builds a fresh IRTcl112Ac per message, so C sends the
    special message whenever quiet is on and never sends quiet off; the port
    sends it when quiet changes (IRTcl112Ac::send's own rule), so the C
    frames get IRTcl112Ac::send's quiet_off state in front on an on -> off
    change, and lose the special message when quiet stays on."""
    last = []

    def adapt(rec):
        now = state_from_record(dev, rec["state"])
        before = last[-1] if last else None
        last.append(now)
        quiet = now.features["quiet"]
        names = ["quiet", "main"] if quiet else ["main"]
        theirs = decode(TCL112AC, rec["pulses"], expected=names)
        if before is None or before.features["quiet"] == quiet:
            if not (before is not None and quiet):
                return rec
            theirs = theirs[1:]  # quiet stays on: no special message
        elif not quiet:
            theirs = [Frame("quiet", QUIET_OFF)] + theirs  # on -> off
        return {**rec, "pulses": list(encode(TCL112AC, theirs).pulses)}

    return adapt


QUIET_STATES = [
    {"mode": m, "temperature": 23, "fan": "low", "swing": "off", "quiet": q}
    for m, q in (
        ("cool", "off"),
        ("cool", "on"),
        ("cool", "on"),
        ("heat", "on"),
        ("off", "on"),
        ("off", "off"),
        ("dry", "on"),
        ("dry", "off"),
        ("dry", "off"),
    )
]


@pytest.mark.parametrize(
    "record, states",
    sequence_params("TCL112AC")
    + [
        pytest.param(r, QUIET_STATES, id=f"quiet-{r['class']}")
        for r in {r["class"]: r for r in load_oracle("TCL112AC")}.values()
    ],
)
def test_sequence_matches_a_persistent_c_object(record, states):
    # Only the special (quiet) message depends on the message before; the
    # port deliberately sends it on a change of quiet (see quiet_change_rule).
    dev = device_for(record)
    assert_sequence_matches_c(
        dev,
        record,
        states,
        layouts,
        DEFECTS,
        adapt=quiet_change_rule(dev),
    )


def test_sequence_needs_the_quiet_change_rule():
    # Without the adaptation, C's second quiet-on message (quiet stays on)
    # has a special message the port does not send.
    record = next(r for r in load_oracle("TCL112AC") if r["class"] == "Tclv1")
    dev = device_for(record)
    with pytest.raises(DecodeError, match="expected end of signal"):
        assert_sequence_matches_c(dev, record, QUIET_STATES[:3], layouts, DEFECTS)


def test_checksums():
    # Normal message: IRTcl112Ac::calcChecksum, sum of bytes 0-12.
    assert TCL112AC_LAYOUT.checksum == Sum8(0, 13, 13)
    for data in (REAL_619, REAL_744, REAL_TEKNOPOINT):
        assert TCL112AC_LAYOUT.checksum.check(data)
    # Special message (byte 3 is 0x02): the sum plus 0xF.
    for data in (REAL_1528, QUIET_OFF):
        assert TCL112AC_QUIET_LAYOUT.checksum.check(data)
        assert not Sum8(0, 13, 13).check(data)
    broken = bytearray(REAL_1528)
    broken[5] ^= 0x20
    assert not TCL112AC_QUIET_LAYOUT.checksum.check(broken)
    TCL112AC_QUIET_LAYOUT.checksum.apply(broken)
    assert bytes(broken) == QUIET_OFF


def test_real_capture_decodes():
    # The port's timings decode the real issue 619 capture.
    (main,) = decode(TCL112AC, wire(RAW_619), expected=["main"])
    assert main.data == REAL_619


def test_port_reproduces_the_real_619_capture():
    target = state(True, "cool", 24.0, features={"light": True})
    (main,) = frames(target)
    assert main.data == REAL_619


def test_port_reproduces_the_real_quiet_capture():
    quiet, main = frames(state(features={"quiet": True}))
    assert quiet.section == "quiet" and quiet.data == REAL_1528
    assert TCL112AC_QUIET_LAYOUT.read(quiet.data)["msg_type"] == "special"


@pytest.mark.parametrize(
    "target, model, capture",
    [
        (dict(temperature=23.0), V1, REAL_744),
        (dict(temperature=16.0, swing_v="auto"), V2, REAL_TEKNOPOINT),
        (dict(temperature=16.5), V1, TEMP_16_5),
        (dict(temperature=19.5), V1, TEMP_19_5),
    ],
)
def test_port_reproduces_real_captures_but_timer_indicator(target, model, capture):
    # These states have TimerIndicator clear; IRac never calls the timer
    # setters, so it keeps stateReset's 1 (as the oracle records carry). The
    # half-degree states (new setpoints) are the library's own test states.
    target = state(model=model, features={"light": True}, **target)
    ours = bytearray(frames(target, model=model)[-1].data)
    assert TCL112AC_LAYOUT.read(ours)["timer_indicator"] == 1
    TCL112AC_LAYOUT.write_raw(ours, "timer_indicator", 0)
    TCL112AC_LAYOUT.checksum.apply(ours)
    assert bytes(ours) == capture


@pytest.mark.parametrize(
    "plugin, model", SERVED + [("tcl", "whatever")], ids=lambda x: str(x)
)
def test_variant_comes_from_the_model(plugin, model):
    variant = PLUGIN_MODELS.get(plugin, {}).get(model, "TAC09CHSD")
    dev = Tcl112AcDevice(plugin, model)
    assert dev.variant == variant
    target = dev.normalise(HvacState(True, "cool", 22.0))
    (main,) = dev.frames(None, target, ())
    assert main.data[12] >> 7 == (variant == "TAC09CHSD")


def test_bad_variant_raises():
    assert Tcl112AcDevice("tcl", "x", variant="GZ055BE1").variant == "GZ055BE1"
    with pytest.raises(ValueError):
        Tcl112AcDevice("tcl", "x", variant="TCL96AC")


@pytest.mark.parametrize(
    "mode, raw", [("auto", 8), ("cool", 3), ("dry", 2), ("fan", 7), ("heat", 1)]
)
def test_mode_uses_its_documented_value(mode, raw):
    # kTcl112Ac{Auto,Cool,Dry,Fan,Heat}; auto is new (the legacy entity had
    # none).
    assert TCL112AC_LAYOUT.read_raw(frames(state(True, mode))[-1].data, "mode") == raw


@pytest.mark.parametrize("model", [V1, V2])
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("t", [16.0, 23.0, 31.0])
def test_off_carries_mode_auto_in_every_mode(model, mode, t):
    # IRac passes mode "off"; convertMode maps it to kTcl112AcAuto.
    values = read(state(False, mode, t, model=model, fan="3"), model=model)
    assert (values["power"], values["mode"]) == (0, "auto")
    assert (values["temperature"], values["fan"]) == (int(t), "3")


@pytest.mark.parametrize("t", range(16, 32))
def test_every_setpoint(t):
    data = frames(state(temperature=float(t)))[-1].data
    assert data[7] == 31 - t  # kTcl112AcTempMax - degrees
    assert TCL112AC_LAYOUT.read(data)["half_degree"] == 0


def test_setpoint_is_clamped_to_16_31():
    assert read(state(temperature=10.0))["temperature"] == 16
    assert read(state(temperature=40.0))["temperature"] == 31
    assert read(state(temperature=40.0))["half_degree"] == 0  # no 31.5


def test_capabilities_offer_auto_and_half_degrees():
    caps = device().capabilities
    assert caps.modes == ("auto", "cool", "dry", "fan", "heat")  # kTcl112AcAuto
    # kTcl112AcTempMin..kTcl112AcTempMax, HalfDegree: 0.5 steps.
    assert (caps.temperature.min, caps.temperature.max) == (16.0, 31.0)
    assert caps.temperature.decimals == (0, 5)
    assert caps.temperature.snap(20.3) == 20.5
    assert caps.temperature.snap(31.5) == 31.0


@pytest.mark.parametrize("model", [V1, V2])
@pytest.mark.parametrize("t", [16 + n / 2 for n in range(31)])
def test_every_half_degree_setpoint(model, t):
    # setTemp: Temp = kTcl112AcTempMax - whole degrees, HalfDegree the half.
    data = frames(state(temperature=t, model=model), model=model)[-1].data
    assert data[7] == 31 - int(t)
    assert TCL112AC_LAYOUT.read(data)["half_degree"] == (t % 1 == 0.5)


def test_port_reproduces_the_auto_mode_state_but_its_sum():
    target = state(True, "auto", 24.0, features={"light": True})
    ours = bytearray(frames(target)[-1].data)
    TCL112AC_LAYOUT.write_raw(ours, "timer_indicator", 0)
    TCL112AC_LAYOUT.checksum.apply(ours)
    assert bytes(ours[:13]) == AUTO_MODE[:13]
    assert ours[13] == sum(AUTO_MODE[:13]) & 0xFF == 0xC8


@pytest.mark.parametrize("model", [V1, V2])
@pytest.mark.parametrize("power", [True, False])
def test_auto_mode_is_sent(model, power):
    # kTcl112AcAuto: an off message is auto anyway (convertMode's default).
    values = read(state(power, "auto", 22.0, model=model, fan="2"), model=model)
    assert (values["mode"], values["power"]) == ("auto", int(power))
    assert (values["temperature"], values["fan"]) == (22, "2")


@pytest.mark.parametrize(
    "fan, raw", [("auto", 0), ("1", 1), ("2", 2), ("3", 3), ("4", 5)]
)
@pytest.mark.parametrize("mode", MODES)
def test_every_fan_level_uses_its_documented_code(mode, fan, raw):
    # kTcl112AcFan{Auto,Min,Low,Med,High}; setMode(fan)'s High is overwritten
    # by IRac's later setFan.
    data = frames(state(True, mode, fan=fan))[-1].data
    assert TCL112AC_LAYOUT.read_raw(data, "fan") == raw


@pytest.mark.parametrize(
    "swing, raw",
    [("off", 0), ("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 5), ("auto", 7)],
)
def test_every_swing_position_uses_its_documented_code(swing, raw):
    # "1" is the topmost documented position (kTcl112AcSwingVHighest).
    data = frames(state(swing_v=swing))[-1].data
    assert TCL112AC_LAYOUT.read_raw(data, "swing_v") == raw


@pytest.mark.parametrize("swing_h, raw", [("off", 0), ("swing", 1)])
def test_swing_h_sets_the_swing_h_bit(swing_h, raw):
    data = frames(state(swing_h=swing_h))[-1].data
    assert TCL112AC_LAYOUT.read_raw(data, "swing_h") == raw


@pytest.mark.parametrize("power", [True, False])
@pytest.mark.parametrize("fan", ["auto", "1", "3"])
@pytest.mark.parametrize("swing", ["off", "1", "5"])
def test_powerful_forces_fan_high_and_swing(power, fan, swing):
    # IRac::tcl112 calls setTurbo after setFan and setSwingVertical, and
    # setTurbo(true) writes kTcl112AcFanHigh and kTcl112AcSwingVOn.
    target = state(power, "heat", fan=fan, swing_v=swing, features={"powerful": True})
    values = read(target)
    assert (values["turbo"], values["fan"], values["swing_v"]) == (1, "4", "auto")
    values = read(state(power, "heat", fan=fan, swing_v=swing))
    assert (values["turbo"], values["fan"], values["swing_v"]) == (0, fan, swing)


@pytest.mark.parametrize(
    "feature, field, on, off",
    [
        ("light", "light", 0, 1),  # setLight: the bit is cleared when on
        ("purifier", "health", 1, 0),
        ("economy", "econo", 1, 0),
    ],
)
def test_feature_bits(feature, field, on, off):
    data = frames(state(features={feature: True}))[-1].data
    assert TCL112AC_LAYOUT.read_raw(data, field) == on
    data = frames(state(features={feature: False}))[-1].data
    assert TCL112AC_LAYOUT.read_raw(data, field) == off


def test_normal_message_keeps_the_reset_bits():
    # stateReset's Quiet (byte 5 bit 5) and TimerIndicator stay set; the
    # timers stay off; quiet never reaches the normal message.
    for quiet in (False, True):
        values = read(state(False, "fan", features={"quiet": quiet}))
        assert values["msg_type"] == "normal"
        assert (values["quiet"], values["timer_indicator"]) == (1, 1)
        assert values["on_timer_enabled"] == values["off_timer_enabled"] == 0
        assert values["on_timer"] == values["off_timer"] == 0


@pytest.mark.parametrize("model", [V1, V2])
@pytest.mark.parametrize("power", [True, False])
def test_quiet_sends_the_special_message_first(model, power):
    # A fresh IRTcl112Ac (previous=None): quiet on is sent, quiet off is not.
    target = state(power, "dry", model=model, features={"quiet": True})
    quiet, main = frames(target, model=model)
    assert quiet.data == REAL_1528
    alone = state(power, "dry", model=model, features={"quiet": False})
    assert frames(alone, model=model) == [main]


@pytest.mark.parametrize(
    "before, after, sent",
    [
        (False, False, None),
        (False, True, REAL_1528),
        (True, True, None),
        (True, False, QUIET_OFF),
    ],
)
def test_with_previous_quiet_is_sent_only_on_a_change(before, after, sent):
    previous = state(True, "heat", 30.0, features={"quiet": before})
    target = state(features={"quiet": after})
    ours = frames(target, previous)
    fresh = frames(target)
    assert ours[-1] == fresh[-1]  # previous changes nothing else
    assert [f.data for f in ours[:-1]] == ([sent] if sent else [])


def test_message_shape():
    dev = device()
    command = dev.encode(None, HvacState(True, "cool", 22.0))
    pulses = command.signal.pulses
    assert pulses[:2] == (3000, 1650)
    assert pulses[-2:] == (500, 100000)
    assert len(pulses) == 2 + 2 * 112 + 2
    assert command.signal.carrier == 38000
    quiet = dev.encode(None, HvacState(True, "cool", 22.0, features={"quiet": True}))
    assert len(quiet.signal.pulses) == 2 * len(pulses)


def _record(cls, **match):
    return next(
        r
        for r in load_oracle("TCL112AC")
        if r["class"] == cls and all(r["state"].get(k) == v for k, v in match.items())
    )


@pytest.mark.parametrize(
    "defect, cls, match",
    [
        (SWING_1, "Tclv1", {"swing": "90°"}),
        (SWING_2, "Tclv1", {"swing": "60°"}),
        (SWING_H, "Tclv1", {"hswing": "on"}),
        (IS_TCL, "Tclv2", {"quiet": "on"}),
    ],
)
def test_undeclared_deviation_is_reported(defect, cls, match):
    record = _record(cls, **match)
    defects = [d for d in DEFECTS if d != defect]
    with pytest.raises(AssertionError, match=defect.field):
        check(device_for(record), record, defects)


def test_layouts_must_cover_every_frame():
    record = _record("Tclv1", quiet="on")
    dev = device_for(record)
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (TCL112AC_LAYOUT,), DEFECTS)
    # A layouts function gets the port's frames (here: special, then normal).
    seen = []
    assert_matches_oracle(dev, record, lambda f: seen.append(f) or layouts(f), DEFECTS)
    assert [f.section for f in seen[0]] == ["quiet", "main"]


# decodeMitsubishi112 (shared with TCL112AC) matches with _tolerance +
# kTcl112AcTolerance (30 %) and no mark excess; these real captures need it.
RAW_744 = (
    "3164 1532 584 1082 472 1068 580 244 602 264 542 328 530 1034 586 262 "
    "540 326 508 1064 582 1082 490 328 532 1032 586 262 544 352 478 1060 "
    "584 1082 486 328 502 1058 588 1084 472 344 530 250 600 1086 492 322 "
    "530 258 594 1082 494 318 510 344 530 248 600 262 544 326 504 296 578 "
    "252 598 260 550 318 506 344 530 250 600 258 546 318 508 342 532 254 "
    "596 236 606 266 524 1066 580 242 602 266 542 1054 574 246 604 262 550 "
    "1088 530 1034 588 262 542 328 504 296 582 238 606 262 546 322 508 342 "
    "530 250 602 260 544 1052 572 252 600 260 546 320 506 344 530 254 596 "
    "264 578 268 552 316 528 256 598 260 578 272 520 372 476 294 582 240 "
    "604 266 542 328 502 294 582 238 604 268 540 322 506 346 530 244 604 "
    "260 542 354 478 298 580 240 604 262 542 326 506 342 530 250 600 260 "
    "548 318 506 344 530 250 600 260 546 320 528 322 530 254 598 262 548 "
    "316 468 380 532 250 600 260 546 1092 500 300 578 246 602 1082 474 346 "
    "530 248 602 260 542 1054 570 1090 524"
)
RAW_1528 = (
    "3040 1632 500 1084 502 1084 500 318 474 344 474 344 472 1110 474 344 "
    "474 344 472 1110 474 1110 474 344 472 1112 474 344 472 346 470 1112 "
    "472 1112 472 346 470 1114 470 1114 470 348 468 348 468 1116 470 348 "
    "468 350 464 354 424 1158 426 392 424 394 424 394 424 392 424 392 424 "
    "394 424 392 424 392 424 394 424 392 424 392 424 394 424 392 460 358 "
    "460 358 458 358 458 358 460 358 460 358 460 1124 460 1124 460 358 460 "
    "358 458 358 458 360 482 334 484 334 484 334 484 334 484 334 484 334 "
    "484 334 486 332 484 334 484 332 484 334 484 332 484 334 484 332 484 "
    "332 484 332 486 332 484 332 484 334 484 334 484 332 484 334 484 334 "
    "484 332 484 332 486 332 484 334 484 334 484 334 484 334 484 334 484 "
    "334 484 334 484 334 482 334 482 334 482 336 482 336 482 336 482 336 "
    "482 336 482 336 482 336 482 336 480 336 480 338 480 338 480 338 480 "
    "336 480 338 480 338 480 338 480 338 478 1104 478 340 478 1104 480 338 "
    "478 340 478 340 476 340 476 1106 478"
)


@pytest.mark.parametrize(
    "raw, section, data",
    [(RAW_744, "main", REAL_744), (RAW_1528, "quiet", REAL_1528)],
)
def test_real_raw_captures_decode(raw, section, data):
    (frame,) = decode(TCL112AC, wire(raw), expected=[section])
    assert frame.data == data
