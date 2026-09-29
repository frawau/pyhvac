# Haier Family Ports Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the C path for every Haier model with a pure-Python `Device`: HAIER_AC, HAIER_AC176, HAIER_AC_YRW02 and HAIER_AC160, all in `pyhvac/plugins/haier.py`.

**Architecture:** Same as the Daikin, Hitachi and Mitsubishi plans:
- one device class per protocol, appended to `haier.py` and registered through a new `DEVICES` dict;
- a guarded `irhvac` import, so the brand loads without the C extension;
- each port written from its `union Haier*Protocol` in `ir_Haier.h`;
- each port verified against every oracle record and against the real C path, reproducing the real captures in `ir_Haier_test.cpp` where the entity can express them.

**Tech Stack:** Python ≥ 3.9 standard library, pytest, black. The port kit on branch `ports`.

**Spec:** `docs/superpowers/specs/2026-09-27-port-kit-design.md`. House rules: the "Rulings made while planning" sections of the Daikin, Hitachi and Mitsubishi plans.

## Global Constraints

- Work on branch `ports`.
- Durations are integer µs, the carrier is in Hz, and temperatures are °C.
- Python ≥ 3.9, and no new runtime dependencies.
- Layouts come from the headers (facts).
- Capabilities equal the legacy entity (C-only test in each file).
- A difference from the C output is allowed only as a declared `Defect`.
- The old API and all existing tests stay green. Run `black` on every modified file.
- Tests: `python -m pytest -q`. The C-extension run is described in Task 6.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **The button field is always Power** (HAIER_AC: On/Off), as the C path; real remotes send the key actually pressed. HAIER_AC160 presses the light button only when the light changes, which IRac::sendAc also does.
2. **HAIER_AC_YRW02 "Code B"** now sends the documented model B code (0x59). The C path never calls `setModel`, so code-B users got code-A frames. The real V9014557-B capture `setmodelb` in `test/ir_Haier_test.cpp` (line 1533) has byte 0 = 0x59, and YRW02 is the first 14 bytes of the same struct. (Corrected after the final review; the first version wrongly said no capture confirmed it.)
3. **Sleep** is sent on all four protocols; the fixtures predate `main`'s sleep glue fix.
4. **Records without hswing** are read as "middle", because C sends kOff → Middle (the HEAVY_152 precedent).
5. **The import guard:** without it the brand vanishes without the C extension.

## Rulings made while planning

- **Sleep (all four):** the ports send the documented sleep bit (`Defect("sleep", 1, 0)`).
- **HAIER_AC_YRW02 model B:** `Defect("model", "B", "A")`, citing `kHaierAcYrw02ModelB` and `IRac::haierYrwo2` never calling `setModel`.
- **HAIER_AC160 swing:** follows C. C maps ceiling/90°/45°/30°/0° to documented codes top to bottom, but skips one documented code (Highest). That is not a defect: re-deriving from the header would move three positions and drop Lowest.
- **HAIER_AC swing "auto high"/"auto low"** reach C (they are in the glue tables), so there is no swing defect in this family.

## Kit follow-ups found here (not in this plan)

- `portkit timings` merges the extra 3000/3000 Haier leader pair into a bit.
- `portkit checksum` only tries checksums in the last two bytes, so it misses mid-frame sums (HAIER_AC176/160 byte 13).

---

### Task 1: Import guard and DEVICES

**Files:**
- Modify: `pyhvac/plugins/haier.py`
- Test: `tests/test_haier_family.py`

- [ ] **Step 1: Write the failing test**: create `tests/test_haier_family.py`:

```python
"""The Haier plugin loads without the C extension and serves every model."""

import importlib


def test_haier_imports_without_the_c_extension():
    module = importlib.import_module("pyhvac.plugins.haier")
    assert isinstance(module.DEVICES, dict)
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `python -m pytest tests/test_haier_family.py -q`
Expected: FAIL: `ModuleNotFoundError: No module named 'pyhvac.irhvac'` (without the C extension).

- [ ] **Step 3: Implement**: in `pyhvac/plugins/haier.py`, replace

```python
from .hvaclib import PulseBased, GenPluginObject
from ..irhvac import V9014557_A, V9014557_B
```

with

```python
from dataclasses import dataclass

from .hvaclib import PulseBased, GenPluginObject
from ..device import Device
from ..fields import Field, Layout, Sum8
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import Capabilities, Choice, TemperatureRange

try:
    from ..irhvac import V9014557_A, V9014557_B
except ImportError:
    # Only the C-backed classes use these; keep the ported ones importable.
    V9014557_A = V9014557_B = None
```

and insert `DEVICES = {}` (followed by two blank lines) immediately before the `# Now the match between models and objects` comment.

- [ ] **Step 4: Run the tests**

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/haier.py tests/test_haier_family.py
git add pyhvac/plugins/haier.py tests/test_haier_family.py
git commit -m "Haier: import without the C extension; DEVICES for the ports

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 2: HAIER_AC

One 9-byte frame, MSB first, header (3000, 3000, 3000, 4300); layout from `union HaierProtocol`; `Sum8(0, 8, 8)`.

**Files:**
- Modify: `pyhvac/plugins/haier.py` (block before `# Now the match between models and objects`)
- Test: `tests/test_haier_ac_device.py`

**Interfaces:**
- Consumes: `Device`, `pyhvac.fields`, `tests/port_oracle.py`, and the oracle fixture `HAIER_AC`.
- Produces: `HaierAcDevice`, `HAIER_AC_MODELS`, and the `DEVICES` entries for those models.

- [ ] **Step 1: Write the failing tests**: create `tests/test_haier_ac_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.ir.codec import decode
from pyhvac.plugins.haier import (
    HAIER_AC,
    HAIER_AC_LAYOUT,
    HAIER_AC_MODELS,
    HaierAcDevice,
)
from pyhvac.state import HvacState

# The C path never sends sleep: IRGHVAC.build_ircode's key map has no
# "sleep", so IRac::haier gets sleep -1 and setSleep(sleep >= 0) clears
# kHaierAcSleepBit. The port sends the documented bit.
DEFECTS = (Defect("sleep", 1, 0, "C glue has no 'sleep' key"),)

# Real captures from ir_Haier_test.cpp.
ON_COOL_25 = bytes.fromhex("a59120000cc0200042")  # issue #668
ISSUE_404_ON_COOL_16 = bytes.fromhex("a501200100c02000a7")
ISSUE_404_TEMP_UP_22 = bytes.fromhex("a566200100c020000c")
ISSUE_404_HEALTH_30 = bytes.fromhex("a5ec200920c02000ba")
ISSUE_668_TEMP_UP_26 = bytes.fromhex("a5a620000cc0200057")


def device(model="HSU07-HEA03 remote"):
    return HaierAcDevice("haier", model)


def read(state, previous=None):
    dev = device()
    if previous is not None:
        previous = dev.normalise(previous)
    (main,) = dev.frames(previous, dev.normalise(state), ())
    return HAIER_AC_LAYOUT.read(main.data)


def data(state):
    dev = device()
    (main,) = dev.frames(None, dev.normalise(state), ())
    return main.data


@pytest.mark.parametrize("record", oracle_params("HAIER_AC"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("HAIER_AC"):
        state = state_from_record(dev, record["state"])
        (main,) = dev.frames(None, state, ())
        values = HAIER_AC_LAYOUT.read(main.data)
        assert HAIER_AC_LAYOUT.build(**values) == bytearray(main.data)
        assert HAIER_AC_LAYOUT.checksum.check(main.data)


def test_every_oracle_message_is_one_frame():
    for record in load_oracle("HAIER_AC"):
        (main,) = decode(HAIER_AC, record["pulses"], ["main"])
        assert main.data[0] == 0xA5  # kHaierAcPrefix


def test_the_port_reproduces_the_issue_668_on_capture():
    # "ON" in cool at 25 °C, fan low: the remote's own frame (Command On).
    assert data(HvacState(True, "cool", 25.0, fan="1")) == ON_COOL_25


@pytest.mark.parametrize(
    "capture, expected",
    [
        (
            ISSUE_404_ON_COOL_16,
            {"command": "on", "temperature": 16, "mode": "cool", "fan": "1"},
        ),
        (
            ISSUE_404_TEMP_UP_22,
            {"command": "temp_up", "temperature": 22, "mode": "cool", "fan": "1"},
        ),
        (
            ISSUE_404_HEALTH_30,
            {"command": "health", "temperature": 30, "health": 1, "fan": "1"},
        ),
        (
            ISSUE_668_TEMP_UP_26,
            {"command": "temp_up", "temperature": 26, "mode": "cool", "fan": "1"},
        ),
    ],
)
def test_real_captures_read_back(capture, expected):
    # These carry the key actually pressed and the remote's clock, which the
    # C path (and so the port) never sends; they read back through the layout.
    values = HAIER_AC_LAYOUT.read(capture)
    assert HAIER_AC_LAYOUT.checksum.check(capture)
    assert {k: values[k] for k in expected} == expected
    assert HAIER_AC_LAYOUT.build(**values) == bytearray(capture)


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat", "fan"])
@pytest.mark.parametrize("t", [16.0, 23.0, 30.0])
def test_off_carries_mode_auto_and_command_off(mode, t):
    # IRac passes mode "off"; convertMode maps it to kHaierAcAuto, and the
    # final setCommand writes kHaierAcCmdOff.
    values = read(HvacState(False, mode, t, fan="3", swing_v="2"))
    assert (values["command"], values["mode"]) == ("off", "auto")
    assert (values["temperature"], values["fan"], values["swing_v"]) == (
        int(t),
        "3",
        "2",
    )


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat", "fan"])
def test_on_always_names_the_on_button(mode):
    # IRac::haier ends with setCommand(kHaierAcCmdOn), overwriting the Mode,
    # TempUp/Down, Fan, Swing, Health and Sleep commands the setters wrote.
    values = read(
        HvacState(True, mode, 30.0, fan="2", swing_v="1", features={"sleep": True})
    )
    assert (values["command"], values["mode"]) == ("on", mode)


def test_setpoint_is_clamped_to_16_30():
    assert read(HvacState(True, "cool", 10.0))["temperature"] == 16
    assert read(HvacState(True, "heat", 35.0))["temperature"] == 30


@pytest.mark.parametrize("fan, raw", [("auto", 0), ("1", 3), ("2", 2), ("3", 1)])
def test_every_fan_level_uses_set_fan_raw_values(fan, raw):
    # IRHaierAC::setFan stores Low as 3, Med as 2, High as 1, Auto as 0.
    assert (
        HAIER_AC_LAYOUT.read_raw(data(HvacState(True, "cool", 22.0, fan=fan)), "fan")
        == raw
    )


@pytest.mark.parametrize("swing, raw", [("off", 0), ("1", 1), ("2", 2)])
def test_every_swing_position(swing, raw):
    # "auto high" -> kHigh -> kHaierAcSwingVUp; "auto low" -> kLow -> Down.
    raw_read = HAIER_AC_LAYOUT.read_raw(
        data(HvacState(True, "cool", 22.0, swing_v=swing)), "swing_v"
    )
    assert raw_read == raw


def test_purifier_is_the_health_bit():
    assert (
        read(HvacState(True, "cool", 22.0, features={"purifier": True}))["health"] == 1
    )
    assert read(HvacState(True, "cool", 22.0))["health"] == 0


def test_sleep_sends_the_documented_sleep_bit():
    raw = data(HvacState(True, "cool", 22.0, features={"sleep": True}))
    assert raw[7] & 0b01000000  # kHaierAcSleepBit
    assert read(HvacState(True, "cool", 22.0))["sleep"] == 0


def test_timers_and_clock_are_never_set():
    # IRac passes clock -1 (no setCurrTime) and has no timers: stateReset's
    # values (OffHours 12, the rest 0) are sent.
    values = read(HvacState(True, "heat", 18.0, fan="2", swing_v="1"))
    assert values["off_hours"] == 12
    for name in (
        "curr_hours",
        "curr_mins",
        "off_timer",
        "on_timer",
        "off_mins",
        "on_hours",
        "on_mins",
    ):
        assert values[name] == 0, name


@pytest.mark.parametrize(
    "previous",
    [
        None,
        HvacState(False, "heat", 18.0),
        HvacState(True, "cool", 26.0, fan="1", swing_v="off"),
        HvacState(True, "cool", 22.0, fan="3", swing_v="1"),
    ],
)
def test_previous_is_ignored(previous):
    # No toggle bits, and IRac::handleToggles has no HAIER_AC case: the C
    # path never derives the button from a previous state.
    dev = device()
    target = HvacState(True, "cool", 22.0, fan="3", swing_v="1")
    assert dev.encode(previous, target).signal == dev.encode(None, target).signal


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:4] == (3000, 3000, 3000, 4300)
    assert pulses[-2:] == (520, 150000)
    assert len(pulses) == 4 + 2 * 72 + 2


@pytest.mark.parametrize("model", HAIER_AC_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("haier", model), HaierAcDevice)


@pytest.mark.parametrize("model", HAIER_AC_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.haier import Haier

    legacy = LegacyDevice("haier", model, Haier)
    assert device(model).capabilities == legacy.capabilities


def test_undeclared_deviation_is_reported():
    dev = device()
    record = next(r for r in load_oracle("HAIER_AC") if r["state"].get("sleep") == "on")
    with pytest.raises(AssertionError, match="sleep"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("HAIER_AC")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_haier_ac_device.py -q`
Expected: collection error, `ImportError: cannot import name ...` from `pyhvac.plugins.haier`.

- [ ] **Step 3: Implement**: insert immediately before `# Now the match between models and objects` in `pyhvac/plugins/haier.py`:

```python
# ---------------------------------------------------------------- HaierAc
# Layout from IRremoteESP8266's HaierProtocol (ir_Haier.h): one 9-byte frame
# (kHaierACStateLength), sent MSB first. IRsend::sendHaierAC opens with a
# kHaierAcHdr mark and space before sendGeneric's kHaierAcHdr/kHaierAcHdrGap
# header, so the section header holds both pairs.

HAIER_AC = Protocol(
    "haier-ac",
    {
        "main": Section(
            PulseDistance(520, 650, 1650),  # kHaierAcBitMark/ZeroSpace/OneSpace
            header=(3000, 3000, 3000, 4300),  # kHaierAcHdr x3, kHaierAcHdrGap
            footer=(520,),
            gap=150000,  # kHaierAcMinGap
            lsb_first=False,
        ),
    },
    carrier=38000,  # sendHaierAC's enableIROut(38000)
)

HAIER_AC_COMMAND = {  # kHaierAcCmd*: the button the frame says was pressed
    "off": 0b0000,
    "on": 0b0001,
    "mode": 0b0010,
    "fan": 0b0011,
    "temp_up": 0b0110,
    "temp_down": 0b0111,
    "sleep": 0b1000,
    "timer_set": 0b1001,
    "timer_cancel": 0b1010,
    "health": 0b1100,
    "swing": 0b1101,
}
HAIER_AC_MODE = {  # kHaierAc{Auto,Cool,Dry,Heat,Fan}
    "auto": 0,
    "cool": 1,
    "dry": 2,
    "heat": 3,
    "fan": 4,
}
HAIER_AC_FAN = {  # canonical fan -> the raw Fan value IRHaierAC::setFan stores
    "auto": 0,  # kHaierAcFanAuto
    "1": 3,  # kHaierAcFanLow (kLow)
    "2": 2,  # kHaierAcFanMed (kMedium)
    "3": 1,  # kHaierAcFanHigh (kHigh)
}
HAIER_AC_SWING_V = {  # kHaierAcSwingV*, as IRHaierAC::convertSwingV
    "off": 0b00,  # Off (kOff)
    "1": 0b01,  # Up ("auto high" = kHigh)
    "2": 0b10,  # Down ("auto low" = kLow)
    "change": 0b11,  # Chg (kAuto): not offered by the entity
}
HAIER_AC_MIN_TEMP = 16  # kHaierAcMinTemp
HAIER_AC_MAX_TEMP = 30  # kHaierAcMaxTemp

# Skeleton: IRHaierAC::stateReset (memset 0, so no stale bytes) with the
# fields the device always writes (Command, Temp, Fan) and the sum cleared:
# Prefix kHaierAcPrefix, the constant "unknown" bit (byte 2 bit 5) and
# OffHours 12 stay.
HAIER_AC_LAYOUT = Layout(
    bytes.fromhex("a50020000c00000000"),
    {
        "command": Field.at(1, 0, 4, values=HAIER_AC_COMMAND),
        "temperature": Field.at(  # whole °C, minus kHaierAcMinTemp
            1,
            4,
            4,
            values={
                t: t - HAIER_AC_MIN_TEMP
                for t in range(HAIER_AC_MIN_TEMP, HAIER_AC_MAX_TEMP + 1)
            },
        ),
        "curr_hours": Field.at(2, 0, 5),
        "swing_v": Field.at(2, 6, 2, values=HAIER_AC_SWING_V),
        "curr_mins": Field.at(3, 0, 6),
        "off_timer": Field.at(3, 6, 1),
        "on_timer": Field.at(3, 7, 1),
        "off_hours": Field.at(4, 0, 5),
        "health": Field.at(4, 5, 1),
        "off_mins": Field.at(5, 0, 6),
        "fan": Field.at(5, 6, 2, values=HAIER_AC_FAN),
        "on_hours": Field.at(6, 0, 5),
        "mode": Field.at(6, 5, 3, values=HAIER_AC_MODE),
        "on_mins": Field.at(7, 0, 6),
        "sleep": Field.at(7, 6, 1),  # kHaierAcSleepBit
    },
    checksum=Sum8(0, 8, 8),  # IRHaierAC::checksum: sumBytes of bytes 0-7
)


class HaierAcDevice(Device):
    """Haier HSU07-HEA03: a full-state frame that also names a button
    (Command), and ``previous`` is ignored.

    The C path always sends kHaierAcCmdOn or kHaierAcCmdOff: IRac::haier ends
    with setCommand(on ? On : Off), overwriting the Mode/TempUp/TempDown/Fan/
    Swing/Health/Sleep commands its earlier setters wrote, and
    IRac::handleToggles has no HAIER_AC case. So C never picks the button
    from a previous state, and neither does the port. The real remote names
    the key actually pressed (the issue #404/#668 captures carry TempUp,
    TempDown and Health); the port does not invent that rule.
    """

    PROTOCOL = HAIER_AC
    LAYOUTS = (HAIER_AC_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "heat", "fan"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
        ),
        swing_v=Choice(
            ("off", "1", "2"), {"off": "off", "1": "auto high", "2": "auto low"}
        ),
        features={
            "purifier": Choice((False, True), {False: "off", True: "on"}),
            "sleep": Choice((False, True), {False: "off", True: "on"}),
        },
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to kHaierAcAuto).
        mode = target.mode if target.power else "auto"
        temperature = min(
            max(int(target.temperature), HAIER_AC_MIN_TEMP), HAIER_AC_MAX_TEMP
        )
        data = HAIER_AC_LAYOUT.build(
            command="on" if target.power else "off",
            temperature=temperature,
            swing_v=target.swing_v,
            health=target.features.get("purifier", False),  # IRac's filter
            fan=target.fan,
            mode=mode,
            # IRac::haier: setSleep(sleep >= 0). The old glue never passed
            # sleep; the port sends the documented bit (see the tests).
            sleep=target.features.get("sleep", False),
        )
        return [Frame("main", bytes(data))]


HAIER_AC_MODELS = ("HSU07-HEA03 remote", "generic")


DEVICES.update({m: HaierAcDevice for m in HAIER_AC_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_haier_ac_device.py -q`
Expected: 247 passed, 2 skipped (the skips need the C extension).

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/haier.py tests/test_haier_ac_device.py
git add pyhvac/plugins/haier.py tests/test_haier_ac_device.py
git commit -m "HAIER_AC: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 3: HAIER_AC176

One 22-byte burst with two byte sums (local `Haier176Checksum`); layout from `union HaierAc176Protocol`; variants A/B from `HAIER176_MODELS`.

**Files:**
- Modify: `pyhvac/plugins/haier.py` (block before `# Now the match between models and objects`)
- Test: `tests/test_haier176_device.py`

**Interfaces:**
- Consumes: `Device`, `pyhvac.fields`, `tests/port_oracle.py`, and the oracle fixture `HAIER_AC176`.
- Produces: `Haier176Device`, `HAIER176_MODELS`, and the `DEVICES` entries for those models.

- [ ] **Step 1: Write the failing tests**: create `tests/test_haier176_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.fields import Sum8
from pyhvac.ir.codec import decode
from pyhvac.plugins.haier import (
    HAIER176,
    HAIER176_LAYOUT,
    HAIER176_MODELS,
    Haier176Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented Haier176 values here:
# - the old glue (IRGHVAC.build_ircode) has no "sleep" key, so IRac's sleep
#   stays -1 and IRac::haier176's setSleep(sleep >= 0) clears the Sleep bit
#   (byte 8 bit 7). The port sends the documented bit.
DEFECTS = (Defect("sleep", 1, 0, "C glue never passes sleep: bit clear"),)

LEGACY_CLASS = {"A": "Haier176A", "B": "Haier176B"}


def device(model="V9014557 M47 8D remote"):
    return Haier176Device("haier", model)


def device_for(record):
    return device(record["model"])


def with_hswing(record):
    # A record without "hswing" leaves IRac's swingh at kOff, which
    # IRHaierAC176::convertSwingH maps to its default, SwingHMiddle: canonical
    # "3" (checked against the C path in cpath_check.py). The port has no
    # "off" swing_h (the legacy entity has none), so the record is read as
    # "middle".
    if "hswing" in record["state"]:
        return record
    return {**record, "state": {**record["state"], "hswing": "middle"}}


def frame(state, previous=None, model="V9014557 M47 8D remote"):
    dev = device(model)
    if previous is not None:
        previous = dev.normalise(previous)
    (main,) = dev.frames(previous, dev.normalise(state), ())
    return main.data


def read(state, previous=None, model="V9014557 M47 8D remote"):
    return HAIER176_LAYOUT.read(frame(state, previous, model))


@pytest.mark.parametrize("record", oracle_params("HAIER_AC176"))
def test_matches_c_library(record):
    dev = device_for(record)
    assert_matches_oracle(dev, with_hswing(record), dev.LAYOUTS, DEFECTS)


def test_oracle_covers_both_variants():
    models = {r["model"] for r in load_oracle("HAIER_AC176")}
    assert {HAIER176_MODELS[m] for m in models} == {"A", "B"}


def test_layout_round_trips_every_oracle_state():
    for record in load_oracle("HAIER_AC176"):
        dev = device_for(record)
        state = state_from_record(dev, with_hswing(record)["state"])
        (main,) = dev.frames(None, state, ())
        values = HAIER176_LAYOUT.read(main.data)
        assert HAIER176_LAYOUT.build(**values) == bytearray(main.data)


def test_every_oracle_frame_has_both_section_sums():
    # IRHaierAC176::checksum: Sum over bytes 0-12 at 13, Sum2 over 14-20 at 21.
    # portkit checksum only searches the last two bytes, so Sum is pinned here.
    for record in load_oracle("HAIER_AC176"):
        (main,) = decode(HAIER176, record["pulses"], expected=["main"])
        assert Sum8(0, 13, 13).check(main.data)
        assert Sum8(14, 21, 21).check(main.data)
        assert HAIER176_LAYOUT.checksum.check(main.data)


def test_no_field_sits_in_a_checksum_byte():
    sums = HAIER176_LAYOUT.checksum.positions()
    assert sums == {13, 21}
    for name, f in HAIER176_LAYOUT.fields.items():
        assert not {b // 8 for b in f.bits} & sums, name


def test_real_capture_decodes():
    # TestDecodeHaierAC176.RealExample (issue 1480), a real remote: the
    # port's timings decode it to the expected state.
    raw = (
        "3096 2948 3048 4388 588 1610 614 498 586 1612 612 500 612 500 586 1610 "
        "588 1612 612 502 586 1612 612 500 612 500 614 500 612 498 586 1610 586 "
        "1612 612 502 612 500 612 500 612 500 612 500 612 500 612 500 612 500 "
        "612 504 612 500 612 500 612 500 612 500 612 500 612 500 612 500 612 502 "
        "614 498 586 1612 612 500 612 500 612 500 612 500 612 500 612 502 586 "
        "1612 612 500 586 1610 612 500 612 498 612 500 614 478 634 502 612 500 "
        "612 500 612 500 612 500 612 500 612 500 612 498 614 504 612 500 614 500 "
        "586 1612 612 500 612 500 612 500 612 500 612 502 612 500 612 500 612 "
        "500 612 500 612 500 612 500 612 500 612 504 614 500 612 500 612 498 614 "
        "500 612 500 612 500 612 500 612 482 632 500 612 502 610 500 614 500 612 "
        "500 612 500 612 480 632 504 612 480 632 500 612 500 612 480 632 500 612 "
        "500 612 500 612 502 612 500 612 500 612 500 612 500 612 500 586 1612 "
        "612 500 586 1616 612 500 612 500 586 1610 588 1612 612 502 612 500 614 "
        "498 586 1614 586 1612 612 500 586 1610 586 1592 632 498 586 1610 588 "
        "1610 586 1614 614 500 612 480 632 500 612 500 612 500 612 500 614 498 "
        "612 500 614 500 614 500 612 500 612 500 614 498 614 498 614 500 612 504 "
        "612 500 612 500 612 500 612 498 612 502 612 500 614 498 612 502 612 500 "
        "612 498 614 500 612 500 612 500 612 500 612 500 614 502 612 500 614 478 "
        "634 498 614 500 612 500 612 500 612 500 612 482 634 500 612 500 612 500 "
        "612 500 614 498 614 500 612 480 632 502 586 1610 614 478 608 1610 588 "
        "1610 612 498 586 1610 588 1610 586 1606 612"
    )
    pulses = [int(x) for x in raw.split()] + [150000]
    (main,) = decode(HAIER176, pulses, expected=["main"])
    assert main.data == bytes(
        [0xA6, 0x86, 0x00, 0x00, 0x40, 0xA0, 0x00, 0x20, 0x00, 0x00, 0x00]
        + [0x00, 0x05, 0x31, 0xB7, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xB7]
    )
    assert HAIER176_LAYOUT.checksum.check(main.data)


def test_real_model_b_capture_except_its_button():
    # TestHaierAC176Class.Models, "setmodelb": a real V9014557-B message in
    # fan mode, 24 °C, fan low, swing Middle, pressed with the C/F button.
    # The port reproduces it except Button, which IRac always sets to Power.
    capture = bytes(
        [0x59, 0x82, 0x00, 0x00, 0x40, 0x60, 0x00, 0xC0, 0x00, 0x00, 0x00]
        + [0x00, 0x1A, 0x55, 0xB7, 0x00, 0xC0, 0x00, 0x00, 0x00, 0x00, 0x77]
    )
    state = HvacState(True, "fan", 24.0, fan="1", swing_v="2", swing_h="3")
    ours = bytearray(frame(state, model="generic 176 code b"))
    assert HAIER176_LAYOUT.read(ours)["button"] == "power"
    HAIER176_LAYOUT.write_raw(ours, "button", 0b11010)  # kHaierAcYrw02ButtonCFAB
    HAIER176_LAYOUT.checksum.apply(ours)
    assert bytes(ours) == capture


@pytest.mark.parametrize(
    "model, variant, byte0",
    [
        ("V9014557 M47 8D remote", "A", 0xA6),
        ("Daichi D-H", "A", 0xA6),
        ("generic 176 code a", "A", 0xA6),
        ("generic 176 code b", "B", 0x59),
    ],
)
def test_variant_comes_from_the_model(model, variant, byte0):
    assert device(model).variant == variant
    assert frame(HvacState(True, "cool", 22.0), model=model)[0] == byte0


def test_unknown_model_gets_variant_a_and_bad_variant_raises():
    assert Haier176Device("haier", "whatever").variant == "A"
    assert Haier176Device("haier", "whatever", variant="B").variant == "B"
    with pytest.raises(ValueError):
        Haier176Device("haier", "whatever", variant="C")


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat", "fan"])
@pytest.mark.parametrize("temp", [16.0, 23.0, 30.0])
def test_off_carries_mode_auto_in_every_mode(mode, temp):
    # IRac passes mode "off"; IRHaierAC176::convertMode maps it to auto.
    values = read(HvacState(False, mode, temp, fan="3"))
    assert (values["power"], values["mode"], values["temperature"]) == (
        0,
        "auto",
        int(temp),
    )
    assert values["fan"] == "3"
    assert values["button"] == "power"


def test_setpoint_is_clamped_to_16_30():
    assert read(HvacState(True, "cool", 10.0))["temperature"] == 16
    assert read(HvacState(True, "heat", 40.0))["temperature"] == 30


@pytest.mark.parametrize("temp", range(16, 31))
def test_every_setpoint(temp):
    assert frame(HvacState(True, "cool", float(temp)))[1] >> 4 == temp - 16


@pytest.mark.parametrize(
    "fan, raw, fan2",
    [("auto", 5, 0), ("1", 3, 3), ("2", 2, 2), ("3", 1, 1)],
)
@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat", "fan"])
def test_every_fan_level_and_fan2(mode, fan, raw, fan2):
    # setFan: Fan2 is 0 for FanAuto, otherwise the Fan code; no mode limits.
    data = frame(HvacState(True, mode, 24.0, fan=fan))
    assert HAIER176_LAYOUT.read_raw(data, "fan") == raw
    assert HAIER176_LAYOUT.read_raw(data, "fan2") == fan2


@pytest.mark.parametrize(
    "swing, other, heat",
    [
        ("off", 0x0, 0x0),
        ("auto", 0xC, 0xC),
        ("1", 0x1, 0x1),  # ceiling: Top
        ("2", 0x2, 0x3),  # 45°: Middle, Bottom in heat
        ("3", 0xA, 0xA),  # 30°: Down
        ("4", 0x2, 0x3),  # 0°: Bottom, only in heat, else Middle
    ],
)
def test_swing_v_per_mode(swing, other, heat):
    for mode in ("auto", "cool", "dry", "fan"):
        data = frame(HvacState(True, mode, 24.0, swing_v=swing))
        assert HAIER176_LAYOUT.read_raw(data, "swing_v") == other, mode
    data = frame(HvacState(True, "heat", 24.0, swing_v=swing))
    assert HAIER176_LAYOUT.read_raw(data, "swing_v") == heat
    # An off message carries mode auto, so heat's Bottom becomes Middle.
    data = frame(HvacState(False, "heat", 24.0, swing_v=swing))
    assert HAIER176_LAYOUT.read_raw(data, "swing_v") == other


@pytest.mark.parametrize(
    "swing_h, raw",
    [("auto", 7), ("1", 3), ("2", 4), ("3", 0), ("4", 5), ("5", 6)],
)
def test_every_swing_h_value(swing_h, raw):
    data = frame(HvacState(True, "cool", 22.0, swing_h=swing_h))
    assert HAIER176_LAYOUT.read_raw(data, "swing_h") == raw


@pytest.mark.parametrize(
    "mode, powerful, quiet, turbo_bit, quiet_bit",
    [
        ("cool", True, False, 1, 0),
        ("cool", False, True, 0, 1),
        ("cool", True, True, 1, 0),  # setTurbo(true) comes last, clears quiet
        ("heat", True, False, 1, 0),
        ("heat", False, True, 0, 1),
        ("heat", True, True, 1, 0),
        ("auto", True, True, 0, 0),  # only in cool and heat
        ("dry", True, True, 0, 0),
        ("fan", True, True, 0, 0),
    ],
)
def test_turbo_and_quiet_only_in_cool_and_heat(
    mode, powerful, quiet, turbo_bit, quiet_bit
):
    features = {"powerful": powerful, "quiet": quiet}
    values = read(HvacState(True, mode, 24.0, features=features))
    assert (values["turbo"], values["quiet"]) == (turbo_bit, quiet_bit)
    off = read(HvacState(False, mode, 24.0, features=features))
    assert (off["turbo"], off["quiet"]) == (0, 0)  # an off message is in auto


@pytest.mark.parametrize("mode", ["auto", "cool", "heat"])
def test_purifier_sets_health_in_every_mode(mode):
    assert read(HvacState(True, mode, 24.0))["health"] == 0
    on = HvacState(True, mode, 24.0, features={"purifier": True})
    assert read(on)["health"] == 1
    off = HvacState(False, mode, 24.0, features={"purifier": True})
    assert read(off)["health"] == 1


def test_sleep_sends_the_documented_bit():
    assert read(HvacState(True, "cool", 24.0))["sleep"] == 0
    on = HvacState(True, "cool", 24.0, features={"sleep": True})
    assert read(on)["sleep"] == 1
    assert frame(on)[8] == 0x80


@pytest.mark.parametrize("power", [True, False])
@pytest.mark.parametrize("mode", ["auto", "cool", "heat"])
def test_button_is_always_power(power, mode):
    state = HvacState(
        power,
        mode,
        24.0,
        fan="2",
        swing_v="1",
        swing_h="2",
        features={"purifier": True, "powerful": True, "sleep": True},
    )
    assert read(state)["button"] == "power"
    assert frame(state)[12] == 0x05


def test_previous_is_ignored():
    # No toggle bits: IRac::handleToggles has no Haier case and
    # IRac::haier176 takes no previous state.
    dev = device()
    target = HvacState(True, "cool", 22.0, swing_v="auto", swing_h="1")
    for previous in (
        None,
        target,
        HvacState(False, "heat", 30.0),
        HvacState(True, "cool", 22.0, swing_v="off", swing_h="auto"),
    ):
        assert dev.encode(previous, target).signal == dev.encode(None, target).signal


def test_skeleton_is_the_reset_state():
    # The oracle's first record: off, 16 °C, fan auto, swing off (hswing
    # absent: Middle).
    record = load_oracle("HAIER_AC176")[0]
    assert record["state"] == {
        "mode": "off",
        "temperature": 16,
        "fan": "auto",
        "swing": "off",
    }
    (main,) = decode(HAIER176, record["pulses"], expected=["main"])
    data = HAIER176_LAYOUT.build(
        model="A", fan="auto", mode="auto", button="power", swing_h="3"
    )
    assert bytes(data) == main.data


def test_message_shape():
    dev = device()
    pulses = dev.encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:4] == (3000, 3000, 3000, 4300)
    assert pulses[-2:] == (520, 150000)
    assert len(pulses) == 4 + 2 * 176 + 2
    assert dev.encode(None, HvacState(True, "cool", 22.0)).signal.carrier == 38000


@pytest.mark.parametrize("model", HAIER176_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("haier", model), Haier176Device)


@pytest.mark.parametrize("model", HAIER176_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins import haier

    cls = getattr(haier, LEGACY_CLASS[HAIER176_MODELS[model]])
    legacy = LegacyDevice("haier", model, cls)
    assert Haier176Device("haier", model).capabilities == legacy.capabilities


def test_undeclared_deviation_is_reported():
    record = next(
        r for r in load_oracle("HAIER_AC176") if r["state"].get("sleep") == "on"
    )
    dev = device_for(record)
    with pytest.raises(AssertionError, match="sleep"):
        assert_matches_oracle(dev, with_hswing(record), dev.LAYOUTS, defects=())


def test_missing_hswing_is_not_silently_accepted():
    # Read as "auto" (the entity's first value), a record without hswing
    # would differ from C's Middle: the rewrite in with_hswing is needed.
    record = next(r for r in load_oracle("HAIER_AC176") if "hswing" not in r["state"])
    dev = device_for(record)
    with pytest.raises(AssertionError, match="swing_h"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layouts_must_cover_every_frame():
    record = load_oracle("HAIER_AC176")[0]
    dev = device_for(record)
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, with_hswing(record), (), DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_haier176_device.py -q`
Expected: collection error, `ImportError: cannot import name ...` from `pyhvac.plugins.haier`.

- [ ] **Step 3: Implement**: insert immediately before `# Now the match between models and objects` in `pyhvac/plugins/haier.py`:

```python
# ------------------------------------------------------------- Haier176
# Layout from IRremoteESP8266's HaierAc176Protocol (ir_Haier.h): 22 bytes,
# each sent MSB first (sendHaierAC: sendGeneric with MSBfirst), in one burst.
# The message opens with a kHaierAcHdr mark and space, then the
# kHaierAcHdr/kHaierAcHdrGap header; bits kHaierAcBitMark/ZeroSpace/OneSpace,
# closed by kHaierAcMinGap; carrier 38 kHz. Bytes 0-13 are the YRW02 section
# (checksum Sum, byte 13), bytes 14-21 the 176-only section (Sum2, byte 21).

HAIER176 = Protocol(
    "haier176",
    {
        "main": Section(
            PulseDistance(520, 650, 1650),  # kHaierAcBitMark/ZeroSpace/OneSpace
            header=(3000, 3000, 3000, 4300),  # kHaierAcHdr x3, kHaierAcHdrGap
            footer=(520,),
            gap=150000,  # kHaierAcMinGap
            lsb_first=False,
        )
    },
    carrier=38000,
)


@dataclass(frozen=True)
class Haier176Checksum:
    """IRHaierAC176::checksum: two byte sums, one per section.

    Sum (byte 13) = sumBytes(raw[0:13]); Sum2 (byte 21) = sumBytes(raw[14:21]).
    """

    parts: tuple = (Sum8(0, 13, 13), Sum8(14, 21, 21))

    def positions(self):
        return {p.at for p in self.parts}

    def apply(self, data):
        for p in self.parts:
            p.apply(data)

    def check(self, data):
        return all(p.check(data) for p in self.parts)


HAIER176_MODEL = {"A": 0xA6, "B": 0x59}  # kHaierAcYrw02ModelA/B
HAIER176_BUTTON = {  # kHaierAcYrw02Button*
    "temp_up": 0b00000,
    "temp_down": 0b00001,
    "swing_v": 0b00010,
    "swing_h": 0b00011,
    "fan": 0b00100,
    "power": 0b00101,
    "mode": 0b00110,
    "health": 0b00111,
    "turbo": 0b01000,
    "sleep": 0b01011,
    "timer": 0b10000,
    "lock": 0b10100,
    "cfab": 0b11010,
}
HAIER176_MODE = {  # kHaierAcYrw02*
    "auto": 0b000,
    "cool": 0b001,
    "dry": 0b010,
    "heat": 0b100,
    "fan": 0b110,
}
HAIER176_FAN = {  # canonical fan -> kHaierAcYrw02Fan*
    "auto": 0b101,  # FanAuto
    "1": 0b011,  # low: FanLow
    "2": 0b010,  # medium: FanMed
    "3": 0b001,  # high: FanHigh
}
HAIER176_SWING_V = {  # canonical swing -> kHaierAcYrw02SwingV*, top to bottom
    "off": 0x0,  # SwingVOff
    "auto": 0xC,  # SwingVAuto (airflow)
    "1": 0x1,  # ceiling: SwingVTop
    "2": 0x2,  # 45°: SwingVMiddle (not available in heat mode)
    "3": 0xA,  # 30°: SwingVDown
    "4": 0x3,  # 0°: SwingVBottom (only available in heat mode)
}
HAIER176_SWING_H = {  # canonical position -> kHaierAcYrw02SwingH*
    "auto": 0x7,  # SwingHAuto
    "1": 0x3,  # far left: SwingHLeftMax
    "2": 0x4,  # left: SwingHLeft
    "3": 0x0,  # middle: SwingHMiddle
    "4": 0x5,  # right: SwingHRight
    "5": 0x6,  # far right: SwingHRightMax
}
HAIER176_MIN_TEMP, HAIER176_MAX_TEMP = 16, 30  # kHaierAcYrw02Min/MaxTempC

# Skeleton: IRHaierAC176::stateReset (all zero, then Prefix2 = kHaierAc176Prefix)
# with every written field cleared. Timers, Lock and the unnamed bits stay 0:
# stateReset zeroes the whole state, so there is no stale memory.
HAIER176_LAYOUT = Layout(
    bytes(14) + bytes([0xB7]) + bytes(7),
    {
        "model": Field.at(0, 0, 8, values=HAIER176_MODEL),
        "swing_v": Field.at(1, 0, 4, values=HAIER176_SWING_V),
        "temperature": Field.at(  # Temp: celsius - kHaierAcYrw02MinTempC
            1,
            4,
            4,
            values={
                t: t - HAIER176_MIN_TEMP
                for t in range(HAIER176_MIN_TEMP, HAIER176_MAX_TEMP + 1)
            },
        ),
        "swing_h": Field.at(2, 5, 3, values=HAIER176_SWING_H),
        "health": Field.at(3, 1, 1),
        "timer_mode": Field.at(3, 5, 3),
        "power": Field.at(4, 6, 1),
        "off_timer_hrs": Field.at(5, 0, 5),
        "fan": Field.at(5, 5, 3, values=HAIER176_FAN),
        "off_timer_mins": Field.at(6, 0, 6),
        "turbo": Field.at(6, 6, 1),
        "quiet": Field.at(6, 7, 1),
        "on_timer_hrs": Field.at(7, 0, 5),
        "mode": Field.at(7, 5, 3, values=HAIER176_MODE),
        "on_timer_mins": Field.at(8, 0, 6),
        "sleep": Field.at(8, 7, 1),
        "extra_degree_f": Field.at(10, 0, 1),
        "use_fahrenheit": Field.at(10, 5, 1),
        "button": Field.at(12, 0, 5, values=HAIER176_BUTTON),
        "lock": Field.at(12, 5, 1),
        "prefix2": Field.at(14, 0, 8),  # kHaierAc176Prefix
        # Fan2: 0 for auto (kHaierAcYrw02FanAuto), else the Fan code.
        "fan2": Field.at(16, 6, 2),
    },
    checksum=Haier176Checksum(),
)


class Haier176Device(Device):
    """Haier 176-bit (V9014557 remote, variants A and B): full state.

    The variant ("A" or "B", haier_ac176_remote_model_t V9014557_A/B) comes
    from the model (HAIER176_MODELS) unless given, so the registry's
    ``cls(brand, model)`` call picks it; unknown models get A, as
    IRHaierAC176::setModel does.

    ``previous`` is ignored. The frame carries every setting as state; the
    only "which key" field, Button (byte 12), is kHaierAcYrw02ButtonPower in
    every C message: IRac::haier176 calls setPower last, and each setter
    overwrites Button. IRac::handleToggles has no Haier case and
    IRac::haier176 takes no previous state, so the C path never uses one.
    """

    PROTOCOL = HAIER176
    LAYOUTS = (HAIER176_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "heat", "fan"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
        ),
        swing_v=Choice(
            ("off", "auto", "1", "2", "3", "4"),
            {
                "off": "off",
                "auto": "auto",
                "1": "ceiling",
                "2": "45°",
                "3": "30°",
                "4": "0°",
            },
        ),
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
        features={
            "purifier": Choice((False, True), {False: "off", True: "on"}),
            "sleep": Choice((False, True), {False: "off", True: "on"}),
            "powerful": Choice((False, True), {False: "off", True: "on"}),
            "quiet": Choice((False, True), {False: "off", True: "on"}),
        },
    )

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        self.variant = variant or HAIER176_MODELS.get(model, "A")
        if self.variant not in HAIER176_MODEL:
            raise ValueError(f"unknown Haier176 variant {self.variant!r}")

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to its default, auto).
        mode = target.mode if target.power else "auto"
        # setTurbo/setQuiet only act in cool and heat (setMode clears both in
        # the other modes); IRac calls setQuiet then setTurbo, and turbo on
        # clears quiet.
        boost = mode in ("cool", "heat")
        turbo = boost and target.features["powerful"]
        quiet = boost and target.features["quiet"] and not turbo
        # setSwingV (after setMode): heat has no Middle, it uses Bottom;
        # Bottom only exists in heat, the other modes use Middle.
        swing_v = target.swing_v
        if mode == "heat" and swing_v == "2":
            swing_v = "4"
        elif mode != "heat" and swing_v == "4":
            swing_v = "2"
        fan = HAIER176_FAN[target.fan]
        data = HAIER176_LAYOUT.build(
            model=self.variant,
            swing_v=swing_v,
            temperature=target.temperature,
            swing_h=target.swing_h,
            health=target.features["purifier"],  # setHealth(filter)
            power=target.power,
            fan=target.fan,
            fan2=0 if fan == HAIER176_FAN["auto"] else fan,
            turbo=turbo,
            quiet=quiet,
            mode=mode,
            # The documented Sleep bit. The C path never sets it: the old
            # glue's key map has no "sleep" (declared as a Defect).
            sleep=target.features["sleep"],
            # IRac::haier176 calls setPower last: Button is always Power.
            button="power",
            prefix2=0xB7,  # kHaierAc176Prefix
        )
        return [Frame("main", bytes(data))]


HAIER176_MODELS = {  # model -> remote variant (haier_ac176_remote_model_t)
    "V9014557 M47 8D remote": "A",
    "Daichi D-H": "A",
    "generic 176 code a": "A",
    "generic 176 code b": "B",
}


DEVICES.update({m: Haier176Device for m in HAIER176_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_haier176_device.py -q`
Expected: 503 passed, 4 skipped (the skips need the C extension).

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/haier.py tests/test_haier176_device.py
git add pyhvac/plugins/haier.py tests/test_haier176_device.py
git commit -m "HAIER_AC176: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 4: HAIER_AC_YRW02

One 14-byte frame (the first section of `union HaierAc176Protocol`), `Sum8(0, 13, 13)`; variants A/B from `HAIER_YRW02_MODELS`.

**Files:**
- Modify: `pyhvac/plugins/haier.py` (block before `# Now the match between models and objects`)
- Test: `tests/test_haier_yrw02_device.py`

**Interfaces:**
- Consumes: `Device`, `pyhvac.fields`, `tests/port_oracle.py`, and the oracle fixture `HAIER_AC_YRW02`.
- Produces: `HaierYrw02Device`, `HAIER_YRW02_MODELS`, and the `DEVICES` entries for those models.

- [ ] **Step 1: Write the failing tests**: create `tests/test_haier_yrw02_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.fields import Sum8
from pyhvac.ir.codec import decode
from pyhvac.plugins.haier import (
    HAIER_YRW02,
    HAIER_YRW02_LAYOUT,
    HAIER_YRW02_MODELS,
    HaierYrw02Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented HaierAc176Protocol values here:
# - model: IRac::haierYrwo2, unlike IRac::haier176, never calls setModel, so
#   every message carries stateReset's kHaierAcYrw02ModelA (0xA6), variant B
#   included. The port sends kHaierAcYrw02ModelB (0x59) for variant B;
# - sleep: IRGHVAC.build_ircode's key map has no "sleep", so IRac's sleep
#   stays -1 and setSleep(sleep >= 0) never sets Sleep (byte 8 bit 7).
# kHaierAcYrw02ModelB = 0x59; the real V9014557-B capture "setmodelb" in
# IRremoteESP8266's test/ir_Haier_test.cpp has byte 0 = 0x59.
MODEL_B = Defect("model", "B", "A", "IRac::haierYrwo2 never calls setModel")
SLEEP = Defect("sleep", 1, 0, "legacy glue never passes sleep")
DEFECTS = (MODEL_B, SLEEP)

# ir_Haier_test.cpp, TestDecodeHaierAC_YRW02.RealExample (issue #485): power
# on, cool, 17 C, fan high, swing(V) Middle, swing(H) Middle, health on,
# button Power.
REAL_EXAMPLE = bytes.fromhex("a61200024020002000000000053f")
# Its raw capture (rawData, 229 durations, ending on the footer mark).
REAL_CAPTURE = (
    2998,
    3086,
    2998,
    4460,
    568,
    1640,
    596,
    492,
    514,
    1690,
    590,
    496,
    566,
    532,
    592,
    1596,
    570,
    1618,
    518,
    584,
    590,
    538,
    524,
    536,
    568,
    532,
    590,
    1596,
    516,
    612,
    568,
    538,
    522,
    1638,
    586,
    500,
    512,
    614,
    568,
    538,
    520,
    538,
    586,
    538,
    566,
    540,
    520,
    538,
    586,
    538,
    522,
    538,
    588,
    538,
    568,
    538,
    520,
    538,
    586,
    538,
    566,
    538,
    520,
    540,
    588,
    1596,
    590,
    536,
    568,
    538,
    520,
    1592,
    640,
    538,
    520,
    540,
    588,
    538,
    568,
    538,
    516,
    562,
    566,
    538,
    518,
    542,
    586,
    540,
    566,
    1596,
    590,
    538,
    566,
    538,
    516,
    544,
    586,
    538,
    516,
    542,
    588,
    540,
    564,
    540,
    468,
    590,
    588,
    538,
    566,
    540,
    466,
    590,
    588,
    538,
    514,
    544,
    588,
    538,
    566,
    538,
    468,
    1692,
    606,
    526,
    466,
    592,
    588,
    538,
    568,
    490,
    588,
    538,
    566,
    540,
    466,
    592,
    588,
    538,
    566,
    538,
    466,
    592,
    588,
    538,
    568,
    492,
    586,
    540,
    566,
    540,
    468,
    590,
    588,
    538,
    568,
    516,
    488,
    590,
    588,
    538,
    568,
    492,
    588,
    538,
    566,
    518,
    488,
    590,
    588,
    540,
    564,
    518,
    490,
    590,
    588,
    538,
    562,
    496,
    588,
    538,
    566,
    518,
    488,
    590,
    588,
    538,
    562,
    522,
    488,
    588,
    590,
    538,
    560,
    498,
    588,
    540,
    564,
    522,
    486,
    590,
    590,
    538,
    560,
    524,
    488,
    588,
    588,
    1598,
    514,
    608,
    564,
    1600,
    548,
    536,
    586,
    538,
    568,
    1594,
    590,
    1618,
    578,
    1606,
    606,
    1582,
    590,
    1596,
    590,
    1616,
    580,
)


def device(model="YR-W02 remote"):
    return HaierYrw02Device("haier", model)


def with_hswing(record):
    # A record without "hswing" leaves IRac's swingh at kOff, which
    # convertSwingH sends as kHaierAcYrw02SwingHMiddle (0). The legacy entity
    # has no "off" swing_h; its "middle" (canonical "3") is the value the C
    # path sends as 0, so the record is read as "middle" (checked against
    # the C path in cpath_check.py).
    if "hswing" in record["state"]:
        return record
    return {**record, "state": {**record["state"], "hswing": "middle"}}


def _device_for(record):
    return HaierYrw02Device("haier", record["model"])


def frame(state, previous=None, dev=None):
    dev = dev or device()
    if previous is not None:
        previous = dev.normalise(previous)
    (main,) = dev.frames(previous, dev.normalise(state), ())
    return main.data


def read(state, previous=None, dev=None):
    return HAIER_YRW02_LAYOUT.read(frame(state, previous, dev))


@pytest.mark.parametrize("record", oracle_params("HAIER_AC_YRW02"))
def test_matches_c_library(record):
    dev = _device_for(record)
    assert_matches_oracle(dev, with_hswing(record), dev.LAYOUTS, DEFECTS)


def test_oracle_covers_both_variants():
    classes = {(r["class"], r["variant"]) for r in load_oracle("HAIER_AC_YRW02")}
    assert classes == {("HaierYRW02A", "1"), ("HaierYRW02B", "2")}
    for record in load_oracle("HAIER_AC_YRW02"):
        expected = {"HaierYRW02A": "A", "HaierYRW02B": "B"}[record["class"]]
        assert _device_for(record).variant == expected


def test_layout_round_trips_every_oracle_state():
    for record in load_oracle("HAIER_AC_YRW02"):
        dev = _device_for(record)
        state = state_from_record(dev, with_hswing(record)["state"])
        (main,) = dev.frames(None, state, ())
        values = HAIER_YRW02_LAYOUT.read(main.data)
        assert HAIER_YRW02_LAYOUT.build(**values) == bytearray(main.data)


def test_checksum_is_the_sum_of_bytes_0_to_12():
    # IRHaierAC176::checksum: Sum = sumBytes(raw, kHaierACYRW02StateLength - 1).
    for record in load_oracle("HAIER_AC_YRW02"):
        (main,) = decode(HAIER_YRW02, record["pulses"], expected=["main"])
        assert Sum8(0, 13, 13).check(main.data)


def test_reproduces_the_upstream_real_example():
    state = HvacState(
        True,
        "cool",
        17.0,
        fan="3",
        swing_v="2",
        swing_h="3",
        features={"purifier": True},
    )
    assert frame(state) == REAL_EXAMPLE
    assert HAIER_YRW02_LAYOUT.checksum.check(REAL_EXAMPLE)


def test_decodes_the_upstream_real_capture():
    (main,) = decode(HAIER_YRW02, REAL_CAPTURE, expected=["main"])
    assert main.data == REAL_EXAMPLE


def test_model_byte_follows_the_variant():
    assert frame(HvacState(True, "cool", 22.0))[0] == 0xA6
    dev_b = device("YR-W02 Code B")
    assert frame(HvacState(True, "cool", 22.0), dev=dev_b)[0] == 0x59
    explicit = HaierYrw02Device("haier", "YR-W02 remote", variant="B")
    assert read(HvacState(True, "cool", 22.0), dev=explicit)["model"] == "B"
    assert HaierYrw02Device("haier", "unknown").variant == "A"
    with pytest.raises(ValueError):
        HaierYrw02Device("haier", "x", variant="C")


def test_every_model_maps_to_its_variant():
    assert HAIER_YRW02_MODELS == {
        "YR-W02 remote": "A",
        "HSU-09HMC203": "A",
        "YR-W02 Code A": "A",
        "YR-W02 Code B": "B",
    }
    for model, variant in HAIER_YRW02_MODELS.items():
        assert device(model).variant == variant


@pytest.mark.parametrize("t", range(16, 31))
def test_temperature_is_offset_from_16(t):
    data = frame(HvacState(True, "cool", float(t)))
    assert data[1] >> 4 == t - 16
    assert read(HvacState(True, "cool", float(t)))["temperature"] == t


def test_setpoint_is_clamped_to_16_30():
    assert read(HvacState(True, "cool", 10.0))["temperature"] == 16
    assert read(HvacState(True, "heat", 40.0))["temperature"] == 30


@pytest.mark.parametrize("mode", ("auto", "cool", "dry", "heat", "fan"))
@pytest.mark.parametrize("t", (16.0, 23.0, 30.0))
def test_off_carries_mode_auto_and_the_setpoint(mode, t):
    # IRac passes mode "off"; convertMode maps it to auto. setTemp still runs.
    values = read(HvacState(False, mode, t, fan="2"))
    assert (values["power"], values["mode"], values["temperature"]) == (
        0,
        "auto",
        int(t),
    )
    assert values["fan"] == "2"
    assert values["button"] == "power"


@pytest.mark.parametrize(
    "mode, raw", [("auto", 0), ("cool", 1), ("dry", 2), ("heat", 4), ("fan", 6)]
)
def test_every_mode_uses_its_documented_value(mode, raw):
    data = frame(HvacState(True, mode, 22.0))
    assert HAIER_YRW02_LAYOUT.read_raw(data, "mode") == raw
    assert HAIER_YRW02_LAYOUT.read(data)["power"] == 1


@pytest.mark.parametrize("fan, raw", [("auto", 5), ("1", 3), ("2", 2), ("3", 1)])
@pytest.mark.parametrize("mode", ("auto", "cool", "dry", "heat", "fan"))
def test_every_fan_level_in_every_mode(mode, fan, raw):
    # IRHaierAC176::setFan has no per-mode limit.
    data = frame(HvacState(True, mode, 22.0, fan=fan))
    assert HAIER_YRW02_LAYOUT.read_raw(data, "fan") == raw


@pytest.mark.parametrize(
    "swing, mode, raw",
    [
        ("off", "cool", 0x0),
        ("auto", "cool", 0xC),
        ("1", "cool", 0x1),  # ceiling: Top
        ("2", "cool", 0x2),  # 45°: Middle
        ("3", "cool", 0xA),  # 30°: Down
        ("4", "cool", 0x2),  # 0°: Bottom is heat only, Middle instead
        ("1", "heat", 0x1),
        ("2", "heat", 0x3),  # heat has no Middle, Bottom instead
        ("3", "heat", 0xA),
        ("4", "heat", 0x3),
        ("auto", "heat", 0xC),
    ],
)
def test_swing_v_positions_and_the_heat_rule(swing, mode, raw):
    data = frame(HvacState(True, mode, 22.0, swing_v=swing))
    assert HAIER_YRW02_LAYOUT.read_raw(data, "swing_v") == raw


def test_swing_v_in_an_off_message_follows_mode_auto():
    assert read(HvacState(False, "heat", 22.0, swing_v="4"))["swing_v"] == "middle"


@pytest.mark.parametrize(
    "swing, raw",
    [("auto", 7), ("1", 3), ("2", 4), ("3", 0), ("4", 5), ("5", 6)],
)
def test_swing_h_positions(swing, raw):
    data = frame(HvacState(True, "cool", 22.0, swing_h=swing))
    assert HAIER_YRW02_LAYOUT.read_raw(data, "swing_h") == raw


@pytest.mark.parametrize("mode", ("cool", "heat"))
def test_turbo_and_quiet_in_cool_and_heat(mode):
    def feats(powerful, quiet):
        values = read(
            HvacState(True, mode, 22.0, features={"powerful": powerful, "quiet": quiet})
        )
        return values["turbo"], values["quiet"]

    assert feats(False, False) == (0, 0)
    assert feats(True, False) == (1, 0)
    assert feats(False, True) == (0, 1)
    assert feats(True, True) == (1, 0)  # setTurbo(true) after setQuiet clears it


@pytest.mark.parametrize("mode", ("auto", "dry", "fan"))
def test_turbo_and_quiet_only_in_cool_and_heat(mode):
    values = read(
        HvacState(True, mode, 22.0, features={"powerful": True, "quiet": True})
    )
    assert (values["turbo"], values["quiet"]) == (0, 0)


def test_turbo_and_quiet_in_an_off_message_follow_mode_auto():
    values = read(
        HvacState(False, "cool", 22.0, features={"powerful": True, "quiet": True})
    )
    assert (values["turbo"], values["quiet"]) == (0, 0)


@pytest.mark.parametrize("power", (True, False))
@pytest.mark.parametrize("mode", ("auto", "cool", "dry", "heat", "fan"))
def test_health_follows_purifier_in_every_mode(mode, power):
    on = HvacState(power, mode, 22.0, features={"purifier": True})
    assert read(on)["health"] == 1
    assert read(HvacState(power, mode, 22.0))["health"] == 0


@pytest.mark.parametrize("power", (True, False))
@pytest.mark.parametrize("mode", ("auto", "cool", "dry", "heat", "fan"))
def test_sleep_bit_in_every_mode(mode, power):
    # Documented Sleep bit (declared Defect: the C path never sets it).
    data = frame(HvacState(power, mode, 22.0, features={"sleep": True}))
    assert data[8] == 0x80
    assert frame(HvacState(power, mode, 22.0))[8] == 0x00


def test_timers_lock_and_units_stay_clear():
    values = read(
        HvacState(
            True,
            "heat",
            30.0,
            fan="3",
            swing_v="auto",
            swing_h="auto",
            features={"purifier": True, "sleep": True, "powerful": True},
        )
    )
    for key in (
        "timer_mode",
        "off_timer_hrs",
        "off_timer_mins",
        "on_timer_hrs",
        "on_timer_mins",
        "extra_degree_f",
        "use_fahrenheit",
        "lock",
    ):
        assert values[key] == 0, key


def test_button_is_always_power():
    # IRac::haierYrwo2 calls setPower last on a fresh object.
    for state in (
        HvacState(True, "cool", 22.0),
        HvacState(False, "heat", 30.0),
        HvacState(True, "heat", 16.0, fan="1", swing_v="1", swing_h="1"),
        HvacState(True, "cool", 25.0, features={"sleep": True, "powerful": True}),
    ):
        assert frame(state)[12] == 0x05


@pytest.mark.parametrize(
    "before",
    [
        HvacState(False, "cool", 22.0),
        HvacState(True, "heat", 25.0, fan="3", swing_v="auto"),
        HvacState(True, "cool", 22.0, features={"sleep": True}),
    ],
)
def test_previous_is_ignored(before):
    # No toggle bits, and IRac::sendAc/handleToggles use no previous state
    # for HAIER_AC_YRW02.
    target = HvacState(True, "cool", 22.0, swing_v="2")
    assert frame(target, before) == frame(target)
    dev = device()
    assert dev.encode(before, target).signal == dev.encode(None, target).signal


def test_message_shape():
    dev = device()
    pulses = dev.encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:4] == (3000, 3000, 3000, 4300)
    assert pulses[-2:] == (520, 150000)
    assert len(pulses) == 4 + 2 * 112 + 2


@pytest.mark.parametrize("model", HAIER_YRW02_MODELS)
def test_registry_serves_the_port(model):
    dev = registry.get_device("haier", model)
    assert isinstance(dev, HaierYrw02Device)
    assert dev.variant == HAIER_YRW02_MODELS[model]


@pytest.mark.parametrize("model", HAIER_YRW02_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.haier import PluginObject

    legacy = LegacyDevice("haier", model, PluginObject.MODELS[model])
    assert HaierYrw02Device("haier", model).capabilities == legacy.capabilities


def _first(pred):
    return next(r for r in load_oracle("HAIER_AC_YRW02") if pred(r))


@pytest.mark.parametrize(
    "pred, field",
    [
        (lambda r: r["class"] == "HaierYRW02B", "model"),
        (lambda r: r["state"].get("sleep") == "on", "sleep"),
    ],
)
def test_undeclared_deviation_is_reported(pred, field):
    record = with_hswing(_first(pred))
    dev = _device_for(record)
    with pytest.raises(AssertionError, match=field):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_layouts_must_cover_every_frame():
    record = with_hswing(load_oracle("HAIER_AC_YRW02")[0])
    dev = _device_for(record)
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_haier_yrw02_device.py -q`
Expected: collection error, `ImportError: cannot import name ...` from `pyhvac.plugins.haier`.

- [ ] **Step 3: Implement**: insert immediately before `# Now the match between models and objects` in `pyhvac/plugins/haier.py`:

```python
# ------------------------------------------------------------ HaierYrw02
# Layout from IRremoteESP8266's HaierAc176Protocol (ir_Haier.h): the YR-W02
# message is its first 14 bytes (kHaierACYRW02StateLength; IRHaierACYRW02
# derives from IRHaierAC176), each sent MSB first (sendHaierAC: sendGeneric
# with MSBfirst). sendHaierAC opens with a kHaierAcHdr mark and space before
# sendGeneric's kHaierAcHdr/kHaierAcHdrGap header; bits kHaierAcBitMark/
# ZeroSpace/OneSpace, gap kHaierAcMinGap, 38 kHz, no repeat
# (kHaierAcYrw02DefaultRepeat = kNoRepeat).

HAIER_YRW02 = Protocol(
    "haier_yrw02",
    {
        "main": Section(
            PulseDistance(520, 650, 1650),
            header=(3000, 3000, 3000, 4300),
            footer=(520,),
            gap=150000,
            lsb_first=False,
        )
    },
    carrier=38000,
)

HAIER_YRW02_BUTTON = {  # kHaierAcYrw02Button*
    "temp_up": 0b00000,
    "temp_down": 0b00001,
    "swing_v": 0b00010,
    "swing_h": 0b00011,
    "fan": 0b00100,
    "power": 0b00101,
    "mode": 0b00110,
    "health": 0b00111,
    "turbo": 0b01000,
    "sleep": 0b01011,
    "timer": 0b10000,
    "lock": 0b10100,
    "cfab": 0b11010,
}
HAIER_YRW02_SWING_V = {  # kHaierAcYrw02SwingV*
    "off": 0x0,
    "top": 0x1,
    "middle": 0x2,  # not available in heat mode
    "bottom": 0x3,  # only available in heat mode
    "down": 0xA,
    "auto": 0xC,
}
# Canonical swing_v -> documented position, from the top down (Top, Middle,
# Down, Bottom: IRHaierAC176::toCommonSwingV's Highest, Middle, Low, Lowest).
HAIER_YRW02_SWING_V_POSITION = {
    "off": "off",
    "auto": "auto",
    "1": "top",
    "2": "middle",
    "3": "down",
    "4": "bottom",
}
HAIER_YRW02_SWING_H = {  # kHaierAcYrw02SwingH*
    "middle": 0x0,
    "left_max": 0x3,
    "left": 0x4,
    "right": 0x5,
    "right_max": 0x6,
    "auto": 0x7,
}
HAIER_YRW02_SWING_H_POSITION = {  # canonical swing_h -> position, as convertSwingH
    "auto": "auto",
    "1": "left_max",
    "2": "left",
    "3": "middle",
    "4": "right",
    "5": "right_max",
}
HAIER_YRW02_MIN_TEMP, HAIER_YRW02_MAX_TEMP = 16, 30  # kHaierAcYrw02Min/MaxTempC

HAIER_YRW02_LAYOUT = Layout(
    # IRHaierAC176::stateReset clears the whole state (memset) and every
    # byte it then sets is a field below: no stale padding.
    bytes(14),
    {
        "model": Field.at(0, 0, 8, values={"A": 0xA6, "B": 0x59}),  # Model A/B
        "swing_v": Field.at(1, 0, 4, values=HAIER_YRW02_SWING_V),
        "temperature": Field.at(  # celsius - kHaierAcYrw02MinTempC
            1,
            4,
            4,
            values={
                t: t - HAIER_YRW02_MIN_TEMP
                for t in range(HAIER_YRW02_MIN_TEMP, HAIER_YRW02_MAX_TEMP + 1)
            },
        ),
        "swing_h": Field.at(2, 5, 3, values=HAIER_YRW02_SWING_H),
        "health": Field.at(3, 1, 1),
        "timer_mode": Field.at(3, 5, 3),  # kHaierAcYrw02*Timer*: never set
        "power": Field.at(4, 6, 1),
        "off_timer_hrs": Field.at(5, 0, 5),
        "fan": Field.at(  # kHaierAcYrw02Fan*, as IRHaierAC176::convertFan
            5, 5, 3, values={"auto": 0b101, "1": 0b011, "2": 0b010, "3": 0b001}
        ),
        "off_timer_mins": Field.at(6, 0, 6),
        "turbo": Field.at(6, 6, 1),
        "quiet": Field.at(6, 7, 1),
        "on_timer_hrs": Field.at(7, 0, 5),
        "mode": Field.at(  # kHaierAcYrw02{Auto,Cool,Dry,Heat,Fan}
            7,
            5,
            3,
            values={
                "auto": 0b000,
                "cool": 0b001,
                "dry": 0b010,
                "heat": 0b100,
                "fan": 0b110,
            },
        ),
        "on_timer_mins": Field.at(8, 0, 6),
        "sleep": Field.at(8, 7, 1),
        "extra_degree_f": Field.at(10, 0, 1),
        "use_fahrenheit": Field.at(10, 5, 1),
        "button": Field.at(12, 0, 5, values=HAIER_YRW02_BUTTON),
        "lock": Field.at(12, 5, 1),
    },
    checksum=Sum8(0, 13, 13),  # IRHaierAC176::checksum: Sum
)


class HaierYrw02Device(Device):
    """Haier YR-W02 (HAIER_AC_YRW02, remote variants A and B): full state in
    one 14-byte frame.

    The variant ("A" or "B", kHaierAcYrw02ModelA/B in byte 0) comes from the
    model (HAIER_YRW02_MODELS) unless given, so the registry's
    ``cls(brand, model)`` call picks it; unknown models get A, as
    IRHaierAC176::setModel does.

    The Button field (the key the remote reports as pressed) is always
    kHaierAcYrw02ButtonPower, as the C path sends: IRac::haierYrwo2 calls
    setPower last, on a fresh object, whatever changed. IRac::sendAc uses no
    previous state for HAIER_AC_YRW02 and IRac::handleToggles has no case
    for it, and the struct has no toggle bits (power, swing and the features
    are states), so ``previous`` is ignored, with or without it.
    """

    PROTOCOL = HAIER_YRW02
    LAYOUTS = (HAIER_YRW02_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "heat", "fan"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
        ),
        swing_v=Choice(
            ("off", "auto", "1", "2", "3", "4"),
            {
                "off": "off",
                "auto": "auto",
                "1": "ceiling",
                "2": "45°",
                "3": "30°",
                "4": "0°",
            },
        ),
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
        features={
            "purifier": Choice((False, True), {False: "off", True: "on"}),
            "sleep": Choice((False, True), {False: "off", True: "on"}),
            "powerful": Choice((False, True), {False: "off", True: "on"}),
            "quiet": Choice((False, True), {False: "off", True: "on"}),
        },
    )

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        self.variant = variant or HAIER_YRW02_MODELS.get(model, "A")
        if self.variant not in ("A", "B"):
            raise ValueError(f"unknown Haier YR-W02 variant {self.variant!r}")

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to auto).
        mode = target.mode if target.power else "auto"
        swing_v = HAIER_YRW02_SWING_V_POSITION[target.swing_v]
        # IRHaierAC176::setSwingV: heat has no Middle (Bottom instead), and
        # Bottom exists in heat only (Middle instead).
        if swing_v == "middle" and mode == "heat":
            swing_v = "bottom"
        elif swing_v == "bottom" and mode != "heat":
            swing_v = "middle"
        # setQuiet then setTurbo, both only in cool and heat (setMode clears
        # them elsewhere); turbo on clears quiet.
        features = target.features
        boost = mode in ("cool", "heat")
        turbo = boost and features["powerful"]
        quiet = boost and features["quiet"] and not turbo
        data = HAIER_YRW02_LAYOUT.build(
            model=self.variant,
            swing_v=swing_v,
            temperature=int(target.temperature),
            swing_h=HAIER_YRW02_SWING_H_POSITION[target.swing_h],
            health=features["purifier"],
            power=target.power,
            fan=target.fan,
            turbo=turbo,
            quiet=quiet,
            mode=mode,
            sleep=features["sleep"],
            button="power",
        )
        return [Frame("main", bytes(data))]


HAIER_YRW02_MODELS = {  # model -> remote variant (haier_ac176_remote_model_t)
    "YR-W02 remote": "A",
    "HSU-09HMC203": "A",
    "YR-W02 Code A": "A",
    "YR-W02 Code B": "B",
}


DEVICES.update({m: HaierYrw02Device for m in HAIER_YRW02_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_haier_yrw02_device.py -q`
Expected: 520 passed, 4 skipped (the skips need the C extension).

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/haier.py tests/test_haier_yrw02_device.py
git add pyhvac/plugins/haier.py tests/test_haier_yrw02_device.py
git commit -m "HAIER_AC_YRW02: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 5: HAIER_AC160

One 20-byte frame with two byte sums (local `Haier160Checksum`); layout from `union HaierAc160Protocol`; light button pressed only when the light changes (as IRac::sendAc).

**Files:**
- Modify: `pyhvac/plugins/haier.py` (block before `# Now the match between models and objects`)
- Test: `tests/test_haier160_device.py`

**Interfaces:**
- Consumes: `Device`, `pyhvac.fields`, `tests/port_oracle.py`, and the oracle fixture `HAIER_AC160`.
- Produces: `Haier160Device`, `HAIER160_MODELS`, and the `DEVICES` entries for those models.

- [ ] **Step 1: Write the failing tests**: create `tests/test_haier160_device.py`:

```python
import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.fields import Sum8
from pyhvac.ir.codec import decode
from pyhvac.plugins.haier import (
    HAIER160,
    HAIER160_LAYOUT,
    HAIER160_MODELS,
    Haier160Checksum,
    Haier160Device,
)
from pyhvac.state import HvacState

# The C path deviates from the documented HaierAc160Protocol here:
# - sleep: IRGHVAC.build_ircode's key map has no "sleep", so IRac's sleep
#   stays -1 and IRac::haier160's setSleep(sleep >= 0) always clears Sleep
#   (byte 8 bit 7). The port sets it.
SLEEP = Defect("sleep", 1, 0, "legacy glue never passes sleep")
DEFECTS = (SLEEP,)

# ir_Haier_test.cpp, TestDecodeHaierAC160.RealExample (issue #1804): power
# on, cool, 26 C, fan low, swing(V) auto, button Power.
REAL_EXAMPLE = bytes.fromhex("a6ac0000406000200000000005 17 b50060000015")
# TestHaierAC160Class.Light: the same settings with the Light button.
LIGHT_PRESS = bytes.fromhex("a6ac00004060002000000000 15 27 b50060000015")
# TestHaierAC160Class.CleanMode: clean on, pressed with the Clean button.
CLEAN_ON = bytes.fromhex("a6ac00004060002000001000 19 3b b54060000055")

ALL_FEATURES = ("purifier", "sleep", "powerful", "quiet", "cleaning", "light")


def device(model="KFR-26GW/83@UI-Ge"):
    return Haier160Device("haier", model)


def frame(state, previous=None):
    dev = device()
    if previous is not None:
        previous = dev.normalise(previous)
    (main,) = dev.frames(previous, dev.normalise(state), ())
    return main.data


def read(state, previous=None):
    return HAIER160_LAYOUT.read(frame(state, previous))


def features(**on):
    return {k: True for k in on}


@pytest.mark.parametrize("record", oracle_params("HAIER_AC160"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("HAIER_AC160"):
        state = state_from_record(dev, record["state"])
        (main,) = dev.frames(None, state, ())
        values = HAIER160_LAYOUT.read(main.data)
        assert HAIER160_LAYOUT.build(**values) == bytearray(main.data)


def test_every_oracle_frame_has_both_section_sums():
    # IRHaierAC160::checksum: sumBytes(raw, 13) at 13, sumBytes(raw + 14, 5)
    # at 19. (portkit checksum only tries the last two bytes, so it finds
    # Sum2 but not Sum.)
    for record in load_oracle("HAIER_AC160"):
        (main,) = decode(HAIER160, record["pulses"], expected=["main"])
        assert Sum8(0, 13, 13).check(main.data)
        assert Sum8(14, 19, 19).check(main.data)
        assert Haier160Checksum().check(main.data)


def test_checksum_bytes_are_not_fields():
    assert Haier160Checksum().positions() == {13, 19}
    for name, f in HAIER160_LAYOUT.fields.items():
        assert not {b // 8 for b in f.bits} & {13, 19}, name


def test_real_example_is_reproduced():
    state = HvacState(True, "cool", 26.0, fan="1", swing_v="auto")
    assert frame(state) == REAL_EXAMPLE


def test_light_press_capture_is_reproduced_without_previous():
    # A fresh IRac: prevlight is its default state's light (off), so light
    # on presses kHaierAc160ButtonLight.
    state = HvacState(True, "cool", 26.0, fan="1", swing_v="auto")
    lit = HvacState(
        True, "cool", 26.0, fan="1", swing_v="auto", features={"light": True}
    )
    assert frame(lit) == LIGHT_PRESS
    assert frame(lit, previous=state) == LIGHT_PRESS


def test_clean_capture_matches_except_the_button():
    # The remote sends the Clean button; IRac::haier160 calls setClean
    # before setPower, so the C path (and the port) send Power.
    state = HvacState(
        True, "cool", 26.0, fan="1", swing_v="auto", features={"cleaning": True}
    )
    data = frame(state)
    assert HAIER160_LAYOUT.read(data) == {
        **HAIER160_LAYOUT.read(CLEAN_ON),
        "button": "power",
    }
    assert HAIER160_LAYOUT.read(CLEAN_ON)["button"] == "clean"


def test_skeleton_is_the_reset_state_with_fields_cleared():
    record = load_oracle("HAIER_AC160")[0]
    assert record["state"] == {
        "fan": "auto",
        "mode": "off",
        "swing": "off",
        "temperature": 16,
    }
    (main,) = decode(HAIER160, record["pulses"], expected=["main"])
    data = HAIER160_LAYOUT.build(button="power", fan="auto", temperature=16)
    assert bytes(data) == main.data


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat", "fan"])
@pytest.mark.parametrize("temp", [16.0, 23.0, 30.0])
def test_off_carries_mode_auto_in_every_mode(mode, temp):
    # IRac passes mode "off"; convertMode maps it to kHaierAcYrw02Auto,
    # which also clears turbo, quiet and AuxHeating.
    state = HvacState(False, mode, temp, features=features(powerful=1, quiet=1))
    values = read(state)
    assert (values["power"], values["mode"], values["temperature"]) == (
        0,
        "auto",
        int(temp),
    )
    assert (values["turbo"], values["quiet"], values["aux_heating"]) == (0, 0, 0)
    assert values["button"] == "power"


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "heat", "fan"])
def test_aux_heating_follows_heat_mode(mode):
    # IRHaierAC160::setMode: AuxHeating = (Mode == kHaierAcYrw02Heat).
    assert read(HvacState(True, mode, 24.0))["aux_heating"] == (mode == "heat")


def test_setpoint_is_clamped_to_16_30():
    assert read(HvacState(True, "cool", 10.0))["temperature"] == 16
    assert read(HvacState(True, "heat", 40.0))["temperature"] == 30
    assert read(HvacState(True, "cool", 22.0))["use_fahrenheit"] == 0


@pytest.mark.parametrize(
    "fan, raw, raw2",
    [("auto", 0b101, 0), ("1", 0b011, 0b011), ("2", 0b010, 0b010), ("3", 0b001, 1)],
)
def test_every_fan_level_and_fan2(fan, raw, raw2):
    # setFan: Fan2 is 0 for auto, else the Fan code.
    data = frame(HvacState(True, "cool", 24.0, fan=fan))
    assert HAIER160_LAYOUT.read_raw(data, "fan") == raw
    assert HAIER160_LAYOUT.read_raw(data, "fan2") == raw2


@pytest.mark.parametrize(
    "swing, raw",
    [
        ("off", 0b0000),
        ("auto", 0b1100),
        ("1", 0b0001),  # ceiling: kHighest -> Top
        ("2", 0b0100),  # 90°: kHigh -> High
        ("3", 0b0110),  # 45°: kMiddle -> Middle
        ("4", 0b1000),  # 30°: kLow -> Low
        ("5", 0b0011),  # 0°: kLowest -> Lowest
    ],
)
def test_every_swing_value(swing, raw):
    data = frame(HvacState(True, "cool", 24.0, swing_v=swing))
    assert HAIER160_LAYOUT.read_raw(data, "swing_v") == raw


@pytest.mark.parametrize("mode", ["cool", "heat"])
def test_turbo_and_quiet_in_cool_and_heat(mode):
    # setQuiet(quiet), then setTurbo(turbo): turbo on clears Quiet.
    assert (
        read(HvacState(True, mode, 24.0, features=features(powerful=1)))["turbo"] == 1
    )
    values = read(HvacState(True, mode, 24.0, features=features(quiet=1)))
    assert (values["turbo"], values["quiet"]) == (0, 1)
    values = read(HvacState(True, mode, 24.0, features=features(powerful=1, quiet=1)))
    assert (values["turbo"], values["quiet"]) == (1, 0)


@pytest.mark.parametrize("mode", ["auto", "dry", "fan"])
def test_no_turbo_or_quiet_outside_cool_and_heat(mode):
    values = read(HvacState(True, mode, 24.0, features=features(powerful=1, quiet=1)))
    assert (values["turbo"], values["quiet"]) == (0, 0)


def test_purifier_cleaning_and_sleep_bits():
    values = read(
        HvacState(
            True, "cool", 24.0, features=features(purifier=1, cleaning=1, sleep=1)
        )
    )
    assert (values["health"], values["clean"], values["clean2"]) == (1, 1, 1)
    assert values["sleep"] == 1  # the documented Sleep bit (a Defect vs C)
    assert values["button"] == "power"


def test_every_feature_leaves_the_power_button():
    # Every IRac setter writes the button, but setPower comes last (before
    # the light toggle).
    state = HvacState(
        True,
        "cool",
        24.0,
        features={k: True for k in ALL_FEATURES if k != "light"},
    )
    assert read(state)["button"] == "power"


def test_light_without_previous_presses_the_light_button():
    assert read(HvacState(True, "cool", 24.0))["button"] == "power"
    lit = HvacState(True, "cool", 24.0, features=features(light=1))
    assert read(lit)["button"] == "light"
    assert frame(lit)[12] == 0x15


@pytest.mark.parametrize(
    "before, after, button",
    [
        (False, False, "power"),
        (False, True, "light"),
        (True, True, "power"),
        (True, False, "light"),
    ],
)
def test_light_button_with_previous_only_on_change(before, after, button):
    # IRac::sendAc: setLightToggle(light ^ prev->light).
    previous = HvacState(True, "cool", 24.0, features={"light": before})
    target = HvacState(True, "heat", 25.0, features={"light": after})
    assert read(target, previous)["button"] == button


def test_encode_passes_previous_to_the_light_button():
    dev = device()
    lit = HvacState(True, "cool", 22.0, features=features(light=1))
    assert dev.encode(None, lit).signal != dev.encode(lit, lit).signal


def test_message_shape():
    dev = device()
    pulses = dev.encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:4] == (3000, 3000, 3000, 4300)
    assert pulses[-2:] == (520, 150000)
    assert len(pulses) == 4 + 2 * 160 + 2


@pytest.mark.parametrize("model", HAIER160_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("haier", model), Haier160Device)


@pytest.mark.parametrize("model", HAIER160_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.haier import Haier160

    legacy = LegacyDevice("haier", model, Haier160)
    assert Haier160Device("haier", model).capabilities == legacy.capabilities


def test_undeclared_sleep_deviation_is_reported():
    dev = device()
    record = next(
        r for r in load_oracle("HAIER_AC160") if r["state"].get("sleep") == "on"
    )
    with pytest.raises(AssertionError, match="sleep"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `python -m pytest tests/test_haier160_device.py -q`
Expected: collection error, `ImportError: cannot import name ...` from `pyhvac.plugins.haier`.

- [ ] **Step 3: Implement**: insert immediately before `# Now the match between models and objects` in `pyhvac/plugins/haier.py`:

```python
# --------------------------------------------------------------- Haier160
# Layout from IRremoteESP8266's HaierAc160Protocol (ir_Haier.h): 20 bytes in
# two checksummed sections, bytes 0-13 (Sum at byte 13) and 14-19 (Sum2 at
# byte 19). Sent by sendHaierAC as one frame, MSB first, after a lone
# kHaierAcHdr mark and space, the kHaierAcHdr/kHaierAcHdrGap header, and
# closed by kHaierAcMinGap. IRHaierAC160::stateReset zeroes every byte, so
# no bit comes from stale memory.

HAIER160 = Protocol(
    "haier160",
    {
        "main": Section(
            PulseDistance(520, 650, 1650),  # kHaierAcBitMark/ZeroSpace/OneSpace
            # mark(kHaierAcHdr), space(kHaierAcHdr), then sendGeneric's
            # kHaierAcHdr/kHaierAcHdrGap header.
            header=(3000, 3000, 3000, 4300),
            footer=(520,),
            gap=150000,  # kHaierAcMinGap
            lsb_first=False,
        )
    },
    carrier=38000,
)


@dataclass(frozen=True)
class Haier160Checksum:
    """IRHaierAC160::checksum: Sum = sumBytes(raw, 13) at byte 13, and
    Sum2 = sumBytes(raw + 14, 5) at byte 19."""

    parts: tuple = (Sum8(0, 13, 13), Sum8(14, 19, 19))

    def positions(self):
        return set().union(*(p.positions() for p in self.parts))

    def apply(self, data):
        for part in self.parts:
            part.apply(data)

    def check(self, data):
        return all(part.check(data) for part in self.parts)


HAIER160_BUTTON = {  # kHaierAcYrw02Button* / kHaierAc160Button*
    "temp_up": 0b00000,
    "temp_down": 0b00001,
    "swing_v": 0b00010,
    "swing_h": 0b00011,
    "fan": 0b00100,
    "power": 0b00101,
    "mode": 0b00110,
    "health": 0b00111,
    "turbo": 0b01000,
    "sleep": 0b01011,
    "timer": 0b10000,
    "lock": 0b10100,
    "light": 0b10101,
    "aux_heating": 0b10110,
    "clean": 0b11001,
    "cfab": 0b11010,
}
HAIER160_FAN = {  # canonical fan -> kHaierAcYrw02Fan*, as convertFan
    "auto": 0b101,
    "1": 0b011,  # low
    "2": 0b010,  # medium
    "3": 0b001,  # high
}
HAIER160_SWING_V = {  # canonical swing -> kHaierAc160SwingV*, as convertSwingV
    "off": 0b0000,
    "auto": 0b1100,  # airflow
    "1": 0b0001,  # ceiling (kHighest): kHaierAc160SwingVTop
    "2": 0b0100,  # 90° (kHigh): kHaierAc160SwingVHigh
    "3": 0b0110,  # 45° (kMiddle): kHaierAc160SwingVMiddle
    "4": 0b1000,  # 30° (kLow): kHaierAc160SwingVLow
    "5": 0b0011,  # 0° (kLowest): kHaierAc160SwingVLowest
}
HAIER160_MIN_TEMP, HAIER160_MAX_TEMP = 16, 30  # kHaierAcYrw02Min/MaxTempC

# Skeleton: IRHaierAC160::stateReset (Model kHaierAcYrw02ModelA, Prefix
# kHaierAc160Prefix) with every field cleared; the device writes them all.
HAIER160_LAYOUT = Layout(
    bytes.fromhex("a6000000000000000000000000" "00b50000000000"),
    {
        "swing_v": Field.at(1, 0, 4, values=HAIER160_SWING_V),
        "temperature": Field.at(  # whole °C, stored as degrees - 16
            1,
            4,
            4,
            values={
                t: t - HAIER160_MIN_TEMP
                for t in range(HAIER160_MIN_TEMP, HAIER160_MAX_TEMP + 1)
            },
        ),
        "swing_h": Field.at(2, 5, 3),  # IRHaierAC160 has no setter
        "health": Field.at(3, 1, 1),
        "timer_mode": Field.at(3, 5, 3),
        "power": Field.at(4, 6, 1),
        "aux_heating": Field.at(4, 7, 1),
        "off_timer_hrs": Field.at(5, 0, 5),
        "fan": Field.at(5, 5, 3, values=HAIER160_FAN),
        "off_timer_mins": Field.at(6, 0, 6),
        "turbo": Field.at(6, 6, 1),
        "quiet": Field.at(6, 7, 1),
        "on_timer_hrs": Field.at(7, 0, 5),
        "mode": Field.at(
            7, 5, 3, values={"auto": 0, "cool": 1, "dry": 2, "heat": 4, "fan": 6}
        ),
        "on_timer_mins": Field.at(8, 0, 6),
        "sleep": Field.at(8, 7, 1),
        "extra_degree_f": Field.at(10, 0, 1),
        "clean": Field.at(10, 4, 1),
        "use_fahrenheit": Field.at(10, 5, 1),
        "button": Field.at(12, 0, 5, values=HAIER160_BUTTON),
        "lock": Field.at(12, 5, 1),
        "clean2": Field.at(15, 6, 1),
        # setFan: Fan2 is 0 for auto, else the Fan code.
        "fan2": Field.at(16, 5, 3, values={**HAIER160_FAN, "auto": 0}),
    },
    checksum=Haier160Checksum(),
)


class Haier160Device(Device):
    """Haier 160-bit (KFR-26GW/83@UI-Ge): full state, plus a light button.

    As IRac::haier160 sends it: an off message carries mode auto
    (convertMode maps IRac's "off" to kHaierAcYrw02Auto), so it also clears
    turbo, quiet and AuxHeating; setMode sets AuxHeating in heat mode only;
    turbo and quiet are kept in cool and heat only, and turbo wins when both
    are asked (setQuiet, then setTurbo(true) clears Quiet); cleaning sets
    Clean and Clean2; purifier sets Health; the temperature is Celsius.

    The Button field (byte 12) is whatever setter ran last. IRac::haier160
    ends with setPower (kHaierAcYrw02ButtonPower), then setLightToggle(light
    ^ prevlight), which presses kHaierAc160ButtonLight when the light changes.
    IRac::sendAc computes prevlight itself (not in handleToggles): the
    previous state's light, and a fresh IRac's previous state has light off.
    So with ``previous`` the light button is pressed only when the light
    changes, as a persistent IRac does; with ``previous=None`` it is pressed
    when the light is on, as a fresh IRac does. The port matches C in both.

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_haier160_device.py):
    - sleep: the old glue never passes sleep, so setSleep(sleep >= 0) always
      clears Sleep; the port sets it.
    """

    PROTOCOL = HAIER160
    LAYOUTS = (HAIER160_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "heat", "fan"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
        ),
        swing_v=Choice(
            ("off", "auto", "1", "2", "3", "4", "5"),
            {
                "off": "off",
                "auto": "auto",
                "1": "ceiling",
                "2": "90°",
                "3": "45°",
                "4": "30°",
                "5": "0°",
            },
        ),
        features={
            name: Choice((False, True), {False: "off", True: "on"})
            for name in ("purifier", "sleep", "powerful", "quiet", "cleaning", "light")
        },
    )

    def frames(self, previous, target, actions):
        f = target.features
        mode = target.mode if target.power else "auto"
        # setTurbo/setQuiet only act in cool and heat; setMode(auto/dry/fan)
        # clears both.
        boost = mode in ("cool", "heat")
        turbo = boost and f["powerful"]
        quiet = boost and f["quiet"] and not f["powerful"]
        if previous is None:
            light = f["light"]
        else:
            light = f["light"] != previous.features["light"]
        data = HAIER160_LAYOUT.build(
            swing_v=target.swing_v,
            temperature=int(target.temperature),
            health=f["purifier"],
            power=target.power,
            aux_heating=mode == "heat",
            fan=target.fan,
            turbo=turbo,
            quiet=quiet,
            mode=mode,
            sleep=f["sleep"],
            clean=f["cleaning"],
            clean2=f["cleaning"],
            button="light" if light else "power",
            fan2=target.fan,
        )
        return [Frame("main", bytes(data))]


HAIER160_MODELS = ("KFR-26GW/83@UI-Ge", "generic 160")


DEVICES.update({m: Haier160Device for m in HAIER160_MODELS})
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_haier160_device.py -q`
Expected: 256 passed, 2 skipped (the skips need the C extension).

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/haier.py tests/test_haier160_device.py
git add pyhvac/plugins/haier.py tests/test_haier160_device.py
git commit -m "HAIER_AC160: pure-Python port on the port kit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```


---

### Task 6: Whole-family verification

**Files:**
- Modify: `tests/test_haier_family.py`

- [ ] **Step 1: Add the family test**: append to `tests/test_haier_family.py`:

```python
def test_no_haier_model_uses_the_c_library():
    from pyhvac import registry
    from pyhvac.legacy import LegacyDevice

    left = [
        m
        for m in registry.models("haier")
        if isinstance(registry.get_device("haier", m), LegacyDevice)
    ]
    assert left == []
```

- [ ] **Step 2: Run it**

Run: `python -m pytest tests/test_haier_family.py -q`
Expected: 2 passed.

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
black tests/test_haier_family.py
git add tests/test_haier_family.py
git commit -m "Test that no Haier model is left on the C library

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
