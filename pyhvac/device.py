"""Stateless devices: (previous, target, actions) -> IR command."""

from __future__ import annotations

from dataclasses import dataclass

from .ir.codec import encode as ir_encode
from .ir.model import Signal
from .state import HvacState


@dataclass(frozen=True)
class Command:
    signal: Signal
    state: HvacState  # the normalised target: what the caller persists


class Device:
    """Base class. Subclasses set ``capabilities`` and implement ``frames``
    (protocol-backed) or override ``encode``."""

    PROTOCOL = None
    capabilities = None

    def __init__(self, brand, model):
        self.brand = brand
        self.model = model

    def normalise(self, state):
        caps = self.capabilities

        def pick(choice, value, default):
            if choice is None:
                return default
            return value if value in choice.values else choice.values[0]

        features = {}
        for name, choice in caps.features.items():
            value = state.features.get(name, choice.values[0])
            features[name] = value if _in_choice(value, choice) else choice.values[0]
        return HvacState(
            power=state.power,
            mode=state.mode if state.mode in caps.modes else caps.modes[0],
            temperature=caps.temperature.snap(state.temperature),
            fan=pick(caps.fan, state.fan, "auto"),
            swing_v=pick(caps.swing_v, state.swing_v, "off"),
            swing_h=pick(caps.swing_h, state.swing_h, "off"),
            features=features,
        )

    def _check_actions(self, actions):
        actions = tuple(actions)
        unknown = [a for a in actions if a not in self.capabilities.actions]
        if unknown:
            raise ValueError(
                f"unknown actions for {self.brand}/{self.model}: {unknown}"
            )
        return actions

    def encode(self, previous, target, actions=()):
        actions = self._check_actions(actions)
        target = self.normalise(target)
        if previous is not None:
            previous = self.normalise(previous)
        frames = self.frames(previous, target, actions)
        return Command(ir_encode(self.PROTOCOL, frames), target)

    def frames(self, previous, target, actions):
        raise NotImplementedError(f"{type(self).__name__} does not build frames")


def _in_choice(value, choice):
    # bools and strings must match by type too: True is not "on", 1 is not True
    return any(type(value) is type(v) and value == v for v in choice.values)
