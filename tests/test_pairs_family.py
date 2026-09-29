"""The paired-protocol modules serve their C-backed models with ported devices."""

import importlib

import pytest

MODULES = ("lg", "panasonic", "sanyo", "kelon", "trotech")


@pytest.mark.parametrize("name", MODULES)
def test_module_has_a_devices_table(name):
    module = importlib.import_module(f"pyhvac.plugins.{name}")
    assert isinstance(module.DEVICES, dict)
