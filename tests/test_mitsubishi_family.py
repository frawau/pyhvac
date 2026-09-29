"""Every Mitsubishi model is served by a pure-Python device."""

import importlib

import pytest

MODULES = ("mitsubishi_electric", "mitsubishi_heavy_industries")


@pytest.mark.parametrize("name", MODULES)
def test_module_has_a_devices_table(name):
    module = importlib.import_module(f"pyhvac.plugins.{name}")
    assert isinstance(module.DEVICES, dict)


@pytest.mark.parametrize("name", MODULES)
def test_no_mitsubishi_model_uses_the_c_library(name):
    from pyhvac import registry
    from pyhvac.legacy import LegacyDevice

    left = [
        m
        for m in registry.models(name)
        if isinstance(registry.get_device(name, m), LegacyDevice)
    ]
    assert left == []
