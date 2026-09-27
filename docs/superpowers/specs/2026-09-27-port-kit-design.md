# Port kit — design

Date: 2026-09-27
Status: draft, awaiting review
Branch: `ports` (forked from `state-api`)
Follows:
- `docs/superpowers/specs/2026-09-26-ir-section-model-design.md`
- `docs/superpowers/specs/2026-09-27-state-api-design.md`

## Goal

Give every C-backed model (IRremoteESP8266 via `_irhvac`) a pure-Python
`Device` that reproduces the C library's frames, so phase four can drop the C
build. This spec defines the tooling and conventions every port follows (the
"port kit") and the pilot port (DAIKIN2). The remaining ports are recipe
work, planned family by family.

## Context

- About 60 C-backed protocols. Daikin is the largest family (9 protocols) and
  goes first.
- Committed oracle fixtures (`tests/fixtures/oracle/<PROTOCOL>.json.gz`) hold
  the C library's pulses for about 200 states per protocol. They are sparse:
  temperatures are min/mid/max only, and each extra feature is toggled once.
- Recorded Daikin shapes that the current section model cannot express:
  - DAIKIN2 opens with a lone 10 024 µs mark + 25 180 µs space;
  - DAIKIN64 and DAIKIN128 open with two 9 800 µs preamble pulses;
  - DAIKIN64 ends with a bare 4 600 µs mark.
  These are fixed bursts with no data bits.
- `LegacyDevice` already maps each old class's capabilities to canonical
  values, with the old names as labels. Ported devices must keep that
  entity surface.

## Decisions

1. **Hybrid method.**
   - Timings, checksums and the fixed skeleton are proven from the oracle
     data with the kit's tools.
   - The complete field layout comes from the bitfield structs in the
     IRremoteESP8266 headers (`ir_*.h`, from a scratch clone of the fork;
     nothing is copied into this repo). These are protocol facts.
   - The oracle cross-check is the acceptance gate.
   - Encoders are written from the layout, not transliterated from the
     C++ `.cpp` code.
2. **Bitless sections** are added to the IR model for fixed bursts.
3. **A declarative field-map helper** (`pyhvac/fields.py`) covers the common
   case. Odd logic stays plain code in `frames()`.
4. **One device class per protocol**, with a `variant` argument where several
   models share a protocol.
5. **Ported capabilities keep today's HA entity:** the same values, with the
   old names as labels. Extra values documented by a header may be added,
   with a ruling.

## 1. Bitless sections — `pyhvac/ir/model.py`, `pyhvac/ir/codec.py`

- `Section.bits` becomes optional (`None`). A bitless section is a fixed
  burst: it emits `header`, then `footer`, then `gap`.
  - At least one of the three must be non-empty.
  - The "PulseDistance needs a footer" rule does not apply to it.
- `Frame` accepts `data=b""` with `nbits=0`, and only in that combination.
  `nbits` defaults to 0 for empty data.
- **Encode:**
  - a bitless section requires an empty frame, otherwise `ValueError`;
  - a normal section requires a non-empty frame, otherwise `ValueError`;
  - fixed pulses go through the same merging as everything else.
- **Decode:**
  - a bitless section matches when its header, footer and gap match within
    tolerance, and yields `Frame(name, b"", 0)`;
  - with `expected`, it is parsed in order;
  - greedy decoding tries it like any section with a header;
  - a bitless section with an empty header can only be decoded with
    `expected`, like any headerless section.
- **Round trip:** the invariant `decode(encode(frames), expected) == frames`
  holds, and is tested on the three recorded shapes:
  - DAIKIN2 leader (mark + gap);
  - DAIKIN64/128 preamble (mark, space, mark, space);
  - DAIKIN64 trailing mark.

## 2. Field maps and checksums — `pyhvac/fields.py`

```python
Field(offset: int, width: int, values: Mapping | None = None, encode: Callable | None = None)
    # offset = absolute bit index in the frame's logical bytes: byte * 8 + bit, bit 0 = LSB
Field.at(byte, bit, width, **kw)

Layout(skeleton: bytes, fields: Mapping[str, Field], checksum: Checksum | None = None)
    .build(checksum=True, **values) -> bytearray
    .read(data) -> dict

class Checksum:            # base
    .apply(data) -> None   # writes the checksum into data
    .check(data) -> bool
Sum8(start, end, at, reverse=False)        # sum of data[start:end] mod 256
NibbleSum(start, end, at, reverse=False)   # sum of all nibbles, mod 256
Xor8(start, end, at, reverse=False)
Crc8(start, end, at, poly, init=0, reflect=False)
InvertedPairs(start, end)                  # every odd byte is the complement of the one before it
```

- **Fields.**
  - A field writes into the logical bytes (`Frame.data`, before wire bit
    order).
  - A field may span a byte boundary; its bits run LSB-first from `offset`.
  - `values` translates canonical values (`"cool"`, `"2"`, `True`) to ints.
  - `encode` computes the int (e.g. a temperature formula).
  - With neither, the value must already be an int (bools count as 0/1).
- **Build.**
  - Starts from the skeleton, writes each given field, then applies the
    checksum.
  - Fields that are not given keep their skeleton bits.
  - `checksum=False` lets a device patch bytes and apply
    `layout.checksum.apply(data)` itself.
  - `reverse=True` on a checksum means each byte is bit-reversed before it
    enters the checksum. The result is written as computed.
- **Read.** Returns every field's int, translated back through `values` where
  a table exists. Computed (`encode`) fields return the raw int.
- **Validation (`ValueError`).**
  - At construction: overlapping fields, a field outside the skeleton, or a
    checksum position inside a field.
  - At build: an unknown field name, an unknown table key, or a value that
    does not fit the width.

## 3. Discovery tools — `tools/portkit.py`

A developer script (not packaged; standard library + pyhvac) reading the
committed oracle fixtures. It has four subcommands, each printing a text
report:

- **`timings PROTOCOL`**
  - Clusters all mark and space durations across the protocol's records
    (within 25 %) and prints the clusters with counts.
  - Splits each record into bursts at spaces longer than 5 000 µs and prints
    the distinct burst shapes (header, bit count, footer, gap), with counts.
  - Prints a draft `Protocol(...)`, with bitless sections for bursts that
    have no bits.
- **`decode PROTOCOL --protocol module:NAME --expected s1,s2,...`**
  - Decodes every record.
  - Failures print the record's state, the pulse index and the
    `DecodeError`.
  - Successes print state → frames (hex), one line per record.
- **`diff PROTOCOL --protocol ... --expected ...`**
  - Pairs records that differ in exactly one state key.
  - For each key, prints the changing (frame, byte, bit) positions and a
    value → bits table.
  - Prints the bits that are constant across all records (the skeleton).
- **`checksum PROTOCOL --protocol ... --expected ...`**
  - For each distinct frame length, tests every `Checksum` class above, each
    `at` in the last two bytes, every range ending before `at`, with and
    without `reverse`, and `Crc8` over polynomials 0x07, 0x31, 0x1D, 0x9B and
    0xD5 with both `reflect` values.
  - Prints only the candidates that hold on every record.

The core functions (`cluster`, `bursts`, `single_key_pairs`,
`find_checksums`) are importable, so tests call them directly.

## 4. Port recipe and acceptance

**Recipe for each protocol:**
1. `portkit timings`: draft the `Protocol`.
2. `portkit decode`: every oracle record decodes.
3. Write the `Layout` from the header's bitfield struct. Check it against
   `portkit diff`, and the checksum against `portkit checksum`.
4. Write the device class:
   - capabilities equal to `LegacyDevice`'s mapping of the old class (same
     values, old names as labels);
   - `previous` ignored unless the header shows toggle or transition bits.
5. Register it: the models move to the module's `DEVICES`. The old class
   stays, for the old API, until 0.2.0.

**Acceptance (all without the C extension):**
- **Oracle cross-check.** A shared helper, `tests/port_oracle.py`,
  translates each oracle record's old-vocabulary state into an `HvacState`
  through the new device's labels (bools from `"on"`/`"off"`). It then calls
  `tests/oracle.py:check_against_oracle`:
  - the C pulses must decode to exactly the device's frames;
  - the device's pulses must match the C pulses within tolerance.
  - Records relying on C defaults (a missing state key whose device default
    is not `off`) are skipped, as in `test_legacy_oracle.py`.
  - Known C defects get ledgered rulings.
- **Layout round trip:** `read(build(values)) == values` for the values of
  every oracle state.
- **Registry smoke test:** `tests/test_legacy_encode_all.py` covers the ported
  models automatically.

## Pilot: DAIKIN2

- Models: `ARC477A1 remote`, `FTXZ25NV1B`, `FTXZ35NV1B`, `FTXZ50NV1B` (the
  current `Daikin2` class).
- Recorded shape: a bitless leader (10 024 µs mark, 25 180 µs space), then a
  20-byte frame and a 19-byte frame, each with a 3 500/1 728 µs header and a
  35 204 µs gap.
- The pilot must pass the acceptance above. It is the first user of every kit
  piece; kit gaps found on the way are fixed in the kit, not worked around in
  the port.

## Plans

- **Plan A (this spec):** bitless sections, `pyhvac/fields.py`,
  `tools/portkit.py`, `tests/port_oracle.py`, and the DAIKIN2 pilot.
- **Plan B:** the other eight Daikin protocols, by the recipe.
- **Later families** (Hitachi, Mitsubishi, Haier, the pairs, singletons in
  batches) each get a plan. A short spec is needed only if a family requires
  a model change (e.g. Manchester for Airwell).

## Out of scope

- Removing the C build and the old API (phase four, 0.2.0).
- SmartIR changes.
- Fixing C-library defects. They are recorded; a port matches the documented
  behaviour where the C output is defective, with a ruling.
