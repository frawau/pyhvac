"""Declarative description of an IR physical layer.

All durations are integer microseconds; carrier frequencies are integer Hz.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Union


def _check_int(name, value, unit, minimum=1):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer ({unit}), got {value!r}")
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum} {unit}, got {value}")


@dataclass(frozen=True)
class PulseDistance:
    """Constant mark; the following space carries the bit."""

    mark: int
    zero_space: int
    one_space: int

    def __post_init__(self):
        for name in ("mark", "zero_space", "one_space"):
            _check_int(name, getattr(self, name), "µs")
        if self.zero_space == self.one_space:
            raise ValueError("zero_space and one_space must differ")


@dataclass(frozen=True)
class PulseWidth:
    """The mark carries the bit; constant space."""

    zero_mark: int
    one_mark: int
    space: int

    def __post_init__(self):
        for name in ("zero_mark", "one_mark", "space"):
            _check_int(name, getattr(self, name), "µs")
        if self.zero_mark == self.one_mark:
            raise ValueError("zero_mark and one_mark must differ")


@dataclass(frozen=True)
class Manchester:
    """Bi-phase: each bit is two half-periods of opposite level."""

    half: int
    one_is_mark_first: bool = True

    def __post_init__(self):
        _check_int("half", self.half, "µs")


BitEncoding = Union[PulseDistance, PulseWidth, Manchester]


@dataclass(frozen=True)
class Section:
    """Template for one burst on the wire: header, bits, footer, gap.

    ``header`` and ``footer`` alternate mark, space, ... starting with a mark.
    With ``bits=None`` the section is a fixed burst (a preamble or leader)
    that carries no data and is sent with an empty frame.
    """

    bits: Optional[BitEncoding]
    header: Tuple[int, ...] = ()
    footer: Tuple[int, ...] = ()
    gap: int = 0
    lsb_first: bool = True

    def __post_init__(self):
        if self.bits is not None and not isinstance(
            self.bits, (PulseDistance, PulseWidth, Manchester)
        ):
            raise ValueError(f"unknown bit encoding {self.bits!r}")
        object.__setattr__(self, "header", tuple(self.header))
        object.__setattr__(self, "footer", tuple(self.footer))
        for i, d in enumerate(self.header):
            _check_int(f"header[{i}]", d, "µs")
        for i, d in enumerate(self.footer):
            _check_int(f"footer[{i}]", d, "µs")
        _check_int("gap", self.gap, "µs", minimum=0)
        if self.bits is None and not (self.header or self.footer or self.gap):
            raise ValueError("a bitless section needs a header, a footer or a gap")
        if isinstance(self.bits, PulseDistance) and not self.footer:
            # Without a closing mark the last bit's space merges into the gap
            # and its value cannot be recovered.
            raise ValueError("a PulseDistance section needs a footer mark")


@dataclass(frozen=True)
class Protocol:
    name: str
    sections: Dict[str, Section]
    carrier: int = 38000
    tolerance: float = 0.25
    mark_excess: int = 50
    trailer_gap: int = 100_000

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("a protocol needs a name")
        sections = dict(self.sections)
        if not sections:
            raise ValueError("a protocol needs at least one section")
        for key, section in sections.items():
            if not isinstance(key, str) or not key:
                raise ValueError(f"section names must be non-empty strings: {key!r}")
            if not isinstance(section, Section):
                raise ValueError(f"section {key!r} is not a Section: {section!r}")
        object.__setattr__(self, "sections", sections)
        _check_int("carrier", self.carrier, "Hz")
        if isinstance(self.tolerance, bool) or not 0 < self.tolerance < 0.5:
            raise ValueError(f"tolerance must be in (0, 0.5), got {self.tolerance!r}")
        _check_int("mark_excess", self.mark_excess, "µs", minimum=0)
        _check_int("trailer_gap", self.trailer_gap, "µs")


@dataclass(frozen=True)
class Frame:
    """Payload for one section. ``nbits`` defaults to all bits of ``data``.

    An empty frame (``data=b""``, ``nbits=0``) is sent with a bitless section.
    """

    section: str
    data: bytes
    nbits: Optional[int] = None

    def __post_init__(self):
        data = bytes(self.data)
        object.__setattr__(self, "data", data)
        if not data:
            if self.nbits not in (None, 0):
                raise ValueError(f"an empty frame has 0 bits, not {self.nbits}")
            object.__setattr__(self, "nbits", 0)
            return
        nbits = 8 * len(data) if self.nbits is None else self.nbits
        _check_int("nbits", nbits, "bits")
        if not 8 * (len(data) - 1) < nbits <= 8 * len(data):
            raise ValueError(
                f"nbits={nbits} must fall within the last of {len(data)} data bytes"
            )
        object.__setattr__(self, "nbits", nbits)


@dataclass(frozen=True)
class Signal:
    """Mark, space, mark, space, ... in µs; starts with a mark, ends with a space."""

    carrier: int
    pulses: Tuple[int, ...]

    def __post_init__(self):
        _check_int("carrier", self.carrier, "Hz")
        pulses = tuple(self.pulses)
        if not pulses or len(pulses) % 2:
            raise ValueError("a signal needs a non-empty, even number of pulses")
        for i, d in enumerate(pulses):
            _check_int(f"pulses[{i}]", d, "µs")
        object.__setattr__(self, "pulses", pulses)
