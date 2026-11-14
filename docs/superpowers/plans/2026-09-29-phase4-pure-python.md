# Phase 4: pure-Python pyhvac 0.2.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship pyhvac 0.2.0 as a pure-Python package: every model served by a `Device`, capabilities giving full control, the brand/model table split from protocol code, no C extension and no old plugin API.

**Architecture:** Verified changes produced while planning (native ports, capability changes) are applied as patches from `docs/superpowers/plans/2026-09-29-phase4/patches/`. The C evidence is then frozen into fixtures through `tests/c_oracle.py`. Plugin modules become `pyhvac/protocols/` with a script that strips the old API; `pyhvac/brands.py` is generated from the name table; `pyhvac/registry.py` reads it. Finally the C build, old API and C-only tests are deleted, and packaging, CI, CLI and docs are rewritten.

**Tech Stack:** Python ≥ 3.9 (verified in Task 8), setuptools, pytest, black; the scratch C environment (pyhvac 0.1.7's `_irhvac.so` + `irhvac.py`) for Tasks 1–3 only.

**Spec:** `docs/superpowers/specs/2026-09-29-phase4-pure-python-design.md`

**Artifacts (committed with this plan):** `docs/superpowers/plans/2026-09-29-phase4/`
- `patches/*.diff`: the verified native ports and capability changes (`diff -ruN` format, apply with `patch -p1`).
- `tables/*.md`: per patch, the capability table old -> new with sources; `tables/names.md`: the old -> new brand/model table.
- `rows.json`: the name table with each row's Device class and variant (416 rows once `sharp:generic` is dropped).
- `tools/strip_legacy.py`, `tools/gen_brands.py`, `tools/c_oracle.py`, `tools/registry.py`: verified scripts and modules used by Tasks 3 and 5.

## Global Constraints

- Branch `phase4` (forked from `ports`); never push, merge or release without the author's explicit go.
- Brand and model names follow `tables/names.md`; old 0.1.x strings resolve only for the 0.1.x pure-Python devices (`brands.ALIASES`).
- Capabilities: what the protocol documents and the port encodes; no-op controls removed, their layout fields and tables kept.
- Frames for every oracle, golden and frozen state must stay as tested; only the declared deviations differ from the recorded C output.
- Excluded from capabilities: timers, clock, sensor temperature, Fahrenheit.
- Run `black` on every modified Python file.
- End state: zero `importorskip("pyhvac.irhvac")`, no `pyhvac/plugins/`, no `pyhvac/legacy.py`, no `irhvac`, no SWIG build; `py3-none-any` wheel.
- Test commands: pure `python -m pytest -q tests`; C (Tasks 1–3): `$S/both_any.sh <repo> <tag>` where `S=/tmp/claude-1000/-home-fw-development-AutoBuddy-pyhvac/e24a44b3-0698-43b6-890a-47d4ddf34b70/scratchpad` (builds a scratch copy with the C extension; logs `$S/pure-<tag>.log`, `$S/c-<tag>.log`). If the scratch C environment is gone, rebuild it: `python -m venv $S/oracle-venv && $S/oracle-venv/bin/pip install pyhvac==0.1.7`.

## Decisions for the author (defaults applied unless changed before execution)

| # | Question | Default (what the plan does) | Alternative |
|---|---|---|---|
| D1 | `sharp:generic` never produced a correct command (broken base of JTech). | Drop the row (`gen_brands.py` drops it). | Map it to `JTechDevice`. |
| D2 | Native capabilities: the Daikin port offers what the shared legacy code encodes (heat/auto on Smash 2; fan, swing, powerful on generic); the LG/Panasonic ports offer only each legacy class's table. | As delivered. | Narrow Daikin to its class tables, or widen LG/Panasonic to their shared code. |
| D3 | GOODWEATHER swing "1"/"2" now send Slow/Fast but keep the labels "auto low"/"auto high". | As delivered. | Relabel "slow"/"fast" (needs an oracle adapter in its test). |
| D4 | LG native: `auto_bias` feature name; economy with levels off/80/60/40; diagnostic as an action. | As delivered. | Rename/reshape. |
| D5 | Hitachi296 setpoint up to 31 °C (header max; no capture above 25). Haier160 new swing "Highest" numbered "2" after "Top". | As delivered. | Keep 25; swap order. |
| D6 | Sharp A903 offers both "auto" and "fan" (same code 0b00); Sharp Coanda swing and Fujitsu OutsideQuiet not offered. | As delivered. | Remove A903 "auto"; add the others. |
| D7 | Mitsubishi 112/136 keep "quiet" (it forces FanMin). | Keep. | Remove for consistency. |
| D8 | Names: generic rows become "`<PROTOCOL>` [`<enumerator>`] protocol" (enumerators spelled as IRremoteESP8266 writes them, e.g. "kVoltasUnknown"); 3 kinds inferred "remote"; "Smash II". | As in `tables/names.md`. | Edit `rows.json` before Task 5. |
| D9 | Hitachi344's documented swing_v state bit stays unsent (C never sent it). | Leave. | Send it (declares a deviation). |
| D10 | Argo WREM3 fan: canonical numbers shift (old "1" is now "2"; labels keep their codes). | As delivered. | — |

Deferred (documented features needing new frame logic, listed in the tables): Sharp econo/light toggles, Coolix sleep word, Fujitsu swing short codes and 10 °C heat, Midea 8 °C heat, Toshiba swing step, Transcold swing_h word, Hitachi264/424 swing buttons, Haier button field, Samsung sleep/Breeze, Kelvinator sleep, Mirage recycle, Daikin312 swing_h positions, Daikin Breeze/Circulate, Daikin128 ceiling light, Panasonic native toggles changed while off.

## Review Focus

1. A model string with different case, spaces or punctuation ("mitsubishi_heavy_industries", "RAS-22NK" vs "ras 22nk") must resolve to the same device; two different models must never collide after normalisation (Task 5 test).
2. An old 0.1.x string for a C-backed model (e.g. `("lg", "6711A20083V  remote")`) must raise `KeyError`, not silently resolve; aliases only for the 0.1.x pure-Python devices (Task 5 test).
3. `get_device(brand)` with no model: returns the device when the brand has one model, otherwise `KeyError` listing the models (Task 5 test).
4. Deleting `pyhvac/plugins/` must not leave an import of it anywhere in `pyhvac/`, `tests/` or `tools/`, including in docstrings' code examples executed by nothing (Task 6 gate: `grep -rn "plugins\|legacy\|irhvac" pyhvac tests tools` has no code hits).
5. A frozen C fixture key that a test never recorded must fail loudly, not pass (Task 3 test).

---

### Task 1: Native ports

**Files:**
- Modify: `pyhvac/plugins/daikin.py`, `pyhvac/plugins/lg.py`, `pyhvac/plugins/panasonic.py`, `tests/test_registry.py`
- Create: `tests/test_daikin_native_device.py`, `tests/test_lg_native_device.py`, `tests/test_panasonic_native_device.py`

**Interfaces:**
- Produces: `DaikinNativeDevice(brand, model)` in `daikin.py`; `LgNativeDevice(brand, model, variant=None)` (variants "generic", "inverter v", "dual inverter") in `lg.py`; `PanasonicNativeDevice(brand, model, variant=None)` (variants "generic", "4 way cassette") in `panasonic.py`; each registered in its module's `DEVICES`.

- [ ] **Step 1: Apply the verified patches**

```bash
A=docs/superpowers/plans/2026-09-29-phase4
patch -p1 --no-backup-if-mismatch < $A/patches/native_daikin_sharp.diff
patch -p1 --no-backup-if-mismatch < $A/patches/native_lg_panasonic.diff
```
Expected: every hunk applies (no "FAILED", no `.rej` files).

- [ ] **Step 2: Run the new tests and the suite**

Run: `python -m pytest -q tests/test_daikin_native_device.py tests/test_lg_native_device.py tests/test_panasonic_native_device.py`
Expected: pass; skips only the declared golden records (1 Daikin, 8 LG DualInverter hswing).
Run: `$S/both_any.sh . t1`
Expected: 0 failed in both runs.

- [ ] **Step 3: Commit**

```bash
git add pyhvac tests
git commit -m "Native ports: DaikinNativeDevice, LgNativeDevice, PanasonicNativeDevice on the golden fixtures"
```

### Task 2: Capabilities: full control

**Files:** the six patches touch `pyhvac/plugins/*.py` and `tests/test_*_device.py` (listed in each patch).

**Interfaces:**
- Consumes: Task 1's modules (daikin.py, lg.py, panasonic.py).
- Produces: capabilities per `tables/cap_*.md`; per-device capability tests replacing every C-only capability-equality test in the patched files.

- [ ] **Step 1: Apply the patches in this order**

```bash
A=docs/superpowers/plans/2026-09-29-phase4
for p in cap_daikin cap_hitachi_haier cap_pairs cap_single_a cap_single_b1 cap_single_b2; do
  patch -p1 --no-backup-if-mismatch < $A/patches/$p.diff
done
```
Expected: two rejects only, both hunk #1 (import lines): `pyhvac/plugins/daikin.py.rej` and `pyhvac/plugins/lg.py.rej`.

- [ ] **Step 2: Resolve the two import rejects**

In `pyhvac/plugins/daikin.py`, the import block becomes:
```python
import struct
from dataclasses import replace

from .hvaclib import HVAC, PulseBased, GenPluginObject, bit_reverse
from ..device import Device
from ..fields import Checksum, Field, HighNibbleSum, Layout, NibbleSum, Sum8
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_5, ON_OFF, SWING, SWING_V_AUTO_ANGLES
from ..state import Capabilities, Choice, TemperatureRange
```
In `pyhvac/plugins/lg.py`, the choices import becomes `from ..choices import FAN_4, FAN_5, ON_OFF, SWING` (keep `from ..state import Capabilities, Choice, TemperatureRange`). Then:
```bash
rm pyhvac/plugins/daikin.py.rej pyhvac/plugins/lg.py.rej
black -q pyhvac tests
python -c "import pyhvac.plugins.daikin, pyhvac.plugins.lg"
```
Expected: no output (imports succeed).

- [ ] **Step 3: Check for unused imports in the plugin modules**

```bash
python - <<'EOF'
import ast, glob
for p in sorted(glob.glob("pyhvac/plugins/*.py")):
    t = ast.parse(open(p).read()); names = []
    for n in t.body:
        if isinstance(n, ast.ImportFrom) and n.module in ("state", "choices", "fields", "dataclasses", "device"):
            names += [a.asname or a.name for a in n.names]
    used = {n.id for n in ast.walk(t) if isinstance(n, ast.Name)}
    used |= {n.value.id for n in ast.walk(t) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)}
    print(p, [n for n in names if n not in used]) if [n for n in names if n not in used] else None
EOF
```
Expected: no output.

- [ ] **Step 4: Run both environments**

Run: `$S/both_any.sh . t2`
Expected: pure ≈ 26062 passed / 461 skipped; C ≈ 37948 passed / 2499 skipped / 90 xfailed-or-xpassed (HITACHI_AC296's known flakiness); 0 failed.

- [ ] **Step 5: Commit, one commit per group**

```bash
git add -A pyhvac tests
git commit -m "Capabilities: full control (Daikin, Hitachi/Haier, paired protocols, singletons)

Per docs/superpowers/plans/2026-09-29-phase4/tables/cap_*.md; the C-only
capability-equality tests are replaced by tests pinning the documented values."
```

### Task 3: Freeze the C evidence

**Files:**
- Create: `tests/c_oracle.py` (copy of `tools/c_oracle.py` from the artifacts), `tests/fixtures/oracle_extra/*.json.gz`, `tests/fixtures/README.md`
- Modify: `tests/conftest.py`, `tests/port_oracle.py`, every test file that still calls `pytest.importorskip("pyhvac.irhvac")`, `LegacyDevice(`, `c_sequence(` with a monkeypatched glue, or `c_raws(`
- Delete tests: every remaining capability-equality test (`*capabilities_match_the_legacy*`)

**Interfaces:**
- Produces: `c_oracle.c_encode(plugin, model, legacy_class_name, state, glue=None) -> list[int]`; `c_oracle.c_sequence(record, states, glue=None) -> list[dict]` (records with `pulses`); `port_oracle.c_sequence` re-exported from `c_oracle`; record mode with `PYHVAC_FREEZE=1`.

- [ ] **Step 1: Write the failing test for replay**

`tests/test_c_oracle.py`:
```python
import pytest

import c_oracle
from oracle import load_oracle


def test_an_unrecorded_call_fails_loudly(monkeypatch, tmp_path):
    monkeypatch.setattr(c_oracle, "FIXTURES", tmp_path)
    monkeypatch.setattr(c_oracle, "RECORDING", False)
    monkeypatch.setattr(c_oracle, "_store", {})
    record = load_oracle("DAIKIN64")[0]
    with pytest.raises(AssertionError, match="not frozen"):
        c_oracle.c_sequence(record, [record["state"]])


def test_a_recorded_call_replays(monkeypatch, tmp_path):
    monkeypatch.setattr(c_oracle, "FIXTURES", tmp_path)
    monkeypatch.setattr(c_oracle, "RECORDING", False)
    monkeypatch.setattr(c_oracle, "_store", {})
    record = load_oracle("DAIKIN64")[0]
    key = c_oracle._key("sequence", record["plugin"], record["class"], None, [record["state"]])
    c_oracle._store["test_c_oracle"] = {key: [record["pulses"]]}
    (rec,) = c_oracle.c_sequence(record, [record["state"]])
    assert rec["pulses"] == record["pulses"]
```
Run: `python -m pytest -q tests/test_c_oracle.py`
Expected: FAIL (`ModuleNotFoundError: No module named 'c_oracle'`).

- [ ] **Step 2: Add the module, the session hook and the port_oracle delegation**

```bash
cp docs/superpowers/plans/2026-09-29-phase4/tools/c_oracle.py tests/c_oracle.py
```
Append to `tests/conftest.py`:
```python


def pytest_sessionfinish(session, exitstatus):
    # c_oracle record mode (PYHVAC_FREEZE=1): write what the C path sent.
    import c_oracle

    if c_oracle.RECORDING:
        c_oracle.write_fixtures()
```
In `tests/port_oracle.py`: delete the `def c_sequence(record, states):` function (the whole body up to `def assert_sequence_matches_c(`) and add `from c_oracle import c_sequence` beside `from oracle import check_against_oracle, load_oracle`.
Run: `python -m pytest -q tests/test_c_oracle.py`
Expected: PASS (2 tests).

- [ ] **Step 3: Convert the C-gated tests**

Find them: `grep -rln 'importorskip("pyhvac.irhvac")\|LegacyDevice(\|trans_swing\|trans_hswing\|c_raws(' tests`.
Apply these rules, file by file:
1. Capability-equality tests (compare a port's capabilities with `LegacyDevice(...).capabilities`): delete them.
2. `LegacyDevice(plugin, model, Cls).encode(None, state).signal.pulses` → `c_encode(plugin, model, "Cls", state)` (a list of ints), import `from c_oracle import c_encode`; remove the `pytest.importorskip("pyhvac.irhvac")` line and the legacy-class imports.
3. Tests that monkeypatch `trans_swing` / `trans_hswing` and then call `c_sequence` / `LegacyDevice`: drop the monkeypatch and pass `glue="fixed"` (`c_sequence(record, states, glue="fixed")`, `c_encode(..., glue="fixed")`).
4. `tests/test_airwell_device.py`: delete `c_raws` and the C-only tests that call it (`tests/fixtures/airwell_c_raw.json` is the record); keep every test that reads the JSON.
5. Tests that read a legacy class's attributes for data (e.g. `JTech().status` in `tests/test_jtech_device.py`): replace the call with the literal dict it returns (print it once in the C env).
6. `tests/test_legacy.py`, `tests/test_legacy_oracle.py`, `tests/test_legacy_encode_all.py`, `tests/test_irghvac.py`, `tests/test_hvac_protocol.py`, `tests/test_golden_native.py`: leave them for now (Task 6 deletes them).
Run black on every edited file.

- [ ] **Step 4: Record in the C environment**

```bash
rm -rf $S/cwork-freeze && mkdir -p $S/cwork-freeze && cp -r pyhvac tests tools $S/cwork-freeze/
cp $S/oracle-venv/lib/python3.14/site-packages/pyhvac/{_irhvac.so,irhvac.py} $S/cwork-freeze/pyhvac/
(cd $S/cwork-freeze && PYHVAC_FREEZE=1 PYTHONPATH=. python -m pytest -q -p no:cacheprovider tests | tail -3)
rm -rf tests/fixtures/oracle_extra && cp -r $S/cwork-freeze/tests/fixtures/oracle_extra tests/fixtures/
```
Expected: 0 failed; `tests/fixtures/oracle_extra/` holds one `.json.gz` per test module that calls C.

- [ ] **Step 5: Replay without C**

Run: `python -m pytest -q tests`
Expected: 0 failed; the only remaining skips are in the six files of rule 6.
Run: `grep -rln 'importorskip("pyhvac.irhvac")' tests`
Expected: only the six files of rule 6.

- [ ] **Step 6: Write the fixtures README**

`tests/fixtures/README.md`:
```markdown
# Test fixtures

- `oracle/<PROTOCOL>.json.gz`: what pyhvac 0.1.7's IRremoteESP8266 C path sent
  for a grid of old-vocabulary states (one record per state: plugin, model,
  class, variant, state, pulses). Generated with pyhvac 0.1.7's
  `tools/oracle_generate.py`; CARRIER_AC64, TROTEC, TROTEC_3550 and
  WHIRLPOOL_AC were regenerated from the fixed C path (protocol names and
  the missing-comma bug fixed) before the C extension was removed.
- `oracle_extra/<test module>.json.gz`: the C output the tests compared with
  beyond the grid (persistent-object sequences, extra states, the
  fixed-glue cases), recorded once by `tests/c_oracle.py` (PYHVAC_FREEZE=1)
  while the C extension still existed; replayed ever since.
- `golden/<module>.json.gz`: what the 0.1.x pure-Python classes sent.
- `airwell_c_raw.json`: the AIRWELL state words the C library built (its
  SWIG timing recorder mis-recorded Manchester pulses).
```

- [ ] **Step 7: Run both environments and commit**

Run: `$S/both_any.sh . t3`
Expected: 0 failed in both.
```bash
git add -A tests
git commit -m "tests: freeze the C evidence into oracle_extra fixtures; replay through c_oracle"
```

### Task 4: Detach the native ports from the legacy classes

**Files:** Modify `pyhvac/plugins/airspool.py`, `pyhvac/plugins/daikin.py`, `pyhvac/plugins/panasonic.py`.

**Interfaces:**
- Consumes: the legacy class attributes the ports read: `Airspool.FBODY`, `Airspool.MODE_NIBBLE`, `Airspool.SLEEP_ENUM`, `Airspool.c_to_f`; `Daikinth.FBODY`; `Panasonic.FHEADER`, `Panasonic.FILLER`, `Panasonic.F2COMMON1`, `Panasonic.F2COMMON2`, `Panasonic.FECON`, `Panasonic.FODOUR`.
- Produces: module-level constants/functions with the same values (e.g. `AIRSPOOL_BODY`, `AIRSPOOL_MODE_NIBBLE`, `AIRSPOOL_SLEEP_ENUM`, `airspool_c_to_f`, `DAIKIN_NATIVE_BODY`, `PANASONIC_NATIVE_HEADER`, ...), used by the Devices.

- [ ] **Step 1: Write the failing gate**

`tests/test_protocols_are_self_contained.py`:
```python
import ast
from pathlib import Path

LEGACY = {"Airspool", "Daikinth", "Smash2", "Panasonic", "PanaCassette"}
DEVICES = {
    "airspool.py": "AirspoolDevice",
    "daikin.py": "DaikinNativeDevice",
    "panasonic.py": "PanasonicNativeDevice",
}


def test_native_devices_do_not_read_legacy_classes():
    root = Path(__file__).resolve().parents[1] / "pyhvac" / "plugins"
    for name, device in DEVICES.items():
        tree = ast.parse((root / name).read_text())
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == device)
        module_level = [n for n in tree.body if not isinstance(n, (ast.ClassDef, ast.FunctionDef))]
        used = {
            n.id
            for part in [cls, *module_level]
            for n in ast.walk(part)
            if isinstance(n, ast.Name)
        }
        assert not used & LEGACY, (name, sorted(used & LEGACY))
```
Run: `python -m pytest -q tests/test_protocols_are_self_contained.py`
Expected: FAIL naming `Airspool`, `Daikinth` and `Panasonic`.

- [ ] **Step 2: Move the constants**

For each attribute listed under Consumes: add a module-level constant (or function) with the same value right after the module's Protocol definition, citing the legacy class it came from in a comment, and replace every read of `<LegacyClass>.<attr>` in the Device class and in module-level code with it. Leave the legacy classes as they are (Task 6 deletes them).
Run: `python -m pytest -q tests/test_protocols_are_self_contained.py tests/test_airspool_device.py tests/test_daikin_native_device.py tests/test_panasonic_native_device.py`
Expected: PASS (golden acceptance unchanged).

- [ ] **Step 3: Confirm the strip script finds nothing dangling**

```bash
rm -rf $S/strip-check && cp -r . $S/strip-check && python docs/superpowers/plans/2026-09-29-phase4/tools/strip_legacy.py $S/strip-check | tail -3
```
Expected: no "PROBLEMS" section.

- [ ] **Step 4: Commit**

```bash
black -q pyhvac tests
git add -A pyhvac tests
git commit -m "Native ports: module-level constants instead of the legacy classes' attributes"
```

### Task 5: `protocols/`, `brands.py` and the registry

**Files:**
- Create: `pyhvac/protocols/` (by `strip_legacy.py`), `pyhvac/brands.py` (by `gen_brands.py`), `tests/test_brands.py`, `tests/fixtures/names_0_1.json` (copy of the artifacts' `rows.json`: the 0.1.x -> 0.2.0 name table the tests check)
- Replace: `pyhvac/registry.py` (from `tools/registry.py`), `tests/test_registry.py`
- Modify: every test importing `pyhvac.plugins.<m>` → `pyhvac.protocols.<new m>`; delete every per-device `test_registry_serves_the_port` and other tests calling `registry.get_device` with 0.1.x names.

**Interfaces:**
- Consumes: `rows.json` (fields `old_brand`, `old_model`, `brand`, `model`, `kind`, `alias`, `cls` = "oldmodule.Class", `var`).
- Produces: `pyhvac.brands.MODELS: tuple[(brand, model, kind, DeviceClass, variant)]`, `pyhvac.brands.ALIASES: dict[(old_brand, old_model), (brand, model)]`; `pyhvac.registry.brands() -> list[str]`, `models(brand) -> list[str]`, `get_device(brand, model=None) -> Device` (name matching: `re.sub(r"[^0-9a-z]", "", s.casefold())`).

- [ ] **Step 1: Write the failing tests**

`tests/test_brands.py`:
```python
import json
import re
from collections import Counter
from pathlib import Path

import pytest

from pyhvac import brands, registry
from pyhvac.state import HvacState

ROWS = json.loads(
    (Path(__file__).parent / "fixtures" / "names_0_1.json").read_text()
)
DROPPED = {("sharp", "generic")}


def key(text):
    return re.sub(r"[^0-9a-z]", "", text.casefold())


@pytest.mark.parametrize(
    "row",
    [r for r in ROWS if (r["old_brand"], r["old_model"]) not in DROPPED],
    ids=lambda r: f"{r['old_brand']}/{r['old_model']}",
)
def test_every_old_model_has_its_new_row(row):
    dev = registry.get_device(row["brand"], row["model"])
    assert type(dev).__name__ == row["cls"].split(".")[1]
    assert getattr(dev, "variant", None) == row["var"]
    caps = dev.capabilities
    dev.encode(None, HvacState(True, caps.modes[0], caps.temperature.min))


def test_names_do_not_collide_after_normalising():
    assert len({key(b) for b, *_ in brands.MODELS}) == len({b for b, *_ in brands.MODELS})
    counts = Counter((key(b), key(m)) for b, m, *_ in brands.MODELS)
    assert [k for k, n in counts.items() if n > 1] == []


def test_aliases_are_the_pure_python_devices_only():
    expected = {(r["old_brand"], r["old_model"]) for r in ROWS if r["alias"]} - DROPPED
    assert set(brands.ALIASES) == expected
    for old in brands.ALIASES:
        registry.get_device(*old)


def test_old_names_of_c_backed_models_do_not_resolve():
    with pytest.raises(KeyError):
        registry.get_device("lg", "6711A20083V  remote")


def test_hitachi_ac3_and_sharp_generic_are_gone():
    for brand, model in (("hitachi", "PC-LH3B"), ("hitachi", "generic 3")):
        with pytest.raises(KeyError):
            registry.get_device(brand, model)
    assert ("sharp", "generic") not in brands.ALIASES
```
`tests/test_registry.py` (replaces the old file):
```python
import pytest

from pyhvac import registry


def test_brands_are_listed_as_manufacturers_write_them():
    names = registry.brands()
    assert "Mitsubishi Heavy Industries" in names and names == sorted(names, key=str.casefold)


def test_lookup_ignores_case_spaces_and_punctuation():
    a = registry.get_device("mitsubishi_heavy_industries", registry.models("Mitsubishi Heavy Industries")[0])
    assert a.brand == "Mitsubishi Heavy Industries"


def test_unknown_brand_or_model():
    with pytest.raises(KeyError, match="unknown brand"):
        registry.get_device("nope", "x")
    with pytest.raises(KeyError, match="unknown model"):
        registry.get_device("Daikin", "nope")


def test_model_may_be_left_out_only_for_single_model_brands():
    single = next(b for b in registry.brands() if len(registry.models(b)) == 1)
    assert registry.get_device(single).brand == single
    several = next(b for b in registry.brands() if len(registry.models(b)) > 1)
    with pytest.raises(KeyError, match="several models"):
        registry.get_device(several)
```
```bash
cp docs/superpowers/plans/2026-09-29-phase4/rows.json tests/fixtures/names_0_1.json
```
Run: `python -m pytest -q tests/test_brands.py tests/test_registry.py`
Expected: FAIL (`ImportError: cannot import name 'brands'`).

- [ ] **Step 2: Build `protocols/`**

```bash
A=docs/superpowers/plans/2026-09-29-phase4
python $A/tools/strip_legacy.py .
```
Expected: one line per module, 34 "registration-only, dropped", no "PROBLEMS". Then fix cross-module imports inside `pyhvac/protocols/` (e.g. `from .kelvinator import KelvinatorBlockSum` in gree.py stays valid; imports of registration modules or of `trotech`/`mitsubishi_heavy_industries` must use the new names):
```bash
grep -rn "from \.\(trotech\|mitsubishi_heavy_industries\|hvaclib\)" pyhvac/protocols
```
Expected: no output after editing.
Remove the per-module model->variant tables' use in `__init__` only where a Device requires them (the registry now always passes `variant`): keep the tables and the `variant or <table>.get(model, <default>)` fallback, so direct construction keeps working.

- [ ] **Step 3: Generate `brands.py` and install the registry**

```bash
python $A/tools/gen_brands.py $A/rows.json pyhvac/brands.py protocols
cp $A/tools/registry.py pyhvac/registry.py
black -q pyhvac
python -c "from pyhvac import registry; print(len(registry.brands()))"
```
Expected: `416 rows, 11 aliases, 77 brands` and `77`.

- [ ] **Step 4: Repoint the tests**

```bash
grep -rl "pyhvac\.plugins\." tests | xargs sed -i -e 's/pyhvac\.plugins\.trotech/pyhvac.protocols.trotec/g' -e 's/pyhvac\.plugins\.mitsubishi_heavy_industries/pyhvac.protocols.mitsubishi_heavy/g' -e 's/pyhvac\.plugins\./pyhvac.protocols./g'
```
Delete from every `tests/test_*_device.py` the tests that call `registry.get_device` / `registry.models` with 0.1.x names (typically `test_registry_serves_the_port`, `test_mabe_models_are_served_by_the_port`, `test_oracle_covers_the_legacy_class` when it reads `PluginObject`); `tests/test_brands.py` covers them all. Tests that still import legacy classes from `pyhvac.protocols` fail here: they belong to rule 6 of Task 3 and are deleted in Task 6 — mark those six files with `pytest.skip("deleted in Task 6", allow_module_level=True)` at the top for now.
Run: `python -m pytest -q tests`
Expected: 0 failed.

- [ ] **Step 5: Commit**

```bash
black -q pyhvac tests
git add -A pyhvac tests
git commit -m "protocols/ and brands.py: protocol code split from the brand/model table; registry on brands"
```

### Task 6: Delete the old API and the C build

**Files:**
- Delete: `pyhvac/plugins/` (Task 5 already copied its protocol code to `pyhvac/protocols/`), `pyhvac/legacy.py`, `pyhvac/irhvac.py` and `pyhvac/_irhvac*.so` if present, `tests/test_legacy.py`, `tests/test_legacy_oracle.py`, `tests/test_legacy_encode_all.py`, `tests/test_irghvac.py`, `tests/test_hvac_protocol.py`, `tests/test_golden_native.py`, `tests/test_pairs_family.py` and the `*_family.py` tests that check legacy registrations, `tools/oracle_generate.py`, `tools/golden_generate.py`, `tools/state_grid.py` (after moving anything the remaining tests import), `setup.py`, the `IRremoteESP8266` submodule (`git rm IRremoteESP8266`, `.gitmodules` entry), `MANIFEST.in`.
- Modify: `tests/conftest.py` (drop the tools/ path if nothing uses it), `tests/c_oracle.py` (drop record mode: remove `RECORDING`, `write_fixtures`, `_legacy_class`, `_fix_glue`, the `compute` bodies; `_lookup` only reads), `tests/port_oracle.py`.

- [ ] **Step 1: Write the failing gate**

`tests/test_pure_python.py`:
```python
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_no_old_api_or_c_left():
    offenders = []
    for base in ("pyhvac", "tests", "tools"):
        for path in (ROOT / base).rglob("*.py"):
            if path.name == "test_pure_python.py":
                continue
            text = path.read_text()
            for pattern in (
                r"^\s*(from|import)\s+\S*\b(plugins|legacy|irhvac|hvaclib)\b",
                r"^\s*from\s+\S+\s+import\s+.*\b(irhvac|LegacyDevice)\b",
                r"PluginObject",
            ):
                for line in text.splitlines():
                    code = line.split("#", 1)[0]
                    if re.search(pattern, code):
                        offenders.append(f"{path.relative_to(ROOT)}: {line.strip()}")
    assert offenders == []


def test_nothing_compiled_is_shipped():
    assert not list((ROOT / "pyhvac").rglob("*.so"))
    assert not (ROOT / "setup.py").exists()
```
Run: `python -m pytest -q tests/test_pure_python.py`
Expected: FAIL listing the old API files.

- [ ] **Step 2: Delete**

```bash
git rm -r -q pyhvac/plugins pyhvac/legacy.py tests/test_legacy.py tests/test_legacy_oracle.py tests/test_legacy_encode_all.py tests/test_irghvac.py tests/test_hvac_protocol.py tests/test_golden_native.py tools/oracle_generate.py tools/golden_generate.py setup.py MANIFEST.in
git rm -q IRremoteESP8266 2>/dev/null; git config -f .gitmodules --remove-section submodule.IRremoteESP8266 2>/dev/null; git add .gitmodules 2>/dev/null
rm -f pyhvac/irhvac.py pyhvac/_irhvac*.so
```
Then remove the remaining references the gate lists: record-mode code in `tests/c_oracle.py` (keep `FIXTURES`, `_store`, `_load`, `_key`, a read-only `_lookup`, `c_encode`, `c_sequence` returning replayed data), the session hook in `tests/conftest.py`, `tools/state_grid.py` if unused, `*_family.py` tests that assert on legacy registrations, and comments that name `irhvac`/`legacy` only when they are code (the gate ignores comments).
Run: `python -m pytest -q tests`
Expected: 0 failed, 0 skipped for C (`grep -rn "importorskip" tests` has no `irhvac`).

- [ ] **Step 3: Commit**

```bash
black -q pyhvac tests tools
git add -A
git commit -m "Remove the old plugin API, the C extension and its build"
```

### Task 7: Command-line tool

**Files:** Replace `pyhvac/__main__.py`; create `tests/test_cli.py`.

**Interfaces:**
- Consumes: `registry.brands/models/get_device`, `HvacState`, `pyhvac.ir.formats.to_broadlink/to_pronto/to_raw`.
- Produces: `python -m pyhvac --list`, `python -m pyhvac --list-models BRAND`, `python -m pyhvac BRAND MODEL --mode cool --temperature 24 [--fan F] [--swing-v S] [--swing-h S] [--feature name=value ...] [--off] [--format broadlink|pronto|raw]`.

- [ ] **Step 1: Write the failing test**

`tests/test_cli.py`:
```python
import base64
import subprocess
import sys

from pyhvac import registry
from pyhvac.ir.formats import to_broadlink
from pyhvac.state import HvacState


def run(*args):
    return subprocess.run(
        [sys.executable, "-m", "pyhvac", *args], capture_output=True, text=True, check=True
    ).stdout


def test_lists_brands_and_models():
    assert "Daikin" in run("--list").splitlines()
    brand = "Daikin"
    assert run("--list-models", brand).splitlines() == registry.models(brand)


def test_broadlink_output_is_the_devices_command():
    brand = "Daikin"
    model = registry.models(brand)[0]
    dev = registry.get_device(brand, model)
    expected = to_broadlink(dev.encode(None, HvacState(True, "cool", 24.0)).signal)
    out = run(brand, model, "--mode", "cool", "--temperature", "24")
    assert base64.b64decode(out.strip()) == expected
```
Run: `python -m pytest -q tests/test_cli.py`
Expected: FAIL (the old CLI imports `plugins`, deleted in Task 6).

- [ ] **Step 2: Write the CLI**

`pyhvac/__main__.py`:
```python
"""Command line: list brands/models, or print the IR command for a state."""

import argparse
import base64
import sys

from . import registry
from .ir.formats import to_broadlink, to_pronto, to_raw
from .state import HvacState


def _feature(text):
    name, _, value = text.partition("=")
    if value.lower() in ("on", "true", "yes"):
        return name, True
    if value.lower() in ("off", "false", "no"):
        return name, False
    return name, value


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pyhvac", description=__doc__)
    parser.add_argument("brand", nargs="?")
    parser.add_argument("model", nargs="?")
    parser.add_argument("--list", action="store_true", help="list the brands")
    parser.add_argument("--list-models", metavar="BRAND", help="list a brand's models")
    parser.add_argument("--mode", default="cool")
    parser.add_argument("--temperature", type=float, default=24.0)
    parser.add_argument("--fan", default="auto")
    parser.add_argument("--swing-v", default="off")
    parser.add_argument("--swing-h", default="off")
    parser.add_argument("--feature", action="append", default=[], type=_feature)
    parser.add_argument("--off", action="store_true", help="send power off")
    parser.add_argument(
        "--format", choices=("broadlink", "pronto", "raw"), default="broadlink"
    )
    opts = parser.parse_args(argv)
    if opts.list:
        print("\n".join(registry.brands()))
        return 0
    if opts.list_models:
        print("\n".join(registry.models(opts.list_models)))
        return 0
    if not opts.brand:
        parser.error("a brand is required (see --list)")
    device = registry.get_device(opts.brand, opts.model)
    state = HvacState(
        power=not opts.off,
        mode=opts.mode,
        temperature=opts.temperature,
        fan=opts.fan,
        swing_v=opts.swing_v,
        swing_h=opts.swing_h,
        features=dict(opts.feature),
    )
    signal = device.encode(None, state).signal
    if opts.format == "broadlink":
        print(base64.b64encode(to_broadlink(signal)).decode())
    elif opts.format == "pronto":
        print(to_pronto(signal))
    else:
        print(" ".join(str(p) for p in to_raw(signal)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
Check `to_raw`'s return type in `pyhvac/ir/formats.py` and adapt the last print if it already returns text.
Run: `python -m pytest -q tests/test_cli.py`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
black -q pyhvac tests
git add pyhvac/__main__.py tests/test_cli.py
git commit -m "CLI on the registry: list brands/models, print a command"
```

### Task 8: Packaging and CI

**Files:** Replace `pyproject.toml`; modify `pyhvac/__init__.py`; delete `.github/workflows/build_wheels.yml`; create `.github/workflows/test.yml`, `.github/workflows/release.yml`.

- [ ] **Step 1: Find the oldest Python the suite passes on**

```bash
for v in 3.9 3.10 3.11; do command -v python$v >/dev/null && python$v -m pytest -q tests 2>&1 | tail -1 | sed "s/^/$v: /"; done
```
Expected: the oldest version that passes becomes `requires-python` (fall back to `>=3.10` if no older interpreter is installed and the code uses 3.10 syntax; check with `grep -rn "match \|\bcase \b\| | None" pyhvac`).

- [ ] **Step 2: Write `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=64"]
build-backend = "setuptools.build_meta"

[project]
name = "pyhvac"
dynamic = ["version"]
description = "Pure-Python IR command generator for HVAC units"
readme = "README.md"
license = { file = "LICENSE" }
authors = [{ name = "François Wautier", email = "fwautier61@gmail.com" }]
requires-python = ">=3.9"
dependencies = []
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]

[project.urls]
Homepage = "https://github.com/frawau/pyhvac"

[tool.setuptools.dynamic]
version = { attr = "pyhvac.__version__" }

[tool.setuptools.packages.find]
include = ["pyhvac*"]
```
Set `requires-python` from Step 1. In `pyhvac/__init__.py`: `__version__ = "0.2.0"`.

- [ ] **Step 3: Build and check the wheel**

```bash
python -m pip install -q build && python -m build -q . && ls dist/
python -m zipfile -l dist/pyhvac-0.2.0-py3-none-any.whl | grep -c "\.so" || true
```
Expected: `pyhvac-0.2.0-py3-none-any.whl` and `pyhvac-0.2.0.tar.gz`; `0` `.so` files.

- [ ] **Step 4: Workflows**

`.github/workflows/test.yml`:
```yaml
name: Tests

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python: ["3.9", "3.10", "3.11", "3.12", "3.13", "3.14"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
      - run: python -m pip install pytest
      - run: python -m pytest -q tests
```
(Start the matrix at the `requires-python` floor from Step 1.)
`.github/workflows/release.yml`:
```yaml
name: Release

on:
  release:
    types: [published]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python -m pip install build pytest
      - run: python -m pytest -q tests
      - run: python -m build
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/*

  upload_pypi:
    needs: [build]
    runs-on: ubuntu-latest
    if: github.event_name == 'release'
    environment:
      name: AutoPublish
      url: https://pypi.org/p/pyhvac
    permissions:
      id-token: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist
      - uses: pypa/gh-action-pypi-publish@release/v1
```
```bash
git rm -q .github/workflows/build_wheels.yml
```

- [ ] **Step 5: Commit**

```bash
rm -rf dist build *.egg-info
git add -A pyproject.toml pyhvac/__init__.py .github
git commit -m "Packaging: pure-Python pyproject, version 0.2.0; test and release workflows"
```

### Task 9: README and release notes

**Files:** Replace `README.md`; create `CHANGELOG.md`.

- [ ] **Step 1: Write the README**

Sections, each with a runnable example checked in Step 2:
1. What pyhvac is (pure-Python IR commands for HVAC units; ~400 models, 77 brands; decoding too).
2. Install: `pip install pyhvac`.
3. Use:
```python
from pyhvac import registry
from pyhvac.ir.formats import to_broadlink
from pyhvac.state import HvacState

device = registry.get_device("Daikin", registry.models("Daikin")[0])
command = device.encode(None, HvacState(True, "cool", 24.0))
packet = to_broadlink(command.signal)  # send with a Broadlink RM
```
4. State and capabilities: `HvacState` fields; `device.capabilities` (modes, `TemperatureRange`, `Choice` values and labels, features, actions); `previous` for toggle protocols (persist `command.state`).
5. Formats: Broadlink, Pronto, raw; decoding with `pyhvac.ir.codec.decode`.
6. Command line: `python -m pyhvac --list`, `--list-models`, a command example.
7. Adding a protocol: `tools/portkit.py`, fixtures, `pyhvac/protocols/`, a row in `pyhvac/brands.py`.
8. Migrating from 0.1.x:

| 0.1.x | 0.2.0 |
|---|---|
| `importlib.import_module(f"pyhvac.plugins.{brand}").PluginObject().get_device(model)` | `registry.get_device(brand, model)` |
| `dev.set_value("mode", "cool")`, `set_value("temperature", 24)`, ... | `HvacState(power=True, mode="cool", temperature=24.0, fan=..., swing_v=..., features={...})` |
| `frames = dev.build_ircode(); dev.to_broadlink(frames)` | `to_broadlink(device.encode(previous, state).signal)` |
| `dev.capabilities["temperature"]`, `all_capabilities["fan"]` | `device.capabilities.temperature`, `device.capabilities.fan` (values and labels) |
| brand = module name, e.g. `"mitsubishi_heavy_industries"` | brand as the maker writes it; lookups ignore case and punctuation |
| model strings of 0.1.x | new names (see `docs/superpowers/plans/2026-09-29-phase4/tables/names.md`); 0.1.x names still work for the former pure-Python devices only |

- [ ] **Step 2: Check the README examples**

Run: `python - <<'EOF'` with the Use example pasted, then `python -m pyhvac --list | head -3`.
Expected: no exception; brand names printed.

- [ ] **Step 3: Write `CHANGELOG.md`**

```markdown
# Changelog

## 0.2.0

Breaking: new API, pure Python.

- No C extension: IRremoteESP8266 protocols are ported to Python and
  verified against recordings of 0.1.7's output; wheels are py3-none-any.
- New API: `registry`, `HvacState`, `Device.encode(previous, target,
  actions)` -> `Command`; Broadlink, Pronto and raw output; decoding.
  The plugin API (`PluginObject`, `set_value`, `build_ircode`) is gone.
- Names: brands and models as the manufacturers write them; 0.1.x names
  still resolve for the former pure-Python devices.
- Capabilities: full control of what each protocol documents (setpoint
  ranges, fan levels, swing positions, features); controls that did
  nothing are removed.
- Output changes on purpose where 0.1.x sent wrong or undocumented codes
  (e.g. swing "on" never reached the C library; Airwell never sent a valid
  state; Ecoclim always sent Sleep; Eurom always had sleep on).
- Removed: Hitachi PC-LH3B and "generic 3" (HITACHI_AC3: 0.1.x sent
  nothing for them); Sharp "generic" (never produced a valid command).
```
(Adjust the removed-models list to decisions D1.)

- [ ] **Step 4: Commit**

```bash
git add README.md CHANGELOG.md
git commit -m "README for the 0.2.0 API, with a 0.1.x migration table; changelog"
```

### Task 10: Final review

- [ ] **Step 1: Full run**

Run: `python -m pytest -q tests`
Expected: 0 failed, no skip mentioning `irhvac`.
Run: `grep -rn "importorskip(\"pyhvac.irhvac\")" tests; ls pyhvac`
Expected: no grep output; `pyhvac` holds `__init__.py __main__.py brands.py choices.py device.py fields.py ir protocols registry.py state.py`.

- [ ] **Step 2: Whole-branch review**

Dispatch one reviewer on the most capable model over `git diff ports..HEAD` with this plan, the spec and the Review Focus list; fix Critical/Important findings with a failing test first; ledger the minors.

- [ ] **Step 3: Hand back**

Report to the author; merging the branch chain into main and publishing the 0.2.0 release each need the author's explicit go.
