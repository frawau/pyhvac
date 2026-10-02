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
from pyhvac.fields import Joined
from pyhvac.ir.codec import DecodeError, decode, encode
from pyhvac.protocols.midea import (
    MIDEA,
    MIDEA_COMFEE_MODELS,
    MIDEA_DANBY_MODELS,
    MIDEA_KAYSUN_MODELS,
    MIDEA_KEYSTONE_MODELS,
    MIDEA_LAYOUT,
    MIDEA_LENNOX_MODELS,
    MIDEA_MODELS,
    MIDEA_MRCOOL_MODELS,
    MIDEA_PIONEER_SYSTEM_MODELS,
    MIDEA_SPECIAL_LAYOUT,
    MIDEA_TROTECH_MODELS,
    MideaChecksum,
    MideaDevice,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Midea values here (pyhvac's glue,
# not IRremoteESP8266):
# - IRGHVAC.build_ircode has no "sleep" key, so IRac gets sleep -1 and
#   IRac::midea calls setSleep(false);
# - IRGHVAC.trans_swing has no "on", so IRac's swingv stays kOff and
#   IRac::midea's setSwingVToggle(false) never sends kMideaACToggleSwingV.
#   That is a whole special message, not a field: ``swing_rule`` puts the
#   port's swing message into the C record where the port sends one (see
#   test_swing_on_never_reaches_c and test_undeclared_swing_is_reported).
SLEEP = Defect("sleep", 1, 0, "legacy glue never passes sleep")
DEFECTS = (SLEEP,)

PLUGIN_MODELS = {
    "midea": MIDEA_MODELS,
    "comfee": MIDEA_COMFEE_MODELS,
    "danby": MIDEA_DANBY_MODELS,
    "kaysun": MIDEA_KAYSUN_MODELS,
    "keystone": MIDEA_KEYSTONE_MODELS,
    "lennox": MIDEA_LENNOX_MODELS,
    "mrcool": MIDEA_MRCOOL_MODELS,
    "pioneer_system": MIDEA_PIONEER_SYSTEM_MODELS,
    "trotech": MIDEA_TROTECH_MODELS,
}
SERVED = [(p, m) for p, models in PLUGIN_MODELS.items() for m in models]
MODES = ("auto", "cool", "dry", "fan", "heat")
FEATURES = ("powerful", "quiet", "economy", "light", "cleaning", "sleep")

# ir_Midea.h's special messages, as 48-bit codes.
SPECIAL_CODES = {
    "swing": 0xA201FFFFFF7C,  # kMideaACToggleSwingV
    "econo": 0xA202FFFFFF7E,  # kMideaACToggleEcono
    "light": 0xA208FFFFFF75,  # kMideaACToggleLight
    "turbo": 0xA209FFFFFF74,  # kMideaACToggleTurbo
    "clean": 0xA20DFFFFFF70,  # kMideaACToggleSelfClean
    "8c_heat": 0xA20FFFFFFF73,  # kMideaACToggle8CHeat
    "quiet_on": 0xA212FFFFFF6E,  # kMideaACQuietOn
    "quiet_off": 0xA213FFFFFF6F,  # kMideaACQuietOff
}

# ir_Midea_test.cpp real captures.
# TestDecodeMidea.DecodeRealExample (issue 354): on, auto, 65 F (Fahrenheit,
# which the entity cannot express), fan auto.
RAW_354 = (
    "4366 4470 498 1658 522 554 498 1658 496 580 498 580 498 578 498 580 "
    "498 1658 498 1658 498 578 498 578 498 580 496 582 496 578 498 1658 "
    "498 580 498 580 498 1656 498 1656 500 580 498 578 502 576 500 1656 "
    "498 1656 500 1654 500 1656 500 1656 498 1658 498 1656 500 1658 498 "
    "1656 498 1656 500 1656 500 1654 500 1578 578 1658 498 1656 500 1658 "
    "498 1656 498 1656 500 578 498 1638 516 1656 500 578 500 1656 500 1656 "
    "498 1658 522 554 500 5258 4366 4472 498 580 498 1658 498 580 498 1656 "
    "500 1600 556 1658 500 1656 500 578 498 578 522 1634 498 1588 568 1658 "
    "498 1656 500 1654 498 580 498 1658 498 1658 498 580 496 578 500 1654 "
    "500 1636 518 1656 500 578 520 558 498 578 498 580 498 576 500 578 498 "
    "580 498 578 498 578 498 580 498 578 498 580 498 580 520 556 498 580 "
    "496 580 498 578 500 578 498 1658 498 580 498 578 498 1656 500 578 498 "
    "580 498 580 498 1656 522"
)
# TestMideaACClass.CelsiusRemoteTemp (issue 819): on, cool, fan low.
REAL_819_17C = 0xA18840FFFF56
REAL_819_30C = 0xA1884DFFFF5D


def code_bytes(code):
    return code.to_bytes(6, "big")


def device(plugin="midea", model="generic"):
    return MideaDevice(plugin, model)


def state(power=True, mode="cool", temperature=22.0, **kw):
    return device().normalise(HvacState(power, mode, temperature, **kw))


def frames(target, previous=None):
    return device().frames(previous, target, ())


def read(target):
    return MIDEA_LAYOUT.read(b"".join(f.data for f in frames(target)[:2]))


def specials(target, previous=None):
    """The special messages sent after the state, by command name."""
    out = []
    for first in frames(target, previous)[2::2]:
        assert first.section == "special"
        out.append(MIDEA_SPECIAL_LAYOUT.read(first.data + bytes(6))["command"])
    return out


def wire(record):
    """``record`` with the pulses the C library puts on the wire.

    IRsend::sendMidea ends each message with space(kMideaMinGap) and then
    space(kDefaultMessageGap); IRac's timing log keeps them as two entries,
    so everything after the first message sits one position off. On the wire
    they are one 105 600 µs space.
    """
    out = []
    for p in record["pulses"]:
        if p == 100000 and out and out[-1] == 5600:
            out[-1] += p
        else:
            out.append(p)
    assert len(out) % 2 == 0
    return {**record, "pulses": out}


def swing_rule(dev):
    """``adapt`` for C records (wired, in order): where the port sends
    kMideaACToggleSwingV, which C never gets to send (the glue drops swing
    "on"), the port's swing message goes into the C record at its place
    (right after the state)."""
    last = []

    def adapt(rec):
        rec = wire(rec)
        now = state_from_record(dev, rec["state"])
        before = last[-1] if last else None
        last.append(now)
        if "swing" not in dev.specials(before, now):
            return rec
        ours = dev.frames(before, now, ())
        names = [f.section for f in ours[:2] + ours[4:]]
        theirs = decode(MIDEA, rec["pulses"], expected=names)
        theirs = theirs[:2] + ours[2:4] + theirs[2:]
        return {**rec, "pulses": list(encode(MIDEA, theirs).pulses)}

    return adapt


def check(record, defects=DEFECTS):
    dev = device()
    adapted = swing_rule(dev)(record)
    assert_matches_oracle(dev, adapted, dev.layouts, defects)


@pytest.mark.parametrize("record", oracle_params("MIDEA"))
def test_matches_c_library(record):
    check(record)


@pytest.mark.parametrize("record, states", sequence_params("MIDEA"))
def test_sequence_matches_a_persistent_c_object(record, states):
    # The toggles depend on the message before: IRac::handleToggles sends
    # swing, econo, turbo, light and clean on a change, and IRac::sendAc's
    # prev_quiet sends quiet on/off on a change, as the port does.
    dev = device()
    assert_sequence_matches_c(
        dev, record, states, dev.layouts, DEFECTS, adapt=swing_rule(dev)
    )


# A walk through the toggles in every mode, on and off, both ways.
TOGGLE_STATES = [
    {"mode": m, "temperature": 24, "fan": "low", **{f: v for f in fs}}
    for m in ("cool", "heat", "off", "fan", "dry", "auto")
    for fs, v in (
        (("powerful", "economy"), "on"),
        (("light", "cleaning", "quiet"), "on"),
        (("powerful",), "off"),
        (("economy", "light"), "off"),
        (("cleaning", "quiet"), "off"),
    )
]


def test_toggle_walk_matches_a_persistent_c_object():
    record = load_oracle("MIDEA")[0]
    dev = device()
    states = []
    current = {}
    for step in TOGGLE_STATES:
        current = {**current, **step}
        states.append(dict(current))
    assert_sequence_matches_c(
        dev, record, states, dev.layouts, DEFECTS, adapt=swing_rule(dev)
    )


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("MIDEA"):
        ours = dev.frames(None, state_from_record(dev, record["state"]), ())
        for i, joined in enumerate(dev.layouts(ours)):
            data = ours[2 * i].data + ours[2 * i + 1].data
            layout = joined.layout
            assert layout.build(**layout.read(data)) == bytearray(data)


def test_layouts_are_one_joined_pair_per_message():
    ours = frames(state(features={"powerful": True, "light": True}))
    layouts = MideaDevice.layouts(ours)
    assert all(isinstance(j, Joined) and j.count == 2 for j in layouts)
    assert [j.layout for j in layouts] == [MIDEA_LAYOUT] + [MIDEA_SPECIAL_LAYOUT] * 2


# States the oracle grid lacks: off and every setpoint in every mode, every
# fan level, and the feature combinations in every mode, on and off.
EXTRA_STATES = (
    [
        {"mode": m, "temperature": t, "fan": f}
        for m in MODES + ("off",)
        for t in (17, 18, 29, 30)
        for f in ("auto", "low", "medium", "high")
    ]
    + [
        {"mode": m, "temperature": 24, "fan": "medium", f: "on"}
        for m in MODES + ("off",)
        for f in FEATURES
    ]
    + [
        {"mode": m, "temperature": 21, "fan": "high", **{f: "on" for f in FEATURES}}
        for m in MODES + ("off",)
    ]
)


def test_states_beyond_the_oracle_grid_match_the_c_path():
    record = load_oracle("MIDEA")[0]
    for old in EXTRA_STATES:
        # One state per C object: a fresh IRac, as previous=None.
        (rec,) = c_sequence(record, [old])
        check(rec)


def test_swing_on_never_reaches_c():
    # The oracle's swing "on" records carry exactly the swing "off" pulses.
    records = load_oracle("MIDEA")
    by_state = {tuple(sorted(r["state"].items())): r["pulses"] for r in records}
    pairs = 0
    for r in records:
        if r["state"].get("swing") == "on":
            off = tuple(sorted({**r["state"], "swing": "off"}.items()))
            assert by_state[off] == r["pulses"]
            pairs += 1
    assert pairs > 0


def test_undeclared_swing_is_reported():
    dev = device()
    record = next(r for r in load_oracle("MIDEA") if r["state"].get("swing") == "on")
    with pytest.raises(DecodeError):
        assert_matches_oracle(dev, wire(record), dev.layouts, DEFECTS)


def test_undeclared_sleep_deviation_is_reported():
    record = next(r for r in load_oracle("MIDEA") if r["state"].get("sleep") == "on")
    check(record)
    with pytest.raises(AssertionError, match="sleep"):
        check(record, defects=())


def test_checksum_matches_calc_checksum():
    # TestMideaACClass.Checksums: IRMideaAC::calcChecksum of the other bytes.
    checksum = MideaChecksum(0, 5, 5, reverse=True)
    for code, sum_ in (
        (0xA1826FFFFF62, 0x62),
        (0xA18177FFFF70, 0x70),
        (0xA1826FFFFF00, 0x62),
        (0x000000000000, 0x00),
        (0x1234567890AB, 0xDF),
        (0xFFFFFFFFFFFF, 0xA0),
    ):
        assert checksum.compute(code_bytes(code)) == sum_
    assert checksum.check(code_bytes(0xA1826FFFFF62))
    assert not checksum.check(code_bytes(0x1234567890AB))


def test_real_capture_decodes():
    # Issue 354: the capture's footer gap is 5258 µs; the second message ends
    # on its footer mark.
    raw = [int(x) for x in RAW_354.split()] + [105600]
    first, second = decode(MIDEA, raw, expected=["state", "state_inverted"])
    assert first.data == code_bytes(0xA18263FFFF6E)
    assert second.data == bytes(~b & 0xFF for b in first.data)
    values = MIDEA_LAYOUT.read(first.data + second.data)
    assert (values["fahrenheit"], values["temperature"], values["mode"]) == (
        1,
        20,  # raw 3: 65 F (kMideaACMinTempF + 3) is read as 17 + 3
        "auto",
    )
    assert MIDEA_LAYOUT.checksum.check(first.data + second.data)


@pytest.mark.parametrize("t, code", [(17.0, REAL_819_17C), (30.0, REAL_819_30C)])
def test_port_reproduces_the_real_819_captures(t, code):
    first, second = frames(state(True, "cool", t, fan="1"))
    assert first.data == code_bytes(code)
    assert second.data == bytes(~b & 0xFF for b in first.data)


@pytest.mark.parametrize("command, code", SPECIAL_CODES.items())
def test_special_messages_are_the_documented_codes(command, code):
    data = MIDEA_SPECIAL_LAYOUT.build(type="special", command=command)
    assert bytes(data[:6]) == code_bytes(code)
    assert bytes(data[6:]) == bytes(~b & 0xFF for b in code_bytes(code))


@pytest.mark.parametrize(
    "mode, raw", [("cool", 0), ("dry", 1), ("auto", 2), ("heat", 3), ("fan", 4)]
)
def test_mode_uses_its_documented_value(mode, raw):
    data = frames(state(True, mode))[0].data
    assert MIDEA_LAYOUT.read_raw(data + bytes(6), "mode") == raw


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("t", [17.0, 23.0, 30.0])
def test_off_carries_mode_auto_and_the_setpoint(mode, t):
    # IRac passes mode "off"; convertMode maps it to kMideaACAuto.
    values = read(state(False, mode, t, fan="3"))
    assert (values["power"], values["mode"]) == (0, "auto")
    assert (values["temperature"], values["fan"]) == (int(t), "3")


@pytest.mark.parametrize("t", range(17, 31))
def test_every_setpoint(t):
    assert frames(state(temperature=float(t)))[0].data[2] == 0x40 | (t - 17)


@pytest.mark.parametrize("fan, raw", [("auto", 0), ("1", 1), ("2", 2), ("3", 3)])
def test_every_fan_level_uses_its_documented_code(fan, raw):
    data = frames(state(fan=fan))[0].data
    assert MIDEA_LAYOUT.read_raw(data + bytes(6), "fan") == raw


def test_state_keeps_the_reset_bits():
    # IRac::midea leaves the timers and the follow-me sensor off: Type
    # command, BeepDisable set, Celsius.
    values = read(state())
    assert values["type"] == "command"
    assert values["off_timer"] == 0b111111  # kMideaACTimerOff
    assert values["sensor_temp"] == 0b1111111  # kMideaACSensorTempOnTimerOff
    assert (values["disable_sensor"], values["beep_disable"]) == (1, 1)
    assert (values["fahrenheit"], values["unknown"]) == (0, 0)


def test_sleep_sets_the_sleep_bit():
    assert read(state(features={"sleep": True}))["sleep"] == 1
    assert read(state())["sleep"] == 0


def test_toggles_are_sent_in_irmideaac_send_order():
    on = {f: True for f in FEATURES}
    assert specials(state(True, "cool", swing_v="swing", features=on)) == [
        "swing",
        "econo",
        "turbo",
        "light",
        "clean",
        "quiet_on",
    ]
    assert specials(state()) == []


@pytest.mark.parametrize(
    "power, mode, sent",
    [
        (True, "cool", True),
        (True, "dry", True),
        (True, "auto", True),
        (True, "heat", False),
        (True, "fan", False),
        (False, "heat", True),  # an off message carries mode auto
    ],
)
def test_cleaning_is_only_sent_in_cool_dry_or_auto(power, mode, sent):
    target = state(power, mode, features={"cleaning": True})
    assert specials(target) == (["clean"] if sent else [])
    before = state(power, mode, features={"cleaning": False})
    assert specials(target, before) == (["clean"] if sent else [])


@pytest.mark.parametrize(
    "feature, command",
    [
        ("economy", "econo"),
        ("powerful", "turbo"),
        ("light", "light"),
        ("cleaning", "clean"),
    ],
)
@pytest.mark.parametrize(
    "before, after, sent",
    [
        (False, False, False),
        (False, True, True),
        (True, True, False),
        (True, False, True),
    ],
)
def test_with_previous_a_toggle_is_sent_on_a_change(
    feature, command, before, after, sent
):
    previous = state(features={feature: before})
    target = state(features={feature: after})
    assert specials(target, previous) == ([command] if sent else [])
    assert specials(target) == ([command] if after else [])


@pytest.mark.parametrize(
    "before, after, sent",
    [
        ("off", "off", []),
        ("off", "swing", ["swing"]),
        ("swing", "swing", []),
        ("swing", "off", ["swing"]),
    ],
)
def test_with_previous_swing_is_toggled_on_a_change(before, after, sent):
    assert specials(state(swing_v=after), state(swing_v=before)) == sent
    assert specials(state(swing_v=after)) == (["swing"] if after == "swing" else [])


@pytest.mark.parametrize(
    "before, after, sent",
    [
        (False, False, []),
        (False, True, ["quiet_on"]),
        (True, True, []),
        (True, False, ["quiet_off"]),
    ],
)
def test_quiet_is_sent_on_a_change(before, after, sent):
    previous = state(features={"quiet": before})
    assert specials(state(features={"quiet": after}), previous) == sent
    # A fresh IRac's last quiet is off: quiet on is sent, quiet off is not.
    assert specials(state(features={"quiet": after})) == (["quiet_on"] if after else [])


def test_encode_passes_previous_to_the_toggles():
    dev = device()
    target = HvacState(True, "cool", 22.0, features={"light": True})
    fresh = dev.encode(None, target).signal.pulses
    again = dev.encode(target, target).signal.pulses
    assert len(fresh) == 2 * len(again)


def test_message_shape():
    command = device().encode(None, HvacState(True, "cool", 22.0))
    pulses = command.signal.pulses
    assert pulses[:2] == (4480, 4480)
    assert pulses[98:102] == (560, 5600, 4480, 4480)
    assert pulses[-2:] == (560, 105600)
    assert len(pulses) == 2 * (2 + 2 * 48 + 2)
    assert command.signal.carrier == 38000


def test_capabilities_are_the_documented_ones():
    # Unchanged by the capability audit: every value ir_Midea.h documents
    # that the port sends. kMideaACToggle8CHeat has no feature name.
    caps = MideaDevice.capabilities
    assert caps.modes == ("auto", "cool", "fan", "dry", "heat")
    # kMideaACMinTempC / kMideaACMaxTempC
    assert (caps.temperature.min, caps.temperature.max) == (17.0, 30.0)
    assert caps.fan.values == ("auto", "1", "2", "3")  # kMideaACFan{Low,Med,High}
    assert caps.swing_v.values == ("off", "swing")  # kMideaACToggleSwingV
    assert caps.swing_h is None
    assert set(caps.features) == {
        "powerful",
        "quiet",
        "economy",
        "light",
        "cleaning",
        "sleep",
    }


# No real capture in ir_Midea_test.cpp needs it, but
# decodeMidea matches with kMideaTolerance (30 %) and kMarkExcess.
def test_decode_tolerance_is_the_c_decoders():
    assert (MIDEA.tolerance, MIDEA.mark_excess) == (0.30, 50)


# ---------------------------------------------------- RG57-family variants
# SmartIR captures (climate 1392, 1393, 1395, 1782, 2900 in °C; 1163, 1220,
# 2040, 2220, 2960 in °F): fan auto also sets data[1] bit 5 (the "unknown"
# bit), fan mode sends setpoint code 30, and RG57-F sends whole °F - 62 with
# useFahrenheit.


def rg57_state(variant, target):
    dev = MideaDevice("Test", "unit", variant=variant)
    return dev.frames(None, dev.normalise(target), ())[0].data[:6].hex()


@pytest.mark.parametrize(
    "variant, target, capture",
    [
        ("RG57", HvacState(True, "cool", 24.0, fan="auto"), "a1a047ffff69"),
        ("RG57", HvacState(True, "cool", 24.0, fan="1"), "a18847ffff51"),
        ("RG57", HvacState(True, "fan", 24.0, fan="1"), "a18c5effff4b"),
        ("RG57-F", HvacState(True, "cool", 22.0, fan="auto"), "a1a06affff44"),
        ("RG57-F", HvacState(True, "heat", 21.0, fan="1"), "a18b68ffff69"),
        ("RG57-F", HvacState(True, "fan", 22.0, fan="3"), "a19c7effff63"),
    ],
)
def test_rg57_variants_reproduce_the_captures(variant, target, capture):
    # 2900 (Goodman MSH123E21AXAA) and 2220 (Blueridge RG57A4)
    assert rg57_state(variant, target) == capture


def test_rg57_f_reaches_every_whole_fahrenheit_from_62_to_86():
    dev = MideaDevice("Test", "unit", variant="RG57-F")
    caps = dev.capabilities.temperature
    sent = set()
    t = caps.min
    while t <= caps.max:
        data = dev.frames(None, dev.normalise(HvacState(True, "cool", t)), ())[0].data
        sent.add(MIDEA_LAYOUT.read_raw(data, "temperature") + 62)
        t = round(t + 0.5, 1)
    assert sent == set(range(62, 87))


@pytest.mark.parametrize("variant", ["RG57", "RG57-F"])
@pytest.mark.parametrize("mode", ["dry", "auto"])
@pytest.mark.parametrize("fan", ["auto", "1", "2", "3"])
def test_rg57_dry_and_auto_force_fan_auto_without_the_bit(variant, mode, fan):
    # SmartIR climate 2040 and 1392: every dry and auto code, whatever the
    # fan key, carries fan auto with data[1] bit 5 clear.
    dev = MideaDevice("Test", "unit", variant=variant)
    data = dev.frames(None, dev.normalise(HvacState(True, mode, 24.0, fan=fan)), ())
    values = MIDEA_LAYOUT.read(data[0].data)
    assert (values["fan"], values["unknown"]) == ("auto", 0)
