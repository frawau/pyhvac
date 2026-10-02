"""Group the files no pyhvac protocol decodes by timing and frame shape,
so files sharing an unknown protocol become one port task.

A file's signature is the burst shape most of its codes share (header
durations rounded to ROUND µs, bit count per burst); files with the same
signature form a cluster. Per cluster: its files, codes and distinct
state keys, its timing clusters (portkit's role-separated ones) and the
draft Protocol portkit writes for it.
"""

import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "tools"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import portkit  # noqa: E402

ROUND = 200  # µs: header and footer durations are compared at this step


@dataclass
class Cluster:
    signature: Tuple
    files: Tuple[int, ...]
    codes: int
    keys: int
    timings: dict
    draft: str


def _records(smartir_file):
    return [{"pulses": list(c.pulses)} for c in smartir_file.codes]


def signature(smartir_file):
    """(header, bit count, footer) per burst of the file's commonest shape,
    durations rounded to ROUND µs; None for a file without codes."""
    records = _records(smartir_file)
    if not records:
        return None
    clusters = portkit.duration_clusters(records)
    shapes = Counter(
        tuple(portkit.burst_shape(b, clusters) for b in portkit.bursts(r["pulses"]))
        for r in records
    )
    shape = shapes.most_common(1)[0][0]
    return tuple(
        (
            tuple(round(d / ROUND) * ROUND for d in header),
            nbits,
            tuple(round(d / ROUND) * ROUND for d in footer),
        )
        for header, nbits, footer, gap in shape
    )


def cluster(files):
    """Clusters of the given parsed files, largest (most files) first."""
    groups = defaultdict(list)
    for f in files:
        sig = signature(f)
        if sig is not None:
            groups[sig].append(f)
    out = []
    for sig, members in groups.items():
        records = [r for f in members for r in _records(f)]
        timings = portkit.duration_clusters(records)
        shape = Counter(
            tuple(portkit.burst_shape(b, timings) for b in portkit.bursts(r["pulses"]))
            for r in records
        ).most_common(1)[0][0]
        out.append(
            Cluster(
                sig,
                tuple(sorted(f.number for f in members)),
                len(records),
                len({c.key for f in members for c in f.codes}),
                timings,
                portkit.draft_protocol(shape, timings),
            )
        )
    return sorted(out, key=lambda c: (-len(c.files), -c.codes))
