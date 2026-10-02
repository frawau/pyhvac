"""Run the SmartIR climate import and write its report.

    python tools/smartir/report.py OUT_DIR [--cache DIR] [--no-fetch] [--jobs N]

Writes OUT_DIR/report.md (verdict per file, gaps, clusters), OUT_DIR/rows.py
(proposed pyhvac/brands.py rows for covered and table files, for review)
and OUT_DIR/results.json. SmartIR files stay in the cache, never in OUT_DIR.
"""

import argparse
import json
import re
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "tools"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from pyhvac import brands  # noqa: E402
from smartir import cluster as clustering  # noqa: E402
from smartir import fetch, match  # noqa: E402
from smartir.codes import parse  # noqa: E402

KIND = "unit"  # SmartIR lists the units a file was learned from
SKIPPED_FLAG = 0.1  # a file with more unreadable codes than this is flagged


@dataclass(frozen=True)
class Row:
    brand: str
    model: str
    cls: str  # Device class name
    variant: Optional[str]
    source: int  # upstream file number
    verdict: str  # the file's verdict: covered, near, unknown


def _key(text):
    return re.sub(r"[^0-9a-z]", "", text.casefold())


def _existing():
    """(brand key, model key) -> (class name, variant); brand key -> name."""
    rows = {(_key(b), _key(m)): (c.__name__, v) for b, m, k, c, v in brands.MODELS}
    names = {_key(b): b for b, *_ in brands.MODELS}
    return rows, names


def rows(results):
    """Proposed rows and conflicts from [(SmartIRFile, Match)]: a covered
    file names its candidate; any other file whose codes can be read is
    served by TableDevice. A name already taken by the same device is
    skipped; taken by another device, it is a conflict."""
    taken, brand_names = _existing()
    out, conflicts = [], []
    for f, m in sorted(results, key=lambda r: r[0].number):
        if m.verdict == "unsupported" or not f.codes:
            continue
        if m.verdict == "covered":
            cls, _, variant = m.candidate.partition("/")
            variant = variant or None
        else:
            cls, variant = "TableDevice", str(f.number)
        brand = brand_names.get(_key(f.manufacturer), f.manufacturer.strip())
        for model in f.models or (f"SmartIR {f.number}",):
            row = Row(brand, model.strip(), cls, variant, f.number, m.verdict)
            k = (_key(brand), _key(row.model))
            if not k[0] or not k[1]:
                conflicts.append((row, "empty name"))
            elif k not in taken:
                taken[k] = (cls, variant)
                brand_names.setdefault(k[0], brand)
                out.append(row)
            elif taken[k] != (cls, variant):
                conflicts.append((row, f"name taken by {taken[k][0]}/{taken[k][1]}"))
    return out, conflicts


def python_rows(new_rows):
    """brands.py MODELS entries for the rows, one per line."""
    lines = []
    for r in new_rows:
        lines.append(
            f"    ({r.brand!r}, {r.model!r}, {KIND!r}, {r.cls}, {r.variant!r}),"
            f"  # SmartIR {r.source}"
        )
    return "\n".join(lines) + "\n"


def markdown(results, clusters, new_rows, conflicts, unreadable=()):
    verdicts = Counter(m.verdict for _, m in results)
    out = ["# SmartIR climate import", ""]
    out += [f"- {v}: {n}" for v, n in sorted(verdicts.items())]
    if unreadable:
        out.append(f"- not JSON: {', '.join(map(str, unreadable))}")
    out += [
        "",
        "## Files",
        "",
        "Skipped: codes that could not be read; flagged (!) when they are "
        f"over {SKIPPED_FLAG:.0%} of the file.",
        "",
        "| file | brand | verdict | candidate | units | verified | skipped | gaps |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for f, m in sorted(results, key=lambda r: r[0].number):
        gaps = ", ".join(f"{k} ({n})" for k, n in m.gaps.items())
        total = len(f.codes) + f.skipped
        flag = " (!)" if total and f.skipped > SKIPPED_FLAG * total else ""
        out.append(
            f"| {f.number} | {f.manufacturer} | {m.verdict} | {m.candidate or ''} "
            f"| {m.units or ''} | {m.verified}/{m.usable} | {f.skipped}{flag} "
            f"| {gaps} |"
        )
    out += ["", "## Clusters of unknown files", ""]
    for c in clusters:
        out += [
            f"### {len(c.files)} files, {c.codes} codes, {c.keys} keys",
            "",
            f"files: {', '.join(map(str, c.files))}",
            "",
            "```",
            c.draft,
            "```",
            "",
        ]
    out += ["## Conflicts", ""]
    out += [
        f"- SmartIR {r.source}: {r.brand} / {r.model}: {why}" for r, why in conflicts
    ]
    out += ["", f"## Rows: {len(new_rows)} proposed (rows.py)", ""]
    return "\n".join(out) + "\n"


_CANDIDATES = None


def _one(path):
    global _CANDIDATES
    if _CANDIDATES is None:
        _CANDIDATES = match.candidates()
    number = int(Path(path).stem)
    try:
        data = json.loads(Path(path).read_text())
    except ValueError:
        return number, None
    f = parse(number, data)
    return f, match.match(f, _CANDIDATES)


def run(paths, jobs=8):
    """([(SmartIRFile, Match)], [numbers of the files that are not JSON])."""
    results, unreadable = [], []
    with ProcessPoolExecutor(jobs) as ex:
        for f, m in ex.map(_one, paths, chunksize=1):
            if m is None:
                unreadable.append(f)
            else:
                results.append((f, m))
    return results, unreadable


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("out", type=Path)
    ap.add_argument("--cache", type=Path, default=None)
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--jobs", type=int, default=8)
    args = ap.parse_args(argv)
    cache = args.cache or fetch.default_dir()
    if not args.no_fetch:
        fetch.fetch(cache)
    results, unreadable = run(fetch.files(cache), args.jobs)
    unknown = [f for f, m in results if m.verdict == "unknown"]
    clusters = clustering.cluster(unknown)
    new_rows, conflicts = rows(results)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "report.md").write_text(
        markdown(results, clusters, new_rows, conflicts, unreadable)
    )
    (args.out / "rows.py").write_text(python_rows(new_rows))
    (args.out / "results.json").write_text(
        json.dumps({f.number: asdict(m) for f, m in results}, indent=1, default=str)
    )
    print(Counter(m.verdict for _, m in results))


if __name__ == "__main__":
    main()
