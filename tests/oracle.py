"""Helpers to compare a Python protocol port against recorded C output."""

import gzip
import json
from pathlib import Path

from pyhvac.ir.codec import decode, encode

ORACLE_DIR = Path(__file__).parent / "fixtures" / "oracle"


def load_oracle(protocol_name):
    return json.loads(
        gzip.decompress((ORACLE_DIR / f"{protocol_name}.json.gz").read_bytes())
    )


def check_against_oracle(protocol, record, frames):
    """The C pulses decode to ``frames`` and our encoding lines up with them."""
    names = [f.section for f in frames]
    assert decode(protocol, record["pulses"], expected=names) == frames, record["state"]
    ours = encode(protocol, frames).pulses
    theirs = record["pulses"]
    assert len(ours) == len(theirs), (record["state"], len(ours), len(theirs))
    for i, (a, b) in enumerate(zip(ours, theirs)):
        assert abs(a - b) <= protocol.tolerance * a, (record["state"], i, a, b)
