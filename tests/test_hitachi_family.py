"""The Hitachi plugin and its ports load with or without the C extension."""

import importlib


def test_hitachi_imports_without_the_c_extension():
    module = importlib.import_module("pyhvac.plugins.hitachi")
    assert isinstance(module.DEVICES, dict)


def test_only_hitachi_ac3_stays_on_the_c_library():
    import pytest

    # Building the remaining legacy devices needs the C extension.
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac import registry
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.hitachi import PluginObject
    from pyhvac.plugins.hvaclib import IRGHVAC

    c_backed = [m for m, cls in PluginObject.MODELS.items() if issubclass(cls, IRGHVAC)]
    left = [
        m
        for m in c_backed
        if isinstance(registry.get_device("hitachi", m), LegacyDevice)
    ]
    # HITACHI_AC3 has no documented layout and the C path sends nothing;
    # these models are dropped in phase 4.
    assert sorted(left) == ["PC-LH3B", "generic 3"]
