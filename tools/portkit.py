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

from pyhvac.fields import Crc8, InvertedPairs, NibbleSum, Sum8, Xor8  # noqa: E402
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


def burst_shape(burst, marks, spaces):
    """(header, bit count, footer, gap) of a burst, durations snapped to the
    cluster centres. A burst of four pulses or fewer is taken as bitless."""
    snap = [_nearest(d, marks if i % 2 == 0 else spaces) for i, d in enumerate(burst)]
    gap = snap[-1] if len(snap) % 2 == 0 and snap[-1] > BURST_SPLIT else 0
    body = snap[:-1] if gap else snap
    if len(body) <= 4:
        return tuple(body), 0, (), gap
    return tuple(body[:2]), (len(body) - 3) // 2, (body[-1],), gap


def timings_report(records):
    marks = cluster([d for r in records for d in r["pulses"][0::2]])
    spaces = cluster([d for r in records for d in r["pulses"][1::2]])
    mark_c, space_c = [m for m, _ in marks], [s for s, _ in spaces]
    shapes = Counter()
    for r in records:
        shapes[tuple(burst_shape(b, mark_c, space_c) for b in bursts(r["pulses"]))] += 1
    lines = [f"marks  (µs, count): {marks}", f"spaces (µs, count): {spaces}", ""]
    for shape, count in shapes.most_common():
        lines.append(f"{count} records:")
        for header, nbits, footer, gap in shape:
            kind = f"{nbits} bits" if nbits else "bitless"
            lines.append(f"  header={header} {kind} footer={footer} gap={gap}")
    lines += ["", "draft:", draft_protocol(shapes.most_common(1)[0][0], marks, spaces)]
    return "\n".join(lines)


def draft_protocol(shape, marks, spaces):
    bit_mark = max(marks, key=lambda c: c[1])[0]
    short, long_ = sorted(sorted(spaces, key=lambda c: -c[1])[:2])
    sections = []
    for i, (header, nbits, footer, gap) in enumerate(shape):
        if nbits:
            bits = f"PulseDistance({bit_mark}, {short[0]}, {long_[0]})"
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
def _candidates(n):
    for at in (n - 1, n - 2):
        if at < 1:
            continue
        for start in range(at):
            for end in range(start + 1, at + 1):
                for rev in (False, True):
                    yield Sum8(start, end, at, rev)
                    yield NibbleSum(start, end, at, rev)
                    yield Xor8(start, end, at, rev)
                for poly in CRC_POLYS:
                    for reflect in (False, True):
                        yield Crc8(start, end, at, poly=poly, reflect=reflect)
    if n % 2 == 0:
        yield InvertedPairs(0, n)


def find_checksums(frames):
    """Checksum candidates that hold on every frame (all of one length)."""
    frames = [bytearray(f) for f in frames]
    return [c for c in _candidates(len(frames[0])) if all(c.check(f) for f in frames)]


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
