"""Command line: list brands/models, or print the IR command for a state."""

import argparse
import base64
import sys

from . import registry
from .ir.formats import to_broadlink, to_pronto, to_raw
from .state import HvacState


def _feature(text):
    name, sep, value = text.partition("=")
    if not sep or value.lower() in ("on", "true", "yes"):
        return name, True
    if value.lower() in ("off", "false", "no"):
        return name, False
    return name, value


def _report_changes(asked, sent):
    """Tell the user when the device could not send what was asked."""
    changes = []
    for name in ("power", "mode", "temperature", "fan", "swing_v", "swing_h"):
        if getattr(asked, name) != getattr(sent, name):
            changes.append(
                f"{name} {getattr(sent, name)!r} (asked {getattr(asked, name)!r})"
            )
    for name, value in asked.features.items():
        if sent.features.get(name) != value:
            changes.append(f"{name} {sent.features.get(name)!r} (asked {value!r})")
    if changes:
        print("pyhvac: sent " + ", ".join(changes), file=sys.stderr)


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
    try:
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
        command = device.encode(None, state)
    except (KeyError, ValueError) as exc:
        parser.error(exc.args[0] if exc.args else str(exc))
    _report_changes(state, command.state)
    signal = command.signal
    if opts.format == "broadlink":
        print(base64.b64encode(to_broadlink(signal)).decode())
    elif opts.format == "pronto":
        print(to_pronto(signal))
    else:
        print(" ".join(str(p) for p in to_raw(signal)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
