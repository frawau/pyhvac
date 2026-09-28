"""Every C-backed Daikin model is served by a pure-Python device."""

from pyhvac import registry
from pyhvac.legacy import LegacyDevice
from pyhvac.plugins.daikin import PluginObject
from pyhvac.plugins.hvaclib import IRGHVAC


def test_no_daikin_model_uses_the_c_library():
    c_backed = [m for m, cls in PluginObject.MODELS.items() if issubclass(cls, IRGHVAC)]
    left = [
        m
        for m in c_backed
        if isinstance(registry.get_device("daikin", m), LegacyDevice)
    ]
    assert left == []
