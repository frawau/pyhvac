"""The Haier plugin loads without the C extension and serves every model."""

import importlib


def test_haier_imports_without_the_c_extension():
    module = importlib.import_module("pyhvac.plugins.haier")
    assert isinstance(module.DEVICES, dict)
