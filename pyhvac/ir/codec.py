"""Encode frames to a pulse train and decode captured pulses back to frames."""

from __future__ import annotations

from .model import Frame, Manchester, PulseDistance, PulseWidth, Signal


def _frame_bits(frame, section):
    """The frame's bits in wire order, after checking the unused bits are zero."""
    used = frame.nbits - 8 * (len(frame.data) - 1)
    if used < 8:
        unused = (0xFF << used) & 0xFF if section.lsb_first else 0xFF >> used
        if frame.data[-1] & unused:
            raise ValueError(
                f"frame for {frame.section!r}: unused bits of the last byte must be zero"
            )
    bits = []
    for i in range(frame.nbits):
        byte = frame.data[i // 8]
        shift = i % 8 if section.lsb_first else 7 - i % 8
        bits.append((byte >> shift) & 1)
    return bits


def _pack(bits, lsb_first):
    data = bytearray((len(bits) + 7) // 8)
    for i, bit in enumerate(bits):
        if bit:
            data[i // 8] |= 1 << (i % 8) if lsb_first else 0x80 >> (i % 8)
    return bytes(data)


def _alternating(durations):
    """Signed levels for a mark-first alternating tuple."""
    return [d if i % 2 == 0 else -d for i, d in enumerate(durations)]


def _section_levels(section, bits):
    levels = _alternating(section.header)
    enc = section.bits
    for bit in bits:
        if isinstance(enc, PulseDistance):
            levels += [enc.mark, -(enc.one_space if bit else enc.zero_space)]
        elif isinstance(enc, PulseWidth):
            levels += [enc.one_mark if bit else enc.zero_mark, -enc.space]
        else:
            mark_first = (bit == 1) == enc.one_is_mark_first
            levels += [enc.half, -enc.half] if mark_first else [-enc.half, enc.half]
    levels += _alternating(section.footer)
    if section.gap:
        levels.append(-section.gap)
    return levels


def _merge(levels):
    """Sum neighbouring same-polarity levels and drop a leading space."""
    merged = []
    for d in levels:
        if merged and (merged[-1] > 0) == (d > 0):
            merged[-1] += d
        else:
            merged.append(d)
    if merged and merged[0] < 0:
        merged.pop(0)
    return merged


def encode(protocol, frames):
    """Turn a list of frames into a Signal."""
    frames = list(frames)
    if not frames:
        raise ValueError("encode needs at least one frame")
    levels = []
    for frame in frames:
        try:
            section = protocol.sections[frame.section]
        except KeyError:
            raise ValueError(
                f"unknown section {frame.section!r} for protocol {protocol.name!r}"
            ) from None
        levels += _section_levels(section, _frame_bits(frame, section))
    merged = _merge(levels)
    if merged[-1] > 0:
        merged.append(-protocol.trailer_gap)
    return Signal(protocol.carrier, tuple(abs(d) for d in merged))
