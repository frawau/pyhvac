import pytest

from pyhvac.ir.model import (
    Frame,
    Manchester,
    Protocol,
    PulseDistance,
    PulseWidth,
    Section,
    Signal,
)

NEC_BITS = PulseDistance(560, 560, 1690)


def main_protocol(**kwargs):
    return Protocol("t", {"main": Section(NEC_BITS, footer=(560,))}, **kwargs)


@pytest.mark.parametrize(
    "args", [(0, 560, 1690), (560.0, 560, 1690), (True, 560, 1690), (560, -1, 1690)]
)
def test_pulse_distance_rejects_bad_durations(args):
    with pytest.raises(ValueError):
        PulseDistance(*args)


def test_pulse_distance_needs_distinct_spaces():
    with pytest.raises(ValueError):
        PulseDistance(560, 560, 560)


def test_pulse_width_needs_distinct_marks():
    with pytest.raises(ValueError):
        PulseWidth(600, 600, 600)


def test_pulse_width_one_space_defaults_to_space():
    assert PulseWidth(600, 1200, 600).space_after(1) == 600
    assert PulseWidth(600, 1500, 1500, one_space=600).space_after(1) == 600
    assert PulseWidth(600, 1500, 1500, one_space=600).space_after(0) == 1500
    with pytest.raises(ValueError):
        PulseWidth(600, 1500, 1500, one_space=0)


def test_manchester_rejects_zero_half():
    with pytest.raises(ValueError):
        Manchester(0)


def test_section_converts_header_and_footer_to_tuples():
    s = Section(NEC_BITS, header=[9000, 4500], footer=[560])
    assert s.header == (9000, 4500)
    assert s.footer == (560,)


@pytest.mark.parametrize(
    "kwargs",
    [dict(header=(9000, 0)), dict(footer=(560.5,)), dict(gap=-1), dict(gap=1.5)],
)
def test_section_rejects_bad_durations(kwargs):
    kwargs.setdefault("footer", (560,))
    with pytest.raises(ValueError):
        Section(NEC_BITS, **kwargs)


def test_pulse_distance_section_needs_footer():
    with pytest.raises(ValueError, match="footer"):
        Section(NEC_BITS)


def test_pulse_width_and_manchester_sections_need_no_footer():
    Section(PulseWidth(600, 1200, 600))
    Section(Manchester(500))


def test_section_rejects_unknown_bit_encoding():
    with pytest.raises(ValueError):
        Section("nec", footer=(560,))


def test_protocol_defaults():
    p = main_protocol()
    assert p.carrier == 38000
    assert p.tolerance == 0.25
    assert p.mark_excess == 50
    assert p.trailer_gap == 100_000


def test_protocol_needs_sections():
    with pytest.raises(ValueError):
        Protocol("t", {})


def test_protocol_rejects_non_section():
    with pytest.raises(ValueError):
        Protocol("t", {"main": NEC_BITS})


@pytest.mark.parametrize("tolerance", [0, 0.5, -0.1, 1])
def test_protocol_rejects_bad_tolerance(tolerance):
    with pytest.raises(ValueError):
        main_protocol(tolerance=tolerance)


@pytest.mark.parametrize(
    "kwargs", [dict(carrier=0), dict(mark_excess=-1), dict(trailer_gap=0)]
)
def test_protocol_rejects_bad_numbers(kwargs):
    with pytest.raises(ValueError):
        main_protocol(**kwargs)


def test_protocol_copies_sections():
    sections = {"main": Section(NEC_BITS, footer=(560,))}
    p = Protocol("t", sections)
    sections.clear()
    assert "main" in p.sections


def test_frame_normalises_bytearray_and_defaults_nbits():
    f = Frame("main", bytearray(b"\x01\x02"))
    assert type(f.data) is bytes
    assert f.data == b"\x01\x02"
    assert f.nbits == 16
    assert f == Frame("main", b"\x01\x02", 16)


def test_frame_accepts_int_list():
    assert Frame("main", [1, 2]).data == b"\x01\x02"


def test_frame_rejects_empty_data_with_bits():
    # Empty data is only for bitless sections, and then carries no bits.
    with pytest.raises(ValueError):
        Frame("main", b"", 8)


@pytest.mark.parametrize("nbits", [0, 8, 17])
def test_frame_nbits_must_fall_in_last_byte(nbits):
    with pytest.raises(ValueError):
        Frame("main", b"\x01\x02", nbits)


@pytest.mark.parametrize("nbits", [9, 16])
def test_frame_accepts_nbits_in_last_byte(nbits):
    assert Frame("main", b"\x01\x02", nbits).nbits == nbits


@pytest.mark.parametrize(
    "carrier, pulses",
    [(38000, ()), (38000, (9000,)), (38000, (9000, 0)), (0, (9000, 4500))],
)
def test_signal_validation(carrier, pulses):
    with pytest.raises(ValueError):
        Signal(carrier, pulses)


def test_signal_stores_tuple():
    assert Signal(38000, [9000, 4500]).pulses == (9000, 4500)
