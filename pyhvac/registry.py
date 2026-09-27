"""Find devices by brand (plugin module name) and model."""

from __future__ import annotations

import functools
import importlib
import logging
import pkgutil

from . import plugins
from .legacy import LegacyDevice

_LOGGER = logging.getLogger(__name__)


def brands():
    """Plugin module names, sorted."""
    return sorted(
        m.name for m in pkgutil.iter_modules(plugins.__path__) if m.name != "hvaclib"
    )


@functools.lru_cache(maxsize=None)
def _factories(brand):
    if brand not in brands():
        raise KeyError(f"unknown brand {brand!r}")
    try:
        module = importlib.import_module(f"{plugins.__name__}.{brand}")
    except ImportError as exc:
        _LOGGER.warning("brand %s unavailable: %s", brand, exc)
        return {}
    factories = {}
    for model, cls in module.PluginObject.MODELS.items():
        factories[model] = functools.partial(LegacyDevice, brand, model, cls)
    for model, device_class in getattr(module, "DEVICES", {}).items():
        factories[model] = functools.partial(device_class, brand, model)
    return factories


def models(brand):
    return list(_factories(brand))


def get_device(brand, model=None):
    factories = _factories(brand)
    model = "generic" if model is None else model
    if model not in factories:
        raise KeyError(f"unknown model {model!r} for brand {brand!r}")
    return factories[model]()
