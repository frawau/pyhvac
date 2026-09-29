"""Discovery tools for porting a C-backed protocol, driven by the oracle
fixtures (tests/fixtures/oracle/<PROTOCOL>.json.gz).

    python tools/portkit.py timings DAIKIN2
    python tools/portkit.py decode DAIKIN2 --protocol pyhvac.plugins.daikin:DAIKIN2 \\
        --expected leader,first,second
    python tools/portkit.py diff DAIKIN2 --protocol ... --expected ...
    python tools/portkit.py checksum DAIKIN2 --protocol ... --expected ...
"""

import argparse
import gzip
import importlib
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pyhvac.fields import (  # noqa: E402
    Copy,
    Crc8,
    HighNibbleSum,
    InvertedPairs,
    NibbleSum,
    Sum8,
    Xor8,
    checksum_bits,
)
from pyhvac.ir.codec import DecodeError, decode  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "oracle"
TOLERANCE = 0.25
BURST_SPLIT = 5000  # µs: a space longer than this ends a burst
CRC_POLYS = (0x07, 0x31, 0x1D, 0x9B, 0xD5)


def load_records(name, fixtures=FIXTURES):
    return json.loads(
        gzip.decompress((Path(fixtures) / f"{name}.json.gz").read_bytes())
    )


# ------------------------------------------------------------------ timings
def cluster(durations, tolerance=TOLERANCE):
    """Group durations that lie within ``tolerance`` of their group's
    smallest value. Returns [(median, count)], shortest first."""
    groups = []
    for d in sorted(durations):
        if groups and d <= groups[-1][0] * (1 + tolerance):
            groups[-1].append(d)
        else:
            groups.append([d])
    return [(round(statistics.median(g)), len(g)) for g in groups]


def bursts(pulses, split=BURST_SPLIT):
    """Split a pulse train after every space longer than ``split``."""
    out, cur = [], []
    for i, d in enumerate(pulses):
        cur.append(d)
        if i % 2 == 1 and d > split:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def _nearest(value, centers):
    return min(centers, key=lambda c: abs(c - value))


def burst_parts(burst):
    """(header, bit pulses, footer, gap) of a raw burst, split by position:
    two header pulses, the bit pulses, one footer mark, then the gap (a
    trailing space longer than BURST_SPLIT). A burst of four pulses or
    fewer before its gap is bitless: all header."""
    gap = burst[-1] if len(burst) % 2 == 0 and burst[-1] > BURST_SPLIT else 0
    body = list(burst[:-1] if gap else burst)
    if len(body) <= 4:
        return body, [], [], gap
    return body[:2], body[2:-1], body[-1:], gap


def duration_clusters(records):
    """Durations clustered by role, so a header or footer duration close to
    a bit duration is not merged with it: {role: [(median, count)]} for
    bit_marks, bit_spaces, marks and spaces (header and footer) and gaps."""
    pools = defaultdict(list)
    for r in records:
        for burst in bursts(r["pulses"]):
            header, bits, footer, gap = burst_parts(burst)
            pools["bit_marks"] += bits[0::2]
            pools["bit_spaces"] += bits[1::2]
            pools["marks"] += header[0::2] + footer
            pools["spaces"] += header[1::2]
            if gap:
                pools["gaps"].append(gap)
    roles = ("bit_marks", "bit_spaces", "marks", "spaces", "gaps")
    return {role: cluster(pools[role]) for role in roles}


def burst_shape(burst, clusters):
    """(header, bit count, footer, gap) of a burst, each duration snapped to
    the cluster centres of its role (see ``duration_clusters``)."""
    centres = {role: [c for c, _ in found] for role, found in clusters.items()}
    header, bits, footer, gap = burst_parts(burst)
    header = tuple(
        _nearest(d, centres["marks" if i % 2 == 0 else "spaces"])
        for i, d in enumerate(header)
    )
    footer = tuple(_nearest(d, centres["marks"]) for d in footer)
    gap = _nearest(gap, centres["gaps"]) if gap else 0
    return header, len(bits) // 2, footer, gap


def timings_report(records):
    clusters = duration_clusters(records)
    shapes = Counter()
    for r in records:
        shapes[tuple(burst_shape(b, clusters) for b in bursts(r["pulses"]))] += 1
    lines = [
        f"bit marks   (µs, count): {clusters['bit_marks']}",
        f"bit spaces  (µs, count): {clusters['bit_spaces']}",
        f"hdr/ftr marks  (µs, count): {clusters['marks']}",
        f"hdr spaces     (µs, count): {clusters['spaces']}",
        f"gaps           (µs, count): {clusters['gaps']}",
        "",
    ]
    for shape, count in shapes.most_common():
        lines.append(f"{count} records:")
        for header, nbits, footer, gap in shape:
            kind = f"{nbits} bits" if nbits else "bitless"
            lines.append(f"  header={header} {kind} footer={footer} gap={gap}")
    lines += ["", "draft:", draft_protocol(shapes.most_common(1)[0][0], clusters)]
    return "\n".join(lines)


def draft_protocol(shape, clusters):
    sections = []
    for i, (header, nbits, footer, gap) in enumerate(shape):
        if nbits:
            bit_mark = max(clusters["bit_marks"], key=lambda c: c[1])[0]
            common = sorted(clusters["bit_spaces"], key=lambda c: -c[1])[:2]
            short, long_ = sorted(c[0] for c in common)
            bits = f"PulseDistance({bit_mark}, {short}, {long_})"
            args = f"{bits}, header={header}, footer={footer}, gap={gap}"
        else:
            args = f"None, header={header}, gap={gap}"
        sections.append(f'        "s{i}": Section({args}),')
    return 'Protocol(\n    "draft",\n    {\n' + "\n".join(sections) + "\n    },\n)"


# ------------------------------------------------------------------- decode
def load_protocol(spec):
    module, _, name = spec.partition(":")
    return getattr(importlib.import_module(module), name)


def decode_all(records, protocol, expected):
    """[(record, frames or DecodeError)]"""
    out = []
    for r in records:
        try:
            out.append((r, decode(protocol, r["pulses"], expected=expected)))
        except DecodeError as exc:
            out.append((r, exc))
    return out


# --------------------------------------------------------------------- diff
def single_key_pairs(states):
    """{key: [(i, j)]}: index pairs whose states differ in exactly that key."""
    pairs = defaultdict(list)
    for i, a in enumerate(states):
        for j in range(i + 1, len(states)):
            b = states[j]
            if a.keys() != b.keys():
                continue
            diff = [k for k in a if a[k] != b[k]]
            if len(diff) == 1:
                pairs[diff[0]].append((i, j))
    return pairs


def changed_bits(frames_a, frames_b):
    """{(frame, byte, bit)} where two decoded messages differ."""
    out = set()
    for f, (a, b) in enumerate(zip(frames_a, frames_b)):
        for byte, (x, y) in enumerate(zip(a.data, b.data)):
            for bit in range(8):
                if (x ^ y) >> bit & 1:
                    out.add((f, byte, bit))
    return out


def constant_bits(messages):
    """Per frame: (skeleton bytes, mask of bits that vary across messages)."""
    out = []
    for f in range(len(messages[0])):
        first = messages[0][f].data
        varying = bytearray(len(first))
        for m in messages[1:]:
            for i, (x, y) in enumerate(zip(first, m[f].data)):
                varying[i] |= x ^ y
        out.append((bytes(first), bytes(varying)))
    return out


def diff_report(decoded):
    good = [(r, m) for r, m in decoded if not isinstance(m, DecodeError)]
    states = [r["state"] for r, _ in good]
    lines = []
    for key, pairs in sorted(single_key_pairs(states).items()):
        positions = set()
        for i, j in pairs:
            positions |= changed_bits(good[i][1], good[j][1])
        pos = sorted(positions)
        lines.append(f"{key}: {len(pairs)} pairs, bits {pos}")
        table = {}
        for r, m in good:
            if key in r["state"]:
                table.setdefault(
                    r["state"][key],
                    "".join(str(m[f].data[b] >> bit & 1) for f, b, bit in pos),
                )
        for value, bits in sorted(table.items(), key=str):
            lines.append(f"    {value!r}: {bits}")
    lines.append("constant skeleton (hex) / varying mask:")
    for f, (skel, mask) in enumerate(constant_bits([m for _, m in good])):
        lines.append(f"  frame {f}: {skel.hex(' ')}")
        lines.append(f"  mask  {f}: {mask.hex(' ')}")
    return "\n".join(lines)


# ----------------------------------------------------------------- checksum
def _ranges(n):
    """(start, end, at): at any byte, the bytes just before it or just
    after it; at the last two bytes, any range before them."""
    for at in range(n):
        for start in range(at):
            yield start, at, at
        for end in range(at + 2, n + 1):
            yield at + 1, end, at
    for at in (n - 1, n - 2):
        for start in range(max(at, 0)):
            for end in range(start + 1, at):
                yield start, end, at


def _candidates(n):
    for start, end, at in _ranges(n):
        for rev in (False, True):
            yield Sum8(start, end, at, rev)
            yield NibbleSum(start, end, at, rev)
            yield Xor8(start, end, at, rev)
            for with_low in (False, True):
                yield HighNibbleSum(start, end, at, rev, with_low)
        for poly in CRC_POLYS:
            for reflect in (False, True):
                yield Crc8(start, end, at, poly=poly, reflect=reflect)
    for start in range(n):
        for end in range(start + 1, n + 1):
            if end + end - start <= n:
                yield Copy(start, end, end)
                yield Copy(start, end, end, invert=True)
            if (end - start) % 2 == 0 and end - start >= 4:
                yield InvertedPairs(start, end)


def find_checksums(frames):
    """Checksum candidates that hold on every frame (all of one length) and
    both read and write at least one bit that varies. Of the inverted-pair
    runs, only the longest are kept, and single inverted bytes inside them
    are dropped; copies and inverted pairs come first."""
    frames = [bytearray(f) for f in frames]
    n = len(frames[0])
    varying = {
        i for i in range(8 * n) if len({f[i // 8] >> i % 8 & 1 for f in frames}) > 1
    }
    found = list(
        dict.fromkeys(
            c
            for c in _candidates(n)
            # a checksum that never changes, or reads bytes that never
            # change, proves nothing
            if varying.intersection(range(8 * c.start, 8 * c.end))
            and varying.intersection(checksum_bits(c))
            and all(c.check(f) for f in frames)
        )
    )
    pairs = {c for c in found if isinstance(c, InvertedPairs)}

    def in_pairs(c):
        if c in pairs:
            return (
                InvertedPairs(c.start - 2, c.end) in pairs
                or InvertedPairs(c.start, c.end + 2) in pairs
            )
        return (
            isinstance(c, Copy)
            and c.invert
            and c.end - c.start == 1
            and any(
                p.start <= c.start < p.end and (c.start - p.start) % 2 == 0
                for p in pairs
            )
        )

    kept = [c for c in found if not in_pairs(c)]
    # Structural relations first: they explain the byte sums and XORs that
    # hold over complemented or copied bytes.
    return sorted(kept, key=lambda c: not isinstance(c, (InvertedPairs, Copy)))


def checksum_report(decoded):
    by_len = defaultdict(list)
    for _, m in decoded:
        if isinstance(m, DecodeError):
            continue
        for f in m:
            if f.data:
                by_len[len(f.data)].append(f.data)
    lines = []
    for n, frames in sorted(by_len.items()):
        found = find_checksums(frames)
        lines.append(f"{n}-byte frames ({len(frames)}): {len(found)} candidates")
        lines += [f"  {c!r}" for c in found]
    return "\n".join(lines)


# ---------------------------------------------------------------------- cli
def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("timings", "decode", "diff", "checksum"))
    parser.add_argument("name", help="oracle fixture name, e.g. DAIKIN2")
    parser.add_argument("--protocol", help="module:NAME of a pyhvac.ir Protocol")
    parser.add_argument("--expected", help="comma-separated section names")
    parser.add_argument("--fixtures", default=str(FIXTURES))
    opts = parser.parse_args(argv)
    records = load_records(opts.name, opts.fixtures)
    if opts.command == "timings":
        print(timings_report(records))
        return 0
    if not opts.protocol:
        parser.error(f"{opts.command} needs --protocol")
    expected = opts.expected.split(",") if opts.expected else None
    decoded = decode_all(records, load_protocol(opts.protocol), expected)
    failures = [(r, m) for r, m in decoded if isinstance(m, DecodeError)]
    if opts.command == "decode":
        for r, m in decoded:
            shown = (
                m if isinstance(m, DecodeError) else " | ".join(f.data.hex() for f in m)
            )
            print(f"{json.dumps(r['state'], sort_keys=True)}: {shown}")
        print(f"{len(decoded) - len(failures)}/{len(decoded)} records decoded")
        return 1 if failures else 0
    print(diff_report(decoded) if opts.command == "diff" else checksum_report(decoded))
    return 0


if __name__ == "__main__":
    sys.exit(main())
