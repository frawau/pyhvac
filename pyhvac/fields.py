"""Declarative frame layouts: named bit fields over a fixed skeleton, and
the checksum functions protocols use.

Bits are numbered LSB-first across the frame's logical bytes: bit ``i`` is
bit ``i % 8`` of byte ``i // 8`` (the bytes of ``Frame.data``, before the
wire bit order is applied).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import reduce
from types import MappingProxyType
from typing import Callable, Mapping, Optional


def bit_reverse(byte):
    return int(f"{byte:08b}"[::-1], 2)


@dataclass(frozen=True)
class Field:
    offset: int
    width: int
    values: Optional[Mapping] = None
    encode: Optional[Callable] = None

    def __post_init__(self):
        if self.offset < 0 or self.width < 1:
            raise ValueError(f"bad field offset/width {self.offset}/{self.width}")
        if self.values is not None and self.encode is not None:
            raise ValueError("a field takes a value table or an encoder, not both")
        if self.values is not None:
            object.__setattr__(self, "values", MappingProxyType(dict(self.values)))

    @classmethod
    def at(cls, byte, bit, width, **kw):
        return cls(byte * 8 + bit, width, **kw)

    @property
    def bits(self):
        return range(self.offset, self.offset + self.width)

    def to_int(self, name, value):
        if self.values is not None:
            if value not in self.values:
                raise ValueError(f"field {name!r} has no value {value!r}")
            raw = self.values[value]
        elif self.encode is not None:
            raw = self.encode(value)
        elif isinstance(value, (bool, int)):
            raw = int(value)
        else:
            raise ValueError(f"field {name!r} needs an int, got {value!r}")
        if not 0 <= raw < 1 << self.width:
            raise ValueError(f"field {name!r}: {raw} does not fit {self.width} bits")
        return raw

    def from_int(self, raw):
        if self.values is None:
            return raw
        for value, code in self.values.items():
            if code == raw:
                return value
        return raw


def _get(data, bit):
    return (data[bit // 8] >> (bit % 8)) & 1


def _set(data, bit, value):
    if value:
        data[bit // 8] |= 1 << (bit % 8)
    else:
        data[bit // 8] &= ~(1 << (bit % 8)) & 0xFF


class Layout:
    def __init__(self, skeleton, fields, checksum=None):
        self.skeleton = bytes(skeleton)
        self.fields = MappingProxyType(dict(fields))
        self.checksum = checksum
        size = 8 * len(self.skeleton)
        owner = {}
        for name, f in self.fields.items():
            for bit in f.bits:
                if bit >= size:
                    raise ValueError(f"field {name!r} runs past the skeleton")
                if bit in owner:
                    raise ValueError(f"fields {owner[bit]!r} and {name!r} overlap")
                owner[bit] = name
        if checksum is not None:
            for byte in checksum.positions():
                if byte >= len(self.skeleton):
                    raise ValueError("checksum position past the skeleton")
                clash = {owner[b] for b in range(8 * byte, 8 * byte + 8) if b in owner}
                if clash:
                    raise ValueError(f"checksum byte {byte} overlaps fields {clash}")

    def write_raw(self, data, name, raw):
        """Write the int ``raw`` into field ``name`` of ``data``."""
        for k, bit in enumerate(self.fields[name].bits):
            _set(data, bit, (raw >> k) & 1)

    def read_raw(self, data, name):
        """The int stored in field ``name`` of ``data``."""
        return sum(_get(data, bit) << k for k, bit in enumerate(self.fields[name].bits))

    def build(self, checksum=True, **values):
        data = bytearray(self.skeleton)
        for name, value in values.items():
            if name not in self.fields:
                raise ValueError(f"unknown field {name!r}")
            self.write_raw(data, name, self.fields[name].to_int(name, value))
        if checksum and self.checksum is not None:
            self.checksum.apply(data)
        return data

    def read(self, data):
        return {
            name: f.from_int(self.read_raw(data, name))
            for name, f in self.fields.items()
        }


@dataclass(frozen=True)
class Checksum:
    """A checksum over ``data[start:end]`` written at ``data[at]``."""

    start: int
    end: int
    at: int
    reverse: bool = False

    def _input(self, data):
        seg = bytes(data[self.start : self.end])
        return bytes(bit_reverse(b) for b in seg) if self.reverse else seg

    def compute(self, data):
        raise NotImplementedError

    def positions(self):
        return {self.at}

    def apply(self, data):
        data[self.at] = self.compute(data)

    def check(self, data):
        return data[self.at] == self.compute(data)


@dataclass(frozen=True)
class Sum8(Checksum):
    def compute(self, data):
        return sum(self._input(data)) & 0xFF


@dataclass(frozen=True)
class NibbleSum(Checksum):
    def compute(self, data):
        return sum((b >> 4) + (b & 0x0F) for b in self._input(data)) & 0xFF


@dataclass(frozen=True)
class Xor8(Checksum):
    def compute(self, data):
        return reduce(lambda a, b: a ^ b, self._input(data), 0)


@dataclass(frozen=True)
class Crc8(Checksum):
    """CRC-8, MSB-first; ``reflect`` reflects input bytes and the result."""

    poly: int = 0x07
    init: int = 0
    reflect: bool = False

    def compute(self, data):
        crc = self.init
        for byte in self._input(data):
            crc ^= bit_reverse(byte) if self.reflect else byte
            for _ in range(8):
                crc = ((crc << 1) ^ self.poly) & 0xFF if crc & 0x80 else crc << 1 & 0xFF
        return bit_reverse(crc) if self.reflect else crc


@dataclass(frozen=True)
class InvertedPairs:
    """Every second byte of data[start:end] is the complement of the one before."""

    start: int
    end: int

    def positions(self):
        return set(range(self.start + 1, self.end, 2))

    def apply(self, data):
        for i in range(self.start, self.end - 1, 2):
            data[i + 1] = ~data[i] & 0xFF

    def check(self, data):
        return all(
            data[i + 1] == ~data[i] & 0xFF for i in range(self.start, self.end - 1, 2)
        )
