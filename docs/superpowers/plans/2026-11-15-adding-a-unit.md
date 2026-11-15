# Adding a unit: captures to a tested PR — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A contributor with Claude Code turns hvactest captures of their own remote into a PR (supported model row, variant, or new protocol) that they have tested on their unit.

**Architecture:** hvactest saves the Note text with each learned code. `tools/capturekit.py` (tested, pure functions + thin CLI) reads the log, checks it, matches it strictly against pyhvac (wrapping `hvacir.match.match` unchanged) and writes portkit records. A project skill `.claude/skills/adding-a-unit/SKILL.md` drives the judgement steps and the mandatory on-unit test before any PR.

**Tech Stack:** Python ≥ 3.9, existing tools (hvactest, hvacir, portkit), Claude Code skills.

**Spec:** docs/superpowers/specs/2026-11-15-capture-to-pr-skill-design.md

## Global Constraints

- A PR is offered only after the contributor has tested the change successfully on their own unit (user, hard rule).
- Variant path: always a variant; existing models of the class send byte-identical codes.
- Supported only when every capture is reproduced under its noted setting, labels one-to-one; `hvacir/match.py` is not modified.
- pyhvac never replays captures; captures appear only as test evidence.
- Contributors do not run `tools/released_models.py`.
- Core °C/UTC; `temperature=75F` notes are converted with the Airspool rule (°F → °C) at the edge.
- black on every modified Python file; text for people uses they/them for the contributor.

## Review Focus

1. A note with a typo'd key or value (`tempreature=24`, `mode=cool24`) must be reported by `check`, never silently dropped or mapped.
2. Two different fan words mapped to the same pyhvac fan (labels not one-to-one) must not yield "supported".
3. A °F remote (`temperature=75F` … `86F`) must match like a °C one.
4. Captures that repeat (same setting twice, codes differ by a toggle bit) must not block `check` (warning, exit 0).
5. A log with zero usable captures (all timeouts) must give a clear message and exit non-zero from every command.

---

### Task 1: hvactest saves the Note with each learned code

**Files:** Modify `tools/hvactest/app.py` (`_learn`, `record("learn", ...)`); Test `tests/test_hvactest_app.py`.

**Interfaces:** Produces: learn log events `{"event": "learn", "model": [...], "code": <b64|None>, "note": <str>}` (note = Note box text, stripped; `""` when empty).

- [ ] **Step 1: failing test** `test_learn_logs_the_note(tmp_path)`: set `#note` value to `"power=on mode=cool temperature=24"`, click Learn with `FakeLink(learned)`, read the log: the learn record has `note == "power=on mode=cool temperature=24"`. Also the timeout case logs `note`.
- [ ] **Step 2:** run `pytest tests/test_hvactest_app.py -k note` → FAIL (KeyError 'note').
- [ ] **Step 3:** add `note=self.query_one("#note", Input).value.strip()` to both learn records.
- [ ] **Step 4:** test passes; `pytest tests/test_hvactest_app.py` green.
- [ ] **Step 5:** black, commit "hvactest: save the Note with each learned code".

### Task 2: capturekit — read and check captures

**Files:** Create `tools/capturekit.py`; Test `tests/test_capturekit.py`.

**Interfaces:** Produces:
- `parse_note(text: str) -> dict[str, str]` — `key=value` pairs, `#` starts a comment; raises `ValueError` on a token without `=`, an empty key/value, or a repeated key.
- `@dataclass Capture: index: int (1-based, learn events with a code), time: str, note: str, setting: dict[str, str], packet: bytes`
- `load(path) -> tuple[list[Capture], list[str]]` — captures and problems. Learn events without a code (timeouts, retried) are not captures and not problems. A learn event whose note does not parse → problem `"capture N: <ValueError text>"`, capture dropped. Non-learn events are ignored.
- `CORE_KEYS = ("power", "mode", "temperature", "fan", "swing_v", "swing_h")`; `MODES = ("auto", "cool", "heat", "dry", "fan")`.
- `check(captures) -> tuple[list[str], list[str]]` — (errors, warnings). Errors: no captures; missing note; `mode` not in MODES; `power` not on/off; `temperature` not a number with optional `F`; a capture lacking a key the first (baseline) capture has; identical packets under different settings. Warnings: same setting with different packets (toggle/clock); feature keys (non-core) listed.
- CLI `python tools/capturekit.py check LOG` prints a table (index, note, flags) then errors/warnings; exit 1 on errors.

- [ ] **Step 1: failing tests** (captures synthesised from `registry.get_device("Daikin","FTXM20R5V1B")` with `to_broadlink`, written through `hvactest.log.SessionLog`): `test_parse_note` (comment, spaces, errors), `test_check_clean_log`, `test_check_reports_bad_notes` (Review Focus 1: `tempreature=24` → "missing temperature" vs baseline; `mode=cool24` → bad mode), `test_check_warns_on_repeats` (Review Focus 4: exit code 0), `test_empty_log` (Review Focus 5: error "no usable capture").
- [ ] **Step 2:** run → FAIL (module missing).
- [ ] **Step 3:** implement.
- [ ] **Step 4:** green; black; commit "capturekit: read and check hvactest captures".

### Task 3: capturekit — match strictly, write portkit records

**Files:** Modify `tools/capturekit.py`; Test `tests/test_capturekit.py`.

**Interfaces:** Consumes Task 2. Produces:
- `to_smartir(captures) -> hvacir.codes.SmartIRFile` — core captures only (no feature keys): `power=off` → `Key("off", None, None, None)`; else `Key(mode→SmartIR name ("fan"→"fan_only"), fan, swing label, °C or °F number)`, swing label `f"{swing_v}/{swing_h}"` (missing side `"-"`); `max_temperature` = largest noted value (so °F ≥ 50 is tried first by the matcher); controller `"Broadlink"`, encoding `"Base64"`.
- `@dataclass Verdict: path: str ("supported"|"variant"|"new"), candidate: str|None, fans: dict, swings: dict, gaps: dict[str,int], features: dict[str, str], reasons: list[str]`.
- `match(captures, cands=None) -> Verdict` — `cands` defaults to `hvacir.match.candidates()`. Runs `hvacir.match.match(to_smartir(...), cands)`. **supported** iff verdict `covered` and `verified == decoded == usable` and `relabelled == 0` and fan and swing maps are one-to-one and every feature capture is reproduced; **variant** if `covered`/`near` otherwise (reasons list relabels, many-to-one labels, gaps, unreproduced feature captures); **new** if `unknown`. Feature captures: for the candidate's device, find the `(feature, value)` whose encoding of the capture's core setting + that feature `compare()`s "same"; map the remote's word to it in `features`, else reason "feature <word>: no pyhvac feature sends it".
- `records(captures, out_dir, name) -> Path` — `out_dir/name.json.gz`, `[{"state": setting, "pulses": [...]}]`, portkit's format.
- CLI: `match LOG [--json]`, `records LOG OUT_DIR NAME`.

- [ ] **Step 1: failing tests:** `test_known_model_is_supported` (Daikin FTXM20R5V1B captures: modes, 3 setpoints, 3 fans, off → path supported, candidate contains "Daikin"); `test_fahrenheit_notes_match` (Review Focus 3: a °F-native model's captures noted `temperature=75F`… → supported); `test_labels_not_one_to_one_are_not_supported` (Review Focus 2: two fan words for the same code → not supported, reason names the fan words); `test_missing_variant_is_variant` (captures from `("Beko", "BEVCA 120")` (ElectraAcDevice variant "aux"), with the `ElectraAcDevice/aux` candidate removed from `cands` → path variant, candidate is the base class); `test_unknown_code_is_new` (an NEC-like pulse train → path new); `test_feature_capture_is_mapped` (Daikin captures + `powerful=on` note → features maps "powerful" word); `test_records_round_trip` (portkit `load_records` reads the file; `decode` with DAIKIN312 decodes all).
- [ ] **Step 2:** run → FAIL.
- [ ] **Step 3:** implement (reuse `hvactest.compare.compare` and `packet_pulses`).
- [ ] **Step 4:** green; full `pytest tests/test_capturekit.py tests/test_hvacir_match.py`; black; commit "capturekit: strict match against pyhvac, portkit records".

### Task 4: the skill

**Files:** Create `.claude/skills/adding-a-unit/SKILL.md` (+ `reference.md` if over ~300 lines).

Follow superpowers:writing-skills (load it at task start): frontmatter `name: adding-a-unit`, `description:` "Use when a contributor wants pyhvac to drive their own air conditioner: recording its remote with a Broadlink and hvactest, turning the captures into a supported-model row, a variant, or a new protocol, testing it on their unit, and opening a pull request."

Content, in order (spec "The skill" steps 1–8), with these fixed rules stated as rules, not suggestions:
- **No PR without a successful test on the contributor's own unit**: the skill must not run `gh pr create` or draft a PR body until the contributor has confirmed every setting on the on-unit list worked; if they cannot test, stop and say the change stays local (they may open an issue instead).
- Never invent a setting; a capture with an unclear note is re-recorded or left out.
- Variant only, never a change to existing behaviour; a byte-identical test over every existing model of the class.
- No `tools/released_models.py`.
- On-unit list: every mode, min/mid/max setpoint, every fan and swing value, every feature on/off, off and on; with `--log`, each Send followed by a verdict + Log.
- PR body template with a checklist of what was tested on the unit (all must be ticked) and the path taken.
- Commands exactly as `capturekit`, `portkit`, hvactest take them.

- [ ] **Step 1 (RED, per writing-skills):** run a subagent *without* the skill on the scenario "here is captures.jsonl (synthesised: a Daikin variant), make a PR" and note where it goes wrong (skips on-unit test, edits the base device, runs released_models, …).
- [ ] **Step 2:** write the skill addressing those.
- [ ] **Step 3 (GREEN):** rerun the subagent with the skill on the same scenario and on a "new protocol" scenario (stub hvactest/unit/PR steps: the subagent must stop and ask at the on-unit step); fix gaps.
- [ ] **Step 4:** commit "Skill: adding-a-unit".

### Task 5: docs

**Files:** `docs/capturing-codes.md`, `README.md` (pyhvac). (The earlier uncommitted guide + README changes are committed here.)

- [ ] Guide Step 2: type the setting in hvactest's Note box before each Learn, in the note format (keys, values, `F` suffix, comment), replacing the notes file; protocol authors' section uses `capturekit records` instead of the snippet; new section "With Claude Code" (open Claude Code in your fork, ask to add your unit; the `adding-a-unit` skill) with the rule in bold: **a pull request is only for a change you have tested successfully on your own unit**; tools table gains capturekit.
- [ ] README "Getting a unit supported": one paragraph on the skill, same bold rule.
- [ ] Commit "Docs: capturing codes, capturekit, the adding-a-unit skill".

Then: final whole-branch review (one opus reviewer), fixes, report.
