# Hitachi Family Ports Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the C path for every portable C-backed Hitachi model with a pure-Python `Device`: HITACHI_AC, HITACHI_AC1, HITACHI_AC424, HITACHI_AC344, HITACHI_AC264 and HITACHI_AC296.

**Architecture:** Same as the Daikin plan. One device class per protocol is appended to `pyhvac/plugins/hitachi.py` and registered through a new `DEVICES` dict. Each port was written from its `union Hitachi*Protocol` in IRremoteESP8266's `ir_Hitachi.h`, then verified two ways:
- against every oracle record, with only declared defects allowed;
- against the real C path on states the grid lacks, including persistent-IRac sequences for the toggle protocols.

**Tech Stack:** Python ≥ 3.9 standard library, pytest, black. The port kit on branch `ports`.

**Spec:** `docs/superpowers/specs/2026-09-27-port-kit-design.md`. House rules: `docs/superpowers/plans/2026-09-28-daikin-ports.md` ("Rulings made while planning").

## Global Constraints

- Work on branch `ports`.
- Durations are integer µs, the carrier is in Hz, and temperatures are °C.
- Python ≥ 3.9, and no new runtime dependencies.
- Layouts come from the headers (facts). Nothing from the fork is copied.
- Ported capabilities equal the legacy entity (C-only test in each file).
- A difference from the C output is allowed only as a declared `Defect`.
- The old API and all existing tests stay green. Run `black` on every modified file.
- Tests: `python -m pytest -q`. The C-extension run is described in Task 8.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **Toggle protocols.** HITACHI_AC1 (power and swing toggles) and HITACHI_AC424/344 (swing button) use `previous`. The same limits apply as for DAIKIN64/128 after a restart (`previous=None`) or a repeated send.
2. **HITACHI_AC296 padding fields.** Sending 0 where the C encoder sends stale memory changes what those units receive. The RAR-3U3 captures are the evidence.
3. **HITACHI_AC264 advertises swing and features that send nothing.** This matches the C path and the legacy entity; users see controls with no effect.
4. **Import guard.** Without it, `hitachi.py` fails to import without the C extension and the whole brand, ports included, vanishes from the registry. Task 1 pins it.
5. **HITACHI_AC3** (`PC-LH3B`, `generic 3`) stays on the C path, which sends nothing. The user decided to drop these models in phase 4.

## Rulings made while planning

- **Swing "on" (all six):** the ports send the documented swing value. The oracle fixtures predate the `main` fix for `trans_swing`/`trans_hswing`.
- **HITACHI_AC1 sleep:** the port sends the documented Sleep2 code. `IRGHVAC.build_ircode`'s key map has no `"sleep"`, so sleep never reached the C library on any C-backed class. That is a glue bug to fix on `main`: IRac expects minutes, −1 for off.
- **HITACHI_AC1 fan in heat/fan mode:** `IRHitachiAc1::setFan` returns before storing the requested speed; its own comment says only auto is forbidden. The port stores low/medium/high and turns auto into low.
- **HITACHI_AC296 padding:** byte 25 bit 7 and byte 13 bits 0–1 are never written by `stateReset`, so the C output comes from stale memory. It varied between processes: 1 in 5 or 6 of 8 runs, 0 in the rest. The port sends 0, as the two RAR-3U3 captures in `ir_Hitachi_test.cpp` do.
- **HITACHI_AC fan "high" sends 4,** matching C (`convertFan` maps kHigh to `kHitachiAcFanHigh − 1`, and `toCommonFanSpeed` maps 4 back to high). This is a designed mapping, not a defect.
- **HITACHI_AC344 SwingV state bit (byte 37):** kept clear, as the C path does. The unit is driven by the swing button, and there is no evidence the bit is needed.
- **HITACHI_AC264 swing:** no swing is sent, as the C path ("No Swing(V) setting available"). No swing-button behaviour is invented.

## Tasks

- Task 1: the import guard and the `DEVICES` dict.
- Tasks 2–7: one port each; the block goes before `# Now the match between models and objects` (right before `class PluginObject`).
- Task 8: the family test and the C-extension run.

---

### Task 1: Import guard and DEVICES

**Files:**
- Modify: `pyhvac/plugins/hitachi.py` (imports; add `DEVICES = {}`)
- Test: `tests/test_hitachi_family.py`

- [ ] **Step 1: Write the failing test**: create `tests/test_hitachi_family.py`:

```python
"""The Hitachi plugin and its ports load with or without the C extension."""

import importlib


def test_hitachi_imports_without_the_c_extension():
    module = importlib.import_module("pyhvac.plugins.hitachi")
    assert isinstance(module.DEVICES, dict)
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `python -m pytest tests/test_hitachi_family.py -q`
Expected: FAIL: `ModuleNotFoundError: No module named 'pyhvac.irhvac'` (without the C extension).

- [ ] **Step 3: Implement**: in `pyhvac/plugins/hitachi.py`, replace

```python
from .hvaclib import PulseBased, GenPluginObject
from ..irhvac import R_LT0541_HTA_A, R_LT0541_HTA_B
```

with

```python
from dataclasses import dataclass

from .hvaclib import PulseBased, GenPluginObject
from ..device import Device
from ..fields import Checksum, Field, InvertedPairs, Layout, NibbleSum, bit_reverse
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import Capabilities, Choice, TemperatureRange

try:
    from ..irhvac import R_LT0541_HTA_A, R_LT0541_HTA_B
except ImportError:
    # Only the C-backed classes use these; keep the ported ones importable.
    R_LT0541_HTA_A = R_LT0541_HTA_B = None
```

and insert `DEVICES = {}` (followed by two blank lines) immediately before the `# Now the match between models and objects` comment that precedes `class PluginObject(GenPluginObject):`.

- [ ] **Step 4: Run the tests**

Run: `python -m pytest -q`
Expected: all pass. Legacy Hitachi models now report skips (they need the C extension) instead of the brand vanishing.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/hitachi.py tests/test_hitachi_family.py
git add pyhvac/plugins/hitachi.py tests/test_hitachi_family.py
git commit -m "Hitachi: import without the C extension; DEVICES for the ports

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 2: HITACHI_AC

One 28-byte frame, MSB first; layout from `union HitachiProtocol` (fields stored bit-reversed); local byte-aligned `HitachiAcChecksum`.

**Files:**
- Modify: `pyhvac/plugins/hitachi.py` (block before `# Now the match between models and objects`)
- Test: `tests/test_hitachi_ac_device.py`

**Interfaces:**
- Consumes: `Device`, `pyhvac.fields`, bitless sections, `tests/port_oracle.py`, and the oracle fixture `HITACHI_AC`.
- Produces: `HitachiAcDevice`, `HITACHI_AC_MODELS`, and the `DEVICES` entries for those models.

- [ ] **Step 1: Write the failing tests**: create `tests/test_hitachi_ac_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.hitachi import (
    HITACHI_AC_LAYOUT,
    HITACHI_AC_MODELS,
    HitachiAcChecksum,
    HitachiAcDevice,
)
from pyhvac.state import HvacState

# The C path never sends swing on: the old vocabulary's "on" has no entry in
# IRGHVAC.trans_swing / trans_hswing, so build_ircode skips the key, swingv and
# swingh stay kOff, and IRac::hitachi never sets the SwingV / SwingH bits
# (HitachiProtocol byte 14 bit 7, byte 15 bit 7).
DEFECTS = (
    Defect("swing_v", "swing", "off", "C glue has no 'on' swing: sends off"),
    Defect("swing_h", "swing", "off", "C glue has no 'on' hswing: sends off"),
)

MODES = ("auto", "heat", "cool", "dry", "fan")


def device():
    return HitachiAcDevice("hitachi", "RAS-35THA6 remote")


def read(state, previous=None):
    dev = device()
    (frame,) = dev.frames(previous, dev.normalise(state), ())
    return HITACHI_AC_LAYOUT.read(frame.data)


def raw(state, name):
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(state), ())
    return HITACHI_AC_LAYOUT.read_raw(frame.data, name)


@pytest.mark.parametrize("record", oracle_params("HITACHI_AC"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("HITACHI_AC"):
        state = state_from_record(dev, record["state"])
        (frame,) = dev.frames(None, state, ())
        values = HITACHI_AC_LAYOUT.read(frame.data)
        assert HITACHI_AC_LAYOUT.build(**values) == bytearray(frame.data)


def test_checksum_matches_a_c_frame():
    # Off, cool, 16 °C, fan auto, as sent by the C library.
    data = bytearray.fromhex("80080c02fd807f8848904004008060600000000000000000800000c5")
    assert HitachiAcChecksum(0, 27, 27, reverse=True).check(data)
    data[27] = 0
    HITACHI_AC_LAYOUT.checksum.apply(data)
    assert data[27] == 0xC5


def test_fields_are_stored_bit_reversed():
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(HvacState(True, "cool", 24.0)), ())
    # kHitachiAcCool = 4, 24 °C << 1 = 48, kHitachiAcFanAuto = 1, all reversed.
    assert (frame.data[10], frame.data[11], frame.data[13]) == (0x20, 0x0C, 0x80)


@pytest.mark.parametrize("mode", MODES)
def test_off_carries_mode_auto_in_every_mode(mode):
    # IRac passes mode "off"; IRHitachiAc::convertMode maps it to auto.
    for t in (16.0, 32.0):
        values = read(HvacState(False, mode, t))
        assert (values["power"], values["mode"]) == (0, "auto")
        sent = raw(HvacState(False, mode, t), "temperature")
        assert sent == int(f"{int(t) << 1:08b}"[::-1], 2)


@pytest.mark.parametrize("mode", MODES)
def test_setpoint_is_sent_in_every_mode_even_fan(mode):
    # setMode(kHitachiAcFan) writes the special temperature 64, but IRac calls
    # setTemp(degrees) afterwards, so the C path always sends the setpoint.
    for t in (16, 23, 32):
        (frame,) = device().frames(None, HvacState(True, mode, float(t)), ())
        assert frame.data[11] == int(f"{t << 1:08b}"[::-1], 2)


def test_setpoint_is_clamped_to_16_32():
    assert raw(HvacState(True, "cool", 10.0), "temperature") == raw(
        HvacState(True, "cool", 16.0), "temperature"
    )
    assert raw(HvacState(True, "cool", 40.0), "temperature") == raw(
        HvacState(True, "cool", 32.0), "temperature"
    )


@pytest.mark.parametrize("mode", MODES)
def test_byte_9_flags_the_minimum_setpoint(mode):
    # IRHitachiAc::setTemp: byte 9 is 0x90 at kHitachiAcMinTemp, else 0x10.
    for power in (False, True):
        for t, byte in ((16.0, 0x90), (17.0, 0x10), (32.0, 0x10)):
            dev = device()
            (frame,) = dev.frames(None, dev.normalise(HvacState(power, mode, t)), ())
            assert frame.data[9] == byte


@pytest.mark.parametrize("fan, code", [("auto", 1), ("1", 2), ("2", 3), ("3", 4)])
def test_fan_levels_follow_convert_fan(fan, code):
    # kLow -> kHitachiAcFanLow, kMedium -> +1, kHigh -> kHitachiAcFanHigh - 1.
    state = HvacState(True, "cool", 24.0, fan=fan)
    assert raw(state, "fan") == int(f"{code:08b}"[::-1], 2)
    assert read(state)["fan"] == fan


@pytest.mark.parametrize(
    "fan, sent", [("auto", "1"), ("1", "1"), ("2", "2"), ("3", "2")]
)
def test_dry_has_only_low_and_medium(fan, sent):
    assert read(HvacState(True, "dry", 24.0, fan=fan))["fan"] == sent


@pytest.mark.parametrize(
    "fan, sent", [("auto", "1"), ("1", "1"), ("2", "2"), ("3", "3")]
)
def test_fan_mode_has_no_auto(fan, sent):
    assert read(HvacState(True, "fan", 24.0, fan=fan))["fan"] == sent


def test_off_keeps_the_requested_fan():
    # An off message is in mode auto, so no dry / fan clamp applies.
    assert read(HvacState(False, "dry", 24.0, fan="3"))["fan"] == "3"
    assert read(HvacState(False, "fan", 24.0))["fan"] == "auto"


def test_swing_on_sets_the_documented_bits():
    state = HvacState(True, "cool", 24.0, swing_v="swing", swing_h="swing")
    assert (read(state)["swing_v"], read(state)["swing_h"]) == ("swing", "swing")
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(state), ())
    assert (frame.data[14], frame.data[15]) == (0xE0, 0xE0)


def test_previous_is_ignored():
    dev = device()
    on = HvacState(True, "cool", 22.0)
    off = HvacState(False, "cool", 22.0)
    assert dev.encode(None, on).signal == dev.encode(off, on).signal
    assert dev.encode(on, on).signal == dev.encode(None, on).signal


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (3300, 1700)
    assert pulses[-2:] == (400, 100000)
    assert len(pulses) == 2 + 2 * 224 + 2


@pytest.mark.parametrize("model", HITACHI_AC_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("hitachi", model), HitachiAcDevice)


@pytest.mark.parametrize("model", HITACHI_AC_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.hitachi import Hitachi

    legacy = LegacyDevice("hitachi", model, Hitachi)
    assert HitachiAcDevice("hitachi", model).capabilities == legacy.capabilities


def test_undeclared_swing_v_deviation_is_reported():
    dev = device()
    record = next(
        r for r in load_oracle("HITACHI_AC") if r["state"].get("swing") == "on"
    )
    with pytest.raises(AssertionError, match="swing_v"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_undeclared_swing_h_deviation_is_reported():
    dev = device()
    record = next(
        r for r in load_oracle("HITACHI_AC") if r["state"].get("hswing") == "on"
    )
    with pytest.raises(AssertionError, match="swing_h"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=DEFECTS[:1])


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("HITACHI_AC")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_hitachi_ac_device.py -q`
Expected: collection error, `ImportError: cannot import name ...` from `pyhvac.plugins.hitachi`.

- [ ] **Step 3: Implement**: insert immediately before `# Now the match between models and objects` in `pyhvac/plugins/hitachi.py`:

```python
# --------------------------------------------------------------- HitachiAc
# Layout from IRremoteESP8266's HitachiProtocol (ir_Hitachi.h): one 28-byte
# frame (kHitachiAcStateLength), sent MSB first (sendHitachiAC), so frame
# byte n is struct byte n. Every field holds its value bit-reversed
# (IRHitachiAc stores reverseBits(value, 8)), and so do the value tables.

HITACHI_AC = Protocol(
    "hitachi-ac",
    {
        "main": Section(
            PulseDistance(400, 500, 1250),  # kHitachiAcBitMark/ZeroSpace/OneSpace
            header=(3300, 1700),  # kHitachiAcHdrMark/HdrSpace
            footer=(400,),
            gap=100000,  # kHitachiAcMinGap = kDefaultMessageGap
            lsb_first=False,
        ),
    },
    carrier=38000,  # kHitachiAcFreq
)


@dataclass(frozen=True)
class HitachiAcChecksum(Checksum):
    """IRHitachiAc::calcChecksum: 62 minus the sum of the bit-reversed bytes
    before ``at``, bit-reversed."""

    def compute(self, data):
        return bit_reverse((62 - sum(self._input(data))) & 0xFF)


HITACHI_AC_MODES = {  # kHitachiAc{Auto,Heat,Cool,Dry,Fan}
    "auto": 2,
    "heat": 3,
    "cool": 4,
    "dry": 5,
    "fan": 0xC,
}
HITACHI_AC_FANS = {  # IRHitachiAc::convertFan
    "auto": 1,  # kHitachiAcFanAuto
    "1": 2,  # kHitachiAcFanLow (kLow)
    "2": 3,  # kHitachiAcFanMed (kMedium)
    "3": 4,  # kHitachiAcFanHigh - 1 (kHigh; kMax would be kHitachiAcFanHigh)
}
HITACHI_AC_MIN_TEMP = 16  # kHitachiAcMinTemp

# Skeleton: IRHitachiAc::stateReset with the written fields and the sum
# cleared. Bytes 0-8, 14/15 (0x60 below the swing bits) and 24 (0x80) are
# fixed; byte 9 is 0x10, or 0x90 at kHitachiAcMinTemp (setTemp).
HITACHI_AC_LAYOUT = Layout(
    bytes.fromhex("80080c02fd807f884810000000006060000000000000000080000000"),
    {
        "min_temp": Field.at(9, 7, 1),
        "mode": Field.at(
            10, 0, 8, values={k: bit_reverse(v) for k, v in HITACHI_AC_MODES.items()}
        ),
        "temperature": Field.at(  # whole °C, doubled
            11, 0, 8, values={t: bit_reverse(t << 1) for t in range(16, 33)}
        ),
        "fan": Field.at(
            13, 0, 8, values={k: bit_reverse(v) for k, v in HITACHI_AC_FANS.items()}
        ),
        "swing_v": Field.at(14, 7, 1, values={"off": 0, "swing": 1}),
        "swing_h": Field.at(15, 7, 1, values={"off": 0, "swing": 1}),
        "power": Field.at(17, 0, 1),
    },
    checksum=HitachiAcChecksum(0, 27, 27, reverse=True),
)


class HitachiAcDevice(Device):
    """Hitachi (RAS-35THA6): a full-state protocol, ``previous`` is ignored."""

    PROTOCOL = HITACHI_AC
    LAYOUTS = (HITACHI_AC_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "heat", "cool", "dry", "fan"),
        temperature=TemperatureRange(16.0, 32.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
        ),
        swing_v=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
        swing_h=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to kHitachiAcAuto).
        mode = target.mode if target.power else "auto"
        # IRHitachiAc::setFan clamps by mode: dry only has low and medium
        # (kHitachiAcFanLow..+1), fan has no auto (minimum kHitachiAcFanLow).
        fan = target.fan
        if mode == "dry":
            fan = {"auto": "1", "3": "2"}.get(fan, fan)
        elif mode == "fan" and fan == "auto":
            fan = "1"
        # setMode(kHitachiAcFan) writes the special temperature 64, but IRac
        # calls setTemp(degrees) after setMode, so the setpoint is always sent.
        temperature = int(target.temperature)
        data = HITACHI_AC_LAYOUT.build(
            min_temp=temperature == HITACHI_AC_MIN_TEMP,
            mode=mode,
            temperature=temperature,
            fan=fan,
            swing_v=target.swing_v,
            swing_h=target.swing_h,
            power=target.power,
        )
        return [Frame("main", bytes(data))]


HITACHI_AC_MODELS = ("RAS-35THA6 remote", "generic")


DEVICES.update({m: HitachiAcDevice for m in HITACHI_AC_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_hitachi_ac_device.py -q`
Expected: 185 passed, 2 skipped (the skips need the C extension).

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/hitachi.py tests/test_hitachi_ac_device.py
git add pyhvac/plugins/hitachi.py tests/test_hitachi_ac_device.py
git commit -m "HITACHI_AC: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 3: HITACHI_AC1

One 13-byte frame, MSB first; layout from `union Hitachi1Protocol`; two variants (A/B) in one class, looked up from `HITACHI1_MODELS`; power and swing TOGGLE bits using `previous` (the C rule lives in IRac::sendAc's HITACHI_AC1 case).

**Files:**
- Modify: `pyhvac/plugins/hitachi.py` (block before `# Now the match between models and objects`)
- Test: `tests/test_hitachi1_device.py`

**Interfaces:**
- Consumes: `Device`, `pyhvac.fields`, bitless sections, `tests/port_oracle.py`, and the oracle fixture `HITACHI_AC1`.
- Produces: `Hitachi1Device`, `HITACHI1_MODELS`, and the `DEVICES` entries for those models.

- [ ] **Step 1: Write the failing tests**: create `tests/test_hitachi1_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.hitachi import (
    HITACHI1_LAYOUT,
    HITACHI1_MODELS,
    Hitachi1Checksum,
    Hitachi1Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Hitachi1 values here:
# - the legacy glue (IRGHVAC.trans_swing/trans_hswing) has no "on" key, so
#   swingv/swingh stay kOff: the SwingV/SwingH bits are never set, and the
#   swing toggle IRac::sendAc derives from them (against a fresh IRac's
#   all-off previous state) is never set either;
# - the legacy glue (IRGHVAC.build_ircode's key map) has no "sleep" key, so
#   sleep stays -1 and IRac::hitachi1 never sends kHitachiAc1Sleep2;
# - IRHitachiAc1::setFan, in heat and fan, returns without storing the
#   requested speed once the current one is not auto, and setMode (called
#   first by IRac::hitachi1) has already forced it to kHitachiAc1FanLow: C
#   sends low for every speed there. The port sends kHitachiAc1FanMed/High.
DEFECTS = (
    Defect("swing_v", "swing", "off", "legacy glue never passes swing on"),
    Defect("swing_h", "swing", "off", "legacy glue never passes hswing on"),
    Defect("swing_toggle", 1, 0, "follows swing_v/swing_h, never passed on"),
    Defect("sleep", 2, 0, "legacy glue never passes sleep"),
    Defect("fan", "2", "1", "IRHitachiAc1::setFan drops medium in heat/fan"),
    Defect("fan", "3", "1", "IRHitachiAc1::setFan drops high in heat/fan"),
)


def device(model="LT0541-HTA remote"):
    return Hitachi1Device("hitachi", model)


def read(state, previous=None, dev=None):
    dev = dev or device()
    (main,) = dev.frames(previous, dev.normalise(state), ())
    return HITACHI1_LAYOUT.read(main.data)


def _device_for(record):
    return Hitachi1Device("hitachi", record["model"])


@pytest.mark.parametrize("record", oracle_params("HITACHI_AC1"))
def test_matches_c_library(record):
    dev = _device_for(record)
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_oracle_covers_both_variants():
    classes = {(r["class"], r["variant"]) for r in load_oracle("HITACHI_AC1")}
    assert classes == {("Hitachi1A", "1"), ("Hitachi1B", "2")}
    for record in load_oracle("HITACHI_AC1"):
        expected = {"Hitachi1A": "A", "Hitachi1B": "B"}[record["class"]]
        assert _device_for(record).variant == expected


def test_layout_round_trips_every_oracle_state():
    for record in load_oracle("HITACHI_AC1"):
        dev = _device_for(record)
        state = state_from_record(dev, record["state"])
        (main,) = dev.frames(None, state, ())
        values = HITACHI1_LAYOUT.read(main.data)
        assert HITACHI1_LAYOUT.build(**values) == bytearray(main.data)


def test_checksum_matches_the_reset_state():
    # IRHitachiAc1::stateReset's known good state, Sum = 0x24.
    data = bytearray.fromhex("b2ae4d91f0e1a4000000006124")
    assert Hitachi1Checksum(5, 12, 12).check(data)
    data[12] = 0
    Hitachi1Checksum(5, 12, 12).apply(data)
    assert data[12] == 0x24


def test_checksum_matches_the_upstream_cool_32_example():
    # ir_Hitachi_test.cpp HumanReadable: cool, 32 °C, auto fan, power on.
    data = bytes.fromhex("b2ae4d91f061cc0000000030" "04")
    assert Hitachi1Checksum(5, 12, 12).check(data)
    dev = device()
    (main,) = dev.frames(None, dev.normalise(HvacState(True, "cool", 32.0)), ())
    assert main.data == data


def test_model_bits_follow_the_variant():
    assert read(HvacState(True, "cool", 22.0))["model"] == "A"
    dev_b = device("generic 1 code b")
    assert read(HvacState(True, "cool", 22.0), dev=dev_b)["model"] == "B"
    explicit = Hitachi1Device("hitachi", "LT0541-HTA remote", variant="B")
    assert read(HvacState(True, "cool", 22.0), dev=explicit)["model"] == "B"
    with pytest.raises(ValueError):
        Hitachi1Device("hitachi", "x", variant="C")


def test_every_model_maps_to_its_variant():
    assert HITACHI1_MODELS == {
        "LT0541-HTA remote": "A",
        "Series VI": "A",
        "KAZE-312KSDP": "A",
        "R-LT0541-HTA/Y.K.1.1-1 V2.3 remote": "A",
        "generic 1 code a": "A",
        "generic 1 code b": "B",
    }
    for model, variant in HITACHI1_MODELS.items():
        assert device(model).variant == variant


@pytest.mark.parametrize("t", range(16, 33))
def test_temperature_is_reversed_offset(t):
    raw = HITACHI1_LAYOUT.build(temperature=t)
    stored = (raw[6] >> 2) & 0x1F
    assert int(f"{stored:05b}"[::-1], 2) + 7 == t
    assert read(HvacState(True, "cool", float(t)))["temperature"] == t


def test_off_carries_mode_auto_at_25_in_every_mode():
    # IRac passes mode "off"; convertMode maps it to auto, and setTemp is a
    # no-op in auto, leaving the reset kHitachiAc1TempAuto.
    dev = device()
    for mode in dev.capabilities.modes:
        for t in (16.0, 32.0):
            for fan in dev.capabilities.fan.values:
                values = read(HvacState(False, mode, t, fan=fan))
                assert (values["mode"], values["temperature"], values["fan"]) == (
                    "auto",
                    25,
                    "auto",
                )
                assert values["power"] == 0


@pytest.mark.parametrize("t", (16.0, 24.0, 32.0))
def test_auto_mode_is_locked_to_25_and_auto_fan(t):
    for fan in ("auto", "1", "2", "3"):
        values = read(HvacState(True, "auto", t, fan=fan))
        assert (values["temperature"], values["fan"]) == (25, "auto")


def test_dry_is_locked_to_low_fan():
    for fan in ("auto", "1", "2", "3"):
        assert read(HvacState(True, "dry", 22.0, fan=fan))["fan"] == "1"


@pytest.mark.parametrize("mode", ("heat", "fan"))
def test_heat_and_fan_replace_auto_fan_with_low(mode):
    assert read(HvacState(True, mode, 22.0, fan="auto"))["fan"] == "1"
    # Documented speeds otherwise (declared Defect: C sends low).
    for fan in ("1", "2", "3"):
        assert read(HvacState(True, mode, 22.0, fan=fan))["fan"] == fan


@pytest.mark.parametrize("fan, raw", [("auto", 1), ("1", 8), ("2", 4), ("3", 2)])
def test_every_fan_level_uses_its_documented_value_in_cool(fan, raw):
    dev = device()
    (main,) = dev.frames(
        None, dev.normalise(HvacState(True, "cool", 22.0, fan=fan)), ()
    )
    assert HITACHI1_LAYOUT.read_raw(main.data, "fan") == raw


@pytest.mark.parametrize("mode", ("auto", "cool"))
def test_sleep_sends_sleep2_in_auto_and_cool(mode):
    on = HvacState(True, mode, 22.0, features={"sleep": True})
    assert read(on)["sleep"] == 2
    assert read(HvacState(True, mode, 22.0))["sleep"] == 0


@pytest.mark.parametrize("mode", ("heat", "dry", "fan"))
def test_sleep_is_off_outside_auto_and_cool(mode):
    assert read(HvacState(True, mode, 22.0, features={"sleep": True}))["sleep"] == 0


def test_sleep_in_an_off_message_follows_mode_auto():
    assert read(HvacState(False, "heat", 22.0, features={"sleep": True}))["sleep"] == 2


def test_swing_bits_are_states():
    values = read(HvacState(True, "cool", 22.0, swing_v="swing"))
    assert (values["swing_v"], values["swing_h"]) == ("swing", "off")
    values = read(HvacState(True, "cool", 22.0, swing_h="swing"))
    assert (values["swing_v"], values["swing_h"]) == ("off", "swing")


def test_toggles_without_previous_compare_against_a_fresh_irac():
    # A fresh IRac's _prev is the stdAc default: power off, swings off.
    on = read(HvacState(True, "cool", 22.0))
    assert (on["power"], on["power_toggle"], on["swing_toggle"]) == (1, 1, 0)
    off = read(HvacState(False, "cool", 22.0))
    assert (off["power"], off["power_toggle"], off["swing_toggle"]) == (0, 0, 0)
    for kw in ({"swing_v": "swing"}, {"swing_h": "swing"}):
        assert read(HvacState(True, "cool", 22.0, **kw))["swing_toggle"] == 1


@pytest.mark.parametrize(
    "before, after, toggle",
    [(True, True, 0), (True, False, 1), (False, False, 0), (False, True, 1)],
)
def test_power_toggle_with_previous_toggles_on_change(before, after, toggle):
    # As IRac::sendAc for HITACHI_AC1: power_toggle = send.power != prev->power.
    previous = HvacState(before, "cool", 22.0)
    values = read(HvacState(after, "cool", 22.0), previous)
    assert (values["power"], values["power_toggle"]) == (int(after), toggle)


@pytest.mark.parametrize(
    "before, after, toggle",
    [
        (("off", "off"), ("off", "off"), 0),
        (("off", "off"), ("swing", "off"), 1),
        (("swing", "off"), ("swing", "off"), 0),
        (("swing", "off"), ("off", "off"), 1),
        (("off", "off"), ("off", "swing"), 1),
        (("swing", "swing"), ("swing", "swing"), 0),
        (("swing", "off"), ("off", "swing"), 1),
    ],
)
def test_swing_toggle_with_previous_toggles_on_change(before, after, toggle):
    # As IRac::sendAc: swingv or swingh differs from the previous state.
    previous = HvacState(True, "cool", 22.0, swing_v=before[0], swing_h=before[1])
    target = HvacState(True, "cool", 22.0, swing_v=after[0], swing_h=after[1])
    values = read(target, previous)
    assert values["swing_toggle"] == toggle
    assert (values["swing_v"], values["swing_h"]) == after


def test_encode_passes_previous_to_the_toggles():
    dev = device()
    on = HvacState(True, "cool", 22.0)
    fresh = dev.encode(None, on).signal
    again = dev.encode(on, on).signal
    assert fresh != again


def test_message_shape():
    dev = device()
    signal = dev.encode(None, HvacState(True, "cool", 22.0)).signal
    assert signal.pulses[:2] == (3400, 3400)
    assert signal.pulses[-2:] == (400, 100000)
    assert len(signal.pulses) == 2 + 2 * 104 + 2


@pytest.mark.parametrize("model", HITACHI1_MODELS)
def test_registry_serves_the_port(model):
    dev = registry.get_device("hitachi", model)
    assert isinstance(dev, Hitachi1Device)
    assert dev.variant == HITACHI1_MODELS[model]


@pytest.mark.parametrize("model", HITACHI1_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.hitachi import PluginObject

    legacy = LegacyDevice("hitachi", model, PluginObject.MODELS[model])
    assert Hitachi1Device("hitachi", model).capabilities == legacy.capabilities


def _first(pred):
    return next(r for r in load_oracle("HITACHI_AC1") if pred(r))


@pytest.mark.parametrize(
    "pred, field",
    [
        (
            lambda r: r["state"].get("swing") == "on" and r["state"]["mode"] != "off",
            "swing_v",
        ),
        (lambda r: r["state"].get("hswing") == "on", "swing_h"),
        (lambda r: r["state"].get("sleep") == "on", "sleep"),
        (
            lambda r: r["state"]["mode"] == "heat" and r["state"].get("fan") == "high",
            "fan",
        ),
        (
            lambda r: r["state"]["mode"] == "fan" and r["state"].get("fan") == "medium",
            "fan",
        ),
    ],
)
def test_undeclared_deviation_is_reported(pred, field):
    record = _first(pred)
    dev = _device_for(record)
    with pytest.raises(AssertionError, match=field):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_swing_toggle_deviation_is_declared_separately():
    record = _first(lambda r: r["state"].get("hswing") == "on")
    dev = _device_for(record)
    only_swing_h = [d for d in DEFECTS if d.field == "swing_h"]
    with pytest.raises(AssertionError, match="swing_toggle"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, only_swing_h)


def test_layouts_must_cover_every_frame():
    record = load_oracle("HITACHI_AC1")[0]
    dev = _device_for(record)
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_hitachi1_device.py -q`
Expected: collection error, `ImportError: cannot import name ...` from `pyhvac.plugins.hitachi`.

- [ ] **Step 3: Implement**: insert immediately before `# Now the match between models and objects` in `pyhvac/plugins/hitachi.py`:

```python
# ------------------------------------------------------------- Hitachi1
# Layout from IRremoteESP8266's Hitachi1Protocol (ir_Hitachi.h): one 13-byte
# frame, bytes in order, each sent MSB first (sendHitachiAC1: sendGeneric
# with MSBfirst). Header kHitachiAc1HdrMark/HdrSpace, bits
# kHitachiAcBitMark/ZeroSpace/OneSpace, gap kHitachiAcMinGap
# (kDefaultMessageGap), carrier kHitachiAcFreq.

HITACHI1 = Protocol(
    "hitachi1",
    {
        "main": Section(
            PulseDistance(400, 500, 1250),
            header=(3400, 3400),
            footer=(400,),
            gap=100000,
            lsb_first=False,
        )
    },
    carrier=38000,
)


@dataclass(frozen=True)
class Hitachi1Checksum(NibbleSum):
    """IRHitachiAc1::calcChecksum: the sum of every nibble of data[start:end],
    each nibble bit-reversed, stored bit-reversed.

    ``reverse=True`` covers the per-nibble reversal (the nibbles of a
    reversed byte are its nibbles reversed); NibbleSum writes its result as
    computed, so the final reversal needs this subclass. The checksum is a
    whole byte (kHitachiAc1ChecksumStartByte..Sum).
    """

    reverse: bool = True

    def compute(self, data):
        return bit_reverse(super().compute(data))


def _rev5(n):
    return int(f"{n:05b}"[::-1], 2)


HITACHI1_MIN_TEMP, HITACHI1_MAX_TEMP = 16, 32  # kHitachiAcMin/MaxTemp
HITACHI1_TEMP_AUTO = 25  # kHitachiAc1TempAuto
HITACHI1_SLEEP = 0b010  # kHitachiAc1Sleep2: what IRac sends for any sleep

HITACHI1_LAYOUT = Layout(
    # IRHitachiAc1::stateReset with the written fields and the sum cleared:
    # byte 6 bit 7 stays set, the timers (bytes 7-10) are never set by IRac.
    bytes.fromhex("b2ae4d11f00080000000000000"),
    {
        "model": Field.at(3, 6, 2, values={"A": 0b10, "B": 0b01}),
        "fan": Field.at(  # kHitachiAc1Fan*
            5, 0, 4, values={"auto": 1, "1": 8, "2": 4, "3": 2}
        ),
        "mode": Field.at(  # kHitachiAc1*
            5,
            4,
            4,
            values={
                "dry": 0b0010,
                "fan": 0b0100,
                "cool": 0b0110,
                "heat": 0b1001,
                "auto": 0b1110,
            },
        ),
        # (celsius - kHitachiAc1TempDelta), 5 bits reversed
        "temperature": Field.at(
            6,
            2,
            5,
            values={
                t: _rev5(t - 7) for t in range(HITACHI1_MIN_TEMP, HITACHI1_MAX_TEMP + 1)
            },
        ),
        "swing_toggle": Field.at(11, 0, 1),
        "sleep": Field.at(11, 1, 3),  # kHitachiAc1Sleep*
        "power_toggle": Field.at(11, 4, 1),
        "power": Field.at(11, 5, 1),
        "swing_v": Field.at(11, 6, 1, values={"off": 0, "swing": 1}),
        "swing_h": Field.at(11, 7, 1, values={"off": 0, "swing": 1}),
    },
    checksum=Hitachi1Checksum(5, 12, 12),
)


class Hitachi1Device(Device):
    """Hitachi AC1 (R-LT0541-HTA, remote variants A and B): full state plus a
    power toggle and a swing toggle bit.

    The variant ("A" or "B", kHitachiAc1Model_A/B) comes from the model
    (HITACHI1_MODELS) unless given, so the registry's ``cls(brand, model)``
    call picks it; unknown models get A, as IRHitachiAc1::setModel does.

    Toggles, as IRac::sendAc does for HITACHI_AC1 (not handleToggles): the
    power toggle is set when the power changes, the swing toggle when
    swing_v or swing_h changes. IRac compares against its previous state,
    and a fresh IRac's previous state is the stdAc default (power off, both
    swings off), so without ``previous`` this device compares against that:
    power toggle = target.power, swing toggle = any swing on. This matches
    the C path in both cases.
    """

    PROTOCOL = HITACHI1
    LAYOUTS = (HITACHI1_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "heat", "cool", "dry", "fan"),
        temperature=TemperatureRange(16.0, 32.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
        ),
        swing_v=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
        swing_h=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
        features={"sleep": Choice((False, True), {False: "off", True: "on"})},
    )

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        self.variant = variant or HITACHI1_MODELS.get(model, "A")
        if self.variant not in ("A", "B"):
            raise ValueError(f"unknown Hitachi1 variant {self.variant!r}")

    def frames(self, previous, target, actions):
        if previous is None:  # a fresh IRac: its previous state is all off
            power_toggle = target.power
            swing_toggle = target.swing_v != "off" or target.swing_h != "off"
        else:
            power_toggle = previous.power != target.power
            swing_toggle = (
                previous.swing_v != target.swing_v or previous.swing_h != target.swing_h
            )
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to auto).
        mode = target.mode if target.power else "auto"
        # setTemp is ignored in auto: the reset state's kHitachiAc1TempAuto.
        temperature = HITACHI1_TEMP_AUTO if mode == "auto" else int(target.temperature)
        fan = target.fan
        if mode == "auto":
            fan = "auto"  # setFan: auto is locked to auto speed
        elif mode == "dry":
            fan = "1"  # setFan: dry is locked to low speed
        elif mode in ("heat", "fan") and fan == "auto":
            fan = "1"  # setFan: no auto speed in heat and fan, low instead
        data = HITACHI1_LAYOUT.build(
            model=self.variant,
            mode=mode,
            temperature=temperature,
            fan=fan,
            swing_v=target.swing_v,
            swing_h=target.swing_h,
            # IRac's Sleep2 for any sleep; setSleep: only in auto and cool.
            sleep=(
                HITACHI1_SLEEP
                if target.features["sleep"] and mode in ("auto", "cool")
                else 0
            ),
            power=target.power,
            power_toggle=power_toggle,
            swing_toggle=swing_toggle,
        )
        return [Frame("main", bytes(data))]


HITACHI1_MODELS = {  # model -> remote variant (hitachi_ac1_remote_model_t)
    "LT0541-HTA remote": "A",
    "Series VI": "A",
    "KAZE-312KSDP": "A",
    "R-LT0541-HTA/Y.K.1.1-1 V2.3 remote": "A",
    "generic 1 code a": "A",
    "generic 1 code b": "B",
}


DEVICES.update({m: Hitachi1Device for m in HITACHI1_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_hitachi1_device.py -q`
Expected: 360 passed, 6 skipped (the skips need the C extension).

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/hitachi.py tests/test_hitachi1_device.py
git add pyhvac/plugins/hitachi.py tests/test_hitachi1_device.py
git commit -m "HITACHI_AC1: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 4: HITACHI_AC424

Bitless leader + one 53-byte frame with inverted byte pairs (`InvertedPairs(3, 53)`); swing is a BUTTON toggle using `previous` (IRac::handleToggles implements the same rule).

**Files:**
- Modify: `pyhvac/plugins/hitachi.py` (block before `# Now the match between models and objects`)
- Test: `tests/test_hitachi424_device.py`

**Interfaces:**
- Consumes: `Device`, `pyhvac.fields`, bitless sections, `tests/port_oracle.py`, and the oracle fixture `HITACHI_AC424`.
- Produces: `Hitachi424Device`, `HITACHI424_MODELS`, and the `DEVICES` entries for those models.

- [ ] **Step 1: Write the failing tests**: create `tests/test_hitachi424_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.fields import InvertedPairs
from pyhvac.ir.codec import decode
from pyhvac.plugins.hitachi import (
    HITACHI424,
    HITACHI424_LAYOUT,
    HITACHI424_MODELS,
    Hitachi424Device,
)
from pyhvac.state import HvacState

# The C path never sends swing on: the old vocabulary's "on" has no entry in
# IRGHVAC.trans_swing, so build_ircode skips the key, swingv stays kOff, and
# IRac::hitachi424's setSwingVToggle(false) leaves the button at
# kHitachiAc424ButtonPowerMode instead of kHitachiAc424ButtonSwingV.
DEFECTS = (Defect("button", "swing_v", "power_mode", "C glue has no 'on' swing"),)


def device():
    return Hitachi424Device("hitachi", "RAR-8P2 remote")


def read(state, previous=None):
    dev = device()
    if previous is not None:
        previous = dev.normalise(previous)
    _, main = dev.frames(previous, dev.normalise(state), ())
    return HITACHI424_LAYOUT.read(main.data)


@pytest.mark.parametrize("record", oracle_params("HITACHI_AC424"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("HITACHI_AC424"):
        state = state_from_record(dev, record["state"])
        _, main = dev.frames(None, state, ())
        values = HITACHI424_LAYOUT.read(main.data)
        assert HITACHI424_LAYOUT.build(**values) == bytearray(main.data)


def test_every_oracle_frame_has_inverted_pairs_from_byte_3():
    # IRHitachiAc424::setInvertedStates: invertBytePairs(raw + 3, 50).
    for record in load_oracle("HITACHI_AC424"):
        _, main = decode(HITACHI424, record["pulses"], expected=["leader", "main"])
        assert InvertedPairs(3, 53).check(main.data)


def test_skeleton_is_the_reset_state():
    # stateReset, then off in cool at 16 °C with fan auto: the whole frame
    # of the oracle's first record (which is that state).
    record = load_oracle("HITACHI_AC424")[0]
    assert record["state"] == {
        "mode": "off",
        "temperature": 16,
        "fan": "auto",
        "swing": "off",
    }
    _, main = decode(HITACHI424, record["pulses"], expected=["leader", "main"])
    data = HITACHI424_LAYOUT.build(
        fan_aux9=0x92,
        button="power_mode",
        temperature=16,
        mode="cool",
        fan="auto",
        power=0,
        fan_aux29=0,
    )
    assert bytes(data) == main.data


@pytest.mark.parametrize("mode", ["fan", "heat", "cool", "dry"])
@pytest.mark.parametrize("temp", [16.0, 23.0, 32.0])
def test_off_carries_mode_cool_in_every_mode(mode, temp):
    # IRac passes mode "off"; IRHitachiAc424::convertMode maps it to cool.
    values = read(HvacState(False, mode, temp))
    assert (values["power"], values["mode"], values["temperature"]) == (
        0,
        "cool",
        int(temp),
    )
    assert values["fan"] == "auto"


def test_fan_mode_keeps_the_setpoint():
    # setMode(fan) writes kHitachiAc424FanTemp, but IRac's setTemp follows.
    assert read(HvacState(True, "fan", 18.0, fan="2"))["temperature"] == 18


def test_setpoint_is_clamped_to_16_32():
    assert read(HvacState(True, "cool", 10.0))["temperature"] == 16
    assert read(HvacState(True, "heat", 40.0))["temperature"] == 32


@pytest.mark.parametrize(
    "mode, fan, sent",
    [
        ("cool", "auto", "auto"),
        ("cool", "5", "5"),
        ("heat", "1", "1"),
        ("dry", "auto", "auto"),  # dry keeps auto
        ("dry", "1", "1"),
        ("dry", "2", "2"),
        ("dry", "3", "2"),  # kHitachiAc424FanMaxDry
        ("dry", "4", "2"),
        ("dry", "5", "2"),
        ("fan", "auto", "1"),  # fan mode has no auto: Min
        ("fan", "5", "5"),
    ],
)
def test_fan_is_limited_per_mode(mode, fan, sent):
    assert read(HvacState(True, mode, 24.0, fan=fan))["fan"] == sent


@pytest.mark.parametrize(
    "fan, raw, aux9, aux29",
    [
        ("auto", 5, 0x92, 0x00),
        ("1", 1, 0x98, 0x00),
        ("2", 2, 0x92, 0x00),
        ("3", 3, 0x92, 0x00),
        ("4", 4, 0x92, 0x00),
        ("5", 6, 0xA9, 0x30),
    ],
)
def test_every_fan_level_and_its_extra_bytes(fan, raw, aux9, aux29):
    dev = device()
    _, main = dev.frames(
        None, dev.normalise(HvacState(True, "cool", 24.0, fan=fan)), ()
    )
    assert HITACHI424_LAYOUT.read_raw(main.data, "fan") == raw
    assert (main.data[9], main.data[29]) == (aux9, aux29)


def test_button_is_power_mode_without_swing():
    assert read(HvacState(True, "cool", 24.0))["button"] == "power_mode"
    assert read(HvacState(False, "cool", 24.0))["button"] == "power_mode"


def test_swing_without_previous_presses_the_swing_button():
    # A fresh IRac has no previous state: swing on -> setSwingVToggle(true).
    state = HvacState(True, "cool", 24.0, swing_v="swing")
    assert read(state)["button"] == "swing_v"
    dev = device()
    _, main = dev.frames(None, dev.normalise(state), ())
    assert main.data[11] == 0x81


@pytest.mark.parametrize(
    "before, after, button",
    [
        ("off", "off", "power_mode"),
        ("off", "swing", "swing_v"),
        ("swing", "swing", "power_mode"),
        ("swing", "off", "swing_v"),
    ],
)
def test_swing_button_with_previous_only_on_change(before, after, button):
    # IRac::handleToggles (HITACHI_AC424): toggle only when swing changes.
    previous = HvacState(True, "cool", 24.0, swing_v=before)
    target = HvacState(True, "cool", 25.0, swing_v=after)
    assert read(target, previous)["button"] == button


def test_encode_passes_previous_to_the_swing_button():
    dev = device()
    on = HvacState(True, "cool", 22.0, swing_v="swing")
    assert dev.encode(None, on).signal != dev.encode(on, on).signal


def test_message_shape():
    dev = device()
    pulses = dev.encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:4] == (29784, 49290, 3416, 1604)
    assert pulses[-2:] == (463, 100000)
    assert len(pulses) == 2 + 2 + 2 * 424 + 2


@pytest.mark.parametrize("model", HITACHI424_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("hitachi", model), Hitachi424Device)


@pytest.mark.parametrize("model", HITACHI424_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.hitachi import Hitachi424

    legacy = LegacyDevice("hitachi", model, Hitachi424)
    assert Hitachi424Device("hitachi", model).capabilities == legacy.capabilities


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(
        r for r in load_oracle("HITACHI_AC424") if r["state"].get("swing") == "on"
    )
    with pytest.raises(AssertionError, match="button"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("HITACHI_AC424")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:1], DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_hitachi424_device.py -q`
Expected: collection error, `ImportError: cannot import name ...` from `pyhvac.plugins.hitachi`.

- [ ] **Step 3: Implement**: insert immediately before `# Now the match between models and objects` in `pyhvac/plugins/hitachi.py`:

```python
# ------------------------------------------------------------- Hitachi424
# Layout from IRremoteESP8266's Hitachi424Protocol (ir_Hitachi.h): 53 bytes,
# each sent LSB first, after a bitless leader (kHitachiAc424LdrMark/Space).
# From byte 3 on, every even byte is the complement of the byte before it
# (IRHitachiAc424::setInvertedStates), so every field sits in an odd byte.

HITACHI424 = Protocol(
    "hitachi424",
    {
        "leader": Section(None, header=(29784,), gap=49290),
        "main": Section(
            PulseDistance(463, 372, 1208),  # kHitachiAc424BitMark/Zero/OneSpace
            header=(3416, 1604),  # kHitachiAc424HdrMark/HdrSpace
            footer=(463,),
            gap=100000,  # kHitachiAcMinGap
        ),
    },
    carrier=38000,  # kHitachiAcFreq
)

HITACHI424_BUTTON = {  # kHitachiAc424Button*
    "power_mode": 0x13,
    "fan": 0x42,
    "temp_down": 0x43,
    "temp_up": 0x44,
    "swing_v": 0x81,
    "swing_h": 0x8C,
}
HITACHI424_FAN = {  # canonical fan -> kHitachiAc424Fan*
    "auto": 5,  # Auto
    "1": 1,  # Min
    "2": 2,  # Low
    "3": 3,  # Medium
    "4": 4,  # High
    "5": 6,  # Max
}

# Skeleton: IRHitachiAc424::stateReset's bytes, pairs inverted, with every
# field cleared. Bytes 9 and 29 are struct padding, but setFan writes them.
HITACHI424_LAYOUT = Layout(
    bytes.fromhex(
        "01100040bfff00cc3300ff00ff00ff00ff00ff00ff00ff00ff00ff"
        "e11e00ff00ff807f03fc01fe887700ff00ffff00ff00ff00ff00"
    ),
    {
        "fan_aux9": Field.at(9, 0, 8),  # 0x98 fan Min, 0xA9 Max, else 0x92
        "button": Field.at(11, 0, 8, values=HITACHI424_BUTTON),
        "temperature": Field.at(13, 2, 6),  # whole °C
        "mode": Field.at(25, 0, 4, values={"fan": 1, "cool": 3, "dry": 5, "heat": 6}),
        "fan": Field.at(25, 4, 4, values=HITACHI424_FAN),
        "power": Field.at(27, 4, 1),
        "fan_aux29": Field.at(29, 0, 8),  # 0x30 fan Max, else 0x00
        # IRHitachiAc344 only: the 424 class has no setter, skeleton kept.
        "swing_h_344": Field.at(35, 0, 3),
        "swing_v_344": Field.at(37, 5, 1),
    },
    checksum=InvertedPairs(3, 53),
)


class Hitachi424Device(Device):
    """Hitachi424 (RAR-8P2): full state, except that vertical swing is a
    button (byte 11): the remote keeps no swing state.

    Every message carries kHitachiAc424ButtonPowerMode, as the C path does
    (IRac::hitachi424 calls setPower last, whatever changed), unless swing is
    toggled: then kHitachiAc424ButtonSwingV. With ``previous`` the swing
    button is sent only when swing changes between off and on, the rule
    IRac::handleToggles applies to HITACHI_AC424 when it is given a previous
    state. Without ``previous`` it is sent whenever swing is on, as a fresh
    IRac sends it (no previous state, no toggle handling).
    """

    PROTOCOL = HITACHI424
    LAYOUTS = (None, HITACHI424_LAYOUT)
    capabilities = Capabilities(
        modes=("fan", "heat", "cool", "dry"),
        temperature=TemperatureRange(16.0, 32.0),
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
        swing_v=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode cool (IRac passes mode
        # "off", which convertMode maps to cool).
        mode = target.mode if target.power else "cool"
        fan = target.fan
        # IRHitachiAc424::setFan: dry allows auto, Min and Low only
        # (kHitachiAc424FanMaxDry); fan mode has no auto and uses Min.
        if mode == "dry" and fan in ("3", "4", "5"):
            fan = "2"
        elif mode == "fan" and fan == "auto":
            fan = "1"
        if previous is None:
            swing = target.swing_v != "off"
        else:
            swing = (target.swing_v != "off") != (previous.swing_v != "off")
        data = HITACHI424_LAYOUT.build(
            fan_aux9={"1": 0x98, "5": 0xA9}.get(fan, 0x92),
            button="swing_v" if swing else "power_mode",
            # IRac's setTemp(degrees) comes after setMode, so fan mode's
            # kHitachiAc424FanTemp never survives.
            temperature=int(target.temperature),
            mode=mode,
            fan=fan,
            power=target.power,
            fan_aux29=0x30 if fan == "5" else 0x00,
        )
        return [Frame("leader", b""), Frame("main", bytes(data))]


HITACHI424_MODELS = ("RAR-8P2 remote", "RAS-AJ25H", "generic 424")


DEVICES.update({m: Hitachi424Device for m in HITACHI424_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_hitachi424_device.py -q`
Expected: 227 passed, 3 skipped (the skips need the C extension).

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/hitachi.py tests/test_hitachi424_device.py
git add pyhvac/plugins/hitachi.py tests/test_hitachi424_device.py
git commit -m "HITACHI_AC424: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 5: HITACHI_AC344

One 43-byte frame with inverted pairs; `Hitachi424Protocol` layout plus the kHitachiAc344* values; swing button toggle as HITACHI_AC424.

**Files:**
- Modify: `pyhvac/plugins/hitachi.py` (block before `# Now the match between models and objects`)
- Test: `tests/test_hitachi344_device.py`

**Interfaces:**
- Consumes: `Device`, `pyhvac.fields`, bitless sections, `tests/port_oracle.py`, and the oracle fixture `HITACHI_AC344`.
- Produces: `Hitachi344Device`, `HITACHI344_MODELS`, and the `DEVICES` entries for those models.

- [ ] **Step 1: Write the failing tests**: create `tests/test_hitachi344_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.ir.codec import decode
from pyhvac.plugins.hitachi import (
    HITACHI344,
    HITACHI344_LAYOUT,
    HITACHI344_MODELS,
    Hitachi344Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Hitachi344 values here:
# - the old glue (IRGHVAC.trans_swing) has no "on" entry, so IRac keeps
#   swingv kOff and IRac::hitachi344's setSwingVToggle(false) leaves the
#   button at kHitachiAc344ButtonPowerMode (0x13) instead of
#   kHitachiAc344ButtonSwingV (0x81).
DEFECTS = (Defect("button", "swing_v", "power_mode", "C path never sends swing: 0x13"),)


def device():
    return Hitachi344Device("hitachi", "RAS-22NK")


def with_hswing(record):
    # A record without "hswing" leaves IRac's swingh at kOff, which
    # IRHitachiAc344::convertSwingH maps to its default, Middle: canonical "3"
    # (checked against the C path in cpath_check.py). The port has no "off"
    # swing_h (the legacy entity has none), so the record is read as "middle".
    if "hswing" in record["state"]:
        return record
    return {**record, "state": {**record["state"], "hswing": "middle"}}


def read(state, previous=None):
    dev = device()
    if previous is not None:
        previous = dev.normalise(previous)
    (main,) = dev.frames(previous, dev.normalise(state), ())
    return HITACHI344_LAYOUT.read(main.data)


@pytest.mark.parametrize("record", oracle_params("HITACHI_AC344"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, with_hswing(record), dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("HITACHI_AC344"):
        state = state_from_record(dev, with_hswing(record)["state"])
        (main,) = dev.frames(None, state, ())
        values = HITACHI344_LAYOUT.read(main.data)
        assert HITACHI344_LAYOUT.build(**values) == bytearray(main.data)


def test_every_oracle_frame_has_inverted_pairs_from_byte_3():
    # portkit checksum only tries InvertedPairs(0, n) on even lengths.
    for record in load_oracle("HITACHI_AC344"):
        (frame,) = decode(HITACHI344, record["pulses"], expected=["main"])
        assert HITACHI344_LAYOUT.checksum.check(frame.data)


def test_no_field_sits_in_a_complement_byte():
    complements = HITACHI344_LAYOUT.checksum.positions()
    for name, f in HITACHI344_LAYOUT.fields.items():
        assert not {b // 8 for b in f.bits} & complements, name


@pytest.mark.parametrize("mode", ["cool", "fan", "dry", "heat"])
@pytest.mark.parametrize("t", [16.0, 32.0])
def test_off_carries_mode_cool_in_every_mode(mode, t):
    # IRac passes mode "off"; IRHitachiAc424::convertMode maps it to cool.
    values = read(HvacState(False, mode, t))
    assert (values["mode"], values["temperature"], values["power"]) == (
        "cool",
        int(t),
        0,
    )


def test_fan_mode_keeps_the_setpoint():
    # IRac calls setTemp(degrees) after setMode, which had set
    # kHitachiAc424FanTemp (27).
    assert read(HvacState(True, "fan", 18.0))["temperature"] == 18


@pytest.mark.parametrize(
    "fan, code, byte9, byte29",
    [
        ("auto", 5, 0x92, 0x00),
        ("1", 1, 0x98, 0x00),
        ("2", 2, 0x92, 0x00),
        ("3", 3, 0x92, 0x00),
        ("4", 4, 0x92, 0x00),
        ("5", 6, 0xA9, 0x30),
    ],
)
def test_every_fan_level_uses_its_documented_value(fan, code, byte9, byte29):
    dev = device()
    (main,) = dev.frames(
        None, dev.normalise(HvacState(True, "cool", 22.0, fan=fan)), ()
    )
    raw = {k: HITACHI344_LAYOUT.read_raw(main.data, k) for k in ("fan", "fan_byte9")}
    assert (raw["fan"], raw["fan_byte9"], main.data[29]) == (code, byte9, byte29)


@pytest.mark.parametrize(
    "fan, code", [("auto", 5), ("1", 1), ("2", 2), ("3", 2), ("4", 2), ("5", 2)]
)
def test_dry_allows_auto_or_up_to_low(fan, code):
    dev = device()
    (main,) = dev.frames(None, dev.normalise(HvacState(True, "dry", 22.0, fan=fan)), ())
    assert HITACHI344_LAYOUT.read_raw(main.data, "fan") == code


def test_fan_mode_has_no_auto_fan():
    dev = device()
    (main,) = dev.frames(None, dev.normalise(HvacState(True, "fan", 22.0)), ())
    assert HITACHI344_LAYOUT.read_raw(main.data, "fan") == 1
    assert main.data[9] == 0x98


@pytest.mark.parametrize(
    "swing_h, raw", [("auto", 0), ("1", 5), ("2", 4), ("3", 3), ("4", 2), ("5", 1)]
)
def test_every_swing_h_position(swing_h, raw):
    dev = device()
    (main,) = dev.frames(
        None, dev.normalise(HvacState(True, "cool", 22.0, swing_h=swing_h)), ()
    )
    assert HITACHI344_LAYOUT.read_raw(main.data, "swing_h") == raw


def test_swing_v_without_previous_presses_the_swing_button():
    # A fresh IRac (no previous state for the protocol) passes swingv as is.
    assert read(HvacState(True, "cool", 22.0, swing_v="swing"))["button"] == "swing_v"
    assert read(HvacState(True, "cool", 22.0))["button"] == "power_mode"


@pytest.mark.parametrize(
    "before, after, button",
    [
        ("off", "off", "power_mode"),
        ("off", "swing", "swing_v"),
        ("swing", "off", "swing_v"),
        ("swing", "swing", "power_mode"),
    ],
)
def test_swing_v_with_previous_toggles_on_change(before, after, button):
    # As IRac::handleToggles does for HITACHI_AC344 with a previous state.
    previous = HvacState(True, "cool", 22.0, swing_v=before)
    target = HvacState(True, "cool", 22.0, swing_v=after)
    assert read(target, previous)["button"] == button


def test_swing_v_state_bit_is_never_set():
    # IRac::hitachi344 only calls setSwingVToggle, never setSwingV.
    assert read(HvacState(True, "cool", 22.0, swing_v="swing"))["swing_v"] == 0


def test_encode_passes_previous_to_the_toggle():
    dev = device()
    on = HvacState(True, "cool", 22.0, swing_v="swing")
    assert dev.encode(None, on).signal != dev.encode(on, on).signal


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (3300, 1700)
    assert pulses[-2:] == (400, 100000)
    assert len(pulses) == 2 + 2 * 344 + 2


@pytest.mark.parametrize("model", HITACHI344_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("hitachi", model), Hitachi344Device)


@pytest.mark.parametrize("model", HITACHI344_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.hitachi import Hitachi344

    legacy = LegacyDevice("hitachi", model, Hitachi344)
    assert Hitachi344Device("hitachi", model).capabilities == legacy.capabilities


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(
        r for r in load_oracle("HITACHI_AC344") if r["state"].get("swing") == "on"
    )
    with pytest.raises(AssertionError, match="button"):
        assert_matches_oracle(dev, with_hswing(record), dev.LAYOUTS, defects=())


def test_missing_hswing_is_not_silently_accepted():
    dev = device()
    record = next(r for r in load_oracle("HITACHI_AC344") if "hswing" not in r["state"])
    with pytest.raises(AssertionError, match="swing_h"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_hitachi344_device.py -q`
Expected: collection error, `ImportError: cannot import name ...` from `pyhvac.plugins.hitachi`.

- [ ] **Step 3: Implement**: insert immediately before `# Now the match between models and objects` in `pyhvac/plugins/hitachi.py`:

```python
# ------------------------------------------------------------- Hitachi344
# Layout from IRremoteESP8266's Hitachi424Protocol (ir_Hitachi.h), which
# IRHitachiAc344 reuses for its 43 bytes (kHitachiAc344StateLength), with the
# kHitachiAc344* values and the 344-only SwingH (byte 35) and SwingV (byte 37)
# fields. Sent by sendHitachiAC: one frame, LSB first (MSBfirst is false for
# kHitachiAc344StateLength), closed by kHitachiAcMinGap. From byte 3 on,
# every second byte is the complement of the one before it
# (IRHitachiAc424::setInvertedStates).

HITACHI344 = Protocol(
    "hitachi344",
    {
        "main": Section(
            PulseDistance(400, 500, 1250),  # kHitachiAcBitMark/ZeroSpace/OneSpace
            header=(3300, 1700),  # kHitachiAcHdrMark/HdrSpace
            footer=(400,),
            gap=100000,  # kHitachiAcMinGap = kDefaultMessageGap
        )
    },
    carrier=38000,  # kHitachiAcFreq
)

HITACHI344_BUTTON = {  # kHitachiAc344Button*
    "power_mode": 0x13,
    "fan": 0x42,
    "temp_down": 0x43,
    "temp_up": 0x44,
    "swing_v": 0x81,
    "swing_h": 0x8C,
}
HITACHI344_FAN = {  # canonical fan -> kHitachiAc344Fan*
    "1": 1,  # lowest: kHitachiAc344FanMin
    "2": 2,  # kHitachiAc344FanLow
    "3": 3,  # kHitachiAc344FanMedium
    "4": 4,  # kHitachiAc344FanHigh
    "auto": 5,  # kHitachiAc344FanAuto
    "5": 6,  # highest: kHitachiAc344FanMax
}
HITACHI344_SWING_H = {  # canonical position -> kHitachiAc344SwingH*
    "auto": 0,  # kHitachiAc344SwingHAuto
    "1": 5,  # far left: kHitachiAc344SwingHLeftMax
    "2": 4,  # kHitachiAc344SwingHLeft
    "3": 3,  # kHitachiAc344SwingHMiddle
    "4": 2,  # kHitachiAc344SwingHRight
    "5": 1,  # far right: kHitachiAc344SwingHRightMax
}

# Skeleton from IRHitachiAc344::stateReset with the written fields cleared
# (the complements are recomputed by the checksum).
HITACHI344_LAYOUT = Layout(
    bytes.fromhex(
        "01100040bfff00cc3300ff00ff00ff00ff00ff00ff00ff00ff00ffe11e00ff00ff807f00ff00ff00ff00ff"
    ),
    {
        # raw[9] and raw[29] are not in the struct: IRHitachiAc424::setFan
        # writes 0x92/0x00, 0x98 for FanMin, and 0xA9/0x30 for FanMax.
        "fan_byte9": Field.at(9, 0, 8),
        "button": Field.at(11, 0, 8, values=HITACHI344_BUTTON),
        "temperature": Field.at(13, 2, 6, encode=int),  # whole °C
        "mode": Field.at(25, 0, 4, values={"fan": 1, "cool": 3, "dry": 5, "heat": 6}),
        "fan": Field.at(25, 4, 4, values=HITACHI344_FAN),
        "power": Field.at(27, 4, 1),
        "fan_byte29": Field.at(29, 0, 8),
        "swing_h": Field.at(35, 0, 3, values=HITACHI344_SWING_H),
        # The SwingV state bit (IRHitachiAc344::setSwingV). IRac::hitachi344
        # never calls setSwingV, only setSwingVToggle (the button), so the C
        # path always sends it clear; the port does too.
        "swing_v": Field.at(37, 5, 1),
    },
    checksum=InvertedPairs(3, 43),
)


class Hitachi344Device(Device):
    """Hitachi344 (RAS-22NK, RF11T1): full state, plus a swing toggle.

    Vertical swing is sent as a button press (``button`` = swing_v, byte 11),
    which toggles the louvre. With ``previous`` the button is pressed only
    when swing_v changes, as IRac::handleToggles does for HITACHI_AC344 with
    a previous state. With ``previous=None`` it is pressed when swing_v is
    "swing", as a fresh IRac sends. Otherwise the button is power/mode:
    IRac::hitachi344 calls setPower last, and setSwingVToggle only replaces
    the button when swing is asked for.
    """

    PROTOCOL = HITACHI344
    LAYOUTS = (HITACHI344_LAYOUT,)
    capabilities = Capabilities(
        modes=("cool", "fan", "dry", "heat"),
        temperature=TemperatureRange(16.0, 32.0),
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
        swing_v=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
        swing_h=Choice(
            ("auto", "1", "2", "3", "4", "5"),
            {
                "auto": "auto",
                "1": "far left",
                "2": "left",
                "3": "middle",
                "4": "right",
                "5": "far right",
            },
        ),
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode cool (IRac passes mode
        # "off", which convertMode maps to cool).
        mode = target.mode if target.power else "cool"
        # IRHitachiAc424::setFan: dry allows auto or up to low; fan mode has
        # no auto and falls back to min.
        fan = HITACHI344_FAN[target.fan]
        if mode == "dry" and fan != HITACHI344_FAN["auto"]:
            fan = min(fan, 2)  # kHitachiAc424FanMaxDry
        elif mode == "fan" and fan == HITACHI344_FAN["auto"]:
            fan = 1  # kHitachiAc424FanMin
        if previous is None:
            press = target.swing_v != "off"
        else:
            press = target.swing_v != previous.swing_v
        data = HITACHI344_LAYOUT.build(
            fan_byte9={1: 0x98, 6: 0xA9}.get(fan, 0x92),
            button="swing_v" if press else "power_mode",
            # IRac's setTemp comes after setMode, so fan mode keeps the
            # setpoint rather than kHitachiAc424FanTemp.
            temperature=int(target.temperature),
            mode=mode,
            fan=HITACHI344_LAYOUT.fields["fan"].from_int(fan),
            power=target.power,
            fan_byte29=0x30 if fan == 6 else 0x00,
            swing_h=target.swing_h,
            swing_v=0,
        )
        return [Frame("main", bytes(data))]


HITACHI344_MODELS = ("RAS-22NK", "RF11T1", "generic 344")


DEVICES.update({m: Hitachi344Device for m in HITACHI344_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_hitachi344_device.py -q`
Expected: 229 passed, 3 skipped (the skips need the C extension).

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/hitachi.py tests/test_hitachi344_device.py
git add pyhvac/plugins/hitachi.py tests/test_hitachi344_device.py
git commit -m "HITACHI_AC344: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 6: HITACHI_AC264

One 33-byte frame with inverted pairs; the button is always power/mode; swing and five features are advertised (legacy entity) but, as in the C path, send nothing.

**Files:**
- Modify: `pyhvac/plugins/hitachi.py` (block before `# Now the match between models and objects`)
- Test: `tests/test_hitachi264_device.py`

**Interfaces:**
- Consumes: `Device`, `pyhvac.fields`, bitless sections, `tests/port_oracle.py`, and the oracle fixture `HITACHI_AC264`.
- Produces: `Hitachi264Device`, `HITACHI264_MODELS`, and the `DEVICES` entries for those models.

- [ ] **Step 1: Write the failing tests**: create `tests/test_hitachi264_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.ir.model import Frame
from pyhvac.plugins.hitachi import (
    HITACHI264_LAYOUT,
    HITACHI264_MODELS,
    Hitachi264Device,
)
from pyhvac.state import HvacState

# No declared defects: the C path sends the documented values for every
# field it writes. Swing and the features have no bits (IRac::hitachi264
# sets none of them), so the oracle's swing "on" records match as they are.


def device():
    return Hitachi264Device("hitachi", "RAR-2P2 remote")


def read(state, previous=None):
    dev = device()
    (frame,) = dev.frames(previous, dev.normalise(state), ())
    return HITACHI264_LAYOUT.read(frame.data)


@pytest.mark.parametrize("record", oracle_params("HITACHI_AC264"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("HITACHI_AC264"):
        state = state_from_record(dev, record["state"])
        (frame,) = dev.frames(None, state, ())
        values = HITACHI264_LAYOUT.read(frame.data)
        assert HITACHI264_LAYOUT.build(**values) == bytearray(frame.data)


def test_bytes_3_to_32_are_inverted_pairs():
    (frame,) = device().frames(None, HvacState(True, "heat", 21.0), ())
    data = frame.data
    assert len(data) == 33
    assert all(data[i + 1] == data[i] ^ 0xFF for i in range(3, 33, 2))
    assert data[:3] == bytes.fromhex("011000")


def test_no_field_sits_on_an_inverted_byte():
    inverted = HITACHI264_LAYOUT.checksum.positions()
    for name, field in HITACHI264_LAYOUT.fields.items():
        assert not {bit // 8 for bit in field.bits} & inverted, name


@pytest.mark.parametrize("mode", ["auto", "cool", "fan", "dry", "heat"])
def test_off_carries_mode_cool_in_every_mode(mode):
    # IRac passes the off mode through IRHitachiAc424::convertMode: cool.
    for t in (16.0, 24.0, 32.0):
        values = read(HvacState(False, mode, t, fan="2"))
        assert (values["power"], values["mode"]) == (0, "cool")
        assert (values["temperature"], values["fan"]) == (int(t), "2")


def test_auto_mode_is_sent_as_cool():
    # IRHitachiAc424::convertMode has no auto; kHitachiAc264* has none either.
    assert read(HvacState(True, "auto", 24.0))["mode"] == "cool"


@pytest.mark.parametrize("mode", ["cool", "fan", "dry", "heat"])
def test_modes_use_their_documented_values(mode):
    assert read(HvacState(True, mode, 24.0))["mode"] == mode


def test_fan_mode_keeps_the_setpoint():
    # setMode(kHitachiAc424Fan) sets kHitachiAc424FanTemp (27), but IRac calls
    # setTemp(degrees) after setMode, so the setpoint wins.
    for t in (16.0, 20.0, 32.0):
        assert read(HvacState(True, "fan", t))["temperature"] == int(t)


def test_setpoint_is_clamped_to_16_32():
    assert read(HvacState(True, "cool", 5.0))["temperature"] == 16
    assert read(HvacState(True, "heat", 40.0))["temperature"] == 32


@pytest.mark.parametrize("fan, raw", [("auto", 5), ("1", 1), ("2", 3), ("3", 4)])
@pytest.mark.parametrize("mode", ["cool", "fan", "dry", "heat"])
def test_every_fan_level_uses_its_documented_value_in_every_mode(mode, fan, raw):
    # IRHitachiAc264::setFan has no per-mode clamp (unlike IRHitachiAc424's).
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(HvacState(True, mode, 24.0, fan=fan)), ())
    assert HITACHI264_LAYOUT.read_raw(frame.data, "fan") == raw


def test_button_is_always_power_mode():
    # IRac::hitachi264 calls setPower last on a fresh object: the button is
    # kHitachiAc264ButtonPowerMode whatever changed; previous is ignored.
    previous = HvacState(True, "cool", 20.0, fan="1")
    for target in (
        HvacState(True, "cool", 24.0, fan="1"),
        HvacState(True, "cool", 20.0, fan="3"),
        HvacState(True, "cool", 20.0, fan="1", swing_v="swing"),
        HvacState(False, "cool", 20.0),
    ):
        assert read(target)["button"] == "power_mode"
        assert read(target, device().normalise(previous))["button"] == "power_mode"


def test_previous_is_ignored():
    dev = device()
    target = HvacState(True, "heat", 22.0, fan="2")
    fresh = dev.encode(None, target).signal
    assert dev.encode(HvacState(False, "cool", 30.0), target).signal == fresh


def test_swing_and_features_have_no_bits():
    # IRac::hitachi264: "No Swing(V) setting available", no quiet, turbo,
    # light, filter...; IRHitachiAc264::toCommon forces swingv off.
    base = device().frames(None, device().normalise(HvacState(True, "cool", 24.0)), ())
    features = {n: True for n in ("purifier", "powerful", "quiet", "economy", "light")}
    loaded = HvacState(True, "cool", 24.0, swing_v="swing", features=features)
    assert device().frames(None, device().normalise(loaded), ()) == base


def test_message_shape():
    dev = device()
    pulses = dev.encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (3300, 1700)
    assert pulses[-2:] == (400, 100000)
    assert len(pulses) == 2 + 2 * 264 + 2


def test_frame_is_a_single_main_section():
    dev = device()
    frames = dev.frames(None, dev.normalise(HvacState(True, "cool", 22.0)), ())
    assert [type(f) for f in frames] == [Frame]
    assert frames[0].section == "main"


@pytest.mark.parametrize("model", HITACHI264_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("hitachi", model), Hitachi264Device)


@pytest.mark.parametrize("model", HITACHI264_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.hitachi import Hitachi264

    legacy = LegacyDevice("hitachi", model, Hitachi264)
    assert Hitachi264Device("hitachi", model).capabilities == legacy.capabilities


def test_undeclared_deviation_is_reported():
    # A port that sends the wrong mode in an off message must fail the check.
    class Wrong(Hitachi264Device):
        def frames(self, previous, target, actions):
            data = HITACHI264_LAYOUT.build(
                button="power_mode",
                temperature=target.temperature,
                mode="heat",
                fan=target.fan,
                power=target.power,
            )
            return [Frame("main", bytes(data))]

    dev = Wrong("hitachi", "RAR-2P2 remote")
    record = next(
        r for r in load_oracle("HITACHI_AC264") if r["state"]["mode"] == "off"
    )
    with pytest.raises(AssertionError, match="mode"):
        assert_matches_oracle(dev, record, dev.LAYOUTS)


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("HITACHI_AC264")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, ())
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_hitachi264_device.py -q`
Expected: collection error, `ImportError: cannot import name ...` from `pyhvac.plugins.hitachi`.

- [ ] **Step 3: Implement**: insert immediately before `# Now the match between models and objects` in `pyhvac/plugins/hitachi.py`:

```python
# --------------------------------------------------------------- Hitachi264
# Layout from IRremoteESP8266's HitachiAC264Protocol (ir_Hitachi.h): 33 bytes,
# one frame sent LSB first (sendHitachiAC: MSBfirst is false for
# kHitachiAc264StateLength) with the kHitachiAcHdrMark/HdrSpace header,
# kHitachiAcBitMark/OneSpace/ZeroSpace bits and kHitachiAcMinGap
# (kDefaultMessageGap). Bytes 3-32 are inverted pairs
# (IRHitachiAc424::setInvertedStates: invertBytePairs(raw + 3, ...)). The
# field offsets equal Hitachi424Protocol's, which IRHitachiAc264 really
# writes (it derives from IRHitachiAc424 and shares its state).

HITACHI264 = Protocol(
    "hitachi264",
    {
        "main": Section(
            PulseDistance(400, 500, 1250),
            header=(3300, 1700),
            footer=(400,),
            gap=100000,
        ),
    },
    carrier=38000,  # kHitachiAcFreq
)

HITACHI264_BUTTON = {  # kHitachiAc264Button*
    "power_mode": 0x13,
    "fan": 0x42,
    "temp_down": 0x43,
    "temp_up": 0x44,
    "swing_v": 0x81,
}

# Skeleton: IRHitachiAc264::stateReset (IRHitachiAc424::stateReset, then
# raw[9] = 0x92 and raw[27] = 0xC1) with the fields cleared; the inverted
# bytes are recomputed by the checksum.
HITACHI264_LAYOUT = Layout(
    bytes.fromhex("0110004000ff00cc0092000000000000ff00ff00ff00ff00ff0000c10000ff00ff"),
    {
        "button": Field.at(11, 0, 8, values=HITACHI264_BUTTON),
        "temperature": Field.at(13, 2, 6, encode=int),  # whole °C
        "mode": Field.at(  # kHitachiAc264{Fan,Cool,Dry,Heat}
            25, 0, 4, values={"fan": 1, "cool": 3, "dry": 5, "heat": 6}
        ),
        "fan": Field.at(  # kHitachiAc264Fan{Low,Medium,High,Auto}
            25, 4, 4, values={"1": 1, "2": 3, "3": 4, "auto": 5}
        ),
        "power": Field.at(27, 4, 1),
    },
    checksum=InvertedPairs(3, 33),
)


class Hitachi264Device(Device):
    """Hitachi264 (RAR-2P2): a full-state protocol, ``previous`` is ignored.

    The button byte names the key "pressed". IRac::hitachi264 builds every
    message on a fresh IRHitachiAc264 and calls setPower last, so the C path
    always sends kHitachiAc264ButtonPowerMode; the port does the same, with
    or without ``previous`` (the frame carries the full state either way).

    Swing and the features (purifier, powerful, quiet, economy, light) are
    kept for the legacy entity but have no bits: IRac::hitachi264 has "No
    Swing(V) setting available" and IRHitachiAc264::toCommon forces swingv
    off, so the kHitachiAc264ButtonSwingV press is never sent.
    """

    PROTOCOL = HITACHI264
    LAYOUTS = (HITACHI264_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "fan", "dry", "heat"),
        temperature=TemperatureRange(16.0, 32.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
        ),
        swing_v=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
        features={
            name: Choice((False, True), {False: "off", True: "on"})
            for name in ("purifier", "powerful", "quiet", "economy", "light")
        },
    )

    def frames(self, previous, target, actions):
        # As the C path: IRHitachiAc424::convertMode has no auto (nor off),
        # so auto and every off message carry cool. setTemp runs after
        # setMode, so fan mode keeps the setpoint (not kHitachiAc424FanTemp).
        mode = target.mode if target.power and target.mode != "auto" else "cool"
        data = HITACHI264_LAYOUT.build(
            button="power_mode",
            temperature=target.temperature,
            mode=mode,
            fan=target.fan,
            power=target.power,
        )
        return [Frame("main", bytes(data))]


HITACHI264_MODELS = ("RAR-2P2 remote", "RAK-25NH5", "generic 264")


DEVICES.update({m: Hitachi264Device for m in HITACHI264_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_hitachi264_device.py -q`
Expected: 190 passed, 3 skipped (the skips need the C extension).

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/hitachi.py tests/test_hitachi264_device.py
git add pyhvac/plugins/hitachi.py tests/test_hitachi264_device.py
git commit -m "HITACHI_AC264: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 7: HITACHI_AC296

One 37-byte frame with inverted pairs; two unwritten padding fields (byte 25 bit 7, byte 13 bits 0-1) that the C encoder fills from stale memory are sent as 0, as in the RAR-3U3 captures.

**Files:**
- Modify: `pyhvac/plugins/hitachi.py` (block before `# Now the match between models and objects`)
- Test: `tests/test_hitachi296_device.py`

**Interfaces:**
- Consumes: `Device`, `pyhvac.fields`, bitless sections, `tests/port_oracle.py`, and the oracle fixture `HITACHI_AC296`.
- Produces: `Hitachi296Device`, `HITACHI296_MODELS`, and the `DEVICES` entries for those models.

- [ ] **Step 1: Write the failing tests**: create `tests/test_hitachi296_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.hitachi import (
    HITACHI296_LAYOUT,
    HITACHI296_MODELS,
    Hitachi296Device,
)
from pyhvac.state import HvacState

# The C path reads uninitialised memory for the unnamed padding bits of
# HitachiAC296Protocol that IRHitachiAc296::stateReset never writes, because
# IRac::sendAc builds the object on the stack:
# - byte 25 bit 7 ("unset", after Fan) changes from process to process (its
#   parity bit, byte 26 bit 7, follows); the committed fixture holds 1;
# - byte 13 bits 0-1 ("unset_low", before Temp) came out 0b11 in every
#   process tried, by accident; the fixture holds 0b11.
# The port sends 0 for all three, as in the library's RAR-3U3 captures
# (ir_Hitachi_test.cpp: byte 13 = 0x04 / 0x60, byte 25 = 0x57 / 0x13).
UNSET = Defect("unset", 0, 1, "C sends stale memory in byte 25 bit 7")
UNSET_LOW = Defect("unset_low", 0, 3, "C sends stale memory in byte 13 bits 0-1")
DEFECTS = (UNSET, UNSET_LOW)

# The two RAR-3U3 messages of ir_Hitachi_test.cpp (TestDecodeHitachiAc296).
REAL_EXAMPLE = bytes.fromhex(  # power on, auto, fan auto
    "01100040bfff00cc33926d44bb04fb00ff00ff00ff00ff00ff57a8f10e00ff00ff00ff03fc"
)
SYNTHETIC_EXAMPLE = bytes.fromhex(  # power on, cool, 24 C, fan quiet
    "01100040bfff00cc33986742bd609f00ff00ff00ff00ff00ff13ecf10e00ff00ff00ff03fc"
)


def device(model="RAR-3U3 remote"):
    return Hitachi296Device("hitachi", model)


def read(state):
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(state), ())
    return HITACHI296_LAYOUT.read(frame.data)


@pytest.mark.parametrize("record", oracle_params("HITACHI_AC296"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("HITACHI_AC296"):
        state = state_from_record(dev, record["state"])
        (frame,) = dev.frames(None, state, ())
        values = HITACHI296_LAYOUT.read(frame.data)
        assert HITACHI296_LAYOUT.build(**values) == bytearray(frame.data)
        assert HITACHI296_LAYOUT.checksum.check(frame.data)


@pytest.mark.parametrize(
    "capture, state, differing",
    [
        # stateReset sends byte 11 = 0x43; this capture has 0x44.
        (REAL_EXAMPLE, HvacState(True, "auto", 24.0), {11, 12}),
        # stateReset sends bytes 9/11 = 0x92/0x43; this capture has 0x98/0x42.
        (SYNTHETIC_EXAMPLE, HvacState(True, "cool", 24.0, fan="1"), {9, 10, 11, 12}),
    ],
)
def test_the_rar_3u3_captures_are_reproduced_but_for_the_reset_bytes(
    capture, state, differing
):
    # Both captures are expressible as HvacStates, but neither can match
    # exactly: bytes 9 and 11 are fixed by stateReset (no field in
    # HitachiAC296Protocol, no IRac setter) and differ from the remote's.
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(state), ())
    diff = {i for i, (a, b) in enumerate(zip(frame.data, capture)) if a != b}
    assert diff == differing
    assert HITACHI296_LAYOUT.read(frame.data) == HITACHI296_LAYOUT.read(capture)


def test_unset_bit_is_always_zero():
    for mode in ("auto", "cool", "dry", "heat"):
        for power in (True, False):
            values = read(HvacState(power, mode, 20.0))
            assert (values["unset"], values["unset_low"]) == (0, 0)


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat"])
def test_off_carries_mode_auto_and_the_auto_temperature(mode):
    # IRac passes mode "off"; convertMode maps it to auto, where setTemp
    # stores kHitachiAc296TempAuto.
    for t in (16.0, 25.0):
        values = read(HvacState(False, mode, t))
        assert (values["power"], values["mode"], values["temperature"]) == (
            0,
            "auto",
            1,
        )


def test_auto_ignores_the_setpoint():
    assert read(HvacState(True, "auto", 22.0))["temperature"] == 1


@pytest.mark.parametrize("mode", ["cool", "dry", "heat"])
def test_setpoint_is_whole_degrees_clamped_to_16_25(mode):
    assert read(HvacState(True, mode, 10.0))["temperature"] == 16
    assert read(HvacState(True, mode, 21.0))["temperature"] == 21
    assert read(HvacState(True, mode, 30.0))["temperature"] == 25


@pytest.mark.parametrize(
    "fan, raw", [("auto", 5), ("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 4)]
)
def test_every_fan_level_uses_convert_fan(fan, raw):
    # convertFan maps kMax (highest) to kHitachiAc296FanHigh, like kHigh.
    assert read(HvacState(True, "cool", 22.0, fan=fan))["fan"] == raw


def test_mode_codes():
    for mode, raw in (("auto", 7), ("cool", 3), ("dry", 5), ("heat", 6)):
        assert (
            HITACHI296_LAYOUT.read_raw(HITACHI296_LAYOUT.build(mode=mode), "mode")
            == raw
        )


def test_previous_is_ignored():
    dev = device()
    on = HvacState(True, "cool", 22.0)
    off = HvacState(False, "cool", 22.0)
    assert dev.encode(off, on).signal == dev.encode(None, on).signal
    assert dev.encode(on, on).signal == dev.encode(None, on).signal


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (3300, 1700)
    assert pulses[-2:] == (400, 100000)
    assert len(pulses) == 2 + 2 * 296 + 2


@pytest.mark.parametrize("model", HITACHI296_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("hitachi", model), Hitachi296Device)


@pytest.mark.parametrize("model", HITACHI296_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.hitachi import Hitachi296

    legacy = LegacyDevice("hitachi", model, Hitachi296)
    assert device(model).capabilities == legacy.capabilities


@pytest.mark.parametrize(
    "declared, field", [((UNSET_LOW,), "'unset'"), ((UNSET,), "'unset_low'")]
)
def test_undeclared_deviation_is_reported(declared, field):
    dev = device()
    record = load_oracle("HITACHI_AC296")[0]
    with pytest.raises(AssertionError, match=field):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=declared)


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("HITACHI_AC296")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_hitachi296_device.py -q`
Expected: collection error, `ImportError: cannot import name ...` from `pyhvac.plugins.hitachi`.

- [ ] **Step 3: Implement**: insert immediately before `# Now the match between models and objects` in `pyhvac/plugins/hitachi.py`:

```python
# ----------------------------------------------------------- Hitachi296
# Layout from IRremoteESP8266's HitachiAC296Protocol (ir_Hitachi.h): 37 bytes
# sent LSB first in one frame (sendHitachiAC with MSBfirst false for
# kHitachiAc296StateLength). After the 3-byte header, every second byte is
# the complement of the one before it (IRHitachiAc296::setInvertedStates).

HITACHI296 = Protocol(
    "hitachi296",
    {
        "main": Section(
            PulseDistance(400, 500, 1250),  # kHitachiAcBitMark/ZeroSpace/OneSpace
            header=(3300, 1700),  # kHitachiAcHdrMark/HdrSpace
            footer=(400,),
            gap=100000,  # kHitachiAcMinGap (kDefaultMessageGap)
        ),
    },
    carrier=38000,  # sendHitachiAC: 38 kHz
)

HITACHI296_MODE = {  # kHitachiAc296*, as IRHitachiAc296::convertMode
    "cool": 0b0011,  # kHitachiAc296Cool
    "dry": 0b0101,  # kHitachiAc296Dehumidify
    "heat": 0b0110,  # kHitachiAc296Heat
    "auto": 0b0111,  # kHitachiAc296Auto
}
HITACHI296_FAN = {  # canonical fan -> kHitachiAc296Fan*, as convertFan
    "1": 0b001,  # lowest: kHitachiAc296FanSilent
    "2": 0b010,  # kHitachiAc296FanLow
    "3": 0b011,  # kHitachiAc296FanMedium
    "4": 0b100,  # kHitachiAc296FanHigh
    "5": 0b100,  # highest: kHitachiAc296FanHigh (no higher code exists)
    "auto": 0b101,  # kHitachiAc296FanAuto
}
HITACHI296_TEMP_AUTO = 1  # kHitachiAc296TempAuto
HITACHI296_MIN_TEMP = 16  # kHitachiAc296MinTemp

# Skeleton: IRHitachiAc296::stateReset with the parity bytes left for the
# checksum. Byte 13 bits 0-1 ("unset_low") and byte 25 bit 7 ("unset") are
# never written by stateReset; see Hitachi296Device.
HITACHI296_LAYOUT = Layout(
    bytes.fromhex(
        "0110004000ff00cc00920043000000000000000000000000000000f1000000000000000300"
    ),
    {
        "unset_low": Field.at(13, 0, 2),  # padding the C path never initialises
        "temperature": Field.at(13, 2, 5),  # whole °C, or kHitachiAc296TempAuto
        "mode": Field.at(25, 0, 4, values=HITACHI296_MODE),
        "fan": Field.at(25, 4, 3),
        "unset": Field.at(25, 7, 1),  # padding bit the C path never initialises
        "power": Field.at(27, 4, 1),
    },
    checksum=InvertedPairs(3, 37),
)


class Hitachi296Device(Device):
    """Hitachi296 (RAR-3U3): a full-state protocol, ``previous`` is ignored.

    Byte 13 bits 0-1 (padding before Temp) and byte 25 bit 7 (padding after
    Fan) are unnamed in HitachiAC296Protocol and never written by
    IRHitachiAc296::stateReset. IRac builds the object on the stack, so the
    C path sends whatever memory held: byte 25 bit 7 differs from process
    to process, and byte 13 bits 0-1 came out 0b11 in every process tried,
    by accident. The port sends 0 for all three bits, as the RAR-3U3 remote
    does in the library's captured messages (ir_Hitachi_test.cpp).
    """

    PROTOCOL = HITACHI296
    LAYOUTS = (HITACHI296_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "heat"),
        temperature=TemperatureRange(16.0, 25.0),
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
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to auto), and in auto setTemp stores
        # kHitachiAc296TempAuto instead of the setpoint.
        mode = target.mode if target.power else "auto"
        if mode == "auto":
            temperature = HITACHI296_TEMP_AUTO
        else:
            temperature = max(int(target.temperature), HITACHI296_MIN_TEMP)
        data = HITACHI296_LAYOUT.build(
            temperature=temperature,
            mode=mode,
            fan=HITACHI296_FAN[target.fan],
            unset_low=0,
            unset=0,
            power=target.power,
        )
        return [Frame("main", bytes(data))]


HITACHI296_MODELS = ("RAR-3U3 remote", "RAS-70YHA3", "generic 296")


DEVICES.update({m: Hitachi296Device for m in HITACHI296_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_hitachi296_device.py -q`
Expected: 117 passed, 3 skipped (the skips need the C extension).

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/hitachi.py tests/test_hitachi296_device.py
git add pyhvac/plugins/hitachi.py tests/test_hitachi296_device.py
git commit -m "HITACHI_AC296: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 8: Whole-family verification

**Files:**
- Modify: `tests/test_hitachi_family.py`

- [ ] **Step 1: Add the family test**: append to `tests/test_hitachi_family.py`:

```python
def test_only_hitachi_ac3_stays_on_the_c_library():
    import pytest

    # Building the remaining legacy devices needs the C extension.
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac import registry
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.hitachi import PluginObject
    from pyhvac.plugins.hvaclib import IRGHVAC

    c_backed = [m for m, cls in PluginObject.MODELS.items() if issubclass(cls, IRGHVAC)]
    left = [
        m for m in c_backed if isinstance(registry.get_device("hitachi", m), LegacyDevice)
    ]
    # HITACHI_AC3 has no documented layout and the C path sends nothing;
    # these models are dropped in phase 4.
    assert sorted(left) == ["PC-LH3B", "generic 3"]
```

- [ ] **Step 2: Run it**

Run: `python -m pytest tests/test_hitachi_family.py -q`
Expected: 1 passed, 1 skipped (the family check needs the C extension; it runs in Step 3).

- [ ] **Step 3: Run the C-extension suite**

```bash
S=/tmp/claude-1000/-home-fw-development-AutoBuddy-pyhvac/e24a44b3-0698-43b6-890a-47d4ddf34b70/scratchpad
test -d $S/oracle-venv || (python -m venv $S/oracle-venv && $S/oracle-venv/bin/pip install -q "pyhvac==0.1.7")
SP=$S/oracle-venv/lib/python3.14/site-packages/pyhvac
rm -rf $S/cwork && mkdir -p $S/cwork && cp -r pyhvac tests tools $S/cwork/
find $S/cwork -name __pycache__ -prune -exec rm -rf {} +
cp $SP/_irhvac.so $SP/irhvac.py $S/cwork/pyhvac/
cd $S/cwork && PYTHONPATH=. python -m pytest -q -p no:cacheprovider tests | tail -3
```

Expected:
- 0 failed;
- the capability-equality tests pass;
- the legacy HITACHI_AC296 cases report as xfail or xpass.

- [ ] **Step 4: Commit**

```bash
black tests/test_hitachi_family.py
git add tests/test_hitachi_family.py
git commit -m "Test that only HITACHI_AC3 is left on the C library

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
