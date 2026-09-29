"""The Hitachi plugin and its ports load with or without the C extension."""

import importlib


def test_hitachi_imports_without_the_c_extension():
    module = importlib.import_module("pyhvac.plugins.hitachi")
    assert isinstance(module.DEVICES, dict)
