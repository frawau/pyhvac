# LG, Panasonic, Sanyo, Kelon and Trotec Ports (the pairs) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the C path for the paired protocols with pure-Python `Device`s:
- LG and LG2 (`lg.py`, plus the GE-branded LG models in `ge.py`);
- PANASONIC_AC and PANASONIC_AC32 (`panasonic.py`);
- SANYO_AC and SANYO_AC88 (`sanyo.py`);
- KELON (`kelon.py`);
- TROTEC and TROTEC_3550 (`trotech.py`).

**Architecture:** Same as the earlier family plans. One device class per protocol is registered through each module's new `DEVICES` dict. Each port is written from `ir_*.h` and verified against every oracle record (only declared defects) and against the real C path, including persistent-object sequences for every protocol with toggle or previous-state rules. The TROTEC fixtures did not exist: the released 0.1.7 had the protocol-name typo. They are generated here from the fixed C path.

**Tech Stack:** Python ≥ 3.9 standard library, pytest, black. The port kit on branch `ports`.

**Spec:** `docs/superpowers/specs/2026-09-27-port-kit-design.md`. House rules: the Rulings sections of the Daikin, Hitachi, Mitsubishi and Haier plans.

## Global Constraints

- Work on branch `ports`.
- Durations are integer µs, the carrier is in Hz, and temperatures are °C.
- Python ≥ 3.9, and no new runtime dependencies.
- Layouts come from the headers (facts).
- Capabilities equal the legacy entity (C-only test in each file).
- A difference from the C output is allowed only as a declared `Defect`, or as a documented previous-state deviation.
- The old API and all existing tests stay green. Run `black` on every modified file.
- Tests: `python -m pytest -q`. The C-extension run is described in Task 10.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **Toggle and previous-state protocols:** LG (swing-toggle word), LG2 (extra words per variant), PANASONIC_AC CKP and PANASONIC_AC32 (power toggles), KELON (power toggle). With `previous=None` each does what a fresh C object does, and with `previous` each follows C's own rule. The two exceptions:
   - LG2 AKB73757604's swing_h word is sent only when it changes, because C's `_swingh_prev` is stale memory (house rule 3a).
   - The KELON off message carries the target mode.
2. **KELON:** C sent *heat* on every message (`setSupercool(false)` restores the reset mode). The port sends the requested mode. Off messages also differ from C in setpoint.
3. **PANASONIC_AC DKE:** C set Ion on every message (`IRac::sendAc` passes clock −1 into `filter`) and never sent the purifier. The port sends the purifier value.
4. **SANYO_AC88:** the old path ended each message with a 100 ms IR *mark* (C's log records two consecutive gaps). The port sends the gap.
5. **Advertised controls that send nothing, matching C:** LG2 AKB75215403 swing/swing_h/light, and LG2 AKB74955603 swing_h.

## Rulings made while planning

- **Swing "1"/"2" (90°/60°):** Highest/High, as in the Mitsubishi ruling (LG2, PANASONIC_AC, PANASONIC_AC32, SANYO_AC); other positions follow C.
- **Sleep, swing "on" and swing_h "on"** are sent where the entity has them; the oracle fixtures predate `main`'s glue fixes.
- **KELON off message:** carries the target mode and its setpoint rule, not smart (which may switch the unit on), and not C's heat at 26 °C.
- **LG2 AKB73757604 swing_h word:** with `previous`, sent only when swing_h changes (C's `_swingh_prev` is never written). With `previous=None`, sent, as fresh C and the vane words do.
- **LG2 AKB74955603 light toggle:** sent on every command with light off, as C does. Every state word turns the light on (issue 1513), so this is correct and not a toggle bug.
- **PANASONIC_AC32 auto = 6** (header and C). One real capture labelled "auto" shows 5; this is open for hardware confirmation.
- **The GE models** (`ge.py`: "AG1BH09AW101", "6711AR2853M Remote") are served by `LgAcDevice` with the GE6711AR2853M variant.
- **Not ported:** KELON168 and PanasonicLke are in no `MODELS` entry. The four Midea models listed in `trotech.py` belong to the Midea singleton.

---

### Task 1: Imports and DEVICES in lg, panasonic, sanyo, kelon and trotech

**Files:**
- Modify: `pyhvac/plugins/lg.py`, `panasonic.py`, `sanyo.py`, `kelon.py`, `trotech.py`
- Test: `tests/test_pairs_family.py`

- [ ] **Step 1: Write the failing test**: create `tests/test_pairs_family.py`:

```python
"""The paired-protocol modules serve their C-backed models with ported devices."""

import importlib

import pytest

MODULES = ("lg", "panasonic", "sanyo", "kelon", "trotech")


@pytest.mark.parametrize("name", MODULES)
def test_module_has_a_devices_table(name):
    module = importlib.import_module(f"pyhvac.plugins.{name}")
    assert isinstance(module.DEVICES, dict)
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `python -m pytest tests/test_pairs_family.py -q`
Expected: 5 failed, `AttributeError: ... has no attribute 'DEVICES'`.

- [ ] **Step 3: Implement.** For each module, replace the import section (from its first `import`/`from` line up to the line before its first `class`) with the text below. Then insert `DEVICES = {}` (followed by two blank lines) immediately before the `# Now the match between models and objects` comment, or before `class PluginObject(GenPluginObject):` where there is no such comment (`lg.py`, `panasonic.py`).

`pyhvac/plugins/lg.py`:

```python
import struct
from dataclasses import dataclass

from .hvaclib import HVAC, PulseBased, GenPluginObject
from ..device import Device
from ..fields import Checksum, Field, Layout
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import Capabilities, Choice, TemperatureRange

try:
    from ..irhvac import (
        GE6711AR2853M,
        LG6711A20083V,
        AKB75215403,
        AKB74955603,
        AKB73757604,
    )
except ImportError:
    # Only the C-backed classes use these; keep the pure-Python ones importable.
    GE6711AR2853M = LG6711A20083V = AKB75215403 = AKB74955603 = AKB73757604 = None


# Frames are 4 bytes (32 bits) on the wire, as the legacy emitter sent them.
LG_NATIVE = Protocol(
    "lg-native",
    {
        "main": Section(
            PulseDistance(520, 520, 1530),
            header=(3100, 9850),
            footer=(520,),
            gap=12000,
            lsb_first=False,
        )
    },
)
```

`pyhvac/plugins/panasonic.py`:

```python
import struct

from dataclasses import dataclass
from .hvaclib import HVAC, PulseBased, GenPluginObject, bit_reverse
from ..device import Device
from ..fields import Field, Layout, Sum8
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import Capabilities, Choice, TemperatureRange

try:
    from ..irhvac import (
        kPanasonicLke,
        kPanasonicCkp,
        kPanasonicDke,
        kPanasonicJke,
        kPanasonicNke,
        kPanasonicRkr,
    )
except ImportError:
    # Only the C-backed classes use these; keep the pure-Python ones importable.
    kPanasonicLke = kPanasonicCkp = kPanasonicDke = None
    kPanasonicJke = kPanasonicNke = kPanasonicRkr = None


PANASONIC_NATIVE = Protocol(
    "panasonic-native",
    {
        "main": Section(
            PulseDistance(435, 435, 1300),
            header=(3500, 1750),
            footer=(435,),
            gap=10000,
            lsb_first=False,
        )
    },
)
```

`pyhvac/plugins/sanyo.py`:

```python
from .hvaclib import PulseBased, GenPluginObject
from ..device import Device
from ..fields import Field, Layout, NibbleSum
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import Capabilities, Choice, TemperatureRange
```

`pyhvac/plugins/kelon.py`:

```python
from .hvaclib import PulseBased, GenPluginObject
from ..device import Device
from ..fields import Field, Layout
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import Capabilities, Choice, TemperatureRange
```

`pyhvac/plugins/trotech.py`:

```python
from .hvaclib import PulseBased, GenPluginObject
from .midea import Midea
from ..device import Device
from ..fields import Field, Layout, Sum8
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import Capabilities, Choice, TemperatureRange
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/lg.py pyhvac/plugins/panasonic.py pyhvac/plugins/sanyo.py pyhvac/plugins/kelon.py pyhvac/plugins/trotech.py tests/test_pairs_family.py
git add pyhvac/plugins/lg.py pyhvac/plugins/panasonic.py pyhvac/plugins/sanyo.py pyhvac/plugins/kelon.py pyhvac/plugins/trotech.py tests/test_pairs_family.py
git commit -m "Pairs: DEVICES tables and imports for the ports

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 2: LG (LGv2 + GE variant)

28-bit LG words; the state word, or the off command; a swing-toggle word when swing changes (C's own rule in IRac::lg). Variants LG6711A20083V (lg) and GE6711AR2853M (ge.py's models). Local nibble `LgAcChecksum`.

**Files:**
- Modify: `pyhvac/plugins/lg.py` (block before `class PluginObject(GenPluginObject):`) and `pyhvac/plugins/ge.py`
- Test: `tests/test_lg_ac_device.py`

- [ ] **Step 1: Write the failing tests**: create `tests/test_lg_ac_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.ir.codec import decode
from pyhvac.plugins.lg import (
    LG_AC,
    LG_AC_GE_MODELS,
    LG_AC_LAYOUT,
    LG_AC_MODEL_VARIANT,
    LG_AC_MODELS,
    LG_AC_OFF_COMMAND,
    LG_AC_SWINGV_TOGGLE,
    LgAcDevice,
    lg_ac_word,
)
from pyhvac.state import HvacState

# The C path deviates from the documented LG6711A20083V behaviour here:
# - the old glue (IRGHVAC.trans_swing) has no "on" entry, so IRac keeps
#   swingv kOff, IRac::lg sees no off -> not-off change, and IRLgAc::send
#   sends no kLgAcSwingVToggle word. The port sends the documented toggle
#   word after the state word. The defect is a whole extra word, not a
#   field, so it is checked by assert_matches below rather than by a layout
#   field diff.
SWING_TOGGLE = Defect(
    "swing_toggle_word", "sent", "absent", "C glue has no 'on' swing: no toggle"
)
DEFECTS = (SWING_TOGGLE,)

TOGGLE = lg_ac_word(LG_AC_SWINGV_TOGGLE)
OFF = lg_ac_word(LG_AC_OFF_COMMAND)
MODEL = "6711A20083V  remote"
GE_MODEL = "AG1BH09AW101"
ALL_MODELS = LG_AC_MODELS + LG_AC_GE_MODELS
LEGACY = {"LG6711A20083V": ("lg", "LGv2"), "GE6711AR2853M": ("ge", "LGv1")}


def device(model=MODEL):
    return LgAcDevice("lg", model)


def words(state, previous=None, model=MODEL):
    dev = device(model)
    if previous is not None:
        previous = dev.normalise(previous)
    return [f.data for f in dev.frames(previous, dev.normalise(state), ())]


def read(state, previous=None):
    return LG_AC_LAYOUT.read(words(state, previous)[0])


class _StateWordOnly:
    """The device, minus the trailing swing toggle word."""

    def __init__(self, dev):
        self.dev = dev
        self.PROTOCOL = dev.PROTOCOL
        self.capabilities = dev.capabilities

    def normalise(self, state):
        return self.dev.normalise(state)

    def frames(self, previous, target, actions):
        return self.dev.frames(previous, target, actions)[:1]


def assert_matches(dev, record, defects=DEFECTS):
    """assert_matches_oracle, with the swing toggle word accepted only when
    its Defect is declared (and only as exactly kLgAcSwingVToggle)."""
    ours = dev.frames(None, state_from_record(dev, record["state"]), ())
    if len(ours) > 1:
        assert [f.data for f in ours[1:]] == [TOGGLE], record["state"]
        declared = {(d.field, d.ours, d.theirs) for d in defects}
        assert (
            SWING_TOGGLE.field,
            SWING_TOGGLE.ours,
            SWING_TOGGLE.theirs,
        ) in declared, f"undeclared swing toggle word for {record['state']}"
        dev = _StateWordOnly(dev)
    assert_matches_oracle(dev, record, (LG_AC_LAYOUT,), defects)


@pytest.mark.parametrize("record", oracle_params("LG"))
def test_matches_c_library(record):
    assert_matches(device(record["model"]), record)


def test_oracle_covers_both_variants():
    seen = {(r["plugin"], r["model"], r["class"]) for r in load_oracle("LG")}
    assert seen == {("lg", MODEL, "LGv2"), ("ge", GE_MODEL, "LGv1")}
    assert {LG_AC_MODEL_VARIANT[m] for _, m, _ in seen} == set(LEGACY)


@pytest.mark.parametrize("swing", ["off", "auto", "1", "2", "3", "4", "5"])
def test_ge_sends_no_swing_word(swing):
    # IRLgAc::send: GE6711AR2853M falls in the default case, no swing word,
    # with or without a previous state.
    target = HvacState(True, "cool", 22.0, swing_v=swing)
    plain = HvacState(True, "cool", 22.0)
    assert words(target, model=GE_MODEL) == words(plain, model=GE_MODEL)
    for before in ("off", "auto", "3"):
        previous = HvacState(True, "cool", 22.0, swing_v=before)
        assert len(words(target, previous, model=GE_MODEL)) == 1


@pytest.mark.parametrize("mode", ["auto", "cool", "fan", "dry", "heat"])
@pytest.mark.parametrize("fan", ["auto", "1", "2", "3", "4"])
def test_variants_share_the_state_word(mode, fan):
    state = HvacState(True, mode, 21.0, fan=fan)
    assert words(state, model=GE_MODEL) == words(state)
    off = HvacState(False, mode, 21.0, fan=fan)
    assert words(off, model=GE_MODEL) == words(off) == [OFF]


def test_layout_round_trips_every_oracle_state():
    for record in load_oracle("LG"):
        dev = device(record["model"])
        state = state_from_record(dev, record["state"])
        for word in dev.frames(None, state, ()):
            values = LG_AC_LAYOUT.read(word.data)
            assert LG_AC_LAYOUT.build(**values) == bytearray(word.data)


def test_every_oracle_word_has_the_nibble_checksum():
    for record in load_oracle("LG"):
        (word,) = decode(LG_AC, record["pulses"], expected=["main"])
        assert word.nbits == 28
        assert LG_AC_LAYOUT.checksum.check(word.data)
        assert word.data[3] & 0x0F == 0  # the 4 bits below the word


def test_checksum_nibble_overlaps_no_field():
    # Sum is raw bits 0-3: the top nibble of byte 3. Nothing else lives in
    # byte 3 (its low nibble is not sent).
    checksum = LG_AC_LAYOUT.checksum
    assert checksum.positions() == {3}
    for name, f in LG_AC_LAYOUT.fields.items():
        assert not {b // 8 for b in f.bits} & {3}, name
    covered = {b for f in LG_AC_LAYOUT.fields.values() for b in f.bits}
    assert covered == set(range(24))  # every other sent bit is a field


@pytest.mark.parametrize("raw, total", [(0x88C0051, 0x1), (0x88C0354, 0x4)])
def test_checksum_known_values(raw, total):
    # TestIRLgAcClass.calcChecksum.
    data = bytearray(lg_ac_word(raw))
    assert LG_AC_LAYOUT.checksum.compute(data) == total
    data[3] = 0
    LG_AC_LAYOUT.checksum.apply(data)
    assert data[3] >> 4 == total


@pytest.mark.parametrize("mode", ["auto", "cool", "fan", "dry", "heat"])
@pytest.mark.parametrize("temp", [16.0, 20.0, 25.0])
@pytest.mark.parametrize("swing", ["off", "swing"])
def test_off_is_the_off_command_in_every_mode(mode, temp, swing):
    # IRLgAc::send: power off always sends kLgAcOffCommand alone, whatever
    # the mode, setpoint, fan, swing or light.
    state = HvacState(
        False,
        mode,
        temp,
        fan="4",
        swing_v=swing,
        swing_h=swing,
        features={"light": True},
    )
    assert words(state) == [OFF]
    assert words(state, previous=HvacState(True, mode, temp)) == [OFF]


def test_off_command_is_the_struct_with_power_off():
    values = LG_AC_LAYOUT.read(OFF)
    assert values == {
        "sign": 0x88,
        "power": "off",
        "unused": 0,
        "mode": "cool",
        "temp": 0,
        "fan": "auto",
    }
    assert LG_AC_LAYOUT.checksum.check(OFF)


@pytest.mark.parametrize("temp", range(16, 26))
def test_every_setpoint(temp):
    # setTemp: Temp = celsius - kLgAcTempAdjust.
    values = read(HvacState(True, "cool", float(temp)))
    assert (values["temp"], values["power"], values["sign"]) == (temp - 15, "on", 0x88)


def test_setpoint_is_clamped_to_the_entity_range():
    # The legacy entity offers 16-25 °C (C itself would clamp to 16-30).
    assert read(HvacState(True, "cool", 10.0))["temp"] == 1
    assert read(HvacState(True, "heat", 35.0))["temp"] == 10


@pytest.mark.parametrize(
    "mode, raw", [("cool", 0), ("dry", 1), ("fan", 2), ("auto", 3), ("heat", 4)]
)
def test_every_mode(mode, raw):
    assert LG_AC_LAYOUT.read_raw(words(HvacState(True, mode, 22.0))[0], "mode") == raw


@pytest.mark.parametrize(
    "fan, raw",
    # high: convertFan's kLgAcFanHigh, which setFan stores as kLgAcFanMax
    # on LG6711A20083V (only AKB74955603 keeps kLgAcFanHigh).
    [("auto", 5), ("1", 0), ("2", 1), ("3", 2), ("4", 4)],
)
@pytest.mark.parametrize("mode", ["auto", "cool", "fan", "dry", "heat"])
def test_every_fan_level(mode, fan, raw):
    data = words(HvacState(True, mode, 22.0, fan=fan))[0]
    assert LG_AC_LAYOUT.read_raw(data, "fan") == raw


def test_light_and_swing_h_send_nothing():
    # IRLgAc::send sends the light toggle for AKB74955603 and SwingH words
    # for AKB73757604 only.
    base = HvacState(True, "cool", 22.0)
    for swing_h in ("off", "swing"):
        for light in (False, True):
            state = HvacState(
                True, "cool", 22.0, swing_h=swing_h, features={"light": light}
            )
            assert words(state) == words(base)


def test_swing_without_previous_sends_the_toggle_word():
    # A fresh IRac: sendAc's prev_swingv is kOff, so IRac::lg sends
    # kLgAcSwingVToggle when the target swing is on.
    on = words(HvacState(True, "cool", 22.0, swing_v="swing"))
    off = words(HvacState(True, "cool", 22.0))
    assert on == off + [TOGGLE]
    assert len(off) == 1


@pytest.mark.parametrize(
    "before, after, toggle",
    [
        ("off", "off", False),
        ("off", "swing", True),
        ("swing", "off", True),
        ("swing", "swing", False),
    ],
)
@pytest.mark.parametrize("was_on", [True, False])
def test_swing_with_previous_toggles_on_change(before, after, toggle, was_on):
    # IRac::lg: toggle when (swingv == kOff) != (swingv_prev == kOff); the
    # previous swing counts even if the previous message was an off.
    previous = HvacState(was_on, "cool", 22.0, swing_v=before)
    target = HvacState(True, "heat", 23.0, swing_v=after)
    sent = words(target, previous)
    assert sent[1:] == ([TOGGLE] if toggle else [])


def test_toggle_word_reads_through_the_layout():
    values = LG_AC_LAYOUT.read(TOGGLE)
    assert (values["sign"], values["unused"], values["power"]) == (0x88, 0b010, "on")
    assert LG_AC_LAYOUT.checksum.check(TOGGLE)


def test_previous_is_ignored_except_for_the_swing():
    dev = device()
    target = HvacState(True, "cool", 22.0, fan="2", swing_v="swing")
    for previous in (
        HvacState(False, "heat", 25.0, swing_v="swing"),
        HvacState(True, "dry", 16.0, fan="4", swing_v="swing"),
        target,
    ):
        assert dev.encode(previous, target).signal == dev.encode(target, target).signal


@pytest.mark.parametrize(
    "raw, mode, temp, fan",
    [
        (0x8800347, "cool", 18, "4"),  # issue 1008
        (0x8800459, "cool", 19, "auto"),  # issue 1008
        (0x8800A4E, "cool", 25, "4"),  # MessageConstruction
    ],
)
def test_known_examples(raw, mode, temp, fan):
    # TestIRLgAcClass: the words the port sends for these states.
    assert words(HvacState(True, mode, float(temp), fan=fan)) == [lg_ac_word(raw)]


@pytest.mark.parametrize(
    "raw, mode, temp, fan",
    [
        (0x880C152, "heat", 16, "auto"),
        (0x8808855, "cool", 23, "auto"),
        (0x880870F, "cool", 22, "1"),
        (0x8808721, "cool", 22, "3"),
        (0x8808743, "cool", 22, "4"),
        (0x8808754, "cool", 22, "auto"),
        (0x880A745, "fan", 22, "4"),
        (0x8808440, "cool", 19, "4"),
        (0x880960F, "dry", 21, "1"),
        (0x880C758, "heat", 22, "auto"),
        (0x8809946, "dry", 24, "4"),
        (0x880A341, "fan", 18, "4"),
    ],
)
def test_real_captures_except_the_unnamed_bit_15(raw, mode, temp, fan):
    # TestIRLgAcClass.KnownExamples (issue 1008 captures): the real remote
    # also sets raw bit 15, one of the struct's unnamed bits (the header
    # names no meaning for it). IRLgAc never sets it; neither does the port.
    (ours,) = words(HvacState(True, mode, float(temp), fan=fan))
    assert LG_AC_LAYOUT.read(ours)["unused"] == 0
    capture = bytearray(ours)
    LG_AC_LAYOUT.write_raw(capture, "unused", 0b001)
    LG_AC_LAYOUT.checksum.apply(capture)
    assert bytes(capture) == lg_ac_word(raw)


def test_real_capture_decodes():
    # TestDecodeLG.Issue620: a real remote's 0x8808721 (cool, 22 °C, fan
    # medium, bit 15 set) decodes with the port's timings.
    raw = (
        "8886 4152 560 1538 532 502 532 504 530 484 558 1536 508 516 558 502 "
        "532 484 558 502 532 500 534 508 532 502 532 1518 558 510 532 484 556 "
        "486 556 510 532 1518 558 1560 532 1528 556 504 530 506 530 1520 558 "
        "508 534 500 532 512 530 484 556 1536 532"
    )
    pulses = [int(x) for x in raw.split()] + [108050]
    (word,) = decode(LG_AC, pulses, expected=["main"])
    assert word.data == lg_ac_word(0x8808721)
    values = LG_AC_LAYOUT.read(word.data)
    assert (values["mode"], values["temp"] + 15, values["fan"]) == ("cool", 22, "3")


def test_message_shape():
    dev = device()
    signal = dev.encode(None, HvacState(True, "cool", 22.0)).signal
    assert signal.carrier == 38000
    assert signal.pulses[:2] == (8500, 4250)
    assert signal.pulses[-2:] == (550, 108050)
    assert len(signal.pulses) == 2 + 2 * 28 + 2
    swing = dev.encode(None, HvacState(True, "cool", 22.0, swing_v="swing")).signal
    assert len(swing.pulses) == 2 * (2 + 2 * 28 + 2)
    assert swing.pulses[60:62] == (8500, 4250)


@pytest.mark.parametrize(
    "model, variant",
    [(m, "LG6711A20083V") for m in LG_AC_MODELS]
    + [(m, "GE6711AR2853M") for m in LG_AC_GE_MODELS],
)
def test_variant_comes_from_the_model(model, variant):
    assert LG_AC_MODEL_VARIANT[model] == variant
    assert device(model).variant == variant


def test_unknown_model_gets_lg6711a20083v_and_bad_variant_raises():
    assert LgAcDevice("lg", "whatever").variant == "LG6711A20083V"
    assert LgAcDevice("lg", "whatever", variant="GE6711AR2853M").variant == (
        "GE6711AR2853M"
    )
    with pytest.raises(ValueError):
        LgAcDevice("lg", "whatever", variant="AKB75215403")


@pytest.mark.parametrize(
    "brand, model",
    [("lg", m) for m in LG_AC_MODELS] + [("ge", m) for m in LG_AC_GE_MODELS],
)
def test_registry_serves_the_port(brand, model):
    dev = registry.get_device(brand, model)
    assert isinstance(dev, LgAcDevice)
    assert dev.variant == LG_AC_MODEL_VARIANT[model]


@pytest.mark.parametrize("model", ALL_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins import lg

    brand, cls = LEGACY[LG_AC_MODEL_VARIANT[model]]
    legacy = LegacyDevice(brand, model, getattr(lg, cls))
    assert LgAcDevice(brand, model).capabilities == legacy.capabilities


def test_ge_capabilities_offer_the_legacy_swing_positions():
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.lg import LGv1

    swing = LegacyDevice("ge", GE_MODEL, LGv1).capabilities.swing_v
    assert swing.values == ("off", "auto", "1", "2", "3", "4", "5")
    assert device(GE_MODEL).capabilities.swing_v == swing


def test_undeclared_deviation_is_reported():
    record = next(
        r
        for r in load_oracle("LG")
        if r["class"] == "LGv2"
        and r["state"].get("swing") == "on"
        and r["state"]["mode"] != "off"
    )
    with pytest.raises(AssertionError, match="swing toggle"):
        assert_matches(device(), record, defects=())


def test_toggle_word_is_not_silently_dropped_by_the_plain_helper():
    # Without the _StateWordOnly view, the C pulses hold one word, not two.
    record = next(
        r
        for r in load_oracle("LG")
        if r["class"] == "LGv2"
        and r["state"].get("swing") == "on"
        and r["state"]["mode"] != "off"
    )
    with pytest.raises(Exception):
        assert_matches_oracle(device(), record, (LG_AC_LAYOUT,) * 2, DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_lg_ac_device.py -q`
Expected: collection error, `ImportError: cannot import name ...`.

- [ ] **Step 3: Implement**: insert immediately before `class PluginObject(GenPluginObject):` in `pyhvac/plugins/lg.py`:

```python
# ------------------------------------------------------------------ LgAc
# Layout from IRremoteESP8266's LGProtocol (ir_LG.h): one 28-bit word, sent
# MSB first (IRsend::sendLG: sendGeneric with kLgHdrMark/kLgHdrSpace,
# kLgBitMark, kLgOneSpace/kLgZeroSpace, MSBfirst). As logical bytes the word
# is (raw << 4) big-endian: byte 0 is Sign, byte 1 holds Power, the unnamed
# bits and Mode, byte 2 Temp and Fan, and the top nibble of byte 3 is Sum;
# the low nibble of byte 3 is not sent (nbits=28). IRLgAc::send sends the
# state word, then, for LG6711A20083V only, the swing word when it changed;
# each word is a separate burst with the same timings. No repeat
# (kLgDefaultRepeat is kNoRepeat). Carrier 38 kHz (sendGeneric's 38).

LG_AC = Protocol(
    "lg-ac",
    {
        "main": Section(
            PulseDistance(550, 550, 1600),  # kLgBitMark/kLgZeroSpace/kLgOneSpace
            header=(8500, 4250),  # kLgHdrMark, kLgHdrSpace
            footer=(550,),  # kLgBitMark
            # sendGeneric's space(max(kLgMinGap, kLgMinMessageLength -
            # elapsed)): the C build's timer does not advance, so the oracle
            # records the whole kLgMinMessageLength.
            gap=108050,
            lsb_first=False,
        )
    },
    carrier=38000,
)


@dataclass(frozen=True)
class LgAcChecksum(Checksum):
    """IRLgAc::calcChecksum: sumNibbles(raw >> 4, 4), i.e. the four nibbles
    above Sum (Fan, Temp, Mode + unnamed bit, unnamed bits + Power), mod 16,
    stored in Sum: the top nibble of byte 3 (raw bits 0-3)."""

    start: int = 1
    end: int = 3
    at: int = 3

    def compute(self, data):
        return sum((b >> 4) + (b & 0x0F) for b in self._input(data)) & 0x0F

    def apply(self, data):
        data[self.at] = (data[self.at] & 0x0F) | self.compute(data) << 4

    def check(self, data):
        return data[self.at] >> 4 == self.compute(data)


LG_AC_SIGNATURE = 0x88  # kLgAcSignature
LG_AC_TEMP_ADJUST = 15  # kLgAcTempAdjust: Temp = celsius - 15
LG_AC_MIN_TEMP, LG_AC_MAX_TEMP = 16, 30  # kLgAcMinTemp, kLgAcMaxTemp
LG_AC_MODE = {  # kLgAc{Cool,Dry,Fan,Auto,Heat}
    "cool": 0b000,
    "dry": 0b001,
    "fan": 0b010,
    "auto": 0b011,
    "heat": 0b100,
}
LG_AC_FAN = {  # canonical fan -> the Fan value IRLgAc::setFan stores
    "auto": 5,  # kLgAcFanAuto (kAuto)
    "1": 0,  # lowest: kLgAcFanLowest (kMin)
    "2": 1,  # low: kLgAcFanLow (kLow)
    "3": 2,  # medium: kLgAcFanMedium (kMedium)
    # high: convertFan gives kLgAcFanHigh, which setFan turns into
    # kLgAcFanMax on every model but AKB74955603 (a designed mapping).
    "4": 4,
}
LG_AC_POWER = {"on": 0b00, "off": 0b11}  # kLgAcPowerOn, kLgAcPowerOff
LG_AC_OFF_COMMAND = 0x88C0051  # kLgAcOffCommand
LG_AC_SWINGV_TOGGLE = 0x8810001  # kLgAcSwingVToggle (LG6711A20083V)


def lg_ac_word(raw):
    """The logical bytes of a 28-bit LG word (sent MSB first)."""
    return (raw << 4).to_bytes(4, "big")


# Skeleton: Sign kLgAcSignature, everything else (and Sum) clear. The C
# object never carries stale bits: stateReset loads kLgAcOffCommand and
# every message is either that constant or setRaw'd state plus setters.
LG_AC_LAYOUT = Layout(
    bytes([LG_AC_SIGNATURE, 0, 0, 0]),
    {
        "sign": Field.at(0, 0, 8),  # raw bits 20-27
        "power": Field.at(1, 6, 2, values=LG_AC_POWER),  # raw bits 18-19
        # The struct's unnamed 3 bits (raw bits 15-17). C never sets them in
        # a state word; special words use them (kLgAcSwingVToggle has bit 16),
        # and real LG remotes set bit 15 (see the tests).
        "unused": Field.at(1, 3, 3),
        "mode": Field.at(1, 0, 3, values=LG_AC_MODE),  # raw bits 12-14
        "temp": Field.at(2, 4, 4),  # raw bits 8-11: celsius - kLgAcTempAdjust
        "fan": Field.at(2, 0, 4, values=LG_AC_FAN),  # raw bits 4-7
    },
    checksum=LgAcChecksum(),
)


_LG_AC_BASE = dict(
    modes=("auto", "cool", "fan", "dry", "heat"),
    temperature=TemperatureRange(16.0, 25.0),
    fan=Choice(
        ("auto", "1", "2", "3", "4"),
        {"auto": "auto", "1": "lowest", "2": "low", "3": "medium", "4": "high"},
    ),
    swing_h=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
    features={"light": Choice((False, True), {False: "off", True: "on"})},
)
LG_AC_CAPABILITIES = {  # variant -> the legacy entity (LGv2 / LGv1)
    "LG6711A20083V": Capabilities(
        swing_v=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
        **_LG_AC_BASE,
    ),
    # The legacy LGv1 entity offers swing positions, but IRLgAc::send sends
    # no swing word for GE6711AR2853M (its default case): they send nothing.
    "GE6711AR2853M": Capabilities(
        swing_v=Choice(
            ("off", "auto", "1", "2", "3", "4", "5"),
            {
                "off": "off",
                "auto": "auto",
                "1": "90°",
                "2": "60°",
                "3": "45°",
                "4": "30°",
                "5": "0°",
            },
        ),
        **_LG_AC_BASE,
    ),
}


class LgAcDevice(Device):
    """LG 28-bit A/C (IRLgAc, protocol LG): a full-state word, plus a swing
    toggle word for the LG6711A20083V remote.

    The variant (an lg_ac_remote_model_t name: LG6711A20083V, or
    GE6711AR2853M for the "ge" plugin's models) comes from the model
    (LG_AC_MODEL_VARIANT) unless given, and picks the capabilities (the
    legacy LGv2 / LGv1 entities). The variants share the state word.

    Power off sends only kLgAcOffCommand, whatever the other settings
    (IRLgAc::send). Light and horizontal swing send nothing for either
    variant: IRLgAc::send sends the light toggle for AKB74955603 and the
    SwingH words for AKB73757604 only.

    Swing: GE6711AR2853M sends no swing word at all. LG6711A20083V has one
    vertical swing button: IRac::lg sends kLgAcSwingVToggle when the swing
    changes between off and not-off, comparing with the previous state
    IRac::sendAc passes (prev->swingv, kOff without one);
    IRac::handleToggles has no LG case, the rule lives in IRac::lg. The port
    does the same: with ``previous`` the toggle word follows the state word
    when the swing changes, without it when the target swing is on. No
    toggle word goes with an off message.
    """

    PROTOCOL = LG_AC
    # One layout per word: the toggle word, when sent, reads with it too.
    LAYOUTS = (LG_AC_LAYOUT,)
    capabilities = LG_AC_CAPABILITIES["LG6711A20083V"]

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        self.variant = variant or LG_AC_MODEL_VARIANT.get(model, "LG6711A20083V")
        if self.variant not in LG_AC_CAPABILITIES:
            raise ValueError(f"unknown LG A/C variant {self.variant!r}")
        self.capabilities = LG_AC_CAPABILITIES[self.variant]

    def frames(self, previous, target, actions):
        if not target.power:
            return [Frame("main", lg_ac_word(LG_AC_OFF_COMMAND), 28)]
        temperature = min(max(int(target.temperature), LG_AC_MIN_TEMP), LG_AC_MAX_TEMP)
        data = LG_AC_LAYOUT.build(
            sign=LG_AC_SIGNATURE,
            power="on",
            mode=target.mode,
            temp=temperature - LG_AC_TEMP_ADJUST,
            fan=target.fan,
        )
        frames = [Frame("main", bytes(data), 28)]
        if self.variant != "LG6711A20083V":
            return frames
        was_swinging = previous is not None and previous.swing_v != "off"
        if (target.swing_v != "off") != was_swinging:
            # The documented toggle word. The old glue never passed swing
            # "on" to C (declared as a Defect in the tests).
            frames.append(Frame("main", lg_ac_word(LG_AC_SWINGV_TOGGLE), 28))
        return frames


LG_AC_MODEL_VARIANT = {  # model -> remote variant (lg_ac_remote_model_t)
    "6711A20083V  remote": "LG6711A20083V",
    "TS-H122ERM1  remote": "LG6711A20083V",
    "AG1BH09AW101": "GE6711AR2853M",  # ge plugin
    "6711AR2853M Remote": "GE6711AR2853M",  # ge plugin
}
LG_AC_MODELS = ("6711A20083V  remote", "TS-H122ERM1  remote")  # lg plugin
LG_AC_GE_MODELS = ("AG1BH09AW101", "6711AR2853M Remote")  # ge plugin


DEVICES.update({m: LgAcDevice for m in LG_AC_MODELS})
```

In `pyhvac/plugins/ge.py`, replace its import section (from its first `from` line up to the line before `# Now the match between models and objects`) with:

```python
from .hvaclib import PulseBased, GenPluginObject
from .lg import LG_AC_GE_MODELS, LGv1, LgAcDevice

DEVICES = {}
DEVICES.update({m: LgAcDevice for m in LG_AC_GE_MODELS})


# Now the match between models and objects
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_lg_ac_device.py -q`
Expected: 532 passed, 5 skipped.

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/lg.py pyhvac/plugins/ge.py tests/test_lg_ac_device.py
git add pyhvac/plugins/lg.py pyhvac/plugins/ge.py tests/test_lg_ac_device.py
git commit -m "LG (LGv2 + GE variant): pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 3: LG2

28-bit words; three variants with variant-specific extra words (swing, 4 vane words, swing_h, light toggle); local `Lg2Checksum`.

**Files:**
- Modify: `pyhvac/plugins/lg.py` (block before `class PluginObject(GenPluginObject):`)
- Test: `tests/test_lg2_device.py`

- [ ] **Step 1: Write the failing tests**: create `tests/test_lg2_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.ir.codec import DecodeError, decode
from pyhvac.plugins.lg import (
    LG2,
    LG2_COMMAND_LAYOUT,
    LG2_COMMANDS,
    LG2_LAYOUT,
    LG2_MODELS,
    Lg2Checksum,
    Lg2Device,
)
from pyhvac.state import HvacState

V1, V2, V3 = "AKB75215403", "AKB74955603", "AKB73757604"
MODEL = {V1: "AKB75215403  remote", V2: "AKB74955603  remote", V3: "AMNW24GTPA1"}
LEGACY_CLASS = {V1: "LG2v1", V2: "LG2v2", V3: "LG2v3"}
MODES = ("auto", "cool", "fan", "dry", "heat")

# The C path deviates from the documented LG2 words here:
# - swing "90°"/"60°": IRGHVAC.trans_swing maps them to kHigh/kUpperMiddle.
#   AKB74955603: IRLgAc::convertSwingV sends kLgAcSwingVHigh for kHigh (so
#   kLgAcSwingVHighest is never sent) and has no kUpperMiddle case, so it
#   returns kLgAcSwingVOff, equal to the previous swing: no swing word at all
#   (see C_DROPS). AKB73757604: convertVaneSwingV sends High for kHigh and
#   its default, Highest, for kUpperMiddle. The port sends Highest for "1"
#   and High for "2", on every vane.
# - swing_h "swing" (the legacy "on"): IRGHVAC.trans_hswing has no "on", so
#   IRac's swingh stays kOff and AKB73757604 sends kLgAcSwingHOff. The port
#   sends kLgAcSwingHAuto.
DEFECTS = (
    Defect("command", "swing_v_highest", "swing_v_high", "C sends High for 90°"),
    Defect("command", "swing_h_auto", "swing_h_off", "C glue has no 'on' hswing"),
) + tuple(
    Defect("command", f"vane{v}_{ours}", f"vane{v}_{theirs}", reason)
    for v in range(4)
    for ours, theirs, reason in (
        ("highest", "high", "convertVaneSwingV(kHigh) for 90°"),
        ("high", "highest", "convertVaneSwingV has no kUpperMiddle (60°)"),
    )
)
# Words the port sends that C drops altogether, as (canonical swing_v,
# command): AKB74955603's swing "2" (60°), which C turns into
# kLgAcSwingVOff and so never sends.
C_DROPS = {("2", "swing_v_high")}

# Real captures (ir_LG_test.cpp).
ISSUE_548 = 0x880094D  # TestDecodeLG2.RealLG2Example: cool, 24 C, fan max
ISSUE_1008 = 0x8800347  # TestDecodeLG2.Issue1008: AKB75215403, cool, 18 C, max
AKB74955603_LOW = 0x880A396  # FanSpeedIssue1513: fan mode, 18 C, LowAlt
AKB74955603_HIGH = 0x880A3A7  # FanSpeedIssue1513: fan mode, 18 C, High
SWINGV_MIDDLE = 0x881306A  # TestIRLgAcClass.SwingV (AKB74955603)
VANE2_MIDDLE = 0x881334B  # AKB73757604: vane 2, Middle
VANE3_UPPER_MIDDLE = 0x88133B2  # AKB73757604: vane 3, Upper Middle
VANE2_UPPER_MIDDLE = 0x881333A  # DetectAKB73757604


def device(variant=V1):
    return Lg2Device("lg", MODEL[variant])


def word(frame):
    """A frame back to the 28-bit word ir_LG.h writes."""
    assert frame.nbits == 28
    return int.from_bytes(frame.data, "big") >> 4


def words(state, variant=V1, previous=None):
    dev = device(variant)
    if previous is not None:
        previous = dev.normalise(previous)
    return [word(f) for f in dev.frames(previous, dev.normalise(state), ())]


def as_frame(code):
    return (code << 4).to_bytes(4, "big")


def command(code):
    return LG2_COMMAND_LAYOUT.read(as_frame(code))["command"]


def variant_of(record):
    return LG2_MODELS[record["model"]]


def layouts(frames):
    """The state layout for a power-on message's first word, else commands."""
    first = LG2_LAYOUT if frames[0].data[1] not in (0xC0, 0x13) else None
    return tuple(
        LG2_LAYOUT if i == 0 and first else LG2_COMMAND_LAYOUT
        for i in range(len(frames))
    )


class AsC:
    """The device minus the words C drops (C_DROPS): C's frame list."""

    def __init__(self, dev, drops=C_DROPS):
        self.dev, self.drops = dev, drops
        self.PROTOCOL, self.capabilities = dev.PROTOCOL, dev.capabilities

    def normalise(self, state):
        return self.dev.normalise(state)

    def frames(self, previous, target, actions):
        return [
            f
            for f in self.dev.frames(previous, target, actions)
            if (target.swing_v, LG2_COMMAND_LAYOUT.read(f.data)["command"])
            not in self.drops
        ]


def check(record, defects=DEFECTS, drops=C_DROPS):
    dev = AsC(device(variant_of(record)), drops)
    state = state_from_record(dev, record["state"])
    assert_matches_oracle(dev, record, layouts(dev.frames(None, state, ())), defects)


@pytest.mark.parametrize("record", oracle_params("LG2"))
def test_matches_c_library(record):
    check(record)


def test_every_oracle_record_is_served_by_its_variant():
    for record in load_oracle("LG2"):
        assert LEGACY_CLASS[variant_of(record)] == record["class"]


def test_layouts_round_trip_every_oracle_state():
    for record in load_oracle("LG2"):
        dev = device(variant_of(record))
        state = state_from_record(dev, record["state"])
        frames = dev.frames(None, state, ())
        for layout, frame in zip(layouts(frames), frames):
            values = layout.read(frame.data)
            assert layout.build(**values) == bytearray(frame.data)
            assert layout.checksum.check(frame.data)


def test_every_oracle_word_has_the_signature_and_checksum():
    for record in load_oracle("LG2"):
        n = len(record["pulses"]) // 60
        for frame in decode(LG2, record["pulses"], expected=["main"] * n):
            assert frame.data[0] == 0x88  # kLgAcSignature
            assert frame.data[3] & 0x0F == 0  # 28 bits: the last nibble unsent
            assert Lg2Checksum().check(frame.data)


def test_checksum_is_the_nibble_sum_below_the_signature():
    # ir_LG_test.cpp: calcChecksum(0x88C0051) == 1, calcChecksum(0x88C0354) == 4.
    for code, total in ((0x88C0051, 1), (0x88C0354, 4)):
        data = bytearray(as_frame(code))
        assert Lg2Checksum().check(data)
        data[3] = 0
        Lg2Checksum().apply(data)
        assert data[3] >> 4 == total


def test_checksum_bits_are_not_fields():
    assert Lg2Checksum().positions() == {3}
    for layout in (LG2_LAYOUT, LG2_COMMAND_LAYOUT):
        for name, f in layout.fields.items():
            assert not {b // 8 for b in f.bits} & {0, 3}, name


def test_every_documented_special_word_is_checksummed():
    # The header's constants carry their Sum: the table rebuilds each one.
    for code in (
        0x88C0051,
        0x88C00A6,
        0x8810001,
        0x8813048,
        0x8813059,
        0x881306A,
        0x881307B,
        0x881308C,
        0x881309D,
        0x8813149,
        0x881315A,
        0x881316B,
        0x881317C,
        VANE2_MIDDLE,
        VANE3_UPPER_MIDDLE,
        VANE2_UPPER_MIDDLE,
    ):
        name = command(code)
        assert name in LG2_COMMANDS
        assert bytes(LG2_COMMAND_LAYOUT.build(command=name)) == as_frame(code)


def test_vane_words():
    assert command(VANE2_MIDDLE) == "vane2_middle"
    assert command(VANE3_UPPER_MIDDLE) == "vane3_upper_middle"
    assert command(VANE2_UPPER_MIDDLE) == "vane2_upper_middle"


@pytest.mark.parametrize("variant", [V1, V2, V3])
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("temperature", [16.0, 20.0, 25.0])
def test_off_is_the_off_command_in_every_mode(variant, mode, temperature):
    # IRLgAc::send: power off always sends kLgAcOffCommand alone.
    state = HvacState(
        False,
        mode,
        temperature,
        fan="3",
        swing_v="auto",
        swing_h="swing",
        features={"light": False},
    )
    assert words(state, variant) == [0x88C0051]


@pytest.mark.parametrize("variant", [V1, V2, V3])
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("temperature", [16.0, 21.0, 25.0])
def test_state_word_carries_mode_and_setpoint(variant, mode, temperature):
    dev = device(variant)
    first = dev.frames(None, dev.normalise(HvacState(True, mode, temperature)), ())[0]
    values = LG2_LAYOUT.read(first.data)
    assert (values["power"], values["mode"], values["temperature"]) == (
        True,
        mode,
        int(temperature),
    )


def test_setpoint_is_clamped_to_16_25():
    assert (
        words(HvacState(True, "cool", 10.0))[0]
        == words(HvacState(True, "cool", 16.0))[0]
    )
    assert (
        words(HvacState(True, "cool", 30.0))[0]
        == words(HvacState(True, "cool", 25.0))[0]
    )


@pytest.mark.parametrize(
    "variant, fans",
    [
        # setFan: kLgAcFanHigh becomes kLgAcFanMax except on AKB74955603,
        # which also turns low into kLgAcFanLowAlt.
        (V1, {"auto": 5, "1": 0, "2": 1, "3": 2, "4": 4, "5": 4}),
        (V2, {"auto": 5, "1": 0, "2": 9, "3": 2, "4": 10}),
        (V3, {"auto": 5, "1": 0, "2": 1, "3": 2, "4": 4}),
    ],
)
def test_every_fan_level(variant, fans):
    for fan, code in fans.items():
        first = as_frame(words(HvacState(True, "cool", 22.0, fan=fan), variant)[0])
        assert LG2_LAYOUT.read_raw(first, "fan") == code


def test_real_captures_are_reproduced():
    assert words(HvacState(True, "cool", 24.0, fan="5"), V1) == [ISSUE_548]
    assert words(HvacState(True, "cool", 18.0, fan="5"), V1) == [ISSUE_1008]
    # TestIRLgAcClass.SwingV / Light (AKB74955603): the state word, then
    # kLgAcSwingVMiddle, then (light off) kLgAcLightToggle, last.
    state = HvacState(True, "fan", 18.0, fan="2", swing_v="3")
    assert words(state, V2)[1:] == [SWINGV_MIDDLE, 0x88C00A6]


@pytest.mark.parametrize(
    "capture, fan", [(AKB74955603_LOW, "2"), (AKB74955603_HIGH, "4")]
)
def test_akb74955603_captures_match_but_for_the_unnamed_bit(capture, fan):
    # These AKB74955603 remote words set bit 3 of byte 1 (in LGProtocol's
    # unnamed 3 bits). IRLgAc starts from kLgAcOffCommand, where those bits
    # are 0, and no setter writes them, so the C path (and the port) send 0.
    lit = {"light": True}
    (ours,) = words(HvacState(True, "fan", 18.0, fan=fan, features=lit), V2)
    theirs = LG2_LAYOUT.read(as_frame(capture))
    assert theirs["unnamed"] == 0b001
    assert LG2_LAYOUT.read(as_frame(ours)) == {**theirs, "unnamed": 0}
    assert LG2_LAYOUT.build(**theirs) == bytearray(as_frame(capture))


def test_swing_off_after_auto_capture():
    # TestIRLgAcClass.SwingVOffAfterAuto (AKB74955603): heat, 26 C (25 here,
    # the legacy maximum), fan lowest, light on; swing auto, then off: the
    # state word and kLgAcSwingVOff, nothing else.
    lit = {"light": True}
    before = HvacState(True, "heat", 25.0, fan="1", swing_v="auto", features=lit)
    after = HvacState(True, "heat", 25.0, fan="1", swing_v="off", features=lit)
    sent = words(after, V2, previous=before)
    assert len(sent) == 2 and sent[1] == 0x881315A
    assert LG2_LAYOUT.read(as_frame(sent[0])) == {
        "power": True,
        "mode": "heat",
        "temperature": 25,
        "fan": "lowest",
        "unnamed": 0,
    }


@pytest.mark.parametrize("swing", ["off", "auto", "1", "2", "3", "4", "5"])
def test_akb75215403_sends_the_state_word_only(swing):
    state = HvacState(True, "cool", 22.0, swing_v=swing, swing_h="swing")
    assert len(words(state, V1)) == 1
    assert words(state, V1) == words(HvacState(True, "cool", 22.0), V1)


@pytest.mark.parametrize(
    "swing, sent",
    [
        ("off", None),  # equal to a fresh IRac's previous swing (off)
        ("auto", "swing_v_swing"),
        ("1", "swing_v_highest"),
        ("2", "swing_v_high"),
        ("3", "swing_v_middle"),
        ("4", "swing_v_low"),
        ("5", "swing_v_lowest"),
    ],
)
def test_akb74955603_swing_word_without_previous(swing, sent):
    state = HvacState(True, "cool", 22.0, swing_v=swing, features={"light": True})
    names = [command(w) for w in words(state, V2)[1:]]
    assert names == ([] if sent is None else [sent])


@pytest.mark.parametrize("before", ["off", "auto", "1", "3", "5"])
@pytest.mark.parametrize("after", ["off", "auto", "1", "3", "5"])
def test_akb74955603_swing_word_with_previous_only_on_change(before, after):
    # IRac::lg seeds the previous swing from prev->swingv; IRLgAc::send sends
    # the swing word only when it differs.
    lit = {"light": True}
    previous = HvacState(True, "cool", 22.0, swing_v=before, features=lit)
    target = HvacState(True, "heat", 23.0, swing_v=after, features=lit)
    sent = words(target, V2, previous=previous)
    assert len(sent) == (1 if before == after else 2)


@pytest.mark.parametrize("light", [False, True])
def test_akb74955603_light_toggle_whenever_light_is_off(light):
    # No previous state is used, as C: IRLgAc::send sends the toggle after a
    # state word, which always turns the light on, whenever light is off.
    for previous in (None, HvacState(True, "cool", 22.0, features={"light": light})):
        sent = words(
            HvacState(True, "cool", 22.0, features={"light": light}), V2, previous
        )
        assert (sent[-1] == 0x88C00A6) == (not light)


def test_akb74955603_sends_no_swing_h():
    state = HvacState(True, "cool", 22.0, swing_h="swing", features={"light": True})
    assert len(words(state, V2)) == 1


@pytest.mark.parametrize(
    "swing, position",
    [
        ("off", "highest"),
        ("auto", "highest"),
        ("1", "highest"),
        ("2", "high"),
        ("3", "middle"),
        ("4", "low"),
        ("5", "lowest"),
    ],
)
def test_akb73757604_sends_every_vane_then_swing_h(swing, position):
    # IRac::lg never seeds the previous vanes: every vane goes, with or
    # without previous. Without previous the swing_h word goes too.
    state = HvacState(True, "cool", 22.0, swing_v=swing)
    vanes = [f"vane{v}_{position}" for v in range(4)]
    assert [command(w) for w in words(state, V3)[1:]] == vanes + ["swing_h_off"]
    previous = HvacState(True, "heat", 25.0, swing_v=swing)
    assert [command(w) for w in words(state, V3, previous)[1:]] == vanes


@pytest.mark.parametrize("before", ["off", "swing"])
@pytest.mark.parametrize("after", ["off", "swing"])
def test_akb73757604_swing_h_with_previous_only_on_change(before, after):
    # IRLgAc::send's rule (_swingh != _swingh_prev); C compares with stale
    # memory (_swingh_prev is never written), the port with previous.
    previous = HvacState(True, "cool", 22.0, swing_h=before)
    sent = words(HvacState(True, "cool", 22.0, swing_h=after), V3, previous)
    expected = (
        []
        if before == after
        else ["swing_h_auto" if after == "swing" else "swing_h_off"]
    )
    assert [command(w) for w in sent[5:]] == expected


def test_akb73757604_swing_h_and_no_light():
    sent = words(HvacState(True, "cool", 22.0, swing_h="swing"), V3)
    assert command(sent[-1]) == "swing_h_auto"
    assert len(words(HvacState(True, "cool", 22.0, features={"light": True}), V3)) == 6


def test_encode_is_one_burst_per_word():
    dev = device(V3)
    pulses = dev.encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert len(pulses) == 6 * (2 + 2 * 28 + 2)
    assert pulses[:2] == (3200, 9900)
    assert pulses[-2:] == (480, 108050)


def test_variant_argument_and_unknown_models():
    assert Lg2Device("lg", "whatever").variant == V1
    assert Lg2Device("lg", "whatever", variant=V3).variant == V3
    with pytest.raises(ValueError):
        Lg2Device("lg", "whatever", variant="GE6711AR2853M")


@pytest.mark.parametrize("model", LG2_MODELS)
def test_registry_serves_the_port(model):
    dev = registry.get_device("lg", model)
    assert isinstance(dev, Lg2Device)
    assert dev.variant == LG2_MODELS[model]


@pytest.mark.parametrize("model", LG2_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins import lg

    old = lg.PluginObject.MODELS[model]
    assert old.__name__ == LEGACY_CLASS[LG2_MODELS[model]]
    legacy = LegacyDevice("lg", model, old)
    assert Lg2Device("lg", model).capabilities == legacy.capabilities


def _record(variant, **state):
    return next(
        r
        for r in load_oracle("LG2")
        if variant_of(r) == variant
        and all(r["state"].get(k) == v for k, v in state.items())
    )


def test_undeclared_swing_highest_deviation_is_reported():
    record = _record(V2, mode="cool", swing="90°")
    with pytest.raises(AssertionError, match="command"):
        check(record, defects=())


def test_undeclared_vane_deviations_are_reported():
    for swing in ("90°", "60°"):
        record = _record(V3, mode="cool", swing=swing)
        with pytest.raises(AssertionError, match="vane0"):
            check(record, defects=())


def test_undeclared_swing_h_deviation_is_reported():
    record = _record(V3, hswing="on")
    with pytest.raises(AssertionError, match="swing_h"):
        check(record, defects=())


def test_undeclared_dropped_swing_word_is_reported():
    record = _record(V2, mode="cool", swing="60°")
    # The port sends one word more than C: C's pulses end a word early.
    with pytest.raises(DecodeError, match="end of signal"):
        check(record, drops=set())
    check(record)  # with C_DROPS declared it matches
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_lg2_device.py -q`
Expected: collection error, `ImportError: cannot import name ...`.

- [ ] **Step 3: Implement**: insert immediately before `class PluginObject(GenPluginObject):` in `pyhvac/plugins/lg.py`:

```python
# ------------------------------------------------------------------- Lg2
# Layout from IRremoteESP8266's LGProtocol (ir_LG.h): one 28-bit word, sent
# MSB first by sendLG2 (sendGeneric: kLg2HdrMark/kLg2HdrSpace header,
# kLg2BitMark, kLgOneSpace/kLgZeroSpace, a kLg2BitMark footer; 38 kHz).
# The word is held in Frame.data as 4 bytes, the last nibble unused:
#   byte 0: Sign (kLgAcSignature 0x88)
#   byte 1: Power (bits 6-7), unnamed (bits 3-5), Mode (bits 0-2)
#   byte 2: Temp (bits 4-7), Fan (bits 0-3)
#   byte 3: Sum (bits 4-7)
# Settings the state word cannot carry (swing, light) are separate "special"
# words (kLgAc*Command/Toggle, kLgAcSwing*, kLgAcVaneSwingVBase + ...), each
# a frame of its own, all with the same Sign and Sum.
#
# The gap closing each word is kLgMinMessageLength (108 050 µs): sendGeneric
# spaces max(kLgMinGap, message length - elapsed), and the C library's timing
# recorder (the oracle) elapses no time, so every word is followed by the
# full message length.

LG2 = Protocol(
    "lg2",
    {
        "main": Section(
            PulseDistance(480, 550, 1600),  # kLg2BitMark, kLgZeroSpace/OneSpace
            header=(3200, 9900),  # kLg2HdrMark, kLg2HdrSpace
            footer=(480,),  # kLg2BitMark
            gap=108050,  # kLgMinMessageLength, as recorded
            lsb_first=False,
        )
    },
    carrier=38000,
)
LG2_NBITS = 28  # kLgBits


@dataclass(frozen=True)
class Lg2Checksum(Checksum):
    """IRLgAc::calcChecksum: sumNibbles(raw >> 4, 4), i.e. the low nibble of
    the sum of the four nibbles below Sign (bytes 1-2), stored in Sum (the
    top nibble of byte 3; its low nibble is not sent)."""

    start: int = 1
    end: int = 3
    at: int = 3

    def compute(self, data):
        return (sum((b >> 4) + (b & 0x0F) for b in self._input(data)) & 0x0F) << 4


def _lg2_command(code):
    """A 28-bit special word (ir_LG.h constant) -> the 16 bits of bytes 1-2,
    as the "command" field stores them (byte 1 low, byte 2 high)."""
    return ((code >> 12) & 0xFF) | ((code >> 4) & 0xFF) << 8


LG2_VANE_POSITION = {  # kLgAcVaneSwingV*
    "highest": 1,
    "high": 2,
    "upper_middle": 3,
    "middle": 4,
    "low": 5,
    "lowest": 6,
}
LG2_COMMANDS = {
    "off": _lg2_command(0x88C0051),  # kLgAcOffCommand
    "light_toggle": _lg2_command(0x88C00A6),  # kLgAcLightToggle
    "swing_v_toggle": _lg2_command(0x8810001),  # kLgAcSwingVToggle
    "swing_v_lowest": _lg2_command(0x8813048),  # kLgAcSwingVLowest
    "swing_v_low": _lg2_command(0x8813059),  # kLgAcSwingVLow
    "swing_v_middle": _lg2_command(0x881306A),  # kLgAcSwingVMiddle
    "swing_v_upper_middle": _lg2_command(0x881307B),  # kLgAcSwingVUpperMiddle
    "swing_v_high": _lg2_command(0x881308C),  # kLgAcSwingVHigh
    "swing_v_highest": _lg2_command(0x881309D),  # kLgAcSwingVHighest
    "swing_v_swing": _lg2_command(0x8813149),  # kLgAcSwingVSwing (= Auto)
    "swing_v_off": _lg2_command(0x881315A),  # kLgAcSwingVOff
    "swing_h_auto": _lg2_command(0x881316B),  # kLgAcSwingHAuto
    "swing_h_off": _lg2_command(0x881317C),  # kLgAcSwingHOff
    # IRLgAc::calcVaneSwingV: kLgAcVaneSwingVBase (0x8813200) +
    # ((vane * kLgAcVaneSwingVSize + position) << 4), for the
    # kLgAcSwingVMaxVanes (4) vanes.
    **{
        f"vane{vane}_{name}": _lg2_command(0x8813200 + ((vane * 8 + pos) << 4))
        for vane in range(4)
        for name, pos in LG2_VANE_POSITION.items()
    },
}
LG2_MODE = {"cool": 0, "dry": 1, "fan": 2, "auto": 3, "heat": 4}  # kLgAc*
LG2_FAN = {  # kLgAcFan*
    "lowest": 0,
    "low": 1,
    "medium": 2,
    "max": 4,
    "auto": 5,
    "low_alt": 9,
    "high": 10,
}
LG2_MIN_TEMP, LG2_MAX_TEMP = 16, 30  # kLgAcMinTemp, kLgAcMaxTemp
LG2_TEMP_ADJUST = 15  # kLgAcTempAdjust

# Skeleton: Sign = kLgAcSignature, the rest cleared. IRLgAc::stateReset
# starts from kLgAcOffCommand, whose unnamed bits (byte 1, bits 3-5) are 0
# and which no setter writes, so no bit comes from stale memory. The device
# never sets "unnamed" (C sends 0).
LG2_LAYOUT = Layout(
    bytes([0x88, 0, 0, 0]),
    {
        "power": Field.at(1, 6, 2, values={True: 0, False: 3}),  # kLgAcPowerOn/Off
        # LGProtocol's unnamed bits. Real AKB74955603 words set bit 3; C
        # never writes them, so they keep kLgAcOffCommand's 0.
        "unnamed": Field.at(1, 3, 3),
        "mode": Field.at(1, 0, 3, values=LG2_MODE),
        "temperature": Field.at(  # Temp: degrees - kLgAcTempAdjust
            2,
            4,
            4,
            values={
                t: t - LG2_TEMP_ADJUST for t in range(LG2_MIN_TEMP, LG2_MAX_TEMP + 1)
            },
        ),
        "fan": Field.at(2, 0, 4, values=LG2_FAN),
    },
    checksum=Lg2Checksum(),
)
# The special words: Sign, a 16-bit command, Sum.
LG2_COMMAND_LAYOUT = Layout(
    bytes([0x88, 0, 0, 0]),
    {"command": Field.at(1, 0, 16, values=LG2_COMMANDS)},
    checksum=Lg2Checksum(),
)

LG2_FAN_BY_VARIANT = {  # canonical fan -> kLgAcFan*, as IRLgAc::setFan stores it
    # AKB75215403: convertFan(kHigh) = kLgAcFanHigh, which setFan turns into
    # kLgAcFanMax on any model but AKB74955603; kMax is kLgAcFanMax too.
    "AKB75215403": {
        "auto": "auto",
        "1": "lowest",
        "2": "low",
        "3": "medium",
        "4": "max",
        "5": "max",
    },
    # AKB74955603: setFan keeps kLgAcFanHigh and turns low into kLgAcFanLowAlt.
    "AKB74955603": {
        "auto": "auto",
        "1": "lowest",
        "2": "low_alt",
        "3": "medium",
        "4": "high",
    },
    "AKB73757604": {
        "auto": "auto",
        "1": "lowest",
        "2": "low",
        "3": "medium",
        "4": "max",
    },
}
LG2_SWING_V = {  # canonical swing -> kLgAcSwingV* (AKB74955603), top to bottom
    "off": "swing_v_off",
    "auto": "swing_v_swing",  # convertSwingV(kAuto): kLgAcSwingVSwing
    "1": "swing_v_highest",  # 90°: the topmost documented position
    "2": "swing_v_high",  # 60°
    "3": "swing_v_middle",  # 45°
    "4": "swing_v_low",  # 30°
    "5": "swing_v_lowest",  # 0°
}
LG2_VANE = {  # canonical swing -> kLgAcVaneSwingV* (AKB73757604)
    # convertVaneSwingV has no off or auto: both fall to its default, Highest.
    "off": "highest",
    "auto": "highest",
    "1": "highest",  # 90°: the topmost documented position
    "2": "high",  # 60°
    "3": "middle",  # 45°
    "4": "low",  # 30°
    "5": "lowest",  # 0°
}


def _lg2_capabilities(fan_names):
    return Capabilities(
        modes=("auto", "cool", "fan", "dry", "heat"),
        temperature=TemperatureRange(16.0, 25.0),
        fan=Choice(
            ("auto",) + tuple(str(i) for i in range(1, len(fan_names) + 1)),
            {"auto": "auto", **{str(i): n for i, n in enumerate(fan_names, 1)}},
        ),
        swing_v=Choice(
            ("off", "auto", "1", "2", "3", "4", "5"),
            {
                "off": "off",
                "auto": "auto",
                "1": "90°",
                "2": "60°",
                "3": "45°",
                "4": "30°",
                "5": "0°",
            },
        ),
        swing_h=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
        features={"light": Choice((False, True), {False: "off", True: "on"})},
    )


LG2_CAPABILITIES = {
    "AKB75215403": _lg2_capabilities(("lowest", "low", "medium", "high", "highest")),
    "AKB74955603": _lg2_capabilities(("lowest", "low", "medium", "high")),
    "AKB73757604": _lg2_capabilities(("lowest", "low", "medium", "high")),
}


class Lg2Device(Device):
    """LG2 (28-bit LG protocol, remotes AKB75215403, AKB74955603 and
    AKB73757604, lg_ac_remote_model_t): a state word plus, depending on the
    remote, special words for swing and light, as IRac::lg / IRLgAc::send
    send them.

    The variant comes from the model (LG2_MODELS) unless given, so the
    registry's ``cls(brand, model)`` call picks it; unknown models get
    AKB75215403, the model IRLgAc::setRaw assumes for LG2.

    Power off is always the single kLgAcOffCommand word, whatever the mode,
    setpoint or variant. Power on sends the state word (Power on, Mode,
    Temp, Fan), then:
    - AKB75215403: nothing else. IRLgAc::send has no swing or light for it,
      so swing_v, swing_h and light (in the legacy entity) have no effect.
    - AKB74955603: the swing_v word when the swing differs from the previous
      one, then kLgAcLightToggle when light is off (every state word turns
      the light on, ir_LG.cpp). swing_h is not sent (as C).
    - AKB73757604: one kLgAcVaneSwingV word per vane (4) for swing_v, then
      kLgAcSwingHAuto/Off. light is not sent (as C).

    ``previous``, as the C path:
    - The swing_v word (AKB74955603) goes only when its code differs from
      the previous swing's: IRac::sendAc passes prev->swingv and IRac::lg
      seeds IRLgAc's previous swing with it, and IRLgAc::send compares. A
      fresh IRac's previous state has swing off, so without ``previous`` the
      word goes when swing_v is not "off". The port matches C in both cases.
      (IRac::handleToggles has no LG case: this rule is in IRac::lg/send.)
    - The vane words are sent every time: IRLgAc::send only sends vanes that
      changed, but IRac::lg never seeds the previous vanes (they stay 0, an
      unused position), so every vane always counts as changed.
    - The swing_h word (AKB73757604) goes without ``previous`` (as every
      fresh C message recorded, and as the vane words), and with
      ``previous`` only when swing_h changed. IRLgAc::send means that rule
      (it compares _swingh with _swingh_prev) but nothing ever writes
      _swingh_prev, so C compares with stale memory and in practice sends
      the word every time; stale memory is not a reference (house rule 3a),
      so the port deliberately applies the documented change rule.
    - light: no previous state is used, as C: the toggle goes whenever light
      is off. It is a real toggle, but IRLgAc::send only sends it right after
      a state word, which always turns the light on (ir_LG.cpp, issue 1513),
      so each message leaves the light as asked; toggling only on change
      would leave it on.

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_lg2_device.py):
    - swing_v "1"/"2" (90°/60°): the glue maps them to kHigh/kUpperMiddle;
      convertSwingV sends kLgAcSwingVHigh for kHigh and has no kUpperMiddle
      case (kLgAcSwingVOff, so no swing word at all), and convertVaneSwingV
      sends High for kHigh and Highest for kUpperMiddle. The port sends
      Highest/High (canonical "1" is the topmost documented position).
    - swing_h "swing" (the legacy "on"): IRGHVAC.trans_hswing has no "on",
      so C sends kLgAcSwingHOff; the port sends kLgAcSwingHAuto.
    """

    PROTOCOL = LG2
    LAYOUTS = (LG2_LAYOUT, LG2_COMMAND_LAYOUT)

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        self.variant = variant or LG2_MODELS.get(model, "AKB75215403")
        if self.variant not in LG2_CAPABILITIES:
            raise ValueError(f"unknown LG2 variant {self.variant!r}")
        self.capabilities = LG2_CAPABILITIES[self.variant]

    @staticmethod
    def _word(layout, **values):
        return Frame("main", bytes(layout.build(**values)), LG2_NBITS)

    def _command(self, name):
        return self._word(LG2_COMMAND_LAYOUT, command=name)

    def frames(self, previous, target, actions):
        if not target.power:
            # IRLgAc::send: "Always send the special Off command".
            return [self._command("off")]
        frames = [
            self._word(
                LG2_LAYOUT,
                power=True,
                mode=target.mode,
                temperature=int(target.temperature),
                fan=LG2_FAN_BY_VARIANT[self.variant][target.fan],
            )
        ]
        if self.variant == "AKB74955603":
            before = "off" if previous is None else previous.swing_v
            if LG2_SWING_V[target.swing_v] != LG2_SWING_V[before]:
                frames.append(self._command(LG2_SWING_V[target.swing_v]))
            if not target.features["light"]:  # must be sent last
                frames.append(self._command("light_toggle"))
        elif self.variant == "AKB73757604":
            position = LG2_VANE[target.swing_v]
            frames += [self._command(f"vane{v}_{position}") for v in range(4)]
            if previous is None or previous.swing_h != target.swing_h:
                frames.append(
                    self._command(
                        "swing_h_auto" if target.swing_h == "swing" else "swing_h_off"
                    )
                )
        return frames


LG2_MODELS = {  # model -> remote (lg_ac_remote_model_t), as the old LG2v1-3
    "AKB74395308  remote": "AKB75215403",
    "S4-W12JA3AA": "AKB75215403",
    "AKB75215403  remote": "AKB75215403",
    "AKB74955603  remote": "AKB74955603",
    "A4UW30GFA2": "AKB74955603",
    "AMNW09GSJA0": "AKB74955603",
    "AKB73315611  remote": "AKB74955603",
    "MS05SQ NW0": "AKB74955603",
    "AMNW24GTPA1": "AKB73757604",
    "AKB73757604  remote": "AKB73757604",
}


DEVICES.update({m: Lg2Device for m in LG2_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_lg2_device.py -q`
Expected: 775 passed, 10 skipped.

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/lg.py tests/test_lg2_device.py
git add pyhvac/plugins/lg.py tests/test_lg2_device.py
git commit -m "LG2: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 4: PANASONIC_AC

Two sections (8 + 19 bytes) at 36.7 kHz; five reachable variants (NKE, DKE, JKE, CKP, RKR); layout from the IRPanasonicAc offset constants (the header has no union); CKP power toggle as IRac::handleToggles.

**Files:**
- Modify: `pyhvac/plugins/panasonic.py` (block before `class PluginObject(GenPluginObject):`)
- Test: `tests/test_panasonic_ac_device.py`

- [ ] **Step 1: Write the failing tests**: create `tests/test_panasonic_ac_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.fields import Sum8
from pyhvac.ir.codec import decode
from pyhvac.plugins import panasonic
from pyhvac.plugins.panasonic import (
    PANASONIC_AC,
    PANASONIC_AC_FIRST,
    PANASONIC_AC_MODELS,
    PANASONIC_AC_SECOND,
    PANASONIC_AC_SECOND_CKP,
    PanasonicAcDevice,
)
from pyhvac.state import HvacState

# The C path deviates from the documented PanasonicAc values here:
# - swing "90°" and "60°": the old glue maps them to kHigh and kUpperMiddle;
#   IRPanasonicAc::convertSwingV has no kUpperMiddle (-> kPanasonicAcSwingVAuto).
#   Canonical "1" is the topmost documented position: the port sends
#   kPanasonicAcSwingVHighest for "1" and kPanasonicAcSwingVHigh for "2".
# - Ion (DKE): IRac::sendAc calls IRac::panasonic(..., send.quiet, send.turbo,
#   send.clock), so send.clock (-1, true) lands in the ``filter`` argument and
#   setIon(true) runs on every DKE message; send.filter never reaches C. The
#   port sends the documented purifier value in the kPanasonicAcIonFilterByte
#   bit.
DEFECTS = (
    Defect("swing_v", "1", "2", "glue sends kHigh for 90°"),
    Defect("swing_v", "2", "auto", "glue sends kUpperMiddle for 60°"),
    Defect("ion", 0, 1, "IRac::sendAc passes send.clock as filter"),
)

LEGACY_CLASS = {
    "NKE": "PanasonicNke",
    "DKE": "PanasonicDke",
    "JKE": "PanasonicJke",
    "CKP": "PanasonicCkp",
    "RKR": "PanasonicRkr",
}
MODEL_OF = {  # one model per variant
    "NKE": "NKE series",
    "DKE": "DKE series",
    "JKE": "JKE series",
    "CKP": "CKP series",
    "RKR": "RKR series",
}


def device(variant="DKE"):
    return PanasonicAcDevice("panasonic", MODEL_OF[variant])


def device_for(record):
    return PanasonicAcDevice("panasonic", record["model"])


def frames(state, previous=None, variant="DKE"):
    dev = device(variant)
    if previous is not None:
        previous = dev.normalise(previous)
    return dev.frames(previous, dev.normalise(state), ())


def read(state, previous=None, variant="DKE"):
    dev = device(variant)
    first, second = frames(state, previous, variant)
    return dev.LAYOUTS[1].read(second.data)


@pytest.mark.parametrize("record", oracle_params("PANASONIC_AC"))
def test_matches_c_library(record):
    dev = device_for(record)
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_oracle_covers_every_variant():
    models = {r["model"] for r in load_oracle("PANASONIC_AC")}
    assert {PANASONIC_AC_MODELS[m] for m in models} == set(LEGACY_CLASS)


def test_models_are_the_legacy_ones():
    # Every PluginObject.MODELS key served by the five classes, with the
    # variant of its class. PanasonicLke is in no MODELS entry: unreachable.
    legacy = {
        m: cls.__name__
        for m, cls in panasonic.PluginObject.MODELS.items()
        if cls.__name__ in LEGACY_CLASS.values() or cls.__name__ == "PanasonicLke"
    }
    assert legacy == {m: LEGACY_CLASS[v] for m, v in PANASONIC_AC_MODELS.items()}


def test_layout_round_trips_every_oracle_state():
    for record in load_oracle("PANASONIC_AC"):
        dev = device_for(record)
        state = state_from_record(dev, record["state"])
        for f, layout in zip(dev.frames(None, state, ()), dev.LAYOUTS):
            values = layout.read(f.data)
            assert layout.build(**values) == bytearray(f.data)


def test_checksum_is_a_plain_sum_of_the_second_section():
    # IRPanasonicAc::calcChecksum sums state bytes 0-25 from
    # kPanasonicAcChecksumInit (0xF4). The constant first section sums to
    # 0x0C, and 0xF4 + 0x0C = 0x100: a plain Sum8 over the second section.
    assert (0xF4 + sum(PANASONIC_AC_FIRST.skeleton)) & 0xFF == 0
    for record in load_oracle("PANASONIC_AC"):
        first, second = decode(
            PANASONIC_AC, record["pulses"], expected=["first", "second"]
        )
        assert first.data == PANASONIC_AC_FIRST.skeleton
        state = first.data + second.data
        assert state[26] == (0xF4 + sum(state[:26])) & 0xFF
        assert Sum8(0, 18, 18).check(second.data)


def test_no_field_sits_in_the_checksum_byte():
    for layout in (PANASONIC_AC_SECOND, PANASONIC_AC_SECOND_CKP):
        assert layout.checksum.positions() == {18}
        for name, f in layout.fields.items():
            assert 18 not in {b // 8 for b in f.bits}, name


def test_skeleton_is_the_known_good_state():
    # The oracle's first record: NKE, off, 16 °C, fan auto, swing auto.
    record = load_oracle("PANASONIC_AC")[0]
    assert record["model"] == "NKE series"
    assert record["state"] == {
        "mode": "off",
        "temperature": 16,
        "fan": "auto",
        "swing": "auto",
    }
    _, second = decode(PANASONIC_AC, record["pulses"], expected=["first", "second"])
    data = PANASONIC_AC_SECOND.build(
        mode="auto",
        temperature=16,
        fan="auto",
        swing_v="auto",
        swing_h=0x6,
        model_23=0x81,
    )
    assert bytes(data) == second.data


@pytest.mark.parametrize(
    "variant, model_13, model_21, model_23, clock",
    [
        ("NKE", 0, 0, 0x81, 0),
        ("DKE", 0, 0, 0x01, 0x600),  # byte 25 = 0x06: kPanasonicAcTimeSpecial
        ("JKE", 0, 0, 0x81, 0),
        ("CKP", 0, 1, 0x01, 0),
        ("RKR", 1, 0, 0x89, 0),
    ],
)
def test_model_bytes_are_those_setmodel_writes(
    variant, model_13, model_21, model_23, clock
):
    for power in (True, False):
        values = read(HvacState(power, "cool", 22.0), variant=variant)
        assert (
            values["model_13"],
            values["model_21"],
            values["model_23"],
            values["clock"],
        ) == (model_13, model_21, model_23, clock)
        # Timers: disabled, kPanasonicAcTimeSpecial, as the known good state.
        assert values["on_timer_enabled"] == values["off_timer_enabled"] == 0
        assert values["on_timer"] == values["off_timer"] == 0x600


@pytest.mark.parametrize("variant", sorted(LEGACY_CLASS))
@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat", "fan"])
def test_off_message_carries_mode_auto(variant, mode):
    values = read(HvacState(False, mode, 27.0), variant=variant)
    assert (values["power"], values["mode"], values["temperature"]) == (0, "auto", 27)
    on = read(HvacState(True, mode, 27.0), variant=variant)
    assert (on["power"], on["mode"]) == (1, mode)


def test_fan_mode_keeps_the_requested_temperature():
    # setMode(Fan) writes kPanasonicAcFanModeTemp (27), but IRac::panasonic
    # calls setTemp(degrees) after it.
    assert read(HvacState(True, "fan", 18.0))["temperature"] == 18


def test_temperatures_clamp_to_the_documented_range():
    assert read(HvacState(True, "cool", 16.0))["temperature"] == 16
    assert read(HvacState(True, "cool", 30.0))["temperature"] == 30
    assert frames(HvacState(True, "cool", 16.0))[1].data[6] == 16 << 1
    assert frames(HvacState(True, "cool", 30.0))[1].data[6] == 30 << 1


@pytest.mark.parametrize(
    "fan, code",
    [("auto", 0xA), ("1", 0x3), ("2", 0x4), ("3", 0x5), ("4", 0x6), ("5", 0x7)],
)
def test_fan_codes(fan, code):
    # kPanasonicAcFan{Auto,Min,Low,Med,High,Max} + kPanasonicAcFanDelta
    assert frames(HvacState(True, "cool", 22.0, fan=fan))[1].data[8] >> 4 == code


@pytest.mark.parametrize(
    "swing, code",
    [("auto", 0xF), ("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 5)],
)
def test_swing_v_sends_the_documented_positions_top_down(swing, code):
    data = frames(HvacState(True, "cool", 22.0, swing_v=swing))[1].data
    assert data[8] & 0x0F == code


@pytest.mark.parametrize("variant", ["DKE", "RKR"])
@pytest.mark.parametrize(
    "swing, code",
    [("auto", 0xD), ("1", 0x9), ("2", 0xA), ("3", 0x6), ("4", 0xB), ("5", 0xC)],
)
def test_swing_h_positions(variant, swing, code):
    state = HvacState(True, "cool", 22.0, swing_h=swing)
    assert frames(state, variant=variant)[1].data[9] == code


@pytest.mark.parametrize("swing", ["off", "swing"])
def test_nke_swing_h_is_always_middle(swing):
    # IRPanasonicAc::setSwingHorizontal forces Middle on NKE (and LKE).
    state = HvacState(True, "cool", 22.0, swing_h=swing)
    assert frames(state, variant="NKE")[1].data[9] == 0x06


@pytest.mark.parametrize("variant", ["JKE", "CKP"])
def test_jke_and_ckp_have_no_swing_h(variant):
    # setSwingHorizontal ignores them: byte 17 stays 0.
    assert device(variant).capabilities.swing_h is None
    assert frames(HvacState(True, "cool", 22.0), variant=variant)[1].data[9] == 0


@pytest.mark.parametrize(
    "variant, quiet_bit, powerful_bit",
    [
        ("NKE", 0, 5),
        ("DKE", 0, 5),
        ("JKE", 0, 5),
        ("CKP", 5, 0),  # kPanasonicAcQuietCkpOffset / PowerfulCkpOffset
        ("RKR", 5, 0),
    ],
)
@pytest.mark.parametrize("power", [True, False])
@pytest.mark.parametrize("mode", ["auto", "cool", "heat"])
def test_quiet_and_powerful(variant, quiet_bit, powerful_bit, power, mode):
    def byte21(**features):
        state = HvacState(power, mode, 22.0, features=features)
        return frames(state, variant=variant)[1].data[13] & ~0x10

    assert byte21() == 0
    assert byte21(quiet=True) == 1 << quiet_bit
    assert byte21(powerful=True) == 1 << powerful_bit
    # setQuiet then setPowerful: Powerful on clears Quiet.
    assert byte21(quiet=True, powerful=True) == 1 << powerful_bit


@pytest.mark.parametrize("power", [True, False])
def test_purifier_sets_the_dke_ion_bit(power):
    assert read(HvacState(power, "heat", 25.0))["ion"] == 0
    on = HvacState(power, "heat", 25.0, features={"purifier": True})
    assert read(on)["ion"] == 1
    assert frames(on)[1].data[14] == 0x01


@pytest.mark.parametrize("variant", ["NKE", "JKE", "CKP", "RKR"])
def test_only_dke_has_a_purifier(variant):
    dev = device(variant)
    assert "purifier" not in dev.capabilities.features
    assert read(HvacState(True, "cool", 22.0), variant=variant)["ion"] == 0


def test_dke_ion_real_messages():
    # TestDecodePanasonicAC.DkeIonRealMessages (issue 1024), a real DKE
    # remote: heat, 25 °C, fan auto, swing auto/auto, Ion off then on. The
    # remote also sets byte 13 bits 1-3 (both timer flags and the bit
    # setModel uses for RKR) and clears two constant bits (byte 19 bit 3,
    # byte 20 bit 7) that IRPanasonicAc never touches, so only the settings
    # and model bytes are compared; Ion is the only bit the captures differ in.
    ion_off = bytes.fromhex("0220e004004f3280af0d000660000001000630")
    ion_on = bytes.fromhex("0220e004004f3280af0d000660000101000631")
    settings = ("power", "mode", "temperature", "fan", "swing_v", "swing_h")
    settings += ("quiet", "powerful", "ion", "model_21", "model_23")
    settings += ("clock",)
    assert (
        bytes(a ^ b for a, b in zip(ion_off, ion_on)).hex()
        == "00" * 14 + "01" + "00" * 3 + "01"
    )
    for capture, purifier in ((ion_off, False), (ion_on, True)):
        assert PANASONIC_AC_SECOND.checksum.check(capture)
        state = HvacState(
            True,
            "heat",
            25.0,
            swing_v="auto",
            swing_h="auto",
            features={"purifier": purifier},
        )
        ours = read(state)
        theirs = PANASONIC_AC_SECOND.read(capture)
        assert {k: ours[k] for k in settings} == {k: theirs[k] for k in settings}


def test_real_capture_decodes():
    # TestDecodePanasonicAC.RealExample (issue 525): the port's timings and
    # checksum hold on a real remote's message (cool, 25 °C, power off).
    raw = (
        "3582 1686 488 378 488 1238 488 378 488 378 488 378 488 378 488 378 488 "
        "384 488 378 488 378 488 378 488 378 488 378 488 1242 486 378 488 384 "
        "488 378 488 378 488 380 486 382 484 382 484 1264 464 1266 460 1272 462 "
        "378 488 406 460 1266 462 380 488 382 484 388 478 406 462 410 462 404 "
        "462 406 462 396 470 406 462 404 462 406 460 404 462 410 462 404 462 "
        "404 462 406 464 406 462 404 462 406 462 404 462 410 462 404 462 406 "
        "462 404 462 404 462 404 462 406 460 406 462 410 462 404 462 1264 484 "
        "1244 486 382 482 382 486 382 486 378 486 382 488 9924 3554 1686 488 "
        "378 490 1240 486 378 488 378 488 378 488 378 488 382 484 386 486 378 "
        "488 382 486 378 488 382 486 382 484 1242 486 380 488 386 484 382 486 "
        "380 486 382 486 380 486 380 486 1242 486 1242 484 1248 484 380 488 382 "
        "484 1242 486 382 484 382 484 382 484 382 486 386 484 382 486 382 484 "
        "382 486 382 486 380 484 382 486 382 488 380 486 382 484 380 462 406 "
        "488 376 484 1246 482 1246 460 404 480 392 484 386 482 1244 484 382 484 "
        "382 484 1242 482 1244 484 382 464 410 460 404 462 406 462 404 462 404 "
        "470 396 462 406 462 404 462 1286 460 1268 458 1268 460 1266 460 1266 "
        "460 406 460 1266 462 406 460 1272 462 406 460 406 460 406 460 406 462 "
        "404 462 406 460 406 462 410 462 404 462 406 460 406 460 406 462 404 "
        "462 406 460 406 460 410 462 406 460 1268 460 1266 460 404 460 406 462 "
        "406 460 406 460 412 456 410 460 410 438 428 460 410 456 410 456 1272 "
        "436 1288 438 434 438 428 438 428 438 428 438 428 438 428 438 428 438 "
        "428 438 434 438 428 438 428 438 428 438 428 438 428 440 428 438 428 "
        "438 432 438 428 438 428 438 428 438 428 438 428 438 428 438 430 438 "
        "1294 438 428 438 428 438 428 438 428 438 428 438 428 438 428 438 434 "
        "438 428 438 1288 438 1290 438 428 438 428 438 428 438 428 438 432 438 "
        "1288 438 1290 438 430 438 428 438 428 438 428 438 428 438 1292 438"
    )
    pulses = [int(x) for x in raw.split()] + [100000]
    first, second = decode(PANASONIC_AC, pulses, expected=["first", "second"])
    assert first.data == PANASONIC_AC_FIRST.skeleton
    assert second.data.hex() == "0220e00400303280af00000660000080000683"
    assert PANASONIC_AC_SECOND.checksum.check(second.data)
    values = PANASONIC_AC_SECOND.read(second.data)
    assert (values["power"], values["mode"], values["temperature"]) == (0, "cool", 25)
    assert (values["fan"], values["swing_v"]) == ("auto", "auto")


def test_ckp_power_toggles_only_on_a_change():
    # IRac::handleToggles: for kPanasonicCkp, power = desired ^ prev->power.
    # (Checked against the C path, the old object sending twice, in
    # cpath_check.py.)
    on, off = HvacState(True, "cool", 22.0), HvacState(False, "cool", 22.0)
    assert read(on, previous=off, variant="CKP")["power"] == 1
    assert read(off, previous=on, variant="CKP")["power"] == 1
    assert read(on, previous=on, variant="CKP")["power"] == 0
    assert read(off, previous=off, variant="CKP")["power"] == 0
    # A setting change alone does not toggle.
    warmer = HvacState(True, "heat", 26.0, fan="3")
    assert read(warmer, previous=on, variant="CKP")["power"] == 0


def test_ckp_without_previous_sends_what_a_fresh_irac_sends():
    # A fresh IRac's _prev has protocol UNKNOWN: handleToggles does nothing,
    # the Power bit is the target power.
    assert read(HvacState(True, "cool", 22.0), variant="CKP")["power"] == 1
    assert read(HvacState(False, "cool", 22.0), variant="CKP")["power"] == 0


@pytest.mark.parametrize("variant", ["NKE", "DKE", "JKE", "RKR"])
def test_previous_is_ignored_except_on_ckp(variant):
    dev = device(variant)
    target = HvacState(True, "cool", 22.0, fan="2", swing_v="3")
    for previous in (
        None,
        target,
        HvacState(False, "heat", 30.0),
        HvacState(True, "cool", 22.0, fan="5", swing_v="auto"),
    ):
        assert dev.encode(previous, target).signal == dev.encode(None, target).signal


def test_message_shape():
    dev = device()
    signal = dev.encode(None, HvacState(True, "cool", 22.0)).signal
    pulses = signal.pulses
    assert signal.carrier == 36700  # kPanasonicFreq
    assert pulses[:2] == (3456, 1728)
    first = 2 + 2 * 64 + 2
    assert pulses[first - 2 : first] == (432, 10000)
    assert pulses[first : first + 2] == (3456, 1728)
    assert pulses[-2:] == (432, 100000)
    assert len(pulses) == first + 2 + 2 * 152 + 2


def test_unknown_model_is_jke_and_unknown_variant_fails():
    # setModel ignores an unknown model; getModel reads the untouched
    # kPanasonicKnownGoodState as JKE.
    assert PanasonicAcDevice("panasonic", "nope").variant == "JKE"
    assert PanasonicAcDevice("panasonic", "nope", variant="RKR").variant == "RKR"
    with pytest.raises(ValueError, match="variant"):
        PanasonicAcDevice("panasonic", "nope", variant="LKE")


@pytest.mark.parametrize("model", PANASONIC_AC_MODELS)
def test_registry_serves_the_port(model):
    dev = registry.get_device("panasonic", model)
    assert isinstance(dev, PanasonicAcDevice)
    assert dev.variant == PANASONIC_AC_MODELS[model]


@pytest.mark.parametrize("model", PANASONIC_AC_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice

    cls = getattr(panasonic, LEGACY_CLASS[PANASONIC_AC_MODELS[model]])
    legacy = LegacyDevice("panasonic", model, cls)
    assert PanasonicAcDevice("panasonic", model).capabilities == legacy.capabilities


@pytest.mark.parametrize(
    "defect, pick",
    [
        (DEFECTS[0], lambda s: s.get("swing") == "90°"),
        (DEFECTS[1], lambda s: s.get("swing") == "60°"),
        (DEFECTS[2], lambda s: s.get("purifier", "off") == "off"),
    ],
)
def test_undeclared_deviation_is_reported(defect, pick):
    records = [
        r
        for r in load_oracle("PANASONIC_AC")
        if pick(r["state"])
        and (defect.field != "ion" or PANASONIC_AC_MODELS[r["model"]] == "DKE")
    ]
    assert records
    others = tuple(d for d in DEFECTS if d != defect)
    for record in records[:3]:
        dev = device_for(record)
        with pytest.raises(AssertionError, match=defect.field):
            assert_matches_oracle(dev, record, dev.LAYOUTS, others)


def test_layouts_must_cover_every_frame():
    record = load_oracle("PANASONIC_AC")[0]
    dev = device_for(record)
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:1], DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_panasonic_ac_device.py -q`
Expected: collection error, `ImportError: cannot import name ...`.

- [ ] **Step 3: Implement**: insert immediately before `class PluginObject(GenPluginObject):` in `pyhvac/plugins/panasonic.py`:

```python
# ------------------------------------------------------------- PanasonicAc
# Layout from IRremoteESP8266's IRPanasonicAc (ir_Panasonic.h/.cpp). The
# header has no bitfield struct for this protocol: the fields are its
# constants (kPanasonicAc*Offset/Size, kPanasonicAcIonFilterByte, the
# per-model bytes IRPanasonicAc::setModel writes) over the 27-byte
# kPanasonicKnownGoodState. IRsend::sendPanasonicAC sends it LSB first in two
# sections: bytes 0-7 (kPanasonicAcSection1Length), closed by
# kPanasonicAcSectionGap, then bytes 8-26, closed by kPanasonicAcMessageGap
# (kDefaultMessageGap). Second-frame byte n is state byte n + 8.

PANASONIC_AC = Protocol(
    "panasonic-ac",
    {
        "first": Section(
            PulseDistance(432, 432, 1296),  # kPanasonicBitMark/ZeroSpace/OneSpace
            header=(3456, 1728),  # kPanasonicHdrMark/HdrSpace
            footer=(432,),
            gap=10000,  # kPanasonicAcSectionGap
        ),
        "second": Section(
            PulseDistance(432, 432, 1296),
            header=(3456, 1728),
            footer=(432,),
            gap=100000,  # kPanasonicAcMessageGap = kDefaultMessageGap
        ),
    },
    carrier=36700,  # kPanasonicFreq
)

PANASONIC_AC_MODE = {  # kPanasonicAc{Auto,Dry,Cool,Heat,Fan}
    "auto": 0b000,
    "dry": 0b010,
    "cool": 0b011,
    "heat": 0b100,
    "fan": 0b110,
}
PANASONIC_AC_FAN = {  # canonical fan -> kPanasonicAcFan* + kPanasonicAcFanDelta
    "auto": 7 + 3,  # FanAuto
    "1": 0 + 3,  # lowest: FanMin (kMin)
    "2": 1 + 3,  # low: FanLow
    "3": 2 + 3,  # medium: FanMed
    "4": 3 + 3,  # high: FanHigh
    "5": 4 + 3,  # highest: FanMax (kMax)
}
PANASONIC_AC_SWING_V = {  # canonical swing -> kPanasonicAcSwingV*, top to bottom
    "auto": 0xF,  # SwingVAuto
    "1": 0x1,  # 90°: SwingVHighest
    "2": 0x2,  # 60°: SwingVHigh
    "3": 0x3,  # 45°: SwingVMiddle
    "4": 0x4,  # 30°: SwingVLow
    "5": 0x5,  # 0°: SwingVLowest
}
PANASONIC_AC_SWING_H = {  # canonical position -> kPanasonicAcSwingH*
    "auto": 0xD,  # SwingHAuto
    "1": 0x9,  # far left: SwingHFullLeft
    "2": 0xA,  # left: SwingHLeft
    "3": 0x6,  # middle: SwingHMiddle
    "4": 0xB,  # right: SwingHRight
    "5": 0xC,  # far right: SwingHFullRight
}
PANASONIC_AC_MIN_TEMP, PANASONIC_AC_MAX_TEMP = 16, 30  # kPanasonicAcMin/MaxTemp
PANASONIC_AC_TIME_SPECIAL = 0x600  # kPanasonicAcTimeSpecial: "no time"

# The first section never changes: kPanasonicKnownGoodState bytes 0-7.
PANASONIC_AC_FIRST = Layout(bytes.fromhex("0220e00400000006"), {})


def _panasonic_ac_second(quiet_bit, powerful_bit):
    """The second section, with Quiet and Powerful at the given byte-21 bits."""
    return Layout(
        # kPanasonicKnownGoodState bytes 8-26 with every field the device
        # writes cleared. Byte 15 (0x80), byte 19 bit 3 and byte 20 bit 7 are
        # constants; both timers stay kPanasonicAcTimeSpecial and disabled,
        # as IRac::panasonic never sets them. stateReset copies the whole
        # known good state, so no byte comes from stale memory.
        bytes.fromhex("0220e004000000800000000ee0000000000000"),
        {
            "power": Field.at(5, 0, 1),  # kPanasonicAcPowerOffset
            "on_timer_enabled": Field.at(5, 1, 1),  # kPanasonicAcOnTimerOffset
            "off_timer_enabled": Field.at(5, 2, 1),  # kPanasonicAcOffTimerOffset
            "model_13": Field.at(5, 3, 1),  # setModel: RKR sets byte 13 |= 0x08
            "mode": Field.at(5, 4, 3, values=PANASONIC_AC_MODE),
            "temperature": Field.at(  # kPanasonicAcTempOffset/Size, in °C
                6,
                1,
                5,
                values={
                    t: t
                    for t in range(PANASONIC_AC_MIN_TEMP, PANASONIC_AC_MAX_TEMP + 1)
                },
            ),
            "swing_v": Field.at(8, 0, 4, values=PANASONIC_AC_SWING_V),
            "fan": Field.at(8, 4, 4, values=PANASONIC_AC_FAN),
            # Byte 17 low nibble: kPanasonicAcSwingH* on DKE/RKR, Middle on
            # NKE (forced by setSwingHorizontal), 0 on JKE/CKP (never written).
            "swing_h": Field.at(9, 0, 4),
            "on_timer": Field.at(10, 0, 11),  # bytes 18-19, _setTime
            "off_timer": Field.at(11, 4, 11),  # bytes 19-20, setOffTimer
            "quiet": Field.at(13, quiet_bit, 1),
            "model_21": Field.at(13, 4, 1),  # setModel: CKP sets byte 21 |= 0x10
            "powerful": Field.at(13, powerful_bit, 1),
            "ion": Field.at(14, 0, 1),  # kPanasonicAcIonFilterByte/Offset (DKE)
            "model_23": Field.at(15, 0, 8),  # setModel: 0x81, DKE/CKP 0x01, RKR 0x89
            "clock": Field.at(16, 0, 11),  # bytes 24-25, _setTime
        },
        # IRPanasonicAc::calcChecksum: sumBytes(state[0:26], kPanasonicAcChecksumInit
        # = 0xF4). The constant first section sums to 0x0C, and 0xF4 + 0x0C
        # = 0x100, so it is a plain sum of this section's bytes 0-17.
        checksum=Sum8(0, 18, 18),
    )


# kPanasonicAcQuietOffset / kPanasonicAcPowerfulOffset; CKP and RKR have them
# swapped (kPanasonicAcQuietCkpOffset / kPanasonicAcPowerfulCkpOffset).
PANASONIC_AC_SECOND = _panasonic_ac_second(quiet_bit=0, powerful_bit=5)
PANASONIC_AC_SECOND_CKP = _panasonic_ac_second(quiet_bit=5, powerful_bit=0)

# What IRPanasonicAc::setModel writes for each panasonic_ac_remote_model_t,
# and which of the per-model settings each remote has. "swing_h" is the
# setSwingHorizontal behaviour: "positions" (DKE, RKR), "middle" (NKE: always
# Middle) or None (JKE, CKP: byte 17 is never written).
PANASONIC_AC_VARIANTS = {
    "NKE": dict(model_13=0, model_21=0, model_23=0x81, clock=0, swing_h="middle"),
    "DKE": dict(
        model_13=0,
        model_21=0,
        model_23=0x01,
        clock=PANASONIC_AC_TIME_SPECIAL,  # setModel: byte 25 = 0x06
        swing_h="positions",
    ),
    "JKE": dict(model_13=0, model_21=0, model_23=0x81, clock=0, swing_h=None),
    "CKP": dict(model_13=0, model_21=1, model_23=0x01, clock=0, swing_h=None),
    "RKR": dict(model_13=1, model_21=0, model_23=0x89, clock=0, swing_h="positions"),
}

_PANASONIC_AC_ON_OFF = Choice((False, True), {False: "off", True: "on"})
_PANASONIC_AC_POSITIONS = Choice(
    ("auto", "1", "2", "3", "4", "5"),
    {
        "auto": "auto",
        "1": "far left",
        "2": "left",
        "3": "middle",
        "4": "right",
        "5": "far right",
    },
)


def _panasonic_ac_capabilities(variant):
    swing_h = {
        "NKE": Choice(("off", "swing"), {"off": "off", "swing": "on"}),
        "DKE": _PANASONIC_AC_POSITIONS,
        "RKR": _PANASONIC_AC_POSITIONS,
    }.get(variant)
    features = {"quiet": _PANASONIC_AC_ON_OFF, "powerful": _PANASONIC_AC_ON_OFF}
    if variant == "DKE":
        features["purifier"] = _PANASONIC_AC_ON_OFF
    return Capabilities(
        modes=("auto", "cool", "dry", "heat", "fan"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=Choice(
            ("auto", "1", "2", "3", "4", "5"),
            {
                "auto": "auto",
                "1": "lowest",
                "2": "low",
                "3": "medium",
                "4": "high",
                "5": "highest",
            },
        ),
        swing_v=Choice(
            ("auto", "1", "2", "3", "4", "5"),
            {"auto": "auto", "1": "90°", "2": "60°", "3": "45°", "4": "30°", "5": "0°"},
        ),
        swing_h=swing_h,
        features=features,
    )


class PanasonicAcDevice(Device):
    """Panasonic 216-bit A/C (remote variants NKE, DKE, JKE, CKP and RKR,
    panasonic_ac_remote_model_t): full state in two sections.

    The variant comes from the model (PANASONIC_AC_MODELS) unless given, so
    the registry's ``cls(brand, model)`` call picks it. An unknown model gets
    JKE: IRPanasonicAc::setModel ignores an unknown model, and getModel reads
    the untouched kPanasonicKnownGoodState as JKE. The capabilities (swing_h,
    purifier) and the Quiet/Powerful bits depend on the variant.

    ``previous`` is ignored, except on CKP. There the Power bit is a toggle
    (setPower's warning): IRac::handleToggles sends ``power ^ prev->power``
    for kPanasonicCkp, so the port toggles only when the power changes.
    Without ``previous`` it sends what a fresh IRac does: its _prev has
    protocol UNKNOWN, so handleToggles does nothing and the bit is the
    target power (1 for on, 0 for off, which leaves a CKP unit as it is).
    The other variants carry the power as state.
    """

    PROTOCOL = PANASONIC_AC

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        self.variant = variant or PANASONIC_AC_MODELS.get(model, "JKE")
        if self.variant not in PANASONIC_AC_VARIANTS:
            raise ValueError(f"unknown PanasonicAc variant {self.variant!r}")
        self.capabilities = _panasonic_ac_capabilities(self.variant)
        second = (
            PANASONIC_AC_SECOND_CKP
            if self.variant in ("CKP", "RKR")
            else PANASONIC_AC_SECOND
        )
        self.LAYOUTS = (PANASONIC_AC_FIRST, second)

    def frames(self, previous, target, actions):
        variant = PANASONIC_AC_VARIANTS[self.variant]
        power = target.power
        if self.variant == "CKP" and previous is not None:
            power = target.power != previous.power
        # IRac::panasonic: setMode(convertMode(mode)) then setTemp(degrees).
        # An off message carries mode auto (convertMode's default for kOff),
        # and fan mode keeps the requested temperature: setMode's 27 °C
        # (kPanasonicAcFanModeTemp) is overwritten by the setTemp after it.
        mode = target.mode if target.power else "auto"
        temperature = min(
            max(int(target.temperature), PANASONIC_AC_MIN_TEMP), PANASONIC_AC_MAX_TEMP
        )
        if variant["swing_h"] == "positions":
            swing_h = PANASONIC_AC_SWING_H[target.swing_h]
        elif variant["swing_h"] == "middle":
            swing_h = PANASONIC_AC_SWING_H["3"]
        else:
            swing_h = 0
        # setQuiet then setPowerful: Powerful on clears Quiet.
        powerful = target.features["powerful"]
        quiet = target.features["quiet"] and not powerful
        # setIon only acts on DKE. The C path passes send.clock (-1, true) as
        # IRac::panasonic's filter argument, so it always sets Ion; the port
        # sends the documented purifier value (declared as a Defect).
        ion = target.features.get("purifier", False)
        second = self.LAYOUTS[1].build(
            power=power,
            model_13=variant["model_13"],
            mode=mode,
            temperature=temperature,
            # The documented positions: "1" (90°) is SwingVHighest. The old
            # glue sent kHigh for 90° and kUpperMiddle (-> Auto) for 60°.
            swing_v=target.swing_v,
            fan=target.fan,
            swing_h=swing_h,
            quiet=quiet,
            model_21=variant["model_21"],
            powerful=powerful,
            ion=ion,
            model_23=variant["model_23"],
            clock=variant["clock"],
        )
        return [
            Frame("first", bytes(PANASONIC_AC_FIRST.skeleton)),
            Frame("second", bytes(second)),
        ]


PANASONIC_AC_MODELS = {  # model -> remote variant (panasonic_ac_remote_model_t)
    "NKE series": "NKE",
    "DKE series": "DKE",
    "DKW series": "DKE",
    "PKR series": "DKE",
    "JKE series": "JKE",
    "CKP series": "CKP",
    "RKR series": "RKR",
    "CS-ME10CKPG": "CKP",
    "CS-ME12CKPG": "CKP",
    "CS-ME14CKPG": "CKP",
    "CS-E7PKR": "DKE",
    "CS-Z9RKR": "RKR",
    "CS-Z24RKR": "RKR",
    "CS-YW9MKD": "JKE",
    "CS-E12QKEW": "DKE",
    "A75C2311remote": "CKP",
    "A75C2616-1remote": "DKE",
    "A75C3704remote": "DKE",
    "PN1122Vremote": "DKE",
    "A75C3747remote": "JKE",
    "A75C4762remote": "RKR",
}


DEVICES.update({m: PanasonicAcDevice for m in PANASONIC_AC_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_panasonic_ac_device.py -q`
Expected: 1137 passed, 21 skipped.

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/panasonic.py tests/test_panasonic_ac_device.py
git add pyhvac/plugins/panasonic.py tests/test_panasonic_ac_device.py
git commit -m "PANASONIC_AC: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 5: PANASONIC_AC32

Doubled-byte 32-bit halves sent high half first (local `PanasonicAc32Doubled`); power toggle as IRac::handleToggles.

**Files:**
- Modify: `pyhvac/plugins/panasonic.py` (block before `class PluginObject(GenPluginObject):`)
- Test: `tests/test_panasonic_ac32_device.py`

- [ ] **Step 1: Write the failing tests**: create `tests/test_panasonic_ac32_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.panasonic import (
    PANASONIC_AC32_HIGH_LAYOUT,
    PANASONIC_AC32_LOW_LAYOUT,
    PANASONIC_AC32_MODELS,
    PanasonicAc32Doubled,
    PanasonicAc32Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented values here:
# - the old swing labels go through IRGHVAC.trans_swing ("90°" -> kHigh,
#   "60°" -> kUpperMiddle) into IRPanasonicAc32::convertSwingV, which passes
#   kHigh through as kPanasonicAcSwingVHigh (so kPanasonicAcSwingVHighest is
#   never sent) and has no kUpperMiddle case (it falls back to
#   kPanasonicAc32SwingVAuto);
# - the legacy glue (IRGHVAC.trans_hswing) has no "on" key, so swingh stays
#   kOff and IRac::panasonic32 never sets the SwingH bit.
DEFECTS = (
    Defect("swing_v", "1", "2", "C sends SwingVHigh for highest"),
    Defect("swing_v", "2", "auto", "C has no upper-middle case: sends auto"),
    Defect("swing_h", "swing", "off", "legacy glue never passes hswing on"),
)


def device(model="generic 32"):
    return PanasonicAc32Device("panasonic", model)


def raw(state, previous=None):
    """The 32-bit word (PanasonicAc32Protocol.raw) the port sends."""
    dev = device()
    if previous is not None:
        previous = dev.normalise(previous)
    high, high2, low, low2 = dev.frames(previous, dev.normalise(state), ())
    assert (high.data, low.data) == (high2.data, low2.data)
    return int.from_bytes(
        bytes((low.data[0], low.data[2], high.data[0], high.data[2])), "little"
    )


def read(state, previous=None):
    dev = device()
    if previous is not None:
        previous = dev.normalise(previous)
    high, _, low, _ = dev.frames(previous, dev.normalise(state), ())
    return {
        **PANASONIC_AC32_HIGH_LAYOUT.read(high.data),
        **PANASONIC_AC32_LOW_LAYOUT.read(low.data),
    }


@pytest.mark.parametrize("record", oracle_params("PANASONIC_AC32"))
def test_matches_c_library(record):
    dev = device(record["model"])
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("PANASONIC_AC32"):
        state = state_from_record(dev, record["state"])
        for frame, layout in zip(dev.frames(None, state, ()), dev.LAYOUTS):
            values = layout.read(frame.data)
            assert layout.build(**values) == bytearray(frame.data)


def test_known_good_state():
    # kPanasonicAc32KnownGood = 0x0AF136FC: cool, 16 °C, fan auto, swing V
    # auto, swing H on, PowerToggle 1 ("keep the same": the unit is on).
    on = HvacState(True, "cool", 16.0, swing_v="auto", swing_h="swing")
    assert raw(on, previous=on) == 0x0AF136FC


def test_human_readable_example():
    # ir_Panasonic_test.cpp HumanReadable: power toggle on, heat, 24 °C, fan
    # medium, swing H off, swing V lowest.
    state = HvacState(True, "heat", 24.0, fan="3", swing_v="5", swing_h="off")
    assert raw(state) == 0x044936D4


def test_every_byte_is_sent_twice_in_two_blocks_high_half_first():
    # sendPanasonicAC32: section 0 = bytes 2-3, section 1 = bytes 0-1; each
    # section twice, each byte doubled.
    dev = device()
    frames = dev.frames(None, dev.normalise(HvacState(True, "cool", 16.0)), ())
    assert [f.section for f in frames] == ["block", "repeat", "block", "repeat"]
    assert [f.data.hex() for f in frames] == [
        "f1f10202",
        "f1f10202",
        "f4f43636",
        "f4f43636",
    ]


def test_message_shape():
    # Matches the SyntheticMessage output in ir_Panasonic_test.cpp.
    dev = device()
    pulses = dev.encode(None, HvacState(True, "cool", 16.0)).signal.pulses
    section = 2 + 64 + 2 + 64 + 2 + 2
    assert len(pulses) == 2 * section
    assert pulses[:2] == (3543, 3450)
    assert pulses[66:68] == (3543, 3450)
    assert pulses[132:136] == (3543, 3450, 920, 13946)
    assert pulses[-4:] == (3543, 3450, 920, 13946)
    assert dev.encode(None, HvacState(True, "cool", 16.0)).signal.carrier == 36700


def test_doubled_bytes_hold_no_field():
    for layout in (PANASONIC_AC32_HIGH_LAYOUT, PANASONIC_AC32_LOW_LAYOUT):
        copies = {8 * b + i for b in layout.checksum.positions() for i in range(8)}
        for name, field in layout.fields.items():
            assert not copies & set(field.bits), name


def test_doubled_bytes_check():
    data = bytearray.fromhex("12003400")
    assert not PanasonicAc32Doubled().check(data)
    PanasonicAc32Doubled().apply(data)
    assert data.hex() == "12123434" and PanasonicAc32Doubled().check(data)


def test_off_carries_mode_auto_in_every_mode():
    # IRac passes mode "off"; IRPanasonicAc32::convertMode maps it to auto.
    dev = device()
    for mode in dev.capabilities.modes:
        for t in (16.0, 30.0):
            values = read(HvacState(False, mode, t))
            assert (values["mode"], values["temperature"]) == ("auto", int(t))


@pytest.mark.parametrize(
    "mode, code", [("auto", 6), ("cool", 2), ("dry", 3), ("heat", 4), ("fan", 1)]
)
def test_every_mode_uses_its_documented_value(mode, code):
    dev = device()
    high, *_ = dev.frames(None, dev.normalise(HvacState(True, mode, 22.0)), ())
    assert PANASONIC_AC32_HIGH_LAYOUT.read_raw(high.data, "mode") == code


def test_temperature_is_offset_from_15_and_clamped():
    assert read(HvacState(True, "cool", 16.0))["temperature"] == 16
    assert raw(HvacState(True, "cool", 30.0)) >> 16 & 0x0F == 15
    assert read(HvacState(True, "cool", 10.0))["temperature"] == 16
    assert read(HvacState(True, "cool", 35.0))["temperature"] == 30


@pytest.mark.parametrize(
    "fan, code", [("auto", 0xF), ("1", 2), ("2", 3), ("3", 4), ("4", 5), ("5", 6)]
)
def test_every_fan_level_uses_its_documented_value(fan, code):
    dev = device()
    high, *_ = dev.frames(
        None, dev.normalise(HvacState(True, "cool", 22.0, fan=fan)), ()
    )
    assert PANASONIC_AC32_HIGH_LAYOUT.read_raw(high.data, "fan") == code


@pytest.mark.parametrize(
    "swing, code", [("auto", 7), ("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 5)]
)
def test_swing_positions_follow_the_documented_order(swing, code):
    # Canonical "1" is the topmost documented position (kPanasonicAcSwingV
    # Highest), counting down to "5" = kPanasonicAcSwingVLowest.
    dev = device()
    _, _, low, _ = dev.frames(
        None, dev.normalise(HvacState(True, "cool", 22.0, swing_v=swing)), ()
    )
    assert PANASONIC_AC32_LOW_LAYOUT.read_raw(low.data, "swing_v") == code


def test_horizontal_swing_sets_the_swing_h_bit():
    assert read(HvacState(True, "cool", 22.0, swing_h="swing"))["swing_h"] == "swing"
    assert read(HvacState(True, "cool", 22.0))["swing_h"] == "off"


def test_power_toggle_without_previous_is_the_target_power():
    # A fresh IRac has no previous state: setPowerToggle(on).
    assert read(HvacState(True, "heat", 20.0))["power_toggle"] is True
    assert read(HvacState(False, "heat", 20.0))["power_toggle"] is False


@pytest.mark.parametrize(
    "before, after, toggle",
    [
        (True, True, False),
        (True, False, True),
        (False, False, False),
        (False, True, True),
    ],
)
def test_power_toggle_with_previous_toggles_on_change(before, after, toggle):
    # As the C path from a persistent IRac: handleToggles XORs the power
    # for PANASONIC_AC32 (checked in cpath_check.py).
    previous = HvacState(before, "cool", 22.0)
    target = HvacState(after, "cool", 22.0)
    assert read(target, previous)["power_toggle"] is toggle


def test_encode_passes_previous_to_the_toggle():
    dev = device()
    on = HvacState(True, "cool", 22.0)
    assert dev.encode(None, on).signal != dev.encode(on, on).signal


@pytest.mark.parametrize("model", PANASONIC_AC32_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("panasonic", model), PanasonicAc32Device)


@pytest.mark.parametrize("model", PANASONIC_AC32_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.panasonic import Panasonic32

    legacy = LegacyDevice("panasonic", model, Panasonic32)
    assert PanasonicAc32Device("panasonic", model).capabilities == legacy.capabilities


def test_every_panasonic32_model_is_ported():
    from pyhvac.plugins.panasonic import Panasonic32, PluginObject

    models = {m for m, cls in PluginObject.MODELS.items() if cls is Panasonic32}
    assert models == set(PANASONIC_AC32_MODELS)


@pytest.mark.parametrize(
    "key, value, field",
    [
        ("swing", "90°", "swing_v"),
        ("swing", "60°", "swing_v"),
        ("hswing", "on", "swing_h"),
    ],
)
def test_undeclared_deviation_is_reported(key, value, field):
    dev = device()
    record = next(
        r for r in load_oracle("PANASONIC_AC32") if r["state"].get(key) == value
    )
    with pytest.raises(AssertionError, match=field):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("PANASONIC_AC32")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:3], DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_panasonic_ac32_device.py -q`
Expected: collection error, `ImportError: cannot import name ...`.

- [ ] **Step 3: Implement**: insert immediately before `class PluginObject(GenPluginObject):` in `pyhvac/plugins/panasonic.py`:

```python
# ------------------------------------------------------- PanasonicAc32
# Layout from IRremoteESP8266's PanasonicAc32Protocol (ir_Panasonic.h): one
# 32-bit word. sendPanasonicAC32 sends it as two sections, the upper 16 bits
# (bytes 2 and 3) first. Each section is sent twice ("block" + repeat), and
# each byte of it is doubled on the wire: b2 b2 b3 b3, then b0 b0 b1 b1, all
# LSB first. A block has no footer mark: the next kPanasonicAc32HdrMark closes
# its last bit. The section then ends with a data-less header, a bit mark and
# kPanasonicAc32SectionGap. So the "block" footer is the repeat's header, and
# the "repeat" footer is that closing header + mark.

PANASONIC_AC32 = Protocol(
    "panasonic-ac32",
    {
        "block": Section(
            PulseDistance(920, 828, 2575),
            header=(3543, 3450),
            footer=(3543, 3450),
        ),
        "repeat": Section(
            PulseDistance(920, 828, 2575),
            footer=(3543, 3450, 920),
            gap=13946,
        ),
    },
    carrier=36700,  # kPanasonicFreq
)


@dataclass(frozen=True)
class PanasonicAc32Doubled:
    """sendPanasonicAC32 duplicates every byte: data[1] == data[0] and
    data[3] == data[2]. Not a checksum, but the same contract: the copies
    are derived from the fields, which live in bytes 0 and 2 only."""

    def positions(self):
        return {1, 3}

    def apply(self, data):
        data[1], data[3] = data[0], data[2]

    def check(self, data):
        return data[1] == data[0] and data[3] == data[2]


# The upper section, raw bytes 2 and 3 (doubled). Skeleton from
# kPanasonicAc32KnownGood (0x0AF136FC): byte 3 bits 4-7 are always 0.
PANASONIC_AC32_HIGH_LAYOUT = Layout(
    bytes.fromhex("f1f10a0a"),
    {
        "temperature": Field.at(0, 0, 4, values={t: t - 15 for t in range(16, 31)}),
        "fan": Field.at(  # kPanasonicAc32Fan*
            0,
            4,
            4,
            values={"auto": 0xF, "1": 2, "2": 3, "3": 4, "4": 5, "5": 6},
        ),
        "mode": Field.at(  # kPanasonicAc32*
            2, 0, 3, values={"fan": 1, "cool": 2, "dry": 3, "heat": 4, "auto": 6}
        ),
        # PowerToggle: 0 means toggle, 1 = keep the same.
        "power_toggle": Field.at(2, 3, 1, values={True: 0, False: 1}),
    },
    checksum=PanasonicAc32Doubled(),
)

# The lower section, raw bytes 0 and 1 (doubled). Byte 0 bits 0-2 (0b100)
# and bit 7 (1), and byte 1 (0x36), are fixed, as in kPanasonicAc32KnownGood.
PANASONIC_AC32_LOW_LAYOUT = Layout(
    bytes.fromhex("fcfc3636"),
    {
        "swing_h": Field.at(0, 3, 1, values={"off": 0, "swing": 1}),
        "swing_v": Field.at(  # kPanasonicAcSwingV*, kPanasonicAc32SwingVAuto
            0,
            4,
            3,
            values={"1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "auto": 7},
        ),
    },
    checksum=PanasonicAc32Doubled(),
)


class PanasonicAc32Device(Device):
    """Panasonic 32-bit (CS-E9CKP, A75C2295): full state, except that the
    power bit is a toggle.

    With ``previous`` the toggle is sent only when the power changes, which
    is also what the C path does from a persistent IRac object
    (IRac::handleToggles XORs the power for PANASONIC_AC32). Without
    ``previous`` the toggle is ``target.power``, as from a fresh IRac: an
    "on" toggles, an "off" toggles nothing.
    """

    PROTOCOL = PANASONIC_AC32
    LAYOUTS = (
        PANASONIC_AC32_HIGH_LAYOUT,
        PANASONIC_AC32_HIGH_LAYOUT,
        PANASONIC_AC32_LOW_LAYOUT,
        PANASONIC_AC32_LOW_LAYOUT,
    )
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "heat", "fan"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=Choice(
            ("auto", "1", "2", "3", "4", "5"),
            {
                "auto": "auto",
                "1": "lowest",
                "2": "low",
                "3": "medium",
                "4": "high",
                "5": "highest",
            },
        ),
        swing_v=Choice(
            ("auto", "1", "2", "3", "4", "5"),
            {"auto": "auto", "1": "90°", "2": "60°", "3": "45°", "4": "30°", "5": "0°"},
        ),
        swing_h=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
    )

    def frames(self, previous, target, actions):
        if previous is None:
            toggle = target.power
        else:
            toggle = target.power != previous.power
        high = PANASONIC_AC32_HIGH_LAYOUT.build(
            temperature=int(target.temperature),
            fan=target.fan,
            # As the C path: an off message carries mode auto (IRac passes
            # mode "off", which convertMode maps to kPanasonicAc32Auto).
            mode=target.mode if target.power else "auto",
            power_toggle=toggle,
        )
        low = PANASONIC_AC32_LOW_LAYOUT.build(
            swing_h=target.swing_h, swing_v=target.swing_v
        )
        return [
            Frame("block", bytes(high)),
            Frame("repeat", bytes(high)),
            Frame("block", bytes(low)),
            Frame("repeat", bytes(low)),
        ]


PANASONIC_AC32_MODELS = ("CS-E9CKP series", "A75C2295remote", "generic 32")


DEVICES.update({m: PanasonicAc32Device for m in PANASONIC_AC32_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_panasonic_ac32_device.py -q`
Expected: 241 passed, 3 skipped.

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/panasonic.py tests/test_panasonic_ac32_device.py
git add pyhvac/plugins/panasonic.py tests/test_panasonic_ac32_device.py
git commit -m "PANASONIC_AC32: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 6: SANYO_AC

One 72-bit frame, `NibbleSum(0, 8, 8)`; layout from `SanyoProtocol`.

**Files:**
- Modify: `pyhvac/plugins/sanyo.py` (block before `# Now the match between models and objects`)
- Test: `tests/test_sanyo_ac_device.py`

- [ ] **Step 1: Write the failing tests**: create `tests/test_sanyo_ac_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.ir.codec import decode
from pyhvac.plugins.sanyo import (
    SANYO_AC,
    SANYO_AC_LAYOUT,
    SANYO_AC_MODELS,
    SanyoAcDevice,
)
from pyhvac.state import HvacState

# The C path deviates from the documented SanyoProtocol values here:
# - swing "90°"/"60°" (canonical "1"/"2"): IRGHVAC.trans_swing maps them to
#   kHigh and kUpperMiddle; IRSanyoAc::convertSwingV sends kHigh as
#   kSanyoAcSwingVHigh (6) and has no kUpperMiddle case, so it sends
#   kSanyoAcSwingVAuto (0). The port counts the documented positions from
#   the top: Highest (7), High (6);
# - sleep: IRGHVAC.build_ircode's key map has no "sleep", so IRac's sleep
#   stays -1 and IRac::sanyo's setSleep(sleep >= 0) never sets Sleep
#   (byte 6 bit 3).
SWING_HIGHEST = Defect("swing_v", "1", "2", "glue sends kHigh for 90°")
SWING_HIGH = Defect("swing_v", "2", "auto", "convertSwingV: no kUpperMiddle")
SLEEP = Defect("sleep", 1, 0, "legacy glue never passes sleep")
DEFECTS = (SWING_HIGHEST, SWING_HIGH, SLEEP)

# ir_Sanyo_test.cpp, DecodeRealExamples ("On", issue #1211): power on,
# cool, 21 C, fan auto, swing Upper Middle, beep on, sensor wall, sensor
# temperature 11 C.
REAL_EXAMPLE = bytes.fromhex("6a7147002085000032")


def device(model="generic"):
    return SanyoAcDevice("sanyo", model)


def frame(state, previous=None):
    dev = device()
    if previous is not None:
        previous = dev.normalise(previous)
    (main,) = dev.frames(previous, dev.normalise(state), ())
    return main.data


def read(state, previous=None):
    return SANYO_AC_LAYOUT.read(frame(state, previous))


@pytest.mark.parametrize("record", oracle_params("SANYO_AC"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("SANYO_AC"):
        state = state_from_record(dev, record["state"])
        (main,) = dev.frames(None, state, ())
        values = SANYO_AC_LAYOUT.read(main.data)
        assert SANYO_AC_LAYOUT.build(**values) == bytearray(main.data)


def test_every_oracle_frame_has_the_nibble_sum_and_the_fixed_bits():
    for record in load_oracle("SANYO_AC"):
        (main,) = decode(SANYO_AC, record["pulses"], expected=["main"])
        assert SANYO_AC_LAYOUT.checksum.check(main.data)
        assert main.data[0] == 0x6A
        assert main.data[1] >> 5 == 0b011  # byte 1 bits 5-7, as kReset


def test_the_real_capture_differs_only_by_what_the_entity_cannot_express():
    # The remote reported its own sensor temperature (11 C) with beep on and
    # the wall sensor; IRac sends the setpoint as the sensor temperature,
    # beep off and the A/C sensor. Everything else is the capture.
    ours = frame(HvacState(True, "cool", 21.0, fan="auto", swing_v="3"))
    theirs = SANYO_AC_LAYOUT.read(REAL_EXAMPLE)
    assert SANYO_AC_LAYOUT.read(ours) == {
        **theirs,
        "sensor_temp": 21 - 4,
        "beep": 0,
        "sensor": 1,
    }
    patched = bytearray(ours)
    for name in ("sensor_temp", "beep", "sensor"):
        SANYO_AC_LAYOUT.write_raw(
            patched, name, SANYO_AC_LAYOUT.read_raw(REAL_EXAMPLE, name)
        )
    SANYO_AC_LAYOUT.checksum.apply(patched)
    assert bytes(patched) == REAL_EXAMPLE


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat"])
@pytest.mark.parametrize("t", [16.0, 30.0])
def test_off_carries_mode_auto_and_power_off_in_every_mode(mode, t):
    # IRac passes mode "off"; convertMode maps it to kSanyoAcAuto, and
    # setPower(false) writes kSanyoAcPowerOff (0b01).
    values = read(HvacState(False, mode, t))
    assert (values["power"], values["mode"], values["temp"]) == (1, "auto", t - 4)


@pytest.mark.parametrize(
    "mode, raw", [("auto", 4), ("cool", 2), ("dry", 3), ("heat", 1)]
)
def test_mode_codes_and_the_setpoint_in_every_mode(mode, raw):
    for t in (16.0, 23.0, 30.0):
        data = frame(HvacState(True, mode, t))
        values = SANYO_AC_LAYOUT.read(data)
        assert SANYO_AC_LAYOUT.read_raw(data, "mode") == raw
        assert (values["power"], values["temp"]) == (2, t - 4)


def test_setpoint_is_clamped_to_16_30():
    assert read(HvacState(True, "cool", 10.0))["temp"] == 16 - 4
    assert read(HvacState(True, "cool", 40.0))["temp"] == 30 - 4


@pytest.mark.parametrize("t", [16.0, 23.0, 30.0])
def test_sensor_temperature_is_the_setpoint_from_the_ac_sensor(t):
    # IRac::sanyo: no sensor reading -> setSensorTemp(degrees);
    # setSensor(!iFeel) with iFeel off; beep and the off timer stay off.
    values = read(HvacState(True, "heat", t))
    assert values["sensor_temp"] == values["temp"] == t - 4
    assert (values["sensor"], values["beep"]) == (1, 0)
    assert (values["off_timer"], values["off_hour"]) == (0, 0)


@pytest.mark.parametrize("fan, raw", [("auto", 0), ("1", 2), ("2", 3), ("3", 1)])
def test_every_fan_level(fan, raw):
    data = frame(HvacState(True, "cool", 22.0, fan=fan))
    assert SANYO_AC_LAYOUT.read_raw(data, "fan") == raw


@pytest.mark.parametrize(
    "swing_v, raw",
    [("auto", 0), ("1", 7), ("2", 6), ("3", 5), ("4", 3), ("5", 2)],
)
def test_every_swing_v_value(swing_v, raw):
    data = frame(HvacState(True, "cool", 22.0, swing_v=swing_v))
    assert SANYO_AC_LAYOUT.read_raw(data, "swing_v") == raw


@pytest.mark.parametrize("power", [True, False])
def test_sleep_bit(power):
    assert read(HvacState(power, "cool", 22.0))["sleep"] == 0
    values = read(HvacState(power, "cool", 22.0, features={"sleep": True}))
    assert values["sleep"] == 1


def test_previous_is_ignored():
    dev = device()
    on = HvacState(True, "cool", 22.0, swing_v="1", features={"sleep": True})
    off = HvacState(False, "heat", 30.0)
    assert dev.encode(off, on).signal == dev.encode(None, on).signal
    assert dev.encode(on, on).signal == dev.encode(None, on).signal
    assert dev.encode(on, off).signal == dev.encode(None, off).signal


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (8500, 4200)
    assert pulses[-2:] == (500, 100000)
    assert len(pulses) == 2 + 2 * 72 + 2


@pytest.mark.parametrize("model", SANYO_AC_MODELS)
def test_registry_serves_the_port(model):
    dev = registry.get_device("sanyo", model)
    assert isinstance(dev, SanyoAcDevice)


@pytest.mark.parametrize("model", SANYO_AC_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.sanyo import Sanyo

    legacy = LegacyDevice("sanyo", model, Sanyo)
    assert device(model).capabilities == legacy.capabilities


@pytest.mark.parametrize(
    "select, defect, field",
    [
        (lambda s: s.get("swing") == "90°", SWING_HIGHEST, "swing_v"),
        (lambda s: s.get("swing") == "60°", SWING_HIGH, "swing_v"),
        (lambda s: s.get("sleep") == "on", SLEEP, "sleep"),
    ],
)
def test_undeclared_deviation_is_reported(select, defect, field):
    dev = device()
    record = next(r for r in load_oracle("SANYO_AC") if select(r["state"]))
    others = tuple(d for d in DEFECTS if d != defect)
    with pytest.raises(AssertionError, match=field):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=others)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_sanyo_ac_device.py -q`
Expected: collection error, `ImportError: cannot import name ...`.

- [ ] **Step 3: Implement**: insert immediately before `# Now the match between models and objects` in `pyhvac/plugins/sanyo.py`:

```python
# ---------------------------------------------------------------- SanyoAc
# Layout from IRremoteESP8266's SanyoProtocol (ir_Sanyo.h): 9 bytes, one
# frame sent LSB first (sendSanyoAc -> sendGeneric with MSBfirst false, at
# kSanyoAcFreq), closed by the sum of every nibble of bytes 0-7
# (IRSanyoAc::calcChecksum: sumNibbles over length - 1 bytes).

SANYO_AC = Protocol(
    "sanyo_ac",
    {
        "main": Section(
            # kSanyoAcBitMark / ZeroSpace / OneSpace
            PulseDistance(500, 550, 1600),
            header=(8500, 4200),  # kSanyoAcHdrMark / HdrSpace
            footer=(500,),
            gap=100000,  # kSanyoAcGap (kDefaultMessageGap)
        ),
    },
    carrier=38000,  # kSanyoAcFreq
)

SANYO_AC_MODE = {  # kSanyoAc{Heat,Cool,Dry,Auto}
    "heat": 1,
    "cool": 2,
    "dry": 3,
    "auto": 4,
}
SANYO_AC_FAN = {  # canonical fan -> kSanyoAcFan*
    "auto": 0,  # kSanyoAcFanAuto
    "1": 2,  # low: kSanyoAcFanLow
    "2": 3,  # medium: kSanyoAcFanMedium
    "3": 1,  # high: kSanyoAcFanHigh
}
SANYO_AC_SWING_V = {  # canonical swing_v -> kSanyoAcSwingV*
    "auto": 0,  # kSanyoAcSwingVAuto
    "1": 7,  # 90°: kSanyoAcSwingVHighest (topmost, counting down)
    "2": 6,  # 60°: kSanyoAcSwingVHigh
    "3": 5,  # 45°: kSanyoAcSwingVUpperMiddle, as C
    "4": 3,  # 30°: kSanyoAcSwingVLow, as C
    "5": 2,  # 0°: kSanyoAcSwingVLowest, as C
}
SANYO_AC_POWER_OFF, SANYO_AC_POWER_ON = 0b01, 0b10  # kSanyoAcPowerOff / On
SANYO_AC_MIN_TEMP, SANYO_AC_MAX_TEMP = 16, 30  # kSanyoAcTempMin / Max
SANYO_AC_TEMP_DELTA = 4  # kSanyoAcTempDelta: native = degrees - 4

# Skeleton: IRSanyoAc::stateReset (kReset; memcpy writes all 9 bytes, so
# nothing comes from stale memory) with the named fields cleared. Byte 0 is
# the fixed 0x6A, byte 1 bits 5-7 stay 0b011 as in kReset and the issue
# #1211 capture (0x71).
SANYO_AC_LAYOUT = Layout(
    bytes.fromhex("6a6000000000000000"),
    {
        "temp": Field.at(1, 0, 5),  # °C - kSanyoAcTempDelta
        "sensor_temp": Field.at(2, 0, 5),  # °C - kSanyoAcTempDelta
        "sensor": Field.at(2, 5, 1),  # 0 = remote (wall), 1 = A/C (room)
        "beep": Field.at(2, 6, 1),
        "off_hour": Field.at(3, 0, 4),
        "fan": Field.at(4, 0, 2, values=SANYO_AC_FAN),
        "off_timer": Field.at(4, 2, 1),
        "mode": Field.at(4, 4, 3, values=SANYO_AC_MODE),
        "swing_v": Field.at(5, 0, 3, values=SANYO_AC_SWING_V),
        "power": Field.at(5, 6, 2),
        "sleep": Field.at(6, 3, 1),
    },
    checksum=NibbleSum(0, 8, 8),
)


class SanyoAcDevice(Device):
    """Sanyo 72-bit A/C (SAP-K121AHA, RCS-2HS4E, SAP-K242AH, RCS-2S4E): a
    full-state protocol with no toggle bits, ``previous`` is ignored.

    As the C path (IRac::sanyo, fed by the legacy glue): an off message
    carries mode auto (IRac passes mode "off", convertMode's default) and
    kSanyoAcPowerOff; the setpoint is whole degrees clamped to 16-30; the
    sensor temperature is the setpoint (IRac has no sensor reading and uses
    the desired temperature); the sensor is the A/C's own (setSensor(!iFeel),
    iFeel off); beep is off (the glue never sets it); the off timer is off.

    Two documented values differ from the C output (declared Defects):
    - swing_v "1" (90°) and "2" (60°): the old glue maps them to kHigh and
      kUpperMiddle, which convertSwingV sends as High and Auto; the port
      sends the documented Highest and High. 45°, 30° and 0° keep C's
      UpperMiddle, Low and Lowest (LowerMiddle is not reachable);
    - sleep: the old glue never passes sleep, so setSleep(sleep >= 0) never
      sets the Sleep bit; the port sets it.
    """

    PROTOCOL = SANYO_AC
    LAYOUTS = (SANYO_AC_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "heat"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
        ),
        swing_v=Choice(
            ("auto", "1", "2", "3", "4", "5"),
            {
                "auto": "auto",
                "1": "90°",
                "2": "60°",
                "3": "45°",
                "4": "30°",
                "5": "0°",
            },
        ),
        features={"sleep": Choice((False, True), {False: "off", True: "on"})},
    )

    def frames(self, previous, target, actions):
        degrees = min(
            max(int(target.temperature), SANYO_AC_MIN_TEMP), SANYO_AC_MAX_TEMP
        )
        native = degrees - SANYO_AC_TEMP_DELTA
        data = SANYO_AC_LAYOUT.build(
            temp=native,
            sensor_temp=native,
            sensor=1,
            beep=0,
            off_hour=0,
            fan=target.fan,
            off_timer=0,
            mode=target.mode if target.power else "auto",
            swing_v=target.swing_v,
            power=SANYO_AC_POWER_ON if target.power else SANYO_AC_POWER_OFF,
            sleep=target.features["sleep"],
        )
        return [Frame("main", bytes(data))]


SANYO_AC_MODELS = (
    "SAP-K121AHA",
    "RCS-2HS4E remote",
    "SAP-K242AH",
    "RCS-2S4E remote",
    "generic",
)


DEVICES.update({m: SanyoAcDevice for m in SANYO_AC_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_sanyo_ac_device.py -q`
Expected: 241 passed, 5 skipped.

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/sanyo.py tests/test_sanyo_ac_device.py
git add pyhvac/plugins/sanyo.py tests/test_sanyo_ac_device.py
git commit -m "SANYO_AC: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 7: SANYO_AC88

One 11-byte frame sent 3 times, then a bitless 100 ms end section; layout from `SanyoAc88Protocol`.

**Files:**
- Modify: `pyhvac/plugins/sanyo.py` (block before `# Now the match between models and objects`)
- Test: `tests/test_sanyo_ac88_device.py`

- [ ] **Step 1: Write the failing tests**: create `tests/test_sanyo_ac88_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.sanyo import (
    SANYO_AC88_LAYOUT,
    SANYO_AC88_MODELS,
    SanyoAc88Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented SanyoAc88 values here (pyhvac's
# glue, not IRremoteESP8266):
# - IRGHVAC.trans_swing has no "on" key, so IRac keeps swingv at kOff and
#   IRac::sanyo88 calls setSwingV(false). The port sends SwingV = 1.
# - IRGHVAC.build_ircode's key map has no "sleep", so IRac keeps sleep at -1
#   and IRac::sanyo88 calls setSleep(false). The port sends Sleep = 1.
SWING = Defect("swing_v", "swing", "off", "C path drops swing 'on' (SwingV)")
SLEEP = Defect("sleep", 1, 0, "C path drops sleep (IRSanyoAc88::setSleep)")
DEFECTS = (SWING, SLEEP)

# ir_Sanyo_test.cpp, DecodeRealExamples ("On", issue 1503): cool, 24 C, fan
# auto, clock 18:42:06. Bytes 1, 7 and 10 are 0x59, 0x00 and 0x80 in the
# capture, where stateReset (and so the C path) has 0x55, 0x01 and 0x10.
REAL_CAPTURE = bytes.fromhex("aa59a018062a1200000080")


def wire(record):
    """``record`` with the pulses the C library puts on the wire.

    sendSanyoAc88 ends with space(kSanyoAc88Gap) then space(kDefaultMessageGap).
    IRac's timing log keeps them as two entries, so the fixture's last entry
    (100 000 µs) sits at a mark position; IRremoteESP8266's own
    SyntheticSelfDecode test shows them merged ("m500s103675").
    """
    pulses = record["pulses"]
    assert len(pulses) % 2 and pulses[-2:] == [3675, 100000]
    return {**record, "pulses": pulses[:-2] + [3675 + 100000]}


def device(model="generic 88"):
    return SanyoAc88Device("sanyo", model)


def frames(state):
    dev = device()
    return dev.frames(None, dev.normalise(state), ())


def read(state):
    return SANYO_AC88_LAYOUT.read(frames(state)[0].data)


def raw(state, field):
    return SANYO_AC88_LAYOUT.read_raw(frames(state)[0].data, field)


@pytest.mark.parametrize("record", oracle_params("SANYO_AC88"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, wire(record), dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("SANYO_AC88"):
        state = state_from_record(dev, record["state"])
        *mains, end = dev.frames(None, state, ())
        assert (end.section, end.data, end.nbits) == ("end", b"", 0)
        assert len(mains) == 3 and len({f.data for f in mains}) == 1
        values = SANYO_AC88_LAYOUT.read(mains[0].data)
        assert SANYO_AC88_LAYOUT.build(**values) == bytearray(mains[0].data)


def test_the_real_capture_reads_as_documented():
    assert SANYO_AC88_LAYOUT.read(REAL_CAPTURE) == {
        "fan": "auto",
        "mode": "cool",
        "power": 1,
        "temperature": 24,
        "filter": 0,
        "swing_v": "off",
        "clock_secs": 6,
        "clock_mins": 42,
        "clock_hours": 18,
        "turbo": 0,
        "start_timer": 0,
        "stop_timer": 0,
        "sleep": 0,
    }


def test_the_real_capture_differs_only_where_the_c_path_does():
    # The clock (never set by IRac) and bytes 1, 7 and 10 (stateReset's 0x55,
    # 0x01 and 0x10) are the only differences.
    frame, *_ = frames(HvacState(True, "cool", 24.0))
    capture = bytearray(REAL_CAPTURE)
    for name in ("clock_secs", "clock_mins", "clock_hours"):
        SANYO_AC88_LAYOUT.write_raw(capture, name, 0)
    capture[1], capture[7], capture[10] = 0x55, 0x01, 0x10
    assert frame.data == bytes(capture)


@pytest.mark.parametrize("mode", ["auto", "cool", "heat", "fan"])
@pytest.mark.parametrize("temperature", [10.0, 20.0, 30.0])
def test_off_carries_mode_auto(mode, temperature):
    # IRac passes mode "off"; convertMode maps it to kSanyoAc88Auto.
    values = read(HvacState(False, mode, temperature))
    assert (values["power"], values["mode"], values["temperature"]) == (
        0,
        "auto",
        int(temperature),
    )


def test_mode_codes():
    for mode, code in (("auto", 0), ("cool", 2), ("heat", 4), ("fan", 5)):
        assert raw(HvacState(True, mode, 22.0), "mode") == code


@pytest.mark.parametrize("mode", ["auto", "cool", "heat", "fan"])
def test_setpoint_is_whole_degrees_clamped_to_10_30(mode):
    assert read(HvacState(True, mode, 5.0))["temperature"] == 10
    assert read(HvacState(True, mode, 21.0))["temperature"] == 21
    assert read(HvacState(True, mode, 21.5))["temperature"] == 21
    assert read(HvacState(True, mode, 40.0))["temperature"] == 30


@pytest.mark.parametrize(
    "fan, code", [("auto", 0), ("1", 1), ("2", 2), ("3", 3), ("4", 3)]
)
def test_fan_codes_as_convert_fan(fan, code):
    # convertFan: kMin and kLow -> FanLow, kHigh and kMax -> FanHigh.
    assert raw(HvacState(True, "cool", 22.0, fan=fan), "fan") == code


@pytest.mark.parametrize(
    "feature, field",
    [("powerful", "turbo"), ("purifier", "filter"), ("sleep", "sleep")],
)
def test_each_feature_sets_its_bit_only(feature, field):
    base = read(HvacState(True, "cool", 22.0))
    on = read(HvacState(True, "cool", 22.0, features={feature: True}))
    assert (base[field], on[field]) == (0, 1)
    assert {k: v for k, v in on.items() if k != field} == {
        k: v for k, v in base.items() if k != field
    }


def test_features_combine():
    feats = {"powerful": True, "purifier": True, "sleep": True}
    values = read(
        HvacState(True, "heat", 26.0, fan="2", swing_v="swing", features=feats)
    )
    assert (values["turbo"], values["filter"], values["sleep"]) == (1, 1, 1)
    assert (values["swing_v"], values["fan"], values["mode"]) == ("swing", "2", "heat")


def test_swing_sends_the_documented_bit():
    assert raw(HvacState(True, "cool", 22.0, swing_v="swing"), "swing_v") == 1
    assert raw(HvacState(True, "cool", 22.0, swing_v="off"), "swing_v") == 0


def test_start_timer_bit_stays_set_as_state_reset():
    assert read(HvacState(True, "cool", 22.0))["start_timer"] == 1


def test_previous_is_ignored():
    dev = device()
    on = HvacState(True, "cool", 22.0, swing_v="swing")
    off = HvacState(False, "heat", 30.0)
    assert dev.encode(off, on).signal == dev.encode(None, on).signal
    assert dev.encode(on, on).signal == dev.encode(None, on).signal


def test_message_shape():
    signal = device().encode(None, HvacState(True, "cool", 22.0)).signal
    assert signal.carrier == 38000
    pulses = signal.pulses
    per_frame = 2 + 2 * 88 + 2
    assert len(pulses) == 3 * per_frame
    for n in range(3):
        start = n * per_frame
        assert pulses[start : start + 2] == (5400, 2000)
        assert pulses[start + 2 : start + 4] == (500, 750)  # 0xAA LSB first
        assert pulses[start + 4 : start + 6] == (500, 1500)
    assert pulses[per_frame - 2 : per_frame] == (500, 3675)
    assert pulses[-2:] == (500, 103675)


def test_the_fixture_ends_on_unmerged_spaces():
    for record in load_oracle("SANYO_AC88"):
        assert len(record["pulses"]) == 3 * (2 + 2 * 88 + 2) + 1
        assert record["pulses"][-2:] == [3675, 100000]


def test_registry_serves_the_port():
    for model in SANYO_AC88_MODELS:
        assert isinstance(registry.get_device("sanyo", model), SanyoAc88Device)


def test_capabilities_match_the_legacy_entity():
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.sanyo import Sanyo88

    for model in SANYO_AC88_MODELS:
        legacy = LegacyDevice("sanyo", model, Sanyo88)
        assert device(model).capabilities == legacy.capabilities


def _record(**state):
    return next(
        r
        for r in load_oracle("SANYO_AC88")
        if all(r["state"].get(k) == v for k, v in state.items())
    )


@pytest.mark.parametrize(
    "state, defect",
    [
        ({"mode": "cool", "fan": "medium", "swing": "on"}, SWING),
        ({"mode": "auto", "sleep": "on"}, SLEEP),
    ],
)
def test_undeclared_deviation_is_reported(state, defect):
    dev = device()
    record = wire(_record(**state))
    assert_matches_oracle(dev, record, dev.LAYOUTS, (defect,))
    others = tuple(d for d in DEFECTS if d is not defect)
    with pytest.raises(AssertionError, match=f"'{defect.field}'"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=others)


def test_layouts_must_cover_every_frame():
    dev = device()
    record = wire(_record(mode="cool", fan="medium", swing="on"))
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:3], DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_sanyo_ac88_device.py -q`
Expected: collection error, `ImportError: cannot import name ...`.

- [ ] **Step 3: Implement**: insert immediately before `# Now the match between models and objects` in `pyhvac/plugins/sanyo.py`:

```python
# ----------------------------------------------------------------- SanyoAc88
# Layout from IRremoteESP8266's SanyoAc88Protocol (ir_Sanyo.h): 11 bytes sent
# LSB first (sendSanyoAc88: sendGeneric with MSBfirst false), no checksum.
# IRSanyoAc88::send sends the message kSanyoAc88MinRepeat + 1 = 3 times, each
# closed by kSanyoAc88BitMark and kSanyoAc88Gap, then adds a
# kDefaultMessageGap space: the wire ends on 500 µs mark + 103 675 µs space
# (as ir_Sanyo_test.cpp's SyntheticSelfDecode shows). stateReset writes every
# byte, so no bit is left to stale memory.

SANYO_AC88 = Protocol(
    "sanyo-ac88",
    {
        "main": Section(
            # kSanyoAc88BitMark / ZeroSpace / OneSpace
            PulseDistance(500, 750, 1500),
            header=(5400, 2000),  # kSanyoAc88HdrMark / HdrSpace
            footer=(500,),
            gap=3675,  # kSanyoAc88Gap
        ),
        # sendSanyoAc88: space(kDefaultMessageGap) after the last repeat.
        "end": Section(None, gap=100000),
    },
    carrier=38000,  # kSanyoAc88Freq
)

SANYO_AC88_MODE = {  # kSanyoAc88{Auto,Cool,Heat,Fan}
    "auto": 0,
    "cool": 2,
    "heat": 4,
    "fan": 5,
}
SANYO_AC88_FAN = {  # canonical fan -> kSanyoAc88Fan*, as convertFan
    "auto": 0,  # FanAuto
    "1": 1,  # lowest (kMin): FanLow
    "2": 2,  # medium: FanMedium
    "3": 3,  # high: FanHigh
    "4": 3,  # highest (kMax): FanHigh, the protocol has no faster speed
}
SANYO_AC88_SWING = {"off": 0, "swing": 1}  # SwingV

# Skeleton: IRSanyoAc88::stateReset (kReset) with Power, Mode, Fan and Temp
# cleared: bytes 0-1 0xAA 0x55, byte 7 0x01, EnableStartTimer (byte 10 bit 4)
# set, the clock (bytes 4-6) zero, as IRac never calls setClock (clock -1).
# The one real capture (ir_Sanyo_test.cpp, issue 1503) has 0x59, 0x00 and
# 0x80 in bytes 1, 7 and 10: undocumented bits, so the port follows C.
SANYO_AC88_LAYOUT = Layout(
    bytes.fromhex("aa550000000000010000" "10"),
    {
        "fan": Field.at(2, 0, 2, values=SANYO_AC88_FAN),
        "mode": Field.at(2, 4, 3, values=SANYO_AC88_MODE),
        "power": Field.at(2, 7, 1),
        "temperature": Field.at(3, 0, 5),  # whole °C, 10-30
        "filter": Field.at(3, 5, 1),
        "swing_v": Field.at(3, 6, 1, values=SANYO_AC88_SWING),
        "clock_secs": Field.at(4, 0, 8),
        "clock_mins": Field.at(5, 0, 8),
        "clock_hours": Field.at(6, 0, 8),
        "turbo": Field.at(10, 3, 1),
        "start_timer": Field.at(10, 4, 1),  # EnableStartTimer
        "stop_timer": Field.at(10, 5, 1),  # EnableStopTimer
        "sleep": Field.at(10, 6, 1),
    },
)


class SanyoAc88Device(Device):
    """Sanyo 88-bit: a full-state protocol with an explicit power bit and no
    toggles, so ``previous`` is ignored. The frame is sent three times.

    As the C path: an off message carries mode auto; fan high and highest
    both send FanHigh; the EnableStartTimer bit of stateReset stays set.
    Swing "on" and sleep send the documented SwingV and Sleep bits; the
    C path of the oracle fixtures never received them (pyhvac's glue).
    """

    PROTOCOL = SANYO_AC88
    LAYOUTS = (SANYO_AC88_LAYOUT,) * 3 + (None,)
    capabilities = Capabilities(
        modes=("auto", "cool", "heat", "fan"),
        temperature=TemperatureRange(10.0, 30.0),
        fan=Choice(
            ("auto", "1", "2", "3", "4"),
            {"auto": "auto", "1": "lowest", "2": "medium", "3": "high", "4": "highest"},
        ),
        swing_v=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
        features={
            name: Choice((False, True), {False: "off", True: "on"})
            for name in ("powerful", "purifier", "sleep")
        },
    )

    def frames(self, previous, target, actions):
        feat = target.features
        data = bytes(
            SANYO_AC88_LAYOUT.build(
                power=target.power,
                # As the C path: IRac passes mode "off" for an off message,
                # which convertMode maps to kSanyoAc88Auto.
                mode=target.mode if target.power else "auto",
                # setTemp clamps to kSanyoAc88TempMin-Max, whole degrees.
                temperature=int(target.temperature),
                fan=target.fan,
                swing_v=target.swing_v,
                turbo=feat["powerful"],
                filter=feat["purifier"],
                sleep=feat["sleep"],
            )
        )
        return [Frame("main", data)] * 3 + [Frame("end", b"", 0)]


SANYO_AC88_MODELS = ("generic 88",)


DEVICES.update({m: SanyoAc88Device for m in SANYO_AC88_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_sanyo_ac88_device.py -q`
Expected: 191 passed, 1 skipped.

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/sanyo.py tests/test_sanyo_ac88_device.py
git add pyhvac/plugins/sanyo.py tests/test_sanyo_ac88_device.py
git commit -m "SANYO_AC88: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 8: KELON

One 48-bit frame, no checksum; power TOGGLE (with previous: toggle on change, as IRac::handleToggles); off messages carry the target mode.

**Files:**
- Modify: `pyhvac/plugins/kelon.py` (block before `# Now the match between models and objects`)
- Test: `tests/test_kelon_device.py`

- [ ] **Step 1: Write the failing tests**: create `tests/test_kelon_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.kelon import KELON_LAYOUT, KELON_MODELS, KelonDevice
from pyhvac.state import HvacState

# The C path deviates from the documented Kelon values here:
# - IRac::kelon calls setSupercool(false) after setMode; its else branch calls
#   setMode(_previousMode), and _previousMode is kKelonModeHeat (0) from
#   stateReset, so every C message is mode heat. That includes off messages
#   (convertMode maps them to kKelonModeSmart, 26C), which carry the target
#   mode in the port. Oracle off records read as mode auto, so they are
#   covered by the auto entry.
# - the legacy glue (IRGHVAC.build_ircode) has no "sleep" key, so IRac gets
#   sleep -1 and setSleep(sleep >= 0) always clears SleepEnabled.
DEFECTS = (
    Defect("mode", "auto", "heat", "setSupercool(false) reverts to heat"),
    Defect("mode", "cool", "heat", "setSupercool(false) reverts to heat"),
    Defect("mode", "dry", "heat", "setSupercool(false) reverts to heat"),
    Defect("mode", "fan", "heat", "setSupercool(false) reverts to heat"),
    Defect("sleep", 1, 0, "legacy glue never passes sleep"),
)


def device():
    return KelonDevice("kelon", "remote")


def state(power=True, mode="cool", temperature=22.0, **kw):
    return device().normalise(HvacState(power, mode, temperature, **kw))


def read(target, previous=None):
    (main,) = device().frames(previous, target, ())
    return KELON_LAYOUT.read(main.data)


@pytest.mark.parametrize("record", oracle_params("KELON"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("KELON"):
        (main,) = dev.frames(None, state_from_record(dev, record["state"]), ())
        values = KELON_LAYOUT.read(main.data)
        assert KELON_LAYOUT.build(**values) == bytearray(main.data)


@pytest.mark.parametrize(
    "raw, fields",
    [
        # ir_Kelon_test.cpp: 26C cool auto; 23C heat with power toggle;
        # dry with swing toggle (26C); dry at grade -2.
        (0x82000683, {"mode": "cool", "temperature": 26, "fan": "auto"}),
        (0x50040683, {"mode": "heat", "temperature": 23, "power_toggle": 1}),
        (0x83800683, {"mode": "dry", "temperature": 26, "swing_toggle": 1}),
        (0x83600683, {"mode": "dry", "dry_grade": 0b110}),
        # Timer12HSmartMode: smart mode, SmartModeEnabled clear, 12 h timer.
        (
            0x1679030683,
            {"mode": "auto", "smart": 0, "timer": 1, "timer_hours": 11, "fan": "1"},
        ),
        # SendDataOnly: 18C cool, super cool (both bits), raw fan 1 (max).
        (0x900002010683, {"super_cool1": 1, "super_cool2": 1, "fan": "3"}),
        # Timer5_5hSuperCoolMode: only SuperCoolEnabled1 is set here.
        (0x100B0A010683, {"super_cool1": 1, "super_cool2": 0, "timer_hours": 5}),
    ],
)
def test_layout_reads_the_real_captures(raw, fields):
    data = raw.to_bytes(6, "little")
    values = KELON_LAYOUT.read(data)
    assert {k: values[k] for k in fields} == fields
    assert KELON_LAYOUT.build(**values) == bytearray(data)


def test_port_reproduces_the_cool_capture():
    # 0x82000683: 26C, cool, fan auto, no toggle (a change while on).
    on = state(True, "cool", 26.0)
    (main,) = device().frames(on, on, ())
    assert main.data == (0x82000683).to_bytes(6, "little")


def test_port_reproduces_the_heat_power_toggle_capture():
    # 0x50040683: 23C, heat, fan auto, power toggle.
    (main,) = device().frames(None, state(True, "heat", 23.0), ())
    assert main.data == (0x50040683).to_bytes(6, "little")


@pytest.mark.parametrize("mode", ["cool", "heat"])
@pytest.mark.parametrize("t", [18.0, 25.0, 32.0])
def test_setpoint_is_sent_in_cool_and_heat(mode, t):
    assert read(state(True, mode, t))["temperature"] == int(t)


@pytest.mark.parametrize("mode, fixed", [("auto", 26), ("dry", 25), ("fan", 25)])
@pytest.mark.parametrize("t", [18.0, 25.0, 32.0])
def test_setmode_forces_the_temperature(mode, fixed, t):
    # IRKelonAc::setMode forces 26C (smart) and 25C (dry, fan); C sends it.
    assert read(state(True, mode, t))["temperature"] == fixed


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan", "heat"])
@pytest.mark.parametrize("t", [18.0, 32.0])
def test_off_carries_the_target_mode_and_its_temperature(mode, t):
    # Ruling: not kKelonModeSmart (convertMode's "off"), which would risk
    # switching the unit on; the same temperature rules as when powered.
    values = read(state(False, mode, t))
    expected = {"auto": 26, "dry": 25, "fan": 25}.get(mode, int(t))
    assert (values["mode"], values["temperature"]) == (mode, expected)
    assert values["power_toggle"] == 0


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan", "heat"])
def test_mode_uses_its_documented_value(mode):
    codes = {"heat": 0, "auto": 1, "cool": 2, "dry": 3, "fan": 4}
    (main,) = device().frames(None, state(True, mode), ())
    assert KELON_LAYOUT.read_raw(main.data, "mode") == codes[mode]


def test_smart_bit_stays_clear():
    # As the C output and the real smart mode capture 0x1679030683.
    for power in (True, False):
        assert read(state(power, "auto"))["smart"] == 0


@pytest.mark.parametrize("fan, raw", [("auto", 0), ("1", 3), ("2", 2), ("3", 1)])
def test_every_fan_level_uses_its_documented_raw_code(fan, raw):
    # The header: raw 0 auto, 1 max, 2 medium, 3 min.
    (main,) = device().frames(None, state(fan=fan), ())
    assert KELON_LAYOUT.read_raw(main.data, "fan") == raw


def test_sleep_sets_the_sleep_bit():
    on = state(features={"sleep": True})
    off = state(features={"sleep": False})
    assert (read(on)["sleep"], read(off)["sleep"]) == (1, 0)


def test_unset_features_stay_clear():
    values = read(state(True, "cool", 22.0, fan="3", features={"sleep": True}))
    for name in (
        "dry_grade",
        "swing_toggle",
        "timer",
        "timer_half_hour",
        "timer_hours",
        "super_cool1",
        "super_cool2",
    ):
        assert values[name] == 0, name


def test_power_toggle_without_previous_is_the_target_power():
    # A fresh IRac's previous state is protocol UNKNOWN: handleToggles does
    # nothing, so PowerToggle = power.
    assert read(state(True, "heat", 20.0))["power_toggle"] == 1
    assert read(state(False, "heat", 20.0))["power_toggle"] == 0


@pytest.mark.parametrize(
    "before, after, toggle",
    [(True, True, 0), (True, False, 1), (False, False, 0), (False, True, 1)],
)
def test_power_toggle_with_previous_toggles_on_change(before, after, toggle):
    # IRac::handleToggles' KELON rule (power ^ prev.power), which a persistent
    # IRac applies; cpath_check.py confirms it against the C library.
    previous = state(before, "cool", 22.0)
    target = state(after, "cool", 22.0)
    assert read(target, previous)["power_toggle"] == toggle


def test_encode_passes_previous_to_the_toggle():
    dev = device()
    on = HvacState(True, "cool", 22.0)
    assert dev.encode(None, on).signal != dev.encode(on, on).signal


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (9000, 4600)
    assert pulses[-2:] == (560, 200000)
    assert len(pulses) == 2 + 2 * 48 + 2


@pytest.mark.parametrize("model", KELON_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("kelon", model), KelonDevice)


@pytest.mark.parametrize("model", KELON_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.kelon import Kelon

    legacy = LegacyDevice("kelon", model, Kelon)
    assert KelonDevice("kelon", model).capabilities == legacy.capabilities


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan"])
def test_undeclared_mode_deviation_is_reported(mode):
    dev = device()
    record = next(r for r in load_oracle("KELON") if r["state"]["mode"] == mode)
    defects = [d for d in DEFECTS if d.field != "mode"]
    with pytest.raises(AssertionError, match="mode"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects)


def test_undeclared_sleep_deviation_is_reported():
    dev = device()
    record = next(r for r in load_oracle("KELON") if r["state"].get("sleep") == "on")
    defects = [d for d in DEFECTS if d.field != "sleep"]
    with pytest.raises(AssertionError, match="sleep"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects)


def test_heat_needs_no_defect():
    # C's mode revert lands on heat, so heat records match exactly.
    dev = device()
    for record in load_oracle("KELON"):
        if record["state"]["mode"] == "heat":
            assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("KELON")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_kelon_device.py -q`
Expected: collection error, `ImportError: cannot import name ...`.

- [ ] **Step 3: Implement**: insert immediately before `# Now the match between models and objects` in `pyhvac/plugins/kelon.py`:

```python
# ------------------------------------------------------------------ Kelon
# Layout from IRremoteESP8266's KelonProtocol (ir_Kelon.h): one 48-bit word
# sent LSB first by sendKelon, i.e. 6 bytes in order, each LSB first, with a
# kKelonHdrMark/HdrSpace header, a kKelonBitMark footer and kKelonGap
# (2 * kDefaultMessageGap) after it. No checksum.

KELON = Protocol(
    "kelon",
    {
        "main": Section(
            PulseDistance(560, 600, 1680),  # kKelonBitMark/ZeroSpace/OneSpace
            header=(9000, 4600),  # kKelonHdrMark/HdrSpace
            footer=(560,),
            gap=200000,  # kKelonGap
        )
    },
    carrier=38000,  # kKelonFreq
)

# Skeleton: stateReset clears the whole word and writes the preamble
# (0x83, 0x06). pad1/pad2 (byte 5) are never written, so they stay 0.
KELON_LAYOUT = Layout(
    bytes.fromhex("830600000000"),
    {
        # Raw fan codes: 0 auto, 1 max, 2 medium, 3 min (the header's note:
        # IRKelonAc::setFan inverts the public 1..3 into these).
        "fan": Field.at(2, 0, 2, values={"auto": 0, "1": 3, "2": 2, "3": 1}),
        "power_toggle": Field.at(2, 2, 1),
        "sleep": Field.at(2, 3, 1),
        "dry_grade": Field.at(2, 4, 3),  # sign-magnitude, -2..+2
        "swing_toggle": Field.at(2, 7, 1),
        "mode": Field.at(  # kKelonMode*
            3, 0, 3, values={"heat": 0, "auto": 1, "cool": 2, "dry": 3, "fan": 4}
        ),
        "timer": Field.at(3, 3, 1),  # TimerEnabled
        "temperature": Field.at(  # degrees - kKelonMinTemp
            3, 4, 4, values={t: t - 18 for t in range(18, 33)}
        ),
        "timer_half_hour": Field.at(4, 0, 1),
        "timer_hours": Field.at(4, 1, 6),
        "smart": Field.at(4, 7, 1),  # SmartModeEnabled
        "super_cool1": Field.at(5, 4, 1),
        "super_cool2": Field.at(5, 7, 1),
    },
)

# The temperature IRKelonAc::setMode forces in these modes (the header's
# kKelonModeSmart "temp = 26C" and kKelonModeDry/Fan "temp = 25C" notes).
# This follows the C path. Real remotes differ: the dry captures in
# ir_Kelon_test.cpp (0x83040683, 0x83800683) carry 26C and the smart mode
# capture (0x1679030683) carries 25C.
KELON_FIXED_TEMPERATURE = {"auto": 26, "dry": 25, "fan": 25}


class KelonDevice(Device):
    """Kelon ON/OFF 9000-12000: the mode, fan, setpoint and sleep are sent
    in full; power (and swing) are toggles.

    As IRac::kelon sends it:
    - the setpoint is sent in cool and heat only; auto sends 26 °C and dry and
      fan send 25 °C, the temperatures IRKelonAc::setMode forces;
    - the dehumidifier grade, timer and super cool are never set (IRac passes
      dryGrade 0 and the glue never passes turbo), and the swing toggle is
      never set (the entity has no swing: IRac's swingv stays kOff);
    - SmartModeEnabled stays clear, as in the C output and the real smart
      mode capture 0x1679030683 (ir_Kelon_test.cpp, Timer12HSmartMode).

    PowerToggle: with ``previous`` it is set only when the power changes;
    this is the rule IRac::handleToggles applies to KELON when the IRac
    object has sent before (a persistent object). With ``previous=None`` it
    is ``target.power``, as a fresh IRac sends (its previous state is of
    protocol UNKNOWN, so handleToggles does nothing): an "on" toggles, an
    "off" toggles nothing.

    An off message carries the target's mode, with that mode's temperature
    rule. It does not carry what C's convertMode maps IRac's "off" to
    (kKelonModeSmart): power is only a toggle, so an off message without the
    toggle just sets the state, and the header's ensurePower note says that
    smart mode switches the unit on. C itself sends heat there, at 26 C (see
    the mode defect below). This was decided by a coordinator ruling.

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_kelon_device.py):
    - mode: IRac::kelon calls setSupercool(false), whose else branch calls
      setMode(_previousMode); _previousMode is kKelonModeHeat (0) from
      stateReset, so every C message is mode heat. The port sends the
      requested kKelonMode* value;
    - sleep: the old glue never passes sleep, so setSleep(sleep >= 0) always
      clears SleepEnabled; the port sets it.
    """

    PROTOCOL = KELON
    LAYOUTS = (KELON_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "fan", "dry", "heat"),
        temperature=TemperatureRange(18.0, 32.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
        ),
        features={"sleep": Choice((False, True), {False: "off", True: "on"})},
    )

    def frames(self, previous, target, actions):
        mode = target.mode
        if previous is None:
            toggle = target.power
        else:
            toggle = target.power != previous.power
        data = KELON_LAYOUT.build(
            fan=target.fan,
            power_toggle=toggle,
            sleep=target.features["sleep"],
            mode=mode,
            temperature=KELON_FIXED_TEMPERATURE.get(mode, int(target.temperature)),
        )
        return [Frame("main", bytes(data))]


KELON_MODELS = ("remote",)


DEVICES.update({m: KelonDevice for m in KELON_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_kelon_device.py -q`
Expected: 135 passed, 1 skipped.

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/kelon.py tests/test_kelon_device.py
git add pyhvac/plugins/kelon.py tests/test_kelon_device.py
git commit -m "KELON: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 9: TROTEC and TROTEC_3550 (with their oracle fixtures)

TROTEC: one 72-bit frame at 36 kHz plus a fixed end burst (bitless section "end"). TROTEC_3550: one 72-bit MSB-first frame. Layouts from `TrotecProtocol`/`Trotec3550Protocol`.

**Files:**
- Create: `tests/fixtures/oracle/TROTEC.json.gz`, `tests/fixtures/oracle/TROTEC_3550.json.gz`
- Modify: `pyhvac/plugins/trotech.py` (block before `# Now the match between models and objects`)
- Test: `tests/test_trotec_device.py`, `tests/test_trotec3550_device.py`

- [ ] **Step 1: Generate the oracle fixtures from the fixed C path** (this branch has the TROTEC/TROTEC_3550 protocol-name fix):

```bash
S=/tmp/claude-1000/-home-fw-development-AutoBuddy-pyhvac/e24a44b3-0698-43b6-890a-47d4ddf34b70/scratchpad
test -d $S/oracle-venv || (python -m venv $S/oracle-venv && $S/oracle-venv/bin/pip install -q "pyhvac==0.1.7")
SP=$S/oracle-venv/lib/python3.14/site-packages/pyhvac
rm -rf $S/cwork $S/gen && mkdir -p $S/cwork $S/gen && cp -r pyhvac tests tools $S/cwork/
find $S/cwork -name __pycache__ -prune -exec rm -rf {} +
cp $SP/_irhvac.so $SP/irhvac.py $S/cwork/pyhvac/
(cd $S/cwork && PYTHONPATH=. python tools/oracle_generate.py $S/gen | grep -E "^using|^TROTEC")
cp $S/gen/TROTEC.json.gz $S/gen/TROTEC_3550.json.gz tests/fixtures/oracle/
sha256sum tests/fixtures/oracle/TROTEC.json.gz tests/fixtures/oracle/TROTEC_3550.json.gz
```

Expected:
- the "using" line points into `$S/cwork`;
- `TROTEC: 37 records` and `TROTEC_3550: 72 records`;
- sha256 `0422d634c7ed0676471a142238dcb9f0dcf141d0c9129a9e56280a9f86337a8e` (TROTEC) and `0053a05165d444c676e4be23e6594dded4933a81cd5bb7204439353589b6644d` (TROTEC_3550). The generator is deterministic.

Copy only these two files; leave every other fixture untouched.

- [ ] **Step 2: Write the failing tests**: create `tests/test_trotec_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.ir.codec import decode
from pyhvac.plugins.trotech import (
    TROTEC,
    TROTEC_LAYOUT,
    TROTEC_MODELS,
    TrotecDevice,
)
from pyhvac.state import HvacState

# The C path never sends sleep: IRGHVAC.build_ircode's key map has no
# "sleep", so IRac::trotec gets sleep -1 and setSleep(sleep >= 0) clears the
# Sleep bit. The port sends the documented bit.
DEFECTS = (Defect("sleep", 1, 0, "C glue has no 'sleep' key"),)

# ir_Trotec_test.cpp (MessageConstructon / SendDataOnly): power on, cool,
# 20 °C, fan medium, sleep on. A synthetic frame built by the C class, not a
# remote capture (the test file has no Trotec remote capture).
ON_COOL_20_MED_SLEEP = bytes.fromhex("1234298200000000ab")


def _with_c_defaults(record):
    # A record without "fan" relied on IRac's default (kAuto), which
    # IRTrotecESP::convertFan sends as kTrotecFanMed, labelled "medium".
    return {**record, "state": {"fan": "medium", **record["state"]}}


def device(model="PAC 3200"):
    return TrotecDevice("trotech", model)


def read(state, previous=None):
    dev = device()
    if previous is not None:
        previous = dev.normalise(previous)
    main, _ = dev.frames(previous, dev.normalise(state), ())
    return TROTEC_LAYOUT.read(main.data)


def data(state):
    dev = device()
    main, _ = dev.frames(None, dev.normalise(state), ())
    return main.data


@pytest.mark.parametrize("record", oracle_params("TROTEC"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, _with_c_defaults(record), dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("TROTEC"):
        state = state_from_record(dev, _with_c_defaults(record)["state"])
        main, end = dev.frames(None, state, ())
        values = TROTEC_LAYOUT.read(main.data)
        assert TROTEC_LAYOUT.build(**values) == bytearray(main.data)
        assert TROTEC_LAYOUT.checksum.check(main.data)
        assert end.data == b""


def test_every_oracle_message_is_a_frame_and_the_end_burst():
    for record in load_oracle("TROTEC"):
        main, end = decode(TROTEC, record["pulses"], ["main", "end"])
        assert main.data[:2] == b"\x12\x34"  # kTrotecIntro1, kTrotecIntro2
        assert end.data == b""


def test_the_port_reproduces_the_c_test_frame():
    state = HvacState(True, "cool", 20.0, fan="2", features={"sleep": True})
    assert data(state) == ON_COOL_20_MED_SLEEP


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0, fan="1"))
    pulses = pulses.signal.pulses
    assert pulses[:2] == (5952, 7364)  # kTrotecHdrMark, kTrotecHdrSpace
    # sendGeneric's footer, then sendTrotec's extra mark + kTrotecGapEnd.
    assert pulses[-4:] == (592, 6184, 592, 1500)
    assert len(pulses) == 2 + 2 * 72 + 4


def test_carrier_is_36_khz():
    signal = device().encode(None, HvacState(True, "cool", 22.0, fan="1")).signal
    assert signal.carrier == 36000  # sendTrotec's enableIROut(36)


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan"])
@pytest.mark.parametrize("t", [16.0, 23.0, 30.0])
def test_off_carries_mode_auto_and_power_off(mode, t):
    # IRac passes mode "off"; convertMode maps it to kTrotecAuto.
    values = read(HvacState(False, mode, t, fan="3", features={"sleep": True}))
    assert (values["power"], values["mode"]) == (0, "auto")
    assert (values["temperature"], values["fan"], values["sleep"]) == (
        max(int(t), 18),
        "3",
        1,
    )


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan"])
def test_on_sends_the_mode(mode):
    values = read(HvacState(True, mode, 25.0, fan="2"))
    assert (values["power"], values["mode"]) == (1, mode)


@pytest.mark.parametrize(
    "t, sent", [(16.0, 18), (17.0, 18), (18.0, 18), (25.0, 25), (30.0, 30)]
)
def test_setpoint_is_clamped_to_18_32(t, sent):
    # The entity offers 16-30 °C, but IRTrotecESP::setTemp clamps to
    # kTrotecMinTemp (18)..kTrotecMaxTemp (32), as the C path sends.
    assert read(HvacState(True, "cool", t, fan="1"))["temperature"] == sent
    assert (
        TROTEC_LAYOUT.read_raw(data(HvacState(True, "cool", t, fan="1")), "temperature")
        == sent - 18
    )


@pytest.mark.parametrize("fan, raw", [("1", 1), ("2", 2), ("3", 3)])
def test_every_fan_level(fan, raw):
    # low/medium/high -> kTrotecFanLow/Med/High (convertFan).
    raw_read = TROTEC_LAYOUT.read_raw(
        data(HvacState(True, "cool", 22.0, fan=fan)), "fan"
    )
    assert raw_read == raw


def test_sleep_sends_the_documented_sleep_bit():
    raw = data(HvacState(True, "cool", 22.0, fan="1", features={"sleep": True}))
    assert raw[3] & 0x80  # Sleep: byte 3 bit 7
    assert read(HvacState(True, "cool", 22.0, fan="1"))["sleep"] == 0


def test_timer_is_never_set():
    # IRac::trotec has no timer: stateReset's zeros are sent.
    values = read(HvacState(True, "dry", 18.0, fan="3", features={"sleep": True}))
    assert (values["timer"], values["hours"]) == (0, 0)


@pytest.mark.parametrize(
    "previous",
    [
        None,
        HvacState(False, "cool", 22.0, fan="3"),
        HvacState(True, "cool", 26.0, fan="1"),
        HvacState(True, "cool", 22.0, fan="3", features={"sleep": True}),
    ],
)
def test_previous_is_ignored(previous):
    # No toggle bits, and IRac::handleToggles has no TROTEC case.
    dev = device()
    target = HvacState(True, "cool", 22.0, fan="3", features={"sleep": True})
    assert dev.encode(previous, target).signal == dev.encode(None, target).signal


@pytest.mark.parametrize("model", TROTEC_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("trotech", model), TrotecDevice)


@pytest.mark.parametrize("model", TROTEC_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.trotech import Trotech

    legacy = LegacyDevice("trotech", model, Trotech)
    assert device(model).capabilities == legacy.capabilities


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(r for r in load_oracle("TROTEC") if r["state"].get("sleep") == "on")
    with pytest.raises(AssertionError, match="sleep"):
        assert_matches_oracle(dev, _with_c_defaults(record), dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("TROTEC")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)
```

and `tests/test_trotec3550_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.ir.codec import decode
from pyhvac.plugins.trotech import (
    TROTEC3550,
    TROTEC3550_LAYOUT,
    TROTEC3550_MODELS,
    Trotec3550Device,
)
from pyhvac.state import HvacState

# The C path never sends swing on: IRGHVAC.trans_swing has no "on" key, so
# the lookup error is swallowed, IRac::trotec3550 gets swingv kOff and
# setSwingV(swingv != kOff) clears the SwingV bit. The port sends the bit.
DEFECTS = (Defect("swing_v", "swing", "off", "C glue has no swing 'on' key"),)

# Real captures from ir_Trotec_test.cpp (issue #1563 and its spreadsheet).
ON_COOL_18_HIGH_SWING = bytes.fromhex("552300050000318836")
OFF_COOL_18_HIGH_SWING = bytes.fromhex("552100050000318834")
DEG_79F = bytes.fromhex("55a30014000031407d")
ONE_HOUR_TIMER = bytes.fromhex("55bb01150000310259")
RESET = bytes.fromhex("5560000d000010885a")  # kReset


def device(model="PAC 3550 Pro"):
    return Trotec3550Device("trotech", model)


def read(state, previous=None):
    dev = device()
    if previous is not None:
        previous = dev.normalise(previous)
    (main,) = dev.frames(previous, dev.normalise(state), ())
    return TROTEC3550_LAYOUT.read(main.data)


def data(state):
    dev = device()
    (main,) = dev.frames(None, dev.normalise(state), ())
    return main.data


@pytest.mark.parametrize("record", oracle_params("TROTEC_3550"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("TROTEC_3550"):
        state = state_from_record(dev, record["state"])
        (main,) = dev.frames(None, state, ())
        values = TROTEC3550_LAYOUT.read(main.data)
        assert TROTEC3550_LAYOUT.build(**values) == bytearray(main.data)
        assert TROTEC3550_LAYOUT.checksum.check(main.data)


def test_every_oracle_message_is_one_frame():
    for record in load_oracle("TROTEC_3550"):
        (main,) = decode(TROTEC3550, record["pulses"], ["main"])
        assert main.data[0] == 0x55  # Intro


def test_the_port_reproduces_the_issue_1563_on_capture():
    # "On, Cool, 18C, Fan 3 (High), Swing(V) On": the remote's own frame.
    state = HvacState(True, "cool", 18.0, fan="3", swing_v="swing")
    assert data(state) == ON_COOL_18_HIGH_SWING


@pytest.mark.parametrize(
    "capture, expected",
    [
        (
            OFF_COOL_18_HIGH_SWING,
            {"power": 0, "mode": "cool", "temperature": 18, "swing_v": "swing"},
        ),
        (DEG_79F, {"celsius": 0, "temp_f": 79 - 59, "fan": "3"}),
        (ONE_HOUR_TIMER, {"timer_set": 1, "timer_hours": 1, "celsius": 0}),
    ],
)
def test_real_captures_read_back(capture, expected):
    # The remote's off frame keeps the mode (the C path, and so the port,
    # sends auto), and the Fahrenheit/timer frames are beyond the entity.
    values = TROTEC3550_LAYOUT.read(capture)
    assert TROTEC3550_LAYOUT.checksum.check(capture)
    assert {k: values[k] for k in expected} == expected


def test_reset_state_is_the_skeleton():
    # kReset: the "modeauto" frame of HumanReadable.
    assert TROTEC3550_LAYOUT.build() == bytearray(RESET)


def test_message_shape():
    signal = device().encode(None, HvacState(True, "cool", 22.0, fan="1")).signal
    assert signal.carrier == 38000
    assert signal.pulses[:2] == (12000, 5130)  # kTrotec3550HdrMark/HdrSpace
    assert signal.pulses[-2:] == (550, 100000)  # kDefaultMessageGap
    assert len(signal.pulses) == 2 + 2 * 72 + 2


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan"])
@pytest.mark.parametrize("t", [16.0, 23.0, 30.0])
def test_off_carries_mode_auto_and_power_off(mode, t):
    # IRac passes mode "off"; convertMode maps it to kTrotecAuto.
    values = read(HvacState(False, mode, t, fan="3", swing_v="swing"))
    assert (values["power"], values["mode"]) == (0, "auto")
    assert (values["temperature"], values["fan"], values["swing_v"]) == (
        int(t),
        "3",
        "swing",
    )


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan"])
def test_on_sends_the_mode(mode):
    values = read(HvacState(True, mode, 25.0, fan="2"))
    assert (values["power"], values["mode"]) == (1, mode)


@pytest.mark.parametrize("t", range(16, 31))
def test_setpoint_is_celsius_with_the_truncated_fahrenheit(t):
    # IRac passes celsius true: setTemp stores TempC, sets Celsius, and
    # stores celsiusToFahrenheit(t) - kTrotec3550MinTempF, truncated.
    values = read(HvacState(True, "cool", float(t), fan="1"))
    assert (values["temperature"], values["celsius"]) == (t, 1)
    assert values["temp_f"] == int(t * 1.8 + 32 + 1e-9) - 59


@pytest.mark.parametrize("fan, raw", [("1", 1), ("2", 2), ("3", 3)])
def test_every_fan_level(fan, raw):
    raw_read = TROTEC3550_LAYOUT.read_raw(
        data(HvacState(True, "cool", 22.0, fan=fan)), "fan"
    )
    assert raw_read == raw


@pytest.mark.parametrize("swing, bit", [("off", 0), ("swing", 1)])
def test_every_swing_value(swing, bit):
    raw = data(HvacState(True, "cool", 22.0, fan="2", swing_v=swing))
    assert raw[1] & 0x01 == bit  # SwingV: byte 1 bit 0


def test_timer_is_never_set():
    # IRac::trotec3550 has no timer: kReset's zeros are sent.
    values = read(HvacState(True, "dry", 18.0, fan="3", swing_v="swing"))
    assert (values["timer_set"], values["timer_hours"]) == (0, 0)


@pytest.mark.parametrize(
    "previous",
    [
        None,
        HvacState(False, "cool", 22.0, fan="3"),
        HvacState(True, "cool", 26.0, fan="1", swing_v="swing"),
        HvacState(True, "cool", 22.0, fan="3", swing_v="off"),
    ],
)
def test_previous_is_ignored(previous):
    # No toggle bits, and IRac::handleToggles has no TROTEC_3550 case.
    dev = device()
    target = HvacState(True, "cool", 22.0, fan="3", swing_v="swing")
    assert dev.encode(previous, target).signal == dev.encode(None, target).signal


@pytest.mark.parametrize("model", TROTEC3550_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("trotech", model), Trotec3550Device)


@pytest.mark.parametrize("model", TROTEC3550_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.trotech import Trotech3550

    legacy = LegacyDevice("trotech", model, Trotech3550)
    assert device(model).capabilities == legacy.capabilities


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(
        r for r in load_oracle("TROTEC_3550") if r["state"].get("swing") == "on"
    )
    with pytest.raises(AssertionError, match="swing_v"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("TROTEC_3550")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)
```

- [ ] **Step 3: Run them to confirm they fail**

Run: `python -m pytest tests/test_trotec_device.py tests/test_trotec3550_device.py -q`
Expected: collection errors, `ImportError: cannot import name ...` from `pyhvac.plugins.trotech`.

- [ ] **Step 4: Implement**: insert immediately before `# Now the match between models and objects` in `pyhvac/plugins/trotech.py`:

```python
# ----------------------------------------------------------------- Trotec
# Layout from IRremoteESP8266's TrotecProtocol (ir_Trotec.h): one 9-byte frame
# (kTrotecStateLength), sent LSB first at 36 kHz. IRsend::sendTrotec follows
# sendGeneric's footer (kTrotecBitMark + kTrotecGap) with one more
# kTrotecBitMark and a kTrotecGapEnd space: a bitless "end" section.

TROTEC = Protocol(
    "trotec",
    {
        "main": Section(
            PulseDistance(592, 592, 1560),  # kTrotecBitMark/ZeroSpace/OneSpace
            header=(5952, 7364),  # kTrotecHdrMark, kTrotecHdrSpace
            footer=(592,),
            gap=6184,  # kTrotecGap
        ),
        "end": Section(None, header=(592,), gap=1500),  # kTrotecGapEnd
    },
    carrier=36000,  # sendTrotec's enableIROut(36)
)

TROTEC_MODE = {  # kTrotec{Auto,Cool,Dry,Fan}
    "auto": 0,
    "cool": 1,
    "dry": 2,
    "fan": 3,
}
TROTEC_FAN = {  # kTrotecFan{Low,Med,High}, as IRTrotecESP::convertFan
    "1": 1,  # low
    "2": 2,  # medium
    "3": 3,  # high
}
TROTEC_MIN_TEMP = 18  # kTrotecMinTemp
TROTEC_MAX_TEMP = 32  # kTrotecMaxTemp

# Skeleton: IRTrotecESP::stateReset (bytes 2-8 zeroed, so no stale memory)
# with Intro1/Intro2 (0x12, 0x34), Temp kTrotecDefTemp and Fan kTrotecFanMed,
# and the sum cleared.
TROTEC_LAYOUT = Layout(
    bytes.fromhex("123420070000000000"),
    {
        "mode": Field.at(2, 0, 2, values=TROTEC_MODE),
        "power": Field.at(2, 3, 1),
        "fan": Field.at(2, 4, 2, values=TROTEC_FAN),
        "temperature": Field.at(  # whole °C, minus kTrotecMinTemp
            3,
            0,
            4,
            values={
                t: t - TROTEC_MIN_TEMP
                for t in range(TROTEC_MIN_TEMP, TROTEC_MAX_TEMP + 1)
            },
        ),
        "sleep": Field.at(3, 7, 1),
        "timer": Field.at(5, 6, 1),
        "hours": Field.at(6, 0, 8),
    },
    checksum=Sum8(2, 8, 8),  # IRTrotecESP::checksum: sumBytes of bytes 2-7
)


class TrotecDevice(Device):
    """Trotec PAC 3200 (and the Duux Blizzard): a full-state frame with a
    power bit, no toggle bits, so ``previous`` is ignored (IRac::handleToggles
    has no TROTEC case either).
    """

    PROTOCOL = TROTEC
    LAYOUTS = (TROTEC_LAYOUT, None)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "fan"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=Choice(("1", "2", "3"), {"1": "low", "2": "medium", "3": "high"}),
        features={"sleep": Choice((False, True), {False: "off", True: "on"})},
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to kTrotecAuto), and setTemp clamps to
        # kTrotecMinTemp..kTrotecMaxTemp, so 16 and 17 °C go out as 18.
        mode = target.mode if target.power else "auto"
        temperature = min(
            max(int(target.temperature), TROTEC_MIN_TEMP), TROTEC_MAX_TEMP
        )
        data = TROTEC_LAYOUT.build(
            mode=mode,
            power=target.power,
            fan=target.fan,
            temperature=temperature,
            # IRac::trotec: setSleep(sleep >= 0). The old glue never passed
            # sleep; the port sends the documented bit (see the tests).
            sleep=target.features.get("sleep", False),
        )
        return [Frame("main", bytes(data)), Frame("end", b"")]


TROTEC_MODELS = ("PAC 3200", "Duux Blizzard Smart 10K / DXMA04", "generic")


# ------------------------------------------------------------- Trotec3550
# Layout from IRremoteESP8266's Trotec3550Protocol (ir_Trotec.h): one 9-byte
# frame (kTrotecStateLength), sent MSB first (sendTrotec3550's sendGeneric
# MSBfirst=true) at 38 kHz, with a kDefaultMessageGap gap.

TROTEC3550 = Protocol(
    "trotec-3550",
    {
        "main": Section(
            PulseDistance(550, 500, 1950),  # kTrotec3550BitMark/Zero/OneSpace
            header=(12000, 5130),  # kTrotec3550HdrMark, kTrotec3550HdrSpace
            footer=(550,),
            gap=100000,  # kDefaultMessageGap
            lsb_first=False,
        ),
    },
    carrier=38000,  # sendGeneric(..., 38, ...)
)

TROTEC3550_SWING_V = {"off": 0, "swing": 1}  # SwingV bit
TROTEC3550_MIN_TEMP = 16  # kTrotec3550MinTempC
TROTEC3550_MAX_TEMP = 30  # kTrotec3550MaxTempC
TROTEC3550_MIN_TEMP_F = 59  # kTrotec3550MinTempF

# Skeleton: IRTrotec3550::stateReset's kReset (all nine bytes written, so no
# stale memory) with the sum cleared: Intro 0x55, TempC 22, TempF 72, Fan
# low, the unknown byte 7 bit 3 and Celsius set.
TROTEC3550_LAYOUT = Layout(
    bytes.fromhex("5560000d0000108800"),
    {
        "swing_v": Field.at(1, 0, 1, values=TROTEC3550_SWING_V),
        "power": Field.at(1, 1, 1),
        "timer_set": Field.at(1, 3, 1),
        "temperature": Field.at(  # whole °C, minus kTrotec3550MinTempC
            1,
            4,
            4,
            values={
                t: t - TROTEC3550_MIN_TEMP
                for t in range(TROTEC3550_MIN_TEMP, TROTEC3550_MAX_TEMP + 1)
            },
        ),
        "timer_hours": Field.at(2, 0, 4),
        "temp_f": Field.at(3, 0, 5),  # whole °F, minus kTrotec3550MinTempF
        "mode": Field.at(6, 0, 2, values=TROTEC_MODE),
        "fan": Field.at(6, 4, 2, values=TROTEC_FAN),
        "celsius": Field.at(7, 7, 1),
    },
    checksum=Sum8(0, 8, 8),  # IRTrotec3550::calcChecksum: bytes 0-7
)


class Trotec3550Device(Device):
    """Trotec PAC 3550 Pro: a full-state frame with a power bit and a SwingV
    bit, no toggle bits, so ``previous`` is ignored (IRac::handleToggles has
    no TROTEC_3550 case either).
    """

    PROTOCOL = TROTEC3550
    LAYOUTS = (TROTEC3550_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "fan"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=Choice(("1", "2", "3"), {"1": "low", "2": "medium", "3": "high"}),
        swing_v=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode auto (convertMode maps
        # IRac's mode "off" to kTrotecAuto). IRac passes celsius (true), so
        # setTemp stores TempC and the truncated Fahrenheit equivalent.
        mode = target.mode if target.power else "auto"
        temperature = min(
            max(int(target.temperature), TROTEC3550_MIN_TEMP), TROTEC3550_MAX_TEMP
        )
        data = TROTEC3550_LAYOUT.build(
            # IRac::trotec3550: setSwingV(swingv != kOff). The old glue never
            # passed swing "on"; the port sends the documented bit.
            swing_v=target.swing_v,
            power=target.power,
            temperature=temperature,
            temp_f=temperature * 9 // 5 + 32 - TROTEC3550_MIN_TEMP_F,
            mode=mode,
            fan=target.fan,
            celsius=True,
        )
        return [Frame("main", bytes(data))]


TROTEC3550_MODELS = ("PAC 3550 Pro", "generic 3550")


DEVICES.update({m: TrotecDevice for m in TROTEC_MODELS})
DEVICES.update({m: Trotec3550Device for m in TROTEC3550_MODELS})
```

- [ ] **Step 5: Run the tests**

Run: `python -m pytest tests/test_trotec_device.py tests/test_trotec3550_device.py -q`
Expected: 202 passed, 5 skipped.

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 6: Format and commit**

```bash
black pyhvac/plugins/trotech.py tests/test_trotec_device.py tests/test_trotec3550_device.py
git add pyhvac/plugins/trotech.py tests/test_trotec_device.py tests/test_trotec3550_device.py tests/fixtures/oracle/TROTEC.json.gz tests/fixtures/oracle/TROTEC_3550.json.gz
git commit -m "TROTEC and TROTEC_3550: fixtures from the fixed C path, and pure-Python ports

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 10: Whole-group verification

**Files:**
- Modify: `tests/test_pairs_family.py`

- [ ] **Step 1: Add the group test**: append to `tests/test_pairs_family.py`:

```python
@pytest.mark.parametrize("name", MODULES + ("ge",))
def test_no_ported_model_uses_the_c_library(name):
    from pyhvac import registry
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.hvaclib import IRGHVAC

    # The Midea models listed in trotech.py belong to the Midea port.
    left = []
    for model in registry.models(name):
        try:
            device = registry.get_device(name, model)
        except AttributeError:  # a legacy C class without the C extension
            left.append(model)
            continue
        if isinstance(device, LegacyDevice) and issubclass(device.legacy_class, IRGHVAC):
            left.append(model)
    if name == "trotech":
        assert sorted(left) == sorted(
            [
                "PAC 2100 X",
                "PAC 3900 X",
                "RG57H(B)/BGE remote",
                "RG57H3(B)/BGCEF-M remote",
            ]
        )
    else:
        assert left == []
```

- [ ] **Step 2: Run it**

Run: `python -m pytest tests/test_pairs_family.py -q`
Expected: 11 passed.

- [ ] **Step 3: Run the C-extension suite**

```bash
S=/tmp/claude-1000/-home-fw-development-AutoBuddy-pyhvac/e24a44b3-0698-43b6-890a-47d4ddf34b70/scratchpad
SP=$S/oracle-venv/lib/python3.14/site-packages/pyhvac
rm -rf $S/cwork && mkdir -p $S/cwork && cp -r pyhvac tests tools $S/cwork/
find $S/cwork -name __pycache__ -prune -exec rm -rf {} +
cp $SP/_irhvac.so $SP/irhvac.py $S/cwork/pyhvac/
cd $S/cwork && PYTHONPATH=. python -m pytest -q -p no:cacheprovider tests | tail -3
```

Expected: 0 failed, and the capability-equality tests pass.

- [ ] **Step 4: Commit**

```bash
black tests/test_pairs_family.py
git add tests/test_pairs_family.py
git commit -m "Test that no paired-protocol model is left on the C library

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
