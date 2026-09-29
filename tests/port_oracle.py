"""Acceptance helper for protocol ports: a ported Device against the
IRremoteESP8266 reference pulses in tests/fixtures/oracle.

A difference between the port and the C output is accepted only when it is
declared as a ``Defect``: a field where the C library is known to deviate
from the documented protocol.
"""

import importlib
from dataclasses import dataclass

import pytest

from oracle import check_against_oracle, load_oracle
from pyhvac.fields import Joined
from pyhvac.ir.codec import decode
from pyhvac.ir.formats import to_broadlink
from pyhvac.state import HvacState


@dataclass(frozen=True)
class Defect:
    """Field ``field`` is ``ours`` in the port but ``theirs`` in the C output."""

    field: str
    ours: object
    theirs: object
    reason: str


def _back(choice, value, default):
    """Old-vocabulary value -> canonical value, through the choice's labels."""
    if choice is None or value is None:
        return default
    for canonical in choice.values:
        if choice.labels.get(canonical, canonical) == value:
            return canonical
    raise ValueError(f"no canonical value labelled {value!r}")


def state_from_record(device, old):
    """The HvacState a record's old-vocabulary state describes, for ``device``."""
    caps = device.capabilities
    mode = old.get("mode", caps.modes[0])
    features = {}
    for key, choice in caps.features.items():
        if key in old:
            value = old[key]
            features[key] = value == "on" if choice.values == (False, True) else value
    return device.normalise(
        HvacState(
            power=mode != "off",
            mode=caps.modes[0] if mode == "off" else mode,
            temperature=old.get("temperature", caps.temperature.min),
            fan=_back(caps.fan, old.get("fan"), "auto"),
            swing_v=_back(caps.swing_v, old.get("swing"), "off"),
            swing_h=_back(caps.swing_h, old.get("hswing"), "off"),
            features=features,
        )
    )


def oracle_params(name):
    """pytest params, one per oracle record of fixture ``name``."""
    return [
        pytest.param(rec, id=f"{name}-{n}") for n, rec in enumerate(load_oracle(name))
    ]


def assert_matches_oracle(device, record, layouts, defects=(), previous=None):
    """Assert the port reproduces ``record``.

    ``layouts`` gives one Layout (or None for bitless frames) per frame of the
    message, in order (a ``Joined`` entry covers several frames), or is a
    function of the port's frames returning them (for messages whose frame
    count varies). Frames must be byte-identical, except for fields listed in
    ``defects`` (and the checksums they change). ``previous`` is the port's
    previous state (None: a fresh C object, as the fixtures were recorded).
    """
    state = state_from_record(device, record["state"])
    ours = device.frames(previous, state, ())
    names = [f.section for f in ours]
    theirs = decode(device.PROTOCOL, record["pulses"], expected=names)
    if callable(layouts):
        layouts = layouts(ours)
    groups = []  # (first frame index, frame count, layout)
    first = 0
    for layout in layouts:
        if isinstance(layout, Joined):
            count, layout = layout.count, layout.layout
        else:
            count = 1
        groups.append((first, count, layout))
        first += count
    assert first == len(ours), "one layout (or None) per frame is required"
    allowed = {(d.field, d.ours, d.theirs) for d in defects}
    deviated = False
    for i, count, layout in groups:
        a, b = (
            b"".join(f.data for f in side[i : i + count]) for side in (ours, theirs)
        )
        if a == b:
            continue
        assert layout is not None, f"frame {i}: {a.hex()} != {b.hex()}"
        read_a, read_b = layout.read(a), layout.read(b)
        diffs = [k for k in read_a if read_a[k] != read_b[k]]
        unexplained = {
            k: (read_a[k], read_b[k])
            for k in diffs
            if (k, read_a[k], read_b[k]) not in allowed
        }
        assert not unexplained, f"frame {i}: {unexplained} for {record['state']}"
        # With C's values in the declared fields (and the checksum redone),
        # our frame must be exactly C's: nothing else may differ.
        expected = bytearray(a)
        for k in diffs:
            layout.write_raw(expected, k, layout.read_raw(b, k))
        if layout.checksum is not None:
            layout.checksum.apply(expected)
        assert bytes(expected) == b, f"frame {i}: more than {diffs} differs"
        deviated = True
    if not deviated:
        check_against_oracle(device.PROTOCOL, record, ours)


def c_sequence(record, states):
    """C-gated: the records one persistent legacy (C) object produces for
    ``states`` (old vocabulary), sent in order. IRac keeps the last message
    sent (its _prev), so toggle protocols toggle as on a real remote.

    ``record`` is an oracle record naming the legacy plugin and class.
    """
    pytest.importorskip("pyhvac.irhvac")
    module = importlib.import_module(f"pyhvac.plugins.{record['plugin']}")
    cls = getattr(module, record["class"])
    legacy = cls()
    status = dict(legacy.status)
    out = []
    for old in states:
        # Only IRac's memory of the last message sent carries over: the
        # glue's status and IRac's next state (which keep keys a state does
        # not mention) start fresh, as for a new object.
        legacy.status = dict(status)
        legacy.irac.next = cls().irac.next
        # Bypass the setters, as tools/oracle_generate.py does.
        legacy.to_set = dict(old)
        pulses = [int(x) for x in legacy.to_lirc(legacy.build_ircode())]
        out.append({**record, "state": old, "pulses": pulses})
    return out


def assert_sequence_matches_c(
    device, record, states, layouts, defects=(), adapt=lambda rec: rec
):
    """Send ``states`` in order through one persistent C object and through
    the port, each message with the one before it as ``previous``; every
    message must match (see ``assert_matches_oracle``). ``adapt`` maps each
    C record to the one the port is compared against (as the test's
    oracle comparison does)."""
    previous = None
    for rec in c_sequence(record, states):
        rec = adapt(rec)
        assert_matches_oracle(device, rec, layouts, defects, previous=previous)
        previous = state_from_record(device, rec["state"])


def sequence_params(name):
    """pytest params, one per legacy class of fixture ``name``: the class's
    first record and its old-vocabulary states in order and then back.
    Consecutive grid states differ in a key or two, so every toggle gets
    exercised both ways."""
    by_class = {}
    for rec in load_oracle(name):
        by_class.setdefault(rec["class"], []).append(rec)
    return [
        pytest.param(
            recs[0], [r["state"] for r in recs + recs[::-1]], id=f"{name}-{cls}"
        )
        for cls, recs in by_class.items()
    ]


def assert_matches_golden(device, record, state, previous=None):
    """Assert the port sends what a 0.1.x pure-Python class sent: ``record``
    is a golden fixture record (tests/fixtures/golden), ``state`` the
    HvacState its old-vocabulary state stands for, ``previous`` the state of
    the fresh legacy object it was built from (or None)."""
    command = device.encode(previous, state)
    assert list(command.signal.pulses) == record["pulses"], record["state"]
    assert to_broadlink(command.signal).hex() == record["broadlink"], record["state"]
