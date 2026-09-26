# IR section model — design

Date: 2026-09-26
Status: draft, awaiting review

## Goal

Make pyhvac pure Python by removing its dependency on the IRremoteESP8266
C/SWIG library (`_irhvac`). This spec covers the first sub-project: a
declarative, bidirectional description of the IR physical layer (timings and
bit encodings). Every HVAC protocol will be defined in terms of it, and edge
formatters will convert its output to device-specific formats.

Why: the C build drives most of the packaging cost. QEMU aarch64 wheel builds
take ~1h45, wheels are Linux-only, setup.py carries SWIG and package-manager
workarounds, and the library depends on a forked C++ codebase.

## Context

- Today 61 of the 75 plugin files go through `IRGHVAC` into the C library,
  covering 65 distinct IRremoteESP8266 protocols. A few plugins (Airspool,
  Sharp JTech, native Daikin/Panasonic/LG classes) already build frames in
  Python.
- Timings live in class attributes (`STARTFRAME`, `MARK`, `SPACE`, `ENDFRAME`,
  plus `LEAD`/`TAIL` on `PulseBased`): one timing set per class, always
  emitted MSB-first. LSB-first protocols byte-swap via `is_msb`.
- The main consumer is the author's SmartIR fork for Home Assistant
  (`custom_components/smartir/climate.py`). It uses `capabilities`,
  `set_value`, `build_ircode` and `to_broadlink`. AutoBuddy is no longer a
  constraint. The public API may change and SmartIR will adapt.
- Licensing: pyhvac stays MIT. Encoders are written from protocol facts
  (timings, byte layouts, checksum rules) and verified against reference
  output. They are not function-by-function translations of the C++ code.

## Decisions

1. **Declarative section objects.** Two alternatives were rejected: extending
   the current class attributes (it does not scale to multi-section messages,
   Manchester, or decode) and IRP notation (it needs a parser and is a poor fit
   for 100+ bit stateful frames).
2. **Core output is one neutral `Signal`** (carrier in Hz + µs pulse train).
   Broadlink, Pronto and raw formats are edge formatters.
3. **Bidirectional.** The same description encodes and decodes.
4. **The physical layer is stateless.** Some protocols need the previous state
   to build a frame. Sharp byte 5 encodes a power *transition* (0x11 on, 0x21
   off, 0x31 change while on). Airspool `se_step` is momentary. That
   dependency belongs to the protocol/state layer, as a pure
   `encode(previous, target)` with caller-persisted state. It is designed in
   the state-API sub-project. This layer only has to allow a variable number
   of frames per message.

## Data model — `pyhvac/ir/model.py`

All durations are positive integers in µs. The carrier is an integer in Hz.
All classes are frozen dataclasses and validate their arguments at
construction, raising `ValueError`.

```python
# How one bit becomes pulses
PulseDistance(mark: int, zero_space: int, one_space: int)  # constant mark; space carries the bit
PulseWidth(zero_mark: int, one_mark: int, space: int)      # mark carries the bit; constant space
Manchester(half: int, one_is_mark_first: bool = True)      # bi-phase; half = half-period

Section(
    bits: PulseDistance | PulseWidth | Manchester,
    header: tuple[int, ...] = (),  # alternating mark, space, ... starting with a mark
    footer: tuple[int, ...] = (),  # alternating, starting with a mark; usually (mark,)
    gap: int = 0,                  # trailing silence after this section, 0 = none
    lsb_first: bool = True,
)

Protocol(
    name: str,
    sections: dict[str, Section],  # named templates; at least one
    carrier: int = 38000,
    tolerance: float = 0.25,       # relative, 0 < tolerance < 0.5
    mark_excess: int = 50,         # decode-side demodulator compensation
    trailer_gap: int = 100_000,    # appended when a message would end on a mark
)

Frame(section: str, data: bytes, nbits: int | None = None)  # None -> 8 * len(data)

Signal(carrier: int, pulses: tuple[int, ...])
```

Rules:

- A message is a `list[Frame]`. The protocol code chooses which sections to
  emit and in what order, so multi-frame messages (Daikin leader + 2–3
  frames), mid-message connectors (Gree), optional extra frames (Sharp) and
  repeats (list the frame twice) need no special cases.
- `Frame.nbits` must satisfy `8 * (len(data) - 1) < nbits <= 8 * len(data)`.
  Bits are streamed from `data` in the section's bit order: LSB-first means
  byte 0 bit 0 first; MSB-first means byte 0 bit 7 first. Streaming stops
  after `nbits`. Bits of the last byte that fall past `nbits` must be zero
  (`ValueError` otherwise), which keeps `decode(encode(x)) == x` exact.
- A `Section` whose `bits` is `PulseDistance` must have a non-empty `footer`.
  Without a closing mark, the last bit's space merges into the gap and cannot
  be recovered.
- `Signal.pulses` alternates mark, space, mark, …, starts with a mark, ends
  with a space, and contains no zeros.

## Encode — `pyhvac/ir/codec.py`

`encode(protocol: Protocol, frames: list[Frame]) -> Signal`

Deterministic; no tolerance is involved.

1. For each frame, look up `protocol.sections[frame.section]`. An unknown
   name raises `ValueError`.
2. Emit, as signed levels: `header`, then per bit:
   - `PulseDistance`: `mark`, then `zero_space` or `one_space`
   - `PulseWidth`: `zero_mark` or `one_mark`, then `space`
   - `Manchester`: two half-periods; with `one_is_mark_first=True` a 1 is
     mark+space and a 0 is space+mark (inverted otherwise)

   then `footer`, then `gap` if non-zero.
3. Normalise the whole message: sum neighbouring durations of the same
   polarity and drop a leading space.
4. If the result ends on a mark, append `protocol.trailer_gap`.
5. Return `Signal(protocol.carrier, pulses)`.

## Decode — `pyhvac/ir/codec.py`

`decode(protocol: Protocol, pulses: Sequence[int], expected: list[str] | None = None) -> list[Frame]`

Designed for real captures.

- **Input:** unsigned µs durations alternating mark/space. If the capture
  source marks polarity and it starts with a space, the caller drops it
  (`from_broadlink`/`from_pronto` do this). The carrier is not used.
- **Compensation:** before matching, subtract `mark_excess` from each mark and
  add it to each space.
- **Matching:** measured `m` matches nominal `n` when
  `abs(m - n) <= protocol.tolerance * n`. A gap matches any space
  `>= (1 - tolerance) * gap`, and the end of input also counts as a gap,
  since captures often truncate the trailing silence.
- **Section selection:**
  - With `expected`, sections are parsed strictly in that order.
  - Without it, at each position try the sections whose non-empty header
    matches, in `sections` insertion order; the first full parse wins.
  - Headerless sections can only be decoded with `expected`.
- **Bits:** classify each bit's pulse(s) to the nearest nominal value, which
  must also match within tolerance. A section's bits end when its footer
  matches (then the gap, if any, must match). For a section with an empty
  footer, the bits end at a space long enough to match the gap, or at the end
  of input. The last bit's own space is absorbed into that gap, which is
  lossless for `PulseWidth` (the mark carries the bit) and for `Manchester`
  (the preceding half carries it). Emitted `Frame.nbits` is the
  number of bits read, and a partial last byte has its unused bits zero.
- **Manchester decoding** re-splits merged durations into half-periods (a
  duration matching `2 * half` counts as two halves of the same level) before
  pairing halves into bits.
- **Errors:** `DecodeError(index, expected, got)`, carrying the pulse index,
  the nominal value(s) being matched, and the measured duration. Leftover
  pulses after the last expected section also raise `DecodeError`.

**Invariant (the core test):** for every protocol and valid frames,
`decode(p, encode(p, frames).pulses, expected=[f.section for f in frames]) == frames`.
It must hold on exact output and with deterministic ±10% jitter added to
every duration (seeded RNG).

## Edge formatters — `pyhvac/ir/formats.py`

- `to_broadlink(signal) -> bytes`: same packet layout as the current
  `HVAC.to_broadlink` (0x26 IR header, 269/8192 µs units, 2-byte escape for
  values > 255, 0x0D 0x05 terminator, pad to a 16-byte multiple including the
  4-byte send header). For the same pulse list its output must be
  byte-identical to the current implementation.
- `to_pronto(signal) -> str`: Pronto hex (learned 0000 format), frequency word
  derived from `signal.carrier`.
- `to_raw(signal) -> list[int]`: signed µs list (+mark, −space), as accepted
  by ESPHome, Tasmota and LOOKin.
- `from_broadlink(data: bytes) -> list[int]` and
  `from_pronto(text: str) -> list[int]`: back to unsigned µs pulses for
  `decode()`. SmartIR users learn codes through Broadlink, so this is the
  main source of real captures.

The formatters depend only on `Signal`/pulse lists, never on plugins.

## Plugin integration (transitional)

A protocol is declared once, as a module-level constant in its plugin:

```python
AIRSPOOL = Protocol("airspool", sections={
    "main": Section(PulseDistance(480, 360, 1180),
                    header=(3200, 1400), footer=(480,), gap=100_000,
                    lsb_first=True),
})
```

- `HVAC` gains a `PROTOCOL` class attribute and `build_signal() -> Signal`,
  which returns `encode(self.PROTOCOL, frames)` for the frames the plugin
  builds.
- Plugin frame builders return `list[Frame]`. During the transition a bare
  `bytes`/`bytearray` frame is wrapped as a `Frame` of the first section.
- `build_ircode`, `to_lirc` and `to_broadlink` remain as thin wrappers over
  the new functions, so SmartIR keeps working unchanged. The state-API
  sub-project replaces this surface.
- `is_msb` byte swapping is removed from migrated plugins; bit order comes
  from `Section.lsb_first`.

## C oracle and golden fixtures

- `tools/oracle_generate.py` runs only where `_irhvac` is built. For each
  C-backed model it sweeps a state grid and records the pulse trains the C
  library produces. The grid is every mode × every fan × every swing ×
  temperature {min, mid, max}, plus each extra feature toggled once, capped at
  200 states per protocol. Each state uses a fresh device object, so no
  previous state leaks between samples.
- Output goes to `tests/fixtures/oracle/<protocol>.json.gz`: a list of
  `{"model", "state", "pulses"}` records. Fixtures are committed, so tests run
  without the C library and only regeneration needs it.
- For a ported protocol, the tests check each record in three ways:
  1. `decode()` the C pulses with the Python `Protocol` (validates timings
     within tolerance);
  2. compare the decoded frames byte-for-byte with the Python encoder's frames
     for the same state (validates the state encoding);
  3. check that the Python `Signal` matches the C pulses element-wise within
     tolerance.
- The existing pure-Python plugins (Airspool, Sharp JTech, native
  Daikin/Panasonic/LG classes) get golden fixtures of their *current* output
  before they are migrated, which catches regressions.

## Testing summary

- `model.py`: validation errors for each rule above.
- `codec.py`: encode on hand-computed small examples (per bit encoding, with
  and without header/footer/gap, partial last byte, merging), round-trip and
  jitter invariant for every declared protocol, and a `DecodeError` index on
  corrupted input.
- `formats.py`: Broadlink byte-identity against the current implementation;
  Pronto and Broadlink round trips (`from_x(to_x(s))` matches `s.pulses`
  within Broadlink's quantisation).
- Plugins: golden fixtures for the migrated pure-Python plugins.

## Scope of the implementation plan for this spec

1. `pyhvac/ir/` (model, codec, formats) with its tests.
2. Golden fixtures for the existing pure-Python plugins, then their migration
   onto `Protocol`.
3. The oracle generator and the committed oracle fixtures.

## Out of scope (separate specs/plans)

- Porting the C-backed protocols, one plan per family (Daikin, Hitachi,
  Mitsubishi, Haier, …).
- The state-API redesign: `encode(previous, target)`, caller-persisted
  previous state (Sharp power transitions, Airspool `se_step`), and the
  HA-facing capability surface for SmartIR.
- Removing the C build, the cibuildwheel setup and the SWIG workarounds, and
  releasing 0.2.0.
