"""Command line: list brands/models, or print the IR command for a state."""

import argparse
import base64
import sys

from . import registry
from .ir.formats import to_broadlink, to_pronto, to_raw
from .state import HvacState


def _feature(text):
    name, _, value = text.partition("=")
    if value.lower() in ("on", "true", "yes"):
        return name, True
    if value.lower() in ("off", "false", "no"):
        return name, False
    return name, value


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pyhvac", description=__doc__)
    parser.add_argument("brand", nargs="?")
    parser.add_argument("model", nargs="?")
    parser.add_argument("--list", action="store_true", help="list the brands")
    parser.add_argument("--list-models", metavar="BRAND", help="list a brand's models")
    parser.add_argument("--mode", default="cool")
    parser.add_argument("--temperature", type=float, default=24.0)
    parser.add_argument("--fan", default="auto")
    parser.add_argument("--swing-v", default="off")
    parser.add_argument("--swing-h", default="off")
    parser.add_argument("--feature", action="append", default=[], type=_feature)
    parser.add_argument("--off", action="store_true", help="send power off")
    parser.add_argument(
        "--format", choices=("broadlink", "pronto", "raw"), default="broadlink"
    )
    opts = parser.parse_args(argv)
    if opts.list:
        print("\n".join(registry.brands()))
        return 0
    if opts.list_models:
        print("\n".join(registry.models(opts.list_models)))
        return 0
    if not opts.brand:
        parser.error("a brand is required (see --list)")
    device = registry.get_device(opts.brand, opts.model)
    state = HvacState(
        power=not opts.off,
        mode=opts.mode,
        temperature=opts.temperature,
        fan=opts.fan,
        swing_v=opts.swing_v,
        swing_h=opts.swing_h,
        features=dict(opts.feature),
    )
    signal = device.encode(None, state).signal
    if opts.format == "broadlink":
        print(base64.b64encode(to_broadlink(signal)).decode())
    elif opts.format == "pronto":
        print(to_pronto(signal))
    else:
        print(" ".join(str(p) for p in to_raw(signal)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
