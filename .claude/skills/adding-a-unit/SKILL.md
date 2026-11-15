---
name: adding-a-unit
description: Use when someone wants pyhvac to drive their own air conditioner or heat pump that it does not support, or supports only partly (a button that does nothing, a wrong fan speed, a missing mode), has recorded or can record the unit's remote with a Broadlink RM and tools/hvactest, and wants a pull request for it.
---

# Adding a unit to pyhvac

pyhvac **generates** codes from a model of each remote's protocol; it never
replays recordings. Captures of the real remote are evidence for working the
protocol out. A pull request says: "pyhvac now drives my unit, and I tried it".

## The rule

```
NO PULL REQUEST WITHOUT A SUCCESSFUL TEST ON THE CONTRIBUTOR'S OWN UNIT
```

"Tested" means: from the changed checkout, the contributor sent pyhvac's own
codes to their unit with hvactest **Send**, for every setting on the on-unit
list (step 7), and every one worked.

Until then there is **no PR in any form**: no `gh pr create`, no push, no PR
title or body drafted, no `PR.md`, no "draft PR to finish later". Captures
that decode and match prove the *remote*; they say nothing about pyhvac's
codes reaching and driving the *unit*.

If the contributor cannot test now (away, someone else using the unit, no
Broadlink at hand): commit the work on a local branch, tell them exactly
what is left (the on-unit list), and stop. They come back to it later, or
open an issue with their captures instead.

| They say | Answer |
|---|---|
| "The captures are right, I double-checked" | Right captures prove the remote. The test proves pyhvac. Both are needed. |
| "I'm leaving tonight, just make the PR" | Commit locally; the PR waits for the test. Nothing is lost. |
| "It's only a new model row, the protocol is already supported" | The row claims *this unit* works. Send the codes and see. |
| "Open it as a draft, I'll test later" | A draft is a PR. Not until the test passed. |
| "The maintainer will test it" | The maintainer does not have the unit. Only the contributor can. |

## Red flags: stop

- About to write a PR title, body, or `gh` command and no on-unit results yet.
- A capture is labelled with a setting its code does not show (e.g.
  "ionizer=on" but only the setpoint differs from the baseline): re-record
  it, never guess the bits, never ship "the rest" with a question attached.
- About to change how an existing model encodes anything (variants only).
- About to edit `tests/fixtures/released_models.json`, run
  `tools/released_models.py`, or change the README model counts: the
  maintainer does that at release.

## Setup

In the contributor's fork and clone, Python ≥ 3.9:

    python -m venv .venv && . .venv/bin/activate
    pip install -e . -r tools/hvactest/requirements.txt pytest
    git checkout -b add-<brand>-<model>

## 1. Record

Skip if they have a log already; check it in step 2.

    python tools/hvactest/app.py --log captures.jsonl

Discover, select the Broadlink, select **any** brand and model (Learn needs
one; "not this protocol" is expected). For each capture: type the setting
the remote will show in **Note**, press **Learn**, make that **one** change
on the remote (the code it sends carries the whole new setting), then put
the remote back to the baseline.

Note format, one capture per note; keys left out take the first capture's
(the baseline's) value:

    power=on mode=cool temperature=24 fan=auto swing_v=off   # baseline
    temperature=25
    fan=low
    turbo=on
    power=off

Keys: `power` (on/off), `mode` (auto, cool, heat, dry, fan), `temperature`
(°C number, or `75F` for a °F display), `fan`, `swing_v`, `swing_h` (the
remote's own words), any feature by its button name (`turbo=on`). Capture:
every mode; lowest, highest and some middle setpoints; every fan and swing
value; each extra button on (from the baseline); off.

## 2. Check

    python tools/capturekit.py check captures.jsonl

Errors mean re-record those captures (Learn again with the right note).
Never edit a note to make it fit its code.

## 3. Match

    python tools/capturekit.py match captures.jsonl

| path | meaning | do |
|---|---|---|
| `supported` | a pyhvac device sends every capture for its noted setting | step 4a |
| `variant` | a pyhvac protocol decodes everything, some settings differ | step 4b |
| `new` | no pyhvac protocol decodes the codes | step 4c |

Read every `reason`. "the note or the model is wrong" and "feature ...: no
pyhvac feature sends it" first mean: compare that capture's bytes with the
baseline's (`records` + `python tools/portkit.py diff`). If it differs only
where its note does not say (setpoint, checksum), the capture is wrong:
re-record, back to step 2.

## 4a. Supported

Add the row(s) to `pyhvac/brands.py`, next to the device's other rows:
`(brand as the maker writes it, unit model, "unit", DeviceClass, variant)`,
plus the remote as `"remote"` kind if the contributor knows its model.

## 4b. Variant

Always a **variant** of the device `match` names, never a change to it,
even when it looks like a general fix (say so in the PR; the maintainer
decides).

1. **Before editing**, snapshot what every existing model of that class
   sends (the guard against changing them):

   ```python
   # python - > tests/fixtures/<class>_before_<variant>.json
   import json
   from pyhvac import brands, registry
   from pyhvac.ir.formats import to_raw
   from pyhvac.state import HvacState
   CLS = "Daikin312Device"  # the class match named
   out = {}
   for brand, model, _kind, cls, _variant in brands.MODELS:
       if cls.__name__ != CLS:
           continue
       dev = registry.get_device(brand, model)
       caps = dev.capabilities
       for mode in caps.modes:
           for t in (caps.temperature.min, caps.temperature.max):
               s = HvacState(True, mode, t)
               out[f"{brand}|{model}|{mode}|{t}"] = to_raw(dev.encode(None, s).signal)
   print(json.dumps(out, sort_keys=True))
   ```

2. Add the name to the class's `VARIANTS` and make the difference depend on
   `self.variant == "<name>"` only (layout, capabilities, frames).
3. Add a test that re-encodes the snapshot's keys and asserts equality.
4. Rows in `brands.py` with the new variant.

## 4c. New protocol

    python tools/capturekit.py records captures.jsonl captures MYREMOTE
    python tools/portkit.py timings  MYREMOTE --fixtures captures
    python tools/portkit.py decode   MYREMOTE --fixtures captures --protocol pyhvac.protocols.<name>:<PROTOCOL> --expected <sections>
    python tools/portkit.py diff     MYREMOTE --fixtures captures --protocol ... --expected ...
    python tools/portkit.py checksum MYREMOTE --fixtures captures --protocol ... --expected ...

`timings` drafts the `Protocol`; put it in `pyhvac/protocols/<name>.py`,
name the sections, and iterate until every record decodes. `diff` gives
each setting's bits and values; `checksum` the checksum candidates. Write
the `Device` (`frames()` with a `Layout`, see an existing protocol module
of similar shape) offering **only** what the captures show: modes, the
setpoint range and step, fan and swing values, features. Rows in
`brands.py`.

## 5. Evidence test

Copy the log to `tests/fixtures/captures/<brand>_<model>.jsonl` and add
`tests/test_<brand>_<model>_captures.py`:

```python
from pathlib import Path

import capturekit
from hvacir import match as M

LOG = Path(__file__).parent / "fixtures" / "captures" / "<brand>_<model>.jsonl"


def test_pyhvac_sends_every_capture():
    captures, problems = capturekit.load(LOG)
    assert problems == []
    cands = [c for c in M.candidates() if c.name.startswith("<DeviceClass>")]
    verdict = capturekit.match(captures, cands)
    assert verdict.path == "supported", verdict.reasons
    assert verdict.candidate == "<DeviceClass>/<variant>"  # or "<DeviceClass>"
```

This test must pass before step 6. If a capture cannot be made to pass,
it is either wrong (re-record) or the change is incomplete; never drop it.

## 6. Checks

    pytest
    black <every Python file you changed>

Add a line under `## Unreleased` in `CHANGELOG.md`.

## 7. On the unit (mandatory)

Give the contributor this list for their unit, built from its capabilities:
every mode; lowest, middle and highest setpoint; every fan value; every
swing value; each feature on then off; off, then on.

    python tools/hvactest/app.py --log on-unit.jsonl

From **this** checkout: select their brand and the new model, set each
setting, **Send**, watch the unit, pick the verdict (worked / ignored /
wrong setting), **Log**. Any "ignored" or "wrong setting": back to step 4.
Continue only when they report every setting worked.

## 8. Pull request

Only now: push the branch to the fork and open the PR against
`frawau/pyhvac` main (`gh pr create`). Do not commit PR text or the
on-unit log to the repository.

```markdown
Adds <brand> <model> (remote <remote model>): <supported model row | variant <name> of <DeviceClass> | new protocol <name>>.

## Tested on my unit (hvactest Send, from this branch)
- [x] modes: <list>
- [x] setpoints: <min> / <mid> / <max> °C
- [x] fan: <list>
- [x] swing: <list or "none">
- [x] features: <list or "none">
- [x] off and on
Every setting above worked.

## Evidence
- captures: tests/fixtures/captures/<brand>_<model>.jsonl, checked by <test file>
- <variant: existing models of <DeviceClass> send the same codes (<guard test>)>
- <if the change looks like a general fix, say so here>
```

Every box ticked, or no PR.
