"""The paired-protocol modules serve their C-backed models with ported devices."""

import importlib

import pytest

MODULES = ("lg", "panasonic", "sanyo", "kelon", "trotech")


@pytest.mark.parametrize("name", MODULES)
def test_module_has_a_devices_table(name):
    module = importlib.import_module(f"pyhvac.plugins.{name}")
    assert isinstance(module.DEVICES, dict)


@pytest.mark.parametrize("name", MODULES + ("ge",))
def test_no_ported_model_uses_the_c_library(name):
    from pyhvac import registry
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.hvaclib import IRGHVAC

    left = []
    for model in registry.models(name):
        try:
            device = registry.get_device(name, model)
        except AttributeError:  # a legacy C class without the C extension
            left.append(model)
            continue
        if isinstance(device, LegacyDevice) and issubclass(
            device.legacy_class, IRGHVAC
        ):
            left.append(model)
    assert left == []
