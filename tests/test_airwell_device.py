"""AirwellDevice against IRremoteESP8266 (ir_Airwell.h / IRac::airwell).

The AIRWELL oracle fixture cannot be compared bit for bit: the C library's
timing recorder (IRsend::mark/space under SWIGLIB) appends each mark() and
space() call as the next pulse of an alternating list, so a Manchester bit
sent as "space, mark" is recorded as "mark, space". Every recorded message
is the same data-free pulse train, whatever the state
(test_recorded_pulses_carry_no_data), and the legacy class sent exactly
that.

The C state itself is sound, so the acceptance compares against it:
tests/fixtures/airwell_c_raw.json holds the AirwellProtocol word the C path
builds for every oracle state (a fresh IRac, as the fixture was recorded)
and for sequence_params' states through one persistent IRac. The word is
read from the compiled library with ctypes (c_raws below): the glue fills
IRac.next and sends, then IRac::handleToggles(cleanState(next), prev) and
IRac::airwell run on a fresh IRAirwellAc and getRaw() gives the word. The
C-only tests regenerate it and check it against the fixture and more states.
The pulses themselves are pinned by the output IRsend::sendAirwell gives in
ir_Airwell_test.cpp (test_encoder_matches_sendairwell).
"""

import json
import re
from pathlib import Path

import pytest

from c_oracle import c_frozen
from oracle import load_oracle
from port_oracle import (
    assert_matches_oracle,
    assert_sequence_matches_c,
    oracle_params,
    sequence_params,
    state_from_record,
)
from pyhvac.ir.codec import decode, encode
from pyhvac.ir.model import Frame
from pyhvac.protocols.airwell import (
    AIRWELL,
    AIRWELL_KNOWN_GOOD_STATE,
    AIRWELL_LAYOUT,
    AIRWELL_MODELS,
    AirwellDevice,
    airwell_word,
)
from pyhvac.state import HvacState

FIXTURE = Path(__file__).parent / "fixtures" / "airwell_c_raw.json"

# What the recorder stores for any Airwell message: per word the header
# mark and space, then two 950 us entries per bit; then the footer mark and
# kDefaultMessageGap.
RECORDED = ([2850, 2850] + [950] * 68) * 3 + [3800, 100000]


def device():
    return AirwellDevice("airwell", "generic")


def c_frames(raw):
    """The frames IRsend::sendAirwell sends for the word ``raw``."""
    word = Frame("main", airwell_word(raw), 34)
    return [word, word, word, Frame("footer", b"")]


def c_record(record, raw):
    """``record`` with the pulses IRsend::sendAirwell sends for ``raw``, and
    its state in today's fan vocabulary (see ``modern``)."""
    return {
        **record,
        "state": modern(record["state"]),
        "pulses": list(encode(AIRWELL, c_frames(raw)).pulses),
    }


def modern(old):
    """An old-vocabulary state with the 0.1.x fan "lowest" read as "low".

    The legacy entity offered four speeds; the header has three
    (kAirwellFanLow/Medium/High). IRAirwellAc::convertFan sends kMin
    ("lowest") and kLow ("low") both as kAirwellFanLow, so a record's
    "lowest" is the port's "1" (low) and C's word is unchanged.
    """
    if old.get("fan") == "lowest":
        return {**old, "fan": "low"}
    return old


def fixture():
    return json.loads(FIXTURE.read_text())


def fixture_raw(state):
    for entry in fixture()["records"]:
        if entry["state"] == state:
            return int(entry["raw"], 16)
    raise KeyError(state)


def main_word(state, previous=None):
    dev = device()
    frames = dev.frames(previous, dev.normalise(state), ())
    assert frames[0] == frames[1] == frames[2]
    return frames[0].data


def read(state, previous=None):
    return AIRWELL_LAYOUT.read(main_word(state, previous))


def c_raws(states):
    """The AirwellProtocol words C built for ``states`` sent in order through
    one legacy object; frozen in tests/fixtures/oracle_extra."""
    return c_frozen(["c_raws", states], lambda: _c_raws_live(states))


def _c_raws_live(states):
    """C-gated: the AirwellProtocol word the C path builds for each
    old-vocabulary state, sent in order through one legacy Airwell object
    (its IRac keeps the last message sent, as in c_sequence)."""
    from pyhvac import irhvac
    import ctypes

    from pyhvac.protocols.airwell import Airwell

    lib = ctypes.CDLL(irhvac._irhvac.__file__)
    ctor = lib._ZN11IRAirwellAcC1Etbb  # IRAirwellAc(pin, inverted, modulation)
    ctor.argtypes = [ctypes.c_void_p, ctypes.c_uint16, ctypes.c_bool, ctypes.c_bool]
    ctor.restype = None
    # IRac::airwell(IRAirwellAc*, on, opmode_t, degrees, fanspeed_t)
    airwell = lib._ZN4IRac7airwellEP11IRAirwellAcbN5stdAc8opmode_tEfNS2_10fanspeed_tE
    airwell.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_bool,
        ctypes.c_int,
        ctypes.c_float,
        ctypes.c_int,
    ]
    airwell.restype = None
    get_raw = lib._ZNK11IRAirwellAc6getRawEv
    get_raw.argtypes = [ctypes.c_void_p]
    get_raw.restype = ctypes.c_uint64

    legacy = Airwell()
    status = dict(legacy.status)
    out = []
    for old in states:
        legacy.status = dict(status)
        legacy.irac.next = Airwell().irac.next
        prev = legacy.irac.getStatePrev()
        legacy.to_set = dict(old)
        legacy.build_ircode()  # sends: IRac's _prev becomes this message
        send = irhvac.IRac.handleToggles(
            irhvac.IRac.cleanState(legacy.irac.getState()), prev
        )
        # The library is built with UNIT_TEST: IRAirwellAc holds an
        # IRsendTest of about 110 kB.
        ac = ctypes.create_string_buffer(1 << 20)
        ctor(ac, 4, False, True)
        airwell(
            int(legacy.irac.this),
            ac,
            send.power,
            send.mode,
            send.degrees,
            send.fanspeed,
        )
        legacy.irac.resetTiming()
        out.append(get_raw(ac))
    return out


# ------------------------------------------------------------- acceptance


@pytest.mark.parametrize("record", oracle_params("AIRWELL"))
def test_matches_c_library(record):
    dev = device()
    assert record["pulses"] == RECORDED
    raw = fixture_raw(record["state"])
    assert_matches_oracle(dev, c_record(record, raw), dev.LAYOUTS)


def test_recorded_pulses_carry_no_data():
    records = load_oracle("AIRWELL")
    assert len({tuple(r["pulses"]) for r in records}) == 1
    frames = decode(AIRWELL, records[0]["pulses"], expected=["main"] * 3 + ["footer"])
    assert [f.data for f in frames[:3]] == [bytes(5)] * 3


def test_raw_recorded_pulses_are_not_what_the_port_sends():
    dev = device()
    record = load_oracle("AIRWELL")[0]
    with pytest.raises(AssertionError):
        assert_matches_oracle(dev, record, dev.LAYOUTS)


def test_sequence_matches_the_recorded_c_states():
    # The power toggle depends on the message before, which C's IRac keeps.
    dev = device()
    ((record, states),) = [p.values for p in sequence_params("AIRWELL")]
    raws = [int(r, 16) for r in fixture()["sequences"][record["class"]]]
    assert len(raws) == len(states)
    previous = None
    for old, raw in zip(states, raws):
        rec = c_record({**record, "state": old}, raw)
        assert_matches_oracle(dev, rec, dev.LAYOUTS, previous=previous)
        previous = state_from_record(dev, modern(old))


@pytest.mark.parametrize("record, states", sequence_params("AIRWELL"))
def test_sequence_matches_a_persistent_c_object(record, states):
    dev = device()
    raws = iter(c_raws(states))

    def adapt(rec):
        assert rec["pulses"] == RECORDED
        return c_record(rec, next(raws))

    assert_sequence_matches_c(dev, record, states, dev.LAYOUTS, adapt=adapt)


def test_fixture_matches_the_c_library():
    data = fixture()
    records = load_oracle("AIRWELL")
    assert [e["state"] for e in data["records"]] == [r["state"] for r in records]
    raws = [c_raws([e["state"]])[0] for e in data["records"]]
    assert [f"{r:#x}" for r in raws] == [e["raw"] for e in data["records"]]
    for record, states in (p.values for p in sequence_params("AIRWELL")):
        raws = c_raws(states)
        assert [f"{r:#x}" for r in raws] == data["sequences"][record["class"]]


LABEL = {"auto": "auto", "1": "low", "2": "medium", "3": "high"}


def _old(state):
    return {
        "mode": state.mode if state.power else "off",
        "temperature": int(state.temperature),
        "fan": LABEL[state.fan],
    }


def test_every_setpoint_fan_and_off_message_matches_the_c_library():
    # Fresh objects: every mode, on and off, every setpoint, every fan.
    dev = device()
    states = [
        HvacState(power, mode, float(t), fan=fan)
        for power in (True, False)
        for mode in dev.capabilities.modes
        for t in range(16, 31)
        for fan in LABEL
    ]
    raws = [c_raws([_old(s)])[0] for s in states]
    for state, raw in zip(states, raws):
        assert main_word(state) == airwell_word(raw), state


# ------------------------------------------------------------------ rules


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("AIRWELL"):
        state = state_from_record(dev, modern(record["state"]))
        main = dev.frames(None, state, ())[0]
        values = AIRWELL_LAYOUT.read(main.data)
        assert AIRWELL_LAYOUT.build(**values) == bytearray(main.data)


def test_known_good_state_reads_as_documented():
    # kAirwellKnownGoodState: "Mode Fan, Speed 1, 25C"; the skeleton is it
    # with the named members cleared.
    data = airwell_word(AIRWELL_KNOWN_GOOD_STATE)
    values = AIRWELL_LAYOUT.read(data)
    assert (values["mode"], values["fan"], values["temperature"]) == (
        "fan",
        "low",
        25,
    )
    assert (values["power_toggle"], values["unnamed_low"]) == (0, 2)
    assert AIRWELL_LAYOUT.build(mode="fan", fan="low", temperature=25) == data


def test_off_carries_mode_auto_in_every_mode():
    # IRac passes mode "off"; IRAirwellAc::convertMode maps it to kAirwellAuto.
    dev = device()
    for mode in dev.capabilities.modes:
        for t in (16.0, 30.0):
            values = read(HvacState(False, mode, t, fan="2"))
            assert (values["mode"], values["temperature"], values["fan"]) == (
                "auto",
                int(t),
                "medium",
            )


def test_dry_locks_the_fan_low():
    for fan in LABEL:
        assert read(HvacState(True, "dry", 22.0, fan=fan))["fan"] == "low"


@pytest.mark.parametrize("fan, code", [("auto", 3), ("1", 0), ("2", 1), ("3", 2)])
def test_every_fan_level_uses_its_documented_code(fan, code):
    # kAirwellFanAuto = 3, kAirwellFanLow = 0, kAirwellFanMedium = 1,
    # kAirwellFanHigh = 2.
    data = main_word(HvacState(True, "cool", 22.0, fan=fan))
    assert AIRWELL_LAYOUT.read_raw(data, "fan") == code


@pytest.mark.parametrize("celsius, code", [(16, 1), (23, 8), (30, 15)])
def test_temperature_is_offset_from_the_minimum(celsius, code):
    data = main_word(HvacState(True, "cool", float(celsius)))
    assert AIRWELL_LAYOUT.read_raw(data, "temperature") == code


def test_power_toggle_without_previous_is_the_target_power():
    # A fresh IRac's previous state is of protocol UNKNOWN: no toggle rule.
    assert read(HvacState(True, "heat", 20.0))["power_toggle"] == 1
    assert read(HvacState(False, "heat", 20.0))["power_toggle"] == 0


@pytest.mark.parametrize(
    "before, after, toggle",
    [(True, True, 0), (True, False, 1), (False, False, 0), (False, True, 1)],
)
def test_power_toggle_with_previous_toggles_on_change(before, after, toggle):
    # IRac::handleToggles: power = desired.power ^ prev->power for AIRWELL.
    dev = device()
    previous = dev.normalise(HvacState(before, "cool", 22.0))
    target = HvacState(after, "cool", 22.0)
    assert read(target, previous)["power_toggle"] == toggle


def test_encode_passes_previous_to_the_toggle():
    dev = device()
    on = HvacState(True, "cool", 22.0)
    assert dev.encode(None, on).signal != dev.encode(on, on).signal


# --------------------------------------------------------------- captures

# IRsend::sendAirwell's output in ir_Airwell_test.cpp (SyntheticExample),
# without the "f38000d50" carrier prefix.
SENDAIRWELL = {
    0x2B0D0181B: "m2850s3800"
    + (
        "m1900s1900m1900s1900m950s950m1900s950m950s950m950s950m950"
        "s1900m950s950m1900s1900m1900s950m950s950m950s950m950s950"
        "m950s950m950s950m950s1900m950s950m1900s950m950s950m950"
        "s950m950s950m950s950m950s1900m950s950m1900s1900m950s950"
    )
    + "m3800s3800"
    + (
        "m1900s1900m1900s1900m950s950m1900s950m950s950m950s950m950"
        "s1900m950s950m1900s1900m1900s950m950s950m950s950m950s950"
        "m950s950m950s950m950s1900m950s950m1900s950m950s950m950"
        "s950m950s950m950s950m950s1900m950s950m1900s1900m950s950"
    )
    + "m3800s3800"
    + (
        "m1900s1900m1900s1900m950s950m1900s950m950s950m950s950m950"
        "s1900m950s950m1900s1900m1900s950m950s950m950s950m950s950"
        "m950s950m950s950m950s1900m950s950m1900s950m950s950m950"
        "s950m950s950m950s950m950s1900m950s950m1900s1900m950s950"
    )
    + "m4750s100000",
    0x60080002: (
        "m2850s2850"
        + (
            "m950s950m950s950m950s1900m950s950m1900s950m950s950m950s950m950s950"
            "m950s950m950s950m950s950m950s950m950s1900m1900s950m950s950m950s950"
            "m950s950m950s950m950s950m950s950m950s950m950s950m950s950m950s950"
            "m950s950m950s950m950s950m950s950m950s950m950s1900m1900s950"
        )
    )
    * 3
    + "m3800s100000",
}


def _pulses(text):
    return tuple(int(x) for x in re.findall(r"[ms](\d+)", text))


@pytest.mark.parametrize("raw", sorted(SENDAIRWELL))
def test_encoder_matches_sendairwell(raw):
    assert encode(AIRWELL, c_frames(raw)).pulses == _pulses(SENDAIRWELL[raw])


# RealExample3 (ir_Airwell_test.cpp): 0x60080002, "Power Toggle: Off, Mode:
# 1 (Cool), Fan: 2 (High), Temp: 16C".
REAL_COOL_16_HIGH = [
    3010, 2852,
    904, 1042, 872, 1052, 872, 1932, 904, 956, 1878, 1050, 874, 1046, 872,
    956, 876, 1048, 872, 1044, 876, 1046, 874, 958, 872, 1050, 872, 1966,
    1880, 956, 872, 1048, 874, 1048, 872, 1050, 872, 958, 872, 1050, 872,
    1048, 872, 1050, 872, 958, 872, 1048, 872, 1050, 872, 1048, 872, 958, 872,
    1050, 872, 1048, 872, 1050, 872, 1872, 1880, 1048,
    2978, 2880,
    872, 1048, 872, 1050, 872, 1964, 872, 958, 1880, 1050, 872, 1050, 872,
    958, 872, 1050, 872, 1050, 872, 1050, 872, 958, 872, 1050, 872, 1964,
    1882, 958, 870, 1050, 872, 1048, 872, 1050, 872, 958, 872, 1048, 872,
    1050, 872, 1050, 872, 958, 872, 1050, 872, 1050, 872, 1050, 872, 958, 872,
    1050, 872, 1050, 872, 1050, 872, 1874, 1880, 1050,
    2978, 2880,
    872, 1050, 872, 1050, 872, 1964, 872, 958, 1880, 1050, 872, 1050, 872,
    958, 872, 1050, 872, 1050, 872, 1050, 872, 958, 872, 1050, 872, 1964,
    1880, 958, 872, 1050, 872, 1050, 872, 1050, 872, 958, 872, 1052, 870,
    1050, 872, 1050, 872, 958, 872, 1050, 872, 1050, 872, 1050, 872, 958, 872,
    1050, 872, 1050, 872, 1050, 872, 1874, 1880, 1050, 3894,
]  # fmt: skip


def test_port_reproduces_the_real_cool_capture():
    dev = device()
    on = dev.normalise(HvacState(True, "cool", 16.0, fan="3"))
    ours = dev.frames(on, on, ())  # no power change: no toggle
    theirs = decode(AIRWELL, REAL_COOL_16_HIGH, expected=[f.section for f in ours])
    assert ours == theirs
    assert ours[0].data == airwell_word(0x60080002)


def test_port_reproduces_the_reconstructed_known_state():
    # ReconstructKnownState: toggle on, cool, 22C, fan low -> 0x240380002.
    assert main_word(HvacState(True, "cool", 22.0, fan="1")) == airwell_word(
        0x240380002
    )


@pytest.mark.parametrize(
    "raw, fields",
    [
        # RealExample: "Power Toggle: On, Mode: 2 (Heat), Fan: 3 (Auto), Temp: 25C"
        (0x2B0D0181B, (1, "heat", "auto", 25)),
        # "Power Toggle: On, Mode: 1 (Cool), Fan: 3 (Auto), Temp: 30C"
        (0x270F8181B, (1, "cool", "auto", 30)),
        # RealExample2: "Power Toggle: Off, Mode: 2 (Heat), Fan: 3 (Auto), Temp: 23C"
        (0xB0C0181B, (0, "heat", "auto", 23)),
    ],
)
def test_layout_reads_the_real_captures(raw, fields):
    # These remotes set unnamed bits (0x181B low, raw bit 23) that
    # kAirwellKnownGoodState, and so the C path and the port, leave clear.
    values = AIRWELL_LAYOUT.read(airwell_word(raw))
    assert (
        values["power_toggle"],
        values["mode"],
        values["fan"],
        values["temperature"],
    ) == fields
    assert (values["unnamed_low"], values["unnamed_high"]) == (0x181B, 1)


# --------------------------------------------------------------- registry


def test_message_shape():
    dev = device()
    frames = dev.frames(None, dev.normalise(HvacState(True, "cool", 22.0)), ())
    assert [f.section for f in frames] == ["main"] * 3 + ["footer"]
    assert all(f.nbits == 34 for f in frames[:3])
    pulses = dev.encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[-1] == 100000


def test_fan_offers_the_headers_three_speeds_and_auto():
    # kAirwellFanLow/Medium/High/Auto: the legacy entity's fourth speed
    # (lowest, the same kAirwellFanLow as low) is gone.
    fan = device().capabilities.fan
    assert fan.values == ("auto", "1", "2", "3")
    assert [fan.label(v) for v in fan.values] == ["auto", "low", "medium", "high"]
    assert device().normalise(HvacState(True, "cool", 22.0, fan="4")).fan == "auto"


def test_a_lowest_record_sends_what_a_low_record_sends():
    # convertFan: kMin and kLow are both kAirwellFanLow.
    for record in load_oracle("AIRWELL"):
        if record["state"]["fan"] == "lowest":
            low = {**record["state"], "fan": "low"}
            assert fixture_raw(record["state"]) == fixture_raw(low)


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("AIRWELL")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:2])
