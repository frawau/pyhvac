"""Every Mitsubishi model is served by a pure-Python device."""

import importlib

import pytest

MODULES = ("mitsubishi_electric", "mitsubishi_heavy_industries")


@pytest.mark.parametrize("name", MODULES)
def test_module_has_a_devices_table(name):
    module = importlib.import_module(f"pyhvac.plugins.{name}")
    assert isinstance(module.DEVICES, dict)
