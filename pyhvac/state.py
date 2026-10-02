"""Device-independent HVAC state and device capability descriptions.

Temperatures are degrees Celsius with at most one decimal.
"""

from __future__ import annotations

import math
from collections.abc import Mapping as _Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Optional, Tuple

MODES = ("auto", "cool", "heat", "dry", "fan")
FAN_KEYWORDS = ("auto",)
SWING_KEYWORDS = ("off", "swing", "auto")


def _is_level(value):
    """A level or position: a positive decimal string such as "1" or "12"."""
    return isinstance(value, str) and value.isdigit() and int(value) > 0


def _check_setting(name, value, keywords):
    if not (value in keywords or _is_level(value)):
        raise ValueError(
            f"{name} must be one of {keywords} or a level '1'..'N', got {value!r}"
        )


def _tenths(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number (°C), got {value!r}")
    if not math.isfinite(value * 10):
        raise ValueError(f"{name} must be a finite number (°C), got {value!r}")
    return round(value * 10)


@dataclass(frozen=True)
class HvacState:
    power: bool
    mode: str
    temperature: float
    fan: str = "auto"
    swing_v: str = "off"
    swing_h: str = "off"
    features: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.power, bool):
            raise ValueError(f"power must be a bool, got {self.power!r}")
        if self.mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}, got {self.mode!r}")
        object.__setattr__(
            self, "temperature", _tenths(self.temperature, "temperature") / 10
        )
        _check_setting("fan", self.fan, FAN_KEYWORDS)
        _check_setting("swing_v", self.swing_v, SWING_KEYWORDS)
        _check_setting("swing_h", self.swing_h, SWING_KEYWORDS)
        features = dict(self.features)
        for key, value in features.items():
            if not isinstance(key, str) or not key:
                raise ValueError(f"feature names must be non-empty strings: {key!r}")
            if not isinstance(value, (bool, str)):
                raise ValueError(f"feature {key!r} must be a bool or str: {value!r}")
        object.__setattr__(self, "features", MappingProxyType(features))

    def __hash__(self):
        return hash(
            (
                self.power,
                self.mode,
                self.temperature,
                self.fan,
                self.swing_v,
                self.swing_h,
                tuple(sorted(self.features.items())),
            )
        )

    def to_dict(self):
        return {
            "power": self.power,
            "mode": self.mode,
            "temperature": self.temperature,
            "fan": self.fan,
            "swing_v": self.swing_v,
            "swing_h": self.swing_h,
            "features": dict(self.features),
        }

    @classmethod
    def from_dict(cls, data):
        """Rebuild a state from ``to_dict()`` output.

        Unknown keys are ignored. Anything malformed (missing or invalid
        fields, a non-mapping) raises ``ValueError``, so a caller restoring
        persisted state can fall back to an unknown previous state.
        """
        if not isinstance(data, _Mapping):
            raise ValueError(f"a state must be a mapping, got {type(data).__name__}")
        missing = [k for k in ("power", "mode", "temperature") if k not in data]
        if missing:
            raise ValueError(f"state is missing {missing}")
        features = data.get("features", {})
        if not isinstance(features, _Mapping):
            raise ValueError(f"features must be a mapping, got {features!r}")
        known = ("power", "mode", "temperature", "fan", "swing_v", "swing_h")
        kwargs = {k: data[k] for k in known if k in data}
        return cls(features=dict(features), **kwargs)


def fahrenheit(celsius):
    """The whole °F a °C setpoint stands for (edge conversion only)."""
    return round(celsius * 9 / 5 + 32)


@dataclass(frozen=True)
class TemperatureRange:
    """Allowed setpoints: [min, max] in °C, with the listed tenths only, or
    exactly ``values`` (sorted °C setpoints, one decimal) when given."""

    min: float
    max: float
    decimals: Tuple[int, ...] = (0,)
    values: Optional[Tuple[float, ...]] = None

    @classmethod
    def fahrenheit(cls, lo_f, hi_f):
        """One °C setpoint per whole °F from ``lo_f`` to ``hi_f``: for a unit
        that steps in °F, reachable while the state stays in °C."""
        values = tuple(round((f - 32) * 5 / 9, 1) for f in range(lo_f, hi_f + 1))
        decimals = tuple(sorted({round(v * 10) % 10 for v in values}))
        return cls(values[0], values[-1], decimals, values)

    def __post_init__(self):
        if self.values is not None:
            tenths = [_tenths(v, "values") for v in self.values]
            if (
                not tenths
                or tenths != sorted(set(tenths))
                or any(abs(t - v * 10) > 1e-6 for t, v in zip(tenths, self.values))
            ):
                raise ValueError(
                    f"values must be sorted unique setpoints with one decimal, "
                    f"got {self.values!r}"
                )
            if tenths[0] < round(self.min * 10) or tenths[-1] > round(self.max * 10):
                raise ValueError(
                    f"values must lie within [{self.min}, {self.max}], "
                    f"got {self.values!r}"
                )
            object.__setattr__(self, "values", tuple(t / 10 for t in tenths))
        decimals = tuple(sorted(self.decimals))
        if (
            not decimals
            or len(set(decimals)) != len(decimals)
            or any(isinstance(d, bool) or not isinstance(d, int) for d in decimals)
            or not all(0 <= d <= 9 for d in decimals)
        ):
            raise ValueError(
                f"decimals must be unique integers 0-9, got {self.decimals!r}"
            )
        object.__setattr__(self, "decimals", decimals)
        lo, hi = _tenths(self.min, "min"), _tenths(self.max, "max")
        if lo > hi:
            raise ValueError(f"min {self.min} is above max {self.max}")
        for name, t in (("min", lo), ("max", hi)):
            if t % 10 not in decimals:
                raise ValueError(
                    f"{name} must use one of the allowed decimals {decimals}"
                )
        object.__setattr__(self, "min", lo / 10)
        object.__setattr__(self, "max", hi / 10)

    def snap(self, celsius):
        """Nearest allowed setpoint, ties to the lower one, clamped to [min, max]."""
        lo, hi = round(self.min * 10), round(self.max * 10)
        t = min(max(_tenths(celsius, "temperature"), lo), hi)
        if self.values is not None:
            return min(self.values, key=lambda v: (abs(round(v * 10) - t), v))
        base = (t // 10) * 10
        candidates = [
            b + d
            for b in (base - 10, base, base + 10)
            for d in self.decimals
            if lo <= b + d <= hi
        ]
        return min(candidates, key=lambda v: (abs(v - t), v)) / 10


@dataclass(frozen=True)
class Choice:
    """Allowed canonical values, in display order, with optional labels."""

    values: Tuple
    labels: Mapping = field(default_factory=dict)

    def __post_init__(self):
        values = tuple(self.values)
        if not values or len(set(values)) != len(values):
            raise ValueError(f"a choice needs unique values, got {self.values!r}")
        labels = dict(self.labels)
        unknown = [k for k in labels if k not in values]
        if unknown:
            raise ValueError(f"labels for unknown values: {unknown!r}")
        object.__setattr__(self, "values", values)
        object.__setattr__(self, "labels", MappingProxyType(labels))

    def label(self, value):
        return self.labels.get(value, str(value))


BOOL = Choice((False, True))


@dataclass(frozen=True)
class Capabilities:
    modes: Tuple[str, ...]
    temperature: TemperatureRange
    fan: Optional[Choice] = None
    swing_v: Optional[Choice] = None
    swing_h: Optional[Choice] = None
    features: Mapping[str, Choice] = field(default_factory=dict)
    actions: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self):
        modes = tuple(self.modes)
        if not modes or any(m not in MODES for m in modes):
            raise ValueError(f"modes must be a non-empty subset of {MODES}: {modes!r}")
        object.__setattr__(self, "modes", modes)
        object.__setattr__(self, "features", MappingProxyType(dict(self.features)))
        object.__setattr__(self, "actions", MappingProxyType(dict(self.actions)))
