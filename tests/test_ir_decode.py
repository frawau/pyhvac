import random

import pytest

from pyhvac.ir.codec import DecodeError, decode, encode
from pyhvac.ir.model import (
    Frame,
    Manchester,
    Protocol,
    PulseDistance,
    PulseWidth,
    Section,
)

NEC = Section(
    PulseDistance(560, 560, 1690), header=(9000, 4500), footer=(560,), gap=40000
)
NEC_MSB = Section(
    PulseDistance(560, 560, 1690),
    header=(9000, 4500),
    footer=(560,),
    gap=40000,
    lsb_first=False,
)
PW = Section(PulseWidth(600, 1200, 600), header=(2400, 600), gap=25000, lsb_first=False)
MAN = Section(Manchester(500), header=(3000, 1000), gap=20000)
# Complementary pulses: a one is a long mark and a short space, a zero the reverse.
PWC = Section(
    PulseWidth(600, 1500, 1500, one_space=600),
    header=(8200, 4200),
    footer=(1900,),
    gap=34300,
)
LEADER = Section(PulseDistance(430, 430, 1300), footer=(430,), gap=25000)
DAIKIN_FRAME = Section(
    PulseDistance(430, 430, 1300), header=(3500, 1700), footer=(430,), gap=35000
)

ALL = Protocol(
    "all",
    {
        "nec": NEC,
        "nec_msb": NEC_MSB,
        "pw": PW,
        "man": MAN,
        "pwc": PWC,
        "leader": LEADER,
        "frame": DAIKIN_FRAME,
    },
)
NEC_ONLY = Protocol("nec", {"nec": NEC})

CASES = [
    [Frame("nec", b"\x5a\xa5\x00\xff")],
    [Frame("nec_msb", b"\x5a\xa5\x03")],
    [Frame("nec", b"\x05", 3)],
    [Frame("pw", b"\xc5\x80", 9)],
    [Frame("man", b"\xa5\x3c")],
    [Frame("pwc", b"\x01\x41\x36\x00"), Frame("pwc", b"\x01\x41\x36\x00")],
    # first bit is 0: its first (space) half merges with the header's last space
    [Frame("man", b"\x02", 2)],
    [
        Frame("leader", b"\x00", 5),
        Frame("frame", bytes.fromhex("11da2700c5")),
        Frame("frame", bytes.fromhex("11da27004210")),
    ],
]


def names(frames):
    return [f.section for f in frames]


def jitter(pulses, seed=1234):
    rng = random.Random(seed)
    return [max(1, round(d * rng.uniform(0.9, 1.1))) for d in pulses]


@pytest.mark.parametrize("frames", CASES)
def test_round_trip_exact(frames):
    pulses = encode(ALL, frames).pulses
    assert decode(ALL, pulses, expected=names(frames)) == frames


@pytest.mark.parametrize("seed", [1, 2, 3])
@pytest.mark.parametrize("frames", CASES)
def test_round_trip_with_jitter(frames, seed):
    pulses = jitter(encode(ALL, frames).pulses, seed)
    assert decode(ALL, pulses, expected=names(frames)) == frames


def test_greedy_decode_without_expected():
    frames = [Frame("nec", b"\x12\x34")]
    assert decode(NEC_ONLY, encode(NEC_ONLY, frames).pulses) == frames


def test_repeated_message_decodes_to_two_frames_greedily():
    frame = Frame("nec", b"\x12\x34")
    pulses = encode(NEC_ONLY, [frame, frame]).pulses
    assert decode(NEC_ONLY, pulses) == [frame, frame]


def test_repeated_message_fails_strict_single_section():
    frame = Frame("nec", b"\x12\x34")
    pulses = encode(NEC_ONLY, [frame, frame]).pulses
    with pytest.raises(DecodeError):
        decode(NEC_ONLY, pulses, expected=["nec"])


def test_capture_without_trailing_gap():
    frames = [Frame("nec", b"\x12\x34")]
    pulses = encode(NEC_ONLY, frames).pulses[:-1]  # ends on the footer mark
    assert decode(NEC_ONLY, pulses, expected=["nec"]) == frames


def test_headerless_section_needs_expected():
    frames = CASES[-1]
    with pytest.raises(DecodeError):
        decode(ALL, encode(ALL, frames).pulses)


def test_protocol_without_headers_needs_expected():
    p = Protocol("leader", {"leader": LEADER})
    pulses = encode(p, [Frame("leader", b"\x00", 5)]).pulses
    with pytest.raises(ValueError, match="expected"):
        decode(p, pulses)


def test_corrupted_bit_reports_index():
    pulses = list(encode(NEC_ONLY, [Frame("nec", b"\x12")]).pulses)
    pulses[5] = 3000  # space of the second bit
    with pytest.raises(DecodeError) as err:
        decode(NEC_ONLY, pulses, expected=["nec"])
    assert err.value.index == 5


@pytest.mark.parametrize(
    "pulses", [[], [9000, -4500, 560, 560], [9000, 0, 560], [9000, 4500.0, 560]]
)
def test_invalid_pulses(pulses):
    with pytest.raises(ValueError):
        decode(NEC_ONLY, pulses, expected=["nec"])


def test_negative_pulse_error_names_index():
    with pytest.raises(ValueError, match=r"pulses\[1\]"):
        decode(NEC_ONLY, [9000, -4500, 560, 560], expected=["nec"])


def test_unknown_expected_section():
    with pytest.raises(ValueError, match="unknown section"):
        decode(NEC_ONLY, [9000, 4500], expected=["nope"])


def test_capture_with_short_final_silence():
    # The last space of a capture is idle time, not a measured gap.
    frames = [Frame("nec", b"\x12\x34")]
    pulses = list(encode(NEC_ONLY, frames).pulses[:-1]) + [8000]
    assert decode(NEC_ONLY, pulses, expected=["nec"]) == frames
    assert decode(NEC_ONLY, pulses) == frames
