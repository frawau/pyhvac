import logging

import pytest

from pyhvac import registry
from pyhvac.legacy import LegacyDevice
from pyhvac.plugins.airspool import AirspoolDevice
from pyhvac.plugins.sharp import JTechDevice


@pytest.fixture(autouse=True)
def fresh_registry():
    registry._factories.cache_clear()
    yield
    registry._factories.cache_clear()


def _has_c_extension():
    try:
        import pyhvac.irhvac  # noqa: F401
    except ImportError:
        return False
    return True


def test_brands_are_plugin_modules():
    names = registry.brands()
    assert "airspool" in names and "sharp" in names
    assert "hvaclib" not in names
    assert names == sorted(names)


def test_new_style_devices_win_over_legacy_models():
    assert isinstance(registry.get_device("airspool"), AirspoolDevice)
    assert isinstance(registry.get_device("sharp", "j-tech"), JTechDevice)
    assert "j-tech" in registry.models("sharp")


def test_other_models_are_wrapped():
    assert isinstance(registry.get_device("daikin", "generic"), LegacyDevice)


def test_device_knows_brand_and_model():
    dev = registry.get_device("sharp", "j-tech")
    assert (dev.brand, dev.model) == ("sharp", "j-tech")


def test_unknown_brand_or_model():
    with pytest.raises(KeyError):
        registry.get_device("acme")
    with pytest.raises(KeyError):
        registry.get_device("airspool", "no such model")


def test_brand_that_fails_to_import_is_skipped_with_warning(caplog, monkeypatch):
    # Every plugin now guards its irhvac import, so simulate a module that
    # cannot be imported (as an unguarded `from ..irhvac import ...` was).
    real = registry.importlib.import_module

    def fail_for_fujitsu(name, *args):
        if name.endswith(".fujitsu"):
            raise ImportError("No module named 'pyhvac.irhvac'")
        return real(name, *args)

    monkeypatch.setattr(registry.importlib, "import_module", fail_for_fujitsu)
    with caplog.at_level(logging.WARNING, logger="pyhvac.registry"):
        assert registry.models("fujitsu") == []
    assert "fujitsu" in caplog.text


@pytest.mark.skipif(not _has_c_extension(), reason="needs the _irhvac extension")
def test_every_model_maps_to_a_device():
    failures = []
    for brand in registry.brands():
        for model in registry.models(brand):
            try:
                registry.get_device(brand, model)
            except Exception as exc:  # collect them all
                failures.append(f"{brand}/{model}: {exc!r}")
    assert failures == []
