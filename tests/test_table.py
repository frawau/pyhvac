import json
import time
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


def variant_file(tmp_path, monkeypatch, **changes):
    """A TableDevice on a copy of the fixture with ``changes`` applied."""
    monkeypatch.setattr(table, "fetch", None)
    data = json.loads(FIXTURE.read_text())
    data.update(changes)
    path = tmp_path / "variant.json"
    path.write_text(json.dumps(data))
    return TableDevice("Example", "EX-1", variant=2, path=path)


def with_commands(**extra):
    commands = json.loads(FIXTURE.read_text())["commands"]
    commands.update(extra)
    return commands


def test_an_on_code_is_sent_before_the_state_when_turning_on(tmp_path, monkeypatch):
    dev = variant_file(
        tmp_path, monkeypatch, commands=with_commands(on=[200, -300, 200])
    )
    on = HvacState(True, "cool", 17, fan="1")
    cmd = dev.encode(None, on)
    assert cmd.signal.pulses == (200, 300, 200, table.FINAL_SPACE, 101, 201)
    cmd = dev.encode(HvacState(False, "cool", 17), on)
    assert cmd.signal.pulses[:4] == (200, 300, 200, table.FINAL_SPACE)


def test_no_on_code_while_already_on_or_turning_off(tmp_path, monkeypatch):
    dev = variant_file(
        tmp_path, monkeypatch, commands=with_commands(on=[200, -300, 200])
    )
    on = HvacState(True, "cool", 17, fan="1")
    assert dev.encode(on, on).signal.pulses == (101, 201)
    off = HvacState(False, "cool", 17)
    assert dev.encode(None, off).signal.pulses[:2] == (9000, 4500)


def test_a_code_stored_without_a_temperature_is_served(tmp_path, monkeypatch):
    dev = variant_file(
        tmp_path, monkeypatch, commands=with_commands(fan_only={"low": [140, -240]})
    )
    cmd = dev.encode(None, HvacState(True, "fan", 17, fan="1"))
    assert cmd.signal.pulses == (140, 240)


def test_a_swing_level_without_temperatures_is_served(tmp_path, monkeypatch):
    commands = with_commands(fan_only={"low": {"off": [150, -250], "on": [151, -251]}})
    dev = variant_file(tmp_path, monkeypatch, commands=commands)
    state = HvacState(True, "fan", 17, fan="1", swing_v="swing")
    assert dev.encode(None, state).signal.pulses == (151, 251)


def test_modes_come_from_the_commands(tmp_path, monkeypatch):
    commands = {
        "off": [9000, -4500],
        "cold": {"low": {"off": {"16": [100, -200]}}},
        "humidity": {"low": {"off": {"16": [101, -201]}}},
        "fan": {"low": [102, -202]},
        "auto": {"low": {"off": {"16": [103, -203]}}},
    }
    dev = variant_file(
        tmp_path,
        monkeypatch,
        operationModes=["cool", "fan_only"],
        commands=commands,
    )
    assert set(dev.capabilities.modes) == {"cool", "dry", "fan", "auto"}
    state = HvacState(True, "fan", 16, fan="1")
    assert dev.encode(None, state).signal.pulses == (102, 202)


def test_a_stalled_fetch_gives_up_at_the_deadline(monkeypatch, tmp_path):
    monkeypatch.setenv("PYHVAC_CACHE", str(tmp_path))
    monkeypatch.setattr(table, "TIMEOUT", 0.2)
    monkeypatch.setattr(table, "fetch", lambda url: time.sleep(3) or b"{}")
    start = time.monotonic()
    with pytest.raises(OSError, match="codes/climate/9999.json"):
        device().capabilities
    assert time.monotonic() - start < 1.5


def test_a_failed_fetch_is_not_retried_at_once(monkeypatch, tmp_path):
    monkeypatch.setenv("PYHVAC_CACHE", str(tmp_path))
    calls = []

    def offline(url):
        calls.append(url)
        raise OSError("offline")

    monkeypatch.setattr(table, "fetch", offline)
    dev = device()
    for _ in range(3):
        with pytest.raises(OSError, match="codes/climate/9999.json"):
            dev.capabilities
    assert len(calls) == 1
