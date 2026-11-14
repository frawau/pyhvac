import pytest

from pyhvac.device import Command, Device
from pyhvac.ir.model import Frame, Protocol, PulseDistance, Section
from pyhvac.state import BOOL, Capabilities, Choice, HvacState, TemperatureRange

TOY_PROTOCOL = Protocol(
    "toy",
    {
        "main": Section(
            PulseDistance(500, 500, 1500), header=(4000, 2000), footer=(500,), gap=20000
        )
    },
)


class Toy(Device):
    """Encodes power, mode index and temperature; flags a 'blink' action."""

    PROTOCOL = TOY_PROTOCOL
    capabilities = Capabilities(
        modes=("cool", "heat"),
        temperature=TemperatureRange(16.0, 30.0, (0, 5)),
        fan=Choice(("auto", "1", "2")),
        swing_v=Choice(("off", "swing")),
        features={"quiet": BOOL, "economy": Choice(("off", "80", "60"))},
        actions={"blink": "Blink"},
    )

    def frames(self, previous, target, actions):
        data = bytes(
            [
                int(target.power),
                self.capabilities.modes.index(target.mode),
                round(target.temperature * 2),
                int("blink" in actions),
            ]
        )
        return [Frame("main", data)]


def toy():
    return Toy("toy", "generic")


def test_normalise_rules():
    s = HvacState(
        power=True,
        mode="dry",  # unsupported -> first mode
        temperature=31.2,  # clamped and snapped
        fan="7",  # unsupported -> first value
        swing_v="auto",  # unsupported -> first value
        swing_h="swing",  # no swing_h capability -> default
        features={"quiet": "on", "economy": "80", "light": True},
    )
    n = toy().normalise(s)
    assert (n.mode, n.temperature, n.fan, n.swing_v, n.swing_h) == (
        "cool",
        30.0,
        "auto",
        "off",
        "off",
    )
    # wrong type -> first value; unknown feature dropped; valid value kept
    assert dict(n.features) == {"quiet": False, "economy": "80"}


def test_missing_features_get_first_value():
    n = toy().normalise(HvacState(True, "heat", 20.0))
    assert dict(n.features) == {"quiet": False, "economy": "off"}


def test_encode_returns_normalised_state_and_signal():
    cmd = toy().encode(None, HvacState(True, "heat", 20.3))
    assert isinstance(cmd, Command)
    assert cmd.state.temperature == 20.5
    assert cmd.signal.carrier == 38000
    assert cmd.signal.pulses[:2] == (4000, 2000)


def test_encode_is_deterministic():
    t = HvacState(True, "cool", 22.0)
    assert toy().encode(None, t) == toy().encode(None, t)


def test_actions_reach_frames_but_not_state():
    t = HvacState(True, "cool", 22.0)
    with_blink = toy().encode(None, t, ["blink"])
    assert with_blink.signal != toy().encode(None, t).signal
    assert with_blink.state == toy().normalise(t)


def test_unknown_action_rejected():
    with pytest.raises(ValueError, match="dance"):
        toy().encode(None, HvacState(True, "cool", 22.0), ["dance"])


def test_previous_is_normalised_before_frames():
    seen = {}

    class Spy(Toy):
        def frames(self, previous, target, actions):
            seen["previous"] = previous
            return super().frames(previous, target, actions)

    Spy("toy", "spy").encode(
        HvacState(False, "dry", 40.0), HvacState(True, "cool", 22.0)
    )
    assert seen["previous"].mode == "cool"
    assert seen["previous"].temperature == 30.0


def test_base_frames_not_implemented():
    class Bare(Device):
        PROTOCOL = TOY_PROTOCOL
        capabilities = Toy.capabilities

    with pytest.raises(NotImplementedError):
        Bare("b", "b").encode(None, HvacState(True, "cool", 22.0))
