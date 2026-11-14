import datetime as dt
import json

from hvactest import names
from hvactest.log import SessionLog


def test_names_round_trip(tmp_path):
    rc = tmp_path / ".pyhvacrc"
    assert names.load(rc) == ({}, None)
    names.rename("AA:BB:CC:00:11:22", "Living room", rc)
    assert names.load(rc) == ({"aa:bb:cc:00:11:22": "Living room"}, None)


def test_renaming_keeps_other_keys(tmp_path):
    rc = tmp_path / ".pyhvacrc"
    rc.write_text(json.dumps({"other": [1, 2], "broadlink_names": {"x": "y"}}))
    names.rename("aa-bb-cc-00-11-22", "Bedroom", rc)
    data = json.loads(rc.read_text())
    assert data["other"] == [1, 2]
    assert data["broadlink_names"] == {"x": "y", "aa:bb:cc:00:11:22": "Bedroom"}


def test_an_empty_name_removes_it(tmp_path):
    rc = tmp_path / ".pyhvacrc"
    names.rename("aa:bb:cc:00:11:22", "Bedroom", rc)
    names.rename("aa:bb:cc:00:11:22", " ", rc)
    assert names.load(rc) == ({}, None)


def test_a_malformed_file_is_reported_and_left_alone(tmp_path):
    rc = tmp_path / ".pyhvacrc"
    rc.write_text("{not json")
    found, error = names.load(rc)
    assert found == {} and "cannot read" in error
    assert rc.read_text() == "{not json"  # loading never writes


def test_the_log_writes_nothing_unless_enabled(tmp_path):
    log = SessionLog(None)
    assert not log.enabled and log.write("send", code="x") is None
    assert list(tmp_path.iterdir()) == []


def test_the_log_appends_utc_json_lines(tmp_path):
    path = tmp_path / "session.jsonl"
    log = SessionLog(path)
    log.write("send", model="Gree/YAW1F", code="26...")
    log.write("verdict", verdict="worked", note="")
    lines = [json.loads(x) for x in path.read_text().splitlines()]
    assert [x["event"] for x in lines] == ["send", "verdict"]
    stamp = dt.datetime.fromisoformat(lines[0]["time"])
    assert stamp.utcoffset() == dt.timedelta(0)
    assert lines[0]["model"] == "Gree/YAW1F"
