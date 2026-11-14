"""What the IRremoteESP8266 C path (pyhvac 0.1.x) sent, beyond the oracle
grid: recorded once while the C extension existed, replayed from
tests/fixtures/oracle_extra/<test module>.json.gz ever after.

Record mode: PYHVAC_FREEZE=1 with the C extension importable. Every call
computes the C output and keeps it; the session writes the fixtures at exit
(tests/conftest.py). Replay mode (the default): calls read the fixtures; a
call whose key was never recorded fails.

Keys are the calls' inputs, so a test replays exactly what it recorded:
(test module, kind, brand/plugin, model, legacy class, glue, the states).
``glue="fixed"`` recorded with main's glue fix (swing "on" passed as kAuto,
hswing "on" as kAuto), which the 0.1.7 oracle fixtures predate.
"""

import gzip
import importlib
import inspect
import json
import os
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures" / "oracle_extra"
RECORDING = os.environ.get("PYHVAC_FREEZE") == "1"
_store = {}  # module name -> {key: value}
_dirty = set()


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


def _lookup(module, key, compute):
    table = _load(module)
    if RECORDING:
        table[key] = compute()
        _dirty.add(module)
    if key not in table:
        raise AssertionError(f"not frozen in oracle_extra/{module}: {key}")
    return table[key]


def write_fixtures():
    """Write every table recorded in this session (record mode only)."""
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for module in sorted(_dirty):
        data = json.dumps(_store[module], sort_keys=True).encode()
        (FIXTURES / f"{module}.json.gz").write_bytes(gzip.compress(data, mtime=0))


def _legacy_class(plugin, name):
    return getattr(importlib.import_module(f"pyhvac.plugins.{plugin}"), name)


def _fix_glue(cls):
    """main's glue fix on one legacy class: swing/hswing "on" reach C."""
    from pyhvac import irhvac

    swing, hswing = cls.trans_swing, cls.trans_hswing

    class Fixed(cls):
        def trans_swing(self, value):
            return irhvac.swingv_t_kAuto if value == "on" else swing(self, value)

        def trans_hswing(self, value):
            return irhvac.swingh_t_kAuto if value == "on" else hswing(self, value)

    Fixed.__name__ = cls.__name__
    return Fixed


def c_encode(plugin, model, legacy, state, glue=None):
    """The pulses a fresh legacy object sent for ``state`` (an HvacState),
    as LegacyDevice(plugin, model, <plugin>.<legacy>).encode(None, state)."""
    module = _module_name()

    def compute():
        from pyhvac.legacy import LegacyDevice

        cls = _legacy_class(plugin, legacy)
        if glue == "fixed":
            cls = _fix_glue(cls)
        dev = LegacyDevice(plugin, model, cls)
        return [int(p) for p in dev.encode(None, state).signal.pulses]

    return _lookup(module, _key("encode", plugin, model, legacy, glue, state), compute)


def c_sequence(record, states, glue=None):
    """The records one persistent legacy object produced for ``states``
    (old vocabulary), sent in order: IRac keeps the last message sent (its
    _prev), so toggle protocols toggle as on a real remote. ``record`` is an
    oracle record naming the legacy plugin and class."""
    module = _module_name()

    def compute():
        cls = _legacy_class(record["plugin"], record["class"])
        if glue == "fixed":
            cls = _fix_glue(cls)
        legacy = cls()
        status = dict(legacy.status)
        out = []
        for old in states:
            # Only IRac's memory of the last message sent carries over: the
            # glue's status and IRac's next state (which keep keys a state
            # does not mention) start fresh, as for a new object.
            legacy.status = dict(status)
            legacy.irac.next = cls().irac.next
            legacy.to_set = dict(old)  # bypass the setters
            out.append([int(x) for x in legacy.to_lirc(legacy.build_ircode())])
        return out

    key = _key("sequence", record["plugin"], record["class"], glue, states)
    pulses = _lookup(module, key, compute)
    return [{**record, "state": old, "pulses": p} for old, p in zip(states, pulses)]
