import itertools

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
from pyhvac import registry
from pyhvac.plugins.fujitsu import (
    FUJITSU_AC,
    FUJITSU_AC_LONG15_LAYOUT,
    FUJITSU_AC_LONG_LAYOUT,
    FUJITSU_AC_MODELS,
    FUJITSU_AC_SHORT6_LAYOUT,
    FUJITSU_AC_SHORT_LAYOUT,
    FUJITSU_AC_VARIANT,
    FujitsuAcDevice,
)
from pyhvac.state import HvacState
from pyhvac.ir.codec import decode

VARIANTS = ("ARRAH2E", "ARDB1", "ARREB1E", "ARJW2", "ARRY4", "ARREW4E")
LEGACY_CLASS = {
    "ARRAH2E": "Fujitsuv1",
    "ARDB1": "Fujitsuv2",
    "ARREB1E": "Fujitsuv3",
    "ARJW2": "Fujitsuv4",
    "ARRY4": "Fujitsuv5",
    "ARREW4E": "Fujitsuv6",
}
MODES = ("auto", "cool", "dry", "fan", "heat")

# The C path deviates from the documented Fujitsu values here: the legacy
# glue (IRGHVAC.trans_swing / trans_hswing) has no "on", so IRac's swingv
# and swingh stay kOff and IRac::fujitsu's setSwing writes
# kFujitsuAcSwingOff; the port sends kFujitsuAcSwingVert/Horiz/Both.
DEFECTS = tuple(
    Defect("swing", ours, "off", "legacy glue has no swing/hswing 'on'")
    for ours in ("vert", "horiz", "both")
)
# Frames the port sends that C drops altogether: IRac::fujitsu sends the
# powerful and economy commands for ARREB1E only (IRac.cpp, "case
# fujitsu_ac_remote_model_t::ARREB1E:" in IRac::fujitsu), though
# IRFujitsuAC::setCmd documents kFujitsuAcCmdPowerful/kFujitsuAcCmdEcono for
# ARREW4E too (and ir_Fujitsu_test.cpp's ARREW4EShortCodes has them). The
# port sends them for ARREW4E: C_DROPS lists (variant, command).
C_DROPS = {("ARREW4E", "powerful"), ("ARREW4E", "econo")}

# ir_Fujitsu_test.cpp, as logical bytes (sent LSB first).
DEFAULT_ARRAH2E = bytes.fromhex("1463001010fe0930 81013100000020fd")
DEFAULT_ARDB1 = bytes.fromhex("1463001010fc0830 8101010000004d")
OFF_ARRAH2E = bytes.fromhex("14630010 1002fd")  # GetRawTurnOff
OFF_ARDB1 = bytes.fromhex("14630010 1002")  # RealShortARDB1OffExample
REAL_ARDB1_18_QUIET = bytes.fromhex(  # RealLongARDB1Example rawData1
    "1463001010fc0830 210104000000aa"
)
REAL_ARDB1_19 = bytes.fromhex(  # RealLongARDB1Example rawData2 (Power 0)
    "1463001010fc0830 3001000000009f"
)
ISSUE_414 = bytes.fromhex("1463001010fe0930 810400000000202b")
ISSUE_726 = bytes.fromhex("1463001010fe0930 810000000000202f")
ISSUE_716_POWERFUL = bytes.fromhex("14630010 1039c6")
ISSUE_716_ECONO = bytes.fromhex("14630010 1009f6")
FILTER_ON = bytes.fromhex("1463001010fe0930 a100000000002807")
CLEAN_ON = bytes.fromhex("1463001010fe0930 a008000000002008")
OUTSIDE_QUIET_ON = bytes.fromhex("1463001010fe0930 800100000000a0af")
TIMER_ON_12H = bytes.fromhex("1463001010fe0930 a030010000ad2032")
DISCUSSION_1701 = bytes.fromhex(  # IRac::fujitsu, ARREW4E, cool, 24 C, high
    "1463001010fe0931 810101000000004c"
)
ARREW4E_18 = bytes.fromhex("1463001010fe0931 500100210320201a")
ARREW4E_25_5 = bytes.fromhex("1463001010fe0931 8c010021031220ec")
ARREW4E_ECONO_ID3 = bytes.fromhex("14633010 1009f6")  # ARREW4EShortCodes
ARREW4E_POWERFUL_ID3 = bytes.fromhex("14633010 1039c6")


def model_of(variant):
    return next(m for m, v in FUJITSU_AC_VARIANT.items() if v == variant)


def device(variant="ARRAH2E"):
    return FujitsuAcDevice("fujitsu", model_of(variant))


def state(variant="ARRAH2E", power=True, mode="cool", temperature=24.0, **kw):
    return device(variant).normalise(HvacState(power, mode, temperature, **kw))


def frames(variant, target, previous=None):
    return device(variant).frames(previous, target, ())


def long_code(variant, target):
    return frames(variant, target)[-1].data


def read(variant, target):
    dev = device(variant)
    return dev.long_layout().read(long_code(variant, target))


class AsC:
    """The device minus the frames C drops (C_DROPS): C's frame list."""

    def __init__(self, dev, drops=C_DROPS):
        self.dev, self.drops = dev, drops
        self.PROTOCOL, self.capabilities = dev.PROTOCOL, dev.capabilities

    def normalise(self, target):
        return self.dev.normalise(target)

    def layouts(self, frames):
        return self.dev.layouts(frames)

    def frames(self, previous, target, actions):
        out = self.dev.frames(previous, target, actions)
        short = self.dev.short_layout()
        return [
            f
            for f in out
            if len(f.data) != len(short.skeleton)
            or (self.dev.variant, short.read(f.data)["cmd"]) not in self.drops
        ]


def device_for(record):
    return FujitsuAcDevice("fujitsu", record["model"])


@pytest.mark.parametrize("record", oracle_params("FUJITSU_AC"))
def test_matches_c_library(record):
    dev = AsC(device_for(record))
    assert_matches_oracle(dev, record, dev.layouts, DEFECTS)


def test_every_oracle_record_is_served_by_its_variant():
    for record in load_oracle("FUJITSU_AC"):
        assert LEGACY_CLASS[device_for(record).variant] == record["class"]


def test_layout_round_trips_every_oracle_state():
    for record in load_oracle("FUJITSU_AC"):
        dev = device_for(record)
        target = state_from_record(dev, record["state"])
        out = dev.frames(None, target, ())
        for frame, layout in zip(out, dev.layouts(out)):
            values = layout.read(frame.data)
            assert layout.build(**values) == bytearray(frame.data)


@pytest.mark.parametrize("record, states", sequence_params("FUJITSU_AC"))
def test_sequence_matches_a_persistent_c_object(record, states):
    # Powerful and economy are buttons: C's IRac::handleToggles sends them
    # only when they changed from the last message sent.
    dev = AsC(device_for(record))
    assert_sequence_matches_c(dev, record, states, dev.layouts, DEFECTS)


# States the oracle grid lacks, each from a fresh C object: off in every
# mode, every setpoint and fan level in every mode, and every combination of
# swing and features, on and off.
def extra_states(variant):
    caps = device(variant).capabilities
    feats = list(caps.features)
    out = [
        {"mode": mode, "temperature": t, "fan": fan, "swing": "off"}
        for mode in MODES + ("off",)
        for t in range(16, 31)
        for fan in ("auto", "lowest", "low", "medium", "high")
    ]
    for mode in MODES + ("off",):
        for combo in itertools.product(("off", "on"), repeat=len(feats)):
            old = {"mode": mode, "temperature": 25, "fan": "medium", "swing": "off"}
            old.update(zip(feats, combo))
            if caps.swing_h is not None:
                old["hswing"] = "off"
            out.append(old)
    return out


@pytest.mark.parametrize("variant", VARIANTS)
def test_states_beyond_the_oracle_grid_match_the_c_path(variant):
    pytest.importorskip("pyhvac.irhvac")
    record = next(
        r for r in load_oracle("FUJITSU_AC") if r["class"] == LEGACY_CLASS[variant]
    )
    dev = AsC(device(variant))
    for old in extra_states(variant):
        (rec,) = c_sequence(record, [old])  # a fresh C object per state
        assert_matches_oracle(dev, rec, dev.layouts, DEFECTS)


def test_checksums_hold_on_the_captures():
    for data, layout in (
        (DEFAULT_ARRAH2E, FUJITSU_AC_LONG_LAYOUT),
        (ISSUE_414, FUJITSU_AC_LONG_LAYOUT),
        (ISSUE_726, FUJITSU_AC_LONG_LAYOUT),
        (FILTER_ON, FUJITSU_AC_LONG_LAYOUT),
        (CLEAN_ON, FUJITSU_AC_LONG_LAYOUT),
        (OUTSIDE_QUIET_ON, FUJITSU_AC_LONG_LAYOUT),
        (TIMER_ON_12H, FUJITSU_AC_LONG_LAYOUT),
        (DISCUSSION_1701, FUJITSU_AC_LONG_LAYOUT),
        (ARREW4E_18, FUJITSU_AC_LONG_LAYOUT),
        (ARREW4E_25_5, FUJITSU_AC_LONG_LAYOUT),
        (DEFAULT_ARDB1, FUJITSU_AC_LONG15_LAYOUT),
        (REAL_ARDB1_18_QUIET, FUJITSU_AC_LONG15_LAYOUT),
        (REAL_ARDB1_19, FUJITSU_AC_LONG15_LAYOUT),
        (OFF_ARRAH2E, FUJITSU_AC_SHORT_LAYOUT),
        (ISSUE_716_POWERFUL, FUJITSU_AC_SHORT_LAYOUT),
        (ISSUE_716_ECONO, FUJITSU_AC_SHORT_LAYOUT),
        (ARREW4E_ECONO_ID3, FUJITSU_AC_SHORT_LAYOUT),
    ):
        assert layout.checksum.check(data)
        broken = bytearray(data)
        broken[-2] ^= 0x10  # a byte every checksum covers
        assert not layout.checksum.check(broken)


@pytest.mark.parametrize(
    "data, layout, fields",
    [
        (
            REAL_ARDB1_19,
            FUJITSU_AC_LONG15_LAYOUT,
            {"power": 0, "temp": 12, "mode": "cool", "fan": "auto"},
        ),
        (
            OUTSIDE_QUIET_ON,
            FUJITSU_AC_LONG_LAYOUT,
            {"outside_quiet": 1, "unknown": 1, "power": 0},
        ),
        (CLEAN_ON, FUJITSU_AC_LONG_LAYOUT, {"clean": 1, "temp": 40}),
        (
            TIMER_ON_12H,
            FUJITSU_AC_LONG_LAYOUT,
            {"timer_type": 3, "on_timer": 720, "on_timer_enable": 1},
        ),
        (ARREW4E_25_5, FUJITSU_AC_LONG_LAYOUT, {"protocol": 0x31, "temp": 35}),
        (ARREW4E_ECONO_ID3, FUJITSU_AC_SHORT_LAYOUT, {"id": 3, "cmd": "econo"}),
        (ARREW4E_POWERFUL_ID3, FUJITSU_AC_SHORT_LAYOUT, {"id": 3, "cmd": "powerful"}),
        (OFF_ARDB1, FUJITSU_AC_SHORT6_LAYOUT, {"id": 0, "cmd": "turn_off"}),
    ],
)
def test_layout_reads_the_captures(data, layout, fields):
    values = layout.read(data)
    assert {k: values[k] for k in fields} == fields
    assert layout.build(**values) == bytearray(data)


@pytest.mark.parametrize(
    "variant, target, expected",
    [
        # GetRawDefault: cool, 24 C, fan high, swing both.
        (
            "ARRAH2E",
            lambda: state(fan="4", swing_v="swing", swing_h="swing"),
            [DEFAULT_ARRAH2E],
        ),
        # ... and the ARDB1 version: Swing forced off by checkSum.
        ("ARDB1", lambda: state("ARDB1", fan="4", swing_v="swing"), [DEFAULT_ARDB1]),
        # GetRawTurnOff / RealShortARDB1OffExample.
        ("ARRAH2E", lambda: state(power=False), [OFF_ARRAH2E]),
        ("ARDB1", lambda: state("ARDB1", power=False, mode="heat"), [OFF_ARDB1]),
        # RealLongARDB1Example rawData1: cool, 18 C, fan quiet.
        (
            "ARDB1",
            lambda: state("ARDB1", temperature=18.0, fan="1"),
            [REAL_ARDB1_18_QUIET],
        ),
        # Issue414: heat, 24 C, fan auto. Issue726: auto, 24 C, fan auto.
        ("ARRAH2E", lambda: state(mode="heat"), [ISSUE_414]),
        ("ARRAH2E", lambda: state(mode="auto"), [ISSUE_726]),
        # Filter: filter_on (ARRY4, auto, 26 C, fan auto).
        (
            "ARRY4",
            lambda: state(
                "ARRY4", mode="auto", temperature=26.0, features={"purifier": True}
            ),
            [FILTER_ON],
        ),
        # Discussion1701: IRac::fujitsu, ARREW4E, cool, 24 C, fan high.
        ("ARREW4E", lambda: state("ARREW4E", fan="4"), [DISCUSSION_1701]),
    ],
)
def test_port_reproduces_the_captures(variant, target, expected):
    assert [f.data for f in frames(variant, target())] == expected


@pytest.mark.parametrize(
    "feature, capture", [("powerful", ISSUE_716_POWERFUL), ("economy", ISSUE_716_ECONO)]
)
def test_powerful_and_economy_are_the_issue_716_commands(feature, capture):
    target = state("ARREB1E", features={feature: True})
    out = frames("ARREB1E", target)
    assert [f.data for f in out[:-1]] == [capture]
    assert out[-1].data == long_code("ARREB1E", state("ARREB1E"))


def test_powerful_comes_before_economy():
    target = state("ARREB1E", features={"powerful": True, "economy": True})
    assert [f.data for f in frames("ARREB1E", target)[:2]] == [
        ISSUE_716_POWERFUL,
        ISSUE_716_ECONO,
    ]


@pytest.mark.parametrize("variant", ["ARREB1E", "ARREW4E"])
@pytest.mark.parametrize("feature", ["powerful", "economy"])
def test_commands_are_buttons_pressed_on_a_change(variant, feature):
    on = state(variant, features={feature: True})
    off = state(variant)
    n = len  # frame count: the command frames, then the long code
    assert n(frames(variant, on)) == 2  # previous=None: a fresh C object
    assert n(frames(variant, off)) == 1
    assert n(frames(variant, on, previous=off)) == 2
    assert n(frames(variant, on, previous=on)) == 1
    assert n(frames(variant, off, previous=on)) == 2  # turning it off: pressed
    assert n(frames(variant, off, previous=off)) == 1
    assert frames(variant, off, previous=on)[-1] == frames(variant, off)[-1]


@pytest.mark.parametrize("variant", ["ARRAH2E", "ARDB1", "ARJW2", "ARRY4"])
def test_other_variants_ignore_previous(variant):
    target = state(variant, swing_v="swing", features={"quiet": True})
    for previous in (None, state(variant, False, "heat", 30.0), target):
        assert frames(variant, target, previous) == frames(variant, target)


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("mode", MODES)
def test_off_is_the_turn_off_command_alone(variant, mode):
    extra = {"quiet": True}
    if "powerful" in device(variant).capabilities.features:
        extra["powerful"] = True
    target = state(variant, False, mode, 30.0, fan="2", features=extra)
    (frame,) = frames(variant, target)
    expected = OFF_ARDB1 if variant in ("ARDB1", "ARJW2") else OFF_ARRAH2E
    assert frame.data == expected


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("mode", MODES)
def test_mode_uses_its_documented_value(variant, mode):
    codes = {"auto": 0, "cool": 1, "dry": 2, "fan": 3, "heat": 4}
    layout = device(variant).long_layout()
    data = long_code(variant, state(variant, mode=mode))
    assert layout.read_raw(data, "mode") == codes[mode]
    assert layout.read(data)["power"] == 1


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize(
    "fan, name",
    zip(("auto", "1", "2", "3", "4"), ("auto", "quiet", "low", "medium", "high")),
)
def test_fan_follows_convert_fan(variant, fan, name):
    assert read(variant, state(variant, fan=fan))["fan"] == name


@pytest.mark.parametrize("variant", VARIANTS)
def test_quiet_sets_the_quiet_fan(variant):
    target = state(variant, fan="4", features={"quiet": True})
    assert read(variant, target)["fan"] == "quiet"


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("t", range(16, 31))
def test_setpoint_encoding(variant, t):
    raw = read(variant, state(variant, temperature=float(t)))["temp"]
    assert raw == ((t - 8) * 2 if variant == "ARREW4E" else (t - 16) * 4)


@pytest.mark.parametrize("tenths", range(160, 301, 5))
def test_arrew4e_setpoint_has_half_degrees(tenths):
    # IRFujitsuAC::setTemp for ARREW4E: Temp = (C - kFujitsuAcTempOffsetC / 2)
    # * 2, so every half degree from kFujitsuAcMinTemp to kFujitsuAcMaxTemp.
    t = tenths / 10
    target = state("ARREW4E", temperature=t)
    assert target.temperature == t
    assert read("ARREW4E", target)["temp"] == round((t - 8) * 2)


def test_arrew4e_half_degree_is_the_real_capture():
    # TestIRFujitsuACClass.Temperature, arrew4e_25_5c (a real ARREW4E
    # message, getTemp 25.5): its Temp field is the port's 25.5 C. The
    # capture's timers and power bit are not what IRac sends.
    capture = FUJITSU_AC_LONG_LAYOUT.read(ARREW4E_25_5)
    ours = read("ARREW4E", state("ARREW4E", temperature=25.5))
    assert ours["temp"] == capture["temp"] == 35
    capture_18 = FUJITSU_AC_LONG_LAYOUT.read(ARREW4E_18)
    assert read("ARREW4E", state("ARREW4E", temperature=18.0))["temp"] == (
        capture_18["temp"]
    )


@pytest.mark.parametrize("variant", ["ARRAH2E", "ARDB1", "ARREB1E", "ARJW2", "ARRY4"])
def test_other_variants_snap_to_whole_degrees(variant):
    # Their Temp is (C - 16) * 4 and getTemp reads it back in whole degrees.
    caps = device(variant).capabilities
    assert caps.temperature.decimals == (0,)
    assert state(variant, temperature=22.5).temperature == 22.0


def test_arrew4e_half_degrees_match_the_c_path():
    # The old glue passes the setpoint through; IRac::fujitsu's setTemp
    # encodes the half degree.
    pytest.importorskip("pyhvac.irhvac")
    record = next(r for r in load_oracle("FUJITSU_AC") if r["class"] == "Fujitsuv6")
    dev = AsC(device("ARREW4E"))
    states = [
        {"mode": mode, "temperature": t, "fan": "medium", "swing": "off"}
        for mode in MODES
        for t in (16.5, 22.5, 25.5, 29.5)
    ]
    for rec in c_sequence(record, states):
        assert_matches_oracle(dev, rec, dev.layouts, DEFECTS)


@pytest.mark.parametrize("variant", VARIANTS)
def test_capabilities_are_the_documented_ones(variant):
    caps = device(variant).capabilities
    assert caps.modes == MODES
    assert (caps.temperature.min, caps.temperature.max) == (16.0, 30.0)
    # kFujitsuAcFanAuto, kFujitsuAcFanQuiet .. kFujitsuAcFanHigh
    assert caps.fan.values == ("auto", "1", "2", "3", "4")
    swing_v = variant not in ("ARDB1", "ARJW2")  # checkSum forces Swing off
    swing_h = variant in ("ARRAH2E", "ARREW4E")  # setSwing: Horiz and Both
    assert (caps.swing_v is not None, caps.swing_h is not None) == (swing_v, swing_h)
    assert (
        set(caps.features)
        == {
            "ARRAH2E": {"quiet"},
            "ARDB1": {"quiet"},
            "ARREB1E": {"powerful", "quiet", "economy"},
            "ARJW2": {"quiet"},
            "ARRY4": {"purifier", "quiet", "cleaning"},
            "ARREW4E": {"powerful", "quiet", "economy"},
        }[variant]
    )


@pytest.mark.parametrize(
    "variant, unknown, protocol",
    [
        ("ARRAH2E", 1, 0x30),
        ("ARREB1E", 1, 0x30),
        ("ARRY4", 1, 0x30),
        ("ARREW4E", 0, 0x31),
    ],
)
def test_long_code_constants_per_variant(variant, unknown, protocol):
    values = read(variant, state(variant))
    assert (values["unknown"], values["protocol"]) == (unknown, protocol)
    assert (values["cmd"], values["rest_length"]) == ("long", 9)


@pytest.mark.parametrize("variant", ["ARDB1", "ARJW2"])
def test_ardb1_and_arjw2_send_15_bytes_and_never_swing(variant):
    # IRFujitsuAC::checkSum forces kFujitsuAcSwingOff for these remotes, so
    # they offer no swing; a swing passed anyway is dropped by normalise.
    caps = device(variant).capabilities
    assert caps.swing_v is None and caps.swing_h is None
    target = state(variant, swing_v="swing", swing_h="swing")
    assert (target.swing_v, target.swing_h) == ("off", "off")
    data = long_code(variant, target)
    assert len(data) == 15
    values = FUJITSU_AC_LONG15_LAYOUT.read(data)
    assert (values["cmd"], values["rest_length"], values["swing"]) == (
        "long_ardb1",
        8,
        "off",
    )


@pytest.mark.parametrize(
    "variant, swing_v, swing_h, expected",
    [
        ("ARRAH2E", "swing", "off", "vert"),
        ("ARRAH2E", "off", "swing", "horiz"),
        ("ARRAH2E", "swing", "swing", "both"),
        ("ARREW4E", "swing", "swing", "both"),
        ("ARREB1E", "swing", "off", "vert"),
        ("ARRY4", "swing", "off", "vert"),
    ],
)
def test_swing_sends_the_documented_bits(variant, swing_v, swing_h, expected):
    target = state(variant, swing_v=swing_v, swing_h=swing_h)
    assert read(variant, target)["swing"] == expected


@pytest.mark.parametrize(
    "purifier, cleaning", [(True, False), (False, True), (True, True)]
)
def test_arry4_sends_filter_and_clean(purifier, cleaning):
    target = state("ARRY4", features={"purifier": purifier, "cleaning": cleaning})
    values = read("ARRY4", target)
    assert (values["filter"], values["clean"]) == (int(purifier), int(cleaning))


def test_message_shape():
    dev = device()
    pulses = dev.encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (3324, 1574)
    assert pulses[-2:] == (448, 8100)
    assert len(pulses) == 2 + 2 * 128 + 2


def test_unknown_variant_is_rejected():
    with pytest.raises(ValueError):
        FujitsuAcDevice("fujitsu", "generic", variant="ARXX")


@pytest.mark.parametrize("model", FUJITSU_AC_MODELS)
def test_registry_serves_the_port(model):
    dev = registry.get_device("fujitsu", model)
    assert isinstance(dev, FujitsuAcDevice)
    assert dev.variant == FUJITSU_AC_VARIANT[model]


@pytest.mark.parametrize("key", ["swing", "hswing"])
def test_undeclared_swing_deviation_is_reported(key):
    record = next(
        r
        for r in load_oracle("FUJITSU_AC")
        if r["state"].get(key) == "on"
        and r["state"]["mode"] != "off"
        and r["class"] == "Fujitsuv1"
    )
    dev = AsC(device_for(record))
    with pytest.raises(AssertionError, match="swing"):
        assert_matches_oracle(dev, record, dev.layouts, ())


def test_undeclared_arrew4e_commands_are_reported():
    record = next(
        r
        for r in load_oracle("FUJITSU_AC")
        if r["state"].get("powerful") == "on" and r["class"] == "Fujitsuv6"
    )
    dev = AsC(device_for(record), drops=set())
    with pytest.raises(Exception):
        assert_matches_oracle(dev, record, dev.layouts, DEFECTS)


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("FUJITSU_AC")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)


# ir_Fujitsu_test.cpp DecodeFujitsuAC.Issue1455: decodeFujitsuAC matches the
# bits with _tolerance + kFujitsuAcExtraTolerance (30 %) and no mark excess;
# this capture has bit marks as short as 304 µs for 448. C reads it as an
# ARREW4E, Heat, 19C.
REAL_RAW = (
    "3220 1700 354 446 380 448 380 1296 352 446 382 1296 354 448 380 448 "
    "378 446 382 1296 352 1296 354 448 378 446 380 446 382 1294 354 1270 "
    "380 448 380 446 380 448 380 446 380 450 378 448 380 446 380 448 380 "
    "448 380 448 380 450 376 450 380 448 378 1298 352 448 378 448 380 448 "
    "380 448 378 450 378 450 378 448 378 1296 354 446 382 446 380 448 378 "
    "448 380 1296 352 1296 354 1296 354 1272 376 1272 378 1296 354 1294 354 "
    "1296 354 446 380 448 378 1296 354 448 378 448 378 448 380 446 380 1272 "
    "378 446 380 450 378 448 378 1296 354 1296 354 446 380 448 378 448 378 "
    "446 382 446 380 1296 354 1296 354 446 380 1296 354 446 380 446 380 446 "
    "380 1294 354 448 380 448 380 448 380 448 380 446 380 448 380 446 380 "
    "448 380 446 380 446 380 448 380 446 380 448 380 448 380 446 380 1296 "
    "352 446 380 1296 354 446 380 448 380 448 380 1296 354 448 378 448 380 "
    "446 380 446 382 446 380 446 382 446 380 1272 378 446 380 446 382 1294 "
    "354 446 382 1294 354 446 382 446 382 446 380 448 380 448 380 448 380 "
    "448 378 1296 354 446 382 446 380 1296 354 446 382 1296 354 446 382 "
    "1294 354 446 382 446 380 446 382"
)


def test_real_raw_capture_decodes():
    (frame,) = decode(FUJITSU_AC, [int(x) for x in REAL_RAW.split()])
    assert frame.data == bytes.fromhex("1463001010fe09315804001401292015")
