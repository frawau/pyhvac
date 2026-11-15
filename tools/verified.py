"""Keep VERIFIED.md in step with pyhvac's models.

``python tools/verified.py`` rewrites VERIFIED.md with one row per model in
``pyhvac.brands.MODELS``, in that order: new models get an empty row,
existing rows keep their tick and notes. Run it after adding a model.
"""

import re
import sys
from dataclasses import dataclass
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "VERIFIED.md"
TICK = "✅"
HEADER = "| Brand | Model | Kind | Protocol | Verified | Notes |"
RULE = "|---|---|---|---|:---:|---|"

INTRO = f"""# Verified units

pyhvac generates each model's codes from its remote's protocol; most
models are listed because their remote's codes match, not because someone
saw the unit follow. A {TICK} means someone sent pyhvac's codes to that unit
and it worked.

**Help by verifying yours.** If pyhvac (through hvactest, IR HVAC or your
own code) drives your unit, open a pull request that puts {TICK} in its row's
Verified column and says in Notes what you checked and with which pyhvac
version, for example: "modes, 18-30 °C, fan, swing, off/on; 0.2.0". Check
at least every mode, a few setpoints, the fan speeds and off/on, and say
in Notes anything that did not work. If your unit is not
listed, see [Getting a unit supported](README.md#getting-a-unit-supported).

Rows are kept by `python tools/verified.py`, which adds a row for each new
model and keeps the ticks.

"""

_CELL = re.compile(r"(?:\\\||[^|])*")


@dataclass(frozen=True)
class Mark:
    verified: bool
    notes: str


def _escape(text):
    return text.replace("|", "\\|")


def _cells(line):
    inner = line.strip()[1:-1]
    cells, pos = [], 0
    while True:
        m = _CELL.match(inner, pos)
        cells.append(m.group(0).strip().replace("\\|", "|"))
        pos = m.end()
        if pos >= len(inner):
            return cells
        pos += 1  # the separating "|"


def parse(text):
    """{(brand, model): Mark} from VERIFIED.md's table."""
    marks, table = {}, False
    for line in text.splitlines():
        if line == HEADER:
            table = True
            continue
        if not table or line == RULE or not line.startswith("|"):
            continue
        brand, model, _kind, _protocol, tick, notes = _cells(line)
        if tick not in ("", TICK):
            raise ValueError(f"{brand} {model}: Verified is {tick!r}, not {TICK}")
        marks[(brand, model)] = Mark(tick == TICK, notes)
    return marks


def _protocol(cls, variant):
    name = getattr(cls, "__name__", "")
    name = name[: -len("Device")] if name.endswith("Device") else name
    return f"{name} ({variant})" if variant else name


def render(models, marks):
    """VERIFIED.md for ``models`` (brands.MODELS rows), keeping ``marks``."""
    lines = [HEADER, RULE]
    for brand, model, kind, cls, variant in models:
        mark = marks.get((brand, model), Mark(False, ""))
        cells = (
            brand,
            model,
            kind,
            _protocol(cls, variant),
            TICK if mark.verified else "",
            mark.notes,
        )
        lines.append("| " + " | ".join(_escape(c) for c in cells) + " |")
    return INTRO + "\n".join(lines) + "\n"


def main():
    from pyhvac import brands

    marks = parse(FILE.read_text()) if FILE.exists() else {}
    current = {(b, m) for b, m, *_ in brands.MODELS}
    gone = sorted(k for k in marks if k not in current)
    if gone:
        names = ", ".join(" ".join(k) for k in gone)
        sys.exit(f"rows for models pyhvac no longer lists: {names}; move their marks")
    FILE.write_text(render(brands.MODELS, marks))


if __name__ == "__main__":
    main()
