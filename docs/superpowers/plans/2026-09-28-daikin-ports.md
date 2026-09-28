# Daikin Family Ports (Plan B) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the C path for every C-backed Daikin model with a pure-Python `Device`, built with the port kit: DAIKIN (ARC433), DAIKIN64, DAIKIN128, DAIKIN152, DAIKIN160, DAIKIN176, DAIKIN216 and DAIKIN312.

**Architecture:** One device class per protocol, appended to `pyhvac/plugins/daikin.py` after the DAIKIN2 block and registered through `DEVICES`. Each port was written from its `union Daikin*Protocol` in IRremoteESP8266's `ir_Daikin.h`, then verified two ways:
- against every oracle record, field by field, with only declared C defects allowed;
- against the real C path (`LegacyDevice`) on states the oracle grid lacks.

**Tech Stack:** Python ≥ 3.9 standard library, pytest, black. The port kit on branch `ports`: `pyhvac.fields`, `tools/portkit.py`, `tests/port_oracle.py`, and bitless IR sections.

**Spec:** `docs/superpowers/specs/2026-09-27-port-kit-design.md` ("Plan B" and "Port recipe and acceptance").

## Global Constraints

- Work on branch `ports`.
- Durations are integer µs, the carrier is in Hz, and temperatures are °C.
- Python ≥ 3.9, and no new runtime dependencies.
- Layouts come from the IRremoteESP8266 headers (facts). Nothing from the fork is copied into this repo.
- Ported capabilities equal the legacy entity (`LegacyDevice(...).capabilities`), pinned by a C-only test in each file.
- A difference from the C output is allowed only as a declared `Defect` with its cause. Everything else must match the C path.
- The old API and all existing tests stay green. Run `black` on every modified file.
- Tests: `python -m pytest -q`. The C-extension run uses a scratch copy, as in Task 10.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **Toggle protocols (DAIKIN64, DAIKIN128):** with `previous=None`, "off" sets no toggle bit, so the unit is not switched off. That is what the C path does from a fresh object. A caller with no persisted state cannot turn these units off. Tests in Tasks 3 and 4 pin both the `previous` rule and the `None` behaviour.
2. **Off messages carry a protocol-specific mode:** auto for most protocols, cool for DAIKIN64 and DAIKIN176 (their `convertMode` maps off that way). Each task has an off-in-every-mode test.
3. **Feature interplay follows IRac's setter order:** powerful cancels quiet; economy cancels powerful (DAIKIN, DAIKIN152). Tested per task.
4. **Swing positions follow the documented top-to-bottom order** (canonical "1" = topmost); DAIKIN160 users see two positions move. Tests in Task 6.
5. **Models of the old class not covered by `DEVICES`** would silently stay on the C path. Task 10 checks that no C-backed Daikin model remains.

## Rulings made while planning (deviations from the C path, all declared as `Defect`s)

- **Swing "on" never reaches C: a pyhvac bug, not IRremoteESP8266.** `IRGHVAC.trans_swing` and `trans_hswing` (`hvaclib.py`) have no `"on"` key. The lookup error is swallowed, so swing stays off.
  - The ports send the documented swing-on value. That affects every Daikin protocol with an `off/on` swing list: DAIKIN, DAIKIN64, DAIKIN128, DAIKIN152, DAIKIN176, DAIKIN216 and DAIKIN312.
  - The same bug hits about 40 C-backed classes in other families. It should be fixed on `main` for 0.1.8.
- **Documented swing positions (DAIKIN160, as DAIKIN2):** canonical position "1" is the topmost documented position. The C path sends High for highest, and Auto for the missing upper-middle.
- **Fan lowest/highest (DAIKIN64, DAIKIN128):** `convertFan` maps them to the documented Quiet/Turbo (Powerful) fan codes, but `IRac` immediately resets them to auto via `setQuiet(false)`/`setTurbo(false)`. The ports send the documented codes. DAIKIN128 keeps its header rule: quiet and powerful fall back to auto in mode auto, including in off messages.
- **DAIKIN128 mode dry:** `convertMode` returns `kDaikinDry` (0b010), which equals `kDaikin128Cool`, so the C path sends cool for dry. The port sends dry.
- **DAIKIN312 horizontal swing off:** `convertSwingH` has no off case (as in DAIKIN2), so the port sends `kDaikin312SwingHOff`.
- **DAIKIN2 `"Daikin2"` model key:** it was missing from `DEVICES` and silently stayed on the C path. Task 1 fixes it.

## Open questions for the reviewer (not blocking)

- **A `power_toggle` capability flag.** SmartIR must persist state for DAIKIN64/DAIKIN128 or it cannot reliably turn them off. A flag in `Capabilities` would let the integration know. This is proposed for the state-API follow-up and is not in this plan.
- **Kit follow-ups:**
  - `portkit timings` clusters header spaces with bit spaces (2140/2145 µs merged with 1780 µs).
  - `Layout` checksum positions are whole bytes: DAIKIN64 and DAIKIN128 need a nibble checksum in the top half of a byte shared with fields, so they define local `Checksum` subclasses with empty `positions()`.
  - `portkit checksum` does not search nibble checksums.

## File Structure

- Modify `pyhvac/plugins/daikin.py`: imports, `DAIKIN2_MODELS`, and one block per protocol before `class PluginObject(GenPluginObject):`, each followed by its `DEVICES.update(...)` line.
- Tests:
  - `tests/test_daikin_arc_device.py`
  - `tests/test_daikin64_device.py`
  - `tests/test_daikin128_device.py`
  - `tests/test_daikin152_device.py`
  - `tests/test_daikin160_device.py`
  - `tests/test_daikin176_device.py`
  - `tests/test_daikin216_device.py`
  - `tests/test_daikin312_device.py`

Every task inserts its block **immediately before** `class PluginObject(GenPluginObject):`, which keeps the blocks in task order.

---

### Task 1: Imports and the DAIKIN2 model gap

**Files:**
- Modify: `pyhvac/plugins/daikin.py` (imports; the DAIKIN2 `DEVICES` definition)
- Modify: `tests/test_daikin2_device.py`

- [ ] **Step 1: Write the failing test**: append to `tests/test_daikin2_device.py`:

```python
def test_every_daikin2_model_is_served_by_the_port():
    for model in ("ARC477A1 remote", "FTXZ25NV1B", "FTXZ35NV1B", "FTXZ50NV1B", "Daikin2"):
        assert isinstance(registry.get_device("daikin", model), Daikin2Device)
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `python -m pytest tests/test_daikin2_device.py -q -k every_daikin2_model`
Expected: FAIL: `"Daikin2"` resolves to a `LegacyDevice`.

- [ ] **Step 3: Implement**

In `pyhvac/plugins/daikin.py`:
- add `from dataclasses import dataclass` right after `import struct`;
- change `from ..fields import Field, Layout, Sum8` to `from ..fields import Checksum, Field, Layout, NibbleSum, Sum8`;
- replace

```python
DEVICES = {
    model: Daikin2Device
    for model in ("ARC477A1 remote", "FTXZ25NV1B", "FTXZ35NV1B", "FTXZ50NV1B")
}
```

with

```python
DAIKIN2_MODELS = ("ARC477A1 remote", "FTXZ25NV1B", "FTXZ35NV1B", "FTXZ50NV1B", "Daikin2")
DEVICES = {model: Daikin2Device for model in DAIKIN2_MODELS}
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/daikin.py tests/test_daikin2_device.py
git add pyhvac/plugins/daikin.py tests/test_daikin2_device.py
git commit -m "Daikin2: serve the 'Daikin2' model key; imports for the Daikin ports

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 2: DAIKIN (ARC433 family)

5-bit zero leader + frames of 8, 8 and 19 bytes; layout from `union DaikinESPProtocol`.

**Files:**
- Modify: `pyhvac/plugins/daikin.py` (new block before `class PluginObject(GenPluginObject):`)
- Test: `tests/test_daikin_arc_device.py`

**Interfaces:**
- Consumes: `Device`, the `pyhvac.fields` layouts and checksums, bitless sections, `tests/port_oracle.py` (`Defect`, `assert_matches_oracle`, `state_from_record`, `oracle_params`), and the oracle fixture `DAIKIN`.
- Produces: `DaikinArcDevice`, `DAIKIN_ARC_MODELS`, and the `DEVICES` entries for those models.

- [ ] **Step 1: Write the failing tests**: create `tests/test_daikin_arc_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.daikin import (
    DAIKIN_ARC_FIRST,
    DAIKIN_ARC_MODELS,
    DAIKIN_ARC_SECOND,
    DAIKIN_ARC_THIRD,
    DaikinArcDevice,
)
from pyhvac.state import HvacState

# The C path never sends swing: pyhvac's IRGHVAC.trans_swing/trans_hswing have
# no "on" key, so IRac keeps swingv/swingh at kOff and IRac::daikin calls
# setSwingVertical/Horizontal(false). The header documents
# kDaikinSwingOn = 0b1111 for SwingV/SwingH; the port sends it.
DEFECTS = (
    Defect("swing_v", "swing", "off", "C path drops swing 'on' (kDaikinSwingOn)"),
    Defect("swing_h", "swing", "off", "C path drops hswing 'on' (kDaikinSwingOn)"),
)


def device():
    return DaikinArcDevice("daikin", "ARC433 remote")


def third(state):
    dev = device()
    frames = dev.frames(None, dev.normalise(state), ())
    return DAIKIN_ARC_THIRD.read(frames[3].data)


@pytest.mark.parametrize("record", oracle_params("DAIKIN"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layouts_round_trip_every_oracle_state():
    dev = device()
    layouts = (DAIKIN_ARC_FIRST, DAIKIN_ARC_SECOND, DAIKIN_ARC_THIRD)
    for record in load_oracle("DAIKIN"):
        state = state_from_record(dev, record["state"])
        leader, *mains = dev.frames(None, state, ())
        assert (leader.data, leader.nbits) == (b"\x00", 5)
        for layout, frame in zip(layouts, mains):
            values = layout.read(frame.data)
            assert layout.build(**values) == bytearray(frame.data)


def test_half_degree_setpoints_are_sent():
    assert third(HvacState(True, "cool", 24.5))["half_degrees"] == 49


@pytest.mark.parametrize("mode", ["auto", "dry", "cool", "heat", "fan"])
@pytest.mark.parametrize("temperature", [10.0, 32.0])
def test_off_frame_carries_mode_auto_in_every_mode(mode, temperature):
    # The C path sends mode "off", which convertMode turns into auto; the
    # setpoint is kept as given.
    read = third(HvacState(False, mode, temperature))
    assert (read["power"], read["mode"], read["half_degrees"]) == (
        0,
        "auto",
        int(temperature * 2),
    )


def test_powerful_cancels_quiet():
    read = third(
        HvacState(True, "cool", 24.0, features={"quiet": True, "powerful": True})
    )
    assert (read["powerful"], read["quiet"]) == (1, 0)


def test_economy_cancels_powerful():
    read = third(
        HvacState(True, "cool", 24.0, features={"economy": True, "powerful": True})
    )
    assert (read["powerful"], read["economy"]) == (0, 1)


def test_quiet_and_economy_coexist():
    read = third(
        HvacState(True, "cool", 24.0, features={"economy": True, "quiet": True})
    )
    assert (read["quiet"], read["economy"]) == (1, 1)


def test_all_three_leave_economy_only():
    feats = {"economy": True, "powerful": True, "quiet": True}
    read = third(HvacState(True, "cool", 24.0, features=feats))
    assert (read["quiet"], read["powerful"], read["economy"]) == (0, 0, 1)


def test_swing_sends_the_documented_value():
    dev = device()
    state = dev.normalise(
        HvacState(True, "cool", 24.0, swing_v="swing", swing_h="swing")
    )
    data = dev.frames(None, state, ())[3].data
    assert data[8] & 0x0F == 0xF and data[9] & 0x0F == 0xF


def test_registry_serves_the_port():
    for model in DAIKIN_ARC_MODELS:
        assert isinstance(registry.get_device("daikin", model), DaikinArcDevice)


def test_capabilities_match_the_legacy_entity():
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.daikin import Daikin

    for model in DAIKIN_ARC_MODELS:
        legacy = LegacyDevice("daikin", model, Daikin)
        assert DaikinArcDevice("daikin", model).capabilities == legacy.capabilities


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(r for r in load_oracle("DAIKIN") if r["state"].get("swing") == "on")
    with pytest.raises(AssertionError, match="swing_v"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("DAIKIN")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:3], DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_daikin_arc_device.py -q`
Expected: collection error, `ImportError: cannot import name ...` from `pyhvac.plugins.daikin`.

- [ ] **Step 3: Implement**: insert immediately before `class PluginObject(GenPluginObject):` in `pyhvac/plugins/daikin.py`:

```python
# --------------------------------------------------------------- Daikin (ARC433)
# Layout from IRremoteESP8266's DaikinESPProtocol (ir_Daikin.h): 35 bytes in
# three sections of 8, 8 and 19, each closed by a sum-of-bytes checksum
# (kDaikinByteChecksum1/2, Sum3); frame byte n of the third section is
# struct byte n + 16. The message opens with a headerless 5-bit all-zero
# leader (kDaikinHeaderLength). Every space after a footer mark is
# kDaikinZeroSpace + kDaikinGap.

DAIKIN_ARC = Protocol(
    "daikin",
    {
        "leader": Section(PulseDistance(428, 428, 1280), footer=(428,), gap=29428),
        "main": Section(
            PulseDistance(428, 428, 1280),
            header=(3650, 1623),
            footer=(428,),
            gap=29428,
        ),
    },
    carrier=38000,
)

DAIKIN_ARC_SWING = {"off": 0x0, "swing": 0xF}  # kDaikinSwingOff / kDaikinSwingOn

# The first two sections carry nothing the C path drives (Comfort, and the
# clock that IRac never sets): they are sent as the header's reset state.
DAIKIN_ARC_FIRST = Layout(bytes.fromhex("11da2700c5000000"), {}, checksum=Sum8(0, 7, 7))
DAIKIN_ARC_SECOND = Layout(
    bytes.fromhex("11da270042000000"), {}, checksum=Sum8(0, 7, 7)
)
DAIKIN_ARC_THIRD = Layout(
    # Hardwired: byte 5 bit 3 (always 1), timers unused (kDaikinUnusedTime
    # in bytes 10-12), byte 15 = 0xC0.
    bytes.fromhex("11da27000008000000000006600000c0000000"),
    {
        "power": Field.at(5, 0, 1),
        "mode": Field.at(
            5, 4, 3, values={"auto": 0, "dry": 2, "cool": 3, "heat": 4, "fan": 6}
        ),
        "half_degrees": Field.at(6, 0, 8),  # Temp: °C × 2
        "swing_v": Field.at(8, 0, 4, values=DAIKIN_ARC_SWING),
        "fan": Field.at(8, 4, 4, values={"auto": 0xA, "1": 3, "2": 5, "3": 6}),
        "swing_h": Field.at(9, 0, 4, values=DAIKIN_ARC_SWING),
        "powerful": Field.at(13, 0, 1),
        "quiet": Field.at(13, 5, 1),
        "economy": Field.at(16, 2, 1),
        "mold": Field.at(17, 1, 1),
    },
    checksum=Sum8(0, 18, 18),
)


class DaikinArcDevice(Device):
    """Daikin (ARC433 and others): a full-state protocol, ``previous`` is
    ignored."""

    PROTOCOL = DAIKIN_ARC
    LAYOUTS = (None, DAIKIN_ARC_FIRST, DAIKIN_ARC_SECOND, DAIKIN_ARC_THIRD)
    capabilities = Capabilities(
        modes=("auto", "dry", "cool", "heat", "fan"),
        temperature=TemperatureRange(10.0, 32.0, (0, 5)),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
        ),
        swing_v=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
        swing_h=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
        features={
            name: Choice((False, True), {False: "off", True: "on"})
            for name in ("economy", "powerful", "quiet", "cleaning")
        },
    )

    def frames(self, previous, target, actions):
        feat = target.features
        third = DAIKIN_ARC_THIRD.build(
            power=target.power,
            # As the C path: an off message carries mode auto (IRac passes
            # mode "off", which convertMode maps to auto).
            mode=target.mode if target.power else "auto",
            half_degrees=int(target.temperature * 2),
            swing_v=target.swing_v,
            fan=target.fan,
            swing_h=target.swing_h,
            # As IRDaikinESP's setters, called in IRac's order (quiet,
            # powerful, econo): powerful cancels quiet, econo cancels powerful.
            quiet=feat["quiet"] and not feat["powerful"],
            powerful=feat["powerful"] and not feat["economy"],
            economy=feat["economy"],
            mold=feat["cleaning"],
        )
        return [
            Frame("leader", b"\x00", 5),
            Frame("main", bytes(DAIKIN_ARC_FIRST.build())),
            Frame("main", bytes(DAIKIN_ARC_SECOND.build())),
            Frame("main", bytes(third)),
        ]


DAIKIN_ARC_MODELS = (
    "ARC433 remote",
    "M Series",
    "FTXM-M",
    "ARC466A12 remote",
    "ARC466A33 remote",
    "Daikin",
)


DEVICES.update({m: DaikinArcDevice for m in DAIKIN_ARC_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_daikin_arc_device.py -q`
Expected: 169 passed, 1 skipped (the skip(s) need the C extension).

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/daikin.py tests/test_daikin_arc_device.py
git add pyhvac/plugins/daikin.py tests/test_daikin_arc_device.py
git commit -m "DAIKIN (ARC433 family): pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 3: DAIKIN64

Double 9800 µs preamble, one 64-bit frame, trailing 4600 µs mark (bitless). Nibble checksum in the top half of byte 7 (local `Checksum` subclass). Power is a TOGGLE bit: uses `previous` (toggle when power changes); with `previous=None` the bit follows `target.power` like a fresh C object.

**Files:**
- Modify: `pyhvac/plugins/daikin.py` (new block before `class PluginObject(GenPluginObject):`)
- Test: `tests/test_daikin64_device.py`

**Interfaces:**
- Consumes: `Device`, the `pyhvac.fields` layouts and checksums, bitless sections, `tests/port_oracle.py` (`Defect`, `assert_matches_oracle`, `state_from_record`, `oracle_params`), and the oracle fixture `DAIKIN64`.
- Produces: `Daikin64Device`, `DAIKIN64_MODELS`, and the `DEVICES` entries for those models.

- [ ] **Step 1: Write the failing tests**: create `tests/test_daikin64_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.daikin import (
    DAIKIN64_LAYOUT,
    DAIKIN64_MODELS,
    Daikin64Checksum,
    Daikin64Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Daikin64 values here:
# - IRac::daikin64 calls setFan(convertFan(fan)) and then setTurbo(turbo) and
#   setQuiet(quiet) with both false, which reset kDaikin64FanTurbo (kMax) and
#   kDaikin64FanQuiet (kMin) to kDaikin64FanAuto;
# - the legacy glue (IRGHVAC.trans_swing) has no "on" key, so swingv stays
#   kOff and IRDaikin64::setSwingVertical never sets the SwingV bit.
DEFECTS = (
    Defect("fan", "1", "auto", "C resets kDaikin64FanQuiet to auto"),
    Defect("fan", "5", "auto", "C resets kDaikin64FanTurbo to auto"),
    Defect("swing_v", "swing", "off", "legacy glue never passes swing on"),
)


def device():
    return Daikin64Device("daikin", "DGS01 remote")


def read(state, previous=None):
    _, main, _ = device().frames(previous, state, ())
    return DAIKIN64_LAYOUT.read(main.data)


@pytest.mark.parametrize("record", oracle_params("DAIKIN64"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("DAIKIN64"):
        state = state_from_record(dev, record["state"])
        _, main, _ = dev.frames(None, state, ())
        values = DAIKIN64_LAYOUT.read(main.data)
        assert DAIKIN64_LAYOUT.build(**values) == bytearray(main.data)


def test_checksum_is_the_nibble_sum_of_the_known_good_state():
    # kDaikin64KnownGoodState = 0x7C16161607204216, sent LSB first.
    data = bytearray((0x7C16161607204216).to_bytes(8, "little"))
    assert Daikin64Checksum().check(data)
    data[7] &= 0x0F
    Daikin64Checksum().apply(data)
    assert data[7] == 0x7C


def test_temperature_is_bcd():
    dev = device()
    _, main, _ = dev.frames(None, dev.normalise(HvacState(True, "cool", 23.0)), ())
    assert main.data[6] == 0x23


def test_off_carries_mode_cool_in_every_mode():
    # IRac passes mode "off"; IRDaikin64::convertMode maps it to cool.
    dev = device()
    for mode in dev.capabilities.modes:
        for t in (16.0, 30.0):
            values = read(dev.normalise(HvacState(False, mode, t)))
            assert (values["mode"], values["temperature"]) == ("cool", int(t))


def test_power_bit_without_previous_is_the_target_power():
    # A fresh IRac has no previous state for DAIKIN64: Power = on.
    dev = device()
    assert read(dev.normalise(HvacState(True, "heat", 20.0)))["power"] == 1
    assert read(dev.normalise(HvacState(False, "heat", 20.0)))["power"] == 0


@pytest.mark.parametrize(
    "before, after, toggle",
    [(True, True, 0), (True, False, 1), (False, False, 0), (False, True, 1)],
)
def test_power_bit_with_previous_toggles_on_change(before, after, toggle):
    # IRac::handleToggles: result.power = desired.power ^ prev->power.
    dev = device()
    previous = dev.normalise(HvacState(before, "cool", 22.0))
    target = dev.normalise(HvacState(after, "cool", 22.0))
    assert read(target, previous)["power"] == toggle


def test_encode_passes_previous_to_the_toggle():
    dev = device()
    on = HvacState(True, "cool", 22.0)
    fresh = dev.encode(None, on).signal
    again = dev.encode(on, on).signal
    assert fresh != again


@pytest.mark.parametrize(
    "fan, raw", [("auto", 1), ("1", 9), ("2", 8), ("3", 4), ("4", 2), ("5", 3)]
)
def test_every_fan_level_uses_its_documented_value(fan, raw):
    dev = device()
    _, main, _ = dev.frames(
        None, dev.normalise(HvacState(True, "cool", 22.0, fan=fan)), ()
    )
    assert DAIKIN64_LAYOUT.read_raw(main.data, "fan") == raw


def test_swing_sets_the_swing_bit():
    dev = device()
    swing = dev.normalise(HvacState(True, "cool", 22.0, swing_v="swing"))
    still = dev.normalise(HvacState(True, "cool", 22.0))
    assert (read(swing)["swing_v"], read(still)["swing_v"]) == ("swing", "off")


def test_message_shape():
    dev = device()
    pulses = dev.encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:5] == (9800, 9800, 9800, 9800, 4600)
    assert pulses[-2:] == (4600, 100000)
    assert len(pulses) == 4 + 2 + 2 * 64 + 2 + 2


@pytest.mark.parametrize("model", DAIKIN64_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("daikin", model), Daikin64Device)


@pytest.mark.parametrize("model", DAIKIN64_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.daikin import Daikin64

    legacy = LegacyDevice("daikin", model, Daikin64)
    assert Daikin64Device("daikin", model).capabilities == legacy.capabilities


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(r for r in load_oracle("DAIKIN64") if r["state"]["swing"] == "on")
    with pytest.raises(AssertionError, match="swing_v"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("DAIKIN64")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:2], DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_daikin64_device.py -q`
Expected: collection error, `ImportError: cannot import name ...` from `pyhvac.plugins.daikin`.

- [ ] **Step 3: Implement**: insert immediately before `class PluginObject(GenPluginObject):` in `pyhvac/plugins/daikin.py`:

```python
# -------------------------------------------------------------- Daikin64
# Layout from IRremoteESP8266's Daikin64Protocol (ir_Daikin.h): one 64-bit
# word sent LSB first, i.e. 8 bytes in order, each LSB first. The message is
# a bitless leader (two kDaikin64LdrMark/LdrSpace pairs), the frame, then a
# bare kDaikin64HdrMark followed by kDefaultMessageGap (sendDaikin64).

DAIKIN64 = Protocol(
    "daikin64",
    {
        "leader": Section(None, header=(9800, 9800, 9800, 9800)),
        "main": Section(
            PulseDistance(350, 382, 954),
            header=(4600, 2500),
            footer=(350,),
            gap=20300,
        ),
        "trailer": Section(None, header=(4600,), gap=100000),
    },
)


class Daikin64Checksum:
    """kDaikin64ChecksumOffset/Size: the sum of the 15 nibbles below bit 60,
    mod 16, stored in bits 60-63 (the top nibble of byte 7)."""

    def positions(self):
        # A nibble, not a byte: byte 7's low nibble holds fields, so Layout's
        # byte-level overlap check cannot apply. No field uses bits 60-63.
        return set()

    def compute(self, data):
        total = sum((b >> 4) + (b & 0x0F) for b in data[:7]) + (data[7] & 0x0F)
        return total & 0x0F

    def apply(self, data):
        data[7] = (data[7] & 0x0F) | self.compute(data) << 4

    def check(self, data):
        return data[7] >> 4 == self.compute(data)


# Skeleton from kDaikin64KnownGoodState with the written fields and the sum
# cleared: byte 0 is 0x16, the clock (07:20, BCD) and both timers (22 h,
# disabled) are never set by the C path, and byte 7 bit 2 is always set.
DAIKIN64_LAYOUT = Layout(
    bytes.fromhex("1600200716160004"),
    {
        "mode": Field.at(1, 0, 4, values={"dry": 1, "cool": 2, "fan": 4, "heat": 8}),
        "fan": Field.at(  # kDaikin64Fan*
            1,
            4,
            4,
            values={
                "auto": 0b0001,
                "1": 0b1001,  # quiet
                "2": 0b1000,  # low
                "3": 0b0100,  # medium
                "4": 0b0010,  # high
                "5": 0b0011,  # turbo
            },
        ),
        "temperature": Field.at(  # whole °C, BCD
            6, 0, 8, values={t: int(str(t), 16) for t in range(16, 31)}
        ),
        "swing_v": Field.at(7, 0, 1, values={"off": 0, "swing": 1}),
        "power": Field.at(7, 3, 1),  # a toggle
    },
    checksum=Daikin64Checksum(),
)


class Daikin64Device(Device):
    """Daikin64 (DGS01): full state, except that the power bit is a toggle.

    With ``previous`` the bit is set when the power changes, as IRac's
    handleToggles does. Without it the bit is ``target.power``, as the C path
    sends from a fresh IRac: an "on" toggles, an "off" toggles nothing.
    """

    PROTOCOL = DAIKIN64
    LAYOUTS = (None, DAIKIN64_LAYOUT, None)
    capabilities = Capabilities(
        modes=("dry", "cool", "heat", "fan"),
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
        swing_v=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
    )

    def frames(self, previous, target, actions):
        if previous is None:
            toggle = target.power
        else:
            toggle = target.power != previous.power
        data = DAIKIN64_LAYOUT.build(
            # As the C path: an off message carries mode cool (IRac passes
            # mode "off", which convertMode maps to cool).
            mode=target.mode if target.power else "cool",
            fan=target.fan,
            temperature=int(target.temperature),
            swing_v=target.swing_v,
            power=toggle,
        )
        return [
            Frame("leader", b""),
            Frame("main", bytes(data)),
            Frame("trailer", b""),
        ]


DAIKIN64_MODELS = ("FFN-C/FCN-F Series", "DGS01 remote", "FTWX35AXV1", "Daikin64")


DEVICES.update({m: Daikin64Device for m in DAIKIN64_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_daikin64_device.py -q`
Expected: 204 passed, 4 skipped (the skip(s) need the C extension).

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/daikin.py tests/test_daikin64_device.py
git add pyhvac/plugins/daikin.py tests/test_daikin64_device.py
git commit -m "DAIKIN64: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 4: DAIKIN128

Double 9800 µs preamble, headed 64-bit frame, headerless 64-bit frame closed by a 4600 µs mark. BCD fields; nibble checksums (local `Daikin128FirstSum` + `NibbleSum`). Power TOGGLE bit, handled as DAIKIN64.

**Files:**
- Modify: `pyhvac/plugins/daikin.py` (new block before `class PluginObject(GenPluginObject):`)
- Test: `tests/test_daikin128_device.py`

**Interfaces:**
- Consumes: `Device`, the `pyhvac.fields` layouts and checksums, bitless sections, `tests/port_oracle.py` (`Defect`, `assert_matches_oracle`, `state_from_record`, `oracle_params`), and the oracle fixture `DAIKIN128`.
- Produces: `Daikin128Device`, `DAIKIN128_MODELS`, and the `DEVICES` entries for those models.

- [ ] **Step 1: Write the failing tests**: create `tests/test_daikin128_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.daikin import (
    DAIKIN128_FIRST,
    DAIKIN128_MODELS,
    DAIKIN128_SECOND,
    Daikin128Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Daikin128 values here:
# IRDaikin128::convertMode returns kDaikinDry (0b010, the DAIKIN protocol's
# dry), which is kDaikin128Cool; the header documents kDaikin128Dry = 0b0001.
# pyhvac's IRGHVAC.trans_swing has no "on" key, so IRac never receives a
# vertical swing and SwingV (documented 1-bit field) is always 0.
# IRDaikin128::convertFan maps kMin to quiet (with DAIKIN's kDaikinFanQuiet,
# 0b1011, not kDaikin128FanQuiet) and kMax to kDaikin128FanPowerful, then
# IRac::daikin128 cancels both with setQuiet(false)/setPowerful(false), as
# the old model has no quiet/powerful feature: lowest and highest send auto.
MODE_DRY = Defect("mode", "dry", "cool", "convertMode sends kDaikinDry (= cool)")
SWING = Defect("swing_v", "swing", "off", "trans_swing drops 'on': SwingV stays 0")
FAN_LOWEST = Defect("fan", "1", "auto", "convertFan + IRac cancel quiet: auto")
FAN_HIGHEST = Defect("fan", "5", "auto", "convertFan + IRac cancel powerful: auto")
DEFECTS = (MODE_DRY, SWING, FAN_LOWEST, FAN_HIGHEST)


def device():
    return Daikin128Device("daikin", "BRC52B63 remote")


def on(mode="cool", temperature=24.0, **kw):
    return device().normalise(HvacState(True, mode, temperature, **kw))


def off(mode="cool", temperature=24.0, **kw):
    return device().normalise(HvacState(False, mode, temperature, **kw))


@pytest.mark.parametrize("record", oracle_params("DAIKIN128"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layouts_round_trip_every_oracle_state():
    dev = device()
    for record in load_oracle("DAIKIN128"):
        state = state_from_record(dev, record["state"])
        _, first, second = dev.frames(None, state, ())
        for layout, frame in ((DAIKIN128_FIRST, first), (DAIKIN128_SECOND, second)):
            values = layout.read(frame.data)
            assert layout.build(**values) == bytearray(frame.data)


def test_first_checksum_is_the_top_nibble_of_byte_7():
    # A C frame from the oracle: 16 1a 00 00 00 00 23 b4 (auto, 23 °C, off).
    data = bytearray.fromhex("161a0000000023b4")
    assert DAIKIN128_FIRST.checksum.check(data)
    data[7] &= 0x0F
    DAIKIN128_FIRST.checksum.apply(data)
    assert data.hex() == "161a0000000023b4"


def test_first_checksum_nibble_is_free_of_fields():
    bits = {b for f in DAIKIN128_FIRST.fields.values() for b in f.bits}
    assert not bits & set(range(60, 64))


def test_temperature_is_bcd():
    _, first, _ = device().frames(None, on(temperature=23.0), ())
    assert first.data[6] == 0x23


def test_power_toggle_without_previous_follows_the_c_path():
    dev = device()
    _, first_on, _ = dev.frames(None, on(), ())
    _, first_off, _ = dev.frames(None, off(), ())
    assert DAIKIN128_FIRST.read(first_on.data)["power"] == 1
    assert DAIKIN128_FIRST.read(first_off.data)["power"] == 0


@pytest.mark.parametrize(
    "was, now, toggle",
    [(False, True, 1), (True, False, 1), (True, True, 0), (False, False, 0)],
)
def test_power_toggles_only_when_power_changes(was, now, toggle):
    dev = device()
    previous = on() if was else off()
    target = on(temperature=20.0) if now else off(temperature=20.0)
    _, first, _ = dev.frames(previous, target, ())
    assert DAIKIN128_FIRST.read(first.data)["power"] == toggle


def test_encode_uses_previous_for_the_toggle():
    dev = device()
    a = dev.encode(on(), on(temperature=20.0)).signal
    b = dev.encode(None, on(temperature=20.0)).signal
    assert a != b


@pytest.mark.parametrize("mode", ["auto", "dry", "cool", "heat", "fan"])
def test_off_frame_carries_mode_auto_in_every_mode(mode):
    _, first, _ = device().frames(None, off(mode, 18.0), ())
    read = DAIKIN128_FIRST.read(first.data)
    assert (read["mode"], read["temperature"], read["power"]) == ("auto", 18, 0)


@pytest.mark.parametrize("mode", ["dry", "cool", "heat", "fan"])
@pytest.mark.parametrize("fan, code", [("1", 0b1001), ("5", 0b0011)])
def test_extreme_fan_levels_send_quiet_and_powerful(mode, fan, code):
    # kDaikin128FanQuiet / kDaikin128FanPowerful, the documented codes
    _, first, _ = device().frames(None, on(mode, fan=fan), ())
    assert DAIKIN128_FIRST.read_raw(first.data, "fan") == code


@pytest.mark.parametrize("fan", ["1", "5"])
def test_extreme_fan_levels_send_auto_in_auto_and_off(fan):
    # setFan: quiet and powerful fall back to auto in mode auto (and an off
    # message carries mode auto)
    dev = device()
    for state in (on("auto", fan=fan), off("cool", fan=fan)):
        _, first, _ = dev.frames(None, state, ())
        assert DAIKIN128_FIRST.read(first.data)["fan"] == "auto"


@pytest.mark.parametrize("mode", ["auto", "dry", "cool", "heat", "fan"])
def test_economy_only_in_cool_and_heat(mode):
    _, _, second = device().frames(None, on(mode, features={"economy": True}), ())
    expected = int(mode in ("cool", "heat"))
    assert DAIKIN128_SECOND.read(second.data)["economy"] == expected


def test_economy_is_cleared_when_off():
    _, _, second = device().frames(None, off("cool", features={"economy": True}), ())
    assert DAIKIN128_SECOND.read(second.data)["economy"] == 0


def test_registry_serves_the_port():
    for model in DAIKIN128_MODELS:
        assert isinstance(registry.get_device("daikin", model), Daikin128Device)


def test_capabilities_match_the_legacy_entity():
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.daikin import Daikin128

    for model in DAIKIN128_MODELS:
        legacy = LegacyDevice("daikin", model, Daikin128)
        assert device().capabilities == legacy.capabilities


def _without(defect):
    return tuple(d for d in DEFECTS if d is not defect)


@pytest.mark.parametrize(
    "defect, pick",
    [
        (SWING, lambda s: s.get("swing") == "on" and s["fan"] == "auto"),
        (MODE_DRY, lambda s: s["mode"] == "dry" and s.get("swing") == "off"),
        (FAN_LOWEST, lambda s: s["mode"] == "cool" and s.get("fan") == "lowest"),
        (FAN_HIGHEST, lambda s: s["mode"] == "cool" and s.get("fan") == "highest"),
    ],
)
def test_undeclared_deviation_is_reported(defect, pick):
    dev = device()
    record = next(r for r in load_oracle("DAIKIN128") if pick(r["state"]))
    with pytest.raises(AssertionError, match=defect.field):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=_without(defect))


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("DAIKIN128")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:2], DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_daikin128_device.py -q`
Expected: collection error, `ImportError: cannot import name ...` from `pyhvac.plugins.daikin`.

- [ ] **Step 3: Implement**: insert immediately before `class PluginObject(GenPluginObject):` in `pyhvac/plugins/daikin.py`:

```python
# --------------------------------------------------------------- Daikin128
# Layout from IRremoteESP8266's Daikin128Protocol (ir_Daikin.h): 16 bytes
# sent as two headerless-joined sections of 8 (kDaikin128SectionLength);
# frame byte n of the second section is struct byte n + 8. The first
# section's checksum is the top nibble of its last byte, the second's is a
# nibble sum in its last byte (IRDaikin128::calcFirst/SecondChecksum).

DAIKIN128 = Protocol(
    "daikin128",
    {
        # kDaikin128LeaderMark/Space, sent twice
        "preamble": Section(None, header=(9800, 9800, 9800, 9800)),
        "first": Section(
            PulseDistance(350, 382, 954),
            header=(4600, 2500),
            footer=(350,),
            gap=20300,
        ),
        # No header: the bits follow the first section's gap directly, and
        # the section closes on kDaikin128FooterMark (= kDaikin128HdrMark).
        "second": Section(PulseDistance(350, 382, 954), footer=(4600,), gap=20300),
    },
    carrier=38000,  # kDaikin128Freq
)


@dataclass(frozen=True)
class Daikin128FirstSum(Checksum):
    """Daikin128's first checksum: the nibbles of data[start:end] plus the low
    nibble of data[at], mod 16, written in the top nibble of data[at].

    It shares its byte with data fields (the low nibble), so ``positions`` is
    empty: Layout checks overlaps per byte. DAIKIN128_FIRST keeps bits 60-63
    free of fields (tested).
    """

    def compute(self, data):
        nibbles = sum((b >> 4) + (b & 0x0F) for b in self._input(data))
        return (nibbles + (data[self.at] & 0x0F)) & 0x0F

    def positions(self):
        return set()

    def apply(self, data):
        data[self.at] = (data[self.at] & 0x0F) | self.compute(data) << 4

    def check(self, data):
        return data[self.at] >> 4 == self.compute(data)


def _bcd(n):
    return (n // 10) << 4 | n % 10


DAIKIN128_MODE = {  # kDaikin128*
    "dry": 0b0001,
    "cool": 0b0010,
    "fan": 0b0100,
    "heat": 0b1000,
    "auto": 0b1010,
}
DAIKIN128_FAN = {  # canonical fan -> kDaikin128Fan*
    "auto": 0b0001,  # kDaikin128FanAuto
    "1": 0b1001,  # lowest: kDaikin128FanQuiet
    "2": 0b1000,  # kDaikin128FanLow
    "3": 0b0100,  # kDaikin128FanMed
    "4": 0b0010,  # kDaikin128FanHigh
    "5": 0b0011,  # highest: kDaikin128FanPowerful
}
# kDaikin128MinTemp..kDaikin128MaxTemp, BCD (setTemp: uint8ToBcd)
DAIKIN128_TEMPERATURE = {t: _bcd(t) for t in range(16, 31)}

DAIKIN128_FIRST = Layout(
    bytes.fromhex("1600000000000004"),  # byte 7 bit 2: always 1
    {
        "mode": Field.at(1, 0, 4, values=DAIKIN128_MODE),
        "fan": Field.at(1, 4, 4, values=DAIKIN128_FAN),
        "clock_mins": Field.at(2, 0, 8),  # BCD
        "clock_hours": Field.at(3, 0, 8),  # BCD
        "on_hours": Field.at(4, 0, 6),  # BCD
        "on_half_hour": Field.at(4, 6, 1),
        "on_timer": Field.at(4, 7, 1),
        "off_hours": Field.at(5, 0, 6),  # BCD
        "off_half_hour": Field.at(5, 6, 1),
        "off_timer": Field.at(5, 7, 1),
        "temperature": Field.at(6, 0, 8, values=DAIKIN128_TEMPERATURE),
        "swing_v": Field.at(7, 0, 1, values={"off": 0, "swing": 1}),
        "sleep": Field.at(7, 1, 1),
        "power": Field.at(7, 3, 1),  # a toggle, not a state
    },
    checksum=Daikin128FirstSum(0, 7, 7),
)
DAIKIN128_SECOND = Layout(
    bytes.fromhex("a100000000000000"),
    {
        "ceiling": Field.at(1, 0, 1),  # light toggle, ceiling unit
        "economy": Field.at(1, 2, 1),
        "wall": Field.at(1, 3, 1),  # light toggle, wall unit
    },
    checksum=NibbleSum(0, 7, 7),
)


class Daikin128Device(Device):
    """Daikin128 (BRC52B63): full state, but power is a toggle bit.

    The power bit asks the unit to flip its power, so it is set only when
    the power changes: ``previous.power != target.power``. With no previous
    state it is set for "on" and clear for "off", as IRac sends from a fresh
    object (no previous state to toggle against).
    """

    PROTOCOL = DAIKIN128
    LAYOUTS = (None, DAIKIN128_FIRST, DAIKIN128_SECOND)
    capabilities = Capabilities(
        modes=("auto", "dry", "cool", "heat", "fan"),
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
        swing_v=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
        features={"economy": Choice((False, True), {False: "off", True: "on"})},
    )

    def frames(self, previous, target, actions):
        if previous is None:
            toggle = target.power
        else:
            toggle = previous.power != target.power
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to auto).
        mode = target.mode if target.power else "auto"
        fan = target.fan
        if mode == "auto" and fan in ("1", "5"):
            fan = "auto"  # setFan: no quiet or powerful in auto
        first = DAIKIN128_FIRST.build(
            mode=mode,
            fan=fan,
            temperature=target.temperature,
            swing_v=target.swing_v,
            power=toggle,
        )
        second = DAIKIN128_SECOND.build(
            # setEcono: only in cool and heat
            economy=target.features["economy"]
            and mode in ("cool", "heat"),
        )
        return [
            Frame("preamble", b""),
            Frame("first", bytes(first)),
            Frame("second", bytes(second)),
        ]


DAIKIN128_MODELS = (
    "17 Series FTXB09AXVJU",
    "17 Series FTXB12AXVJU",
    "17 Series FTXB24AXVJU",
    "BRC52B63 remote",
    "Daikin128",
)


DEVICES.update({m: Daikin128Device for m in DAIKIN128_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_daikin128_device.py -q`
Expected: 237 passed, 1 skipped (the skip(s) need the C extension).

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/daikin.py tests/test_daikin128_device.py
git add pyhvac/plugins/daikin.py tests/test_daikin128_device.py
git commit -m "DAIKIN128: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 5: DAIKIN152

5-bit zero leader + one 19-byte frame; layout from `union Daikin152Protocol`.

**Files:**
- Modify: `pyhvac/plugins/daikin.py` (new block before `class PluginObject(GenPluginObject):`)
- Test: `tests/test_daikin152_device.py`

**Interfaces:**
- Consumes: `Device`, the `pyhvac.fields` layouts and checksums, bitless sections, `tests/port_oracle.py` (`Defect`, `assert_matches_oracle`, `state_from_record`, `oracle_params`), and the oracle fixture `DAIKIN152`.
- Produces: `Daikin152Device`, `DAIKIN152_MODELS`, and the `DEVICES` entries for those models.

- [ ] **Step 1: Write the failing tests**: create `tests/test_daikin152_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.daikin import DAIKIN152_MAIN, Daikin152Device
from pyhvac.state import HvacState

# The C path never sends vertical swing: IRGHVAC.trans_swing has no entry for
# the old "on" value, so IRac's swingv stays kOff and IRac::daikin152 calls
# setSwingV(false). The header documents kDaikinSwingOn (0xF) for it.
DEFECTS = (Defect("swing_v", "swing", "off", "C never sets kDaikinSwingOn"),)


def device():
    return Daikin152Device("daikin", "ARC480A5 remote")


@pytest.mark.parametrize("record", oracle_params("DAIKIN152"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("DAIKIN152"):
        state = state_from_record(dev, record["state"])
        _, main = dev.frames(None, state, ())
        values = DAIKIN152_MAIN.read(main.data)
        assert DAIKIN152_MAIN.build(**values) == bytearray(main.data)


def test_leader_is_five_zero_bits():
    dev = device()
    leader, _ = dev.frames(None, dev.normalise(HvacState(True, "cool", 24.0)), ())
    assert (leader.section, leader.data, leader.nbits) == ("leader", b"\x00", 5)
    assert dev.LAYOUTS[0] is None


def _read(state):
    dev = device()
    _, main = dev.frames(None, dev.normalise(state), ())
    return DAIKIN152_MAIN.read(main.data)


@pytest.mark.parametrize("mode", ["auto", "dry", "cool", "fan"])
def test_setpoint_floor_is_18_outside_heat(mode):
    assert _read(HvacState(True, mode, 10.0))["temperature"] == 18


def test_heat_setpoint_floor_is_10():
    assert _read(HvacState(True, "heat", 10.0))["temperature"] == 10


@pytest.mark.parametrize("mode", ["dry", "fan"])
def test_dry_and_fan_keep_the_requested_setpoint(mode):
    # setMode's kDaikin152DryTemp/FanTemp are overwritten by IRac's setTemp.
    assert _read(HvacState(True, mode, 27.0))["temperature"] == 27


@pytest.mark.parametrize("mode", ["auto", "dry", "cool", "heat", "fan"])
def test_off_frame_matches_the_c_path_in_every_mode(mode):
    # The C path sends mode "off", which Daikin152 turns into auto, so the
    # 18 °C floor applies even when the last mode was heat.
    read = _read(HvacState(False, mode, 10.0))
    assert (read["power"], read["mode"], read["temperature"]) == (0, "auto", 18)


def test_swing_sets_the_documented_value():
    assert _read(HvacState(True, "cool", 24.0, swing_v="swing"))["swing_v"] == "swing"


@pytest.mark.parametrize(
    "features, expected",
    [
        ({"powerful": True, "quiet": True}, (1, 0, 0)),
        ({"powerful": True, "economy": True}, (0, 0, 1)),
        ({"quiet": True, "economy": True}, (0, 1, 1)),
        ({"powerful": True, "quiet": True, "economy": True}, (0, 0, 1)),
    ],
)
def test_feature_interplay_follows_the_c_path(features, expected):
    # IRac sets quiet, then powerful (clears quiet), then econo (clears
    # powerful).
    read = _read(HvacState(True, "cool", 24.0, features=features))
    assert (read["powerful"], read["quiet"], read["economy"]) == expected


def test_registry_serves_the_port():
    for model in ("ARC480A5 remote", "Daikin152"):
        assert isinstance(registry.get_device("daikin", model), Daikin152Device)


def test_capabilities_match_the_legacy_entity():
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.daikin import Daikin152

    for model in ("ARC480A5 remote", "Daikin152"):
        legacy = LegacyDevice("daikin", model, Daikin152)
        assert Daikin152Device("daikin", model).capabilities == legacy.capabilities


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(
        r for r in load_oracle("DAIKIN152") if r["state"].get("swing") == "on"
    )
    with pytest.raises(AssertionError, match="swing_v"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("DAIKIN152")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:1], DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_daikin152_device.py -q`
Expected: collection error, `ImportError: cannot import name ...` from `pyhvac.plugins.daikin`.

- [ ] **Step 3: Implement**: insert immediately before `class PluginObject(GenPluginObject):` in `pyhvac/plugins/daikin.py`:

```python
# --------------------------------------------------------------- Daikin152
# Layout from IRremoteESP8266's Daikin152Protocol (ir_Daikin.h): one 19-byte
# frame closed by a sum-of-bytes checksum, preceded by a 5-bit all-zero
# leader sent with the same bit timings but no header.

DAIKIN152 = Protocol(
    "daikin152",
    {
        "leader": Section(PulseDistance(433, 433, 1529), footer=(433,), gap=25182),
        "main": Section(
            PulseDistance(433, 433, 1529),  # kDaikin152BitMark/ZeroSpace/OneSpace
            header=(3492, 1718),  # kDaikin152HdrMark/HdrSpace
            footer=(433,),
            gap=25182,  # kDaikin152Gap
        ),
    },
    carrier=38000,  # kDaikin152Freq
)

DAIKIN152_LEADER = Frame("leader", b"\x00", 5)  # kDaikin152LeaderBits zeros
DAIKIN152_MAIN = Layout(
    bytes.fromhex("11da27000000000000000000000000c5000000"),
    {
        "power": Field.at(5, 0, 1),
        "mode": Field.at(  # kDaikinAuto/Dry/Cool/Heat/Fan
            5, 4, 3, values={"auto": 0, "dry": 2, "cool": 3, "heat": 4, "fan": 6}
        ),
        "temperature": Field.at(6, 1, 7, encode=int),  # whole °C
        "swing_v": Field.at(  # kDaikinSwingOff/On
            8, 0, 4, values={"off": 0x0, "swing": 0xF}
        ),
        # IRac's kLow/kMedium/kHigh (kDaikinFanMin, Med, Max - 1) plus 2.
        "fan": Field.at(8, 4, 4, values={"auto": 0xA, "1": 3, "2": 5, "3": 6}),
        "powerful": Field.at(13, 0, 1),
        "quiet": Field.at(13, 5, 1),
        "comfort": Field.at(16, 1, 1),  # never set through IRac
        "economy": Field.at(16, 2, 1),
        "sensor": Field.at(16, 3, 1),  # never set through IRac
    },
    checksum=Sum8(0, 18, 18),
)
DAIKIN152_MIN_TEMP = 10.0  # kDaikinMinTemp, heat only
DAIKIN152_MIN_OTHER = 18.0  # kDaikin2MinCoolTemp, every other mode
DAIKIN152_MAX_TEMP = 32.0  # kDaikinMaxTemp


class Daikin152Device(Device):
    """Daikin152 (ARC480A5): a full-state protocol, ``previous`` is ignored."""

    PROTOCOL = DAIKIN152
    LAYOUTS = (None, DAIKIN152_MAIN)
    capabilities = Capabilities(
        modes=("auto", "dry", "cool", "heat", "fan"),
        temperature=TemperatureRange(10.0, 32.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
        ),
        swing_v=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
        features={
            name: Choice((False, True), {False: "off", True: "on"})
            for name in ("economy", "powerful", "quiet")
        },
    )

    def frames(self, previous, target, actions):
        feat = target.features
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which Daikin152 maps to auto).
        mode = target.mode if target.power else "auto"
        # IRac sets the mode before the setpoint, so the dry/fan setpoints
        # setMode writes are always overwritten; setTemp's floor is 10 °C in
        # heat and 18 °C in every other mode.
        floor = DAIKIN152_MIN_TEMP if mode == "heat" else DAIKIN152_MIN_OTHER
        temperature = min(max(target.temperature, floor), DAIKIN152_MAX_TEMP)
        # IRac sets quiet, then powerful (which clears quiet), then econo
        # (which clears powerful).
        main = DAIKIN152_MAIN.build(
            power=target.power,
            mode=mode,
            temperature=temperature,
            swing_v=target.swing_v,
            fan=target.fan,
            powerful=feat["powerful"] and not feat["economy"],
            quiet=feat["quiet"] and not feat["powerful"],
            economy=feat["economy"],
        )
        return [DAIKIN152_LEADER, Frame("main", bytes(main))]


DAIKIN152_MODELS = ("ARC480A5 remote", "Daikin152")


DEVICES.update({m: Daikin152Device for m in DAIKIN152_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_daikin152_device.py -q`
Expected: 169 passed, 1 skipped (the skip(s) need the C extension).

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/daikin.py tests/test_daikin152_device.py
git add pyhvac/plugins/daikin.py tests/test_daikin152_device.py
git commit -m "DAIKIN152: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 6: DAIKIN160

Two headed frames of 7 and 13 bytes (header space 2145 µs, from the header: portkit clustered it with the bit space).

**Files:**
- Modify: `pyhvac/plugins/daikin.py` (new block before `class PluginObject(GenPluginObject):`)
- Test: `tests/test_daikin160_device.py`

**Interfaces:**
- Consumes: `Device`, the `pyhvac.fields` layouts and checksums, bitless sections, `tests/port_oracle.py` (`Defect`, `assert_matches_oracle`, `state_from_record`, `oracle_params`), and the oracle fixture `DAIKIN160`.
- Produces: `Daikin160Device`, `DAIKIN160_MODELS`, and the `DEVICES` entries for those models.

- [ ] **Step 1: Write the failing tests**: create `tests/test_daikin160_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.daikin import (
    DAIKIN160_FIRST,
    DAIKIN160_MODELS,
    DAIKIN160_SECOND,
    Daikin160Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented kDaikin160SwingV* positions here:
# the old labels go through IRGHVAC.trans_swing ("90°" -> kHigh, "60°" ->
# kUpperMiddle) into IRDaikin160::convertSwingV, which maps kHigh to
# kDaikin160SwingVHigh (so kDaikin160SwingVHighest is never sent) and has no
# kUpperMiddle case (it falls back to kDaikin160SwingVAuto).
DEFECTS = (
    Defect("swing_v", "1", "2", "C sends 'high' (0x4) for highest"),
    Defect("swing_v", "2", "auto", "C has no upper-middle case: sends auto"),
)


def device():
    return Daikin160Device("daikin", "ARC423A5 remote")


@pytest.mark.parametrize("record", oracle_params("DAIKIN160"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layouts_round_trip_every_oracle_state():
    dev = device()
    for record in load_oracle("DAIKIN160"):
        state = state_from_record(dev, record["state"])
        first, second = dev.frames(None, state, ())
        for layout, frame in ((DAIKIN160_FIRST, first), (DAIKIN160_SECOND, second)):
            values = layout.read(frame.data)
            assert layout.build(**values) == bytearray(frame.data)


def test_first_frame_is_constant():
    dev = device()
    first, _ = dev.frames(None, dev.normalise(HvacState(True, "heat", 28.0)), ())
    assert first.data == bytes.fromhex("11da27f00d000f")


@pytest.mark.parametrize("mode", ["auto", "dry", "cool", "heat", "fan"])
def test_off_frame_matches_the_c_path_in_every_mode(mode):
    # The C path sends mode "off", which convertMode turns into auto, with
    # the setpoint as given.
    dev = device()
    state = dev.normalise(HvacState(False, mode, 21.0))
    _, second = dev.frames(None, state, ())
    read = DAIKIN160_SECOND.read(second.data)
    assert (read["power"], read["mode"], read["temperature"]) == (0, "auto", 11)


@pytest.mark.parametrize("temperature", [10.0, 21.0, 32.0])
def test_temperature_is_stored_as_degrees_minus_10(temperature):
    dev = device()
    state = dev.normalise(HvacState(True, "cool", temperature))
    _, second = dev.frames(None, state, ())
    assert DAIKIN160_SECOND.read(second.data)["temperature"] == temperature - 10


def test_swing_off_is_sent_as_auto():
    # The header has no "off" value; the C path falls back to auto (0xF).
    dev = device()
    off = dev.frames(None, dev.normalise(HvacState(True, "cool", 24.0)), ())
    auto = dev.frames(
        None, dev.normalise(HvacState(True, "cool", 24.0, swing_v="auto")), ()
    )
    assert off == auto
    assert DAIKIN160_SECOND.read_raw(off[1].data, "swing_v") == 0xF


def test_swing_positions_follow_the_header():
    dev = device()
    raw = {
        v: DAIKIN160_SECOND.read_raw(
            dev.frames(
                None, dev.normalise(HvacState(True, "cool", 24.0, swing_v=v)), ()
            )[1].data,
            "swing_v",
        )
        for v in ("1", "2", "3", "4", "5")
    }
    assert raw == {"1": 5, "2": 4, "3": 3, "4": 2, "5": 1}


def test_registry_serves_the_port():
    for model in DAIKIN160_MODELS:
        assert isinstance(registry.get_device("daikin", model), Daikin160Device)


@pytest.mark.parametrize("model", DAIKIN160_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.daikin import Daikin160

    legacy = LegacyDevice("daikin", model, Daikin160)
    assert Daikin160Device("daikin", model).capabilities == legacy.capabilities


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(
        r
        for r in load_oracle("DAIKIN160")
        if r["state"]["swing"] == "60°" and r["state"]["mode"] != "off"
    )
    with pytest.raises(AssertionError, match="swing_v"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("DAIKIN160")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:1], DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_daikin160_device.py -q`
Expected: collection error, `ImportError: cannot import name ...` from `pyhvac.plugins.daikin`.

- [ ] **Step 3: Implement**: insert immediately before `class PluginObject(GenPluginObject):` in `pyhvac/plugins/daikin.py`:

```python
# --------------------------------------------------------------- Daikin160
# Layout from IRremoteESP8266's Daikin160Protocol (ir_Daikin.h): 20 bytes in
# two sections of 7 and 13, each closed by a sum-of-bytes checksum; frame
# byte n of the second section is struct byte n + 7.

DAIKIN160 = Protocol(
    "daikin160",
    {
        "main": Section(
            PulseDistance(342, 700, 1786),
            header=(5000, 2145),
            footer=(342,),
            gap=29650,
        ),
    },
    carrier=38000,
)

DAIKIN160_SWING_V = {  # kDaikin160SwingV*; the header has no "off" value
    "auto": 0xF,
    "off": 0xF,  # as the C path: setSwingVertical falls back to auto
    "1": 0x5,  # highest
    "2": 0x4,  # high
    "3": 0x3,  # middle
    "4": 0x2,  # low
    "5": 0x1,  # lowest
}

DAIKIN160_FIRST = Layout(
    bytes.fromhex("11da27f00d0000"),
    {},
    checksum=Sum8(0, 6, 6),
)
DAIKIN160_SECOND = Layout(
    bytes.fromhex("11da2700d30001000000000800"),
    {
        "power": Field.at(5, 0, 1),
        "mode": Field.at(
            5, 4, 3, values={"auto": 0, "dry": 2, "cool": 3, "heat": 4, "fan": 6}
        ),
        "swing_v": Field.at(6, 4, 4, values=DAIKIN160_SWING_V),
        "temperature": Field.at(9, 1, 6),  # whole °C - 10
        "fan": Field.at(10, 0, 4, values={"auto": 0xA, "1": 4, "2": 5, "3": 6}),
    },
    checksum=Sum8(0, 12, 12),
)


class Daikin160Device(Device):
    """Daikin160 (ARC423A5): a full-state protocol, ``previous`` is ignored."""

    PROTOCOL = DAIKIN160
    LAYOUTS = (DAIKIN160_FIRST, DAIKIN160_SECOND)
    capabilities = Capabilities(
        modes=("auto", "dry", "cool", "heat", "fan"),
        temperature=TemperatureRange(10.0, 32.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
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
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to auto).
        second = DAIKIN160_SECOND.build(
            power=target.power,
            mode=target.mode if target.power else "auto",
            swing_v=target.swing_v,
            temperature=int(target.temperature) - 10,
            fan=target.fan,
        )
        return [
            Frame("main", bytes(DAIKIN160_FIRST.build())),
            Frame("main", bytes(second)),
        ]


DAIKIN160_MODELS = ("ARC423A5 remote", "FTE12HV2S", "Daikin160")


DEVICES.update({m: Daikin160Device for m in DAIKIN160_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_daikin160_device.py -q`
Expected: 215 passed, 3 skipped (the skip(s) need the C extension).

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/daikin.py tests/test_daikin160_device.py
git add pyhvac/plugins/daikin.py tests/test_daikin160_device.py
git commit -m "DAIKIN160: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 7: DAIKIN176

Two headed frames of 7 and 15 bytes (header space 2140 µs, from the header). Only 37 oracle records: C-path comparison covers the rest.

**Files:**
- Modify: `pyhvac/plugins/daikin.py` (new block before `class PluginObject(GenPluginObject):`)
- Test: `tests/test_daikin176_device.py`

**Interfaces:**
- Consumes: `Device`, the `pyhvac.fields` layouts and checksums, bitless sections, `tests/port_oracle.py` (`Defect`, `assert_matches_oracle`, `state_from_record`, `oracle_params`), and the oracle fixture `DAIKIN176`.
- Produces: `Daikin176Device`, `DAIKIN176_MODELS`, and the `DEVICES` entries for those models.

- [ ] **Step 1: Write the failing tests**: create `tests/test_daikin176_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.daikin import (
    DAIKIN176_FIRST,
    DAIKIN176_MODELS,
    DAIKIN176_SECOND,
    Daikin176Device,
)
from pyhvac.state import HvacState

# The C path never sends kDaikin176SwingHAuto (0x5): IRGHVAC.trans_hswing has
# no entry for the old value "on", so swingh stays at IRac's default kOff and
# IRDaikin176::convertSwingH turns that into kDaikin176SwingHOff (0x6).
DEFECTS = (Defect("swing_h", "swing", "off", "C sends SwingHOff for swing 'on'"),)


def device():
    return Daikin176Device("daikin", "BRC4C153 remote")


def _with_c_defaults(record):
    # A record without "fan" relied on IRac's default (kAuto), which
    # IRDaikin176::convertFan sends as kDaikin176FanMax, labelled "high".
    return {**record, "state": {"fan": "high", **record["state"]}}


@pytest.mark.parametrize("record", oracle_params("DAIKIN176"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, _with_c_defaults(record), dev.LAYOUTS, DEFECTS)


def test_layouts_round_trip_every_oracle_state():
    dev = device()
    for record in load_oracle("DAIKIN176"):
        state = state_from_record(dev, _with_c_defaults(record)["state"])
        first, second = dev.frames(None, state, ())
        for layout, frame in ((DAIKIN176_FIRST, first), (DAIKIN176_SECOND, second)):
            values = layout.read(frame.data)
            assert layout.build(**values) == bytearray(frame.data)


@pytest.mark.parametrize("mode", ["dry", "fan"])
def test_dry_and_fan_send_17(mode):
    dev = device()
    _, second = dev.frames(None, dev.normalise(HvacState(True, mode, 30.0)), ())
    assert DAIKIN176_SECOND.read(second.data)["temperature"] == 17 - 9


@pytest.mark.parametrize(
    "mode, alt", [("auto", 7), ("cool", 7), ("heat", 7), ("dry", 2), ("fan", 6)]
)
def test_alt_mode_follows_the_mode(mode, alt):
    dev = device()
    _, second = dev.frames(None, dev.normalise(HvacState(True, mode, 24.0)), ())
    read = DAIKIN176_SECOND.read(second.data)
    assert (read["mode"], read["alt_mode"], read["mode_button"]) == (mode, alt, 0)


@pytest.mark.parametrize("mode", ["auto", "dry", "cool", "heat", "fan"])
def test_off_frame_matches_the_c_path_in_every_mode(mode):
    # The C path sends mode "off", which convertMode turns into cool, with
    # the setpoint as given (the dry/fan 17 °C rule does not apply to cool).
    dev = device()
    state = dev.normalise(HvacState(False, mode, 12.0))
    _, second = dev.frames(None, state, ())
    read = DAIKIN176_SECOND.read(second.data)
    assert (read["power"], read["mode"], read["alt_mode"]) == (0, "cool", 7)
    assert read["temperature"] == 12 - 9


def test_fan_and_swing_codes():
    dev = device()
    for fan, code in (("1", 1), ("2", 3)):
        for swing, scode in (("off", 6), ("swing", 5)):
            state = dev.normalise(HvacState(True, "cool", 24.0, fan, swing_h=swing))
            _, second = dev.frames(None, state, ())
            assert second.data[11] == code << 4 | scode


@pytest.mark.parametrize("model", DAIKIN176_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("daikin", model), Daikin176Device)


def test_capabilities_match_the_legacy_entity():
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.daikin import Daikin176

    for model in DAIKIN176_MODELS:
        legacy = LegacyDevice("daikin", model, Daikin176)
        assert device().capabilities == legacy.capabilities


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(
        r for r in load_oracle("DAIKIN176") if r["state"].get("hswing") == "on"
    )
    with pytest.raises(AssertionError, match="swing_h"):
        assert_matches_oracle(dev, _with_c_defaults(record), dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("DAIKIN176")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:1], DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_daikin176_device.py -q`
Expected: collection error, `ImportError: cannot import name ...` from `pyhvac.plugins.daikin`.

- [ ] **Step 3: Implement**: insert immediately before `class PluginObject(GenPluginObject):` in `pyhvac/plugins/daikin.py`:

```python
# ------------------------------------------------------------- Daikin176
# Layout from IRremoteESP8266's Daikin176Protocol (ir_Daikin.h): 22 bytes in
# two sections of 7 and 15, each closed by a sum-of-bytes checksum; frame
# byte n of the second section is struct byte n + 7.

DAIKIN176 = Protocol(
    "daikin176",
    {
        "main": Section(
            PulseDistance(370, 710, 1780),
            header=(5070, 2140),
            footer=(370,),
            gap=29410,
        ),
    },
    carrier=38000,
)

DAIKIN176_MODES = {"fan": 0, "heat": 1, "cool": 2, "auto": 3, "dry": 7}
# AltMode bits kept in line with the mode (IRDaikin176::setMode)
DAIKIN176_ALT_MODES = {"fan": 6, "heat": 7, "cool": 7, "auto": 7, "dry": 2}
DAIKIN176_DRY_FAN_TEMP = 17.0  # kDaikin176DryFanTemp

DAIKIN176_FIRST = Layout(
    bytes.fromhex("11da1718040000"),
    {"unit_id": Field.at(3, 0, 1)},  # Id1: 0 = unit A, 1 = unit B
    checksum=Sum8(0, 6, 6),
)
DAIKIN176_SECOND = Layout(
    bytes.fromhex("11da17180003000000000000002000"),
    {
        "unit_id": Field.at(3, 0, 1),  # Id2, always equal to Id1
        "alt_mode": Field.at(5, 4, 3),
        "mode_button": Field.at(6, 0, 8),  # kDaikin176ModeButton when set
        "power": Field.at(7, 0, 1),
        "mode": Field.at(7, 4, 3, values=DAIKIN176_MODES),
        "temperature": Field.at(10, 1, 6),  # whole °C - 9
        "swing_h": Field.at(11, 0, 4, values={"off": 0x6, "swing": 0x5}),
        "fan": Field.at(11, 4, 4, values={"1": 1, "2": 3}),  # kDaikinFanMin/176FanMax
    },
    checksum=Sum8(0, 14, 14),
)


class Daikin176Device(Device):
    """Daikin176 (BRC4C153): a full-state protocol, ``previous`` is ignored.

    The header's ModeButton byte marks a mode-button press, but the C path
    always clears it (IRac::daikin176 calls setTemp and setFan after
    setMode), so every message is a plain full state with ModeButton 0.
    """

    PROTOCOL = DAIKIN176
    LAYOUTS = (DAIKIN176_FIRST, DAIKIN176_SECOND)
    capabilities = Capabilities(
        modes=("auto", "dry", "cool", "heat", "fan"),
        temperature=TemperatureRange(10.0, 32.0),
        fan=Choice(("1", "2"), {"1": "low", "2": "high"}),
        swing_h=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode cool (IRac passes mode
        # "off", which convertMode maps to cool) with the setpoint as given.
        mode = target.mode if target.power else "cool"
        temperature = target.temperature
        if mode in ("dry", "fan"):
            temperature = DAIKIN176_DRY_FAN_TEMP
        first = DAIKIN176_FIRST.build()
        second = DAIKIN176_SECOND.build(
            alt_mode=DAIKIN176_ALT_MODES[mode],
            mode_button=0,
            power=target.power,
            mode=mode,
            temperature=int(temperature) - 9,
            swing_h=target.swing_h,
            fan=target.fan,
        )
        return [Frame("main", bytes(first)), Frame("main", bytes(second))]


DAIKIN176_MODELS = ("BRC4C153 remote", "FFQ35B8V1B", "BRC4C151 remote", "Daikin176")


DEVICES.update({m: Daikin176Device for m in DAIKIN176_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_daikin176_device.py -q`
Expected: 57 passed, 1 skipped (the skip(s) need the C extension).

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/daikin.py tests/test_daikin176_device.py
git add pyhvac/plugins/daikin.py tests/test_daikin176_device.py
git commit -m "DAIKIN176: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 8: DAIKIN216

Two headed frames of 8 and 19 bytes; the first is constant.

**Files:**
- Modify: `pyhvac/plugins/daikin.py` (new block before `class PluginObject(GenPluginObject):`)
- Test: `tests/test_daikin216_device.py`

**Interfaces:**
- Consumes: `Device`, the `pyhvac.fields` layouts and checksums, bitless sections, `tests/port_oracle.py` (`Defect`, `assert_matches_oracle`, `state_from_record`, `oracle_params`), and the oracle fixture `DAIKIN216`.
- Produces: `Daikin216Device`, `DAIKIN216_MODELS`, and the `DEVICES` entries for those models.

- [ ] **Step 1: Write the failing tests**: create `tests/test_daikin216_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.daikin import (
    DAIKIN216_FIRST,
    DAIKIN216_MODELS,
    DAIKIN216_SECOND,
    Daikin216Device,
)
from pyhvac.state import HvacState

# The C path never sends swing on: the old vocabulary's "on" has no entry in
# IRGHVAC.trans_swing / trans_hswing, so build_ircode skips the key, swingv and
# swingh stay kOff, and IRac::daikin216 writes kDaikin216SwingOff instead of
# the documented kDaikin216SwingOn (0b1111).
DEFECTS = (
    Defect("swing_v", "swing", "off", "C glue has no 'on' swing: sends off"),
    Defect("swing_h", "swing", "off", "C glue has no 'on' hswing: sends off"),
)


def device():
    return Daikin216Device("daikin", "ARC433B69 remote")


def second(state):
    dev = device()
    _, frame = dev.frames(None, dev.normalise(state), ())
    return DAIKIN216_SECOND.read(frame.data)


@pytest.mark.parametrize("record", oracle_params("DAIKIN216"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layouts_round_trip_every_oracle_state():
    dev = device()
    for record in load_oracle("DAIKIN216"):
        state = state_from_record(dev, record["state"])
        first, sec = dev.frames(None, state, ())
        for layout, frame in ((DAIKIN216_FIRST, first), (DAIKIN216_SECOND, sec)):
            values = layout.read(frame.data)
            assert layout.build(**values) == bytearray(frame.data)


def test_first_section_is_constant():
    assert bytes(DAIKIN216_FIRST.build()) == bytes.fromhex("11da27f000000002")


@pytest.mark.parametrize("mode", ["auto", "dry", "cool", "heat", "fan"])
def test_off_frame_matches_the_c_path_in_every_mode(mode):
    # The C path sends mode "off", which convertMode turns into auto.
    read = second(HvacState(False, mode, 24.0))
    assert (read["power"], read["mode"], read["temperature"]) == (0, "auto", 24)


def test_setpoint_is_clamped_to_10_32():
    assert second(HvacState(True, "cool", 5.0))["temperature"] == 10
    assert second(HvacState(True, "heat", 40.0))["temperature"] == 32


def test_quiet_is_a_fan_speed():
    read = second(HvacState(True, "cool", 24.0, fan="3", features={"quiet": True}))
    assert (read["fan"], read["powerful"]) == ("quiet", 0)


def test_powerful_cancels_quiet_and_leaves_fan_auto_as_the_c_path_does():
    state = HvacState(
        True, "cool", 24.0, fan="3", features={"quiet": True, "powerful": True}
    )
    read = second(state)
    assert (read["fan"], read["powerful"]) == ("auto", 1)


def test_powerful_keeps_the_fan_speed():
    read = second(HvacState(True, "cool", 24.0, fan="2", features={"powerful": True}))
    assert (read["fan"], read["powerful"]) == ("2", 1)


def test_swing_on_sets_the_documented_nibble():
    read = second(HvacState(True, "cool", 24.0, swing_v="swing", swing_h="swing"))
    assert (read["swing_v"], read["swing_h"]) == ("swing", "swing")
    raw = DAIKIN216_SECOND.build(swing_v="swing", swing_h="swing")
    assert (raw[8] & 0x0F, raw[9] & 0x0F) == (0xF, 0xF)


@pytest.mark.parametrize("model", DAIKIN216_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("daikin", model), Daikin216Device)


def test_capabilities_match_the_legacy_entity():
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.daikin import Daikin216

    legacy = LegacyDevice("daikin", "ARC433B69 remote", Daikin216)
    assert device().capabilities == legacy.capabilities


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(
        r for r in load_oracle("DAIKIN216") if r["state"].get("swing") == "on"
    )
    with pytest.raises(AssertionError, match="swing_v"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("DAIKIN216")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:1], DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_daikin216_device.py -q`
Expected: collection error, `ImportError: cannot import name ...` from `pyhvac.plugins.daikin`.

- [ ] **Step 3: Implement**: insert immediately before `class PluginObject(GenPluginObject):` in `pyhvac/plugins/daikin.py`:

```python
# --------------------------------------------------------------- Daikin216
# Layout from IRremoteESP8266's Daikin216Protocol (ir_Daikin.h): 27 bytes in
# two sections of 8 and 19 (kDaikin216Section1Length), each closed by a
# sum-of-bytes checksum; frame byte n of the second section is struct byte
# n + 8.

DAIKIN216 = Protocol(
    "daikin216",
    {
        "main": Section(
            PulseDistance(420, 450, 1300),
            header=(3440, 1750),
            footer=(420,),
            gap=29650,
        ),
    },
    carrier=38000,
)

DAIKIN216_SWING = {"off": 0b0000, "swing": 0b1111}  # kDaikin216Swing{Off,On}

DAIKIN216_FIRST = Layout(
    bytes.fromhex("11da27f000000000"),
    {},
    checksum=Sum8(0, 7, 7),
)
DAIKIN216_SECOND = Layout(
    bytes.fromhex("11da27000000000000000000000000c0000000"),
    {
        "power": Field.at(5, 0, 1),
        "mode": Field.at(
            5, 4, 3, values={"auto": 0, "dry": 2, "cool": 3, "heat": 4, "fan": 6}
        ),
        "temperature": Field.at(6, 1, 6, encode=int),  # whole °C
        "swing_v": Field.at(8, 0, 4, values=DAIKIN216_SWING),
        # kDaikinFan*: level n is sent as n + 2; quiet is a fan value.
        "fan": Field.at(
            8, 4, 4, values={"auto": 0xA, "quiet": 0xB, "1": 3, "2": 5, "3": 6}
        ),
        "swing_h": Field.at(9, 0, 4, values=DAIKIN216_SWING),
        "powerful": Field.at(13, 0, 1),
    },
    checksum=Sum8(0, 18, 18),
)


class Daikin216Device(Device):
    """Daikin216 (ARC433B69): a full-state protocol, ``previous`` is ignored."""

    PROTOCOL = DAIKIN216
    LAYOUTS = (DAIKIN216_FIRST, DAIKIN216_SECOND)
    capabilities = Capabilities(
        modes=("auto", "dry", "cool", "heat", "fan"),
        temperature=TemperatureRange(10.0, 32.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
        ),
        swing_v=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
        swing_h=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
        features={
            name: Choice((False, True), {False: "off", True: "on"})
            for name in ("powerful", "quiet")
        },
    )

    def frames(self, previous, target, actions):
        feat = target.features
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode turns into auto).
        mode = target.mode if target.power else "auto"
        # Quiet is a fan speed (kDaikinFanQuiet); powerful cancels quiet and
        # then leaves the fan on auto (IRDaikin216::setPowerful/setQuiet).
        fan = target.fan
        if feat["quiet"]:
            fan = "auto" if feat["powerful"] else "quiet"
        second = DAIKIN216_SECOND.build(
            power=target.power,
            mode=mode,
            temperature=target.temperature,
            swing_v=target.swing_v,
            fan=fan,
            swing_h=target.swing_h,
            powerful=feat["powerful"],
        )
        return [
            Frame("main", bytes(DAIKIN216_FIRST.build())),
            Frame("main", bytes(second)),
        ]


DAIKIN216_MODELS = ("ARC433B69 remote", "ARC484A4 remote", "FTQ60TV16U2", "Daikin216")


DEVICES.update({m: Daikin216Device for m in DAIKIN216_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_daikin216_device.py -q`
Expected: 165 passed, 1 skipped (the skip(s) need the C extension).

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/daikin.py tests/test_daikin216_device.py
git add pyhvac/plugins/daikin.py tests/test_daikin216_device.py
git commit -m "DAIKIN216: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 9: DAIKIN312

5-bit zero leader + frames of 20 and 19 bytes; carrier 36.7 kHz.

**Files:**
- Modify: `pyhvac/plugins/daikin.py` (new block before `class PluginObject(GenPluginObject):`)
- Test: `tests/test_daikin312_device.py`

**Interfaces:**
- Consumes: `Device`, the `pyhvac.fields` layouts and checksums, bitless sections, `tests/port_oracle.py` (`Defect`, `assert_matches_oracle`, `state_from_record`, `oracle_params`), and the oracle fixture `DAIKIN312`.
- Produces: `Daikin312Device`, `DAIKIN312_MODELS`, and the `DEVICES` entries for those models.

- [ ] **Step 1: Write the failing tests**: create `tests/test_daikin312_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.ir.model import Frame
from pyhvac.plugins.daikin import (
    DAIKIN312_FIRST,
    DAIKIN312_MODELS,
    DAIKIN312_SECOND,
    Daikin312Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Daikin312 values here:
# - IRDaikin312::convertSwingH has no kOff case, so "off" is sent as
#   kDaikin312SwingHAuto (0xF) instead of kDaikin312SwingHOff (0x0);
# - the old glue (IRGHVAC.trans_swing) has no "on" entry, so IRac keeps
#   swingv kOff and sends kDaikin312SwingVOff (0x0) instead of
#   kDaikin312SwingVSwing (0xF).
DEFECTS = (
    Defect("swing_h", "off", "swing", "C has no off case: sends swing (0xF)"),
    Defect("swing_v", "swing", "off", "C path never sends swing: sends off (0x0)"),
)


def device():
    return Daikin312Device("daikin", "ARC466A67 remote")


def frames(**kw):
    dev = device()
    features = kw.pop("features", {})
    state = dev.normalise(HvacState(features=features, **kw))
    return dev.frames(None, state, ())


@pytest.mark.parametrize("record", oracle_params("DAIKIN312"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layouts_round_trip_every_oracle_state():
    dev = device()
    for record in load_oracle("DAIKIN312"):
        state = state_from_record(dev, record["state"])
        _, first, second = dev.frames(None, state, ())
        for layout, frame in ((DAIKIN312_FIRST, first), (DAIKIN312_SECOND, second)):
            values = layout.read(frame.data)
            assert layout.build(**values) == bytearray(frame.data)


def test_leader_is_five_zero_bits():
    leader, _, _ = frames(power=True, mode="cool", temperature=24.0)
    assert leader == Frame("leader", b"\x00", 5)


def test_half_degree_setpoint():
    _, _, second = frames(power=True, mode="heat", temperature=22.5)
    assert second.data[6] == 45


def test_cool_raises_setpoint_to_18():
    _, _, second = frames(power=True, mode="cool", temperature=12.0)
    assert DAIKIN312_SECOND.read(second.data)["temperature"] == 36  # 18 °C


def test_off_clears_power_and_sets_power2():
    _, first, second = frames(power=False, mode="cool", temperature=24.0)
    assert DAIKIN312_SECOND.read(second.data)["power"] == 0
    assert DAIKIN312_FIRST.read(first.data)["power2"] == 1


@pytest.mark.parametrize("mode", ["auto", "dry", "cool", "heat", "fan"])
def test_off_frame_matches_the_c_path_in_every_mode(mode):
    # The C path sends mode "off", which Daikin312 turns into auto, with the
    # setpoint as given (the cool minimum does not apply to auto).
    _, _, second = frames(power=False, mode=mode, temperature=12.0)
    read = DAIKIN312_SECOND.read(second.data)
    assert (read["mode"], read["temperature"]) == ("auto", 24)


def test_powerful_cancels_quiet_as_the_c_path_does():
    _, _, second = frames(
        power=True,
        mode="cool",
        temperature=24.0,
        features={"quiet": True, "powerful": True},
    )
    read = DAIKIN312_SECOND.read(second.data)
    assert (read["powerful"], read["quiet"]) == (1, 0)


@pytest.mark.parametrize("light,raw", [(False, 3), (True, 1)])
def test_light_as_irac_sends_it(light, raw):
    _, first, _ = frames(
        power=True, mode="cool", temperature=24.0, features={"light": light}
    )
    assert first.data[12] & 0x03 == raw


def test_beep_off_and_auto_clean_are_hardwired():
    _, first, _ = frames(power=True, mode="cool", temperature=24.0)
    assert first.data[7] >> 6 == 3  # Beep off
    assert first.data[14] & 0x10  # Clean


def test_registry_serves_the_port():
    for model in DAIKIN312_MODELS:
        assert isinstance(registry.get_device("daikin", model), Daikin312Device)


def test_capabilities_match_the_legacy_entity():
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.daikin import Daikin312

    for model in DAIKIN312_MODELS:
        legacy = LegacyDevice("daikin", model, Daikin312)
        assert device().capabilities == legacy.capabilities


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(r for r in load_oracle("DAIKIN312") if "hswing" not in r["state"])
    with pytest.raises(AssertionError, match="swing_h"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("DAIKIN312")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:2], DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_daikin312_device.py -q`
Expected: collection error, `ImportError: cannot import name ...` from `pyhvac.plugins.daikin`.

- [ ] **Step 3: Implement**: insert immediately before `class PluginObject(GenPluginObject):` in `pyhvac/plugins/daikin.py`:

```python
# --------------------------------------------------------------- Daikin312
# Layout from IRremoteESP8266's Daikin312Protocol (ir_Daikin.h): 39 bytes in
# two sections of 20 and 19, each closed by a sum-of-bytes checksum; frame
# byte n of the second section is struct byte n + 20. The sections follow a
# headerless leader of five zero bits (sendDaikin312).

DAIKIN312_BITS = PulseDistance(453, 414, 1275)  # kDaikin312BitMark/Zero/OneSpace
DAIKIN312 = Protocol(
    "daikin312",
    {
        "leader": Section(DAIKIN312_BITS, footer=(453,), gap=25100),
        "main": Section(DAIKIN312_BITS, header=(3518, 1688), footer=(453,), gap=35512),
    },
    carrier=36700,  # kDaikin312Freq
)

# Skeleton bits the port never changes, as IRac::daikin312 sends them: beep
# off (Beep = 3, byte 7) and auto clean hardwired on (Clean, byte 14 bit 4).
DAIKIN312_FIRST = Layout(
    bytes.fromhex("11da2700025864d8640600000000100000000000"),
    {
        "power2": Field.at(6, 7, 1),  # inverse of power
        "mold": Field.at(8, 3, 1),
        "light": Field.at(12, 0, 2, values={True: 1, False: 3}),  # as IRac
    },
    checksum=Sum8(0, 19, 19),
)
DAIKIN312_SECOND = Layout(
    bytes.fromhex("11da27000008000000000006600000c5000800"),
    {
        "power": Field.at(5, 0, 1),
        "mode": Field.at(
            5, 4, 3, values={"auto": 0, "dry": 2, "cool": 3, "heat": 4, "fan": 6}
        ),
        "temperature": Field.at(6, 0, 7),  # in half degrees
        "swing_v": Field.at(8, 0, 4, values={"off": 0x0, "swing": 0xF}),
        "fan": Field.at(8, 4, 4, values={"auto": 0xA, "1": 3, "2": 5, "3": 6}),
        "swing_h": Field.at(9, 0, 4, values={"off": 0x0, "swing": 0xF}),
        "powerful": Field.at(13, 0, 1),
        "quiet": Field.at(13, 5, 1),
        "economy": Field.at(16, 2, 1),
        "purifier": Field.at(16, 4, 1),
    },
    checksum=Sum8(0, 18, 18),
)
DAIKIN312_MIN_COOL = 18.0  # kDaikin312MinCoolTemp


class Daikin312Device(Device):
    """Daikin312 (ARC466A67): a full-state protocol, ``previous`` is ignored."""

    PROTOCOL = DAIKIN312
    LAYOUTS = (None, DAIKIN312_FIRST, DAIKIN312_SECOND)
    capabilities = Capabilities(
        modes=("auto", "dry", "cool", "heat", "fan"),
        temperature=TemperatureRange(10.0, 32.0, (0, 5)),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
        ),
        swing_v=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
        swing_h=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
        features={
            name: Choice((False, True), {False: "off", True: "on"})
            for name in (
                "quiet",
                "powerful",
                "light",
                "economy",
                "purifier",
                "cleaning",
            )
        },
    )

    def frames(self, previous, target, actions):
        feat = target.features
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which Daikin312 maps to auto), so the cool minimum never
        # applies to it.
        mode = target.mode if target.power else "auto"
        temperature = target.temperature
        if mode == "cool":
            temperature = max(temperature, DAIKIN312_MIN_COOL)
        first = DAIKIN312_FIRST.build(
            power2=not target.power,
            mold=feat["cleaning"],
            light=feat["light"],
        )
        second = DAIKIN312_SECOND.build(
            power=target.power,
            mode=mode,
            temperature=int(temperature * 2),
            fan=target.fan,
            swing_v=target.swing_v,
            swing_h=target.swing_h,
            powerful=feat["powerful"],
            quiet=feat["quiet"] and not feat["powerful"],  # powerful cancels quiet
            economy=feat["economy"],
            purifier=feat["purifier"],
        )
        return [
            Frame("leader", b"\x00", 5),
            Frame("main", bytes(first)),
            Frame("main", bytes(second)),
        ]


DAIKIN312_MODELS = ("FTXM20R5V1B", "ARC466A67 remote", "Daikin312")


DEVICES.update({m: Daikin312Device for m in DAIKIN312_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_daikin312_device.py -q`
Expected: 168 passed, 1 skipped (the skip(s) need the C extension).

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/daikin.py tests/test_daikin312_device.py
git add pyhvac/plugins/daikin.py tests/test_daikin312_device.py
git commit -m "DAIKIN312: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 10: Whole-family verification

**Files:**
- Test: `tests/test_daikin_family.py`

- [ ] **Step 1: Write the test**: create `tests/test_daikin_family.py`:

```python
"""Every C-backed Daikin model is served by a pure-Python device."""

from pyhvac import registry
from pyhvac.legacy import LegacyDevice
from pyhvac.plugins.daikin import PluginObject
from pyhvac.plugins.hvaclib import IRGHVAC


def test_no_daikin_model_uses_the_c_library():
    c_backed = [m for m, cls in PluginObject.MODELS.items() if issubclass(cls, IRGHVAC)]
    left = [
        m for m in c_backed if isinstance(registry.get_device("daikin", m), LegacyDevice)
    ]
    assert left == []
```

- [ ] **Step 2: Run it**

Run: `python -m pytest tests/test_daikin_family.py -q`
Expected: 1 passed. (The remaining `LegacyDevice` models, `generic` and `smash 2`, are the old pure-Python classes and never used the C library.)

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
- every `test_capabilities_match_the_legacy_entity` passes;
- the HITACHI_AC296 cases report as xfail or xpass.

- [ ] **Step 4: Commit**

```bash
black tests/test_daikin_family.py
git add tests/test_daikin_family.py
git commit -m "Test that no Daikin model is left on the C library

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
