"""Every advertised capability value of every model must encode.

A Home Assistant entity is built from ``capabilities``: anything listed there
reaches the user as a control, so it must produce a signal, not an exception.
Models that need the C extension skip when it is absent.
"""

import pytest

pytest.skip("old API: deleted in Task 6", allow_module_level=True)


import pytest

from pyhvac import registry

# IRremoteESP8266 produces no signal for these (HITACHI_AC3 via IRac).
UNSENDABLE = {("hitachi", "PC-LH3B"), ("hitachi", "generic 3")}
from pyhvac.state import HvacState


def _models():
    for brand in registry.brands():
        for model in registry.models(brand):
            yield pytest.param(brand, model, id=f"{brand}/{model}")


def _device(brand, model):
    try:
        dev = registry.get_device(brand, model)
    except AttributeError as exc:  # C-backed class without the extension
        pytest.skip(f"needs the C extension: {exc}")
    if (brand, model) in UNSENDABLE:
        with pytest.raises(NotImplementedError, match="no signal"):
            dev.encode(None, _base(dev))
        pytest.skip("the C library cannot send this protocol")
    return dev


def _base(dev):
    caps = dev.capabilities
    return dev.normalise(HvacState(True, caps.modes[0], caps.temperature.min))


def _variants(caps, base):
    yield base
    for mode in caps.modes:
        yield HvacState(True, mode, base.temperature, features=base.features)
    for field, choice in (
        ("fan", caps.fan),
        ("swing_v", caps.swing_v),
        ("swing_h", caps.swing_h),
    ):
        for value in choice.values if choice else ():
            yield HvacState(**{**base.to_dict(), field: value})
    for name, choice in caps.features.items():
        for value in choice.values:
            yield HvacState(**{**base.to_dict(), "features": {name: value}})


@pytest.mark.parametrize("brand, model", list(_models()))
def test_every_capability_value_encodes(brand, model):
    dev = _device(brand, model)
    caps = dev.capabilities
    base = _base(dev)
    for state in _variants(caps, base):
        dev.encode(None, state)


@pytest.mark.parametrize("brand, model", list(_models()))
def test_off_encodes_at_every_setpoint(brand, model):
    dev = _device(brand, model)
    rng = dev.capabilities.temperature
    t = rng.min
    while t <= rng.max:
        dev.encode(None, HvacState(False, dev.capabilities.modes[0], t))
        t += 1
