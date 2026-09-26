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
                try:
                    dev, frames = build_native(cls, state)
                except Exception as exc:  # pre-existing plugin bugs
                    print(f"skip {name} {state}: {exc!r}")
                    continue
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
