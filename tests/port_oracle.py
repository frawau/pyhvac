"""Acceptance helper for protocol ports: a ported Device against the
IRremoteESP8266 reference pulses in tests/fixtures/oracle.

A difference between the port and the C output is accepted only when it is
declared as a ``Defect``: a field where the C library is known to deviate
from the documented protocol.
"""

from dataclasses import dataclass

import pytest

from oracle import check_against_oracle, load_oracle
from pyhvac.ir.codec import decode
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


def assert_matches_oracle(device, record, layouts, defects=()):
    """Assert the port reproduces ``record``.

    ``layouts`` gives one Layout (or None for bitless frames) per frame of the
    message, in order. Frames must be byte-identical, except for fields listed
    in ``defects`` (and the checksums they change).
    """
    state = state_from_record(device, record["state"])
    ours = device.frames(None, state, ())
    names = [f.section for f in ours]
    theirs = decode(device.PROTOCOL, record["pulses"], expected=names)
    allowed = {(d.field, d.ours, d.theirs) for d in defects}
    deviated = False
    for i, (a, b, layout) in enumerate(zip(ours, theirs, layouts)):
        if a.data == b.data:
            continue
        assert layout is not None, f"frame {i}: {a.data.hex()} != {b.data.hex()}"
        read_a, read_b = layout.read(a.data), layout.read(b.data)
        diffs = [k for k in read_a if read_a[k] != read_b[k]]
        unexplained = {
            k: (read_a[k], read_b[k])
            for k in diffs
            if (k, read_a[k], read_b[k]) not in allowed
        }
        assert not unexplained, f"frame {i}: {unexplained} for {record['state']}"
        # With C's values in the declared fields (and the checksum redone),
        # our frame must be exactly C's: nothing else may differ.
        expected = bytearray(a.data)
        for k in diffs:
            layout.write_raw(expected, k, layout.read_raw(b.data, k))
        if layout.checksum is not None:
            layout.checksum.apply(expected)
        assert bytes(expected) == b.data, f"frame {i}: more than {diffs} differs"
        deviated = True
    if not deviated:
        check_against_oracle(device.PROTOCOL, record, ours)
