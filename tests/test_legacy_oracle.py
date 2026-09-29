"""LegacyDevice against the IRremoteESP8266 reference pulses (needs _irhvac)."""

import pytest

pytest.skip("old API: deleted in Task 6", allow_module_level=True)


import gzip
import importlib
import json
from pathlib import Path

import pytest

pytest.importorskip("pyhvac.irhvac")

from pyhvac.legacy import TRAILER_GAP, LegacyDevice  # noqa: E402

ORACLE = Path(__file__).parent / "fixtures" / "oracle"
# The C encoder for HITACHI_AC296 reads stale memory: its output depends on
# what was encoded earlier in the same process.
UNSTABLE = {"HITACHI_AC296"}
_DEVICES = {}


def _device(record):
    key = (record["plugin"], record["model"])
    if key not in _DEVICES:
        module = importlib.import_module(f"pyhvac.protocols.{record['plugin']}")
        cls = module.PluginObject.MODELS[record["model"]]
        _DEVICES[key] = LegacyDevice(record["plugin"], record["model"], cls)
    return _DEVICES[key]


def _cases():
    for path in sorted(ORACLE.glob("*.json.gz")):
        name = path.name[: -len(".json.gz")]
        marks = (
            [pytest.mark.xfail(reason="unstable C encoder", strict=False)]
            if name in UNSTABLE
            else []
        )
        for n, rec in enumerate(json.loads(gzip.decompress(path.read_bytes()))):
            yield pytest.param(rec, id=f"{name}-{n}", marks=marks)


@pytest.mark.parametrize("record", list(_cases()))
def test_legacy_device_matches_c_library(record):
    dev = _device(record)
    try:
        target = dev.from_old(record["state"])
    except ValueError as exc:
        pytest.skip(f"state not expressible: {exc}")
    old = dev.to_old(target)
    assert {k: old.get(k) for k in record["state"]} == record["state"]
    missing = {k: v for k, v in old.items() if k not in record["state"]}
    if any(v != "off" for v in missing.values()):
        pytest.skip(f"record relied on C defaults for {sorted(missing)}")
    expected = list(record["pulses"])
    if len(expected) % 2:  # the C output ended on a mark
        expected.append(TRAILER_GAP)
    assert list(dev.encode(None, target).signal.pulses) == expected
