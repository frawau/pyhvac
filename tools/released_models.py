"""Add the current catalogue to tests/fixtures/released_models.json.

Run at each release: ``python tools/released_models.py``. Pairs are only
ever added; a pair pyhvac no longer lists stays, so the released-models
test keeps checking that it still resolves (through ``brands.ALIASES``).
"""

import json
from pathlib import Path

FIXTURE = (
    Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "released_models.json"
)


def merge(existing, current):
    """Sorted union of the released pairs and the current ones."""
    return [list(p) for p in sorted({*map(tuple, existing), *map(tuple, current)})]


def main():
    from pyhvac import registry

    current = [(b, m) for b in registry.brands() for m in registry.models(b)]
    existing = json.loads(FIXTURE.read_text())
    FIXTURE.write_text(json.dumps(merge(existing, current), indent=1) + "\n")


if __name__ == "__main__":
    main()
