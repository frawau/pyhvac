# SmartIR climate codes import — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every upstream SmartIR climate code file a verdict (covered, near, unknown, unsupported). Serve covered files with their pyhvac device and every other readable file with a `TableDevice` that fetches the file from upstream at runtime.

**Architecture:**
- A development tool, `tools/smartir/` (not shipped in the wheel), does the work:
  - fetches the upstream files into a cache;
  - turns their codes into pulses;
  - decodes the pulses with every pyhvac protocol;
  - fits the mapping (features, fan and swing labels, °C/°F keys) by bit distance;
  - gates each match by encoding, and names the layout fields that differ.
- The tool clusters the unknown files and writes a report and proposed `brands.py` rows.
- `pyhvac/protocols/table.py` serves a SmartIR file at runtime, sharing its code reader with the tool.
- `TemperatureRange` gains explicit °C `values`, which reach °F-stepped units while the state stays °C.

**Tech Stack:** Python ≥ 3.9, standard library only (urllib, zipfile, concurrent.futures), pytest, black. Reuses `tools/portkit.py` and `pyhvac.fields`.

**Spec:** `docs/superpowers/specs/2026-10-01-smartir-import-design.md`

**Branch:** `smartir` (forked from `phase4`). Every task commits on it.

**Provenance:** every code block below was run in a scratch worktree before the plan was written. With all eight tasks applied, the full suite gives 23105 passed and 64 skipped (`python -m pytest -q`, ~90 s). The importer on upstream master (2026-10-01, 358 files) gives:
- covered 4, near 196, unknown 143, unsupported 13;
- not JSON: 2680;
- 538 proposed rows, 39 name conflicts.

Upstream moves, so expect drift in these numbers.

## Global Constraints

- Metric only. `HvacState.temperature` is °C everywhere; °F exists only inside a device's lookup and at the edge (`fahrenheit()`). No °F value is stored or passed between modules.
- No SmartIR file is committed to this repo: not in tests, fixtures or docs. Test fixtures are hand-written (`tests/fixtures/smartir/table.json`) or built from pyhvac's own encoders.
- Table devices fetch `https://raw.githubusercontent.com/smartHomeHub/SmartIR/master/codes/climate/<n>.json`. There is no pinning and no hash; upstream is responsible for content.
- No new runtime dependencies. `tools/` is not packaged (`include = ["pyhvac*"]` stays).
- The core codec stays strict. The lenient Broadlink reader lives in `pyhvac/protocols/table.py`, not in `pyhvac/ir/formats.py`.
- Xiaomi compressed codes are out of scope: verdict "unsupported", no table row.
- Run `black` on every Python file you touch.
- Tests never touch the network unless run with `--network`.

## Review Focus

1. **First use of a table device blocks on the network** (up to the 10 s timeout) inside whatever thread calls `capabilities` or `encode`.
   - Expect: an `OSError` naming the URL on failure, never a hang past the timeout; the cached copy is used when present.
   - Pinned by `test_a_failed_fetch_without_cache_names_the_url` and `test_the_cache_serves_when_the_fetch_fails` (Task 2).
   - The module docstring tells async consumers (Home Assistant) to call these from an executor.
2. **Upstream answers with something that is not the file** (rate limit page, 404 body).
   - Expect: fall back to the cache, else the URL error.
   - Pinned by `test_a_bad_download_falls_back_to_the_cache` (Task 2).
3. **Unwritable or read-only cache directory** (containers).
   - Expect: the device still works, uncached.
   - Pinned by `test_an_unwritable_cache_still_serves` (Task 2).
4. **Two processes caching the same file at once**: a reader must never see half a file.
   - Pinned by `test_the_cache_is_replaced_whole` (Task 2).
5. **A `TemperatureRange` built with values outside its own min/max** would make `snap` return a value outside the range.
   - Pinned by `test_values_must_lie_within_min_and_max` (Task 1).

## Rulings made while planning (open to the author's correction)

- **Near files get table rows now.** A near file decodes with a pyhvac protocol, but no mapping reproduces every code. It is served by `TableDevice` until a gap fix (a later plan) turns it covered; the re-run then proposes the protocol row in its place.
- **Fitting by bit distance, not by layout-field inference.** Coordinate descent over features, fan labels and swing labels minimises differing non-checksum bits on a sample of codes; encoding every code is the gate. The spec's per-field functional checks become the per-field gap counts in the report.
- **The °F hypotheses implemented** are "keys °C" and "keys °F, unit encodes °C". "Unit encodes °F" needs the per-protocol `units` option, which belongs to the gap-fix plans; such files show up as near with a temperature or fahrenheit gap.
- **Table rows use kind "unit".** SmartIR lists units.
- **Brands use pyhvac's existing spelling** when the normalised name matches; otherwise the file's spelling.
- **Name conflicts** (another device already holds the name) are reported in `docs/smartir/report.md`, not resolved.

## File structure

```
pyhvac/state.py                 + fahrenheit(), TemperatureRange.values / .fahrenheit()
pyhvac/protocols/table.py       new: SmartIR code reader, fetch/cache, TableDevice
pyhvac/brands.py                + TableDevice import and rows (Task 8)
tools/smartir/__init__.py       new
tools/smartir/codes.py          SmartIRFile / Code, parse()
tools/smartir/match.py          candidates, decode, fit, verify, gaps, match()
tools/smartir/cluster.py        unknown files -> timing/shape clusters
tools/smartir/fetch.py          upstream archive -> cache
tools/smartir/report.py         CLI: run all, write report.md and rows.py
tests/conftest.py               tools/ on sys.path (exists) + --network option
pyproject.toml                  + pytest "network" marker
tests/fixtures/smartir/table.json   hand-written SmartIR-format fixture
tests/test_fahrenheit_range.py, test_table.py, test_smartir_codes.py,
tests/test_smartir_match.py, test_smartir_cluster.py, test_smartir_fetch.py,
tests/test_smartir_report.py, tests/test_brands.py (+1 test)
docs/smartir/report.md          generated by Task 8, committed
```

---

### Task 1: °F-stepped temperatures that stay °C

**Files:**
- Modify: `pyhvac/state.py` (`TemperatureRange`, a new `fahrenheit()` above it; `Optional` is already imported)
- Test: `tests/test_fahrenheit_range.py`

**Interfaces:**
- Produces:
  - `pyhvac.state.fahrenheit(celsius: float) -> int`;
  - `TemperatureRange(min, max, decimals=(0,), values: Optional[Tuple[float, ...]] = None)`;
  - `TemperatureRange.fahrenheit(lo_f: int, hi_f: int) -> TemperatureRange`.
- With `values`, `snap()` returns the nearest listed value (ties to the lower one) after clamping to [min, max].

- [ ] **Step 1: Write the failing test** — `tests/test_fahrenheit_range.py`:

```python
import pytest

from pyhvac.state import TemperatureRange, fahrenheit


def test_fahrenheit_range_offers_one_celsius_setpoint_per_whole_fahrenheit():
    r = TemperatureRange.fahrenheit(60, 86)
    assert r.values[:3] == (15.6, 16.1, 16.7)
    assert (r.min, r.max) == (15.6, 30.0)
    assert len(r.values) == 27


def test_round_trip_is_exact_for_0_to_120_f():
    r = TemperatureRange.fahrenheit(0, 120)
    assert [fahrenheit(c) for c in r.values] == list(range(0, 121))


@pytest.mark.parametrize(
    "celsius, snapped", [(24.0, 23.9), (24.2, 24.4), (10.0, 15.6), (40.0, 30.0)]
)
def test_snap_picks_the_nearest_offered_setpoint(celsius, snapped):
    assert TemperatureRange.fahrenheit(60, 86).snap(celsius) == snapped


def test_explicit_values_must_be_sorted_unique_tenths():
    with pytest.raises(ValueError):
        TemperatureRange(16.0, 17.0, values=(17.0, 16.0))
    with pytest.raises(ValueError):
        TemperatureRange(16.0, 17.0, values=(16.0, 16.05))


def test_values_must_lie_within_min_and_max():
    with pytest.raises(ValueError):
        TemperatureRange(16.0, 20.0, (0,), (16.0, 21.0))
```

- [ ] **Step 2: Run it.** `python -m pytest -q tests/test_fahrenheit_range.py`. Expected: FAIL, `ImportError: cannot import name 'fahrenheit'`.

- [ ] **Step 3: Implement.** In `pyhvac/state.py`:
  - add `fahrenheit()` just above `TemperatureRange`;
  - add the `values` field and the `fahrenheit` classmethod;
  - put the `values` checks at the top of `__post_init__`;
  - put the `values` branch in `snap` right after the clamp.

  The resulting code:

```python
def fahrenheit(celsius):
    """The whole °F a °C setpoint stands for (edge conversion only)."""
    return round(celsius * 9 / 5 + 32)


@dataclass(frozen=True)
class TemperatureRange:
    """Allowed setpoints: [min, max] in °C, with the listed tenths only, or
    exactly ``values`` (sorted °C setpoints, one decimal) when given."""

    min: float
    max: float
    decimals: Tuple[int, ...] = (0,)
    values: Optional[Tuple[float, ...]] = None

    @classmethod
    def fahrenheit(cls, lo_f, hi_f):
        """One °C setpoint per whole °F from ``lo_f`` to ``hi_f``: for a unit
        that steps in °F, reachable while the state stays in °C."""
        values = tuple(round((f - 32) * 5 / 9, 1) for f in range(lo_f, hi_f + 1))
        decimals = tuple(sorted({round(v * 10) % 10 for v in values}))
        return cls(values[0], values[-1], decimals, values)

    def __post_init__(self):
        if self.values is not None:
            tenths = [_tenths(v, "values") for v in self.values]
            if (
                not tenths
                or tenths != sorted(set(tenths))
                or any(abs(t - v * 10) > 1e-6 for t, v in zip(tenths, self.values))
            ):
                raise ValueError(
                    f"values must be sorted unique setpoints with one decimal, "
                    f"got {self.values!r}"
                )
            if tenths[0] < round(self.min * 10) or tenths[-1] > round(self.max * 10):
                raise ValueError(
                    f"values must lie within [{self.min}, {self.max}], "
                    f"got {self.values!r}"
                )
            object.__setattr__(self, "values", tuple(t / 10 for t in tenths))
        decimals = tuple(sorted(self.decimals))
        if (
            not decimals
            or len(set(decimals)) != len(decimals)
            or any(isinstance(d, bool) or not isinstance(d, int) for d in decimals)
            or not all(0 <= d <= 9 for d in decimals)
        ):
            raise ValueError(
                f"decimals must be unique integers 0-9, got {self.decimals!r}"
            )
        object.__setattr__(self, "decimals", decimals)
        lo, hi = _tenths(self.min, "min"), _tenths(self.max, "max")
        if lo > hi:
            raise ValueError(f"min {self.min} is above max {self.max}")
        for name, t in (("min", lo), ("max", hi)):
            if t % 10 not in decimals:
                raise ValueError(
                    f"{name} must use one of the allowed decimals {decimals}"
                )
        object.__setattr__(self, "min", lo / 10)
        object.__setattr__(self, "max", hi / 10)

    def snap(self, celsius):
        """Nearest allowed setpoint, ties to the lower one, clamped to [min, max]."""
        lo, hi = round(self.min * 10), round(self.max * 10)
        t = min(max(_tenths(celsius, "temperature"), lo), hi)
        if self.values is not None:
            return min(self.values, key=lambda v: (abs(round(v * 10) - t), v))
```

  (`snap` continues unchanged after the inserted `if self.values is not None:` branch.)

- [ ] **Step 4: Run it.** `python -m pytest -q tests/test_fahrenheit_range.py tests/test_state.py`. Expected: PASS (all).

- [ ] **Step 5: Format and commit.**

```bash
black pyhvac/state.py tests/test_fahrenheit_range.py
git add pyhvac/state.py tests/test_fahrenheit_range.py
git commit -m "state: TemperatureRange with explicit °C values; °F-stepped ranges"
```

---

### Task 2: TableDevice — serve a SmartIR file fetched from upstream

**Files:**
- Create: `pyhvac/protocols/table.py`
- Create: `tests/fixtures/smartir/table.json` (hand-written; not a SmartIR file)
- Modify: `tests/conftest.py` (add the `--network` option), `pyproject.toml` (marker)
- Test: `tests/test_table.py`

**Interfaces:**
- Consumes: `TemperatureRange(..., values=...)` and `fahrenheit()` (Task 1).
- Produces (all in `pyhvac.protocols.table`):
  - `Key(mode, fan, swing, temperature)`: a frozen dataclass; `mode` is SmartIR's name or `"off"`; `temperature` is a float or None.
  - `UnsupportedFormat(ValueError)`.
  - `to_pulses(code, controller, encoding) -> list[int]`: unsigned µs, mark first. It raises `UnsupportedFormat` for Xiaomi and `ValueError` for an unreadable code.
  - `walk(commands) -> iterator of (Key, stored code)`.
  - `fetch(url) -> bytes`: the network seam tests replace.
  - `cache_dir() -> Path`: `$PYHVAC_CACHE`, else `$XDG_CACHE_HOME/pyhvac`, else `~/.cache/pyhvac`.
  - `load(number, path=None) -> dict`.
  - `TableDevice(brand, model, variant=<file number>, path=None)`.
  - Constants `URL`, `FINAL_SPACE`, `CARRIER`, `TIMEOUT`.
- Capabilities from the file:
  - modes, through `MODES` (heat_cool → auto, fan_only → fan);
  - fan labels → `"auto"` by name, the rest `"1".."n"` in file order;
  - swing labels → `off`/`swing`/`auto` by name ("on" → swing), the rest levels;
  - temperatures: the °C value of each key (°F keys when `maxTemperature > 50`).
- `encode(previous, target)` looks the state up. It raises `KeyError` naming a missing key; `previous` is ignored.

- [ ] **Step 1: Write the fixture** — `tests/fixtures/smartir/table.json`:

```json
{
  "manufacturer": "Example",
  "supportedModels": ["EX-1"],
  "supportedController": "ESPHome",
  "commandsEncoding": "Raw",
  "minTemperature": 16,
  "maxTemperature": 18,
  "precision": 1,
  "operationModes": ["cool", "heat_cool", "fan_only"],
  "fanModes": ["low", "high", "auto"],
  "swingModes": ["off", "on"],
  "commands": {
    "off": [9000, -4500, 560, -1690, 560],
    "cool": {
      "low": {
        "off": {"16": [100, -200], "17": [101, -201], "18": [102, -202]},
        "on": {"16": [110, -210], "17": [111, -211], "18": [112, -212]}
      },
      "auto": {
        "off": {"16": [120, -220], "17": [121, -221]}
      }
    },
    "heat_cool": {
      "high": {"off": {"17": [130, -230]}}
    },
    "fan_only": {
      "low": {"off": {"16": [140, -240]}}
    }
  }
}
```

- [ ] **Step 2: Add the `--network` option.** Replace `tests/conftest.py` with:

```python
import sys
from pathlib import Path

import pytest

# tools/ holds portkit and the smartir importer, which tests import.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))


def pytest_addoption(parser):
    parser.addoption(
        "--network",
        action="store_true",
        help="run the tests that fetch from the internet",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--network"):
        return
    skip = pytest.mark.skip(reason="needs --network")
    for item in items:
        if "network" in item.keywords:
            item.add_marker(skip)
```

and append to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = ["network: fetches from the internet (run with --network)"]
```

- [ ] **Step 3: Write the failing tests** — `tests/test_table.py`:

```python
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
```

- [ ] **Step 4: Run them.** `python -m pytest -q tests/test_table.py`. Expected: FAIL, `ModuleNotFoundError: No module named 'pyhvac.protocols.table'`.

- [ ] **Step 5: Implement** — `pyhvac/protocols/table.py`:

```python
"""Devices served from a SmartIR climate code file instead of a protocol.

A SmartIR file holds one learned code per state: ``commands["off"]`` and
``commands[mode][fan][swing?][temperature]``. Codes are Broadlink packets
(base64), or signed µs lists (ESPHome: JSON, LOOKin: space separated).
Xiaomi's compressed formats cannot be turned into pulses.

The file is fetched from upstream SmartIR ``master`` on first use (upstream
is responsible for its content) and cached; the cached copy is used when
the fetch fails. The first ``capabilities`` or ``encode`` of a device may
block on the network for up to TIMEOUT seconds: async callers run it in an
executor. Temperatures stay °C: a file keyed in °F offers the °C
setpoint of each of its °F keys.
"""

import base64
import binascii
import json
import os
import struct
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..device import Command, Device
from ..ir.formats import _BROADLINK_TICK_DEN, _BROADLINK_TICK_NUM
from ..ir.model import Signal
from ..state import (
    Capabilities,
    Choice,
    HvacState,
    SWING_KEYWORDS,
    TemperatureRange,
    fahrenheit,
)

URL = "https://raw.githubusercontent.com/smartHomeHub/SmartIR/master/codes/climate/{}.json"
CARRIER = 38000
TIMEOUT = 10  # s, per fetch
FINAL_SPACE = 100000  # µs, closes a learned code that ends on a mark
FAHRENHEIT_ABOVE = 50  # a file whose keys go above this is keyed in °F
MODES = {
    "auto": "auto",
    "heat_cool": "auto",
    "cool": "cool",
    "heat": "heat",
    "dry": "dry",
    "fan_only": "fan",
    "fan": "fan",
}


class UnsupportedFormat(ValueError):
    """A code format that cannot be turned into pulses."""


@dataclass(frozen=True)
class Key:
    mode: str  # SmartIR's mode name, or "off"
    fan: Optional[str]
    swing: Optional[str]
    temperature: Optional[float]


def _broadlink_pulses(packet):
    """µs pulses of a Broadlink IR packet, leniently: learned codes in the
    wild are often truncated (declared length past the data, a cut 2-byte
    value); keep what is there."""
    if len(packet) < 4 or packet[0] != 0x26:
        raise ValueError("not a Broadlink IR packet")
    (length,) = struct.unpack("<H", packet[2:4])
    body = packet[4 : 4 + length]
    pulses, i = [], 0
    while i < len(body):
        ticks = body[i]
        i += 1
        if ticks == 0:
            if i + 2 > len(body):
                break
            (ticks,) = struct.unpack(">H", body[i : i + 2])
            i += 2
        pulses.append(round(ticks * _BROADLINK_TICK_DEN / _BROADLINK_TICK_NUM))
    return pulses


def to_pulses(code, controller, encoding):
    """Unsigned µs pulses (mark first) for one stored code."""
    if controller == "Xiaomi":
        raise UnsupportedFormat("Xiaomi compressed IR codes")
    if not isinstance(code, (str, list)):
        raise ValueError(f"not a code: {code!r}")
    if encoding == "Base64":
        text = code.strip()
        try:
            packet = base64.b64decode(text + "=" * (-len(text) % 4), validate=False)
        except (binascii.Error, ValueError) as exc:
            raise ValueError(f"bad base64: {exc}") from None
        pulses = _broadlink_pulses(packet)
    elif isinstance(code, list):
        pulses = code
    else:
        text = code.strip()
        pulses = json.loads(text) if text.startswith("[") else text.split()
    pulses = [abs(int(p)) for p in pulses]
    if not pulses or any(p <= 0 for p in pulses):
        raise ValueError("empty code or a zero-length pulse")
    return pulses


def _temperature(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def walk(commands):
    """(Key, stored code) for every leaf of a commands tree."""
    for mode, sub in commands.items():
        if not isinstance(sub, dict):
            yield Key(mode, None, None, None), sub
            continue
        for fan, sub2 in sub.items():
            if not isinstance(sub2, dict):
                yield Key(mode, fan, None, None), sub2
                continue
            for k, sub3 in sub2.items():
                if isinstance(sub3, dict):  # a swing level
                    for t, code in sub3.items():
                        yield Key(mode, fan, k, _temperature(t)), code
                else:
                    yield Key(mode, fan, None, _temperature(k)), sub3


def fahrenheit_keyed(data):
    return (data.get("maxTemperature") or 0) > FAHRENHEIT_ABOVE


def cache_dir():
    """``$PYHVAC_CACHE``, else ``$XDG_CACHE_HOME/pyhvac``, else ~/.cache/pyhvac."""
    if os.environ.get("PYHVAC_CACHE"):
        return Path(os.environ["PYHVAC_CACHE"])
    base = os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache"
    return Path(base) / "pyhvac"


def fetch(url):
    """The bytes at ``url`` (the seam tests replace)."""
    with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
        return response.read()


def load(number, path=None):
    """A SmartIR climate file as parsed JSON: ``path`` if given, else
    upstream master (cached), else the cached copy."""
    if path is not None:
        return json.loads(Path(path).read_text())
    url = URL.format(number)
    cached = cache_dir() / "smartir" / "climate" / f"{number}.json"
    try:
        raw = fetch(url)
        data = json.loads(raw)
    except (OSError, ValueError) as exc:
        if cached.exists():
            return json.loads(cached.read_text())
        raise OSError(f"cannot fetch SmartIR climate file {url}: {exc}") from exc
    try:
        cached.parent.mkdir(parents=True, exist_ok=True)
        partial = cached.with_name(f"{cached.name}.{os.getpid()}.tmp")
        partial.write_bytes(raw)
        partial.replace(cached)  # readers never see a half-written file
    except OSError:
        pass  # caching is best effort
    return data


def _levels(labels, keywords, aliases):
    """Canonical value -> file label: keywords by name, the rest "1".."n"."""
    out, n = {}, 0
    for label in labels:
        name = aliases.get(label.casefold(), label.casefold())
        if name in keywords and name not in out:
            out[name] = label
        else:
            n += 1
            out[str(n)] = label
    return out


class TableDevice(Device):
    """Serves the learned codes of upstream SmartIR climate file ``variant``
    (its number). A state with no code raises; it never guesses."""

    def __init__(self, brand, model, variant=None, path=None):
        super().__init__(brand, model)
        if variant is None:
            raise ValueError(f"{brand}/{model}: a table device needs variant=")
        self.variant = str(variant)
        self._path = path
        self._data = None

    def _load(self):
        if self._data is None:
            data = load(self.variant, self._path)
            self._fahrenheit = fahrenheit_keyed(data)
            codes = {}
            for key, stored in walk(data.get("commands", {})):
                codes[key] = stored
            self._codes = codes
            self._controller = data.get("supportedController", "")
            self._encoding = data.get("commandsEncoding", "")
            self._modes = {}
            for name in data.get("operationModes", ()):
                if name in MODES and MODES[name] not in self._modes:
                    self._modes[MODES[name]] = name
            self._fans = _levels(data.get("fanModes", ()), ("auto",), {})
            self._swings = _levels(
                data.get("swingModes", ()), SWING_KEYWORDS, {"on": "swing"}
            )
            temps = sorted(
                {
                    self._celsius(k.temperature)
                    for k in codes
                    if k.temperature is not None
                }
            )
            if not self._modes or not temps:
                raise ValueError(f"SmartIR climate file {self.variant} has no codes")
            self._capabilities = Capabilities(
                modes=tuple(self._modes),
                temperature=TemperatureRange(
                    temps[0],
                    temps[-1],
                    tuple(sorted({round(t * 10) % 10 for t in temps})),
                    tuple(temps),
                ),
                fan=Choice(tuple(self._fans), self._fans) if self._fans else None,
                swing_v=(
                    Choice(tuple(self._swings), self._swings) if self._swings else None
                ),
            )
            self._data = data
        return self._data

    def _celsius(self, t):
        return round((t - 32) * 5 / 9, 1) if self._fahrenheit else float(t)

    @property
    def capabilities(self):
        self._load()
        return self._capabilities

    def encode(self, previous, target, actions=()):
        self._load()
        actions = self._check_actions(actions)
        target = self.normalise(target)
        if not target.power:
            key = Key("off", None, None, None)
        else:
            t = target.temperature
            key = Key(
                self._modes[target.mode],
                self._fans.get(target.fan),
                self._swings.get(target.swing_v),
                float(fahrenheit(t)) if self._fahrenheit else t,
            )
        if key not in self._codes:
            raise KeyError(f"SmartIR climate file {self.variant} has no code for {key}")
        pulses = to_pulses(self._codes[key], self._controller, self._encoding)
        if len(pulses) % 2:
            pulses.append(FINAL_SPACE)
        return Command(Signal(CARRIER, tuple(pulses)), target)
```

- [ ] **Step 6: Run them.** `python -m pytest -q tests/test_table.py`. Expected: `14 passed, 1 skipped`. Then `python -m pytest -q tests/test_table.py --network`. Expected: `15 passed` (it fetches upstream file 1000; skip this check offline and say so in the ledger).

- [ ] **Step 7: Format and commit.**

```bash
black pyhvac/protocols/table.py tests/test_table.py tests/conftest.py
git add pyhvac/protocols/table.py tests/test_table.py tests/conftest.py pyproject.toml tests/fixtures/smartir/table.json
git commit -m "TableDevice: serve a SmartIR climate file fetched from upstream master"
```

---

### Task 3: tools/smartir/codes.py — a SmartIR file as keys and pulses

**Files:**
- Create: `tools/smartir/__init__.py`, `tools/smartir/codes.py`
- Test: `tests/test_smartir_codes.py`

**Interfaces:**
- Consumes: `Key`, `UnsupportedFormat`, `to_pulses` and `walk` from `pyhvac.protocols.table` (Task 2).
- Produces (`smartir.codes`; tests import `smartir` because `tests/conftest.py` puts `tools/` on `sys.path`):
  - `Code(key: Key, pulses: tuple[int, ...])`;
  - `SmartIRFile(number, manufacturer, models, controller, encoding, min_temperature, max_temperature, precision, modes, fans, swings, codes, skipped, unsupported=None)`;
  - `parse(number: int, data: dict) -> SmartIRFile`;
  - re-exports `Key`, `UnsupportedFormat` and `to_pulses`.

- [ ] **Step 1: Write the failing tests** — `tests/test_smartir_codes.py`:

```python
import base64

import pytest

from pyhvac.ir.formats import broadlink_packet
from smartir.codes import Key, UnsupportedFormat, parse, to_pulses

PULSES = [3000, 1500, 500, 500, 500, 1500, 500, 100000]


def b64(pulses):
    return base64.b64encode(broadlink_packet(pulses)).decode()


def test_broadlink_base64_becomes_pulses():
    out = to_pulses(b64(PULSES), "Broadlink", "Base64")
    assert len(out) == len(PULSES)
    assert all(abs(a - b) <= 0.02 * b + 31 for a, b in zip(out, PULSES))


@pytest.mark.parametrize(
    "controller, code",
    [
        ("ESPHome", "[3000, -1500, 500, -500, 500, -1500, 500, -100000]"),
        ("LOOKin", "3000 -1500 500 -500 500 -1500 500 -100000"),
    ],
)
def test_signed_raw_lists_become_pulses(controller, code):
    assert to_pulses(code, controller, "Raw") == PULSES


def test_xiaomi_raw_is_unsupported():
    with pytest.raises(UnsupportedFormat):
        to_pulses("Z6WHAQAA", "Xiaomi", "Raw")


def test_parse_walks_modes_fans_swings_and_temperatures():
    data = {
        "manufacturer": "Acme",
        "supportedModels": ["X1"],
        "supportedController": "Broadlink",
        "commandsEncoding": "Base64",
        "minTemperature": 16,
        "maxTemperature": 17,
        "precision": 1,
        "operationModes": ["cool"],
        "fanModes": ["low", "high"],
        "swingModes": ["off", "on"],
        "commands": {
            "off": b64(PULSES),
            "cool": {
                "low": {"off": {"16": b64(PULSES), "17": "!!bad!!"}},
                "high": {"on": {"16": b64(PULSES)}},
            },
        },
    }
    f = parse(42, data)
    assert f.number == 42 and f.manufacturer == "Acme" and f.models == ("X1",)
    keys = [c.key for c in f.codes]
    assert Key("off", None, None, None) in keys
    assert Key("cool", "low", "off", 16.0) in keys
    assert Key("cool", "high", "on", 16.0) in keys
    assert f.skipped == 1 and len(f.codes) == 3


def test_parse_without_swing_level():
    data = {
        "supportedController": "Broadlink",
        "commandsEncoding": "Base64",
        "commands": {"heat": {"auto": {"20": b64(PULSES)}}},
    }
    (code,) = parse(1, data).codes
    assert code.key == Key("heat", "auto", None, 20.0)


def test_missing_base64_padding_is_tolerated():
    code = b64(PULSES).rstrip("=")
    assert len(to_pulses(code, "Broadlink", "Base64")) == len(PULSES)


def test_a_truncated_packet_keeps_the_pulses_it_has():
    packet = bytearray(broadlink_packet(PULSES))
    packet[2] += 4  # declared length overruns the data
    code = base64.b64encode(bytes(packet[: 4 + 8])).decode()  # cut inside the body
    out = to_pulses(code, "Broadlink", "Base64")
    assert 0 < len(out) < len(PULSES)


def test_a_null_code_is_skipped():
    data = {
        "supportedController": "Broadlink",
        "commandsEncoding": "Base64",
        "commands": {"off": None, "heat": {"auto": {"20": b64(PULSES)}}},
    }
    f = parse(1, data)
    assert len(f.codes) == 1 and f.skipped == 1
```

- [ ] **Step 2: Run them.** `python -m pytest -q tests/test_smartir_codes.py`. Expected: FAIL, `ModuleNotFoundError: No module named 'smartir'`.

- [ ] **Step 3: Implement.** `tools/smartir/__init__.py`:

```python
"""Importer for SmartIR climate code files (development tool, not shipped)."""
```

`tools/smartir/codes.py`:

```python
"""A SmartIR climate code file as keys and µs pulses.

The reading of stored codes is shared with pyhvac.protocols.table, which
serves such files at runtime.
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple

from pyhvac.protocols.table import Key, UnsupportedFormat, to_pulses, walk

__all__ = ["Code", "Key", "SmartIRFile", "UnsupportedFormat", "parse", "to_pulses"]


@dataclass(frozen=True)
class Code:
    key: Key
    pulses: Tuple[int, ...]


@dataclass(frozen=True)
class SmartIRFile:
    number: int
    manufacturer: str
    models: Tuple[str, ...]
    controller: str
    encoding: str
    min_temperature: Optional[float]
    max_temperature: Optional[float]
    precision: Optional[float]
    modes: Tuple[str, ...]
    fans: Tuple[str, ...]
    swings: Tuple[str, ...]
    codes: Tuple[Code, ...] = field(repr=False)
    skipped: int  # codes that could not be turned into pulses
    unsupported: Optional[str] = None  # why no code could be read at all


def parse(number, data):
    controller = data.get("supportedController", "")
    encoding = data.get("commandsEncoding", "")
    codes, skipped, unsupported = [], 0, None
    for key, stored in walk(data.get("commands", {})):
        try:
            codes.append(Code(key, tuple(to_pulses(stored, controller, encoding))))
        except UnsupportedFormat as exc:
            unsupported = str(exc)
            skipped += 1
        except (ValueError, TypeError):
            skipped += 1
    return SmartIRFile(
        number=number,
        manufacturer=data.get("manufacturer", ""),
        models=tuple(data.get("supportedModels", ())),
        controller=controller,
        encoding=encoding,
        min_temperature=data.get("minTemperature"),
        max_temperature=data.get("maxTemperature"),
        precision=data.get("precision"),
        modes=tuple(data.get("operationModes", ())),
        fans=tuple(data.get("fanModes", ())),
        swings=tuple(data.get("swingModes", ())),
        codes=tuple(codes),
        skipped=skipped,
        unsupported=unsupported if not codes else None,
    )
```

- [ ] **Step 4: Run them.** `python -m pytest -q tests/test_smartir_codes.py`. Expected: PASS (9).

- [ ] **Step 5: Format and commit.**

```bash
black tools/smartir tests/test_smartir_codes.py
git add tools/smartir tests/test_smartir_codes.py
git commit -m "smartir tool: parse climate files into keys and pulses"
```

---

### Task 4: tools/smartir/match.py — decode, fit, verify, name the gaps

**Files:**
- Create: `tools/smartir/match.py`
- Test: `tests/test_smartir_match.py`

**Interfaces:**
- Consumes:
  - `smartir.codes.Key`, `Code` and `SmartIRFile` (Task 3);
  - `pyhvac.brands.MODELS`;
  - `pyhvac.fields.Joined` and `checksum_bits`;
  - `pyhvac.ir.codec.decode`.
- Produces:
  - `candidates() -> list[Candidate]`: one per distinct (Device class, variant); `Candidate.name` is `"Class"` or `"Class/variant"`.
  - `decode_code(candidate, pulses) -> tuple[bytes, ...] | None`.
  - `match(smartir_file, candidates) -> Match`.
  - `Match` fields:
    - `verdict`: "covered", "near", "unknown" or "unsupported";
    - `candidate` (name), `units` ("C"/"F"), `fans` (label → value), `swings` (label → value), `features` (dict);
    - `decoded`, `verified`, `usable`;
    - `unexplained`: the first 10 keys not reproduced;
    - `gaps`: field name → number of codes. A name is `"frames"` for a shape mismatch, and `"byte i bit b"` where no layout field owns the bit.
- How a match is made:
  1. A candidate must decode ≥ 90 % of the codes, in full or as a prefix cut after a space ≥ 7000 µs.
  2. Coordinate descent minimises the differing non-checksum bits on ≤ 24 sampled codes. It runs over each fan label, each swing label, then each feature, for 2 passes.
  3. Every code is encoded with `device.frames(None, normalise(state), ())` and compared.
  4. Off codes match any off state over the file's modes × setpoints × mapped fans and swings. A learned off code carries the last state, which the file does not record.
- Ranking and selection:
  - a candidate whose frames differ in shape for more than half the decoded codes is dropped;
  - candidates rank by (not unknown, verified, fewest gap counts);
  - the first covered result returns at once.

- [ ] **Step 1: Write the failing tests** — `tests/test_smartir_match.py`. The files are synthetic, built from pyhvac's own encoders: a plain file, constant features, °F keys, a remote variant, one swapped code, and a field pyhvac never sets.

```python
import dataclasses
import random

import pytest

from pyhvac import brands, registry
from pyhvac.ir.codec import encode as ir_encode
from pyhvac.protocols.electra import ELECTRA_AC_LAYOUT
from pyhvac.state import HvacState
from smartir.codes import Code, Key, SmartIRFile
from smartir.match import candidates, match

CANDIDATES = candidates()
FANS = {"low": "1", "mid": "2", "high": "3", "auto": "auto"}


def synthetic(brand, model, keys_in_f=False, features=None, tamper=None):
    """A SmartIR file the way someone would learn it from this device;
    ``tamper`` may rewrite each frame's bytes first."""
    dev = registry.get_device(brand, model)

    def pulses(state):
        if tamper is None:
            return dev.encode(None, state).signal.pulses
        frames = dev.frames(None, dev.normalise(state), ())
        frames = [dataclasses.replace(f, data=tamper(f.data)) for f in frames]
        return ir_encode(dev.PROTOCOL, frames).pulses

    codes = []
    temps = range(61, 86, 2) if keys_in_f else range(17, 30)
    for mode in ("cool", "heat"):
        for label, fan in FANS.items():
            for t in temps:
                c = round((t - 32) * 5 / 9, 1) if keys_in_f else float(t)
                state = HvacState(True, mode, c, fan=fan, features=features or {})
                codes.append(
                    Code(Key(mode, label, None, float(t)), tuple(pulses(state)))
                )
    off = HvacState(False, "cool", 24.0, features=features or {})
    codes.append(Code(Key("off", None, None, None), tuple(pulses(off))))
    return SmartIRFile(
        1,
        brand,
        (model,),
        "Broadlink",
        "Base64",
        min(temps),
        max(temps),
        1,
        ("cool", "heat"),
        tuple(FANS),
        (),
        tuple(codes),
        0,
    )


def test_a_file_learned_from_a_pyhvac_device_is_covered():
    m = match(synthetic("Electra", registry.models("Electra")[0]), CANDIDATES)
    assert m.verdict == "covered" and m.candidate == "ElectraAcDevice"
    assert m.fans == FANS and m.units == "C"


def test_constant_features_are_found():
    f = synthetic("Electra", registry.models("Electra")[0], features={"light": True})
    m = match(f, CANDIDATES)
    assert m.verdict == "covered" and m.features["light"] is True


def test_fahrenheit_keys_are_recognised():
    m = match(
        synthetic("Electra", registry.models("Electra")[0], keys_in_f=True), CANDIDATES
    )
    assert m.verdict == "covered" and m.units == "F"


def test_random_pulses_are_unknown():
    rng = random.Random(1)
    codes = tuple(
        Code(
            Key("cool", "low", None, float(t)),
            tuple(rng.randrange(300, 3000) for _ in range(60)),
        )
        for t in range(17, 27)
    )
    f = SmartIRFile(
        2,
        "X",
        ("Y",),
        "Broadlink",
        "Base64",
        17,
        26,
        1,
        ("cool",),
        ("low",),
        (),
        codes,
        0,
    )
    assert match(f, CANDIDATES).verdict == "unknown"


def test_the_remote_variant_is_identified():
    brand, model = next(
        (b, m)
        for b, m, k, c, v in brands.MODELS
        if c.__name__ == "Haier176Device" and v == "B"
    )
    m = match(synthetic(brand, model), CANDIDATES)
    assert m.verdict == "covered" and m.candidate == "Haier176Device/B"


def test_one_code_no_mapping_explains_is_near():
    f = synthetic("Electra", registry.models("Electra")[0])
    swapped = dataclasses.replace(f.codes[0], pulses=f.codes[5].pulses)
    f = dataclasses.replace(f, codes=(swapped,) + f.codes[1:])
    m = match(f, CANDIDATES)
    assert m.verdict == "near" and m.unexplained == (f.codes[0].key,)


def test_a_field_pyhvac_never_sets_is_named_as_the_gap():
    def sensor(data):
        data = bytearray(data)
        ELECTRA_AC_LAYOUT.write_raw(data, "sensor_temp", 0x19)
        ELECTRA_AC_LAYOUT.checksum.apply(data)
        return bytes(data)

    f = synthetic("Electra", registry.models("Electra")[0], tamper=sensor)
    m = match(f, CANDIDATES)
    assert m.verdict == "near" and m.candidate == "ElectraAcDevice"
    assert m.gaps == {"sensor_temp": len(f.codes)}
```

- [ ] **Step 2: Run them.** `python -m pytest -q tests/test_smartir_match.py`. Expected: FAIL, `ModuleNotFoundError: No module named 'smartir.match'`.

- [ ] **Step 3: Implement** — `tools/smartir/match.py`:

```python
"""Does a pyhvac device generate a SmartIR file's codes?

For each candidate (a Device class and variant from pyhvac.brands):
1. decode: every code must decode with the candidate's protocol, in full
   or as a prefix cut at a long space (learned codes often repeat);
2. infer: the features held constant over the file and the canonical
   value of each fan and swing label are those whose encoding differs from
   a sample of the codes in the fewest bits (coordinate descent);
   temperature keys are read as °C, or as °F converted to °C;
3. verify (the gate): every usable code is encoded with
   ``device.encode(None, state)`` and must decode to the same frames.

Verdicts: covered (all codes verified), near (decodes and a consistent
mapping, but some codes not reproduced: the layout fields that differ are
counted per code), unknown (no candidate decodes the file).
"""

import collections
import functools
import itertools
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from pyhvac import brands
from pyhvac.fields import Joined, checksum_bits
from pyhvac.ir.codec import DecodeError, decode
from pyhvac.state import HvacState

from .codes import Key

MODE = {
    "heat": "heat",
    "cool": "cool",
    "fan_only": "fan",
    "fan": "fan",
    "dry": "dry",
    "auto": "auto",
    "heat_cool": "auto",
}
CUT_SPACE = 7000  # µs: a learned code may be cut after any space this long
DECODE_SHARE = 0.9  # a candidate must decode this share of the codes
SAMPLE = 24  # codes the mapping is fitted on
PASSES = 2  # coordinate descent rounds


@dataclass
class Candidate:
    name: str  # "Device class/variant"
    device: object
    sequences: Tuple[Tuple[str, ...], ...]


@dataclass
class Match:
    verdict: str  # "covered", "near", "unknown", "unsupported"
    candidate: Optional[str] = None
    units: Optional[str] = None  # "C" or "F" (the file's temperature keys)
    fans: Dict[str, str] = field(default_factory=dict)
    swings: Dict[str, str] = field(default_factory=dict)
    features: Dict[str, object] = field(default_factory=dict)
    decoded: int = 0
    verified: int = 0
    usable: int = 0
    unexplained: Tuple[object, ...] = ()  # the first keys not reproduced
    gaps: Dict[str, int] = field(default_factory=dict)  # field -> codes


def _probe_states(device):
    caps = device.capabilities
    t = caps.temperature.snap((caps.temperature.min + caps.temperature.max) / 2)
    base = HvacState(True, caps.modes[0], t)
    yield base
    yield HvacState(False, caps.modes[0], t)
    for name, choice in caps.features.items():
        on = next((v for v in choice.values if v), None)
        if on is not None:
            yield HvacState(True, caps.modes[0], t, features={name: on})
    if caps.swing_v is not None:
        for v in caps.swing_v.values:
            yield HvacState(True, caps.modes[0], t, swing_v=v)


def candidates():
    """One Candidate per distinct (Device class, variant) in pyhvac.brands."""
    out, seen = [], set()
    for brand, model, kind, cls, variant in brands.MODELS:
        if (cls, variant) in seen:
            continue
        seen.add((cls, variant))
        try:
            device = (
                cls(brand, model, variant=variant) if variant else cls(brand, model)
            )
        except (TypeError, ValueError):
            continue
        if device.PROTOCOL is None:
            continue
        sequences = set()
        for state in _probe_states(device):
            try:
                frames = device.frames(None, device.normalise(state), ())
            except (TypeError, ValueError, KeyError):
                continue
            sequences.add(tuple(f.section for f in frames))
        name = cls.__name__ + (f"/{variant}" if variant else "")
        out.append(Candidate(name, device, tuple(sorted(sequences, key=len))))
    return out


def decode_code(candidate, pulses):
    """The frames a code decodes to (bytes per frame), or None."""
    cuts = [len(pulses)] + [
        i + 1 for i, d in enumerate(pulses) if i % 2 and d >= CUT_SPACE
    ]
    for end in cuts:
        for seq in candidate.sequences:
            try:
                frames = decode(candidate.device.PROTOCOL, pulses[:end], expected=seq)
            except (DecodeError, ValueError):
                continue
            return tuple(f.data for f in frames)
    return None


def _frames(device, state):
    try:
        return tuple(f.data for f in device.frames(None, device.normalise(state), ()))
    except (TypeError, ValueError, KeyError):
        return None


def _celsius(key, units):
    if key.temperature is None:
        return None
    if units == "C":
        return key.temperature
    return round((key.temperature - 32) * 5 / 9, 1)


def _state(device, key, units, fan, swing, features, power=True, mode=None):
    caps = device.capabilities
    mode = mode or MODE.get(key.mode)
    if mode is None:
        return None
    t = _celsius(key, units)
    kw = {"features": dict(features)}
    if fan is not None:
        kw["fan"] = fan
    if swing is not None:
        kw["swing_v"] = swing
    try:
        return HvacState(power, mode, caps.temperature.min if t is None else t, **kw)
    except ValueError:
        return None


BIG = 10**6  # distance between frames of different shapes


def _place(layouts, lengths):
    """[(byte offset in the joined message, Layout)] covering frames of
    ``lengths``: a Joined layout where its frames' total length fits, else a
    per-frame Layout of the frame's length."""
    out, i, offset = [], 0, 0
    while i < len(lengths):
        for entry in layouts:
            if isinstance(entry, Joined):
                size = sum(lengths[i : i + entry.count])
                if size == len(entry.layout.skeleton):
                    out.append((offset, entry.layout))
                    i, offset = i + entry.count, offset + size
                    break
            elif entry is not None and len(entry.skeleton) == lengths[i]:
                out.append((offset, entry))
                i, offset = i + 1, offset + lengths[i]
                break
        else:
            i, offset = i + 1, offset + lengths[i]
    return out


@functools.lru_cache(maxsize=None)
def _owners(device, lengths):
    """Joined-message bit -> field name ("checksum" for checksum bits)."""
    owners = {}
    for offset, layout in _place(getattr(device, "LAYOUTS", ()), lengths):
        base = 8 * offset
        for name, fl in layout.fields.items():
            owners.update({base + b: name for b in fl.bits})
        if layout.checksum is not None:
            owners.update(
                {base + b: "checksum" for b in checksum_bits(layout.checksum)}
            )
    return owners


@functools.lru_cache(maxsize=None)
def _mask(device, lengths):
    """Joined-message mask clearing the checksum bits: a checksum follows
    the other fields, so it is not counted as a difference."""
    mask = bytearray(b"\xff" * sum(lengths))
    for bit, name in _owners(device, lengths).items():
        if name == "checksum":
            mask[bit // 8] &= ~(1 << bit % 8) & 0xFF
    return bytes(mask)


def _distance(device, a, b):
    """Differing non-checksum bits between two frame tuples (BIG if their
    shapes differ)."""
    if (
        a is None
        or b is None
        or len(a) != len(b)
        or any(len(x) != len(y) for x, y in zip(a, b))
    ):
        return BIG
    mask = _mask(device, tuple(len(x) for x in a))
    return sum(
        bin((p ^ q) & m).count("1") for p, q, m in zip(b"".join(a), b"".join(b), mask)
    )


def _sample(on, size=SAMPLE):
    """Up to ``size`` codes spread over the file, every fan and swing label
    included."""
    out, seen = [], set()
    for k, f in on:
        if (k.fan, k.swing) not in seen:
            seen.add((k.fan, k.swing))
            out.append((k, f))
    step = max(1, len(on) // size)
    out += [c for c in on[::step] if c not in out]
    return out[: max(size, len(seen))]


def _fit(device, decoded, units):
    """Mapping (fans, swings, features) closest to the codes: coordinate
    descent on the differing bits over a sample of codes."""
    caps = device.capabilities
    on = [(k, f) for k, f in decoded if k.mode != "off" and MODE.get(k.mode)]
    if not on:
        return None
    sample = _sample(on)
    fans = caps.fan.values if caps.fan else (None,)
    swings = caps.swing_v.values if caps.swing_v else (None,)
    features = {n: c.values[0] for n, c in caps.features.items()}
    fan_map = {k.fan: fans[0] for k, _ in on}
    swing_map = {k.swing: swings[0] for k, _ in on}

    def cost(codes):
        total = 0
        for k, f in codes:
            st = _state(device, k, units, fan_map[k.fan], swing_map[k.swing], features)
            total += BIG if st is None else _distance(device, _frames(device, st), f)
        return total

    def descend(table, name, values, codes):
        scores = {}
        for v in values:
            table[name] = v
            scores[v] = cost(codes)
        table[name] = min(values, key=lambda v: (scores[v], values.index(v)))

    for _ in range(PASSES):
        for label in fan_map:
            descend(fan_map, label, fans, [c for c in sample if c[0].fan == label])
        for label in swing_map:
            descend(
                swing_map, label, swings, [c for c in sample if c[0].swing == label]
            )
        for name, choice in caps.features.items():
            descend(features, name, choice.values, sample)
    return fan_map, swing_map, features


def _gaps(device, frames, expected):
    """Names of the layout fields where ``frames`` differ from ``expected``."""
    if _distance(device, frames, expected) >= BIG:
        return {"frames"}
    owners = _owners(device, tuple(len(x) for x in frames))
    out = set()
    for i, (p, q) in enumerate(zip(b"".join(frames), b"".join(expected))):
        for bit in range(8):
            if (p ^ q) >> bit & 1:
                out.add(owners.get(8 * i + bit, f"byte {i} bit {bit}"))
    if len(out) > 1:
        out.discard("checksum")  # it follows the other fields
    return out


def _off_frames(device, decoded, units, fan_map, swing_map, features, modes):
    """Every frame tuple an "off" code may be: a learned off code carries the
    mode, setpoint and fan last sent, which the file does not record."""
    on_keys = {k for k, _ in decoded if k.mode != "off"}
    temps = {k.temperature for k in on_keys} or {None}
    modes = [MODE[m] for m in modes if m in MODE] or ["cool"]
    fans = set(fan_map.values()) | {None}
    swings = set(swing_map.values()) | {None}
    out = set()
    for mode, t, fan, swing in itertools.product(modes, temps, fans, swings):
        key = Key(mode, None, None, t)
        st = _state(device, key, units, fan, swing, features, False, mode)
        if st is not None:
            out.add(_frames(device, st))
    return out


def _verify(device, decoded, units, fan_map, swing_map, features, smartir_modes):
    """(verified count, unexplained keys, Counter of differing fields)."""
    verified, unexplained, off, gaps = 0, [], None, collections.Counter()
    for key, frames in decoded:
        if key.mode == "off":
            if off is None:
                off = _off_frames(
                    device, decoded, units, fan_map, swing_map, features, smartir_modes
                )
            ok = frames in off
            want = min(off, key=lambda o: _distance(device, frames, o)) if off else None
        else:
            st = _state(
                device,
                key,
                units,
                fan_map.get(key.fan),
                swing_map.get(key.swing),
                features,
            )
            want = None if st is None else _frames(device, st)
            ok = want == frames
        if ok:
            verified += 1
        else:
            unexplained.append(key)
            gaps.update(_gaps(device, frames, want))
    return verified, unexplained, gaps


def _rank(m):
    return (m.verdict != "unknown", m.verified, -sum(m.gaps.values()))


SHAPE_SHARE = 0.5  # a candidate whose frames differ in shape this often is wrong


def match(smartir_file, cands):
    """The best Match of a parsed SmartIRFile against the candidates."""
    if smartir_file.unsupported:
        return Match("unsupported")
    codes = smartir_file.codes
    usable = len(codes)
    if not usable:
        return Match("unknown")
    best = Match("unknown", usable=usable)
    units_order = (
        ("F", "C") if (smartir_file.max_temperature or 0) >= 50 else ("C", "F")
    )
    for cand in cands:
        probe = codes[len(codes) // 2]
        if decode_code(cand, list(probe.pulses)) is None:
            continue
        decoded = [(c.key, decode_code(cand, list(c.pulses))) for c in codes]
        decoded = [(k, f) for k, f in decoded if f is not None]
        if len(decoded) < DECODE_SHARE * usable:
            continue
        for units in units_order:
            fit = _fit(cand.device, decoded, units)
            if fit is None:
                continue
            fan_map, swing_map, features = fit
            verified, unexplained, gaps = _verify(
                cand.device,
                decoded,
                units,
                fan_map,
                swing_map,
                features,
                smartir_file.modes,
            )
            if gaps["frames"] > SHAPE_SHARE * len(decoded):
                continue
            result = Match(
                "covered" if verified == usable else "near",
                cand.name,
                units,
                fan_map,
                swing_map,
                features,
                len(decoded),
                verified,
                usable,
                tuple(unexplained[:10]),
                dict(gaps.most_common()),
            )
            if _rank(result) > _rank(best):
                best = result
            if result.verdict == "covered":
                return best
    return best
```

- [ ] **Step 4: Run them.** `python -m pytest -q tests/test_smartir_match.py`. Expected: PASS (7), in a few seconds (`candidates()` builds 95 candidates once per module).

- [ ] **Step 5: Format and commit.**

```bash
black tools/smartir/match.py tests/test_smartir_match.py
git add tools/smartir/match.py tests/test_smartir_match.py
git commit -m "smartir tool: match files to pyhvac devices, gated by encoding"
```

---

### Task 5: tools/smartir/cluster.py — group the unknown files

**Files:**
- Create: `tools/smartir/cluster.py`
- Test: `tests/test_smartir_cluster.py`

**Interfaces:**
- Consumes:
  - `smartir.codes.SmartIRFile` (Task 3);
  - `portkit.duration_clusters`, `bursts`, `burst_shape` and `draft_protocol` from `tools/portkit.py`.
- Produces:
  - `signature(smartir_file) -> tuple | None`;
  - `cluster(files) -> list[Cluster]`, largest first;
  - `Cluster(signature, files: tuple[int, ...], codes: int, keys: int, timings: dict, draft: str)`.

- [ ] **Step 1: Write the failing tests** — `tests/test_smartir_cluster.py`:

```python
from pyhvac import registry
from pyhvac.state import HvacState
from smartir.cluster import cluster, signature
from smartir.codes import Code, Key, SmartIRFile


def learned(number, brand, temps=range(17, 27)):
    dev = registry.get_device(brand, registry.models(brand)[0])
    codes = tuple(
        Code(
            Key("cool", "auto", None, float(t)),
            dev.encode(None, HvacState(True, "cool", t)).signal.pulses,
        )
        for t in temps
    )
    return SmartIRFile(
        number,
        brand,
        ("X",),
        "Broadlink",
        "Base64",
        17,
        26,
        1,
        ("cool",),
        ("auto",),
        (),
        codes,
        0,
    )


def test_files_of_one_protocol_share_a_cluster():
    a, b, c = (
        learned(1, "Electra"),
        learned(2, "Electra", range(20, 25)),
        learned(3, "Daikin"),
    )
    assert signature(a) == signature(b) != signature(c)
    clusters = cluster([a, b, c])
    assert [cl.files for cl in clusters] == [(1, 2), (3,)]
    assert clusters[0].codes == 15 and clusters[0].keys == 10
    assert "Protocol(" in clusters[0].draft


def test_a_file_without_codes_is_left_out():
    empty = SmartIRFile(4, "X", (), "", "", None, None, None, (), (), (), (), 3)
    assert signature(empty) is None and cluster([empty]) == []
```

- [ ] **Step 2: Run them.** `python -m pytest -q tests/test_smartir_cluster.py`. Expected: FAIL, `ModuleNotFoundError: No module named 'smartir.cluster'`.

- [ ] **Step 3: Implement** — `tools/smartir/cluster.py`:

```python
"""Group the files no pyhvac protocol decodes by timing and frame shape,
so files sharing an unknown protocol become one port task.

A file's signature is the burst shape most of its codes share (header
durations rounded to ROUND µs, bit count per burst); files with the same
signature form a cluster. Per cluster: its files, codes and distinct
state keys, its timing clusters (portkit's role-separated ones) and the
draft Protocol portkit writes for it.
"""

import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "tools"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import portkit  # noqa: E402

ROUND = 200  # µs: header and footer durations are compared at this step


@dataclass
class Cluster:
    signature: Tuple
    files: Tuple[int, ...]
    codes: int
    keys: int
    timings: dict
    draft: str


def _records(smartir_file):
    return [{"pulses": list(c.pulses)} for c in smartir_file.codes]


def signature(smartir_file):
    """(header, bit count, footer) per burst of the file's commonest shape,
    durations rounded to ROUND µs; None for a file without codes."""
    records = _records(smartir_file)
    if not records:
        return None
    clusters = portkit.duration_clusters(records)
    shapes = Counter(
        tuple(portkit.burst_shape(b, clusters) for b in portkit.bursts(r["pulses"]))
        for r in records
    )
    shape = shapes.most_common(1)[0][0]
    return tuple(
        (
            tuple(round(d / ROUND) * ROUND for d in header),
            nbits,
            tuple(round(d / ROUND) * ROUND for d in footer),
        )
        for header, nbits, footer, gap in shape
    )


def cluster(files):
    """Clusters of the given parsed files, largest (most files) first."""
    groups = defaultdict(list)
    for f in files:
        sig = signature(f)
        if sig is not None:
            groups[sig].append(f)
    out = []
    for sig, members in groups.items():
        records = [r for f in members for r in _records(f)]
        timings = portkit.duration_clusters(records)
        shape = Counter(
            tuple(portkit.burst_shape(b, timings) for b in portkit.bursts(r["pulses"]))
            for r in records
        ).most_common(1)[0][0]
        out.append(
            Cluster(
                sig,
                tuple(sorted(f.number for f in members)),
                len(records),
                len({c.key for f in members for c in f.codes}),
                timings,
                portkit.draft_protocol(shape, timings),
            )
        )
    return sorted(out, key=lambda c: (-len(c.files), -c.codes))
```

- [ ] **Step 4: Run them.** `python -m pytest -q tests/test_smartir_cluster.py`. Expected: PASS (2).

- [ ] **Step 5: Format and commit.**

```bash
black tools/smartir/cluster.py tests/test_smartir_cluster.py
git add tools/smartir/cluster.py tests/test_smartir_cluster.py
git commit -m "smartir tool: cluster unknown files by timing and frame shape"
```

---

### Task 6: tools/smartir/fetch.py — upstream archive into a cache

**Files:**
- Create: `tools/smartir/fetch.py`
- Test: `tests/test_smartir_fetch.py`

**Interfaces:**
- Consumes: `pyhvac.protocols.table.fetch` and `cache_dir` (Task 2).
- Produces:
  - `ARCHIVE`;
  - `default_dir() -> Path`;
  - `fetch(dest=None, url=ARCHIVE, get=None) -> Path`;
  - `files(directory) -> list[Path]`, sorted by file number.

- [ ] **Step 1: Write the failing test** — `tests/test_smartir_fetch.py`:

```python
import io
import zipfile

from smartir.fetch import ARCHIVE, fetch, files


def archive():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("SmartIR-master/codes/climate/1000.json", "{}")
        z.writestr("SmartIR-master/codes/climate/20.json", "{}")
        z.writestr("SmartIR-master/codes/climate/sub/9.json", "{}")
        z.writestr("SmartIR-master/codes/fan/1000.json", "{}")
        z.writestr("SmartIR-master/README.md", "")
    return buf.getvalue()


def test_only_climate_files_are_kept(tmp_path):
    asked = []
    dest = fetch(tmp_path, get=lambda url: asked.append(url) or archive())
    assert asked == [ARCHIVE]
    assert [p.name for p in files(dest)] == ["20.json", "1000.json"]
```

- [ ] **Step 2: Run it.** `python -m pytest -q tests/test_smartir_fetch.py`. Expected: FAIL, `ModuleNotFoundError: No module named 'smartir.fetch'`.

- [ ] **Step 3: Implement** — `tools/smartir/fetch.py`:

```python
"""Upstream SmartIR climate code files into a local cache (never committed)."""

import io
import zipfile
from pathlib import Path

from pyhvac.protocols import table

ARCHIVE = "https://codeload.github.com/smartHomeHub/SmartIR/zip/refs/heads/master"
PREFIX = "codes/climate/"


def default_dir():
    return table.cache_dir() / "smartir-upstream" / "climate"


def fetch(dest=None, url=ARCHIVE, get=None):
    """Download upstream master and write its ``codes/climate/<n>.json``
    files to ``dest``; returns the directory. ``get(url) -> bytes`` defaults
    to pyhvac.protocols.table.fetch."""
    dest = Path(dest or default_dir())
    dest.mkdir(parents=True, exist_ok=True)
    archive = zipfile.ZipFile(io.BytesIO((get or table.fetch)(url)))
    for name in archive.namelist():
        _, _, path = name.partition("/")  # drop the "SmartIR-master/" root
        if path.startswith(PREFIX) and path.endswith(".json"):
            leaf = path[len(PREFIX) :]
            if "/" not in leaf:
                (dest / leaf).write_bytes(archive.read(name))
    return dest


def files(directory):
    """The cached files, by file number."""
    found = []
    for p in Path(directory).glob("*.json"):
        if p.stem.isdigit():
            found.append(p)
    return sorted(found, key=lambda p: int(p.stem))
```

- [ ] **Step 4: Run it.** `python -m pytest -q tests/test_smartir_fetch.py`. Expected: PASS (1).

- [ ] **Step 5: Format and commit.**

```bash
black tools/smartir/fetch.py tests/test_smartir_fetch.py
git add tools/smartir/fetch.py tests/test_smartir_fetch.py
git commit -m "smartir tool: fetch upstream climate files into a cache"
```

---

### Task 7: tools/smartir/report.py — verdicts, rows, conflicts

**Files:**
- Create: `tools/smartir/report.py`
- Test: `tests/test_smartir_report.py`

**Interfaces:**
- Consumes:
  - `match.candidates` and `match.match`, with `Match` (Task 4);
  - `cluster.cluster` (Task 5);
  - `fetch.fetch`, `fetch.files` and `fetch.default_dir` (Task 6);
  - `codes.parse` (Task 3);
  - `pyhvac.brands.MODELS`.
- Produces:
  - `Row(brand, model, cls, variant, source, verdict)`;
  - `rows(results) -> (list[Row], list[(Row, reason)])`;
  - `python_rows(rows) -> str`;
  - `markdown(results, clusters, rows, conflicts, unreadable=()) -> str`;
  - `run(paths, jobs) -> (results, unreadable numbers)`;
  - CLI `python tools/smartir/report.py OUT_DIR [--cache DIR] [--no-fetch] [--jobs N]`, which writes `report.md`, `rows.py` and `results.json`.

- [ ] **Step 1: Write the failing tests** — `tests/test_smartir_report.py`:

```python
import dataclasses

from smartir.codes import Code, Key, SmartIRFile
from smartir.match import Match
from smartir.report import Row, markdown, python_rows, rows

CODE = (Code(Key("cool", "low", None, 20.0), (500, 500)),)


def file(number, brand, *models, codes=CODE):
    return SmartIRFile(
        number,
        brand,
        models,
        "Broadlink",
        "Base64",
        16,
        30,
        1,
        ("cool",),
        ("low",),
        (),
        codes,
        0,
    )


def test_covered_files_name_their_candidate_others_are_tables():
    results = [
        (file(1, "Acme", "A-1"), Match("covered", "Haier176Device/B")),
        (file(2, "acme", "B-2"), Match("near", "ElectraAcDevice")),
        (file(3, "Acme", "C-3"), Match("unknown")),
        (file(4, "Acme", "D-4"), Match("unsupported")),
    ]
    new, conflicts = rows(results)
    assert new == [
        Row("Acme", "A-1", "Haier176Device", "B", 1, "covered"),
        Row("Acme", "B-2", "TableDevice", "2", 2, "near"),
        Row("Acme", "C-3", "TableDevice", "3", 3, "unknown"),
    ]
    assert conflicts == []


def test_existing_names_skip_or_conflict():
    results = [
        (file(5, "electra", "AXW12DCS"), Match("covered", "ElectraAcDevice")),
        (file(6, "Electra", "Classic INV 17"), Match("unknown")),
    ]
    new, conflicts = rows(results)
    assert new == []
    assert [(r.source, why) for r, why in conflicts] == [
        (6, "name taken by ElectraAcDevice/None")
    ]


def test_the_brand_keeps_pyhvacs_spelling():
    new, _ = rows([(file(7, "MITSUBISHI HEAVY INDUSTRIES", "X9"), Match("unknown"))])
    assert new[0].brand == "Mitsubishi Heavy Industries"


def test_a_file_without_models_gets_its_number():
    new, _ = rows([(file(8, "Acme"), Match("unknown"))])
    assert new[0].model == "SmartIR 8"


def test_rows_are_python():
    text = python_rows([Row("Acme", "A-1", "TableDevice", "1", 1, "unknown")])
    assert text == "    ('Acme', 'A-1', 'unit', TableDevice, '1'),  # SmartIR 1\n"


def test_markdown_lists_every_file():
    results = [(file(1, "Acme", "A-1"), Match("near", "X", gaps={"fan": 3}))]
    text = markdown(results, [], [], [])
    assert "| 1 | Acme | near | X |" in text and "fan (3)" in text


def test_files_that_are_not_json_are_listed():
    assert "- not JSON: 2680" in markdown([], [], [], [], [2680])


def test_a_file_with_many_unreadable_codes_is_flagged():
    f = dataclasses.replace(file(9, "Acme", "A"), skipped=1)
    assert "| 1 (!) |" in markdown([(f, Match("unknown"))], [], [], [])
```

- [ ] **Step 2: Run them.** `python -m pytest -q tests/test_smartir_report.py`. Expected: FAIL, `ModuleNotFoundError: No module named 'smartir.report'`.

- [ ] **Step 3: Implement** — `tools/smartir/report.py`:

```python
"""Run the SmartIR climate import and write its report.

    python tools/smartir/report.py OUT_DIR [--cache DIR] [--no-fetch] [--jobs N]

Writes OUT_DIR/report.md (verdict per file, gaps, clusters), OUT_DIR/rows.py
(proposed pyhvac/brands.py rows for covered and table files, for review)
and OUT_DIR/results.json. SmartIR files stay in the cache, never in OUT_DIR.
"""

import argparse
import json
import re
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "tools"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from pyhvac import brands  # noqa: E402
from smartir import cluster as clustering  # noqa: E402
from smartir import fetch, match  # noqa: E402
from smartir.codes import parse  # noqa: E402

KIND = "unit"  # SmartIR lists the units a file was learned from
SKIPPED_FLAG = 0.1  # a file with more unreadable codes than this is flagged


@dataclass(frozen=True)
class Row:
    brand: str
    model: str
    cls: str  # Device class name
    variant: Optional[str]
    source: int  # upstream file number
    verdict: str  # the file's verdict: covered, near, unknown


def _key(text):
    return re.sub(r"[^0-9a-z]", "", text.casefold())


def _existing():
    """(brand key, model key) -> (class name, variant); brand key -> name."""
    rows = {(_key(b), _key(m)): (c.__name__, v) for b, m, k, c, v in brands.MODELS}
    names = {_key(b): b for b, *_ in brands.MODELS}
    return rows, names


def rows(results):
    """Proposed rows and conflicts from [(SmartIRFile, Match)]: a covered
    file names its candidate; any other file whose codes can be read is
    served by TableDevice. A name already taken by the same device is
    skipped; taken by another device, it is a conflict."""
    taken, brand_names = _existing()
    out, conflicts = [], []
    for f, m in sorted(results, key=lambda r: r[0].number):
        if m.verdict == "unsupported" or not f.codes:
            continue
        if m.verdict == "covered":
            cls, _, variant = m.candidate.partition("/")
            variant = variant or None
        else:
            cls, variant = "TableDevice", str(f.number)
        brand = brand_names.get(_key(f.manufacturer), f.manufacturer.strip())
        for model in f.models or (f"SmartIR {f.number}",):
            row = Row(brand, model.strip(), cls, variant, f.number, m.verdict)
            k = (_key(brand), _key(row.model))
            if not k[0] or not k[1]:
                conflicts.append((row, "empty name"))
            elif k not in taken:
                taken[k] = (cls, variant)
                brand_names.setdefault(k[0], brand)
                out.append(row)
            elif taken[k] != (cls, variant):
                conflicts.append((row, f"name taken by {taken[k][0]}/{taken[k][1]}"))
    return out, conflicts


def python_rows(new_rows):
    """brands.py MODELS entries for the rows, one per line."""
    lines = []
    for r in new_rows:
        lines.append(
            f"    ({r.brand!r}, {r.model!r}, {KIND!r}, {r.cls}, {r.variant!r}),"
            f"  # SmartIR {r.source}"
        )
    return "\n".join(lines) + "\n"


def markdown(results, clusters, new_rows, conflicts, unreadable=()):
    verdicts = Counter(m.verdict for _, m in results)
    out = ["# SmartIR climate import", ""]
    out += [f"- {v}: {n}" for v, n in sorted(verdicts.items())]
    if unreadable:
        out.append(f"- not JSON: {', '.join(map(str, unreadable))}")
    out += [
        "",
        "## Files",
        "",
        "Skipped: codes that could not be read; flagged (!) when they are "
        f"over {SKIPPED_FLAG:.0%} of the file.",
        "",
        "| file | brand | verdict | candidate | units | verified | skipped | gaps |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for f, m in sorted(results, key=lambda r: r[0].number):
        gaps = ", ".join(f"{k} ({n})" for k, n in m.gaps.items())
        total = len(f.codes) + f.skipped
        flag = " (!)" if total and f.skipped > SKIPPED_FLAG * total else ""
        out.append(
            f"| {f.number} | {f.manufacturer} | {m.verdict} | {m.candidate or ''} "
            f"| {m.units or ''} | {m.verified}/{m.usable} | {f.skipped}{flag} "
            f"| {gaps} |"
        )
    out += ["", "## Clusters of unknown files", ""]
    for c in clusters:
        out += [
            f"### {len(c.files)} files, {c.codes} codes, {c.keys} keys",
            "",
            f"files: {', '.join(map(str, c.files))}",
            "",
            "```",
            c.draft,
            "```",
            "",
        ]
    out += ["## Conflicts", ""]
    out += [
        f"- SmartIR {r.source}: {r.brand} / {r.model}: {why}" for r, why in conflicts
    ]
    out += ["", f"## Rows: {len(new_rows)} proposed (rows.py)", ""]
    return "\n".join(out) + "\n"


_CANDIDATES = None


def _one(path):
    global _CANDIDATES
    if _CANDIDATES is None:
        _CANDIDATES = match.candidates()
    number = int(Path(path).stem)
    try:
        data = json.loads(Path(path).read_text())
    except ValueError:
        return number, None
    f = parse(number, data)
    return f, match.match(f, _CANDIDATES)


def run(paths, jobs=8):
    """([(SmartIRFile, Match)], [numbers of the files that are not JSON])."""
    results, unreadable = [], []
    with ProcessPoolExecutor(jobs) as ex:
        for f, m in ex.map(_one, paths, chunksize=1):
            if m is None:
                unreadable.append(f)
            else:
                results.append((f, m))
    return results, unreadable


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("out", type=Path)
    ap.add_argument("--cache", type=Path, default=None)
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--jobs", type=int, default=8)
    args = ap.parse_args(argv)
    cache = args.cache or fetch.default_dir()
    if not args.no_fetch:
        fetch.fetch(cache)
    results, unreadable = run(fetch.files(cache), args.jobs)
    unknown = [f for f, m in results if m.verdict == "unknown"]
    clusters = clustering.cluster(unknown)
    new_rows, conflicts = rows(results)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "report.md").write_text(
        markdown(results, clusters, new_rows, conflicts)
    )
    (args.out / "rows.py").write_text(python_rows(new_rows))
    (args.out / "results.json").write_text(
        json.dumps({f.number: asdict(m) for f, m in results}, indent=1, default=str)
    )
    print(Counter(m.verdict for _, m in results))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run them.** `python -m pytest -q tests/test_smartir_report.py`. Expected: PASS (8).

- [ ] **Step 5: Format and commit.**

```bash
black tools/smartir/report.py tests/test_smartir_report.py
git add tools/smartir/report.py tests/test_smartir_report.py
git commit -m "smartir tool: report verdicts, proposed rows and conflicts"
```

---

### Task 8: Run the importer; commit the report and the rows

**Files:**
- Create: `docs/smartir/report.md` (generated)
- Modify: `pyhvac/brands.py` (TableDevice import; rows appended at the end of `MODELS`)
- Test: `tests/test_brands.py` (one new test)

**Interfaces:**
- Consumes: the CLI (Task 7) and `TableDevice` (Task 2).
- Produces: `brands.MODELS` rows `(brand, model, "unit", Class, variant)`; a TableDevice row's variant is the upstream file number as a string.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_brands.py`:

```python
def test_table_rows_name_a_smartir_file_and_do_not_fetch(monkeypatch):
    from pyhvac.protocols import table
    from pyhvac.protocols.table import TableDevice

    monkeypatch.setattr(table, "fetch", None)  # construction must not fetch
    rows = [r for r in brands.MODELS if r[3] is TableDevice]
    assert rows
    for brand, model, kind, cls, variant in rows:
        assert kind == "unit" and variant.isdigit()
        assert registry.get_device(brand, model).variant == variant
```

- [ ] **Step 2: Run it.** `python -m pytest -q tests/test_brands.py -k table_rows`. Expected: FAIL on `assert rows`.

- [ ] **Step 3: Run the importer.** It needs the network and takes ~5 min with 8 jobs.

```bash
python tools/smartir/report.py /tmp/smartir-out --jobs 8
cp /tmp/smartir-out/report.md docs/smartir/report.md
```

  Expected output: a Counter close to `{'near': 196, 'unknown': 143, 'unsupported': 13, 'covered': 4}`; drift from upstream changes is fine. Record the actual counts in the ledger. `results.json` and `rows.py` are not committed: they are regenerable.

- [ ] **Step 4: Add the rows to `pyhvac/brands.py`.**
  - Add `from .protocols.table import TableDevice` among the imports, alphabetically: after `.protocols.sharp`/`.protocols.samsung`, before `.protocols.technibel`.
  - Insert the comment line `# SmartIR climate files (tools/smartir; docs/smartir/report.md)` before the closing `)` of `MODELS`, followed by the contents of `/tmp/smartir-out/rows.py`.
  - Run `black pyhvac/brands.py`.
  - The covered rows name protocol classes that `brands.py` already imports. If `rows.py` names one that is not imported, add its import.

- [ ] **Step 5: Run the whole suite.** `python -m pytest -q`. Expected: all pass, about 23100 passed and 64 skipped. In particular, `test_names_do_not_collide_after_normalising` and `test_direct_construction_never_picks_a_wrong_variant` must pass: TableDevice raises `ValueError` without `variant=`.

- [ ] **Step 6: Check one table device end to end** (network). Expected: a base64 Broadlink packet.

```bash
PYHVAC_CACHE=/tmp/pyhvac-cache python -m pyhvac Toyotomi "AKIRA GAN/GAG-A128 VL" --mode cool --temperature 22 --fan 1
```

- [ ] **Step 7: Commit.**

```bash
git add pyhvac/brands.py tests/test_brands.py docs/smartir/report.md
git commit -m "brands: SmartIR climate files as rows (covered: protocol devices; others: TableDevice)"
```

- [ ] **Step 8: Hand the report to the author.** In the final message, list:
  - the verdict counts;
  - the near files grouped by candidate and top gap fields (these become the gap-fix plans);
  - the largest unknown clusters (port candidates);
  - the conflicts from `docs/smartir/report.md`.

---

## After this plan (separate plans, after the author reviews the report)

- **Gap fixes** for the near groups, for example Electra light_toggle, Coolix fan/temp, Panasonic model bytes, Kelon power_toggle, Midea fahrenheit/temperature, and the per-protocol `units` option. After each fix, re-run Task 8's importer; files that become covered swap their TableDevice row for the protocol row.
- **Ports** from the largest unknown clusters (portkit pipeline, captures as the only evidence).
