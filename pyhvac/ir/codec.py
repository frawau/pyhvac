"""Encode frames to a pulse train and decode captured pulses back to frames."""

from __future__ import annotations

import copy

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
            levels += [enc.one_mark if bit else enc.zero_mark, -enc.space_after(bit)]
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
        if section.bits is None:
            if frame.nbits:
                raise ValueError(
                    f"bitless section {frame.section!r} takes an empty frame"
                )
            bits = []
        elif not frame.nbits:
            raise ValueError(f"section {frame.section!r} needs data")
        else:
            bits = _frame_bits(frame, section)
        levels += _section_levels(section, bits)
    merged = _merge(levels)
    if merged[-1] > 0:
        merged.append(-protocol.trailer_gap)
    return Signal(protocol.carrier, tuple(abs(d) for d in merged))


class DecodeError(ValueError):
    """A pulse train does not match the protocol description."""

    def __init__(self, index, expected, got):
        self.index = index
        self.expected = expected
        self.got = got
        super().__init__(f"pulse {index}: expected {expected}, got {got}")


def _kind(is_mark):
    return "mark" if is_mark else "space"


class _Cursor:
    """Walks a pulse train; a pulse may be consumed in several pieces.

    Marks sit at even indices, spaces at odd ones.  ``rest`` is what is left
    of the current pulse, after demodulator compensation.
    """

    def __init__(self, protocol, pulses):
        self.tol = protocol.tolerance
        self.excess = excess = protocol.mark_excess
        self.p = [
            d - excess if i % 2 == 0 else d + excess for i, d in enumerate(pulses)
        ]
        self.i = 0
        self.rest = self.p[0]

    def clone(self):
        return copy.copy(self)

    def commit(self, other):
        self.i, self.rest = other.i, other.rest

    def at_end(self):
        return self.i >= len(self.p)

    def is_mark(self):
        return self.i % 2 == 0

    def done(self):
        """Nothing left but, at most, one final space (the trailing silence)."""
        return self.at_end() or (self.i == len(self.p) - 1 and not self.is_mark())

    def match(self, measured, nominal):
        """``measured`` is compensated; the tolerance applies, as in
        IRrecv::matchMark / matchSpace, to the nominal plus the excess for a
        mark and minus it for a space."""
        base = nominal + self.excess if self.is_mark() else nominal - self.excess
        return abs(measured - nominal) <= self.tol * base

    def _advance(self):
        self.i += 1
        self.rest = self.p[self.i] if self.i < len(self.p) else 0

    def _check_polarity(self, is_mark, expected):
        if self.is_mark() != is_mark:
            raise DecodeError(
                self.i, expected, f"{_kind(self.is_mark())} {round(self.rest)}"
            )

    def take(self, is_mark, nominal, partial=False, quantum=0):
        """Consume ``nominal`` µs of the given level.

        ``partial`` lets a longer pulse keep its leftover for what follows.
        ``quantum`` (a Manchester half) means the pulse may be either
        ``nominal`` alone or ``nominal + quantum``; the nearer one wins.
        """
        expected = f"{_kind(is_mark)} {nominal}"
        if self.at_end():
            if is_mark:
                raise DecodeError(self.i, expected, "end of signal")
            return  # captures often drop the trailing silence
        self._check_polarity(is_mark, expected)
        r = self.rest
        if quantum:
            merged = nominal + quantum
            if abs(r - merged) < abs(r - nominal):
                if not self.match(r, merged):
                    raise DecodeError(self.i, f"{expected} or {merged}", round(r))
                self.rest = r * quantum / merged
                return
        if self.match(r, nominal):
            self._advance()
            return
        if partial and r > nominal:
            k = round(r / nominal)
            if k >= 2 and abs(r - k * nominal) <= self.tol * k * nominal:
                self.rest = r * (k - 1) / k
            else:
                self.rest = r - nominal
            return
        raise DecodeError(self.i, expected, round(r))

    def classify(self, is_mark, zero, one):
        """Consume a whole pulse and return the bit whose nominal it matches."""
        expected = f"{_kind(is_mark)} {zero} or {one}"
        if self.at_end():
            raise DecodeError(self.i, expected, "end of signal")
        self._check_polarity(is_mark, expected)
        r = self.rest
        bit = 1 if abs(r - one) < abs(r - zero) else 0
        if not self.match(r, one if bit else zero):
            raise DecodeError(self.i, expected, round(r))
        self._advance()
        return bit

    def gap_ahead(self, gap):
        if self.at_end():
            return True
        if self.is_mark():
            return False
        # The final space of a capture is idle time, not a measured gap.
        return self.i == len(self.p) - 1 or self.rest >= (1 - self.tol) * gap

    def take_gap(self, gap):
        if not self.gap_ahead(gap):
            raise DecodeError(self.i, f"space >= {gap}", round(self.rest))
        if not self.at_end():
            self._advance()


def _read_bit(cur, enc):
    if isinstance(enc, PulseDistance):
        cur.take(True, enc.mark)
        return cur.classify(False, enc.zero_space, enc.one_space)
    if isinstance(enc, PulseWidth):
        bit = cur.classify(True, enc.zero_mark, enc.one_mark)
        cur.take(False, enc.space_after(bit), partial=True)
        return bit
    if cur.at_end():
        raise DecodeError(cur.i, "Manchester bit", "end of signal")
    first_is_mark = cur.is_mark()
    cur.take(first_is_mark, enc.half, partial=True)
    cur.take(not first_is_mark, enc.half, partial=True)
    return 1 if first_is_mark == enc.one_is_mark_first else 0


def _can_read_bit(cur, enc):
    try:
        _read_bit(cur.clone(), enc)
    except DecodeError:
        return False
    return True


def _section_end(cur, section):
    """A cursor past the footer and gap if the section's bits end here, else None."""
    look = cur.clone()
    try:
        for k, d in enumerate(section.footer):
            look.take(k % 2 == 0, d, partial=True)
        if section.gap:
            look.take_gap(section.gap)
            return look
    except DecodeError:
        return None
    if look.done() or not _can_read_bit(cur, section.bits):
        return look
    return None


def _parse_bitless(cur, name, section):
    for k, d in enumerate(section.header):
        cur.take(k % 2 == 0, d, partial=True)
    for k, d in enumerate(section.footer):
        cur.take(k % 2 == 0, d, partial=True)
    if section.gap:
        cur.take_gap(section.gap)
    return Frame(name, b"", 0)


def _parse_section(cur, name, section):
    if section.bits is None:
        return _parse_bitless(cur, name, section)
    enc = section.bits
    for k, d in enumerate(section.header):
        last = k == len(section.header) - 1
        quantum = enc.half if last and isinstance(enc, Manchester) else 0
        cur.take(k % 2 == 0, d, partial=True, quantum=quantum)
    start = cur.i
    bits = []
    while True:
        end = _section_end(cur, section)
        if end is not None:
            cur.commit(end)
            break
        bits.append(_read_bit(cur, enc))
    if not bits:
        raise DecodeError(start, f"at least one bit of section {name!r}", "none")
    return Frame(name, _pack(bits, section.lsb_first), len(bits))


def decode(protocol, pulses, expected=None):
    """Decode unsigned µs pulses (mark first) into frames.

    With ``expected`` (section names) the sections are parsed strictly in
    that order; without it, sections with a header are tried greedily.
    """
    pulses = list(pulses)
    if not pulses:
        raise ValueError("decode needs at least one pulse")
    for i, d in enumerate(pulses):
        if isinstance(d, bool) or not isinstance(d, int) or d <= 0:
            raise ValueError(f"pulses[{i}] must be a positive integer (µs), got {d!r}")
    cur = _Cursor(protocol, pulses)
    frames = []
    if expected is not None:
        for name in expected:
            if name not in protocol.sections:
                raise ValueError(
                    f"unknown section {name!r} for protocol {protocol.name!r}"
                )
            frames.append(_parse_section(cur, name, protocol.sections[name]))
    else:
        headed = [(n, s) for n, s in protocol.sections.items() if s.header]
        if not headed:
            raise ValueError(
                f"protocol {protocol.name!r} has no section with a header; pass expected="
            )
        while not cur.done():
            for name, section in headed:
                look = cur.clone()
                try:
                    frame = _parse_section(look, name, section)
                except DecodeError:
                    continue
                cur.commit(look)
                frames.append(frame)
                break
            else:
                raise DecodeError(
                    cur.i,
                    "header of " + " or ".join(repr(n) for n, _ in headed),
                    round(cur.rest),
                )
    if not cur.done():
        raise DecodeError(cur.i, "end of signal", round(cur.rest))
    return frames
