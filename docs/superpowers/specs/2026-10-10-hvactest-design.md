# hvactest: send, learn and compare on real units — design

Status: approved in conversation 2026-10-10 (sections 1–2). Branch:
`hvacir`.

## Intent

A development tool to test pyhvac devices — including the variants derived
from SmartIR captures — on real air conditioners through a Broadlink RM,
using the author's `aiobroadlink`.

What the author said:
- Send, learn and compare: send pyhvac's codes to a unit, learn the real
  remote's codes, compare them with pyhvac's for the same state.
- It is a tool (not shipped in the pyhvac package).
- Textual user interface (works over SSH).
- A session log, as a startup option, off by default.
- Discovered Broadlink devices can be named, and the names persist (in
  `~/.pyhvacrc`).

Assumptions (not stated by the author, open to correction):
- The tool lives in `tools/hvactest/`, beside `tools/hvacir/`, and reuses
  the hvacir matcher for decoding and comparison.
- aiobroadlink comes from PyPI (0.1.4) unless the author installs his local
  checkout.

Success criteria:
- From one screen: choose a Broadlink RM, a brand and model, set a state with
  the device's own controls, send it; learn a code from the real remote and
  see whether pyhvac's code for the current state matches it, and which
  fields differ if not; rank all pyhvac models and variants against a
  learned code.
- With `--log FILE`, every send, learn, compare, match and verdict is a JSON
  line with a UTC timestamp; without it nothing is written.
- Everything except the Broadlink I/O is tested without hardware.

## 1. Components

```
tools/hvactest/
  link.py       aiobroadlink wrapper: discover RM devices (or connect to a
                given IP), authenticate, send(packet), learn(timeout) -> packet
  compare.py    learned packet -> pulses -> decoded with the selected device;
                equal to pyhvac's frames for the current state (modulo key
                and toggle fields)? else the differing fields; match():
                every pyhvac model/variant ranked against a learned code
  log.py        optional session log: JSON lines, UTC timestamps
  names.py      Broadlink device names, persisted in ~/.pyhvacrc
  app.py        the Textual app (entry point)
  requirements.txt   textual, aiobroadlink
```

- Device names: `~/.pyhvacrc` is a JSON object; the tool keeps its names
  under the key `"broadlink_names"`, a map from the device's MAC address
  (lower case, colon separated) to the name the author gave it. Discovered
  devices show their name when they have one, else their type, IP and MAC; a
  Rename action names the selected device and writes the file at once
  (other keys in the file are preserved; written atomically). An unreadable
  or malformed file is reported and treated as empty, never overwritten
  without the author renaming something.
- `link.py` is the only module touching the network. `compare.py` is pure
  (no I/O) and reuses `tools/hvacir` (the Broadlink reader, candidate
  decoding, the comparable/difference logic, the candidate list).
- Screen: left — Broadlink device picker, brand and model pickers; centre —
  the selected device's controls built from its capabilities (power, mode,
  setpoint in °C in the device's steps, fan, swing v/h, features); bottom —
  Send, Learn, Compare, Match, a verdict (worked / ignored / wrong setting)
  and a note; right — result pane (sent code, learned code, field
  difference table, match ranking).
- Send: controls -> `HvacState` -> `device.encode(previous, state)` ->
  Broadlink packet -> `link.send`; the last state sent becomes `previous`
  (toggles behave as a real remote's).
- Learn: `link.learn` -> packet -> compared with the current state ->
  shown (and logged).
- Codes may also be pasted as base64 Broadlink packets (offline compare and
  match without a Broadlink).

## 2. Errors, dependencies, testing

Errors (shown in the result pane, logged when on; the app does not crash):
- No Broadlink found: discovery times out after a few seconds; the author
  may enter an IP or work offline.
- Send or learn without an answer: "no answer from <device>"; nothing
  learned within the timeout (10 s): reported as such.
- A learned code the selected device does not decode: "not this protocol",
  with a hint to run Match.
- `encode` raising (should not happen, the controls come from the
  capabilities): the message is shown.

Dependencies and launch:
- `textual` and `aiobroadlink` are tool requirements
  (`tools/hvactest/requirements.txt`), not pyhvac dependencies.
- `python tools/hvactest/app.py [--ip ADDR] [--log FILE]`.
- One asyncio loop: aiobroadlink's UDP endpoint opens at app startup; send
  and learn run as Textual workers, so the UI stays responsive during
  learning.

Units: setpoints are °C as the device offers them; log timestamps are UTC.

Testing (no hardware):
- `compare`: codes pyhvac encodes itself (equal), a tampered code (fields
  named), a foreign code ("not this protocol"), `match` ranking the right
  device first.
- `link`: a fake RM recording sends and returning canned learned packets.
- `log`: round trip; nothing written unless enabled.
- `names`: round trip; other keys preserved; a malformed file is reported
  and not clobbered until a rename.
- `app`: Textual's Pilot drives a model choice (controls appear), Send (the
  fake link receives pyhvac's packet), Learn (difference table shown).

## Out of scope

RF codes; non-climate devices; editing pyhvac protocols from the tool;
shipping the tool in the pyhvac package; Broadlink provisioning (aiobroadlink
already does it).
