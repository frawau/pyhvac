"""Bitless sections: fixed bursts with no data bits (preambles, leaders)."""

import random

import pytest

from pyhvac.ir.codec import DecodeError, decode, encode
from pyhvac.ir.model import Frame, Protocol, PulseDistance, Section

BITS = PulseDistance(460, 420, 1270)
FRAME = Section(BITS, header=(3500, 1728), footer=(460,), gap=35204)

# DAIKIN2: a lone mark and a long space before the frames
LEADER = Protocol(
    "leader",
    {"leader": Section(None, header=(10024,), gap=25180), "main": FRAME},
)
# DAIKIN64/128: two long pulses, then the frame
PREAMBLE = Protocol(
    "preamble",
    {"preamble": Section(None, header=(9800, 9800, 9800, 9800)), "main": FRAME},
)
# DAIKIN64: a bare mark after the frame
TRAILING = Protocol("trailing", {"main": FRAME, "tail": Section(None, header=(4600,))})

EMPTY = b""
CASES = [
    (LEADER, [Frame("leader", EMPTY), Frame("main", b"\x11\xda\x27")]),
    (PREAMBLE, [Frame("preamble", EMPTY), Frame("main", b"\x11\xda\x27")]),
    (TRAILING, [Frame("main", b"\x11\xda\x27"), Frame("tail", EMPTY)]),
]


def test_empty_frame_has_zero_bits():
    assert Frame("leader", b"").nbits == 0
    assert Frame("leader", b"", 0) == Frame("leader", b"")


@pytest.mark.parametrize("nbits", [1, 8])
def test_empty_frame_needs_zero_bits(nbits):
    with pytest.raises(ValueError):
        Frame("leader", b"", nbits)


def test_data_frame_still_needs_bits():
    with pytest.raises(ValueError):
        Frame("main", b"\x01", 0)


def test_bitless_section_needs_some_pulses():
    with pytest.raises(ValueError):
        Section(None)


def test_bitless_section_needs_no_footer():
    Section(None, header=(10024,), gap=25180)


def test_leader_encodes_as_mark_then_gap():
    pulses = encode(LEADER, CASES[0][1]).pulses
    assert pulses[:3] == (10024, 25180, 3500)


def test_bitless_section_rejects_data():
    with pytest.raises(ValueError, match="bitless"):
        encode(LEADER, [Frame("leader", b"\x01"), Frame("main", b"\x01")])


def test_data_section_rejects_empty_frame():
    with pytest.raises(ValueError, match="data"):
        encode(LEADER, [Frame("main", b"")])


@pytest.mark.parametrize(
    "protocol, frames", CASES, ids=["leader", "preamble", "trailing"]
)
def test_round_trip(protocol, frames):
    pulses = encode(protocol, frames).pulses
    assert decode(protocol, pulses, expected=[f.section for f in frames]) == frames


@pytest.mark.parametrize(
    "protocol, frames", CASES, ids=["leader", "preamble", "trailing"]
)
def test_round_trip_with_jitter(protocol, frames):
    rng = random.Random(7)
    pulses = [round(d * rng.uniform(0.9, 1.1)) for d in encode(protocol, frames).pulses]
    assert decode(protocol, pulses, expected=[f.section for f in frames]) == frames


def test_greedy_decode_finds_bitless_sections():
    frames = CASES[0][1]
    assert decode(LEADER, encode(LEADER, frames).pulses) == frames


def test_wrong_leader_is_reported():
    pulses = list(encode(LEADER, CASES[0][1]).pulses)
    pulses[0] = 5000
    with pytest.raises(DecodeError) as err:
        decode(LEADER, pulses, expected=["leader", "main"])
    assert err.value.index == 0
