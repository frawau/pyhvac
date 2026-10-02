"""Find devices by brand and model (see pyhvac/brands.py)."""

from __future__ import annotations

import re

from . import brands as _brands


def _key(text):
    """Names match ignoring case, whitespace and punctuation."""
    return re.sub(r"[^0-9a-z]", "", text.casefold())


def _index():
    rows = {}
    for brand, model, kind, cls, variant in _brands.MODELS:
        rows.setdefault(_key(brand), (brand, {}))[1][_key(model)] = (
            model,
            kind,
            cls,
            variant,
        )
    return rows


_ROWS = _index()


def brands():
    """Brand names, as the manufacturers write them, sorted."""
    return sorted((brand for brand, _ in _ROWS.values()), key=str.casefold)


def models(brand):
    """The brand's model names; KeyError for an unknown brand."""
    return [model for model, *_ in _brand(brand)[1].values()]


def get_device(brand, model=None):
    """A Device for ``brand`` and ``model``. ``model`` may be left out when
    the brand has one model. The 0.1.x names of the devices that were pure
    Python in 0.1.x still resolve (brands.ALIASES)."""
    alias = _alias(brand, model)
    if alias is not None:
        brand, model = alias
    name, table = _brand(brand)
    if model is None:
        if len(table) != 1:
            raise KeyError(f"brand {name!r} has several models: {models(name)}")
        (entry,) = table.values()
    else:
        entry = table.get(_key(model))
        if entry is None:
            raise KeyError(f"unknown model {model!r} for {name!r}: {models(name)}")
    model, kind, cls, variant = entry
    if variant is None:
        return cls(name, model)
    return cls(name, model, variant=variant)


def variant_of(cls, brand, model):
    """The variant pyhvac.brands gives ``cls`` for ``brand``/``model``, or
    None (no row, another class, or the row has none): for Devices built
    directly rather than through ``get_device``."""
    entry = _ROWS.get(_key(brand), (None, {}))[1].get(_key(model))
    if entry is None or entry[2] is not cls:
        return None
    return entry[3]


def _brand(brand):
    try:
        return _ROWS[_key(brand)]
    except KeyError:
        raise KeyError(f"unknown brand {brand!r}") from None


def _alias(brand, model):
    if model is None:
        return None
    for (old_brand, old_model), new in _brands.ALIASES.items():
        if _key(old_brand) == _key(brand) and _key(old_model) == _key(model):
            return new
    return None
