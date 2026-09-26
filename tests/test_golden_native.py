import gzip
import importlib
import json
from pathlib import Path

import pytest

from state_grid import NATIVE, build_native

FIXTURES = Path(__file__).parent / "fixtures" / "golden"


def _records():
    for module in NATIVE:
        path = FIXTURES / f"{module}.json.gz"
        for n, record in enumerate(json.loads(gzip.decompress(path.read_bytes()))):
            yield pytest.param(module, record, id=f"{module}-{record['class']}-{n}")


RECORDS = list(_records())


def test_every_native_module_has_fixtures():
    assert {p.values[0] for p in RECORDS} == set(NATIVE)


@pytest.mark.parametrize("module, record", RECORDS)
def test_native_wire_output_unchanged(module, record):
    cls = getattr(importlib.import_module(f"pyhvac.plugins.{module}"), record["class"])
    dev, frames = build_native(cls, record["state"])
    assert [int(x) for x in dev.to_lirc(frames)] == record["pulses"]
    assert dev.to_broadlink(frames).hex() == record["broadlink"]
