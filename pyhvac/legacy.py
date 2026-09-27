"""Adapter from the old mutable HVAC classes to the stateless Device API."""

from __future__ import annotations

from .device import Command, Device
from .ir.model import Signal
from .plugins.hvaclib import IRGHVAC
from .state import Capabilities, Choice, HvacState, TemperatureRange

FAN_RANK = ("lowest", "low", "medium", "high", "highest")
SWING_KEYWORDS = {"off": "off", "on": "swing", "swing": "swing", "auto": "auto"}
HSWING_RANK = (
    "far left",
    "left",
    "close left",
    "middle",
    "close right",
    "right",
    "far right",
)
TRAILER_GAP = 100_000  # µs, appended when legacy pulses end on a mark


def _swing_choice(values, rank=None):
    """Canonical swing choice; labels hold the old names for every value."""
    keywords, positions = [], []
    for old in values:
        if old in SWING_KEYWORDS:
            keywords.append((SWING_KEYWORDS[old], old))
        else:
            positions.append(old)
    if rank is not None:
        known = sorted((p for p in positions if p in rank), key=rank.index)
        positions = known + [p for p in positions if p not in rank]
    canonical = keywords + [(str(i), old) for i, old in enumerate(positions, 1)]
    return Choice(tuple(c for c, _ in canonical), dict(canonical))


def _fan_choice(values):
    levels = []
    for old in values:
        if old != "auto" and old not in FAN_RANK:
            raise ValueError(f"unknown fan speed {old!r}")
        if old != "auto":
            levels.append(old)
    levels.sort(key=FAN_RANK.index)
    canonical = ([("auto", "auto")] if "auto" in values else []) + [
        (str(i), old) for i, old in enumerate(levels, 1)
    ]
    return Choice(tuple(c for c, _ in canonical), dict(canonical))


def legacy_capabilities(caps, temperature_step):
    """Capabilities for an old class from its ``capabilities | xtra_capabilities``.

    Every fan/swing value is labelled with its old name, so the labels are
    also the translation table back to the old vocabulary.
    """
    temps = list(caps["temperature"])
    decimals = (0, 5) if temperature_step == 0.5 else (0,)
    features = {}
    for key, values in caps.items():
        if key in ("mode", "temperature", "fan", "swing", "hswing"):
            continue
        values = list(values)
        if sorted(values) == ["off", "on"]:
            features[key] = Choice((False, True), {False: "off", True: "on"})
        else:
            features[key] = Choice(tuple(values))
    return Capabilities(
        modes=tuple(m for m in caps["mode"] if m != "off"),
        temperature=TemperatureRange(temps[0], temps[-1], decimals),
        fan=_fan_choice(caps["fan"]) if "fan" in caps else None,
        swing_v=_swing_choice(caps["swing"]) if "swing" in caps else None,
        swing_h=(
            _swing_choice(caps["hswing"], HSWING_RANK) if "hswing" in caps else None
        ),
        features=features,
    )


class LegacyDevice(Device):
    """Wraps an old-style class (C-backed or pure Python) as a Device."""

    def __init__(self, brand, model, cls):
        super().__init__(brand, model)
        self.legacy_class = cls
        probe = cls()
        self.capabilities = legacy_capabilities(
            {**probe.capabilities, **probe.xtra_capabilities}, probe.temperature_step
        )

    def to_old(self, state):
        """The old key/value dict for a (normalised) state."""
        caps = self.capabilities
        t = state.temperature
        old = {
            "mode": state.mode if state.power else "off",
            "temperature": int(t) if t == int(t) else t,
        }
        for key, choice, value in (
            ("fan", caps.fan, state.fan),
            ("swing", caps.swing_v, state.swing_v),
            ("hswing", caps.swing_h, state.swing_h),
        ):
            if choice is not None:
                old[key] = choice.labels[value]
        for key, choice in caps.features.items():
            value = state.features[key]
            old[key] = choice.labels.get(value, value)
        return old

    def from_old(self, old):
        """An HvacState from old key/value pairs; missing keys get defaults."""
        caps = self.capabilities

        def back(choice, value, default):
            if choice is None or value is None:
                return default
            for canonical, name in choice.labels.items():
                if name == value:
                    return canonical
            return default

        features = {}
        for key, choice in caps.features.items():
            if key in old:
                features[key] = back(choice, old[key], old[key])
        mode = old.get("mode", caps.modes[0])
        return self.normalise(
            HvacState(
                power=mode != "off",
                mode=caps.modes[0] if mode == "off" else mode,
                temperature=old.get("temperature", caps.temperature.min),
                fan=back(caps.fan, old.get("fan"), "auto"),
                swing_v=back(caps.swing_v, old.get("swing"), "off"),
                swing_h=back(caps.swing_h, old.get("hswing"), "off"),
                features=features,
            )
        )

    def encode(self, previous, target, actions=()):
        self._check_actions(actions)
        target = self.normalise(target)
        dev = self.legacy_class()
        old = self.to_old(target)
        # Setters are bypassed (IRGHVAC.set_fan wrote "mode" before 0.1.8).
        # As the old setters did, only values that differ from the fresh
        # object's status are set. Pure-Python classes only take keys they
        # keep a status for (their code indexes status[key]); C-backed
        # classes keep a sparse status by design.
        sparse = isinstance(dev, IRGHVAC)
        dev.to_set = {
            k: v
            for k, v in old.items()
            if (sparse or k in dev.status) and dev.status.get(k) != v
        }
        pulses = [int(x) for x in dev.to_lirc(dev.build_ircode())]
        if len(pulses) % 2:
            pulses.append(TRAILER_GAP)
        return Command(Signal(38000, tuple(pulses)), target)
