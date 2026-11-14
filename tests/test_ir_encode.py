import pytest

from pyhvac.ir.codec import encode
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
NEC_NO_GAP = Section(PulseDistance(560, 560, 1690), header=(9000, 4500), footer=(560,))
PW = Section(PulseWidth(600, 1200, 600), header=(2400, 600), gap=25000, lsb_first=False)
MAN = Section(Manchester(500))
PWC = Section(PulseWidth(600, 1500, 1500, one_space=600), footer=(1900,), gap=34300)

P = Protocol(
    "test",
    {
        "nec": NEC,
        "nec_msb": NEC_MSB,
        "nec_no_gap": NEC_NO_GAP,
        "pw": PW,
        "man": MAN,
        "pwc": PWC,
    },
    carrier=36000,
)


def pulses(*frames):
    return encode(P, list(frames)).pulses


def test_pulse_distance_lsb_first():
    assert pulses(Frame("nec", b"\x01")) == (
        (9000, 4500, 560, 1690) + (560, 560) * 7 + (560, 40000)
    )


def test_pulse_distance_msb_first():
    assert pulses(Frame("nec_msb", b"\x01")) == (
        (9000, 4500) + (560, 560) * 7 + (560, 1690) + (560, 40000)
    )


def test_partial_last_byte_lsb_first():
    assert pulses(Frame("nec", b"\x05", 3)) == (
        9000,
        4500,
        560,
        1690,
        560,
        560,
        560,
        1690,
        560,
        40000,
    )


def test_partial_last_byte_msb_first_uses_high_bits():
    assert pulses(Frame("nec_msb", b"\xa0", 3)) == (
        9000,
        4500,
        560,
        1690,
        560,
        560,
        560,
        1690,
        560,
        40000,
    )


@pytest.mark.parametrize(
    "frame", [Frame("nec", b"\x09", 3), Frame("nec_msb", b"\xa1", 3)]
)
def test_unused_bits_must_be_zero(frame):
    with pytest.raises(ValueError, match="unused"):
        encode(P, [frame])


def test_pulse_width_last_space_merges_into_gap():
    assert pulses(Frame("pw", b"\x80", 2)) == (2400, 600, 1200, 600, 600, 25600)


def test_trailer_gap_appended_when_ending_on_mark():
    assert pulses(Frame("nec_no_gap", b"\x00", 1)) == (
        9000,
        4500,
        560,
        560,
        560,
        100000,
    )


def test_manchester_merges_neighbouring_halves():
    # bits 1,1,0 -> +500 -500 +500 -500 -500 +500
    assert pulses(Frame("man", b"\x03", 3)) == (500, 500, 500, 1000, 500, 100000)


def test_leading_space_is_dropped():
    # a single 0 bit is -500 +500
    assert pulses(Frame("man", b"\x00", 1)) == (500, 100000)


def test_frames_are_concatenated():
    assert pulses(Frame("nec", b"\x01", 1), Frame("nec", b"\x00", 1)) == (
        9000,
        4500,
        560,
        1690,
        560,
        40000,
        9000,
        4500,
        560,
        560,
        560,
        40000,
    )


def test_signal_carries_protocol_carrier():
    assert encode(P, [Frame("nec", b"\x01")]).carrier == 36000


def test_unknown_section():
    with pytest.raises(ValueError, match="unknown section"):
        encode(P, [Frame("nope", b"\x01")])


def test_no_frames():
    with pytest.raises(ValueError):
        encode(P, [])


def test_pulse_width_with_a_one_space_varies_the_space_with_the_bit():
    assert pulses(Frame("pwc", b"\x05", 3)) == (
        (1500, 600, 600, 1500, 1500, 600) + (1900, 34300)
    )
