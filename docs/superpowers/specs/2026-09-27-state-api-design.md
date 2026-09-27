# State API — design

Date: 2026-09-27
Status: draft, awaiting review
Branch: `state-api` (forked from `ir-section-model`)
Follows: `docs/superpowers/specs/2026-09-26-ir-section-model-design.md`

## Goal

Give pyhvac a stateless device API. The caller holds a plain, serialisable
state and asks a device for the IR command that takes the unit from
`previous` to `target`. It keeps working across restarts: after a Home
Assistant restart, pyhvac no longer guesses the unit's state. The API is the
contract the protocol ports are written against, and the one SmartIR moves
to.

## Context

- Today each device object holds mutable state (`status`, `to_set`,
  `update_status()`). After a restart that state is a guess. Sharp JTech's
  power byte encodes a *transition* (0x11 on, 0x21 off, 0x31 change while
  on). The object starts with `mode: "off"`, so an "off" request after a
  restart matches the stored state and sends 0x31: the unit does not turn
  off.
- Capabilities today are key → list of allowed strings, with inconsistent
  vocabulary across the 99 device classes:
  - fan: `auto/high/medium/low` (44 classes), `highest…lowest` (22),
    `fan1…fan5` (Airspool);
  - swing: `off/on` (42), angle lists (28);
  - hswing: `left/middle/right…`, in either direction.
- 61 of the 99 classes still use the IRremoteESP8266 C library. The new API
  must cover them from day one so SmartIR can move once.
- The SmartIR fork (`VerySmartIRClimate`) uses mode, fan, swing and
  temperature only, and sends `to_broadlink(...).hex()`.

## Decisions

1. **Stateless devices with an immutable state value.** Two alternatives were
   rejected: mutable classes with serialisation (they keep hidden state that
   drifts) and declarative register maps (premature; they may come later as a
   helper inside `frames()` when the first family is ported).
2. **Canonical vocabulary, with optional device labels** for display.
3. **Momentary actions are a separate `actions` argument**, never part of the
   state.
4. **`previous=None` means "unknown".** The device emits frames that reach
   `target` from any state.
5. Temperatures are °C with at most one decimal. A device may restrict the
   allowed decimals.
6. The old API stays untouched and working in this phase. The new API is
   additive.

## State — `pyhvac/state.py`

```python
@dataclass(frozen=True)
class HvacState:
    power: bool
    mode: str                  # "auto" | "cool" | "heat" | "dry" | "fan"
    temperature: float         # setpoint in °C, rounded to 0.1 on construction
    fan: str = "auto"          # "auto" | "1".."N"      (1 = lowest)
    swing_v: str = "off"       # "off" | "swing" | "auto" | "1".."N"  (1 = top)
    swing_h: str = "off"       # "off" | "swing" | "auto" | "1".."N"  (1 = leftmost)
    features: Mapping[str, bool | str] = {}   # stored read-only

    def to_dict(self) -> dict        # JSON-safe
    @classmethod
    def from_dict(cls, data) -> "HvacState"
```

- `power` is separate from `mode`. An "off" state keeps its mode, because
  Sharp's off frame carries it and a later "turn on" restores it.
- Levels and positions are decimal strings, so every choice is a plain string
  and the state JSON-round-trips exactly.
- Canonical feature names: `powerful`, `quiet`, `economy`, `sleep`, `light`,
  `purifier`, `cleaning`, `power_limit`. A device may add others (e.g. `spot`,
  `auto_bias`). On/off features are `bool`; multi-valued features are strings
  (e.g. `economy="80"`).
- Construction validates types: `mode` in the five canonical modes, `fan`/
  `swing_*` either a keyword or a positive decimal string, feature values
  `bool` or `str`. Invalid values raise `ValueError`.
- `from_dict` ignores unknown keys, so states persisted by a newer version
  still load.

## Capabilities — `pyhvac/state.py`

```python
@dataclass(frozen=True)
class TemperatureRange:
    min: float                 # °C, one decimal max
    max: float
    decimals: tuple[int, ...] = (0,)   # allowed tenths, e.g. (0, 5) or (0, 2, 5, 8)

    def snap(self, celsius: float) -> float   # nearest allowed value in [min, max]

@dataclass(frozen=True)
class Choice:
    values: tuple              # canonical values, in order
    labels: Mapping = {}       # value -> display label (optional)

@dataclass(frozen=True)
class Capabilities:
    modes: tuple[str, ...]
    temperature: TemperatureRange
    fan: Choice | None = None
    swing_v: Choice | None = None
    swing_h: Choice | None = None
    features: Mapping[str, Choice] = {}     # bool feature: Choice((False, True))
    actions: Mapping[str, str] = {}         # action name -> label
```

- `TemperatureRange.snap` works in integer tenths of a degree: nearest
  allowed value, ties to the lower value, clamped to `[min, max]`. `min` and
  `max` must themselves be allowed values.
- `decimals` entries are integers 0–9, unique; `(0,)` means whole degrees.

## Device — `pyhvac/device.py`

```python
@dataclass(frozen=True)
class Command:
    signal: Signal             # pyhvac.ir.Signal
    state: HvacState           # normalised target: what the caller persists

class Device:
    brand: str
    model: str
    capabilities: Capabilities
    PROTOCOL: Protocol | None = None

    def normalise(self, state: HvacState) -> HvacState
    def encode(self, previous: HvacState | None, target: HvacState,
               actions: Sequence[str] = ()) -> Command
    def frames(self, previous: HvacState | None, target: HvacState,
               actions: tuple[str, ...]) -> list[Frame]      # protocol-backed devices
```

**`normalise` (base implementation).** Returns a state the device can
express:
- mode not in `modes` → `modes[0]`;
- temperature snapped via `TemperatureRange.snap`;
- fan/swing value not in its `Choice` → the first value; no `Choice` → the
  field's default;
- features the device lacks are dropped; values not in the feature's
  `Choice` → the first value; missing features → the first value.

A device may override `normalise` to add its own rules (e.g. Sharp forces fan
`auto` in dry mode), calling the base implementation first.

**`encode` (base implementation).**
1. Unknown action names raise `ValueError` listing them.
2. Normalise `target`, and `previous` when it is not `None`.
3. `frames = self.frames(previous, target, tuple(actions))`, then
   `signal = pyhvac.ir.encode(self.PROTOCOL, frames)`.
4. Return `Command(signal, normalised_target)`.

Devices hold no state between calls; equal arguments give equal results.

**Behaviour every device follows:**
- `encode` always returns a signal, even when `previous == target` and there
  are no actions (re-sending resyncs a unit changed with its own remote).
- Full-state protocols ignore `previous`.
- Transition protocols use `previous`. With `previous=None` they emit frames
  that reach `target` from any state; if a unit needs a sequence (e.g. "on"
  then "off"), the device emits it in one message.
- Actions apply to this message only and never appear in `Command.state`.

## Legacy adapter — `pyhvac/legacy.py`

`LegacyDevice(cls, brand, model)` wraps any old-style class (C-backed
`IRGHVAC` subclasses and the pure-Python classes not yet rewritten).

**Capabilities mapping.** A pure function
`legacy_capabilities(caps: dict, temperature_step: float) -> Capabilities`,
where `caps` is the old `capabilities | xtra_capabilities`:
- `mode`: `"off"` is dropped (it becomes `power`); the others map 1:1.
- `temperature`: old `[min, max]` or the full list → `TemperatureRange(min,
  max, decimals)`, where `decimals` is `(0, 5)` if `temperature_step` is 0.5,
  otherwise `(0,)`.
- `fan`: `auto` stays `auto`. The other names are ranked
  `lowest < low < medium < high < highest` and become `"1".."N"` in that
  order, with the old names as labels.
- `swing` → `swing_v`, and `hswing` → `swing_h`:
  - `off` → `off`;
  - `on` and `swing` → `swing`;
  - `auto` → `auto`;
  - every other value becomes a position `"1".."N`", labelled with the old
    name. For `swing_v` positions keep the device's list order. For `swing_h`
    they are ordered left to right by the ranking `far left < left <
    close left < middle < close right < right < far right`. Words outside
    that ranking (e.g. `wide`) follow in list order.
- Every other key → a feature. Old `off/on` lists become bool
  `Choice((False, True))`. Other lists stay strings, e.g. `economy`:
  `off/80/60/40`.
- A fan or swing word outside the known vocabulary raises `ValueError` at
  construction, so nothing is silently misordered.

**Encode.**
- Translate the normalised target back to the old keys: `mode = "off"` when
  `power` is false, levels and positions back to their old names, bools back
  to `"on"/"off"`.
- Create a fresh instance and set `to_set` directly. Setters are bypassed:
  on the `ir-section-model` line, `IRGHVAC.set_fan` still has the pre-0.1.8
  bug.
- Build with the old path. C-backed classes give pulses. Pure-Python classes
  give frames, which go through the old `to_lirc`.
- Return `Signal(38000, pulses)`, appending a 100 000 µs trailer if the
  pulses end on a mark. `previous` is ignored, as it is today.

## Registry — `pyhvac/registry.py`

```python
brands() -> list[str]                        # plugin module names, sorted
models(brand: str) -> list[str]
get_device(brand: str, model: str | None = None) -> Device   # None -> "generic"
```

- Brands are the plugin module names under `pyhvac/plugins` (excluding
  `hvaclib`). Modules are imported lazily, per brand, on first use.
- A module may define `DEVICES = {model: DeviceClass}`. Those models use the
  new class; the remaining models in `PluginObject.MODELS` are wrapped in
  `LegacyDevice`. `models()` lists both.
- A module that fails to import (typically missing the C extension) is
  logged at WARNING and treated as having no models. `get_device` on an
  unknown brand or model raises `KeyError`.

## Reference devices

### Airspool — `pyhvac/plugins/airspool.py`, `DEVICES`

- Capabilities:
  - modes `cool`, `dry`, `heat`;
  - temperature 16.0–30.0 °C with `decimals=(0, 5)`, converted to the
    nearest °F and BCD-encoded as today;
  - fan `auto` + `"1".."5"` (labels `fan1`…`fan5`);
  - `swing_v` `off`/`swing`; `swing_h` `off`/`swing`;
  - features `sleep`, `powerful` (was `turbo`), `light` (was `display`,
    default True), `power_limit` (was `se`);
  - action `se_step`.
- `frames()` builds the same 14-byte frame the old class builds, from the
  state alone. `power` maps to byte 5 bit 0x04.
- `se_step` sets byte 6 bit 0x40 in this message only.
- Full-state protocol: `previous` is ignored.

### Sharp JTech — `pyhvac/plugins/sharp.py`, `DEVICES["j-tech"]`

- Capabilities from the old JTech lists:
  - modes `auto`, `cool`, `dry`;
  - temperature 14.0–29.0 °C with `decimals=(0, 5)`;
  - fan `auto` + `"1".."4"` (lowest…highest);
  - `swing_v` `auto`/`swing` + 5 positions (`ceiling`, `90°`, `60°`,
    `45°`, `30°`);
  - `swing_h` `swing` + 3 positions (left, middle, right);
  - features `purifier`, `powerful`, `economy`, and `spot` (the old
    `target` values).
- Byte 5 (power transition) is derived from `previous` and `target`:

  | previous | target | byte 5 |
  |---|---|---|
  | power off | power on | 0x11 |
  | power on | power on | 0x31 |
  | any | power off | 0x21 |
  | `None` | power on | 0x11 |
  | `None` | power off | 0x21 |

  The off frame carries the target's mode (previously the last mode).
- `powerful`/`economy` are sent as the extra frame only when they differ
  from `previous` (or when `previous` is `None`) and power is on, as the old
  class does.
- `normalise` keeps the old fan rule (fan `auto` in dry mode). As in the old
  class, the setpoint is only encoded in cool mode; the state keeps its
  temperature in every mode.

## Testing

- **State/capabilities:**
  - temperature rounding to 0.1;
  - `snap` with `(0,)`, `(0, 5)` and `(0, 2, 5, 8)`, including clamping and
    ties;
  - `to_dict`/`from_dict` round trip, and unknown keys ignored;
  - validation errors; features are read-only.
- **`normalise`:** each rule above, on a small in-test device.
- **`encode`:** unknown action → `ValueError`; `Command.state` is the
  normalised target; equal inputs give equal outputs.
- **`legacy_capabilities`:** tested on plain dicts, covering:
  - the fan ranking;
  - swing keywords, positions and labels;
  - the `swing_h` left-to-right ordering, and `wide`;
  - bool vs string features;
  - an unknown word raising `ValueError`.
- **`LegacyDevice`** against the oracle fixtures: each record's old state is
  translated to an `HvacState`, encoded, and must equal the recorded pulses.
  These tests skip when the C extension is absent.
- **Airspool device:**
  - reproduces every golden record, and the reference frames in
    `tests/test_airspool.py`;
  - `se_step` appears in the frame and not in `Command.state`.
- **Sharp JTech device:**
  - reproduces every golden record except those whose old state was mode
    `off` (the 0x31 bug, changed on purpose);
  - the transition table above as explicit tests, including
    `previous=None` + power off → 0x21.
- **Registry:**
  - pure-Python brands load without the C extension;
  - with it, every brand/model returns a `Device` whose capabilities map
    without error.

## Out of scope

- SmartIR changes. They are in the SmartIR repo; the contract is
  `get_device`, persisting `command.state.to_dict()`, restoring through
  `RestoreEntity`, `None` when nothing is restored, and sending
  `to_broadlink(command.signal)`.
- Family ports: moving models from `MODELS` to `DEVICES`.
- Per-mode temperature ranges, measured room values, and °F display (an edge
  concern).
- Removing the old API and the C build (0.2.0).
