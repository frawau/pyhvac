"""The Haier plugin loads without the C extension and serves every model."""

import importlib


def test_haier_imports_without_the_c_extension():
    module = importlib.import_module("pyhvac.plugins.haier")
    assert isinstance(module.DEVICES, dict)


def test_no_haier_model_uses_the_c_library():
    from pyhvac import registry
    from pyhvac.legacy import LegacyDevice

    left = [
        m
        for m in registry.models("haier")
        if isinstance(registry.get_device("haier", m), LegacyDevice)
    ]
    assert left == []
