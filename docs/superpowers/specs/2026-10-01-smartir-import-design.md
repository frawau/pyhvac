# SmartIR climate codes: import, match, port — design

Status: approved in conversation 2026-10-01 (sections 1–4). Branch:
`smartir`, forked from `phase4`.

## Intent

SmartIR lets people use A/C codes uploaded by others: "dumb" captures of a
remote, one per state, which need many codes to be useful. pyhvac should
cover those units with real devices: for each upstream SmartIR climate code
file, find out whether pyhvac already generates the same codes (then offer
the file's brand/model as an alias), whether pyhvac lacks something it can
gain (a variant, a fan level, °F encoding, a feature), whether the file is
a protocol pyhvac can port from the captures, or, as a last resort, serve
it from the file itself.

What the author said:
- Use the upstream SmartIR codes (github.com/smartHomeHub/SmartIR,
  `codes/climate/`).
- When temperatures differ, check whether the cause is Fahrenheit vs
  Celsius (either way). pyhvac uses metric only, but must adapt to cover
  every value a unit accepts.
- New devices: real ports where possible; otherwise devices that use the
  data files fetched from the web. The unknown/undecoded files are not kept
  in this repo.
- Table devices follow upstream `master` (upstream is responsible for the
  codes); no pinning.
- Matcher: inference plus an encode check (approach 3).

Assumptions (not stated by the author, open to correction):
- HVAC (`codes/climate`) only; fans, lights and media players are out.
- The importer is a development tool (`tools/smartir/`), not shipped in the
  wheel; its outputs (report, `brands.py` rows, port worklist) are what gets
  committed, after the author reviews them.

Success criteria:
- Every upstream climate file has a verdict: covered, near, ported (after a
  port lands: covered), or table.
- A covered file's every usable code is reproduced byte for byte by
  `device.encode(None, state)` under the reported mapping.
- No SmartIR file is committed to this repo; fixtures for new ports hold
  only decoded frames and states.
- `HvacState.temperature` stays °C everywhere; °F units are reachable
  through °C setpoints.

Baseline (throwaway probe on the 356 files, before this work): 230 files
decode with a pyhvac protocol, 29 already reproduce well with a naive
mapping, 67 use an unknown protocol, 60 hit parsing problems.

## 1. Components and data flow

```
tools/smartir/                 dev tool, not shipped in the wheel
  fetch.py      upstream climate files -> local cache (never committed)
  codes.py      a file's commands -> (state key, pulses): Broadlink base64,
                raw µs lists, Xiaomi and ESPHome raw forms; bad codes
                skipped and counted
  match.py      decode with candidate protocols, infer the mapping from
                layout fields, verify by encoding
  cluster.py    unknown files -> portkit timing/length clusters
  report.py     per-file verdicts, proposed brands.py rows, port worklist
pyhvac/
  brands.py           + rows for covered files (and table rows)
  protocols/table.py  TableDevice: serves a SmartIR file fetched at runtime
  state.py            + a °F-stepped temperature range (still °C)
```

Flow: `fetch` caches the files; `match` gives each a verdict:
- covered: one consistent mapping and pyhvac's encode reproduces every
  usable code byte for byte -> a `brands.py` row;
- near: the mapping is consistent but pyhvac lacks something -> a gap to
  fix in the protocol module, then re-run;
- unknown -> `cluster`.
Clusters rich enough become port tasks; files left over become
`TableDevice` rows. The report and proposed rows are committed after the
author's review; SmartIR files never are.

Matched features need no "fixed setting" mechanism: a file captured with
the light on is covered by a device that offers `light`; the report records
the state that reproduces each code.

## 2. Temperatures: metric only, covering °F units

- `HvacState.temperature` is always °C; Fahrenheit lives only inside an
  encoder and at the edge.
- `TemperatureRange.fahrenheit(lo_f, hi_f)`: one °C setpoint per whole °F,
  `round((F - 32) * 5 / 9, 1)`; `snap(c)` picks the nearest offered value;
  devices convert back with `round(c * 9 / 5 + 32)`. The round trip is
  exact (offered values are ≥ 0.5 °C apart; rounding is 0.1 °C); a test pins
  it for 0–120 °F. Half-degree files keep the existing `decimals`.
- Protocols with a °F mode (Fahrenheit flag or °F setpoint encoding:
  Gree, Midea, Daikin, Electra, Haier, Whirlpool, Argo, ... as their
  headers document) gain a `units` option ("C"/"F", like `variant`) where
  the importer proves a file's unit uses it; with "F" the capabilities use
  the °F-stepped range and the encoder writes the °F flag and value. The
  `brands.py` row carries `units`.
- Matcher hypotheses for the setpoint field, in order: keys °C encoded °C;
  keys °F encoded °F; keys °F with the unit encoding °C (converted,
  rounded or truncated); keys °C with the unit encoding °F. The first that
  explains every code wins; the report says which.
- TableDevice: °F keys give a °F-stepped range (a °C request goes to the
  nearest °F key); °C files use their min/max/precision.

## 3. The matcher

1. Parse: walk `off` and mode -> fan -> [swing] -> temperature; codes to
   pulses (Broadlink base64, raw µs lists, Xiaomi, ESPHome; LOOKin if
   trivial). Bad codes skipped and counted; a file below 90 % usable codes
   is flagged.
2. Candidates: decode every code with each pyhvac protocol and its section
   sequences; learned captures may hold the message twice or a trailing
   repeat, so the decoder may drop a repeated tail. A protocol is a
   candidate if ≥ 90 % of the codes decode.
3. Infer: read every decoded code's fields through the device layouts
   (incl. `Joined`) and require: mode field a function of the mode key
   (`off` via power field / off message); setpoint field following the
   temperature keys under one units hypothesis; fan and swing fields
   functions of their keys; every other field constant, or varying only
   in ways the Device's own rules explain (checked in step 4); toggle
   fields consistent with a fresh device or one previous state. Output: a
   mapping (variant, units, fan labels -> canonical values, swing labels,
   features set throughout).
4. Verify (the gate): build each code's `HvacState` from the mapping;
   `device.encode(None, state)` must equal every code's decoded frames
   byte for byte -> covered.
5. Near: step 3 holds but step 4 fails on a minority of codes, or a field
   value has no pyhvac equivalent (unknown fan code, °F flag the Device
   cannot set, unknown variant byte) -> report the field, values and codes.
6. Unknown: no consistent candidate -> clustering.

Per-file record: verdict, candidate, mapping, units hypothesis,
usable/decoded/verified counts, gap if near. The tool is deterministic and
re-runnable: after each port or gap fix, files move to covered.

## 4. Unknown files, new ports, the table fallback

- Clustering: portkit's role-separated timing clusters plus frame-length
  signatures group unknown files sharing a protocol; per cluster: files,
  codes, distinct states, and how many fields `portkit diff` can isolate.
- Ports: a cluster with enough single-key pairs to locate mode, setpoint
  and fan, and a checksum `portkit checksum` explains, becomes a port task
  (same pipeline as the singleton ports; captures are the only evidence; a
  field no capture exercises is left out, not invented). After a port
  lands, its files re-run through the matcher. Port test fixtures hold
  only the decoded frames and states the tests need.
- Table fallback: each remaining file becomes a `TableDevice` row (brand
  and model as the file spells them, the upstream file number). The device
  fetches `https://raw.githubusercontent.com/smartHomeHub/SmartIR/master/codes/climate/<n>.json`
  on first use, caches it in a user cache directory (overridable; a local
  file may be given for offline use), derives capabilities from the file
  (modes, fan labels, swing labels, temperatures °C / °F-stepped / half
  degrees), and encodes by looking up the state's code and decoding it to
  pulses. A state with no code raises an error naming it; it never
  guesses. A fetch failure raises an error naming the URL; a cached copy is
  used if present. `previous` is ignored.
- Names: covered and table rows use the file's `manufacturer` and
  `supportedModels`, normalised like the rest of `brands.py`; when the name
  already exists, the row is skipped if it is the same device, otherwise
  reported as a conflict for the author.
- Testing: matcher inference and gate unit-tested on synthetic files built
  from pyhvac's own encoders (incl. a °F file and a variant file);
  TableDevice tested with a small hand-written JSON fixture and a fetch
  seam the tests replace; one optional network test (marked, skipped by
  default) fetches a real upstream file.

## Out of scope

Non-climate SmartIR codes; SmartIR integration changes; pinning or
verifying upstream files; codes for controllers whose format cannot be
turned into pulses.
