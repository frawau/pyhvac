# Phase 4: pure-Python pyhvac 0.2.0 — design

Status: approved in conversation 2026-09-29 (sections 1–5). Branch: `phase4`,
forked from `ports`.

## Intent

Ship a clean, pure-Python pyhvac: no C extension, no old plugin API, one
consistent `Device` API for every supported model, with capabilities that
give full control of what each protocol documents. The consumer (the
author's SmartIR fork) is migrated later, separately; nothing in SmartIR
changes in this phase.

What the author said:
- Start phase 4; skip 0.1.8 (it will soon be obsolete).
- Teco/alaska models that drive TECHNIBEL_AC: group them with the other
  Technibel models.
- Kaysun swing code, Goodweather light/turbo toggles, Sharp powerful-while-
  off: unknown; keep current behaviour.
- Capabilities: allow full control (e.g. AIRTON full temperature range),
  remove controls that do nothing, but keep the possibility to add them back.
- Port the eight native (pre-IRremoteESP8266) models.
- Structure: split protocol code from the brand/model table (approach 2).
- The README must be updated since the plugin API goes away.

Assumptions (not stated by the author, open to correction):
- Brand and model strings stay byte-identical to today's registry output.
- The oracle and golden fixtures remain the acceptance evidence.
- `requires-python` is the oldest version the suite passes on.

Success criteria:
- `import pyhvac` and every registered model work without any compiled
  code; the wheel is `py3-none-any`.
- `registry.get_device(brand, model)` serves every pre-phase-4 brand/model
  pair except the two HITACHI_AC3 models, with a `Device`.
- No `importorskip("pyhvac.irhvac")` remains in the tree; the evidence the
  C-gated tests held survives as frozen fixtures.
- The old API (`plugins/`, `PluginObject`, `hvaclib`, `legacy.py`, `irhvac`,
  SWIG build) is gone.
- README, release notes and CI describe and ship the new package.

## 1. Package layout and registry

```
pyhvac/
  ir/            unchanged: model, codec, formats
  state.py       unchanged: HvacState, Capabilities, Choice, ...
  device.py      unchanged: Device, Command
  fields.py      unchanged: the port kit
  choices.py     unchanged: shared Choices
  protocols/     one module per protocol family: layouts + Device classes only
  brands.py      brand -> {model -> (Device class, variant or None)}
  registry.py    brands(), models(brand), get_device(brand, model)
  __main__.py    command-line tool, rewritten on the registry
```

- `protocols/` modules are named after the protocol family (daikin, hitachi,
  mitsubishi_electric, mitsubishi_heavy, haier, lg, panasonic, sanyo, kelon,
  trotec, coolix, midea, gree, kelvinator, fujitsu, samsung, toshiba, sharp,
  airton, airwell, amcor, argo, bosch, carrier, corona, delonghi, ecoclim,
  electra, eurom, goodweather, mirage, neoclima, rhoss, tcl, technibel,
  transcold, truma, vestel, voltas, whirlpool, airspool, jtech). A module
  holds protocol code only: no brand tables, no `DEVICES` dicts.
- `brands.py` is the only place that knows which brand sells which model on
  which protocol. Each row gives the Device class and, where the class has
  remote variants, the variant explicitly. The per-module model->variant
  dicts go away (removing the name-collision fragility flagged in review for
  TCL and GREE); Devices keep their `variant=` parameter.
- Brand and model strings are byte-identical to the pre-phase-4 registry
  output. Removed rows: `hitachi:PC-LH3B`, `hitachi:generic 3` (HITACHI_AC3).
  Teco and alaska models become plain `TechnibelAcDevice` rows.
- `registry` keeps `brands()`, `models(brand)`, `get_device(brand, model)`
  and their signatures; `get_device` raises `KeyError` naming the known
  models for an unknown model. There are no import-time failures left, so
  the warn-and-skip path is removed.
- `__main__.py` is rewritten on the registry and `HvacState`: brand, model,
  mode, setpoint, fan, swing and features on the command line; output in
  Broadlink (base64/hex), Pronto or raw pulses. It also lists brands and
  models.
- Removed: `pyhvac/plugins/` (incl. `hvaclib.py`, every `PluginObject` and
  legacy class, the ~40 registration-only modules), `pyhvac/legacy.py`,
  `pyhvac/irhvac.py`, `pyhvac/_irhvac*.so`.

Tests: a frozen list of the pre-phase-4 brand/model pairs (minus
HITACHI_AC3) generated before any move, compared with `brands.py`; every row
instantiates and encodes a default state.

## 2. Capabilities: full control

Rule: a device's capabilities are what its protocol documents and the port
can encode, within the `HvacState` model. The legacy entity no longer bounds
them; the capability-equality tests are deleted.

- Setpoint: the header's min/max (`kXxxMinTemp`/`MaxTemp`) in the header's
  step; half degrees only where the protocol has a half-degree bit. Where
  the range differs by mode or variant, capabilities give the union and
  `normalise` clamps per mode as the protocol does (e.g. AIRTON 16–31;
  WHIRLPOOL DG11J191 gains 16–17).
- Modes, fan levels, swing positions (v and h): every documented value the
  layout can encode, with canonical names (`"1"`…`"n"`, `auto`, `off`,
  `swing`) and the existing labels. A protocol without auto fan offers none.
- Features: only from the existing vocabulary (powerful, quiet, economy,
  light, purifier, cleaning, sleep, ...), and only where the protocol has a
  bit or message the port sends.
- Excluded: timers, clock, sensor temperature, Fahrenheit.
- Controls that do nothing are removed from capabilities (e.g. DELONGHI
  quiet, SHARP economy/light, Technibel light, GOODWEATHER quiet, ARGO
  WREM2 quiet, the HITACHI_AC264 and LG2 no-ops). Their layout fields,
  value tables and comments stay, so re-adding one is a capabilities entry
  plus a test.
- Features the protocol supports and the port can encode by a documented
  field write are added. Anything needing new frame logic (a new special
  message) is listed in the plan as deferred, not invented.
- Evidence per new value: the header constant, a unit test, and a real
  capture reproduced where one exists. The oracle fixtures keep checking
  every state they cover.
- The plan carries, per protocol, a table old -> new capability with its
  source line, for the author's review before execution.

Kept as they are: Kaysun swing code (C's 0xA201), Goodweather light/turbo
sent every message, Sharp powerful while off.

## 3. Verification without C

- Kept: the oracle fixtures (`tests/fixtures/oracle/`), the golden fixtures
  (`tests/fixtures/golden/`), `assert_matches_oracle`, `Defect` (a declared,
  justified difference from the recorded C output), layout round-trips,
  real-capture tests, `tools/portkit.py`.
- Freeze before deletion, while C still works: the C-gated tests that hold
  evidence (sequence tests on a persistent C object, extra-state checks
  beyond the grid, glue-fixed swing checks, AIRWELL's C-state check) are
  run once in recording mode; every (state sequence, C output) they compare
  is written to `tests/fixtures/oracle_extra/<PROTO>.json.gz`. The tests
  are rewritten to read those fixtures (`assert_sequence_matches_c` becomes
  `assert_sequence_matches_fixture`). The recorder is committed with a
  README in the fixtures directory saying how every fixture was made
  (pyhvac 0.1.7's C path, the fixed-glue cases, the regenerated ones).
- Deleted: capability-equality tests (section 2), `test_legacy*.py`,
  `test_irghvac.py` and other old-API tests, `tools/oracle_generate.py`
  (its provenance moves to the fixtures README).
- Gate: zero `importorskip("pyhvac.irhvac")` in the tree at the end; pure
  test count at least today's pure count plus the converted tests, minus the
  deleted capability-equality tests (the plan states the exact number).

## 4. Native models, HITACHI_AC3, Teco

- The eight native models (daikin: generic (Daikinth), smash 2; lg:
  generic, dual inverter, inverter v; panasonic: generic, 4 way cassette;
  sharp: generic) get `Device` classes in their family's protocol module, on
  the existing `*_NATIVE` Protocol objects. Acceptance: the golden fixtures
  (pulses and Broadlink bytes of today's classes) reproduced byte for byte
  for every recorded state, through a golden-acceptance helper beside
  `assert_matches_oracle`. Layouts come from the legacy class code (the
  author's own protocols); a deviation only where the legacy code has an
  evident bug, justified and declared. Capabilities per section 2, from the
  legacy class's own tables.
- HITACHI_AC3: rows removed, layout-less code removed, noted in the release
  notes (the C path never sent anything for them).
- Teco/alaska: plain Technibel rows, full Technibel capabilities; the
  "teco" variant is removed.
- Airspool and JTech: already `Device`s; they move to `protocols/`.

## 5. Packaging, docs, release

- `setup.py`, the IRremoteESP8266 submodule, SWIG and cibuildwheel config go.
  `pyproject.toml` gets `[project]` metadata on setuptools: name, version
  0.2.0 single-sourced from `pyhvac/__init__.py`, no dependencies,
  `requires-python` set to the oldest version the suite passes on (checked
  in the plan). Output: an sdist and one `py3-none-any` wheel.
- CI: `test.yml` runs pytest on push/PR over the supported versions, no
  publishing; `build_wheels.yml` becomes `release.yml`: on a published
  release (or manual dispatch), build with `python -m build`, run the tests,
  upload via the existing trusted-publishing environment `AutoPublish`.
- README rewritten: what pyhvac is, install, the API (`registry`,
  `HvacState`, `Device.encode(previous, target, actions)` -> `Command`,
  Broadlink/Pronto/raw), capabilities and labels, adding a protocol
  (portkit, fixtures), and "migrating from 0.1.x" mapping
  `PluginObject().get_device` / `set_value` / `build_ircode` /
  `to_broadlink` to the new calls.
- Release notes for 0.2.0: breaking API, pure Python, dropped models,
  intentional output changes (the declared deviations, summarised),
  capability changes.
- Branches: at the end, only on the author's explicit go, the chain
  `ir-section-model -> state-api -> ports -> phase4` merges into main,
  folding main's unreleased 0.1.8 commits in. Tagging and publishing the
  0.2.0 GitHub release (which uploads to PyPI) is a separate explicit go.

## Order of work

1. Freeze the C evidence (section 3) and the brand/model list (section 1),
   while C still works.
2. Port the native models (section 4).
3. Create `protocols/`, `brands.py`, the new registry; move code across.
4. Capability audit and changes (section 2), after author review of the
   tables.
5. Delete the old API, C files and C-gated tests.
6. Packaging, CI, CLI, README, release notes.
7. Final whole-branch review and fix pass.

## Out of scope

SmartIR migration; new frame logic for features the ports do not encode
today; timers, clock, sensor temperature, Fahrenheit; the deferred kit items
(portkit Manchester/PulseWidth drafts, message-level Defects, further
checksum shapes), unless a step above needs one.
