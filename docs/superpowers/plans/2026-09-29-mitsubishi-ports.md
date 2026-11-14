# Mitsubishi Family Ports Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the C path for every Mitsubishi model with a pure-Python `Device`:
- MITSUBISHI_AC, MITSUBISHI136 and MITSUBISHI112 (`mitsubishi_electric`);
- MITSUBISHI_HEAVY_152 and MITSUBISHI_HEAVY_88 (`mitsubishi_heavy_industries`).

**Architecture:** Same as the Daikin and Hitachi plans. One device class per protocol is appended to its plugin module and registered through a new `DEVICES` dict. Each port was written from its `union *Protocol` in `ir_Mitsubishi.h`/`ir_MitsubishiHeavy.h`, then verified against every oracle record (only declared defects allowed) and against the real C path on every state the capabilities allow. The real captures in `ir_Mitsubishi*_test.cpp` are reproduced where the entity can express them.

**Tech Stack:** Python ≥ 3.9 standard library, pytest, black. The port kit on branch `ports`.

**Spec:** `docs/superpowers/specs/2026-09-27-port-kit-design.md`. House rules: the "Rulings made while planning" sections of `docs/superpowers/plans/2026-09-28-daikin-ports.md` and `2026-09-28-hitachi-ports.md`.

## Global Constraints

- Work on branch `ports`.
- Durations are integer µs, the carrier is in Hz, and temperatures are °C.
- Python ≥ 3.9, and no new runtime dependencies.
- Layouts come from the headers (facts).
- Capabilities equal the legacy entity (C-only test in each file).
- A difference from the C output is allowed only as a declared `Defect`.
- The old API and all existing tests stay green. Run `black` on every modified file.
- Tests: `python -m pytest -q`. The C-extension run is described in Task 7.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **Fan lowest/highest** now send the documented quiet/silent/econo/turbo codes; the C path resets them. On MITSUBISHI136 the lowest code equals FanQuiet, which is the unit's own semantics.
2. **Swing positions follow the documented top-to-bottom order** ("1" = highest). Users of 90°/60° see the vanes move to their documented positions.
3. **Off messages carry mode auto,** as C. A real HEAVY_152 power-off capture keeps the previous mode; the port follows C, per the Daikin2 precedent.
4. **HEAVY_152 "wide" horizontal swing sends SwingHOff,** as C. The header documents no wide value.
5. **`mitsubishi_heavy_industries` keys "gemeric"/"gemeric 152" are misspelled.** They are kept (existing configs may use them). The brand has no "generic" model, so `get_device(brand)` without a model raises `KeyError`.

## Rulings made while planning

- **Fan lowest/highest (MITSUBISHI136, MITSUBISHI112, HEAVY_152, HEAVY_88):** `convertFan` maps them to the documented FanMin/Quiet/Econo/Turbo codes, but IRac's `setQuiet(false)`/`setEcono(false)`/`setTurbo(false)` reset them. The ports send the documented codes. For MITSUBISHI_AC, lowest → Silent is a designed mapping that C does send.
- **Swing "1"/"2" (90°/60°), all five:** the glue maps 90° to kHigh and 60° to kUpperMiddle, which `convertSwingV` lacks. The ports send Highest/High.
- **HEAVY_152 `night`:** the port sends the documented sleep bit. The oracle fixtures predate `main`'s sleep glue fix.
- **MITSUBISHI112 swing "off" → auto, and HEAVY_152 "wide" → SwingHOff:** as C, because the header documents no alternative.
- **No stale padding in this family:** every `stateReset` writes all bytes.

## Kit follow-ups found here (not in this plan)

- **Non-contiguous fields:** HEAVY_88's split swing bits use a local `Field` subclass. `fields.py` should support fields made of several bit ranges.
- **`portkit checksum`** does not try `InvertedPairs` with an odd start or a complement block (MITSUBISHI136).
- **`portkit timings`** merged the MITSUBISHI_AC footer mark (440) into the 450 bit mark.

---

### Task 1: Imports and DEVICES in both Mitsubishi modules

**Files:**
- Modify: `pyhvac/plugins/mitsubishi_electric.py`, `pyhvac/plugins/mitsubishi_heavy_industries.py`
- Test: `tests/test_mitsubishi_family.py`

- [ ] **Step 1: Write the failing test**: create `tests/test_mitsubishi_family.py`:

```python
"""Every Mitsubishi model is served by a pure-Python device."""

import importlib

import pytest

MODULES = ("mitsubishi_electric", "mitsubishi_heavy_industries")


@pytest.mark.parametrize("name", MODULES)
def test_module_has_a_devices_table(name):
    module = importlib.import_module(f"pyhvac.plugins.{name}")
    assert isinstance(module.DEVICES, dict)
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `python -m pytest tests/test_mitsubishi_family.py -q`
Expected: 2 failed: `AttributeError: module ... has no attribute 'DEVICES'`.

- [ ] **Step 3: Implement**

In `pyhvac/plugins/mitsubishi_electric.py`, replace `from .hvaclib import PulseBased, GenPluginObject` with:

```python
from dataclasses import dataclass

from .hvaclib import PulseBased, GenPluginObject
from ..device import Device
from ..fields import Checksum, Field, Layout, Sum8
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import Capabilities, Choice, TemperatureRange
```

In `pyhvac/plugins/mitsubishi_heavy_industries.py`, replace `from .hvaclib import PulseBased, GenPluginObject` with:

```python
from dataclasses import dataclass

from .hvaclib import PulseBased, GenPluginObject
from ..device import Device
from ..fields import Field, InvertedPairs, Layout
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import Capabilities, Choice, TemperatureRange
```

In both files, insert `DEVICES = {}` (followed by two blank lines) immediately before the `# Now the match between models and objects` comment.

- [ ] **Step 4: Run the tests**

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/mitsubishi_electric.py pyhvac/plugins/mitsubishi_heavy_industries.py tests/test_mitsubishi_family.py
git add pyhvac/plugins/mitsubishi_electric.py pyhvac/plugins/mitsubishi_heavy_industries.py tests/test_mitsubishi_family.py
git commit -m "Mitsubishi: DEVICES tables and imports for the ports

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 2: MITSUBISHI_AC

One 18-byte frame sent twice (repeat mark 440, gap 15500); layout from `union Mitsubishi144Protocol`, plus `mode_aux` for the byte-8 nibble setMode writes.

**Files:**
- Modify: `pyhvac/plugins/mitsubishi_electric.py` (block before `# Now the match between models and objects`)
- Test: `tests/test_mitsubishi_ac_device.py`

**Interfaces:**
- Consumes: `Device`, `pyhvac.fields`, `tests/port_oracle.py`, and the oracle fixture `MITSUBISHI_AC`.
- Produces: `MitsubishiAcDevice`, `MITSUBISHI_AC_MODELS`, and the `DEVICES` entries for those models.

- [ ] **Step 1: Write the failing tests**: create `tests/test_mitsubishi_ac_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.ir.codec import decode
from pyhvac.plugins.mitsubishi_electric import (
    MITSUBISHI_AC,
    MITSUBISHI_AC_LAYOUT,
    MITSUBISHI_AC_MODELS,
    MitsubishiAcDevice,
)
from pyhvac.state import HvacState

# The C path deviates from the documented kMitsubishiAcVane* positions here:
# the old labels go through IRGHVAC.trans_swing ("90°" -> kHigh, "60°" ->
# kUpperMiddle) into IRMitsubishiAC::convertSwingV, which maps kHigh to
# kMitsubishiAcVaneHigh (so kMitsubishiAcVaneHighest is never sent) and has
# no kUpperMiddle case (it falls back to kMitsubishiAcVaneAuto). IRac writes
# the same value into Vane and VaneLeft.
DEFECTS = tuple(
    Defect(field, ours, theirs, reason)
    for field in ("swing_v", "swing_v_left")
    for ours, theirs, reason in (
        ("1", "2", "C sends VaneHigh (0b010) for the highest position"),
        ("2", "off", "C has no upper-middle case: sends VaneAuto (0b000)"),
    )
)

# The library's reset state (kReset, ir_Mitsubishi_test.cpp): power on, heat,
# 22 C, fan 5 (FanAuto clear), Vane auto with VaneBit, WideVane middle,
# Clock 0x67, checksum 0x1F.
RESET_CAPTURE = bytes.fromhex("23cb2601002008063045670000000000001f")


def device(model="MSZ-GV2519"):
    return MitsubishiAcDevice("mitsubishi_electric", model)


def with_hswing(record):
    # A record without "hswing" leaves IRac's swingh at kOff, which
    # IRMitsubishiAC::convertSwingH maps to its default, WideVane Middle:
    # canonical "3" (checked against the C path in cpath_check.py). The port
    # has no "off" swing_h (the legacy entity has none), so the record is
    # read as "middle".
    if "hswing" in record["state"]:
        return record
    return {**record, "state": {**record["state"], "hswing": "middle"}}


def read(state):
    dev = device()
    first, second = dev.frames(None, dev.normalise(state), ())
    assert first == second
    return MITSUBISHI_AC_LAYOUT.read(first.data)


@pytest.mark.parametrize("record", oracle_params("MITSUBISHI_AC"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, with_hswing(record), dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("MITSUBISHI_AC"):
        state = state_from_record(dev, with_hswing(record)["state"])
        for frame in dev.frames(None, state, ()):
            values = MITSUBISHI_AC_LAYOUT.read(frame.data)
            assert MITSUBISHI_AC_LAYOUT.build(**values) == bytearray(frame.data)
            assert MITSUBISHI_AC_LAYOUT.checksum.check(frame.data)


def test_every_oracle_message_is_one_frame_sent_twice():
    for record in load_oracle("MITSUBISHI_AC"):
        first, second = decode(MITSUBISHI_AC, record["pulses"], ["main", "main"])
        assert first == second


def test_reset_state_capture_reads_back():
    # The known-good state of stateReset, as captured in the library's tests.
    values = MITSUBISHI_AC_LAYOUT.read(RESET_CAPTURE)
    assert MITSUBISHI_AC_LAYOUT.checksum.check(RESET_CAPTURE)
    assert (values["power"], values["mode"], values["temperature"]) == (1, "heat", 22)
    assert (values["swing_h"], values["swing_v"], values["vane_bit"]) == ("3", "off", 1)
    assert (values["fan"], values["fan_auto"], values["clock"]) == (5, 0, 0x67)


def test_the_port_reproduces_the_reset_capture_but_for_its_fan():
    # kReset has Fan 5 without FanAuto; setFan never stores 5 unless asked for
    # silent, so the nearest state is lowest (Fan 5, FanAuto clear).
    state = HvacState(True, "heat", 22.0, fan="1", swing_h="3")
    dev = device()
    first, _ = dev.frames(None, dev.normalise(state), ())
    assert first.data == RESET_CAPTURE


@pytest.mark.parametrize("mode", ["auto", "cool", "fan", "dry", "heat"])
@pytest.mark.parametrize("t", [16.0, 31.0])
def test_off_carries_mode_auto_and_the_rest_of_the_state(mode, t):
    # IRac passes mode "off"; convertMode maps it to kMitsubishiAcAuto, and
    # setMode writes byte 8's low nibble for auto (0).
    values = read(HvacState(False, mode, t, fan="3", swing_v="4", swing_h="6"))
    assert (values["power"], values["mode"], values["mode_aux"]) == (0, "auto", 0)
    assert (values["temperature"], values["fan"]) == (int(t), 2)
    assert (values["swing_v"], values["swing_v_left"], values["swing_h"]) == (
        "4",
        "4",
        "6",
    )


@pytest.mark.parametrize(
    "mode, code, aux",
    [("auto", 4, 0), ("cool", 3, 6), ("dry", 2, 2), ("heat", 1, 0), ("fan", 7, 7)],
)
def test_mode_codes_and_the_byte_8_nibble_set_mode_writes(mode, code, aux):
    values = read(HvacState(True, mode, 22.0))
    assert MITSUBISHI_AC_LAYOUT.fields["mode"].values[values["mode"]] == code
    assert (values["mode"], values["mode_aux"]) == (mode, aux)


@pytest.mark.parametrize(
    "t, whole, half",
    [(16.0, 16, 0), (16.5, 16, 1), (22.5, 22, 1), (30.5, 30, 1), (31.0, 31, 0)],
)
def test_setpoint_has_half_degrees(t, whole, half):
    values = read(HvacState(True, "cool", t))
    assert (values["temperature"], values["half_degree"]) == (whole, half)


def test_setpoint_is_clamped_to_16_31():
    assert read(HvacState(True, "cool", 10.0))["temperature"] == 16
    assert read(HvacState(True, "heat", 35.0))["temperature"] == 31
    assert read(HvacState(True, "heat", 35.0))["half_degree"] == 0


@pytest.mark.parametrize(
    "fan, raw, auto",
    [("auto", 0, 1), ("1", 5, 0), ("2", 1, 0), ("3", 2, 0), ("4", 3, 0), ("5", 4, 0)],
)
def test_every_fan_level_uses_set_fan(fan, raw, auto):
    # convertFan: lowest -> kMitsubishiAcFanSilent (6), which setFan stores as
    # 5; low..highest -> kMitsubishiAcFanRealMax - 3 .. RealMax.
    values = read(HvacState(True, "cool", 22.0, fan=fan))
    assert (values["fan"], values["fan_auto"]) == (raw, auto)


@pytest.mark.parametrize(
    "swing_v, raw",
    [("off", 0), ("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 5), ("auto", 7)],
)
def test_every_swing_v_position_drives_both_vanes(swing_v, raw):
    dev = device()
    first, _ = dev.frames(
        None, dev.normalise(HvacState(True, "cool", 22.0, swing_v=swing_v)), ()
    )
    raws = {
        k: MITSUBISHI_AC_LAYOUT.read_raw(first.data, k)
        for k in ("swing_v", "swing_v_left", "vane_bit")
    }
    assert raws == {"swing_v": raw, "swing_v_left": raw, "vane_bit": 1}


@pytest.mark.parametrize(
    "swing_h, raw",
    [("auto", 8), ("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 5), ("6", 6)],
)
def test_every_swing_h_position(swing_h, raw):
    dev = device()
    first, _ = dev.frames(
        None, dev.normalise(HvacState(True, "cool", 22.0, swing_h=swing_h)), ()
    )
    assert MITSUBISHI_AC_LAYOUT.read_raw(first.data, "swing_h") == raw


def test_unset_features_stay_clear():
    values = read(HvacState(True, "heat", 16.0))
    for name in (
        "isee",
        "stop_clock",
        "start_clock",
        "timer",
        "weekly_timer",
        "ecocool",
        "direct_indirect",
        "absense_detect",
        "isave_10c",
        "natural_flow",
    ):
        assert values[name] == 0, name
    assert values["clock"] == 0x67  # kReset's clock: IRac never sets one


def test_previous_is_ignored():
    dev = device()
    on = HvacState(True, "cool", 22.0)
    off = HvacState(False, "cool", 22.0)
    assert dev.encode(off, on).signal == dev.encode(None, on).signal
    assert dev.encode(on, on).signal == dev.encode(None, on).signal


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    one = 2 + 2 * 144 + 2
    assert len(pulses) == 2 * one
    for start in (0, one):
        assert pulses[start : start + 2] == (3400, 1750)
        assert pulses[start + one - 2 : start + one] == (440, 15500)


@pytest.mark.parametrize("model", MITSUBISHI_AC_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(
        registry.get_device("mitsubishi_electric", model), MitsubishiAcDevice
    )


@pytest.mark.parametrize("model", MITSUBISHI_AC_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.mitsubishi_electric import Mitsubishi

    legacy = LegacyDevice("mitsubishi_electric", model, Mitsubishi)
    assert device(model).capabilities == legacy.capabilities


@pytest.mark.parametrize("label, field", [("90°", "swing_v"), ("60°", "swing_v")])
def test_undeclared_deviation_is_reported(label, field):
    dev = device()
    record = next(
        r for r in load_oracle("MITSUBISHI_AC") if r["state"].get("swing") == label
    )
    with pytest.raises(AssertionError, match=field):
        assert_matches_oracle(dev, with_hswing(record), dev.LAYOUTS, defects=())


def test_left_vane_deviation_must_be_declared_too():
    dev = device()
    record = next(
        r for r in load_oracle("MITSUBISHI_AC") if r["state"].get("swing") == "90°"
    )
    right_only = tuple(d for d in DEFECTS if d.field == "swing_v")
    with pytest.raises(AssertionError, match="swing_v_left"):
        assert_matches_oracle(dev, with_hswing(record), dev.LAYOUTS, right_only)


def test_missing_hswing_is_not_silently_accepted():
    dev = device()
    record = next(r for r in load_oracle("MITSUBISHI_AC") if "hswing" not in r["state"])
    with pytest.raises(AssertionError, match="swing_h"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("MITSUBISHI_AC")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, with_hswing(record), dev.LAYOUTS[:1], DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_mitsubishi_ac_device.py -q`
Expected: collection error, `ImportError: cannot import name ...` from `pyhvac.plugins.mitsubishi_electric`.

- [ ] **Step 3: Implement**: insert immediately before `# Now the match between models and objects` in `pyhvac/plugins/mitsubishi_electric.py`:

```python
# ------------------------------------------------------------- MitsubishiAc
# Layout from IRremoteESP8266's Mitsubishi144Protocol (ir_Mitsubishi.h): one
# 18-byte state (kMitsubishiACStateLength) sent LSB first, closed by a
# sum-of-bytes checksum (IRMitsubishiAC::calculateChecksum). sendMitsubishiAC
# sends it kMitsubishiACMinRepeat + 1 = 2 times, each copy with the header,
# a kMitsubishiAcRptMark footer and a kMitsubishiAcRptSpace gap.

MITSUBISHI_AC = Protocol(
    "mitsubishi-ac",
    {
        "main": Section(
            PulseDistance(450, 420, 1300),  # kMitsubishiAcBitMark/Zero/OneSpace
            header=(3400, 1750),  # kMitsubishiAcHdrMark/HdrSpace
            footer=(440,),  # kMitsubishiAcRptMark
            gap=15500,  # kMitsubishiAcRptSpace
        ),
    },
    carrier=38000,  # sendMitsubishiAC: 38 kHz
)

MITSUBISHI_AC_MODE = {  # kMitsubishiAc*, as IRMitsubishiAC::convertMode
    "auto": 0b100,
    "cool": 0b011,
    "dry": 0b010,
    "heat": 0b001,
    "fan": 0b111,
}
# IRMitsubishiAC::setMode also rewrites the whole of byte 8: the low nibble
# (unnamed in the struct) gets these values; the high nibble (WideVane) is
# then overwritten by IRac's setWideVane.
MITSUBISHI_AC_MODE_AUX = {"auto": 0b0000, "cool": 0b0110, "dry": 0b0010}
MITSUBISHI_AC_MODE_AUX.update({"heat": 0b0000, "fan": 0b0111})
MITSUBISHI_AC_FAN = {  # canonical fan -> (Fan, FanAuto), as setFan(convertFan)
    "auto": (0, 1),  # kMitsubishiAcFanAuto: the FanAuto bit
    "1": (5, 0),  # lowest: kMitsubishiAcFanSilent (6), stored as 5 by setFan
    "2": (1, 0),  # kMitsubishiAcFanRealMax - 3
    "3": (2, 0),  # kMitsubishiAcFanRealMax - 2
    "4": (3, 0),  # kMitsubishiAcFanRealMax - 1
    "5": (4, 0),  # kMitsubishiAcFanRealMax
}
MITSUBISHI_AC_VANE = {  # canonical swing_v -> kMitsubishiAcVane*
    "off": 0b000,  # VaneAuto: convertSwingV's choice for stdAc "off"
    "1": 0b001,  # VaneHighest
    "2": 0b010,  # VaneHigh
    "3": 0b011,  # VaneMiddle
    "4": 0b100,  # VaneLow
    "5": 0b101,  # VaneLowest
    "auto": 0b111,  # VaneSwing: convertSwingV's choice for stdAc "auto"
}
MITSUBISHI_AC_WIDE_VANE = {  # canonical swing_h -> kMitsubishiAcWideVane*
    "1": 0b0001,  # LeftMax
    "2": 0b0010,  # Left
    "3": 0b0011,  # Middle
    "4": 0b0100,  # Right
    "5": 0b0101,  # RightMax
    "6": 0b0110,  # Wide
    "auto": 0b1000,  # Auto
}
MITSUBISHI_AC_MIN_TEMP = 16  # kMitsubishiAcMinTemp

# Skeleton: IRMitsubishiAC::stateReset (kReset, zero-filled to 18 bytes) with
# the fields IRac writes cleared. Byte 10 keeps kReset's Clock (0x67): the
# pyhvac glue never sets a clock, so IRac skips setClock.
MITSUBISHI_AC_LAYOUT = Layout(
    bytes.fromhex("23cb26010000000000006700000000000000"),
    {
        "power": Field.at(5, 5, 1),
        "mode": Field.at(6, 3, 3, values=MITSUBISHI_AC_MODE),
        "isee": Field.at(6, 6, 1),
        "temperature": Field.at(  # whole °C, as an offset from 16
            7, 0, 4, values={t: t - MITSUBISHI_AC_MIN_TEMP for t in range(16, 32)}
        ),
        "half_degree": Field.at(7, 4, 1),
        "mode_aux": Field.at(8, 0, 4),  # struct padding that setMode writes
        "swing_h": Field.at(8, 4, 4, values=MITSUBISHI_AC_WIDE_VANE),
        "fan": Field.at(9, 0, 3),
        "swing_v": Field.at(9, 3, 3, values=MITSUBISHI_AC_VANE),
        "vane_bit": Field.at(9, 6, 1),
        "fan_auto": Field.at(9, 7, 1),
        "clock": Field.at(10, 0, 8),
        "stop_clock": Field.at(11, 0, 8),
        "start_clock": Field.at(12, 0, 8),
        "timer": Field.at(13, 0, 3),
        "weekly_timer": Field.at(13, 3, 1),
        "ecocool": Field.at(14, 5, 1),
        "direct_indirect": Field.at(15, 0, 2),
        "absense_detect": Field.at(15, 2, 1),
        "isave_10c": Field.at(15, 5, 1),
        "natural_flow": Field.at(16, 1, 1),
        "swing_v_left": Field.at(16, 3, 3, values=MITSUBISHI_AC_VANE),
    },
    checksum=Sum8(0, 17, 17),
)


class MitsubishiAcDevice(Device):
    """Mitsubishi 144-bit (MSZ-GV2519 and others): a full-state protocol,
    ``previous`` is ignored (Mitsubishi144Protocol has no toggle bits).

    The message is the same 18-byte frame sent twice, as sendMitsubishiAC
    does with kMitsubishiACMinRepeat. Vertical positions are the documented
    kMitsubishiAcVane* ones, "1" the highest; IRac sets the left vane
    (VaneLeft) to the same position as the right one (Vane).
    """

    PROTOCOL = MITSUBISHI_AC
    LAYOUTS = (MITSUBISHI_AC_LAYOUT, MITSUBISHI_AC_LAYOUT)
    capabilities = Capabilities(
        modes=("auto", "cool", "fan", "dry", "heat"),
        temperature=TemperatureRange(16.0, 31.0, decimals=(0, 5)),
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
        swing_h=Choice(
            ("auto", "1", "2", "3", "4", "5", "6"),
            {
                "auto": "auto",
                "1": "far left",
                "2": "left",
                "3": "middle",
                "4": "right",
                "5": "far right",
                "6": "wide",
            },
        ),
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to kMitsubishiAcAuto) and every other
        # setting as asked.
        mode = target.mode if target.power else "auto"
        # setTemp: half degrees, clamped to 16-31 (normalise already did).
        halves = int(target.temperature * 2)
        fan, fan_auto = MITSUBISHI_AC_FAN[target.fan]
        data = MITSUBISHI_AC_LAYOUT.build(
            power=target.power,
            mode=mode,
            temperature=halves // 2,
            half_degree=halves & 1,
            mode_aux=MITSUBISHI_AC_MODE_AUX[mode],
            swing_h=target.swing_h,
            fan=fan,
            fan_auto=fan_auto,
            swing_v=target.swing_v,
            vane_bit=1,  # setVane always sets it
            swing_v_left=target.swing_v,
            isave_10c=0,  # IRac calls setISave10C(false)
        )
        frame = Frame("main", bytes(data))
        return [frame, frame]


MITSUBISHI_AC_MODELS = (
    "MS-GK24VA",
    "KM14A 0179213 remote",
    "MLZ-RX5017AS",
    "SG153/M21EDF426 remote",
    "MSZ-GV2519",
    "RH151/M21ED6426 remote",
    "MSZ-SF25VE3",
    "SG15D remote",
    "MSZ-ZW4017S",
    "MSZ-FHnnVE",
    "RH151 remote",
    "generic",
)


DEVICES.update({m: MitsubishiAcDevice for m in MITSUBISHI_AC_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_mitsubishi_ac_device.py -q`
Expected: 265 passed, 12 skipped (the skips need the C extension).

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/mitsubishi_electric.py tests/test_mitsubishi_ac_device.py
git add pyhvac/plugins/mitsubishi_electric.py tests/test_mitsubishi_ac_device.py
git commit -m "MITSUBISHI_AC: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 3: MITSUBISHI136

One 17-byte frame; bytes 11-16 are the complement of bytes 5-10 (local `Mitsubishi136Checksum`); layout from `union Mitsubishi136Protocol`.

**Files:**
- Modify: `pyhvac/plugins/mitsubishi_electric.py` (block before `# Now the match between models and objects`)
- Test: `tests/test_mitsubishi136_device.py`

**Interfaces:**
- Consumes: `Device`, `pyhvac.fields`, `tests/port_oracle.py`, and the oracle fixture `MITSUBISHI136`.
- Produces: `Mitsubishi136Device`, `MITSUBISHI136_MODELS`, and the `DEVICES` entries for those models.

- [ ] **Step 1: Write the failing tests**: create `tests/test_mitsubishi136_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.ir.codec import decode
from pyhvac.plugins.mitsubishi_electric import (
    MITSUBISHI136,
    MITSUBISHI136_LAYOUT,
    MITSUBISHI136_MODELS,
    Mitsubishi136Checksum,
    Mitsubishi136Device,
)
from pyhvac.state import HvacState

# Fan lowest: convertFan(kMin) gives kMitsubishi136FanMin, but IRac then calls
# setQuiet(false), and IRMitsubishi136::setQuiet turns FanMin (which is also
# kMitsubishi136FanQuiet) into kMitsubishi136FanLow. The port sends FanMin.
FAN_MIN = Defect("fan", 0, 1, "IRac's setQuiet(false) turns FanMin into FanLow")
# Swing positions count down from kMitsubishi136SwingVHighest. The legacy
# labels 90° and 60° reach C as kHigh and kUpperMiddle, which
# IRMitsubishi136::convertSwingV maps to SwingVHigh and SwingVAuto.
SWING_HIGHEST = Defect("swing_v", 3, 2, "C maps 90° (kHigh) to SwingVHigh")
SWING_HIGH = Defect("swing_v", 2, 12, "C maps 60° (kUpperMiddle) to SwingVAuto")
DEFECTS = (FAN_MIN, SWING_HIGHEST, SWING_HIGH)

# PEAD-RP71JAA capture (ir_Mitsubishi_test.cpp, DecodeRealExample):
# power on, cool, 20 C, fan Max, swing Highest, quiet off.
REAL_EXAMPLE = bytes.fromhex("23cb262100404137040000bfbec8fbffff")


def device(model="PEAD-RP71JAA Ducted"):
    return Mitsubishi136Device("mitsubishi_electric", model)


def frame(state):
    dev = device()
    (main,) = dev.frames(None, dev.normalise(state), ())
    return main.data


def read(state):
    return MITSUBISHI136_LAYOUT.read(frame(state))


@pytest.mark.parametrize("record", oracle_params("MITSUBISHI136"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("MITSUBISHI136"):
        state = state_from_record(dev, record["state"])
        (main,) = dev.frames(None, state, ())
        values = MITSUBISHI136_LAYOUT.read(main.data)
        assert MITSUBISHI136_LAYOUT.build(**values) == bytearray(main.data)
        assert MITSUBISHI136_LAYOUT.checksum.check(main.data)


def test_every_oracle_frame_has_the_inverted_section():
    # IRMitsubishi136::checksum: bytes 11-16 are ~bytes 5-10.
    for record in load_oracle("MITSUBISHI136"):
        (main,) = decode(MITSUBISHI136, record["pulses"], expected=["main"])
        assert all(main.data[11 + i] == ~main.data[5 + i] & 0xFF for i in range(6))
        assert Mitsubishi136Checksum(5, 11, 11).check(main.data)


def test_no_field_overlaps_the_inverted_section():
    checked = {
        b for byte in (11, 12, 13, 14, 15, 16) for b in range(8 * byte, 8 * byte + 8)
    }
    assert MITSUBISHI136_LAYOUT.checksum.positions() == set(range(11, 17))
    for name, field in MITSUBISHI136_LAYOUT.fields.items():
        assert not checked & set(field.bits), name


def test_checksum_rejects_a_broken_frame():
    data = bytearray(frame(HvacState(True, "cool", 20.0)))
    data[14] ^= 0x01
    assert not MITSUBISHI136_LAYOUT.checksum.check(data)


def test_the_real_capture_is_reproduced():
    # With swing "1" as the documented Highest (the C path would send High).
    state = HvacState(True, "cool", 20.0, fan="5", swing_v="1")
    assert frame(state) == REAL_EXAMPLE
    assert frame(HvacState(True, "cool", 20.0, fan="4", swing_v="1")) == (REAL_EXAMPLE)


def test_skeleton_keeps_the_reset_bytes():
    # stateReset: 23 CB 26 21 00 then zeros from byte 9; byte 7 bit 0 set.
    data = MITSUBISHI136_LAYOUT.build(checksum=False)
    assert data[:5] == bytes.fromhex("23cb262100")
    assert data[7] & 1 and data[8] == 0x04
    assert data[9:11] == b"\x00\x00"


@pytest.mark.parametrize("mode", ["auto", "cool", "fan", "dry", "heat"])
@pytest.mark.parametrize("temp", [16.0, 20.0, 25.0])
def test_off_carries_mode_auto_in_every_mode(mode, temp):
    # IRac passes mode "off"; IRMitsubishi136::convertMode maps it to auto.
    values = read(HvacState(False, mode, temp))
    assert (values["power"], values["mode"]) == (0, "auto")
    assert values["temperature"] == max(int(temp), 17) - 16


@pytest.mark.parametrize(
    "mode, raw", [("fan", 0), ("cool", 1), ("heat", 2), ("auto", 3), ("dry", 5)]
)
def test_mode_codes(mode, raw):
    values = read(HvacState(True, mode, 20.0))
    assert values["power"] == 1
    assert (
        MITSUBISHI136_LAYOUT.read_raw(frame(HvacState(True, mode, 20.0)), "mode") == raw
    )


@pytest.mark.parametrize(
    "temp, raw", [(10.0, 1), (16.0, 1), (17.0, 1), (20.0, 4), (25.0, 9), (30.0, 9)]
)
def test_setpoint_is_whole_degrees_clamped_to_17(temp, raw):
    # setTemp clamps to kMitsubishi136MinTemp (17) and stores degrees - 16;
    # the entity's range stops at 25.
    assert read(HvacState(True, "cool", temp))["temperature"] == raw


def test_setpoint_is_kept_in_every_mode():
    for mode in ("auto", "cool", "fan", "dry", "heat"):
        assert read(HvacState(True, mode, 22.0))["temperature"] == 6


@pytest.mark.parametrize(
    "fan, raw", [("auto", 2), ("1", 0), ("2", 1), ("3", 2), ("4", 3), ("5", 3)]
)
def test_every_fan_level(fan, raw):
    # convertFan: kHigh and kMax -> FanMax, auto -> FanMed (no auto code).
    assert read(HvacState(True, "cool", 22.0, fan=fan))["fan"] == raw


@pytest.mark.parametrize("fan", ["auto", "1", "2", "3", "4", "5"])
def test_quiet_forces_the_quiet_fan(fan):
    state = HvacState(True, "cool", 22.0, fan=fan, features={"quiet": True})
    assert read(state)["fan"] == 0  # kMitsubishi136FanQuiet
    off = HvacState(False, "heat", 22.0, fan=fan, features={"quiet": True})
    assert read(off)["fan"] == 0


@pytest.mark.parametrize(
    "swing, raw",
    [("off", 12), ("auto", 12), ("1", 3), ("2", 2), ("3", 1), ("4", 0)],
)
def test_every_swing_value(swing, raw):
    # No off code: convertSwingV(kOff) is SwingVAuto. Positions count down
    # from SwingVHighest.
    assert read(HvacState(True, "cool", 22.0, swing_v=swing))["swing_v"] == raw


def test_previous_is_ignored():
    dev = device()
    on = HvacState(True, "cool", 22.0, swing_v="1")
    off = HvacState(False, "cool", 22.0)
    assert dev.encode(off, on).signal == dev.encode(None, on).signal
    assert dev.encode(on, on).signal == dev.encode(None, on).signal


def test_message_shape():
    signal = device().encode(None, HvacState(True, "cool", 22.0)).signal
    assert signal.carrier == 38000
    assert signal.pulses[:2] == (3324, 1474)
    assert signal.pulses[-2:] == (467, 100000)
    assert len(signal.pulses) == 2 + 2 * 136 + 2


@pytest.mark.parametrize("model", MITSUBISHI136_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(
        registry.get_device("mitsubishi_electric", model), Mitsubishi136Device
    )


@pytest.mark.parametrize("model", MITSUBISHI136_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.mitsubishi_electric import Mitsubishi136

    legacy = LegacyDevice("mitsubishi_electric", model, Mitsubishi136)
    assert device(model).capabilities == legacy.capabilities


def _record(swing=None, fan=None):
    return next(
        r
        for r in load_oracle("MITSUBISHI136")
        if (swing is None or r["state"].get("swing") == swing)
        and (fan is None or r["state"].get("fan") == fan)
        and "quiet" not in r["state"]
    )


@pytest.mark.parametrize(
    "record_kw, missing",
    [
        ({"fan": "lowest"}, FAN_MIN),
        ({"swing": "90°"}, SWING_HIGHEST),
        ({"swing": "60°"}, SWING_HIGH),
    ],
)
def test_undeclared_deviation_is_reported(record_kw, missing):
    dev = device()
    record = _record(**record_kw)
    declared = tuple(d for d in DEFECTS if d != missing)
    with pytest.raises(AssertionError, match=missing.field):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=declared)


def test_layouts_must_cover_every_frame():
    dev = device()
    record = _record(swing="90°")
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_mitsubishi136_device.py -q`
Expected: collection error, `ImportError: cannot import name ...` from `pyhvac.plugins.mitsubishi_electric`.

- [ ] **Step 3: Implement**: insert immediately before `# Now the match between models and objects` in `pyhvac/plugins/mitsubishi_electric.py`:

```python
# -------------------------------------------------------- Mitsubishi136
# Layout from IRremoteESP8266's Mitsubishi136Protocol (ir_Mitsubishi.h):
# 17 bytes sent LSB first in one frame, no repeat (sendMitsubishi136:
# kMitsubishi136MinRepeat = kNoRepeat). Bytes 11-16 are the complements of
# bytes 5-10 (IRMitsubishi136::checksum): the inverted section.

MITSUBISHI136 = Protocol(
    "mitsubishi136",
    {
        "main": Section(
            PulseDistance(467, 351, 1137),  # kMitsubishi136BitMark/Zero/OneSpace
            header=(3324, 1474),  # kMitsubishi136HdrMark/HdrSpace
            footer=(467,),
            gap=100000,  # kMitsubishi136Gap (kDefaultMessageGap)
        ),
    },
    carrier=38000,  # sendMitsubishi136: 38 kHz
)


@dataclass(frozen=True)
class Mitsubishi136Checksum(Checksum):
    """IRMitsubishi136::checksum: data[at + i] = ~data[start + i] for the
    ``end - start`` bytes from kMitsubishi136PowerByte (5..10 -> 11..16)."""

    def positions(self):
        return set(range(self.at, self.at + self.end - self.start))

    def compute(self, data):
        return bytes(~b & 0xFF for b in data[self.start : self.end])

    def apply(self, data):
        data[self.at : self.at + self.end - self.start] = self.compute(data)

    def check(self, data):
        return bytes(data[self.at : self.at + self.end - self.start]) == (
            self.compute(data)
        )


MITSUBISHI136_MODE = {  # kMitsubishi136*, as IRMitsubishi136::convertMode
    "fan": 0b000,  # kMitsubishi136Fan
    "cool": 0b001,  # kMitsubishi136Cool
    "heat": 0b010,  # kMitsubishi136Heat
    "auto": 0b011,  # kMitsubishi136Auto
    "dry": 0b101,  # kMitsubishi136Dry
}
MITSUBISHI136_FAN = {  # canonical fan -> kMitsubishi136Fan*
    "auto": 0b10,  # convertFan's default: kMitsubishi136FanMed (no auto code)
    "1": 0b00,  # lowest: kMitsubishi136FanMin (see Mitsubishi136Device)
    "2": 0b01,  # kMitsubishi136FanLow
    "3": 0b10,  # kMitsubishi136FanMed
    "4": 0b11,  # high: kMitsubishi136FanMax, as convertFan
    "5": 0b11,  # highest: kMitsubishi136FanMax
}
MITSUBISHI136_FAN_QUIET = 0b00  # kMitsubishi136FanQuiet (= FanMin)
MITSUBISHI136_SWING_V = {  # canonical swing -> kMitsubishi136SwingV*
    "off": 0b1100,  # convertSwingV(kOff): kMitsubishi136SwingVAuto (no off)
    "auto": 0b1100,  # kMitsubishi136SwingVAuto
    "1": 0b0011,  # 90°: kMitsubishi136SwingVHighest (topmost, counting down)
    "2": 0b0010,  # 60°: kMitsubishi136SwingVHigh
    "3": 0b0001,  # 30°: kMitsubishi136SwingVLow
    "4": 0b0000,  # 0°: kMitsubishi136SwingVLowest
}
MITSUBISHI136_MIN_TEMP, MITSUBISHI136_MAX_TEMP = 17, 30  # kMitsubishi136Min/MaxTemp
MITSUBISHI136_TEMP_OFFSET = 16  # setTemp stores degrees - kMitsubishiAcMinTemp

# Skeleton: IRMitsubishi136::stateReset (kReset, zero-padded to 17 bytes;
# memcpy writes every byte, so nothing comes from stale memory) with the
# fields and the inverted section cleared. Byte 7 bit 0 stays set, as in
# kReset and the PEAD-RP71JAA capture of ir_Mitsubishi_test.cpp.
MITSUBISHI136_LAYOUT = Layout(
    bytes.fromhex("23cb262100000001040000000000000000"),
    {
        "power": Field.at(5, 6, 1),
        "mode": Field.at(6, 0, 3, values=MITSUBISHI136_MODE),
        "temperature": Field.at(6, 4, 4),  # °C - 16 (kMitsubishiAcMinTemp)
        "fan": Field.at(7, 1, 2),
        "swing_v": Field.at(7, 4, 4),
    },
    checksum=Mitsubishi136Checksum(5, 11, 11),
)


class Mitsubishi136Device(Device):
    """Mitsubishi136 (PEAD-RP71JAA, PAR-FA32MA): a full-state protocol with
    no toggle bits, ``previous`` is ignored.

    As the C path (IRac::mitsubishi136): an off message carries mode auto
    (IRac passes mode "off", convertMode's default), the setpoint is whole
    degrees clamped to 17-30, auto fan sends Med, swing off sends Auto
    (there is no off code), and quiet forces kMitsubishi136FanQuiet.

    Two documented values differ from the C output (declared Defects):
    - fan lowest sends kMitsubishi136FanMin: convertFan maps kMin there,
      but IRac's setQuiet(false) then turns it into FanLow because FanMin is
      also FanQuiet;
    - swing positions count down from kMitsubishi136SwingVHighest: the
      legacy labels 90° and 60° reach C as kHigh and kUpperMiddle, which
      convertSwingV maps to High and Auto.
    """

    PROTOCOL = MITSUBISHI136
    LAYOUTS = (MITSUBISHI136_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "fan", "dry", "heat"),
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
        swing_v=Choice(
            ("off", "auto", "1", "2", "3", "4"),
            {
                "off": "off",
                "auto": "auto",
                "1": "90°",
                "2": "60°",
                "3": "30°",
                "4": "0°",
            },
        ),
        features={"quiet": Choice((False, True), {False: "off", True: "on"})},
    )

    def frames(self, previous, target, actions):
        mode = target.mode if target.power else "auto"
        degrees = min(
            max(int(target.temperature), MITSUBISHI136_MIN_TEMP),
            MITSUBISHI136_MAX_TEMP,
        )
        if target.features.get("quiet"):
            fan = MITSUBISHI136_FAN_QUIET
        else:
            fan = MITSUBISHI136_FAN[target.fan]
        data = MITSUBISHI136_LAYOUT.build(
            power=target.power,
            mode=mode,
            temperature=degrees - MITSUBISHI136_TEMP_OFFSET,
            fan=fan,
            swing_v=MITSUBISHI136_SWING_V[target.swing_v],
        )
        return [Frame("main", bytes(data))]


MITSUBISHI136_MODELS = (
    "PEAD-RP71JAA Ducted",
    "001CP T7WE10714 remote",
    "PAR-FA32MA remote",
    "generic 136",
)


DEVICES.update({m: Mitsubishi136Device for m in MITSUBISHI136_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_mitsubishi136_device.py -q`
Expected: 261 passed, 4 skipped (the skips need the C extension).

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/mitsubishi_electric.py tests/test_mitsubishi136_device.py
git add pyhvac/plugins/mitsubishi_electric.py tests/test_mitsubishi136_device.py
git commit -m "MITSUBISHI136: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 4: MITSUBISHI112

One 14-byte frame, `Sum8(0, 13, 13)`; layout from `union Mitsubishi112Protocol`.

**Files:**
- Modify: `pyhvac/plugins/mitsubishi_electric.py` (block before `# Now the match between models and objects`)
- Test: `tests/test_mitsubishi112_device.py`

**Interfaces:**
- Consumes: `Device`, `pyhvac.fields`, `tests/port_oracle.py`, and the oracle fixture `MITSUBISHI112`.
- Produces: `Mitsubishi112Device`, `MITSUBISHI112_MODELS`, and the `DEVICES` entries for those models.

- [ ] **Step 1: Write the failing tests**: create `tests/test_mitsubishi112_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.mitsubishi_electric import (
    MITSUBISHI112_LAYOUT,
    MITSUBISHI112_MODELS,
    Mitsubishi112Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented values here:
# - the old swing labels go through IRGHVAC.trans_swing ("90°" -> kHigh,
#   "60°" -> kUpperMiddle) into IRMitsubishi112::convertSwingV, which maps
#   kHigh to kMitsubishi112SwingVHigh (so kMitsubishi112SwingVHighest is never
#   sent) and has no kUpperMiddle case (it falls back to SwingVAuto);
# - convertFan maps lowest (kMin) to kMitsubishi112FanMin, but
#   IRac::mitsubishi112 then calls setQuiet(false), and since FanMin equals
#   kMitsubishi112FanQuiet, setQuiet turns it into kMitsubishi112FanLow.
DEFECTS = (
    Defect("swing_v", "1", "2", "C sends SwingVHigh for highest"),
    Defect("swing_v", "2", "auto", "C has no upper-middle case: sends auto"),
    Defect("fan", "1", "2", "setQuiet(false) turns FanMin into FanLow"),
)

# ir_Mitsubishi_test.cpp (KPOA remote capture): power on, cool, 23 °C,
# fan 2 (quiet), swing V and H auto.
REAL_CAPTURE = bytes.fromhex("23cb2601002403083a00000030ae")


def device(model="KPOA remote"):
    return Mitsubishi112Device("mitsubishi_electric", model)


def read(state):
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(state), ())
    return MITSUBISHI112_LAYOUT.read(frame.data)


def _with_c_defaults(record):
    # A record without "fan" relied on IRac's default (kAuto), which
    # IRMitsubishi112::convertFan sends as kMitsubishi112FanMed ("medium").
    # Missing swing/hswing (kOff) fall back to auto, as the port's defaults.
    return {**record, "state": {"fan": "medium", **record["state"]}}


@pytest.mark.parametrize("record", oracle_params("MITSUBISHI112"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, _with_c_defaults(record), dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("MITSUBISHI112"):
        state = state_from_record(dev, _with_c_defaults(record)["state"])
        (frame,) = dev.frames(None, state, ())
        values = MITSUBISHI112_LAYOUT.read(frame.data)
        assert MITSUBISHI112_LAYOUT.build(**values) == bytearray(frame.data)
        assert MITSUBISHI112_LAYOUT.checksum.check(frame.data)


@pytest.mark.parametrize(
    "state",
    [
        HvacState(True, "cool", 23.0, fan="1", swing_v="auto", swing_h="auto"),
        HvacState(
            True,
            "cool",
            23.0,
            fan="4",
            swing_v="auto",
            swing_h="auto",
            features={"quiet": True},
        ),
    ],
)
def test_the_kpoa_capture_is_reproduced(state):
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(state), ())
    assert frame.data == REAL_CAPTURE


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat"])
def test_off_carries_mode_auto_and_the_setpoint(mode):
    # IRac passes mode "off"; convertMode maps it to auto.
    for t in (16.0, 25.0):
        values = read(HvacState(False, mode, t))
        assert (values["power"], values["mode"], values["temperature"]) == (
            0,
            "auto",
            31 - int(t),
        )


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat"])
def test_setpoint_is_31_minus_whole_degrees_clamped_to_16_25(mode):
    assert read(HvacState(True, mode, 10.0))["temperature"] == 15
    assert read(HvacState(True, mode, 21.0))["temperature"] == 10
    assert read(HvacState(True, mode, 30.0))["temperature"] == 6


def test_mode_codes():
    for mode, raw in (("auto", 7), ("cool", 3), ("dry", 2), ("heat", 1)):
        values = read(HvacState(True, mode, 20.0))
        assert values["mode"] == mode
        assert MITSUBISHI112_LAYOUT.fields["mode"].values[mode] == raw


@pytest.mark.parametrize("fan, raw", [("1", 2), ("2", 3), ("3", 5), ("4", 0)])
def test_every_fan_level_uses_the_documented_code(fan, raw):
    # "1" (lowest) sends kMitsubishi112FanMin although the C path sends
    # FanLow (the declared fan defect).
    dev = device()
    (frame,) = dev.frames(
        None, dev.normalise(HvacState(True, "cool", 22.0, fan=fan)), ()
    )
    assert MITSUBISHI112_LAYOUT.read_raw(frame.data, "fan") == raw


@pytest.mark.parametrize("fan", ["1", "2", "3", "4"])
def test_quiet_overrides_the_fan(fan):
    # setQuiet(true) runs after setFan and stores kMitsubishi112FanQuiet.
    state = HvacState(True, "cool", 22.0, fan=fan, features={"quiet": True})
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(state), ())
    assert MITSUBISHI112_LAYOUT.read_raw(frame.data, "fan") == 0b010


@pytest.mark.parametrize(
    "swing, raw",
    [("off", 7), ("auto", 7), ("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 5)],
)
def test_every_vertical_swing_value(swing, raw):
    # "off" is auto, as the C path (the header documents no off value);
    # positions count down from kMitsubishi112SwingVHighest.
    dev = device()
    state = dev.normalise(HvacState(True, "cool", 22.0, fan="3", swing_v=swing))
    (frame,) = dev.frames(None, state, ())
    assert MITSUBISHI112_LAYOUT.read_raw(frame.data, "swing_v") == raw


@pytest.mark.parametrize(
    "swing, raw",
    [
        ("auto", 0b1100),
        ("1", 0b0001),
        ("2", 0b0010),
        ("3", 0b0011),
        ("4", 0b0100),
        ("5", 0b0101),
        ("6", 0b1000),
    ],
)
def test_every_horizontal_swing_value(swing, raw):
    dev = device()
    state = dev.normalise(HvacState(True, "cool", 22.0, fan="3", swing_h=swing))
    (frame,) = dev.frames(None, state, ())
    assert MITSUBISHI112_LAYOUT.read_raw(frame.data, "swing_h") == raw


def test_previous_is_ignored():
    dev = device()
    on = HvacState(True, "cool", 22.0, fan="3")
    off = HvacState(False, "cool", 22.0, fan="3")
    assert dev.encode(off, on).signal == dev.encode(None, on).signal
    assert dev.encode(on, on).signal == dev.encode(None, on).signal
    assert dev.encode(on, off).signal == dev.encode(None, off).signal


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (3450, 1696)
    assert pulses[-2:] == (450, 100000)
    assert len(pulses) == 2 + 2 * 112 + 2


@pytest.mark.parametrize("model", MITSUBISHI112_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(
        registry.get_device("mitsubishi_electric", model), Mitsubishi112Device
    )


@pytest.mark.parametrize("model", MITSUBISHI112_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.mitsubishi_electric import Mitsubishi112

    legacy = LegacyDevice("mitsubishi_electric", model, Mitsubishi112)
    assert device(model).capabilities == legacy.capabilities


@pytest.mark.parametrize(
    "old, field",
    [
        ({"swing": "90°"}, "swing_v"),
        ({"swing": "60°"}, "swing_v"),
        ({"fan": "lowest"}, "fan"),
    ],
)
def test_undeclared_deviation_is_reported(old, field):
    dev = device()
    record = next(
        r
        for r in load_oracle("MITSUBISHI112")
        if all(r["state"].get(k) == v for k, v in old.items())
        and r["state"]["mode"] != "off"
    )
    with pytest.raises(AssertionError, match=field):
        assert_matches_oracle(dev, _with_c_defaults(record), dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("MITSUBISHI112")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, _with_c_defaults(record), (), DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_mitsubishi112_device.py -q`
Expected: collection error, `ImportError: cannot import name ...` from `pyhvac.plugins.mitsubishi_electric`.

- [ ] **Step 3: Implement**: insert immediately before `# Now the match between models and objects` in `pyhvac/plugins/mitsubishi_electric.py`:

```python
# ----------------------------------------------------------- Mitsubishi112
# Layout from IRremoteESP8266's Mitsubishi112Protocol (ir_Mitsubishi.h): 14
# bytes sent LSB first in one frame (sendMitsubishi112 -> sendGeneric with
# MSBfirst false), closed by a sum of bytes 0-12 (IRMitsubishi112::checksum
# uses IRTcl112Ac::calcChecksum; byte 3 is never 0x02, so no offset).

MITSUBISHI112 = Protocol(
    "mitsubishi112",
    {
        "main": Section(
            PulseDistance(450, 385, 1250),  # kMitsubishi112BitMark/Zero/OneSpace
            header=(3450, 1696),  # kMitsubishi112HdrMark/HdrSpace
            footer=(450,),
            gap=100000,  # kMitsubishi112Gap (kDefaultMessageGap)
        ),
    },
    carrier=38000,  # sendGeneric(..., 38, ...)
)

MITSUBISHI112_MODE = {  # kMitsubishi112*, as convertMode (no fan-only mode)
    "auto": 0b111,
    "cool": 0b011,
    "heat": 0b001,
    "dry": 0b010,
}
MITSUBISHI112_FAN = {  # canonical fan -> kMitsubishi112Fan*, as convertFan
    "1": 0b010,  # lowest: kMitsubishi112FanMin (= kMitsubishi112FanQuiet)
    "2": 0b011,  # kMitsubishi112FanLow
    "3": 0b101,  # kMitsubishi112FanMed
    "4": 0b000,  # highest: kMitsubishi112FanMax
}
MITSUBISHI112_SWING_V = {  # kMitsubishi112SwingV*; the header has no "off"
    "auto": 0b111,
    "off": 0b111,  # as the C path: convertSwingV maps kOff to auto
    "1": 0b001,  # highest
    "2": 0b010,  # high
    "3": 0b011,  # middle
    "4": 0b100,  # low
    "5": 0b101,  # lowest
}
MITSUBISHI112_SWING_H = {  # kMitsubishi112SwingH*, as convertSwingH
    "auto": 0b1100,
    "1": 0b0001,  # far left: kMitsubishi112SwingHLeftMax
    "2": 0b0010,  # left
    "3": 0b0011,  # middle
    "4": 0b0100,  # right
    "5": 0b0101,  # far right: kMitsubishi112SwingHRightMax
    "6": 0b1000,  # wide
}
MITSUBISHI112_MAX_TEMP = 31  # kMitsubishiAcMaxTemp: Temp holds 31 - setpoint

# Skeleton: IRMitsubishi112::stateReset (kReset, byte 13 zero-initialised),
# which writes every byte, so no padding bit comes from stale memory.
MITSUBISHI112_LAYOUT = Layout(
    bytes.fromhex("23cb260100240308100000003000"),
    {
        "power": Field.at(5, 2, 1),
        "mode": Field.at(6, 0, 3, values=MITSUBISHI112_MODE),
        "temperature": Field.at(7, 0, 4),  # 31 - whole °C
        "fan": Field.at(8, 0, 3, values=MITSUBISHI112_FAN),
        "swing_v": Field.at(8, 3, 3, values=MITSUBISHI112_SWING_V),
        "swing_h": Field.at(12, 2, 4, values=MITSUBISHI112_SWING_H),
    },
    checksum=Sum8(0, 13, 13),
)


class Mitsubishi112Device(Device):
    """Mitsubishi112 (KPOA remote): a full-state protocol, ``previous`` is
    ignored (no toggle bits; IRac::handleToggles has no MITSUBISHI112 case).

    Quiet has no bit of its own: as IRMitsubishi112::setQuiet, it sends
    kMitsubishi112FanQuiet (= kMitsubishi112FanMin) whatever the fan.
    """

    PROTOCOL = MITSUBISHI112
    LAYOUTS = (MITSUBISHI112_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "heat"),
        temperature=TemperatureRange(16.0, 25.0),
        fan=Choice(
            ("1", "2", "3", "4"),
            {"1": "lowest", "2": "low", "3": "medium", "4": "highest"},
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
        swing_h=Choice(
            ("auto", "1", "2", "3", "4", "5", "6"),
            {
                "auto": "auto",
                "1": "far left",
                "2": "left",
                "3": "middle",
                "4": "right",
                "5": "far right",
                "6": "wide",
            },
        ),
        features={"quiet": Choice((False, True), {False: "off", True: "on"})},
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to auto) and the setpoint as given.
        # Quiet overrides the fan (setQuiet runs after setFan).
        fan = "1" if target.features["quiet"] else target.fan
        data = MITSUBISHI112_LAYOUT.build(
            power=target.power,
            mode=target.mode if target.power else "auto",
            temperature=MITSUBISHI112_MAX_TEMP - int(target.temperature),
            fan=fan,
            swing_v=target.swing_v,
            swing_h=target.swing_h,
        )
        return [Frame("main", bytes(data))]


MITSUBISHI112_MODELS = ("MSH-A24WV", "MUH-A24WV", "KPOA remote", "generic 112")


DEVICES.update({m: Mitsubishi112Device for m in MITSUBISHI112_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_mitsubishi112_device.py -q`
Expected: 244 passed, 4 skipped (the skips need the C extension).

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/mitsubishi_electric.py tests/test_mitsubishi112_device.py
git add pyhvac/plugins/mitsubishi_electric.py tests/test_mitsubishi112_device.py
git commit -m "MITSUBISHI112: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 5: MITSUBISHI_HEAVY_152

One 19-byte frame with inverted pairs (`InvertedPairs(3, 19)`); layout from `union Mitsubishi152Protocol` (ir_MitsubishiHeavy.h).

**Files:**
- Modify: `pyhvac/plugins/mitsubishi_heavy_industries.py` (block before `# Now the match between models and objects`)
- Test: `tests/test_mitsubishi_heavy152_device.py`

**Interfaces:**
- Consumes: `Device`, `pyhvac.fields`, `tests/port_oracle.py`, and the oracle fixture `MITSUBISHI_HEAVY_152`.
- Produces: `MitsubishiHeavy152Device`, `MITSUBISHI_HEAVY152_MODELS`, and the `DEVICES` entries for those models.

- [ ] **Step 1: Write the failing tests**: create `tests/test_mitsubishi_heavy152_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.ir.codec import decode
from pyhvac.plugins.mitsubishi_heavy_industries import (
    MITSUBISHI_HEAVY152,
    MITSUBISHI_HEAVY152_LAYOUT,
    MITSUBISHI_HEAVY152_MODELS,
    MitsubishiHeavy152Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Mitsubishi152Protocol values here:
# - fan lowest: IRMitsubishiHeavy152Ac::convertFan maps kMin to
#   kMitsubishiHeavy152FanEcono (0x6), then IRac::mitsubishiHeavy152 calls
#   setEcono(false), which sees getEcono() and resets the fan to Auto (0x0);
# - swing "90°"/"60°" (canonical "1"/"2"): IRGHVAC.trans_swing maps them to
#   kHigh and kUpperMiddle; convertSwingV sends kHigh as
#   kMitsubishiHeavy152SwingVHigh (2) and has no kUpperMiddle case, so it
#   sends kMitsubishiHeavy152SwingVOff (6). The port counts the documented
#   positions from the top: Highest (1), High (2);
# - sleep: IRGHVAC.build_ircode's key map has no "sleep", so IRac's sleep
#   stays -1 and setNight(sleep >= 0) never sets Night (byte 15 bit 6).
FAN_LOWEST = Defect("fan", "econo", "auto", "IRac's setEcono(false) resets Econo")
SWING_HIGHEST = Defect("swing_v", "highest", "high", "glue sends kHigh for 90°")
SWING_HIGH = Defect("swing_v", "high", "off", "convertSwingV: no kUpperMiddle")
NIGHT = Defect("night", 1, 0, "legacy glue never passes sleep")
DEFECTS = (FAN_LOWEST, SWING_HIGHEST, SWING_HIGH, NIGHT)

# ir_MitsubishiHeavy_test.cpp, ZmsRealExample (issue #660): power on, heat,
# 24 C, fan Max, swing(V) and swing(H) auto.
REAL_EXAMPLE = bytes.fromhex("ad513ce51a0cf307f804fb00ff00ff00ff807f")
# ZmsSyntheticExample: the same settings with the power off.
OFF_EXAMPLE = bytes.fromhex("ad513ce51a04fb07f804fb00ff00ff00ff807f")


def device(model="RLA502A700B remote"):
    return MitsubishiHeavy152Device("mitsubishi_heavy_industries", model)


def with_hswing(record):
    # A record without "hswing" leaves IRac's swingh at kOff, which
    # convertSwingH sends as kMitsubishiHeavy152SwingHOff (8). The legacy
    # entity has no "off" swing_h; its "wide" (canonical "6") is the value
    # the C path sends as 8 (convertSwingH has no kWide case), so the record
    # is read as "wide" (checked against the C path in cpath_check.py).
    if "hswing" in record["state"]:
        return record
    return {**record, "state": {**record["state"], "hswing": "wide"}}


def frame(state, previous=None):
    dev = device()
    if previous is not None:
        previous = dev.normalise(previous)
    (main,) = dev.frames(previous, dev.normalise(state), ())
    return main.data


def read(state, previous=None):
    return MITSUBISHI_HEAVY152_LAYOUT.read(frame(state, previous))


@pytest.mark.parametrize("record", oracle_params("MITSUBISHI_HEAVY_152"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, with_hswing(record), dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("MITSUBISHI_HEAVY_152"):
        state = state_from_record(dev, with_hswing(record)["state"])
        (main,) = dev.frames(None, state, ())
        values = MITSUBISHI_HEAVY152_LAYOUT.read(main.data)
        assert MITSUBISHI_HEAVY152_LAYOUT.build(**values) == bytearray(main.data)


def test_every_oracle_frame_has_inverted_pairs_from_byte_3():
    # portkit checksum only tries InvertedPairs(0, n) on even lengths.
    for record in load_oracle("MITSUBISHI_HEAVY_152"):
        (main,) = decode(MITSUBISHI_HEAVY152, record["pulses"], expected=["main"])
        assert MITSUBISHI_HEAVY152_LAYOUT.checksum.check(main.data)
        assert main.data[:5] == bytes.fromhex("ad513ce51a")  # kMitsubishiHeavyZmsSig


def test_no_field_sits_in_a_complement_byte():
    complements = MITSUBISHI_HEAVY152_LAYOUT.checksum.positions()
    for name, f in MITSUBISHI_HEAVY152_LAYOUT.fields.items():
        assert not {b // 8 for b in f.bits} & complements, name


def test_the_real_capture_is_reproduced():
    state = HvacState(True, "heat", 24.0, fan="5", swing_v="auto", swing_h="auto")
    assert frame(state) == REAL_EXAMPLE


def test_the_off_capture_differs_only_by_the_mode_an_off_message_carries():
    # The C path (and the port) send mode auto when off; the remote kept heat.
    state = HvacState(False, "heat", 24.0, fan="5", swing_v="auto", swing_h="auto")
    ours = frame(state)
    assert {i for i, (a, b) in enumerate(zip(ours, OFF_EXAMPLE)) if a != b} == {5, 6}
    values = MITSUBISHI_HEAVY152_LAYOUT.read(OFF_EXAMPLE)
    assert {**values, "mode": "auto"} == MITSUBISHI_HEAVY152_LAYOUT.read(ours)


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan", "heat"])
@pytest.mark.parametrize("t", [17.0, 31.0])
def test_off_carries_mode_auto_in_every_mode(mode, t):
    # IRac passes mode "off"; convertMode maps it to kMitsubishiHeavyAuto.
    values = read(HvacState(False, mode, t))
    assert (values["power"], values["mode"], values["temp"]) == (0, "auto", t - 17)


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan", "heat"])
def test_mode_codes_and_the_setpoint_in_every_mode(mode):
    for t in (17.0, 24.0, 31.0):
        values = read(HvacState(True, mode, t))
        assert (values["power"], values["mode"], values["temp"]) == (1, mode, t - 17)


def test_setpoint_is_clamped_to_17_31():
    assert read(HvacState(True, "cool", 10.0))["temp"] == 0
    assert read(HvacState(True, "cool", 40.0))["temp"] == 14


@pytest.mark.parametrize(
    "fan, raw", [("auto", 0), ("1", 6), ("2", 1), ("3", 2), ("4", 3), ("5", 4)]
)
def test_every_fan_level(fan, raw):
    data = frame(HvacState(True, "cool", 22.0, fan=fan))
    assert MITSUBISHI_HEAVY152_LAYOUT.read_raw(data, "fan") == raw


@pytest.mark.parametrize("fan", ["auto", "1", "2", "3", "4", "5"])
def test_powerful_is_turbo_and_economy_is_econo_and_wins(fan):
    def fan_of(**features):
        return read(HvacState(True, "cool", 22.0, fan=fan, features=features))["fan"]

    assert fan_of(powerful=True) == "turbo"
    assert fan_of(economy=True) == "econo"
    # setEcono runs after setTurbo.
    assert fan_of(powerful=True, economy=True) == "econo"


@pytest.mark.parametrize(
    "swing_v, raw",
    [("off", 6), ("auto", 0), ("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 5)],
)
def test_every_swing_v_value(swing_v, raw):
    data = frame(HvacState(True, "cool", 22.0, swing_v=swing_v))
    assert MITSUBISHI_HEAVY152_LAYOUT.read_raw(data, "swing_v") == raw


@pytest.mark.parametrize(
    "swing_h, raw",
    [("auto", 0), ("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 5), ("6", 8)],
)
def test_every_swing_h_value(swing_h, raw):
    # "wide" (canonical "6") is sent as kMitsubishiHeavy152SwingHOff, as C.
    data = frame(HvacState(True, "cool", 22.0, swing_h=swing_h))
    assert MITSUBISHI_HEAVY152_LAYOUT.read_raw(data, "swing_h") == raw


@pytest.mark.parametrize(
    "features, bits",
    [
        ({}, (0, 0, 0, 0)),
        ({"cleaning": True}, (1, 0, 0, 0)),
        ({"purifier": True}, (0, 1, 0, 0)),
        ({"cleaning": True, "purifier": True}, (1, 1, 0, 0)),
        ({"sleep": True}, (0, 0, 1, 0)),
        ({"quiet": True}, (0, 0, 0, 1)),
    ],
)
def test_feature_bits(features, bits):
    # setClean writes Clean and Filter, then setFilter(purifier) rewrites
    # Filter: cleaning alone leaves Filter clear.
    values = read(HvacState(True, "cool", 22.0, features=features))
    assert (
        values["clean"],
        values["filter"],
        values["night"],
        values["silent"],
    ) == bits
    assert (values["three"], values["d"]) == (0, 0)  # IRac never calls set3D


def test_previous_is_ignored():
    dev = device()
    on = HvacState(True, "cool", 22.0, swing_v="auto", features={"quiet": True})
    off = HvacState(False, "heat", 30.0)
    assert dev.encode(off, on).signal == dev.encode(None, on).signal
    assert dev.encode(on, on).signal == dev.encode(None, on).signal


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (3140, 1630)
    assert pulses[-2:] == (370, 100000)
    assert len(pulses) == 2 + 2 * 152 + 2


@pytest.mark.parametrize("model", MITSUBISHI_HEAVY152_MODELS)
def test_registry_serves_the_port(model):
    dev = registry.get_device("mitsubishi_heavy_industries", model)
    assert isinstance(dev, MitsubishiHeavy152Device)


@pytest.mark.parametrize("model", MITSUBISHI_HEAVY152_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.mitsubishi_heavy_industries import Mitsubishi152

    legacy = LegacyDevice("mitsubishi_heavy_industries", model, Mitsubishi152)
    assert device(model).capabilities == legacy.capabilities


@pytest.mark.parametrize(
    "select, defect, field",
    [
        (lambda s: s.get("fan") == "lowest", FAN_LOWEST, "fan"),
        (lambda s: s.get("swing") == "90°", SWING_HIGHEST, "swing_v"),
        (lambda s: s.get("swing") == "60°", SWING_HIGH, "swing_v"),
        (lambda s: s.get("sleep") == "on", NIGHT, "night"),
    ],
)
def test_undeclared_deviation_is_reported(select, defect, field):
    dev = device()
    record = next(r for r in load_oracle("MITSUBISHI_HEAVY_152") if select(r["state"]))
    others = tuple(d for d in DEFECTS if d != defect)
    with pytest.raises(AssertionError, match=field):
        assert_matches_oracle(dev, with_hswing(record), dev.LAYOUTS, defects=others)


def test_missing_hswing_is_not_silently_accepted():
    dev = device()
    record = next(
        r for r in load_oracle("MITSUBISHI_HEAVY_152") if "hswing" not in r["state"]
    )
    with pytest.raises(AssertionError, match="swing_h"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_mitsubishi_heavy152_device.py -q`
Expected: collection error, `ImportError: cannot import name ...` from `pyhvac.plugins.mitsubishi_heavy_industries`.

- [ ] **Step 3: Implement**: insert immediately before `# Now the match between models and objects` in `pyhvac/plugins/mitsubishi_heavy_industries.py`:

```python
# --------------------------------------------------------- MitsubishiHeavy152
# Layout from IRremoteESP8266's Mitsubishi152Protocol (ir_MitsubishiHeavy.h):
# 19 bytes, one frame sent LSB first (sendMitsubishiHeavy152 ->
# sendMitsubishiHeavy88: sendGeneric with MSBfirst false, 38 kHz). Bytes 0-4
# are kMitsubishiHeavyZmsSig; from byte 3 on every second byte is the
# complement of the one before it (IRMitsubishiHeavy152Ac::checksum:
# invertBytePairs(raw + 3, 16)), so every field sits in an odd byte.

MITSUBISHI_HEAVY152 = Protocol(
    "mitsubishi_heavy152",
    {
        "main": Section(
            # kMitsubishiHeavyBitMark / ZeroSpace / OneSpace
            PulseDistance(370, 1220, 420),
            header=(3140, 1630),  # kMitsubishiHeavyHdrMark / HdrSpace
            footer=(370,),
            gap=100000,  # kMitsubishiHeavyGap (kDefaultMessageGap)
        ),
    },
    carrier=38000,
)

MITSUBISHI_HEAVY152_MODE = {  # kMitsubishiHeavy{Auto,Cool,Dry,Fan,Heat}
    "auto": 0,
    "cool": 1,
    "dry": 2,
    "fan": 3,
    "heat": 4,
}
MITSUBISHI_HEAVY152_FAN = {  # kMitsubishiHeavy152Fan*
    "auto": 0x0,
    "low": 0x1,
    "med": 0x2,
    "high": 0x3,
    "max": 0x4,
    "econo": 0x6,
    "turbo": 0x8,
}
MITSUBISHI_HEAVY152_FAN_OF = {  # canonical fan -> code name, as convertFan
    "auto": "auto",
    "1": "econo",  # lowest: kMin -> kMitsubishiHeavy152FanEcono
    "2": "low",
    "3": "med",
    "4": "high",
    "5": "max",
}
MITSUBISHI_HEAVY152_SWING_V = {  # kMitsubishiHeavy152SwingV*
    "auto": 0,
    "highest": 1,
    "high": 2,
    "middle": 3,
    "low": 4,
    "lowest": 5,
    "off": 6,
}
MITSUBISHI_HEAVY152_SWING_V_OF = {  # canonical swing_v -> code name
    "off": "off",
    "auto": "auto",
    "1": "highest",  # 90°: the topmost documented position
    "2": "high",  # 60°
    "3": "middle",  # 45°
    "4": "low",  # 30°
    "5": "lowest",  # 0°
}
MITSUBISHI_HEAVY152_SWING_H = {  # kMitsubishiHeavy152SwingH*
    "auto": 0,
    "left_max": 1,
    "left": 2,
    "middle": 3,
    "right": 4,
    "right_max": 5,
    "right_left": 6,
    "left_right": 7,
    "off": 8,
}
MITSUBISHI_HEAVY152_SWING_H_OF = {  # canonical swing_h -> code name
    "auto": "auto",
    "1": "left_max",  # far left
    "2": "left",
    "3": "middle",
    "4": "right",
    "5": "right_max",  # far right
    # "wide": convertSwingH has no kWide case and falls back to SwingHOff;
    # the header documents no wide position.
    "6": "off",
}
MITSUBISHI_HEAVY152_MIN_TEMP = 17  # kMitsubishiHeavyMinTemp

# Skeleton: IRMitsubishiHeavy152Ac::stateReset (the signature, raw[17] =
# 0x80, every other odd byte 0), the complements left for the checksum.
MITSUBISHI_HEAVY152_LAYOUT = Layout(
    bytes.fromhex("ad513ce51a0000000000000000000000008000"),
    {
        "mode": Field.at(5, 0, 3, values=MITSUBISHI_HEAVY152_MODE),
        "power": Field.at(5, 3, 1),
        "clean": Field.at(5, 5, 1),
        "filter": Field.at(5, 6, 1),
        "temp": Field.at(7, 0, 4),  # °C - kMitsubishiHeavyMinTemp
        "fan": Field.at(9, 0, 4, values=MITSUBISHI_HEAVY152_FAN),
        "three": Field.at(11, 1, 1),  # 3D, with "d"
        "d": Field.at(11, 4, 1),
        "swing_v": Field.at(11, 5, 3, values=MITSUBISHI_HEAVY152_SWING_V),
        "swing_h": Field.at(13, 0, 4, values=MITSUBISHI_HEAVY152_SWING_H),
        "night": Field.at(15, 6, 1),
        "silent": Field.at(15, 7, 1),
    },
    checksum=InvertedPairs(3, 19),
)


class MitsubishiHeavy152Device(Device):
    """Mitsubishi Heavy 152-bit (RLA502A700B, SRKxxZM-S): a full-state
    protocol, ``previous`` is ignored (the struct has no toggle bits).

    As IRac::mitsubishiHeavy152 does: an off message carries mode auto
    (convertMode maps IRac's "off" to kMitsubishiHeavyAuto); powerful sets
    the fan to kMitsubishiHeavy152FanTurbo (setTurbo after setFan), and
    economy to kMitsubishiHeavy152FanEcono, which wins over turbo (setEcono
    comes last); cleaning sets Clean and purifier sets Filter (setClean
    writes both bits, then setFilter overwrites Filter); 3D is never set.

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_mitsubishi_heavy152_device.py):
    - fan lowest: convertFan gives kMitsubishiHeavy152FanEcono, but IRac's
      setEcono(false) then resets it to auto; the port sends Econo;
    - swing_v "1" (90°) and "2" (60°): the old glue maps them to kHigh and
      kUpperMiddle, which convertSwingV sends as High and Off; the port sends
      the documented Highest and High (positions counted from the top);
    - sleep: the old glue never passes sleep, so setNight(sleep >= 0) never
      sets Night; the port sets it.
    """

    PROTOCOL = MITSUBISHI_HEAVY152
    LAYOUTS = (MITSUBISHI_HEAVY152_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "fan", "heat"),
        temperature=TemperatureRange(17.0, 31.0),
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
        swing_h=Choice(
            ("auto", "1", "2", "3", "4", "5", "6"),
            {
                "auto": "auto",
                "1": "far left",
                "2": "left",
                "3": "middle",
                "4": "right",
                "5": "far right",
                "6": "wide",
            },
        ),
        features={
            name: Choice((False, True), {False: "off", True: "on"})
            for name in (
                "quiet",
                "sleep",
                "purifier",
                "cleaning",
                "powerful",
                "economy",
            )
        },
    )

    def frames(self, previous, target, actions):
        features = target.features
        fan = MITSUBISHI_HEAVY152_FAN_OF[target.fan]
        if features["powerful"]:
            fan = "turbo"
        if features["economy"]:
            fan = "econo"
        data = MITSUBISHI_HEAVY152_LAYOUT.build(
            mode=target.mode if target.power else "auto",
            power=target.power,
            clean=features["cleaning"],
            filter=features["purifier"],
            temp=int(target.temperature) - MITSUBISHI_HEAVY152_MIN_TEMP,
            fan=fan,
            three=0,
            d=0,
            swing_v=MITSUBISHI_HEAVY152_SWING_V_OF[target.swing_v],
            swing_h=MITSUBISHI_HEAVY152_SWING_H_OF[target.swing_h],
            night=features["sleep"],
            silent=features["quiet"],
        )
        return [Frame("main", bytes(data))]


MITSUBISHI_HEAVY152_MODELS = (
    "RLA502A700B remote",
    "SRKxxZM-S A/C",
    "SRKxxZMXA-S A/C",
    "gemeric",
    "gemeric 152",
)


DEVICES.update({m: MitsubishiHeavy152Device for m in MITSUBISHI_HEAVY152_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_mitsubishi_heavy152_device.py -q`
Expected: 265 passed, 5 skipped (the skips need the C extension).

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/mitsubishi_heavy_industries.py tests/test_mitsubishi_heavy152_device.py
git add pyhvac/plugins/mitsubishi_heavy_industries.py tests/test_mitsubishi_heavy152_device.py
git commit -m "MITSUBISHI_HEAVY_152: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 6: MITSUBISHI_HEAVY_88

One 11-byte frame with inverted pairs (`InvertedPairs(3, 11)`); layout from `union Mitsubishi88Protocol`; swing codes scattered over non-adjacent bits (local `MitsubishiHeavy88SplitField`).

**Files:**
- Modify: `pyhvac/plugins/mitsubishi_heavy_industries.py` (block before `# Now the match between models and objects`)
- Test: `tests/test_mitsubishi_heavy88_device.py`

**Interfaces:**
- Consumes: `Device`, `pyhvac.fields`, `tests/port_oracle.py`, and the oracle fixture `MITSUBISHI_HEAVY_88`.
- Produces: `MitsubishiHeavy88Device`, `MITSUBISHI_HEAVY88_MODELS`, and the `DEVICES` entries for those models.

- [ ] **Step 1: Write the failing tests**: create `tests/test_mitsubishi_heavy88_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.mitsubishi_heavy_industries import (
    MITSUBISHI_HEAVY88_LAYOUT,
    MITSUBISHI_HEAVY88_MODELS,
    MitsubishiHeavy88Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Mitsubishi88 values here:
# - IRac::mitsubishiHeavy88 calls setFan(convertFan(fan)), then setTurbo(turbo)
#   and setEcono(econo). With powerful/economy off, they reset the
#   kMitsubishiHeavy88FanTurbo (kMax, "highest") and kMitsubishiHeavy88FanEcono
#   (kMin, "lowest") that convertFan returned to kMitsubishiHeavy88FanAuto.
#   The same auto comes out when the state has no fan at all (IRac's default).
# - the legacy glue maps "90°" to kHigh (convertSwingV: High) and "60°" to
#   kUpperMiddle, which convertSwingV has no case for (Off). The port counts
#   the positions down from the topmost documented one (Highest).
FAN_LOWEST = Defect("fan", "1", "auto", "IRac setEcono(false) resets Econo: auto")
FAN_HIGHEST = Defect("fan", "4", "auto", "IRac setTurbo(false) resets Turbo: auto")
SWING_1 = Defect("swing_v", "1", "2", "C sends High (kHigh) for '90°'")
SWING_2 = Defect("swing_v", "2", "off", "C has no upper-middle case: sends off")
DEFECTS = (FAN_LOWEST, FAN_HIGHEST, SWING_1, SWING_2)

# ir_MitsubishiHeavy_test.cpp (ZjsSyntheticExample): power on, dry, 25 C,
# fan auto, swing V off, swing H LeftRight.
SYNTHETIC_EXAMPLE = bytes.fromhex("ad513cd92648b700ff8a75")


def device(model="RKX502A001C remote"):
    return MitsubishiHeavy88Device("mitsubishi_heavy_industries", model)


def read(state):
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(state), ())
    return MITSUBISHI_HEAVY88_LAYOUT.read(frame.data)


def raw(state, field):
    dev = device()
    (frame,) = dev.frames(None, dev.normalise(state), ())
    return MITSUBISHI_HEAVY88_LAYOUT.read_raw(frame.data, field)


@pytest.mark.parametrize("record", oracle_params("MITSUBISHI_HEAVY_88"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("MITSUBISHI_HEAVY_88"):
        state = state_from_record(dev, record["state"])
        (frame,) = dev.frames(None, state, ())
        values = MITSUBISHI_HEAVY88_LAYOUT.read(frame.data)
        assert MITSUBISHI_HEAVY88_LAYOUT.build(**values) == bytearray(frame.data)
        assert MITSUBISHI_HEAVY88_LAYOUT.checksum.check(frame.data)


def test_the_synthetic_capture_reads_as_documented():
    layout = MITSUBISHI_HEAVY88_LAYOUT
    assert layout.checksum.check(SYNTHETIC_EXAMPLE)
    values = layout.read(SYNTHETIC_EXAMPLE)
    assert values == {
        "swing_v": "off",
        "swing_h": 0b0110,  # kMitsubishiHeavy88SwingHLeftRight: not in the entity
        "clean": 0,
        "fan": "auto",
        "mode": "dry",
        "power": 1,
        "temperature": 25 - 17,
    }


def test_the_synthetic_capture_differs_only_in_its_unreachable_values():
    # Fan auto and swing H LeftRight are not in the entity; with fan low and
    # swing H off instead, nothing else differs.
    capture = bytearray(SYNTHETIC_EXAMPLE)
    layout = MITSUBISHI_HEAVY88_LAYOUT
    layout.write_raw(capture, "fan", 2)
    layout.write_raw(capture, "swing_h", 0)
    layout.checksum.apply(capture)
    dev = device()
    (frame,) = dev.frames(
        None, dev.normalise(HvacState(True, "dry", 25.0, fan="2")), ()
    )
    assert frame.data == bytes(capture)


def test_split_swing_fields_use_the_struct_bits():
    # SwingV5 = byte 5 bit 1, SwingV7 = byte 7 bits 3-4;
    # SwingH1 = byte 5 bits 2-3, SwingH2 = byte 5 bits 6-7.
    layout = MITSUBISHI_HEAVY88_LAYOUT
    assert tuple(layout.fields["swing_v"].bits) == (41, 59, 60)
    assert tuple(layout.fields["swing_h"].bits) == (42, 43, 46, 47)
    lowest = layout.build(swing_v="5")  # 0b111
    assert (lowest[5] & 0x02, lowest[7] & 0x18) == (0x02, 0x18)
    right = layout.build(swing_h="4")  # 0b1101: SwingH1 = 0b01, SwingH2 = 0b11
    assert right[5] & 0xCC == 0b11000100


def test_no_field_overlaps_the_inverted_bytes():
    parity = {8 * b + i for b in (4, 6, 8, 10) for i in range(8)}
    for name, field in MITSUBISHI_HEAVY88_LAYOUT.fields.items():
        assert not parity & set(field.bits), name


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat"])
def test_off_carries_mode_auto(mode):
    # IRac passes mode "off"; convertMode maps it to kMitsubishiHeavyAuto.
    for t in (17.0, 24.0, 31.0):
        values = read(HvacState(False, mode, t))
        assert (values["power"], values["mode"], values["temperature"]) == (
            0,
            "auto",
            int(t) - 17,
        )


def test_mode_codes():
    for mode, code in (("auto", 0), ("cool", 1), ("dry", 2), ("heat", 4)):
        assert raw(HvacState(True, mode, 22.0), "mode") == code


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat"])
def test_setpoint_is_whole_degrees_offset_from_17(mode):
    assert read(HvacState(True, mode, 10.0))["temperature"] == 0
    assert read(HvacState(True, mode, 21.0))["temperature"] == 4
    assert read(HvacState(True, mode, 21.5))["temperature"] == 4
    assert read(HvacState(True, mode, 40.0))["temperature"] == 14


@pytest.mark.parametrize("fan, code", [("1", 7), ("2", 2), ("3", 3), ("4", 6)])
def test_every_fan_level_uses_its_documented_code(fan, code):
    # convertFan: kMin -> Econo, kLow, kMedium, kMax -> Turbo.
    assert raw(HvacState(True, "cool", 22.0, fan=fan), "fan") == code


@pytest.mark.parametrize("fan", ["1", "2", "3", "4"])
def test_powerful_and_economy_are_fan_codes(fan):
    # setTurbo(true) stores Turbo, then setEcono(true) stores Econo: economy
    # wins over powerful, and both win over the requested speed.
    def code(powerful, economy):
        features = {"powerful": powerful, "economy": economy}
        return raw(HvacState(True, "cool", 22.0, fan=fan, features=features), "fan")

    assert code(True, False) == 6
    assert code(False, True) == 7
    assert code(True, True) == 7


def test_cleaning_sets_the_clean_bit():
    on = HvacState(True, "cool", 22.0, features={"cleaning": True})
    assert (read(on)["clean"], read(HvacState(True, "cool", 22.0))["clean"]) == (
        1,
        0,
    )


@pytest.mark.parametrize(
    "position, code",
    [("off", 0), ("auto", 4), ("1", 6), ("2", 1), ("3", 3), ("4", 5), ("5", 7)],
)
def test_vertical_swing_counts_down_from_highest(position, code):
    assert raw(HvacState(True, "cool", 22.0, swing_v=position), "swing_v") == code


@pytest.mark.parametrize(
    "position, code",
    [("off", 0), ("auto", 8), ("1", 1), ("2", 5), ("3", 9), ("4", 13), ("5", 2)],
)
def test_horizontal_swing_runs_left_to_right(position, code):
    assert raw(HvacState(True, "cool", 22.0, swing_h=position), "swing_h") == code


def test_previous_is_ignored():
    dev = device()
    on = HvacState(True, "cool", 22.0, swing_v="auto")
    off = HvacState(False, "heat", 30.0)
    assert dev.encode(off, on).signal == dev.encode(None, on).signal
    assert dev.encode(on, on).signal == dev.encode(None, on).signal


def test_message_shape():
    signal = device().encode(None, HvacState(True, "cool", 22.0)).signal
    assert signal.carrier == 38000
    pulses = signal.pulses
    assert pulses[:2] == (3140, 1630)
    assert pulses[2:4] == (370, 420)  # 0xAD sent LSB first: a one first
    assert pulses[4:6] == (370, 1220)
    assert pulses[-2:] == (370, 100000)
    assert len(pulses) == 2 + 2 * 88 + 2


@pytest.mark.parametrize("model", MITSUBISHI_HEAVY88_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(
        registry.get_device("mitsubishi_heavy_industries", model),
        MitsubishiHeavy88Device,
    )


@pytest.mark.parametrize("model", MITSUBISHI_HEAVY88_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.mitsubishi_heavy_industries import Mitsubishi88

    legacy = LegacyDevice("mitsubishi_heavy_industries", model, Mitsubishi88)
    assert device(model).capabilities == legacy.capabilities


def _record(**state):
    return next(
        r
        for r in load_oracle("MITSUBISHI_HEAVY_88")
        if all(r["state"].get(k) == v for k, v in state.items())
    )


@pytest.mark.parametrize(
    "state, defect",
    [
        ({"mode": "cool", "fan": "lowest", "swing": "off"}, FAN_LOWEST),
        ({"mode": "cool", "fan": "highest", "swing": "off"}, FAN_HIGHEST),
        ({"mode": "cool", "fan": "low", "swing": "90°"}, SWING_1),
        ({"mode": "cool", "fan": "low", "swing": "60°"}, SWING_2),
    ],
)
def test_undeclared_deviation_is_reported(state, defect):
    dev = device()
    record = _record(**state)
    assert_matches_oracle(dev, record, dev.LAYOUTS, (defect,))
    others = tuple(d for d in DEFECTS if d is not defect)
    with pytest.raises(AssertionError, match=f"'{defect.field}'"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=others)


def test_layouts_must_cover_every_frame():
    dev = device()
    record = _record(mode="cool", fan="lowest", swing="off")
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_mitsubishi_heavy88_device.py -q`
Expected: collection error, `ImportError: cannot import name ...` from `pyhvac.plugins.mitsubishi_heavy_industries`.

- [ ] **Step 3: Implement**: insert immediately before `# Now the match between models and objects` in `pyhvac/plugins/mitsubishi_heavy_industries.py`:

```python
# ---------------------------------------------------- MitsubishiHeavy88
# Layout from IRremoteESP8266's Mitsubishi88Protocol (ir_MitsubishiHeavy.h):
# 11 bytes sent LSB first in one frame (sendMitsubishiHeavy88: sendGeneric
# with MSBfirst false). Bytes 0-4 are kMitsubishiHeavyZjsSig; from byte 3 on,
# every second byte is the complement of the one before it
# (IRMitsubishiHeavy88Ac::checksum, invertBytePairs from byte 3). stateReset
# zeroes bytes 5-10, so no bit is left to stale memory. The vertical and
# horizontal swing codes are split across the struct (SwingV5/SwingV7,
# SwingH1/SwingH2).

MITSUBISHI_HEAVY88 = Protocol(
    "mitsubishi-heavy88",
    {
        "main": Section(
            # kMitsubishiHeavyBitMark/ZeroSpace/OneSpace: a one is the short space
            PulseDistance(370, 1220, 420),
            header=(3140, 1630),  # kMitsubishiHeavyHdrMark/HdrSpace
            footer=(370,),
            gap=100000,  # kMitsubishiHeavyGap = kDefaultMessageGap
        ),
    },
    carrier=38000,  # sendMitsubishiHeavy88: 38 kHz
)


@dataclass(frozen=True)
class MitsubishiHeavy88SplitField(Field):
    """A field whose bits are scattered over the frame: raw bit k is frame
    bit ``spread[k]``, as the header's getters join the struct parts
    (getSwingVertical: SwingV5 | SwingV7 << 1; getSwingHorizontal:
    SwingH1 | SwingH2 << 2)."""

    spread: tuple = ()

    @classmethod
    def over(cls, *positions, **kw):
        """A field over the (byte, bit) ``positions``, lowest raw bit first."""
        bits = tuple(byte * 8 + bit for byte, bit in positions)
        return cls(bits[0], len(bits), spread=bits, **kw)

    @property
    def bits(self):
        return self.spread


MITSUBISHI_HEAVY88_MODE = {  # kMitsubishiHeavy{Auto,Cool,Dry,Heat}
    "auto": 0,
    "cool": 1,
    "dry": 2,
    "heat": 4,
}
MITSUBISHI_HEAVY88_FAN = {  # canonical fan -> kMitsubishiHeavy88Fan*, as convertFan
    "auto": 0,  # Auto: not in the entity; what C falls back to (see the device)
    "1": 7,  # lowest (kMin): Econo
    "2": 2,  # Low
    "3": 3,  # Med
    "4": 6,  # highest (kMax): Turbo
}
MITSUBISHI_HEAVY88_SWING_V = {  # canonical -> kMitsubishiHeavy88SwingV*
    "off": 0b000,
    "auto": 0b100,
    "1": 0b110,  # Highest
    "2": 0b001,  # High
    "3": 0b011,  # Middle
    "4": 0b101,  # Low
    "5": 0b111,  # Lowest
}
MITSUBISHI_HEAVY88_SWING_H = {  # canonical -> kMitsubishiHeavy88SwingH*
    "off": 0b0000,
    "auto": 0b1000,
    "1": 0b0001,  # LeftMax
    "2": 0b0101,  # Left
    "3": 0b1001,  # Middle
    "4": 0b1101,  # Right
    "5": 0b0010,  # RightMax
}
MITSUBISHI_HEAVY88_MIN_TEMP = 17  # kMitsubishiHeavyMinTemp

# Skeleton: IRMitsubishiHeavy88Ac::stateReset (signature, then zeroes) with
# the inverted bytes filled in.
MITSUBISHI_HEAVY88_LAYOUT = Layout(
    bytes.fromhex("ad513cd92600ff00ff00ff"),
    {
        "swing_v": MitsubishiHeavy88SplitField.over(
            (5, 1), (7, 3), (7, 4), values=MITSUBISHI_HEAVY88_SWING_V
        ),
        "swing_h": MitsubishiHeavy88SplitField.over(
            (5, 2), (5, 3), (5, 6), (5, 7), values=MITSUBISHI_HEAVY88_SWING_H
        ),
        "clean": Field.at(5, 5, 1),
        "fan": Field.at(7, 5, 3, values=MITSUBISHI_HEAVY88_FAN),
        "mode": Field.at(9, 0, 3, values=MITSUBISHI_HEAVY88_MODE),
        "power": Field.at(9, 3, 1),
        "temperature": Field.at(9, 4, 4),  # whole °C - kMitsubishiHeavyMinTemp
    },
    checksum=InvertedPairs(3, 11),
)


class MitsubishiHeavy88Device(Device):
    """Mitsubishi Heavy 88-bit (RKX502A001C): a full-state protocol with an
    explicit power bit and no toggles, so ``previous`` is ignored.

    Powerful and economy are fan codes (Turbo, Econo), not separate bits:
    as IRac::mitsubishiHeavy88 calls setFan, then setTurbo, then setEcono,
    powerful overrides the fan speed and economy overrides both.

    Fan lowest and highest send the documented Econo and Turbo codes that
    convertFan maps them to. The C path sends auto instead: IRac's
    setTurbo(false) / setEcono(false) reset a Turbo / Econo fan to auto.
    Vertical swing positions count down from the topmost documented one
    (Highest); the C path sends High for "90°" and Off for "60°"
    (kUpperMiddle has no case in convertSwingV).
    """

    PROTOCOL = MITSUBISHI_HEAVY88
    LAYOUTS = (MITSUBISHI_HEAVY88_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "heat"),
        temperature=TemperatureRange(17.0, 31.0),
        fan=Choice(
            ("1", "2", "3", "4"),
            {"1": "lowest", "2": "low", "3": "medium", "4": "highest"},
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
        swing_h=Choice(
            ("off", "auto", "1", "2", "3", "4", "5"),
            {
                "off": "off",
                "auto": "auto",
                "1": "far left",
                "2": "left",
                "3": "middle",
                "4": "right",
                "5": "far right",
            },
        ),
        features={
            "cleaning": Choice((False, True), {False: "off", True: "on"}),
            "powerful": Choice((False, True), {False: "off", True: "on"}),
            "economy": Choice((False, True), {False: "off", True: "on"}),
        },
    )

    def frames(self, previous, target, actions):
        # setTurbo(true) stores the Turbo fan code ("4"), then setEcono(true)
        # the Econo code ("1"), whatever the requested speed.
        fan = target.fan
        if target.features["powerful"]:
            fan = "4"
        if target.features["economy"]:
            fan = "1"
        data = MITSUBISHI_HEAVY88_LAYOUT.build(
            power=target.power,
            # As the C path: an off message carries mode auto (IRac passes
            # mode "off", which convertMode maps to kMitsubishiHeavyAuto).
            mode=target.mode if target.power else "auto",
            # setTemp clamps to 17-31 and stores the offset from 17.
            temperature=int(target.temperature) - MITSUBISHI_HEAVY88_MIN_TEMP,
            fan=fan,
            swing_v=target.swing_v,
            swing_h=target.swing_h,
            clean=target.features["cleaning"],
        )
        return [Frame("main", bytes(data))]


MITSUBISHI_HEAVY88_MODELS = ("RKX502A001C remote", "SRKxxZJ-S A/C", "generic 88")


DEVICES.update({m: MitsubishiHeavy88Device for m in MITSUBISHI_HEAVY88_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_mitsubishi_heavy88_device.py -q`
Expected: 247 passed, 3 skipped (the skips need the C extension).

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/mitsubishi_heavy_industries.py tests/test_mitsubishi_heavy88_device.py
git add pyhvac/plugins/mitsubishi_heavy_industries.py tests/test_mitsubishi_heavy88_device.py
git commit -m "MITSUBISHI_HEAVY_88: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 7: Whole-family verification

**Files:**
- Modify: `tests/test_mitsubishi_family.py`

- [ ] **Step 1: Add the family test**: append to `tests/test_mitsubishi_family.py`:

```python
@pytest.mark.parametrize("name", MODULES)
def test_no_mitsubishi_model_uses_the_c_library(name):
    from pyhvac import registry
    from pyhvac.legacy import LegacyDevice

    left = [
        m for m in registry.models(name) if isinstance(registry.get_device(name, m), LegacyDevice)
    ]
    assert left == []
```

- [ ] **Step 2: Run it**

Run: `python -m pytest tests/test_mitsubishi_family.py -q`
Expected: 4 passed.

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

Expected: 0 failed, and the capability-equality tests pass.

- [ ] **Step 4: Commit**

```bash
black tests/test_mitsubishi_family.py
git add tests/test_mitsubishi_family.py
git commit -m "Test that no Mitsubishi model is left on the C library

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
