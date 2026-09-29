"""What the IRremoteESP8266 C path (pyhvac 0.1.x) sent, beyond the oracle
grid, replayed from tests/fixtures/oracle_extra/<test module>.json.gz.

The fixtures were recorded once, while pyhvac still had its C extension
(see tests/fixtures/README.md). Keys are the calls' inputs, so a test
replays exactly what it recorded: (test module, kind, plugin, model,
legacy class, glue, the states). A call whose key was never recorded
fails. ``glue="fixed"`` replays C with main's glue fix (swing and hswing
"on" passed as kAuto), which the 0.1.7 oracle fixtures predate.
"""

import gzip
import inspect
import json
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures" / "oracle_extra"
_store = {}  # module name -> {key: value}


def _module_name():
    for frame in inspect.stack()[2:]:
        name = Path(frame.filename).stem
        if name.startswith("test_"):
            return name
    raise RuntimeError("c_oracle must be called from a test module")


def _load(module):
    if module not in _store:
        path = FIXTURES / f"{module}.json.gz"
        _store[module] = (
            json.loads(gzip.decompress(path.read_bytes())) if path.exists() else {}
        )
    return _store[module]


def _key(*parts):
    return json.dumps(parts, sort_keys=True, default=repr)


def _lookup(module, key):
    table = _load(module)
    if key not in table:
        raise AssertionError(f"not frozen in oracle_extra/{module}: {key}")
    return table[key]


def c_encode(plugin, model, legacy, state, glue=None):
    """The pulses a fresh legacy object sent for ``state`` (an HvacState),
    as LegacyDevice(plugin, model, <plugin>.<legacy>).encode(None, state)."""
    key = _key("encode", plugin, model, legacy, glue, state)
    return _lookup(_module_name(), key)


def c_sequence(record, states, glue=None):
    """The records one persistent legacy object produced for ``states``
    (old vocabulary), sent in order: IRac kept the last message sent (its
    _prev), so toggle protocols toggled as on a real remote. ``record`` is
    an oracle record naming the legacy plugin and class."""
    key = _key("sequence", record["plugin"], record["class"], glue, states)
    pulses = _lookup(_module_name(), key)
    return [{**record, "state": old, "pulses": p} for old, p in zip(states, pulses)]


def c_frozen(label):
    """A JSON-able result a test computed from the C library directly,
    replayed by ``label``."""
    return _lookup(_module_name(), _key("frozen", label))
