import json
import re
from collections import Counter
from pathlib import Path

import pytest

from pyhvac import brands, registry
from pyhvac.state import HvacState

ROWS = json.loads((Path(__file__).parent / "fixtures" / "names_0_1.json").read_text())
DROPPED = {("sharp", "generic")}


def key(text):
    return re.sub(r"[^0-9a-z]", "", text.casefold())


@pytest.mark.parametrize(
    "row",
    [r for r in ROWS if (r["old_brand"], r["old_model"]) not in DROPPED],
    ids=lambda r: f"{r['old_brand']}/{r['old_model']}",
)
def test_every_old_model_has_its_new_row(row):
    dev = registry.get_device(row["brand"], row["model"])
    assert type(dev).__name__ == row["cls"].split(".")[1]
    assert getattr(dev, "variant", None) == row["var"]
    caps = dev.capabilities
    dev.encode(None, HvacState(True, caps.modes[0], caps.temperature.min))


def test_names_do_not_collide_after_normalising():
    assert len({key(b) for b, *_ in brands.MODELS}) == len(
        {b for b, *_ in brands.MODELS}
    )
    counts = Counter((key(b), key(m)) for b, m, *_ in brands.MODELS)
    assert [k for k, n in counts.items() if n > 1] == []


def test_aliases_are_the_pure_python_devices_only():
    expected = {(r["old_brand"], r["old_model"]) for r in ROWS if r["alias"]} - DROPPED
    assert set(brands.ALIASES) == expected
    for old in brands.ALIASES:
        registry.get_device(*old)


def test_old_names_of_c_backed_models_do_not_resolve():
    with pytest.raises(KeyError):
        registry.get_device("lg", "6711A20083V  remote")


def test_hitachi_ac3_and_sharp_generic_are_gone():
    for brand, model in (("hitachi", "PC-LH3B"), ("hitachi", "generic 3")):
        with pytest.raises(KeyError):
            registry.get_device(brand, model)
    assert ("sharp", "generic") not in brands.ALIASES
