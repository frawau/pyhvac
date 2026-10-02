"""Devices served from a SmartIR climate code file instead of a protocol.

A SmartIR file holds one learned code per state: ``commands["off"]`` and
``commands[mode][fan][swing?][temperature]``. Codes are Broadlink packets
(base64), or signed µs lists (ESPHome: JSON, LOOKin: space separated).
Xiaomi's compressed formats cannot be turned into pulses.

The file is fetched from upstream SmartIR ``master`` on first use (upstream
is responsible for its content) and cached; the cached copy is used when
the fetch fails. The first ``capabilities`` or ``encode`` of a device may
block on the network for up to TIMEOUT seconds: async callers run it in an
executor. Temperatures stay °C: a file keyed in °F offers the °C
setpoint of each of its °F keys.
"""

import base64
import binascii
import json
import os
import struct
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..device import Command, Device
from ..ir.formats import _BROADLINK_TICK_DEN, _BROADLINK_TICK_NUM
from ..ir.model import Signal
from ..state import (
    Capabilities,
    Choice,
    HvacState,
    SWING_KEYWORDS,
    TemperatureRange,
    fahrenheit,
)

URL = "https://raw.githubusercontent.com/smartHomeHub/SmartIR/master/codes/climate/{}.json"
CARRIER = 38000
TIMEOUT = 10  # s, per fetch
FINAL_SPACE = 100000  # µs, closes a learned code that ends on a mark
FAHRENHEIT_ABOVE = 50  # a file whose keys go above this is keyed in °F
MODES = {
    "auto": "auto",
    "heat_cool": "auto",
    "cool": "cool",
    "heat": "heat",
    "dry": "dry",
    "fan_only": "fan",
    "fan": "fan",
}


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


def walk(commands):
    """(Key, stored code) for every leaf of a commands tree."""
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
                else:
                    yield Key(mode, fan, None, _temperature(k)), sub3


def fahrenheit_keyed(data):
    return (data.get("maxTemperature") or 0) > FAHRENHEIT_ABOVE


def cache_dir():
    """``$PYHVAC_CACHE``, else ``$XDG_CACHE_HOME/pyhvac``, else ~/.cache/pyhvac."""
    if os.environ.get("PYHVAC_CACHE"):
        return Path(os.environ["PYHVAC_CACHE"])
    base = os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache"
    return Path(base) / "pyhvac"


def fetch(url):
    """The bytes at ``url`` (the seam tests replace)."""
    with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
        return response.read()


def load(number, path=None):
    """A SmartIR climate file as parsed JSON: ``path`` if given, else
    upstream master (cached), else the cached copy."""
    if path is not None:
        return json.loads(Path(path).read_text())
    url = URL.format(number)
    cached = cache_dir() / "smartir" / "climate" / f"{number}.json"
    try:
        raw = fetch(url)
        data = json.loads(raw)
    except (OSError, ValueError) as exc:
        if cached.exists():
            return json.loads(cached.read_text())
        raise OSError(f"cannot fetch SmartIR climate file {url}: {exc}") from exc
    try:
        cached.parent.mkdir(parents=True, exist_ok=True)
        partial = cached.with_name(f"{cached.name}.{os.getpid()}.tmp")
        partial.write_bytes(raw)
        partial.replace(cached)  # readers never see a half-written file
    except OSError:
        pass  # caching is best effort
    return data


def _levels(labels, keywords, aliases):
    """Canonical value -> file label: keywords by name, the rest "1".."n"."""
    out, n = {}, 0
    for label in labels:
        name = aliases.get(label.casefold(), label.casefold())
        if name in keywords and name not in out:
            out[name] = label
        else:
            n += 1
            out[str(n)] = label
    return out


class TableDevice(Device):
    """Serves the learned codes of upstream SmartIR climate file ``variant``
    (its number). A state with no code raises; it never guesses."""

    def __init__(self, brand, model, variant=None, path=None):
        super().__init__(brand, model)
        if variant is None:
            raise ValueError(f"{brand}/{model}: a table device needs variant=")
        self.variant = str(variant)
        self._path = path
        self._data = None

    def _load(self):
        if self._data is None:
            data = load(self.variant, self._path)
            self._fahrenheit = fahrenheit_keyed(data)
            codes = {}
            for key, stored in walk(data.get("commands", {})):
                codes[key] = stored
            self._codes = codes
            self._controller = data.get("supportedController", "")
            self._encoding = data.get("commandsEncoding", "")
            self._modes = {}
            for name in data.get("operationModes", ()):
                if name in MODES and MODES[name] not in self._modes:
                    self._modes[MODES[name]] = name
            self._fans = _levels(data.get("fanModes", ()), ("auto",), {})
            self._swings = _levels(
                data.get("swingModes", ()), SWING_KEYWORDS, {"on": "swing"}
            )
            temps = sorted(
                {
                    self._celsius(k.temperature)
                    for k in codes
                    if k.temperature is not None
                }
            )
            if not self._modes or not temps:
                raise ValueError(f"SmartIR climate file {self.variant} has no codes")
            self._capabilities = Capabilities(
                modes=tuple(self._modes),
                temperature=TemperatureRange(
                    temps[0],
                    temps[-1],
                    tuple(sorted({round(t * 10) % 10 for t in temps})),
                    tuple(temps),
                ),
                fan=Choice(tuple(self._fans), self._fans) if self._fans else None,
                swing_v=(
                    Choice(tuple(self._swings), self._swings) if self._swings else None
                ),
            )
            self._data = data
        return self._data

    def _celsius(self, t):
        return round((t - 32) * 5 / 9, 1) if self._fahrenheit else float(t)

    @property
    def capabilities(self):
        self._load()
        return self._capabilities

    def encode(self, previous, target, actions=()):
        self._load()
        actions = self._check_actions(actions)
        target = self.normalise(target)
        if not target.power:
            key = Key("off", None, None, None)
        else:
            t = target.temperature
            key = Key(
                self._modes[target.mode],
                self._fans.get(target.fan),
                self._swings.get(target.swing_v),
                float(fahrenheit(t)) if self._fahrenheit else t,
            )
        if key not in self._codes:
            raise KeyError(f"SmartIR climate file {self.variant} has no code for {key}")
        pulses = to_pulses(self._codes[key], self._controller, self._encoding)
        if len(pulses) % 2:
            pulses.append(FINAL_SPACE)
        return Command(Signal(CARRIER, tuple(pulses)), target)
