#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Tests for the IRremoteESP8266-backed (IRGHVAC) classes.

import importlib
import pkgutil

import pytest

from pyhvac.plugins.hvaclib import IRGHVAC


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
        mod = importlib.import_module(f"pyhvac.plugins.{info.name}")
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


def test_every_c_backed_class_uses_known_modes():
    pytest.importorskip("pyhvac.irhvac")
    known = {"off", "auto", "cool", "heat", "dry", "fan"}
    unknown = [
        f"{name}: {sorted(set(cls().capabilities['mode']) - known)}"
        for name, cls in _irghvac_classes()
        if not set(cls().capabilities["mode"]) <= known
    ]
    assert unknown == []


def test_every_advertised_swing_value_translates():
    # A value missing from trans_swing/trans_hswing is silently dropped by
    # build_ircode, so e.g. swing "on" never reached the C library.
    pytest.importorskip("pyhvac.irhvac")
    missing = []
    for name, cls in _irghvac_classes():
        dev = cls()
        caps = {**dev.capabilities, **dev.xtra_capabilities}
        for key, trans in (("swing", dev.trans_swing), ("hswing", dev.trans_hswing)):
            for value in caps.get(key, ()):
                try:
                    trans(value)
                except KeyError:
                    missing.append(f"{name}.{key}={value!r}")
    assert missing == []


def test_swing_on_means_swing():
    irhvac = pytest.importorskip("pyhvac.irhvac")
    dev = bare_device(CAPS)
    assert dev.trans_swing("on") == irhvac.swingv_t_kAuto
    assert dev.trans_hswing("on") == irhvac.swingh_t_kAuto
