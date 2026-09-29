import pytest

pytest.skip("old API: deleted in Task 6", allow_module_level=True)

#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Tests for the IRremoteESP8266-backed (IRGHVAC) classes.

import importlib
import pkgutil

import pytest

from pyhvac.protocols.hvaclib import IRGHVAC


def bare_device(capabilities):
    """An IRGHVAC without the C extension: setters only touch plain attributes."""
    dev = object.__new__(IRGHVAC)
    dev.capabilities = capabilities
    dev.to_set = {}
    return dev


CAPS = {"mode": ["off", "auto", "cool"], "fan": ["auto", "high", "low"]}


def test_set_fan_sets_fan_not_mode():
    dev = bare_device(CAPS)
    dev.set_fan("high")
    assert dev.to_set == {"fan": "high"}


def test_set_fan_falls_back_to_first_fan_value():
    dev = bare_device(CAPS)
    dev.set_fan("turbo")
    assert dev.to_set == {"fan": "auto"}


def test_set_fan_ignored_without_fan_capability():
    dev = bare_device({"mode": ["off", "cool"]})
    dev.set_fan("high")
    assert dev.to_set == {}


def _irghvac_classes():
    import pyhvac.plugins as plugins

    seen = {}
    for info in pkgutil.iter_modules(plugins.__path__):
        if info.name == "hvaclib":
            continue
        mod = importlib.import_module(f"pyhvac.protocols.{info.name}")
        for cls in mod.PluginObject.MODELS.values():
            if isinstance(cls, type) and issubclass(cls, IRGHVAC):
                seen[cls.__name__] = cls
    return sorted(seen.items())


def test_every_c_backed_class_names_a_known_protocol():
    irhvac = pytest.importorskip("pyhvac.irhvac")
    unknown = [
        f"{name}: {cls().protocol}"
        for name, cls in _irghvac_classes()
        if not hasattr(irhvac, cls().protocol)
    ]
    assert unknown == []
