# From captures to a pull request: the `adding-a-unit` skill — design

## Intent

Someone whose A/C pyhvac does not drive has the unit, its remote, a
Broadlink RM and Claude Code. Today they can record the remote (see
`docs/capturing-codes.md`) and open an issue; the maintainer then works the
protocol out without the unit. The goal is to let that contributor go all
the way: record, find out whether this is a known protocol, a variant of
one, or a new one, write it, check it on their own unit, and open a pull
request the maintainer can review with evidence it works.

Users of this: contributors running Claude Code in their clone (fork) of
pyhvac, on their own unit. Not (yet) the maintainer working from an issue.

## Goals

- A Claude Code skill shipped in the repository (`.claude/skills/`), found
  by anyone who opens Claude Code in a pyhvac clone.
- The exact, error-prone steps are code with tests (`tools/capturekit.py`),
  not improvised by the model each run: reading the captures, checking
  them, matching them against pyhvac, writing portkit's input.
- Three outcomes, decided by evidence:
  1. **Already supported**: a pyhvac model reproduces every capture → add
     the brand/model row(s) only.
  2. **Variant**: an existing protocol decodes every capture, some fields
     differ → add a variant of that device.
  3. **New protocol**: nothing decodes → write a protocol and device with
     portkit's help.
- Every outcome ends with the contributor sending pyhvac's own codes to the
  unit (hvactest Send) and confirming each setting, then a PR from their
  fork that states what was checked.
- **Hard rule (user, 2026-11-15): a PR is offered only after the
  contributor has tested the change successfully on their own unit.** The
  skill does not open or draft a PR otherwise, the PR body carries a
  checklist of what was tested on the unit, and the guide and README say
  so.
- README (pyhvac) and the capture guide describe the skill.

## Non-goals

- The maintainer-from-an-issue path (no unit at hand). Later.
- Capture devices other than a Broadlink RM through hvactest (the paste box
  already takes base64 Broadlink codes learned elsewhere; nothing more).
- Automating protocol code generation: protocols differ too much; writing
  the `Device` and its layout stays a judgement step guided by the skill.

## Anti-goals (failures even if it works)

- A PR claiming support that was never checked on the unit: the skill must
  stop and ask the contributor, and the PR must say what was and was not
  checked.
- Replaying captures: pyhvac generates codes from a protocol model; it
  never stores and replays recordings. Captures may appear in tests as
  evidence, never as runtime data.
- Inventing settings: a capture whose setting is unknown is left out, not
  guessed.
- Breaking a released model: the released-models test must keep passing;
  a variant must not change what existing models send.
- Metric/UTC rules: °C in core; a °F remote is handled the existing way
  (°C range, encoder converts, the Airspool pattern).

## Approaches

- A. Skill instructions only, model writes throwaway scripts: nothing new
  to maintain, but every run improvises the exact steps where mistakes
  hide (pairing codes with settings, judging variant vs new).
- **B. Skill + a small tested helper (chosen by the user).** capturekit
  does the bookkeeping and the matching; the skill does the judgement.
- C. A generator writing protocol code: not realistic.

## Design

### Recording: the setting travels with its code (hvactest change)

hvactest's `learn` log event gains `note`: the Note box's text when Learn
was pressed. The contributor types the setting the remote will show,
presses Learn, presses the remote's button. No separate notes file, no
pairing by order.

Note format (machine-readable, documented in the guide):

    power=on mode=cool temperature=24 fan=auto swing_v=off  # free comment

`key=value` pairs separated by spaces; anything after `#` is a comment.
Keys: `power` (on/off), `mode`, `temperature` (number; `temperature=75F`
for a °F display), `fan`, `swing_v`, `swing_h`, and any feature name
(`turbo=on`, `light=off`, ...). Values are the remote's own words (fan
`low`, `2`, `quiet` ...): the matcher maps them. Keys left out mean "as
the baseline".

The guide's Step 2 is updated to this; the notes-file instructions go.

### `tools/capturekit.py`

    python tools/capturekit.py check  captures.jsonl
    python tools/capturekit.py match  captures.jsonl [--json]
    python tools/capturekit.py records captures.jsonl OUT_DIR NAME

- **check**: lists the learned captures with their parsed settings and
  flags: learn events without a code, captures without a note or with an
  unparsable note, keys missing against the first (baseline) capture,
  two identical codes under different settings, the same setting with
  different codes (toggle bits or clock — reported, not an error).
  Non-zero exit if any capture is unusable.
- **Strictness (builder check, ruled 2026-11-15):** hvacir's `covered` is
  tuned for messy SmartIR files (it accepts codes pyhvac only sends for
  another state, needs 15 % verified, maps fan/swing words freely).
  capturekit wraps it without changing it (the SmartIR import results stay
  as they are): **supported** only when every capture is reproduced under
  the setting its note gives, the remote's words mapping one-to-one;
  relabels and ambiguous label maps are reported as "the note or the model
  is wrong" and the skill asks the contributor. Base captures supported
  but a feature capture differs → variant path.
- **match**: the captures with settings in the SmartIR shape (mode/fan/
  swing/temperature tree plus `off`) go through `hvacir.match.match`
  against every pyhvac candidate; verdict covered → "already supported:
  <model>", near → "variant of <device class>: fields that differ ...",
  unknown → "new protocol". Captures carrying feature keys are then
  compared one by one (`hvactest.compare.compare`) against the best
  candidate. `--json` gives the same for the skill.
- **records**: writes `OUT_DIR/NAME.json.gz`, portkit's input
  (`{"state", "pulses"}` per capture).
- Pure functions under a thin CLI, tested in `tests/test_capturekit.py`
  with captures synthesised from existing pyhvac devices (a known model
  must come out covered; a model with a field changed must come out near
  with that field; noise must come out unknown).

### The skill (`.claude/skills/adding-a-unit/SKILL.md`)

Steps the skill drives, stopping for the contributor where only they can
act:

1. Prerequisites: a fork and clone, the venv and hvactest requirements
   (guide's Installing), a Broadlink found by hvactest.
2. Recording with notes (guide's Step 2); `capturekit check` until clean.
3. `capturekit match` → one of the three paths.
4. Path work:
   - supported: `brands.py` row(s) with the contributor's brand and model;
   - variant: **always a variant** (user, 2026-11-15), never a change to
     the existing device: add it to the device's `VARIANTS`, enable the
     difference only for that variant, and test that every existing
     model of that class sends byte-identical codes before and after. If
     the difference looks like a general fix or a missing capability, the
     PR says so and the maintainer decides in review;
   - new: `capturekit records` → portkit `timings`/`decode`/`diff`/
     `checksum` → `pyhvac/protocols/<name>.py` (Protocol, Device, layout,
     capabilities from what the captures show) and `brands.py` rows.
5. Tests: a test file with the captures as evidence (setting + code) that
   asserts pyhvac's encoding of each setting decodes to the captured
   frames, modulo unrecorded fields (as `compare` does).
6. On the unit (**mandatory**): the contributor sends pyhvac's codes with
   hvactest for a list of settings the skill gives (each mode, min/max/mid
   setpoint, each fan and swing value, each feature, off/on) and reports
   the result. The skill does not go on to the PR until every listed
   setting worked; a failure goes back to step 4. With hvactest `--log`,
   the Send + verdict lines are the record.
7. Full suite, `black`, CHANGELOG entry. Contributors do **not** run
   `tools/released_models.py` (ruled 2026-11-15: the maintainer adds new
   pairs at release; avoids fixture conflicts between PRs and permanent
   aliases for names changed in review).
8. PR from the fork (`gh pr create`), body: unit and remote, path taken,
   what was checked on the unit, anything not checked.

The skill follows superpowers:writing-skills conventions (frontmatter
`name` + `description` stating when to use it), and is tested by running
it with a subagent on synthesised captures for each path.

### Docs

- `docs/capturing-codes.md`: Note format replaces the notes file; a
  section "With Claude Code" pointing to the skill.
- pyhvac README "Getting a unit supported": mention the skill (one
  paragraph).

## Left to the builder

- capturekit's exact output layout and JSON keys.
- How a note's fan/swing words are matched when the matcher's label
  mapping is ambiguous (report it; the skill asks the contributor).
- The skill's wording and how it is split (one SKILL.md, plus a reference
  file if long).
