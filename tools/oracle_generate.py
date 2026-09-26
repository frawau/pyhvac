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
            for state in state_grid(
                probe.capabilities, probe.xtra_capabilities, opts.limit
            ):
                dev = cls()
                # Bypass the setters: IRGHVAC.set_fan writes "mode" (known bug).
                dev.to_set = dict(state)
                try:
                    pulses = [int(x) for x in dev.to_lirc(dev.build_ircode())]
                except Exception as exc:  # record what works, report the rest
                    print(f"skip {cls.__name__} {state}: {exc!r}")
                    continue
                if not pulses:
                    print(f"skip {cls.__name__} {state}: no pulses from the C library")
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
