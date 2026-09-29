import pytest

pytest.skip("old API: deleted in Task 6", allow_module_level=True)

import gzip
import importlib
import json
from pathlib import Path

import pytest

from pyhvac.ir.codec import decode
from pyhvac.ir.model import Frame
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
    cls = getattr(
        importlib.import_module(f"pyhvac.protocols.{module}"), record["class"]
    )
    dev, frames = build_native(cls, record["state"])
    assert [int(x) for x in dev.to_lirc(frames)] == record["pulses"]
    assert dev.to_broadlink(frames).hex() == record["broadlink"]


@pytest.mark.parametrize("module, record", RECORDS)
def test_native_protocol_decodes_its_own_output(module, record):
    cls = getattr(
        importlib.import_module(f"pyhvac.protocols.{module}"), record["class"]
    )
    if cls.PROTOCOL is None:
        pytest.skip(f"{cls.__name__} not migrated yet")
    dev, frames = build_native(cls, record["state"])
    expected = [Frame("main", bytes(f)) for f in frames]
    assert (
        decode(cls.PROTOCOL, record["pulses"], expected=["main"] * len(frames))
        == expected
    )
