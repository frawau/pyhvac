import gzip
import json
import random

import pytest

from oracle import ORACLE_DIR, check_against_oracle, load_oracle
from pyhvac.ir.codec import DecodeError, encode
from pyhvac.ir.model import Frame, Protocol, PulseDistance, Section

NEC = Protocol(
    "nec",
    {
        "nec": Section(
            PulseDistance(560, 560, 1690), header=(9000, 4500), footer=(560,), gap=40000
        )
    },
)
FRAMES = [Frame("nec", b"\x12\x34")]


def record(pulses):
    return {"state": {}, "pulses": list(pulses)}


def test_accepts_matching_jittered_record():
    rng = random.Random(7)
    pulses = [round(d * rng.uniform(0.95, 1.05)) for d in encode(NEC, FRAMES).pulses]
    check_against_oracle(NEC, record(pulses), FRAMES)


def test_rejects_different_bytes():
    pulses = encode(NEC, [Frame("nec", b"\x12\x35")]).pulses
    with pytest.raises(AssertionError):
        check_against_oracle(NEC, record(pulses), FRAMES)


def test_rejects_different_timing():
    pulses = [d * 2 for d in encode(NEC, FRAMES).pulses]
    with pytest.raises((AssertionError, DecodeError)):
        check_against_oracle(NEC, record(pulses), FRAMES)


def test_load_oracle_reads_gzipped_json(tmp_path, monkeypatch):
    monkeypatch.setattr("oracle.ORACLE_DIR", tmp_path)
    (tmp_path / "NEC.json.gz").write_bytes(
        gzip.compress(json.dumps([record([1, 2])]).encode())
    )
    assert load_oracle("NEC") == [record([1, 2])]


FILES = sorted(ORACLE_DIR.glob("*.json.gz"))


@pytest.mark.parametrize("path", FILES, ids=[p.name for p in FILES])
def test_fixture_is_well_formed(path):
    records = json.loads(gzip.decompress(path.read_bytes()))
    assert records
    for rec in records:
        assert {"plugin", "model", "class", "variant", "state", "pulses"} <= set(rec)
        assert rec["pulses"]
        assert all(isinstance(d, int) and d > 0 for d in rec["pulses"])
