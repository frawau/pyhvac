# Capturing IR codes to add a unit

pyhvac generates A/C codes from a model of each remote's protocol; it does
not replay recordings. To add a unit it does not support yet, the protocol
must be worked out from the codes its real remote sends. This page explains
the tools for recording those codes, how to record a set that is enough to
work the protocol out, and what to send in.

## With Claude Code

The repository ships a Claude Code skill, `adding-a-unit`
(`.claude/skills/adding-a-unit/`). Open Claude Code in your fork of pyhvac
and ask it to add your unit: it guides the recording, runs capturekit,
writes the model row, the variant or the new protocol with its tests, has
you try pyhvac's codes on your unit, and opens the pull request.

**A pull request is only for a change you have tested successfully on your
own unit**: with hvactest, from your changed checkout, you sent pyhvac's
codes for every mode, setpoints, fan and swing values, features, off and
on, and each one worked. The skill will not open a pull request before
that; if you cannot test now, your work stays on a local branch until you
can, or open an issue with your captures instead.

## The tools

They live in `tools/` in the source repository. They are development tools:
not in the package on PyPI.

| Tool | What it does | Who uses it |
|---|---|---|
| `tools/hvactest` | A terminal app driving a Broadlink RM: **sends** pyhvac's code for any model and setting, **learns** codes from a real remote, **compares** a learned code with what pyhvac sends, and **matches** a learned code against every pyhvac model. Can log everything to a file. | Anyone with a Broadlink RM |
| `tools/capturekit.py` | Reads an hvactest log: **checks** the captures and their notes, **matches** them against pyhvac (already supported, a variant of a pyhvac protocol, or a new protocol), and writes portkit's input. | Contributors, protocol authors |
| `tools/portkit.py` | Works out a protocol from recorded codes: timings and a draft `Protocol`, which bits each setting changes, and checksum candidates. | Protocol authors |
| `tools/hvacir` | Runs pyhvac against the community SmartIR code files and reports which files pyhvac already generates. | Maintainers |
| `tools/released_models.py` | Adds the current models to the list the "a released model never goes away" test checks. Run at each release. | Maintainers |

## Installing

You need Python 3.9 or newer and git. For hvactest, a Broadlink RM (RM4
mini, RM4 pro, RM mini 3, ...) already set up on your network with the
Broadlink app.

    git clone https://github.com/frawau/pyhvac.git
    cd pyhvac
    python -m venv .venv
    . .venv/bin/activate          # Windows: .venv\Scripts\activate
    pip install -e .
    pip install -r tools/hvactest/requirements.txt

capturekit, portkit, hvacir and released_models need nothing beyond
`pip install -e .`.

## hvactest

    python tools/hvactest/app.py [--ip ADDRESS] [--log FILE] [--offline]

- `--ip`: the Broadlink's address. Without it, hvactest looks for Broadlink
  devices by broadcast (on Linux on every network interface, elsewhere on
  the default one). Give the address if yours is not found.
- `--log FILE`: append one JSON line per action to `FILE`, with UTC
  timestamps. Off by default. **Turn it on when recording codes to send
  in.**
- `--offline`: no Broadlink; Compare and Match still work on pasted codes.

The screen has the Broadlink, brand and model on the left, the chosen
model's settings (power, mode, setpoint in °C, fan, swing, features) in the
middle, results on the right, and the actions at the bottom:

- **Discover** finds Broadlink devices; **Rename** gives the selected one a
  name (kept in `~/.pyhvacrc`).
- **Send** sends pyhvac's code for the settings shown. Then pick a verdict
  (worked, ignored, wrong setting), add a note, and press **Log**.
- **Learn** waits 10 s for a code from the real remote: point the remote at
  the Broadlink from 5 to 10 cm and press a button. The learned code is
  then compared with pyhvac's code for the settings shown. With `--log`,
  it is saved with the Note box's text: type the setting before Learn.
- **Compare** compares the last learned (or pasted) code with pyhvac's code
  for the settings shown: same, differs (with the fields that differ), or
  "not this protocol".
- **Match** tries the learned code against every pyhvac model and lists
  the models, and the settings, that send it.
- The paste box takes a base64 Broadlink code learned elsewhere (Home
  Assistant's Broadlink integration, for example).
- `q` quits.

Learn needs a brand and model selected. When your unit is not supported,
select any model: the comparison will say "not this protocol", which is
expected, and the code is learned and logged all the same.

## Step 1: is the unit already supported?

Many units use a protocol pyhvac already has, under another brand's name.

1. Start `python tools/hvactest/app.py`, press Discover, select the
   Broadlink.
2. Select any brand and model, press **Learn** and press the power button
   on the real remote.
3. Press **Match**. If models are listed, try them: select one, set the
   settings shown on your remote, press **Send** and see whether the unit
   follows. Check a few modes, setpoints and fan speeds.

If your own model is listed and works, tick its row in
[VERIFIED.md](../VERIFIED.md) in a pull request. If another model works,
open an issue with the brand and model of your unit and remote and the
pyhvac model that works: adding a name for it is quick. If none works, or
Match lists nothing, go on to step 2.

## Step 2: record the remote

A protocol is worked out by comparing codes that differ in **one setting
only**. So the recording is a set of captures, each one setting change away
from a baseline, each carrying a note saying what the remote shows.

1. Start hvactest with a log:

       python tools/hvactest/app.py --log captures.jsonl

   Select the Broadlink and any brand and model.
2. Choose a baseline and set the real remote to it, for example: on, cool,
   24 °C, fan auto, swing off, every extra feature off.
3. For each capture: type the setting the remote will show into **Note**,
   press **Learn**, then on the real remote make that **one** change (the
   code the remote sends then carries the whole new setting). Put the
   remote back to the baseline before the next capture. hvactest saves the
   note with the learned code.

Notes are `key=value` pairs separated by spaces; anything after `#` is a
comment. The first capture's note is the baseline (the unit on, with a
mode and a temperature) and gives every key;
later notes give only what changed (keys left out keep the baseline's
value):

    power=on mode=cool temperature=24 fan=auto swing_v=off   # baseline
    temperature=25
    mode=heat
    fan=low
    turbo=on
    power=off

| Key | Values |
|---|---|
| `power` | `on`, `off` |
| `mode` | `auto`, `cool`, `heat`, `dry`, `fan` |
| `temperature` | the number shown, °C; add `F` for a °F display: `75F` |
| `fan`, `swing_v`, `swing_h` | the remote's own words: `low`, `2`, `quiet`, `swing`, ... |
| any extra button | its name on the remote: `turbo=on`, `light=off`, `ionizer=on` |

What to capture, each from the baseline:

- the baseline itself (press any button that leaves it unchanged, or set a
  value and back);
- every mode;
- the setpoint: the lowest, the highest, and several in between, with half
  degrees if the remote has them;
- every fan speed, auto included;
- every swing position, vertical and horizontal;
- each extra button: turbo/powerful, eco, quiet, sleep, display light,
  clean, ionizer, ... (on, from the baseline);
- off (the power button from the baseline);
- a few captures twice, to see what changes between two identical presses
  (some remotes add a toggle bit or a clock).

If Learn reports "nothing learned within 10 s", type nothing new: press
Learn again and repeat the change.

Then check the log:

    python tools/capturekit.py check captures.jsonl

It lists every capture with its note and reports notes it cannot read,
misspelt keys ("tempreature: did you mean temperature?"), and the same code
under two settings (a missed press). Learn those captures again. Then:

    python tools/capturekit.py match captures.jsonl

says whether a pyhvac model already sends every capture (supported: only a
model name to add), a pyhvac protocol decodes them with differences (a
variant), or no pyhvac protocol decodes them (a new protocol).

## Step 3: send it in

If you can, let Claude Code and the `adding-a-unit` skill take it from here
(see [With Claude Code](#with-claude-code)): you end up with a pull request
you have tested on your unit. Otherwise, open an issue on
[pyhvac](https://github.com/frawau/pyhvac/issues) with:

- the brand and model of the unit, and of the remote (on its back or in the
  battery compartment);
- `captures.jsonl` and what `capturekit match` printed;
- anything the remote does that the list above does not cover.

## For protocol authors: from captures to a protocol

portkit reads a list of `{"state": {...}, "pulses": [...]}` records, gzipped
JSON, from a directory. capturekit writes it from the log, each capture's
note as its state:

    python tools/capturekit.py records captures.jsonl captures MYREMOTE

Then:

    python tools/portkit.py timings MYREMOTE --fixtures captures

prints the mark and space clusters, the shape of each burst, and a draft
`Protocol`. Copy the draft into `pyhvac/protocols/<name>.py`, name its
sections, and check that every capture decodes:

    python tools/portkit.py decode MYREMOTE --fixtures captures \
        --protocol pyhvac.protocols.<name>:<PROTOCOL> --expected <section,...>

    python tools/portkit.py diff MYREMOTE --fixtures captures \
        --protocol pyhvac.protocols.<name>:<PROTOCOL> --expected <section,...>

`diff` lists, for each setting, the bits that change between captures that
differ in that setting only, and each value's bit pattern, followed by the
bytes that never change. `checksum` (same arguments) proposes checksums
that fit every frame.

From there, write the `Device` whose `frames()` builds the frames with a
`Layout` (`pyhvac.fields`), register the models in `pyhvac/brands.py`, and
check the result on the unit with hvactest: Send for each setting, and
Compare against the remote's codes.
