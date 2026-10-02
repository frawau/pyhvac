"""A SmartIR climate code file as keys and µs pulses.

SmartIR stores one learned code per state: ``commands["off"]`` and
``commands[mode][fan][swing?][temperature]``. Codes are Broadlink packets
(base64), or signed µs lists (ESPHome: JSON, LOOKin: space separated).
Xiaomi's compressed formats cannot be turned into pulses.

Development tool only: the files are analysed to find, fix or port the
pyhvac protocol that generates their codes; pyhvac never serves them.
"""

import base64
import binascii
import json
import struct
from dataclasses import dataclass, field
from typing import Optional, Tuple

from pyhvac.ir.formats import _BROADLINK_TICK_DEN, _BROADLINK_TICK_NUM


class UnsupportedFormat(ValueError):
    """A code format that cannot be turned into pulses."""


@dataclass(frozen=True)
class Key:
    mode: str  # SmartIR's mode name, or "off"
    fan: Optional[str]
    swing: Optional[str]
    temperature: Optional[float]


def _broadlink_pulses(packet):
    """µs pulses of a Broadlink IR packet, leniently: learned codes in the
    wild are often truncated (declared length past the data, a cut 2-byte
    value); keep what is there."""
    if len(packet) < 4 or packet[0] != 0x26:
        raise ValueError("not a Broadlink IR packet")
    (length,) = struct.unpack("<H", packet[2:4])
    body = packet[4 : 4 + length]
    pulses, i = [], 0
    while i < len(body):
        ticks = body[i]
        i += 1
        if ticks == 0:
            if i + 2 > len(body):
                break
            (ticks,) = struct.unpack(">H", body[i : i + 2])
            i += 2
        pulses.append(round(ticks * _BROADLINK_TICK_DEN / _BROADLINK_TICK_NUM))
    return pulses


def to_pulses(code, controller, encoding):
    """Unsigned µs pulses (mark first) for one stored code."""
    if controller == "Xiaomi":
        raise UnsupportedFormat("Xiaomi compressed IR codes")
    if not isinstance(code, (str, list)):
        raise ValueError(f"not a code: {code!r}")
    if encoding == "Base64":
        text = code.strip()
        try:
            packet = base64.b64decode(text + "=" * (-len(text) % 4), validate=False)
        except (binascii.Error, ValueError) as exc:
            raise ValueError(f"bad base64: {exc}") from None
        pulses = _broadlink_pulses(packet)
    elif isinstance(code, list):
        pulses = code
    else:
        text = code.strip()
        pulses = json.loads(text) if text.startswith("[") else text.split()
    pulses = [abs(int(p)) for p in pulses]
    if not pulses or any(p <= 0 for p in pulses):
        raise ValueError("empty code or a zero-length pulse")
    return pulses


def _temperature(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def walk(commands, swings=()):
    """(Key, stored code) for every leaf of a commands tree. Under a fan,
    a key in ``swings`` is a swing level even when it holds a code (no
    temperature level)."""
    for mode, sub in commands.items():
        if not isinstance(sub, dict):
            yield Key(mode, None, None, None), sub
            continue
        for fan, sub2 in sub.items():
            if not isinstance(sub2, dict):
                yield Key(mode, fan, None, None), sub2
                continue
            for k, sub3 in sub2.items():
                if isinstance(sub3, dict):  # a swing level
                    for t, code in sub3.items():
                        yield Key(mode, fan, k, _temperature(t)), code
                elif k in swings and _temperature(k) is None:
                    yield Key(mode, fan, k, None), sub3
                else:
                    yield Key(mode, fan, None, _temperature(k)), sub3


@dataclass(frozen=True)
class Code:
    key: Key
    pulses: Tuple[int, ...]


@dataclass(frozen=True)
class SmartIRFile:
    number: int
    manufacturer: str
    models: Tuple[str, ...]
    controller: str
    encoding: str
    min_temperature: Optional[float]
    max_temperature: Optional[float]
    precision: Optional[float]
    modes: Tuple[str, ...]
    fans: Tuple[str, ...]
    swings: Tuple[str, ...]
    codes: Tuple[Code, ...] = field(repr=False)
    skipped: int  # codes that could not be turned into pulses
    unsupported: Optional[str] = None  # why no code could be read at all


def parse(number, data):
    controller = data.get("supportedController", "")
    encoding = data.get("commandsEncoding", "")
    codes, skipped, unsupported = [], 0, None
    for key, stored in walk(data.get("commands", {}), data.get("swingModes", ())):
        try:
            codes.append(Code(key, tuple(to_pulses(stored, controller, encoding))))
        except UnsupportedFormat as exc:
            unsupported = str(exc)
            skipped += 1
        except (ValueError, TypeError):
            skipped += 1
    return SmartIRFile(
        number=number,
        manufacturer=data.get("manufacturer", ""),
        models=tuple(data.get("supportedModels", ())),
        controller=controller,
        encoding=encoding,
        min_temperature=data.get("minTemperature"),
        max_temperature=data.get("maxTemperature"),
        precision=data.get("precision"),
        modes=tuple(data.get("operationModes", ())),
        fans=tuple(data.get("fanModes", ())),
        swings=tuple(data.get("swingModes", ())),
        codes=tuple(codes),
        skipped=skipped,
        unsupported=unsupported if not codes else None,
    )
