import json
from pathlib import Path

import pytest

from pyhvac.protocols import table
from pyhvac.protocols.table import TableDevice
from pyhvac.state import HvacState

FIXTURE = Path(__file__).parent / "fixtures" / "smartir" / "table.json"


@pytest.fixture
def upstream(monkeypatch, tmp_path):
    """Serve the fixture as upstream file 9999; record the URLs asked for."""
    monkeypatch.setenv("PYHVAC_CACHE", str(tmp_path))
    asked = []

    def fetch(url):
        asked.append(url)
        return FIXTURE.read_bytes()

    monkeypatch.setattr(table, "fetch", fetch)
    return asked


def device():
    return TableDevice("Example", "EX-1", variant=9999)


def test_capabilities_come_from_the_file(upstream):
    caps = device().capabilities
    assert caps.modes == ("cool", "auto", "fan")
    assert caps.fan.values == ("1", "2", "auto")
    assert caps.fan.label("2") == "high"
    assert caps.swing_v.values == ("off", "swing")
    assert caps.temperature.values == (16.0, 17.0, 18.0)


def test_a_state_sends_its_learned_code(upstream):
    cmd = device().encode(None, HvacState(True, "cool", 17, fan="1", swing_v="swing"))
    assert cmd.signal.pulses == (111, 211)
    assert cmd.signal.carrier == 38000


def test_off_ends_on_a_space(upstream):
    cmd = device().encode(None, HvacState(False, "cool", 17))
    assert cmd.signal.pulses == (9000, 4500, 560, 1690, 560, table.FINAL_SPACE)


def test_a_state_without_a_code_raises_naming_it(upstream):
    with pytest.raises(KeyError, match="no code"):
        device().encode(None, HvacState(True, "cool", 18, fan="auto"))


def test_fetched_once_from_master_and_cached(upstream, tmp_path):
    dev = device()
    dev.capabilities
    dev.encode(None, HvacState(True, "cool", 16, fan="1"))
    assert upstream == [
        "https://raw.githubusercontent.com/smartHomeHub/SmartIR/master/codes/climate/9999.json"
    ]
    assert (tmp_path / "smartir" / "climate" / "9999.json").exists()


def test_the_cache_serves_when_the_fetch_fails(upstream, monkeypatch):
    device().capabilities

    def offline(url):
        raise OSError("offline")

    monkeypatch.setattr(table, "fetch", offline)
    assert device().capabilities.modes == ("cool", "auto", "fan")


def test_a_failed_fetch_without_cache_names_the_url(monkeypatch, tmp_path):
    monkeypatch.setenv("PYHVAC_CACHE", str(tmp_path))

    def offline(url):
        raise OSError("offline")

    monkeypatch.setattr(table, "fetch", offline)
    with pytest.raises(OSError, match="codes/climate/9999.json"):
        device().capabilities


def test_construction_does_not_fetch(monkeypatch):
    monkeypatch.setattr(table, "fetch", None)
    device()


def test_a_local_file_needs_no_network(monkeypatch):
    monkeypatch.setattr(table, "fetch", None)
    dev = TableDevice("Example", "EX-1", variant=9999, path=FIXTURE)
    assert dev.capabilities.modes == ("cool", "auto", "fan")


def test_fahrenheit_keys_offer_celsius_setpoints(tmp_path, monkeypatch):
    monkeypatch.setattr(table, "fetch", None)
    data = json.loads(FIXTURE.read_text())
    data.update(minTemperature=60, maxTemperature=62)
    cool = data["commands"]["cool"]["low"]
    cool["off"] = {"60": [100, -200], "61": [101, -201], "62": [102, -202]}
    cool["on"] = {"60": [110, -210]}
    data["commands"] = {"cool": {"low": cool}}
    path = tmp_path / "f.json"
    path.write_text(json.dumps(data))
    dev = TableDevice("Example", "EX-1", variant=1, path=path)
    assert dev.capabilities.temperature.values == (15.6, 16.1, 16.7)
    cmd = dev.encode(None, HvacState(True, "cool", 16.0, fan="1"))
    assert cmd.signal.pulses == (101, 201)
    assert cmd.state.temperature == 16.1


def test_a_variant_is_required():
    with pytest.raises(ValueError):
        TableDevice("Example", "EX-1")


@pytest.mark.network
def test_a_real_upstream_file(monkeypatch, tmp_path):
    monkeypatch.setenv("PYHVAC_CACHE", str(tmp_path))
    dev = TableDevice("Toyotomi", "AKIRA GAN/GAG-A128 VL", variant=1000)
    caps = dev.capabilities
    state = HvacState(True, caps.modes[0], caps.temperature.min, fan=caps.fan.values[0])
    assert dev.encode(None, state).signal.pulses


def test_a_bad_download_falls_back_to_the_cache(upstream, monkeypatch):
    device().capabilities
    monkeypatch.setattr(table, "fetch", lambda url: b"<html>rate limited</html>")
    assert device().capabilities.modes == ("cool", "auto", "fan")


def test_an_unwritable_cache_still_serves(monkeypatch, tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("")
    monkeypatch.setenv("PYHVAC_CACHE", str(blocker))
    monkeypatch.setattr(table, "fetch", lambda url: FIXTURE.read_bytes())
    assert device().capabilities.modes == ("cool", "auto", "fan")


def test_the_cache_is_replaced_whole(upstream, tmp_path, monkeypatch):
    device().capabilities
    written = []
    real = Path.replace

    def replace(self, target):
        written.append((self.name, Path(target).name))
        return real(self, target)

    monkeypatch.setattr(Path, "replace", replace)
    device().capabilities
    ((partial, target),) = written
    assert partial.startswith("9999.json.") and partial.endswith(".tmp")
    assert target == "9999.json"
