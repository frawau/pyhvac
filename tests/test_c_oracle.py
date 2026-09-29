import pytest

import c_oracle
from oracle import load_oracle


def test_an_unrecorded_call_fails_loudly(monkeypatch, tmp_path):
    monkeypatch.setattr(c_oracle, "FIXTURES", tmp_path)
    monkeypatch.setattr(c_oracle, "_store", {})
    record = load_oracle("DAIKIN64")[0]
    with pytest.raises(AssertionError, match="not frozen"):
        c_oracle.c_sequence(record, [record["state"]])


def test_a_recorded_call_replays(monkeypatch, tmp_path):
    monkeypatch.setattr(c_oracle, "FIXTURES", tmp_path)
    monkeypatch.setattr(c_oracle, "_store", {})
    record = load_oracle("DAIKIN64")[0]
    key = c_oracle._key(
        "sequence", record["plugin"], record["class"], None, [record["state"]]
    )
    c_oracle._store["test_c_oracle"] = {key: [record["pulses"]]}
    (rec,) = c_oracle.c_sequence(record, [record["state"]])
    assert rec["pulses"] == record["pulses"]


def test_c_frozen_replays_a_labelled_result(monkeypatch, tmp_path):
    monkeypatch.setattr(c_oracle, "FIXTURES", tmp_path)
    monkeypatch.setattr(c_oracle, "_store", {})
    c_oracle._store["test_c_oracle"] = {c_oracle._key("frozen", "answer"): 42}
    assert c_oracle.c_frozen("answer") == 42
    with pytest.raises(AssertionError, match="not frozen"):
        c_oracle.c_frozen("other")
