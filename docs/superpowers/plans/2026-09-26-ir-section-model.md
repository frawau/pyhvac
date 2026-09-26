# IR Section Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a pure-Python, declarative, bidirectional IR physical layer (`pyhvac/ir/`), move the existing pure-Python plugins onto it without changing their wire output, and record reference pulse trains from the C library for the later protocol ports.

**Architecture:** `pyhvac/ir/model.py` holds frozen dataclasses (bit encodings, `Section`, `Protocol`, `Frame`, `Signal`). `pyhvac/ir/codec.py` turns frames into a `Signal` (`encode`) and captured pulses back into frames (`decode`). `pyhvac/ir/formats.py` holds the edge formatters (Broadlink, Pronto, raw). `HVAC` in `hvaclib.py` gains an optional `PROTOCOL`; the old `build_ircode`/`to_lirc`/`to_broadlink` become thin wrappers. Golden fixtures pin the current plugin output before migration, and C-oracle fixtures pin what IRremoteESP8266 produces.

**Tech Stack:** Python ≥ 3.9 standard library only (dataclasses, struct, gzip, json), pytest, black.

**Spec:** `docs/superpowers/specs/2026-09-26-ir-section-model-design.md`

## Global Constraints

- All durations are integer µs; carrier is integer Hz. No floats in public model fields except `Protocol.tolerance`.
- Python ≥ 3.9 compatible (wheels are built for cp39+): every new module starts with `from __future__ import annotations`; no `match`, no runtime `X | Y` types (use `typing.Union`/tuples in `isinstance`).
- No new runtime dependencies.
- `pyhvac/ir/` never imports from `pyhvac.plugins`.
- Run `black` on every modified Python file before committing.
- Run tests with `python -m pytest -q` from the repo root.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Do not change the wire output (`to_lirc`, `to_broadlink`) of any existing plugin; the golden fixtures from Task 5 are the arbiter.

## Review Focus

1. A capture whose trailing silence was cut off (ends on the footer mark) must still decode. The test is in Task 3.
2. A capture holding the message twice (remotes often repeat) must decode to two frames greedily, and must raise `DecodeError` when `expected` names only one section. Tests in Task 3.
3. Signed raw lists (ESPHome style, negative spaces) or zero durations passed to `decode` must raise `ValueError` naming the index, not decode garbage. Test in Task 3.
4. Legacy builders return `bytearray`s. `Frame` must normalise them to `bytes` with equality preserved, and the `HVAC` wrappers must accept them. Tests in Tasks 1 and 6.
5. A Manchester message whose first half-bit has the same level as the header's last element (so the two merge on the wire) must decode correctly. Test in Task 3.

## Known issues found while planning (NOT fixed by this plan)

- `IRGHVAC.set_fan` (`pyhvac/plugins/hvaclib.py:271-274`) validates against `capabilities["mode"]` and writes `to_set["mode"]`. A fan change on a C-backed model therefore sets the mode to `capabilities["mode"][0]`, usually `"off"`. The oracle generator (Task 9) bypasses setters because of this.
- The generic `Sharp` class raises `KeyError('economy')` from `build_ircode()`. It is excluded from golden fixtures, while `JTech` covers the Sharp code path.
- Native `LG` emits 32 bits per frame; the LG protocol is 28 bits (`LG.get_timing` mentions `drop_bits: 4`). The migration keeps 32 bits so the wire output does not change.
- `LG.get_timing` references undefined globals (`STARTFRAME`…) and would raise `NameError`. It is removed in Task 8.

## File Structure

- Create `pyhvac/ir/__init__.py`: re-exports the public names.
- Create `pyhvac/ir/model.py`: the data model and its validation.
- Create `pyhvac/ir/codec.py`: `encode`, `decode`, `DecodeError`.
- Create `pyhvac/ir/formats.py`: `to_broadlink`, `broadlink_packet`, `to_pronto`, `to_raw`, `from_broadlink`, `from_pronto`.
- Create `tools/state_grid.py`: builds the deterministic state grid; shared by both generators and the golden test.
- Create `tools/golden_generate.py`: records the current output of the pure-Python plugins.
- Create `tools/oracle_generate.py`: records C library output (runs against an installed release).
- Create `tests/conftest.py`: puts `tools/` on `sys.path`.
- Create `tests/test_ir_model.py`, `tests/test_ir_encode.py`, `tests/test_ir_decode.py`, `tests/test_ir_formats.py`, `tests/test_hvac_protocol.py`, `tests/test_golden_native.py`, `tests/oracle.py`, `tests/test_oracle_support.py`.
- Create `tests/fixtures/golden/*.json.gz` and `tests/fixtures/oracle/*.json.gz` (generated).
- Modify `setup.py`: add `pyhvac.ir` to `packages`.
- Modify `pyhvac/plugins/hvaclib.py`: `HVAC.PROTOCOL`, `build_signal`, wrappers; remove `get_timing`.
- Modify `pyhvac/plugins/sharp.py`, `lg.py`, `panasonic.py`: tolerate a missing `irhvac`; `PROTOCOL` for the native classes.
- Modify `pyhvac/plugins/daikin.py`: `PROTOCOL` for `Daikinth`.
- Modify `pyhvac/plugins/airspool.py`: `PROTOCOL`; `decode_pulse` via `codec.decode`.

---

### Task 1: Data model

**Files:**
- Create: `pyhvac/ir/__init__.py`, `pyhvac/ir/model.py`
- Modify: `setup.py` (the `packages=` line)
- Test: `tests/test_ir_model.py`

**Interfaces:**
- Consumes: nothing.
- Produces (`pyhvac.ir.model`):
  - `PulseDistance(mark: int, zero_space: int, one_space: int)`
  - `PulseWidth(zero_mark: int, one_mark: int, space: int)`
  - `Manchester(half: int, one_is_mark_first: bool = True)`
  - `BitEncoding = Union[PulseDistance, PulseWidth, Manchester]`
  - `Section(bits, header: tuple[int, ...] = (), footer: tuple[int, ...] = (), gap: int = 0, lsb_first: bool = True)`
  - `Protocol(name: str, sections: dict[str, Section], carrier: int = 38000, tolerance: float = 0.25, mark_excess: int = 50, trailer_gap: int = 100_000)`
  - `Frame(section: str, data: bytes, nbits: int | None = None)`: after construction `data` is `bytes` and `nbits` is an `int`.
  - `Signal(carrier: int, pulses: tuple[int, ...])`
  - All raise `ValueError` on invalid input.

- [ ] **Step 1: Write the failing tests** in `tests/test_ir_model.py`

```python
import pytest

from pyhvac.ir.model import (
    Frame,
    Manchester,
    Protocol,
    PulseDistance,
    PulseWidth,
    Section,
    Signal,
)

NEC_BITS = PulseDistance(560, 560, 1690)


def main_protocol(**kwargs):
    return Protocol("t", {"main": Section(NEC_BITS, footer=(560,))}, **kwargs)


@pytest.mark.parametrize(
    "args", [(0, 560, 1690), (560.0, 560, 1690), (True, 560, 1690), (560, -1, 1690)]
)
def test_pulse_distance_rejects_bad_durations(args):
    with pytest.raises(ValueError):
        PulseDistance(*args)


def test_pulse_distance_needs_distinct_spaces():
    with pytest.raises(ValueError):
        PulseDistance(560, 560, 560)


def test_pulse_width_needs_distinct_marks():
    with pytest.raises(ValueError):
        PulseWidth(600, 600, 600)


def test_manchester_rejects_zero_half():
    with pytest.raises(ValueError):
        Manchester(0)


def test_section_converts_header_and_footer_to_tuples():
    s = Section(NEC_BITS, header=[9000, 4500], footer=[560])
    assert s.header == (9000, 4500)
    assert s.footer == (560,)


@pytest.mark.parametrize(
    "kwargs",
    [dict(header=(9000, 0)), dict(footer=(560.5,)), dict(gap=-1), dict(gap=1.5)],
)
def test_section_rejects_bad_durations(kwargs):
    kwargs.setdefault("footer", (560,))
    with pytest.raises(ValueError):
        Section(NEC_BITS, **kwargs)


def test_pulse_distance_section_needs_footer():
    with pytest.raises(ValueError, match="footer"):
        Section(NEC_BITS)


def test_pulse_width_and_manchester_sections_need_no_footer():
    Section(PulseWidth(600, 1200, 600))
    Section(Manchester(500))


def test_section_rejects_unknown_bit_encoding():
    with pytest.raises(ValueError):
        Section("nec", footer=(560,))


def test_protocol_defaults():
    p = main_protocol()
    assert p.carrier == 38000
    assert p.tolerance == 0.25
    assert p.mark_excess == 50
    assert p.trailer_gap == 100_000


def test_protocol_needs_sections():
    with pytest.raises(ValueError):
        Protocol("t", {})


def test_protocol_rejects_non_section():
    with pytest.raises(ValueError):
        Protocol("t", {"main": NEC_BITS})


@pytest.mark.parametrize("tolerance", [0, 0.5, -0.1, 1])
def test_protocol_rejects_bad_tolerance(tolerance):
    with pytest.raises(ValueError):
        main_protocol(tolerance=tolerance)


@pytest.mark.parametrize(
    "kwargs", [dict(carrier=0), dict(mark_excess=-1), dict(trailer_gap=0)]
)
def test_protocol_rejects_bad_numbers(kwargs):
    with pytest.raises(ValueError):
        main_protocol(**kwargs)


def test_protocol_copies_sections():
    sections = {"main": Section(NEC_BITS, footer=(560,))}
    p = Protocol("t", sections)
    sections.clear()
    assert "main" in p.sections


def test_frame_normalises_bytearray_and_defaults_nbits():
    f = Frame("main", bytearray(b"\x01\x02"))
    assert type(f.data) is bytes
    assert f.data == b"\x01\x02"
    assert f.nbits == 16
    assert f == Frame("main", b"\x01\x02", 16)


def test_frame_accepts_int_list():
    assert Frame("main", [1, 2]).data == b"\x01\x02"


def test_frame_rejects_empty_data():
    with pytest.raises(ValueError):
        Frame("main", b"")


@pytest.mark.parametrize("nbits", [0, 8, 17])
def test_frame_nbits_must_fall_in_last_byte(nbits):
    with pytest.raises(ValueError):
        Frame("main", b"\x01\x02", nbits)


@pytest.mark.parametrize("nbits", [9, 16])
def test_frame_accepts_nbits_in_last_byte(nbits):
    assert Frame("main", b"\x01\x02", nbits).nbits == nbits


@pytest.mark.parametrize(
    "carrier, pulses",
    [(38000, ()), (38000, (9000,)), (38000, (9000, 0)), (0, (9000, 4500))],
)
def test_signal_validation(carrier, pulses):
    with pytest.raises(ValueError):
        Signal(carrier, pulses)


def test_signal_stores_tuple():
    assert Signal(38000, [9000, 4500]).pulses == (9000, 4500)
```

- [ ] **Step 2: Run the tests to confirm they fail**

Run: `python -m pytest tests/test_ir_model.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'pyhvac.ir'`

- [ ] **Step 3: Write `pyhvac/ir/model.py`**

```python
"""Declarative description of an IR physical layer.

All durations are integer microseconds; carrier frequencies are integer Hz.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Union


def _check_int(name, value, unit, minimum=1):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer ({unit}), got {value!r}")
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum} {unit}, got {value}")


@dataclass(frozen=True)
class PulseDistance:
    """Constant mark; the following space carries the bit."""

    mark: int
    zero_space: int
    one_space: int

    def __post_init__(self):
        for name in ("mark", "zero_space", "one_space"):
            _check_int(name, getattr(self, name), "µs")
        if self.zero_space == self.one_space:
            raise ValueError("zero_space and one_space must differ")


@dataclass(frozen=True)
class PulseWidth:
    """The mark carries the bit; constant space."""

    zero_mark: int
    one_mark: int
    space: int

    def __post_init__(self):
        for name in ("zero_mark", "one_mark", "space"):
            _check_int(name, getattr(self, name), "µs")
        if self.zero_mark == self.one_mark:
            raise ValueError("zero_mark and one_mark must differ")


@dataclass(frozen=True)
class Manchester:
    """Bi-phase: each bit is two half-periods of opposite level."""

    half: int
    one_is_mark_first: bool = True

    def __post_init__(self):
        _check_int("half", self.half, "µs")


BitEncoding = Union[PulseDistance, PulseWidth, Manchester]


@dataclass(frozen=True)
class Section:
    """Template for one burst on the wire: header, bits, footer, gap.

    ``header`` and ``footer`` alternate mark, space, ... starting with a mark.
    """

    bits: BitEncoding
    header: Tuple[int, ...] = ()
    footer: Tuple[int, ...] = ()
    gap: int = 0
    lsb_first: bool = True

    def __post_init__(self):
        if not isinstance(self.bits, (PulseDistance, PulseWidth, Manchester)):
            raise ValueError(f"unknown bit encoding {self.bits!r}")
        object.__setattr__(self, "header", tuple(self.header))
        object.__setattr__(self, "footer", tuple(self.footer))
        for i, d in enumerate(self.header):
            _check_int(f"header[{i}]", d, "µs")
        for i, d in enumerate(self.footer):
            _check_int(f"footer[{i}]", d, "µs")
        _check_int("gap", self.gap, "µs", minimum=0)
        if isinstance(self.bits, PulseDistance) and not self.footer:
            # Without a closing mark the last bit's space merges into the gap
            # and its value cannot be recovered.
            raise ValueError("a PulseDistance section needs a footer mark")


@dataclass(frozen=True)
class Protocol:
    name: str
    sections: Dict[str, Section]
    carrier: int = 38000
    tolerance: float = 0.25
    mark_excess: int = 50
    trailer_gap: int = 100_000

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("a protocol needs a name")
        sections = dict(self.sections)
        if not sections:
            raise ValueError("a protocol needs at least one section")
        for key, section in sections.items():
            if not isinstance(key, str) or not key:
                raise ValueError(f"section names must be non-empty strings: {key!r}")
            if not isinstance(section, Section):
                raise ValueError(f"section {key!r} is not a Section: {section!r}")
        object.__setattr__(self, "sections", sections)
        _check_int("carrier", self.carrier, "Hz")
        if isinstance(self.tolerance, bool) or not 0 < self.tolerance < 0.5:
            raise ValueError(f"tolerance must be in (0, 0.5), got {self.tolerance!r}")
        _check_int("mark_excess", self.mark_excess, "µs", minimum=0)
        _check_int("trailer_gap", self.trailer_gap, "µs")


@dataclass(frozen=True)
class Frame:
    """Payload for one section. ``nbits`` defaults to all bits of ``data``."""

    section: str
    data: bytes
    nbits: Optional[int] = None

    def __post_init__(self):
        data = bytes(self.data)
        if not data:
            raise ValueError("frame data must not be empty")
        object.__setattr__(self, "data", data)
        nbits = 8 * len(data) if self.nbits is None else self.nbits
        _check_int("nbits", nbits, "bits")
        if not 8 * (len(data) - 1) < nbits <= 8 * len(data):
            raise ValueError(
                f"nbits={nbits} must fall within the last of {len(data)} data bytes"
            )
        object.__setattr__(self, "nbits", nbits)


@dataclass(frozen=True)
class Signal:
    """Mark, space, mark, space, ... in µs; starts with a mark, ends with a space."""

    carrier: int
    pulses: Tuple[int, ...]

    def __post_init__(self):
        _check_int("carrier", self.carrier, "Hz")
        pulses = tuple(self.pulses)
        if not pulses or len(pulses) % 2:
            raise ValueError("a signal needs a non-empty, even number of pulses")
        for i, d in enumerate(pulses):
            _check_int(f"pulses[{i}]", d, "µs")
        object.__setattr__(self, "pulses", pulses)
```

Write `pyhvac/ir/__init__.py`:

```python
"""Pure-Python IR physical layer: timings, bit encodings, encode/decode."""

from .model import (  # noqa: F401
    BitEncoding,
    Frame,
    Manchester,
    Protocol,
    PulseDistance,
    PulseWidth,
    Section,
    Signal,
)
```

In `setup.py`, change `packages=["pyhvac", "pyhvac.plugins"],` to `packages=["pyhvac", "pyhvac.ir", "pyhvac.plugins"],`.

- [ ] **Step 4: Run the tests to confirm they pass**

Run: `python -m pytest tests/test_ir_model.py -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/ir tests/test_ir_model.py setup.py
git add pyhvac/ir setup.py tests/test_ir_model.py
git commit -m "Add IR physical-layer data model

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Encoder

**Files:**
- Create: `pyhvac/ir/codec.py`
- Modify: `pyhvac/ir/__init__.py`
- Test: `tests/test_ir_encode.py`

**Interfaces:**
- Consumes: the Task 1 model.
- Produces: `pyhvac.ir.codec.encode(protocol: Protocol, frames: list[Frame]) -> Signal`, which raises `ValueError` for no frames, an unknown section, or non-zero bits past `nbits`. Also the module-private helpers `_frame_bits(frame, section) -> list[int]` and `_pack(bits: list[int], lsb_first: bool) -> bytes`, reused by Task 3.

- [ ] **Step 1: Write the failing tests** in `tests/test_ir_encode.py`

```python
import pytest

from pyhvac.ir.codec import encode
from pyhvac.ir.model import Frame, Manchester, Protocol, PulseDistance, PulseWidth, Section

NEC = Section(PulseDistance(560, 560, 1690), header=(9000, 4500), footer=(560,), gap=40000)
NEC_MSB = Section(
    PulseDistance(560, 560, 1690), header=(9000, 4500), footer=(560,), gap=40000, lsb_first=False
)
NEC_NO_GAP = Section(PulseDistance(560, 560, 1690), header=(9000, 4500), footer=(560,))
PW = Section(PulseWidth(600, 1200, 600), header=(2400, 600), gap=25000, lsb_first=False)
MAN = Section(Manchester(500))

P = Protocol(
    "test",
    {"nec": NEC, "nec_msb": NEC_MSB, "nec_no_gap": NEC_NO_GAP, "pw": PW, "man": MAN},
    carrier=36000,
)


def pulses(*frames):
    return encode(P, list(frames)).pulses


def test_pulse_distance_lsb_first():
    assert pulses(Frame("nec", b"\x01")) == (
        (9000, 4500, 560, 1690) + (560, 560) * 7 + (560, 40000)
    )


def test_pulse_distance_msb_first():
    assert pulses(Frame("nec_msb", b"\x01")) == (
        (9000, 4500) + (560, 560) * 7 + (560, 1690) + (560, 40000)
    )


def test_partial_last_byte_lsb_first():
    assert pulses(Frame("nec", b"\x05", 3)) == (
        9000, 4500, 560, 1690, 560, 560, 560, 1690, 560, 40000
    )


def test_partial_last_byte_msb_first_uses_high_bits():
    assert pulses(Frame("nec_msb", b"\xa0", 3)) == (
        9000, 4500, 560, 1690, 560, 560, 560, 1690, 560, 40000
    )


@pytest.mark.parametrize("frame", [Frame("nec", b"\x09", 3), Frame("nec_msb", b"\xa1", 3)])
def test_unused_bits_must_be_zero(frame):
    with pytest.raises(ValueError, match="unused"):
        encode(P, [frame])


def test_pulse_width_last_space_merges_into_gap():
    assert pulses(Frame("pw", b"\x80", 2)) == (2400, 600, 1200, 600, 600, 25600)


def test_trailer_gap_appended_when_ending_on_mark():
    assert pulses(Frame("nec_no_gap", b"\x00", 1)) == (9000, 4500, 560, 560, 560, 100000)


def test_manchester_merges_neighbouring_halves():
    # bits 1,1,0 -> +500 -500 +500 -500 -500 +500
    assert pulses(Frame("man", b"\x03", 3)) == (500, 500, 500, 1000, 500, 100000)


def test_leading_space_is_dropped():
    # a single 0 bit is -500 +500
    assert pulses(Frame("man", b"\x00", 1)) == (500, 100000)


def test_frames_are_concatenated():
    assert pulses(Frame("nec", b"\x01", 1), Frame("nec", b"\x00", 1)) == (
        9000, 4500, 560, 1690, 560, 40000, 9000, 4500, 560, 560, 560, 40000
    )


def test_signal_carries_protocol_carrier():
    assert encode(P, [Frame("nec", b"\x01")]).carrier == 36000


def test_unknown_section():
    with pytest.raises(ValueError, match="unknown section"):
        encode(P, [Frame("nope", b"\x01")])


def test_no_frames():
    with pytest.raises(ValueError):
        encode(P, [])
```

- [ ] **Step 2: Run the tests to confirm they fail**

Run: `python -m pytest tests/test_ir_encode.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'pyhvac.ir.codec'`

- [ ] **Step 3: Write `pyhvac/ir/codec.py`**

```python
"""Encode frames to a pulse train and decode captured pulses back to frames."""

from __future__ import annotations

from .model import Frame, Manchester, PulseDistance, PulseWidth, Signal


def _frame_bits(frame, section):
    """The frame's bits in wire order, after checking the unused bits are zero."""
    used = frame.nbits - 8 * (len(frame.data) - 1)
    if used < 8:
        unused = (0xFF << used) & 0xFF if section.lsb_first else 0xFF >> used
        if frame.data[-1] & unused:
            raise ValueError(
                f"frame for {frame.section!r}: unused bits of the last byte must be zero"
            )
    bits = []
    for i in range(frame.nbits):
        byte = frame.data[i // 8]
        shift = i % 8 if section.lsb_first else 7 - i % 8
        bits.append((byte >> shift) & 1)
    return bits


def _pack(bits, lsb_first):
    data = bytearray((len(bits) + 7) // 8)
    for i, bit in enumerate(bits):
        if bit:
            data[i // 8] |= 1 << (i % 8) if lsb_first else 0x80 >> (i % 8)
    return bytes(data)


def _alternating(durations):
    """Signed levels for a mark-first alternating tuple."""
    return [d if i % 2 == 0 else -d for i, d in enumerate(durations)]


def _section_levels(section, bits):
    levels = _alternating(section.header)
    enc = section.bits
    for bit in bits:
        if isinstance(enc, PulseDistance):
            levels += [enc.mark, -(enc.one_space if bit else enc.zero_space)]
        elif isinstance(enc, PulseWidth):
            levels += [enc.one_mark if bit else enc.zero_mark, -enc.space]
        else:
            mark_first = (bit == 1) == enc.one_is_mark_first
            levels += [enc.half, -enc.half] if mark_first else [-enc.half, enc.half]
    levels += _alternating(section.footer)
    if section.gap:
        levels.append(-section.gap)
    return levels


def _merge(levels):
    """Sum neighbouring same-polarity levels and drop a leading space."""
    merged = []
    for d in levels:
        if merged and (merged[-1] > 0) == (d > 0):
            merged[-1] += d
        else:
            merged.append(d)
    if merged and merged[0] < 0:
        merged.pop(0)
    return merged


def encode(protocol, frames):
    """Turn a list of frames into a Signal."""
    frames = list(frames)
    if not frames:
        raise ValueError("encode needs at least one frame")
    levels = []
    for frame in frames:
        try:
            section = protocol.sections[frame.section]
        except KeyError:
            raise ValueError(
                f"unknown section {frame.section!r} for protocol {protocol.name!r}"
            ) from None
        levels += _section_levels(section, _frame_bits(frame, section))
    merged = _merge(levels)
    if merged[-1] > 0:
        merged.append(-protocol.trailer_gap)
    return Signal(protocol.carrier, tuple(abs(d) for d in merged))
```

Add to `pyhvac/ir/__init__.py`:

```python
from .codec import encode  # noqa: F401
```

- [ ] **Step 4: Run the tests to confirm they pass**

Run: `python -m pytest tests/test_ir_encode.py -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/ir tests/test_ir_encode.py
git add pyhvac/ir tests/test_ir_encode.py
git commit -m "Add IR encoder

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Decoder

**Files:**
- Modify: `pyhvac/ir/codec.py`, `pyhvac/ir/__init__.py`
- Test: `tests/test_ir_decode.py`

**Interfaces:**
- Consumes: `encode`, `_pack` (Task 2); the model (Task 1).
- Produces:
  - `pyhvac.ir.codec.decode(protocol: Protocol, pulses: Sequence[int], expected: list[str] | None = None) -> list[Frame]`
  - `pyhvac.ir.codec.DecodeError(ValueError)` with attributes `index: int`, `expected: str`, `got`.
  - Bad input (empty, non-int, ≤ 0, unknown `expected` name, or a protocol with no header when `expected` is None) raises plain `ValueError`.

How decoding works: a cursor walks the pulses (marks at even indices) and may consume part of a pulse, because the encoder merges neighbouring same-level durations. Durations are compensated by `mark_excess` (subtracted from marks, added to spaces). `take()` consumes one nominal duration. When the pulse is larger and merging is allowed, it keeps the leftover: proportionally when the pulse is a near-integer multiple of the nominal (Manchester halves), otherwise by subtracting the nominal. The last header element of a Manchester section may also hold the first half-bit (`quantum`), and the nearer of "alone" and "merged" wins. The bits of a section end when its footer plus gap is next. With `gap == 0`, they end when the footer is next and no further bit can be read.

- [ ] **Step 1: Write the failing tests** in `tests/test_ir_decode.py`

```python
import random

import pytest

from pyhvac.ir.codec import DecodeError, decode, encode
from pyhvac.ir.model import Frame, Manchester, Protocol, PulseDistance, PulseWidth, Section

NEC = Section(PulseDistance(560, 560, 1690), header=(9000, 4500), footer=(560,), gap=40000)
NEC_MSB = Section(
    PulseDistance(560, 560, 1690), header=(9000, 4500), footer=(560,), gap=40000, lsb_first=False
)
PW = Section(PulseWidth(600, 1200, 600), header=(2400, 600), gap=25000, lsb_first=False)
MAN = Section(Manchester(500), header=(3000, 1000), gap=20000)
LEADER = Section(PulseDistance(430, 430, 1300), footer=(430,), gap=25000)
DAIKIN_FRAME = Section(PulseDistance(430, 430, 1300), header=(3500, 1700), footer=(430,), gap=35000)

ALL = Protocol(
    "all",
    {"nec": NEC, "nec_msb": NEC_MSB, "pw": PW, "man": MAN, "leader": LEADER, "frame": DAIKIN_FRAME},
)
NEC_ONLY = Protocol("nec", {"nec": NEC})

CASES = [
    [Frame("nec", b"\x5a\xa5\x00\xff")],
    [Frame("nec_msb", b"\x5a\xa5\x03")],
    [Frame("nec", b"\x05", 3)],
    [Frame("pw", b"\xc5\x80", 9)],
    [Frame("man", b"\xa5\x3c")],
    # first bit is 0: its first (space) half merges with the header's last space
    [Frame("man", b"\x02", 2)],
    [
        Frame("leader", b"\x00", 5),
        Frame("frame", bytes.fromhex("11da2700c5")),
        Frame("frame", bytes.fromhex("11da27004210")),
    ],
]


def names(frames):
    return [f.section for f in frames]


def jitter(pulses, seed=1234):
    rng = random.Random(seed)
    return [max(1, round(d * rng.uniform(0.9, 1.1))) for d in pulses]


@pytest.mark.parametrize("frames", CASES)
def test_round_trip_exact(frames):
    pulses = encode(ALL, frames).pulses
    assert decode(ALL, pulses, expected=names(frames)) == frames


@pytest.mark.parametrize("seed", [1, 2, 3])
@pytest.mark.parametrize("frames", CASES)
def test_round_trip_with_jitter(frames, seed):
    pulses = jitter(encode(ALL, frames).pulses, seed)
    assert decode(ALL, pulses, expected=names(frames)) == frames


def test_greedy_decode_without_expected():
    frames = [Frame("nec", b"\x12\x34")]
    assert decode(NEC_ONLY, encode(NEC_ONLY, frames).pulses) == frames


def test_repeated_message_decodes_to_two_frames_greedily():
    frame = Frame("nec", b"\x12\x34")
    pulses = encode(NEC_ONLY, [frame, frame]).pulses
    assert decode(NEC_ONLY, pulses) == [frame, frame]


def test_repeated_message_fails_strict_single_section():
    frame = Frame("nec", b"\x12\x34")
    pulses = encode(NEC_ONLY, [frame, frame]).pulses
    with pytest.raises(DecodeError):
        decode(NEC_ONLY, pulses, expected=["nec"])


def test_capture_without_trailing_gap():
    frames = [Frame("nec", b"\x12\x34")]
    pulses = encode(NEC_ONLY, frames).pulses[:-1]  # ends on the footer mark
    assert decode(NEC_ONLY, pulses, expected=["nec"]) == frames


def test_headerless_section_needs_expected():
    frames = CASES[-1]
    with pytest.raises(DecodeError):
        decode(ALL, encode(ALL, frames).pulses)


def test_protocol_without_headers_needs_expected():
    p = Protocol("leader", {"leader": LEADER})
    pulses = encode(p, [Frame("leader", b"\x00", 5)]).pulses
    with pytest.raises(ValueError, match="expected"):
        decode(p, pulses)


def test_corrupted_bit_reports_index():
    pulses = list(encode(NEC_ONLY, [Frame("nec", b"\x12")]).pulses)
    pulses[5] = 3000  # space of the second bit
    with pytest.raises(DecodeError) as err:
        decode(NEC_ONLY, pulses, expected=["nec"])
    assert err.value.index == 5


@pytest.mark.parametrize(
    "pulses", [[], [9000, -4500, 560, 560], [9000, 0, 560], [9000, 4500.0, 560]]
)
def test_invalid_pulses(pulses):
    with pytest.raises(ValueError):
        decode(NEC_ONLY, pulses, expected=["nec"])


def test_negative_pulse_error_names_index():
    with pytest.raises(ValueError, match=r"pulses\[1\]"):
        decode(NEC_ONLY, [9000, -4500, 560, 560], expected=["nec"])


def test_unknown_expected_section():
    with pytest.raises(ValueError, match="unknown section"):
        decode(NEC_ONLY, [9000, 4500], expected=["nope"])
```

- [ ] **Step 2: Run the tests to confirm they fail**

Run: `python -m pytest tests/test_ir_decode.py -q`
Expected: collection error, `ImportError: cannot import name 'DecodeError'`

- [ ] **Step 3: Add the decoder to `pyhvac/ir/codec.py`**

Add `import copy` at the top (after the `__future__` import), then append:

```python
class DecodeError(ValueError):
    """A pulse train does not match the protocol description."""

    def __init__(self, index, expected, got):
        self.index = index
        self.expected = expected
        self.got = got
        super().__init__(f"pulse {index}: expected {expected}, got {got}")


def _kind(is_mark):
    return "mark" if is_mark else "space"


class _Cursor:
    """Walks a pulse train; a pulse may be consumed in several pieces.

    Marks sit at even indices, spaces at odd ones.  ``rest`` is what is left
    of the current pulse, after demodulator compensation.
    """

    def __init__(self, protocol, pulses):
        self.tol = protocol.tolerance
        excess = protocol.mark_excess
        self.p = [d - excess if i % 2 == 0 else d + excess for i, d in enumerate(pulses)]
        self.i = 0
        self.rest = self.p[0]

    def clone(self):
        return copy.copy(self)

    def commit(self, other):
        self.i, self.rest = other.i, other.rest

    def at_end(self):
        return self.i >= len(self.p)

    def is_mark(self):
        return self.i % 2 == 0

    def done(self):
        """Nothing left but, at most, one final space (the trailing silence)."""
        return self.at_end() or (self.i == len(self.p) - 1 and not self.is_mark())

    def match(self, measured, nominal):
        return abs(measured - nominal) <= self.tol * nominal

    def _advance(self):
        self.i += 1
        self.rest = self.p[self.i] if self.i < len(self.p) else 0

    def _check_polarity(self, is_mark, expected):
        if self.is_mark() != is_mark:
            raise DecodeError(
                self.i, expected, f"{_kind(self.is_mark())} {round(self.rest)}"
            )

    def take(self, is_mark, nominal, partial=False, quantum=0):
        """Consume ``nominal`` µs of the given level.

        ``partial`` lets a longer pulse keep its leftover for what follows.
        ``quantum`` (a Manchester half) means the pulse may be either
        ``nominal`` alone or ``nominal + quantum``; the nearer one wins.
        """
        expected = f"{_kind(is_mark)} {nominal}"
        if self.at_end():
            if is_mark:
                raise DecodeError(self.i, expected, "end of signal")
            return  # captures often drop the trailing silence
        self._check_polarity(is_mark, expected)
        r = self.rest
        if quantum:
            merged = nominal + quantum
            if abs(r - merged) < abs(r - nominal):
                if not self.match(r, merged):
                    raise DecodeError(self.i, f"{expected} or {merged}", round(r))
                self.rest = r * quantum / merged
                return
        if self.match(r, nominal):
            self._advance()
            return
        if partial and r > nominal:
            k = round(r / nominal)
            if k >= 2 and abs(r - k * nominal) <= self.tol * k * nominal:
                self.rest = r * (k - 1) / k
            else:
                self.rest = r - nominal
            return
        raise DecodeError(self.i, expected, round(r))

    def classify(self, is_mark, zero, one):
        """Consume a whole pulse and return the bit whose nominal it matches."""
        expected = f"{_kind(is_mark)} {zero} or {one}"
        if self.at_end():
            raise DecodeError(self.i, expected, "end of signal")
        self._check_polarity(is_mark, expected)
        r = self.rest
        bit = 1 if abs(r - one) < abs(r - zero) else 0
        if not self.match(r, one if bit else zero):
            raise DecodeError(self.i, expected, round(r))
        self._advance()
        return bit

    def gap_ahead(self, gap):
        return self.at_end() or (
            not self.is_mark() and self.rest >= (1 - self.tol) * gap
        )

    def take_gap(self, gap):
        if not self.gap_ahead(gap):
            raise DecodeError(self.i, f"space >= {gap}", round(self.rest))
        if not self.at_end():
            self._advance()


def _read_bit(cur, enc):
    if isinstance(enc, PulseDistance):
        cur.take(True, enc.mark)
        return cur.classify(False, enc.zero_space, enc.one_space)
    if isinstance(enc, PulseWidth):
        bit = cur.classify(True, enc.zero_mark, enc.one_mark)
        cur.take(False, enc.space, partial=True)
        return bit
    if cur.at_end():
        raise DecodeError(cur.i, "Manchester bit", "end of signal")
    first_is_mark = cur.is_mark()
    cur.take(first_is_mark, enc.half, partial=True)
    cur.take(not first_is_mark, enc.half, partial=True)
    return 1 if first_is_mark == enc.one_is_mark_first else 0


def _can_read_bit(cur, enc):
    try:
        _read_bit(cur.clone(), enc)
    except DecodeError:
        return False
    return True


def _section_end(cur, section):
    """A cursor past the footer and gap if the section's bits end here, else None."""
    look = cur.clone()
    try:
        for k, d in enumerate(section.footer):
            look.take(k % 2 == 0, d, partial=True)
        if section.gap:
            look.take_gap(section.gap)
            return look
    except DecodeError:
        return None
    if look.done() or not _can_read_bit(cur, section.bits):
        return look
    return None


def _parse_section(cur, name, section):
    enc = section.bits
    for k, d in enumerate(section.header):
        last = k == len(section.header) - 1
        quantum = enc.half if last and isinstance(enc, Manchester) else 0
        cur.take(k % 2 == 0, d, partial=True, quantum=quantum)
    start = cur.i
    bits = []
    while True:
        end = _section_end(cur, section)
        if end is not None:
            cur.commit(end)
            break
        bits.append(_read_bit(cur, enc))
    if not bits:
        raise DecodeError(start, f"at least one bit of section {name!r}", "none")
    return Frame(name, _pack(bits, section.lsb_first), len(bits))


def decode(protocol, pulses, expected=None):
    """Decode unsigned µs pulses (mark first) into frames.

    With ``expected`` (section names) the sections are parsed strictly in
    that order; without it, sections with a header are tried greedily.
    """
    pulses = list(pulses)
    if not pulses:
        raise ValueError("decode needs at least one pulse")
    for i, d in enumerate(pulses):
        if isinstance(d, bool) or not isinstance(d, int) or d <= 0:
            raise ValueError(f"pulses[{i}] must be a positive integer (µs), got {d!r}")
    cur = _Cursor(protocol, pulses)
    frames = []
    if expected is not None:
        for name in expected:
            if name not in protocol.sections:
                raise ValueError(
                    f"unknown section {name!r} for protocol {protocol.name!r}"
                )
            frames.append(_parse_section(cur, name, protocol.sections[name]))
    else:
        headed = [(n, s) for n, s in protocol.sections.items() if s.header]
        if not headed:
            raise ValueError(
                f"protocol {protocol.name!r} has no section with a header; pass expected="
            )
        while not cur.done():
            for name, section in headed:
                look = cur.clone()
                try:
                    frame = _parse_section(look, name, section)
                except DecodeError:
                    continue
                cur.commit(look)
                frames.append(frame)
                break
            else:
                raise DecodeError(
                    cur.i,
                    "header of " + " or ".join(repr(n) for n, _ in headed),
                    round(cur.rest),
                )
    if not cur.done():
        raise DecodeError(cur.i, "end of signal", round(cur.rest))
    return frames
```

Update `pyhvac/ir/__init__.py`: change the codec import to `from .codec import DecodeError, decode, encode  # noqa: F401`.

- [ ] **Step 4: Run the tests to confirm they pass**

Run: `python -m pytest tests/test_ir_decode.py tests/test_ir_encode.py -q`
Expected: all pass. If a jitter case fails, print the failing `DecodeError` (index, expected, got) and fix the decoder. Do not loosen the jitter range or the tolerance.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/ir tests/test_ir_decode.py
git add pyhvac/ir tests/test_ir_decode.py
git commit -m "Add IR decoder

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Edge formatters

**Files:**
- Create: `pyhvac/ir/formats.py`
- Test: `tests/test_ir_formats.py`

**Interfaces:**
- Consumes: `Signal` (Task 1), `encode` (Task 2, tests only).
- Produces (`pyhvac.ir.formats`):
  - `broadlink_packet(pulses: Sequence[int]) -> bytes`: packet from any pulse list (used by the legacy `HVAC.to_broadlink`, whose C-backed pulse lists need not satisfy `Signal`).
  - `to_broadlink(signal: Signal) -> bytes`
  - `to_pronto(signal: Signal) -> str`
  - `to_raw(signal: Signal) -> list[int]`
  - `from_broadlink(data: bytes) -> list[int]`
  - `from_pronto(text: str) -> list[int]`

- [ ] **Step 1: Write the failing tests** in `tests/test_ir_formats.py`

```python
import pytest

from pyhvac.ir.codec import encode
from pyhvac.ir.formats import (
    broadlink_packet,
    from_broadlink,
    from_pronto,
    to_broadlink,
    to_pronto,
    to_raw,
)
from pyhvac.ir.model import Frame, Protocol, PulseDistance, Section, Signal

SMALL = Signal(38000, (9000, 4500, 560, 1690, 560, 40000))

# Output of HVAC().to_lirc([bytearray(b"\x12\x34")]) with the pre-migration code
LEGACY_PULSES = (
    [3500, 1750]
    + [435, 435, 435, 435, 435, 435, 435, 1300, 435, 435, 435, 435, 435, 1300, 435, 435]
    + [435, 435, 435, 435, 435, 1300, 435, 1300, 435, 435, 435, 1300, 435, 435, 435, 435]
    + [435, 10000]
)
# ... and the matching HVAC().to_broadlink output
LEGACY_BROADLINK = (
    "2600260073390e0e0e0e0e0e0e2b0e0e0e0e0e2b0e0e0e0e0e0e0e2b0e2b0e0e0e2b0e0e0e0e0e0001480d05"
)

NEC = Protocol(
    "nec",
    {"nec": Section(PulseDistance(560, 560, 1690), header=(9000, 4500), footer=(560,), gap=40000)},
)


def test_broadlink_matches_legacy_implementation():
    assert to_broadlink(Signal(38000, tuple(LEGACY_PULSES))).hex() == LEGACY_BROADLINK
    assert broadlink_packet(LEGACY_PULSES).hex() == LEGACY_BROADLINK


def test_broadlink_small_signal_uses_two_byte_escape():
    assert to_broadlink(SMALL).hex() == "26000a00000128941237120005210d05" + "00" * 12


def test_from_broadlink_quantises_to_broadlink_units():
    data = bytes.fromhex("26000a00000128941237120005210d05" + "00" * 12)
    assert from_broadlink(data) == [9014, 4507, 548, 1675, 548, 39985]


def test_broadlink_round_trip_within_quantisation():
    signal = encode(NEC, [Frame("nec", b"\x5a\xa5\x12")])
    back = from_broadlink(to_broadlink(signal))
    assert len(back) == len(signal.pulses)
    assert all(abs(a - b) <= 16 for a, b in zip(back, signal.pulses))


def test_from_broadlink_rejects_non_ir_packet():
    with pytest.raises(ValueError):
        from_broadlink(bytes.fromhex("b2000200"))


def test_from_broadlink_rejects_truncated_packet():
    with pytest.raises(ValueError):
        from_broadlink(bytes.fromhex("26000a000001"))


def test_pronto():
    assert to_pronto(SMALL) == "0000 006D 0003 0000 0156 00AB 0015 0040 0015 05F1"


def test_from_pronto():
    text = "0000 006D 0003 0000 0156 00AB 0015 0040 0015 05F1"
    assert from_pronto(text) == [8993, 4497, 552, 1683, 552, 39996]


def test_pronto_round_trip_within_one_unit():
    signal = encode(NEC, [Frame("nec", b"\x5a\xa5\x12")])
    back = from_pronto(to_pronto(signal))
    assert all(abs(a - b) <= 14 for a, b in zip(back, signal.pulses))


def test_from_pronto_rejects_non_learned_codes():
    with pytest.raises(ValueError):
        from_pronto("5000 0073 0000 0001 0001 0001")


def test_from_pronto_rejects_short_body():
    with pytest.raises(ValueError):
        from_pronto("0000 006D 0003 0000 0156 00AB")


def test_raw_is_signed():
    assert to_raw(SMALL) == [9000, -4500, 560, -1690, 560, -40000]
```

- [ ] **Step 2: Run the tests to confirm they fail**

Run: `python -m pytest tests/test_ir_formats.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'pyhvac.ir.formats'`

- [ ] **Step 3: Write `pyhvac/ir/formats.py`**

```python
"""Edge formatters: convert a Signal to and from device-specific formats."""

from __future__ import annotations

import struct

# One Broadlink tick is 8192/269 µs (~30.45 µs).
_BROADLINK_TICK_NUM = 269
_BROADLINK_TICK_DEN = 8192
# One Pronto unit is (frequency word * 0.241246) µs.
_PRONTO_CLOCK = 0.241246


def broadlink_packet(pulses):
    """Broadlink IR packet for any mark/space pulse list in µs."""
    body = bytearray()
    for pulse in pulses:
        ticks = round(int(pulse) * _BROADLINK_TICK_NUM / _BROADLINK_TICK_DEN)
        if ticks < 256:
            body += struct.pack(">B", ticks)
        else:
            body += b"\x00" + struct.pack(">H", ticks)  # 0x00 escapes a 2-byte value
    packet = bytearray([0x26, 0x00])  # 0x26 = IR, 0x00 = no repeat
    packet += struct.pack("<H", len(body))
    packet += body
    packet += bytes([0x0D, 0x05])
    # The device prepends a 4-byte header and AES-encrypts in 16-byte blocks.
    remainder = (len(packet) + 4) % 16
    if remainder:
        packet += bytes(16 - remainder)
    return bytes(packet)


def to_broadlink(signal):
    return broadlink_packet(signal.pulses)


def from_broadlink(data):
    """µs pulses from a Broadlink IR packet (e.g. a learned code)."""
    data = bytes(data)
    if len(data) < 4 or data[0] != 0x26:
        raise ValueError("not a Broadlink IR packet (expected 0x26 header)")
    (length,) = struct.unpack("<H", data[2:4])
    body = data[4 : 4 + length]
    if len(body) < length:
        raise ValueError("truncated Broadlink packet")
    pulses = []
    i = 0
    while i < len(body):
        ticks = body[i]
        i += 1
        if ticks == 0:
            if i + 2 > len(body):
                raise ValueError("truncated 2-byte value in Broadlink packet")
            (ticks,) = struct.unpack(">H", body[i : i + 2])
            i += 2
        pulses.append(round(ticks * _BROADLINK_TICK_DEN / _BROADLINK_TICK_NUM))
    return pulses


def to_pronto(signal):
    """Learned-format (0000) Pronto hex."""
    freq = round(1_000_000 / (signal.carrier * _PRONTO_CLOCK))
    unit = freq * _PRONTO_CLOCK
    words = [0x0000, freq, len(signal.pulses) // 2, 0x0000]
    words += [round(d / unit) for d in signal.pulses]
    return " ".join(f"{w:04X}" for w in words)


def from_pronto(text):
    """µs pulses from a learned-format (0000) Pronto hex string."""
    words = [int(w, 16) for w in text.split()]
    if len(words) < 4 or words[0] != 0x0000:
        raise ValueError("only learned (0000) Pronto codes are supported")
    freq, once, repeat = words[1], words[2], words[3]
    count = 2 * (once + repeat)
    body = words[4 : 4 + count]
    if len(body) != count:
        raise ValueError(f"Pronto code announces {count} durations, has {len(body)}")
    unit = freq * _PRONTO_CLOCK
    return [round(w * unit) for w in body]


def to_raw(signal):
    """Signed µs list: positive marks, negative spaces."""
    return [d if i % 2 == 0 else -d for i, d in enumerate(signal.pulses)]
```

- [ ] **Step 4: Run the tests to confirm they pass**

Run: `python -m pytest tests/test_ir_formats.py -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/ir tests/test_ir_formats.py
git add pyhvac/ir/formats.py tests/test_ir_formats.py
git commit -m "Add Broadlink, Pronto and raw edge formatters

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Golden fixtures for the pure-Python plugins

Pins today's wire output before anything is migrated. Must be generated from the *unmodified* plugin code (only the import change below).

**Files:**
- Modify: `pyhvac/plugins/sharp.py:33`, `pyhvac/plugins/lg.py:32`, `pyhvac/plugins/panasonic.py:34-41`: tolerate a missing `irhvac`.
- Create: `tools/state_grid.py`, `tools/golden_generate.py`, `tests/conftest.py`, `tests/test_golden_native.py`
- Create (generated): `tests/fixtures/golden/{airspool,sharp,daikin,panasonic,lg}.json.gz`

**Interfaces:**
- Consumes: the existing plugins.
- Produces:
  - `state_grid.state_grid(capabilities: dict, extra: dict | None = None, limit: int = 200) -> list[dict]`
  - `state_grid.build_native(cls, state: dict) -> tuple[HVAC, list]`: a fresh device with `state` applied through `set_value` (mode last), and its `build_ircode()` result.
  - `state_grid.NATIVE: dict[str, list[str]]`: module name → class names covered by golden fixtures.
  - Fixture record: `{"class": str, "state": dict, "pulses": list[int], "broadlink": str}` (hex).

- [ ] **Step 1: Make the native plugin modules importable without the C extension**

Only the C-backed classes use these constants, so a `None` fallback is safe; `hvaclib.py:34-41` already does the same for `irhvac`.

In `pyhvac/plugins/sharp.py` replace line 33 with:

```python
try:
    from ..irhvac import A907, A903, A705
except ImportError:
    # Only the C-backed classes use these; keep the pure-Python ones importable.
    A907 = A903 = A705 = None
```

In `pyhvac/plugins/lg.py` replace line 32 with:

```python
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
```

In `pyhvac/plugins/panasonic.py` replace the `from ..irhvac import (...)` block with:

```python
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
```

Verify: `python -c "import pyhvac.plugins.sharp, pyhvac.plugins.lg, pyhvac.plugins.panasonic, pyhvac.plugins.daikin, pyhvac.plugins.airspool"`
Expected: no output, exit 0.

- [ ] **Step 2: Write `tools/state_grid.py`**

This file must not import `pyhvac`: the oracle generator (Task 9) imports it while running against an installed release.

```python
"""Deterministic grids of device states for golden and oracle fixtures."""

import itertools

# Pure-Python classes covered by golden fixtures: module -> class names.
# The generic Sharp class is left out: its build_ircode() raises KeyError.
NATIVE = {
    "airspool": ["Airspool"],
    "sharp": ["JTech"],
    "daikin": ["Daikinth", "Smash2"],
    "panasonic": ["Panasonic", "PanaCassette"],
    "lg": ["LG", "InverterV", "DualInverter"],
}


def _temperatures(values):
    """min, middle, max of a temperature capability.

    Pure-Python plugins list every value; C-backed ones give [min, max].
    """
    values = list(values)
    lo, hi = values[0], values[-1]
    mid = values[len(values) // 2] if len(values) > 2 else (lo + hi) // 2
    return sorted({lo, mid, hi})


def state_grid(capabilities, extra=None, limit=200):
    """States covering mode x temperature x fan x swing, plus each other
    capability set once to each non-default value, at most ``limit`` in all."""
    caps = dict(capabilities)
    caps.update(extra or {})
    temps = _temperatures(caps["temperature"])
    axes = [("mode", list(caps["mode"])), ("temperature", temps)]
    for key in ("fan", "swing"):
        if key in caps:
            axes.append((key, list(caps[key])))
    names = [name for name, _ in axes]

    active = next((m for m in caps["mode"] if m != "off"), caps["mode"][0])
    base = {"mode": active, "temperature": temps[len(temps) // 2]}
    extras = []
    for key, values in caps.items():
        if key in names:
            continue
        for value in list(values)[1:]:
            extras.append({**base, key: value})

    main = [dict(zip(names, combo)) for combo in itertools.product(*(v for _, v in axes))]
    room = max(limit - len(extras), 1)
    if len(main) > room:
        step = len(main) / room
        main = [main[int(i * step)] for i in range(room)]
    return (main + extras)[:limit]


def build_native(cls, state):
    """Fresh device with ``state`` applied (mode last) and its frames."""
    dev = cls()
    for key, value in state.items():
        if key != "mode":
            dev.set_value(key, value)
    dev.set_value("mode", state["mode"])
    return dev, dev.build_ircode()
```

- [ ] **Step 3: Write `tools/golden_generate.py`**

```python
"""Record the current wire output of the pure-Python plugins.

Run from the repo root:  python tools/golden_generate.py
"""

import gzip
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from state_grid import NATIVE, build_native, state_grid  # noqa: E402

OUT = ROOT / "tests" / "fixtures" / "golden"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for module, classes in NATIVE.items():
        mod = importlib.import_module(f"pyhvac.plugins.{module}")
        records = []
        for name in classes:
            cls = getattr(mod, name)
            probe = cls()
            for state in state_grid(probe.capabilities, probe.xtra_capabilities):
                dev, frames = build_native(cls, state)
                records.append(
                    {
                        "class": name,
                        "state": state,
                        "pulses": [int(x) for x in dev.to_lirc(frames)],
                        "broadlink": dev.to_broadlink(frames).hex(),
                    }
                )
        path = OUT / f"{module}.json.gz"
        path.write_bytes(gzip.compress(json.dumps(records).encode(), mtime=0))
        print(f"{module}: {len(records)} records -> {path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Generate the fixtures**

Run: `python tools/golden_generate.py`
Expected: one line per module (airspool, sharp, daikin, panasonic, lg), each with a non-zero record count, and no traceback.

- [ ] **Step 5: Write `tests/conftest.py` and `tests/test_golden_native.py`**

`tests/conftest.py`:

```python
import sys
from pathlib import Path

# tools/ holds helpers shared by the fixture generators and the tests.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
```

`tests/test_golden_native.py`:

```python
import gzip
import importlib
import json
from pathlib import Path

import pytest

from state_grid import NATIVE, build_native

FIXTURES = Path(__file__).parent / "fixtures" / "golden"


def _records():
    for module in NATIVE:
        path = FIXTURES / f"{module}.json.gz"
        for n, record in enumerate(json.loads(gzip.decompress(path.read_bytes()))):
            yield pytest.param(module, record, id=f"{module}-{record['class']}-{n}")


RECORDS = list(_records())


def test_every_native_module_has_fixtures():
    assert {p.values[0] for p in RECORDS} == set(NATIVE)


@pytest.mark.parametrize("module, record", RECORDS)
def test_native_wire_output_unchanged(module, record):
    cls = getattr(importlib.import_module(f"pyhvac.plugins.{module}"), record["class"])
    dev, frames = build_native(cls, record["state"])
    assert [int(x) for x in dev.to_lirc(frames)] == record["pulses"]
    assert dev.to_broadlink(frames).hex() == record["broadlink"]
```

- [ ] **Step 6: Run the full suite**

Run: `python -m pytest -q`
Expected: all pass, including every golden record and the existing `tests/test_airspool.py`.

- [ ] **Step 7: Format and commit**

```bash
black pyhvac/plugins/sharp.py pyhvac/plugins/lg.py pyhvac/plugins/panasonic.py tools tests/conftest.py tests/test_golden_native.py
git add pyhvac/plugins/sharp.py pyhvac/plugins/lg.py pyhvac/plugins/panasonic.py tools tests/conftest.py tests/test_golden_native.py tests/fixtures/golden
git commit -m "Pin current pure-Python plugin output with golden fixtures

Make the Sharp, LG and Panasonic modules importable without the C
extension so their pure-Python classes can be tested anywhere.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: `HVAC` integration

**Files:**
- Modify: `pyhvac/plugins/hvaclib.py` (`HVAC` class, lines 48-150)
- Test: `tests/test_hvac_protocol.py`

**Interfaces:**
- Consumes: `encode` (Task 2), `Frame`/`Signal` (Task 1), `broadlink_packet` (Task 4).
- Produces, on `HVAC`:
  - `PROTOCOL = None`: a class attribute; a `pyhvac.ir.Protocol` on migrated plugins.
  - `build_signal() -> Signal`: raises `NotImplementedError` when `PROTOCOL` is None.
  - `to_lirc(frames) -> list[int]` and `to_broadlink(frames) -> bytearray`, unchanged signatures.
  - `build_ircode()` no longer bit-reverses when `PROTOCOL` is set; bit order then comes from `Section.lsb_first`.
  - A bare `bytes`/`bytearray` frame maps to the protocol's first section.
  - `get_timing` is removed from `HVAC`; it has no callers.

- [ ] **Step 1: Write the failing tests** in `tests/test_hvac_protocol.py`

```python
import pytest

from pyhvac.ir.codec import encode
from pyhvac.ir.formats import to_broadlink
from pyhvac.ir.model import Frame, Protocol, PulseDistance, Section
from pyhvac.plugins.hvaclib import HVAC

TOY = Protocol(
    "toy",
    {
        "main": Section(PulseDistance(500, 500, 1500), header=(4000, 2000), footer=(500,), gap=20000),
        "short": Section(PulseDistance(500, 500, 1500), header=(2000, 1000), footer=(500,), gap=20000),
    },
)
TOY_PULSES = [4000, 2000, 500, 1500] + [500, 500] * 7 + [500, 20000]


class Toy(HVAC):
    PROTOCOL = TOY

    def __init__(self):
        super().__init__()
        self.is_msb = True  # must be ignored once PROTOCOL is set

    def _build_ircode(self):
        return [bytearray(b"\x01")]


def test_to_lirc_encodes_bytearray_frames_with_first_section():
    assert Toy().to_lirc([bytearray(b"\x01")]) == TOY_PULSES


def test_to_lirc_accepts_frame_objects():
    frames = [Frame("short", b"\x01", 1)]
    assert Toy().to_lirc(frames) == list(encode(TOY, frames).pulses)


def test_build_ircode_does_not_bit_reverse_with_protocol():
    assert Toy().build_ircode() == [bytearray(b"\x01")]


def test_build_signal():
    assert Toy().build_signal().pulses == tuple(TOY_PULSES)


def test_to_broadlink_goes_through_formatter():
    dev = Toy()
    assert dev.to_broadlink([bytearray(b"\x01")]) == to_broadlink(dev.build_signal())


def test_legacy_class_output_unchanged():
    dev = HVAC()
    frames = [bytearray(b"\x12\x34")]
    assert dev.to_lirc(frames)[:4] == [3500, 1750, 435, 435]
    assert dev.to_broadlink(frames).hex() == (
        "2600260073390e0e0e0e0e0e0e2b0e0e0e0e0e2b0e0e0e0e0e0e0e2b0e2b0e0e0e2b0e0e0e0e0e0001480d05"
    )


def test_build_signal_needs_protocol():
    with pytest.raises(NotImplementedError):
        HVAC().build_signal()
```

- [ ] **Step 2: Run the tests to confirm they fail**

Run: `python -m pytest tests/test_hvac_protocol.py -q`
Expected: failures. `to_lirc` ignores `PROTOCOL`, and `build_signal` does not exist.

- [ ] **Step 3: Modify `HVAC` in `pyhvac/plugins/hvaclib.py`**

Add below `import struct`:

```python
from ..ir.codec import encode
from ..ir.formats import broadlink_packet
from ..ir.model import Frame
```

In `class HVAC`, below the `SPACE = [435, 1300]` line, add:

```python
    # pyhvac.ir.Protocol describing the physical layer. When None, the legacy
    # STARTFRAME/MARK/SPACE/ENDFRAME attributes above are used instead.
    PROTOCOL = None
```

Delete the `get_timing` method.

Replace `build_ircode`, `to_lirc` and `to_broadlink` with:

```python
    def build_ircode(self):
        frames = self._build_ircode()
        if self.is_msb and self.PROTOCOL is None:
            frames = [bytearray([bit_reverse(x) for x in f]) for f in frames]
        return frames

    def _as_frames(self, frames):
        """Frame objects; bare bytes go to the protocol's first section."""
        default = next(iter(self.PROTOCOL.sections))
        return [f if isinstance(f, Frame) else Frame(default, bytes(f)) for f in frames]

    def build_signal(self):
        if self.PROTOCOL is None:
            raise NotImplementedError(f"{type(self).__name__} has no PROTOCOL")
        return encode(self.PROTOCOL, self._as_frames(self.build_ircode()))

    def to_lirc(self, frames):
        """Transform a list of frames into a LIRC compatible list of pulse timings."""
        if self.PROTOCOL is not None:
            return list(encode(self.PROTOCOL, self._as_frames(frames)).pulses)
        lircframe = []
        for frame in frames:
            lircframe += self.STARTFRAME
            for x in frame:
                idx = 0x80
                while idx:
                    if x & idx:
                        lircframe.append(self.MARK[-1])
                        lircframe.append(self.SPACE[-1])
                    else:
                        lircframe.append(self.MARK[0])
                        lircframe.append(self.SPACE[0])
                    idx >>= 1
            lircframe += self.ENDFRAME
        return lircframe

    def to_broadlink(self, frames):
        """Transform a list of frames to a Broadlink compatible byte string."""
        return bytearray(broadlink_packet([int(x) for x in self.to_lirc(frames)]))
```

`IRGHVAC` overrides `to_lirc` and `build_ircode` and leaves `PROTOCOL` as None, so its behaviour does not change.

- [ ] **Step 4: Run the full suite**

Run: `python -m pytest -q`
Expected: all pass, including the golden fixtures (no plugin output changed).

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/hvaclib.py tests/test_hvac_protocol.py
git add pyhvac/plugins/hvaclib.py tests/test_hvac_protocol.py
git commit -m "Let HVAC plugins describe their physical layer with a Protocol

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Migrate Airspool

**Files:**
- Modify: `pyhvac/plugins/airspool.py` (class docstring lines 36-40, timing attributes 81-88, `self.is_msb = True` at 152, `decode_pulse` 342-370, import line 32)
- Test: `tests/test_airspool.py` (existing, unchanged) and `tests/test_golden_native.py`

**Interfaces:**
- Consumes: `HVAC.PROTOCOL` (Task 6), `decode` (Task 3), the model (Task 1).
- Produces: `pyhvac.plugins.airspool.AIRSPOOL: Protocol` with the single section `"main"`; `Airspool.PROTOCOL = AIRSPOOL`; `Airspool.decode_pulse(pulse, endian="msb") -> bytearray` (logical 14-byte frame, same as before).

- [ ] **Step 1: Declare the protocol**

Change the import at line 32 to:

```python
from .hvaclib import HVAC, GenPluginObject
from ..ir.codec import decode
from ..ir.model import Protocol, PulseDistance, Section
```

Above `class Airspool`, add:

```python
# Physical layer: 38 kHz, pulse-distance, LSB-first within each byte.
AIRSPOOL = Protocol(
    "airspool",
    {
        "main": Section(
            PulseDistance(480, 360, 1180),
            header=(3200, 1400),
            # Final stop mark, then a long trailing gap before any repeat.  The
            # exact gap length is not part of the documented capture; 100 ms is
            # a safe value.
            footer=(480,),
            gap=100_000,
            lsb_first=True,
        )
    },
)
```

In the class, replace the block from `# Physical-layer timings (microseconds).` through `SPACE = [360, 1180]  # SPACE[0] -> bit 0, SPACE[-1] -> bit 1` with:

```python
    PROTOCOL = AIRSPOOL
```

Delete `self.is_msb = True` in `__init__`.

In the class docstring, replace:

```
    Physical layer: 38 kHz carrier, pulse-distance encoding, LSB-first within
    each byte (handled by ``is_msb`` which swaps the bit order at build time so
    the MSB-first emitter in :class:`HVAC` produces an LSB-first wire stream).
```

with:

```
    Physical layer (see ``AIRSPOOL``): 38 kHz carrier, pulse-distance
    encoding, LSB-first within each byte.
```

- [ ] **Step 2: Rewrite `decode_pulse`**

```python
    def decode_pulse(self, pulse, endian="msb"):
        """Decode an Airspool pulse train back into the logical 14-byte frame."""
        frames = decode(self.PROTOCOL, [int(x) for x in pulse], expected=["main"])
        return bytearray(frames[0].data)
```

Check with `grep -n bit_reverse pyhvac/plugins/airspool.py` that nothing else in the file uses `bit_reverse`; the import was dropped in Step 1.

- [ ] **Step 3: Run the tests**

Run: `python -m pytest tests/test_airspool.py tests/test_golden_native.py -q -k "airspool or Airspool"`
Expected: all pass. The golden records show that the Airspool wire output is byte-identical.

- [ ] **Step 4: Run the full suite**

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Format and commit**

```bash
black pyhvac/plugins/airspool.py
git add pyhvac/plugins/airspool.py
git commit -m "Airspool: describe the physical layer with a Protocol

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Migrate the native Sharp, Daikin, Panasonic and LG classes

For each class, the legacy emitter wrote `STARTFRAME` + each byte MSB-first (after `bit_reverse` when `is_msb` was True) + `ENDFRAME`. In the equivalent `Section`, `header = STARTFRAME`, `footer = (ENDFRAME[0],)`, `gap = ENDFRAME[1]`, and `lsb_first = is_msb`. `Daikinth` and `Panasonic` use the `HVAC` defaults (`[3500, 1750]`, `[435, 10000]`, `[435]`, `[435, 1300]`). LG keeps 32 bits per frame (see Known issues).

**Files:**
- Modify: `pyhvac/plugins/sharp.py` (`Sharp` timing attributes 40-43, `self.is_msb = True` at 59, `get_timing` 333-340)
- Modify: `pyhvac/plugins/daikin.py` (`Daikinth`, `self.is_msb = False` at 55)
- Modify: `pyhvac/plugins/panasonic.py` (`Panasonic`, `self.is_msb = False` at 71)
- Modify: `pyhvac/plugins/lg.py` (`LG` timing attributes 39-42, `self.is_msb = False` at 58, `get_timing` 388-398)
- Test: `tests/test_golden_native.py` (extended)

**Interfaces:**
- Consumes: `HVAC.PROTOCOL` (Task 6), `decode` (Task 3).
- Produces: module constants `sharp.SHARP_NATIVE`, `daikin.DAIKIN_NATIVE`, `panasonic.PANASONIC_NATIVE`, `lg.LG_NATIVE` (each a `Protocol` with the single section `"main"`), set as `PROTOCOL` on `Sharp`, `Daikinth`, `Panasonic` and `LG`. Subclasses (`JTech`, `Smash2`, `PanaCassette`, `InverterV`, `DualInverter`) inherit it.

- [ ] **Step 1: Extend the golden test to also decode every record** (append to `tests/test_golden_native.py`)

```python
from pyhvac.ir.codec import decode
from pyhvac.ir.model import Frame


@pytest.mark.parametrize("module, record", RECORDS)
def test_native_protocol_decodes_its_own_output(module, record):
    cls = getattr(importlib.import_module(f"pyhvac.plugins.{module}"), record["class"])
    if cls.PROTOCOL is None:
        pytest.skip(f"{cls.__name__} not migrated yet")
    dev, frames = build_native(cls, record["state"])
    expected = [Frame("main", bytes(f)) for f in frames]
    assert decode(cls.PROTOCOL, record["pulses"], expected=["main"] * len(frames)) == expected
```

Run: `python -m pytest tests/test_golden_native.py -q`
Expected: pass. Airspool records decode; the other modules skip.

- [ ] **Step 2: Sharp**

In `pyhvac/plugins/sharp.py`, extend the hvaclib import line with the IR imports:

```python
from ..ir.model import Protocol, PulseDistance, Section
```

Above `class Sharp`, add:

```python
SHARP_NATIVE = Protocol(
    "sharp",
    {
        "main": Section(
            PulseDistance(435, 435, 1400),
            header=(3800, 1900),
            footer=(435,),
            gap=10000,
            lsb_first=True,
        )
    },
)
```

In `Sharp`, replace the four lines `STARTFRAME = [3800, 1900]` … `SPACE = [435, 1400]` with `PROTOCOL = SHARP_NATIVE`. Delete `self.is_msb = True` and the whole `get_timing` method of `Sharp`. Do not touch `SharpA907`/`SharpA903`/`SharpA705`: they are C-backed and keep their own attributes.

- [ ] **Step 3: Daikin**

In `pyhvac/plugins/daikin.py`, add `from ..ir.model import Protocol, PulseDistance, Section` after the hvaclib import, and above `class Daikinth`:

```python
DAIKIN_NATIVE = Protocol(
    "daikin-native",
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

In `Daikinth`, add `PROTOCOL = DAIKIN_NATIVE` above `FBODY = ...`, and delete the comment line `# Specify wether the bits order has to be swapped` together with `self.is_msb = False` below it.

- [ ] **Step 4: Panasonic**

In `pyhvac/plugins/panasonic.py`, add `from ..ir.model import Protocol, PulseDistance, Section` after the hvaclib import, and above `class Panasonic`:

```python
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

In `Panasonic`, add `PROTOCOL = PANASONIC_NATIVE` above `FHEADER = ...`, and delete the comment `# Specify wether the bits order has to be swapped` with `self.is_msb = False`.

- [ ] **Step 5: LG**

In `pyhvac/plugins/lg.py`, add `from ..ir.model import Protocol, PulseDistance, Section` after the hvaclib import, and above `class LG`:

```python
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

In `LG`, replace `STARTFRAME = [3100, 9850]` … `SPACE = [520, 1530]` with `PROTOCOL = LG_NATIVE`. Delete the `self.is_msb = False` line (and its comment line, if present), and delete the `get_timing` method. Leave the C-backed `LGv1`/`LGv2`/`LG2v*` classes alone.

- [ ] **Step 6: Run the full suite**

Run: `python -m pytest -q`
Expected: all pass. Every golden record reproduces byte-identical `to_lirc`/`to_broadlink` output, and `test_native_protocol_decodes_its_own_output` passes (no skips) for every module.

If a golden record differs, compare `record["pulses"]` with the new output at the first differing index. The usual cause is a wrong `lsb_first` (it must equal the class's old `is_msb`) or a timing attribute the subclass overrode.

- [ ] **Step 7: Format and commit**

```bash
black pyhvac/plugins/sharp.py pyhvac/plugins/daikin.py pyhvac/plugins/panasonic.py pyhvac/plugins/lg.py tests/test_golden_native.py
git add pyhvac/plugins/sharp.py pyhvac/plugins/daikin.py pyhvac/plugins/panasonic.py pyhvac/plugins/lg.py tests/test_golden_native.py
git commit -m "Move native Sharp, Daikin, Panasonic and LG onto Protocol

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: C-oracle generator, fixtures and test helper

**Files:**
- Create: `tools/oracle_generate.py`, `tests/oracle.py`, `tests/test_oracle_support.py`
- Create (generated): `tests/fixtures/oracle/<PROTOCOL>.json.gz`

**Interfaces:**
- Consumes: `state_grid.state_grid` (Task 5), `encode`/`decode` (Tasks 2-3).
- Produces:
  - Fixture record: `{"plugin": str, "model": str, "class": str, "variant": str | None, "state": dict, "pulses": list[int]}`, one file per IRremoteESP8266 protocol name (e.g. `DAIKIN.json.gz`).
  - `tests/oracle.py`: `ORACLE_DIR: Path`, `load_oracle(protocol_name: str) -> list[dict]`, and `check_against_oracle(protocol: Protocol, record: dict, frames: list[Frame]) -> None`, which raises `AssertionError` or `DecodeError`. The family-port plans use these.

- [ ] **Step 1: Write the failing helper tests** in `tests/test_oracle_support.py`

```python
import gzip
import json
import random

import pytest

from oracle import ORACLE_DIR, check_against_oracle, load_oracle
from pyhvac.ir.codec import DecodeError, encode
from pyhvac.ir.model import Frame, Protocol, PulseDistance, Section

NEC = Protocol(
    "nec",
    {"nec": Section(PulseDistance(560, 560, 1690), header=(9000, 4500), footer=(560,), gap=40000)},
)
FRAMES = [Frame("nec", b"\x12\x34")]


def record(pulses):
    return {"state": {}, "pulses": list(pulses)}


def test_accepts_matching_jittered_record():
    rng = random.Random(7)
    pulses = [round(d * rng.uniform(0.95, 1.05)) for d in encode(NEC, FRAMES).pulses]
    check_against_oracle(NEC, record(pulses), FRAMES)


def test_rejects_different_bytes():
    pulses = encode(NEC, [Frame("nec", b"\x12\x35")]).pulses
    with pytest.raises(AssertionError):
        check_against_oracle(NEC, record(pulses), FRAMES)


def test_rejects_different_timing():
    pulses = [d * 2 for d in encode(NEC, FRAMES).pulses]
    with pytest.raises((AssertionError, DecodeError)):
        check_against_oracle(NEC, record(pulses), FRAMES)


def test_load_oracle_reads_gzipped_json(tmp_path, monkeypatch):
    monkeypatch.setattr("oracle.ORACLE_DIR", tmp_path)
    (tmp_path / "NEC.json.gz").write_bytes(gzip.compress(json.dumps([record([1, 2])]).encode()))
    assert load_oracle("NEC") == [record([1, 2])]


FILES = sorted(ORACLE_DIR.glob("*.json.gz"))


@pytest.mark.parametrize("path", FILES, ids=[p.name for p in FILES])
def test_fixture_is_well_formed(path):
    records = json.loads(gzip.decompress(path.read_bytes()))
    assert records
    for rec in records:
        assert {"plugin", "model", "class", "variant", "state", "pulses"} <= set(rec)
        assert rec["pulses"]
        assert all(isinstance(d, int) and d > 0 for d in rec["pulses"])
```

- [ ] **Step 2: Run the tests to confirm they fail**

Run: `python -m pytest tests/test_oracle_support.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'oracle'`

- [ ] **Step 3: Write `tests/oracle.py`**

```python
"""Helpers to compare a Python protocol port against recorded C output."""

import gzip
import json
from pathlib import Path

from pyhvac.ir.codec import decode, encode

ORACLE_DIR = Path(__file__).parent / "fixtures" / "oracle"


def load_oracle(protocol_name):
    return json.loads(gzip.decompress((ORACLE_DIR / f"{protocol_name}.json.gz").read_bytes()))


def check_against_oracle(protocol, record, frames):
    """The C pulses decode to ``frames`` and our encoding lines up with them."""
    names = [f.section for f in frames]
    assert decode(protocol, record["pulses"], expected=names) == frames, record["state"]
    ours = encode(protocol, frames).pulses
    theirs = record["pulses"]
    assert len(ours) == len(theirs), (record["state"], len(ours), len(theirs))
    for i, (a, b) in enumerate(zip(ours, theirs)):
        assert abs(a - b) <= protocol.tolerance * a, (record["state"], i, a, b)
```

- [ ] **Step 4: Run the helper tests**

Run: `python -m pytest tests/test_oracle_support.py -q`
Expected: all pass. There are no fixture files yet, so `test_fixture_is_well_formed` collects nothing.

- [ ] **Step 5: Write `tools/oracle_generate.py`**

```python
"""Record the pulse trains the IRremoteESP8266 C library produces.

Runs against an INSTALLED pyhvac release that includes the compiled irhvac
extension, never against this checkout:

    python -m venv /tmp/oracle-venv
    /tmp/oracle-venv/bin/pip install "pyhvac>=0.1.6"
    /tmp/oracle-venv/bin/python tools/oracle_generate.py tests/fixtures/oracle
"""

import argparse
import gzip
import importlib
import json
import pkgutil
import sys
from collections import defaultdict
from pathlib import Path

from state_grid import state_grid  # tools/ is sys.path[0] when run as a script


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("outdir", type=Path)
    parser.add_argument("--limit", type=int, default=200)
    opts = parser.parse_args()

    import pyhvac

    try:
        from pyhvac import irhvac  # noqa: F401
    except ImportError:
        sys.exit(f"{pyhvac.__file__}: no compiled irhvac extension")
    from pyhvac import plugins
    from pyhvac.plugins.hvaclib import IRGHVAC

    print(f"using pyhvac {pyhvac.__version__} from {pyhvac.__file__}")
    records = defaultdict(list)
    seen = set()
    for info in sorted(pkgutil.iter_modules(plugins.__path__), key=lambda m: m.name):
        if info.name == "hvaclib":
            continue
        mod = importlib.import_module(f"pyhvac.plugins.{info.name}")
        for model, cls in mod.PluginObject.MODELS.items():
            if not (isinstance(cls, type) and issubclass(cls, IRGHVAC)) or cls in seen:
                continue
            seen.add(cls)
            probe = cls()
            for state in state_grid(probe.capabilities, probe.xtra_capabilities, opts.limit):
                dev = cls()
                # Bypass the setters: IRGHVAC.set_fan writes "mode" (known bug).
                dev.to_set = dict(state)
                try:
                    pulses = [int(x) for x in dev.to_lirc(dev.build_ircode())]
                except Exception as exc:  # record what works, report the rest
                    print(f"skip {cls.__name__} {state}: {exc!r}")
                    continue
                records[dev.protocol].append(
                    {
                        "plugin": info.name,
                        "model": model,
                        "class": cls.__name__,
                        "variant": None if dev.variant is None else str(dev.variant),
                        "state": state,
                        "pulses": pulses,
                    }
                )
    opts.outdir.mkdir(parents=True, exist_ok=True)
    total = 0
    for protocol, recs in sorted(records.items()):
        data = gzip.compress(json.dumps(recs).encode(), mtime=0)
        (opts.outdir / f"{protocol}.json.gz").write_bytes(data)
        total += len(data)
        print(f"{protocol}: {len(recs)} records, {len(data)} bytes")
    print(f"{len(records)} protocols, {total} bytes in all")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Generate the oracle fixtures**

```bash
python -m venv /tmp/oracle-venv
/tmp/oracle-venv/bin/pip install "pyhvac>=0.1.6"
cd /tmp && /tmp/oracle-venv/bin/python /home/fw/development/AutoBuddy/pyhvac/tools/oracle_generate.py /home/fw/development/AutoBuddy/pyhvac/tests/fixtures/oracle
```

Running from `/tmp` guarantees that the installed pyhvac is used, not the checkout. Expected output:
- `using pyhvac 0.1.x from /tmp/oracle-venv/...`, where the path is not the repo;
- one line per protocol, around 65 of them;
- a total of a few MB.

Some `skip` lines are acceptable; report them in the commit message. If the total is above 20 MB, rerun with `--limit 100` and note that in the commit message.

- [ ] **Step 7: Run the full suite**

Run: `python -m pytest -q`
Expected: all pass, including `test_fixture_is_well_formed` for every generated file.

- [ ] **Step 8: Format and commit**

```bash
black tools/oracle_generate.py tests/oracle.py tests/test_oracle_support.py
git add tools/oracle_generate.py tests/oracle.py tests/test_oracle_support.py tests/fixtures/oracle
git commit -m "Record IRremoteESP8266 reference pulse trains for protocol ports

Generated with pyhvac <version> from PyPI; <N> protocols, <M> states skipped.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Replace `<version>`, `<N>` and `<M>` with the values the generator printed.
