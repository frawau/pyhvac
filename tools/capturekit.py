"""From hvactest captures to a verdict and portkit records.

    python tools/capturekit.py check   LOG
    python tools/capturekit.py match   LOG [--json]
    python tools/capturekit.py records LOG OUT_DIR NAME

LOG is an hvactest session log (``--log``): each learn event holds the
learned Broadlink code and the Note typed before Learn, the setting the
remote shows, e.g. ``power=on mode=cool temperature=24 fan=auto``. Keys a
note leaves out are those of the first capture (the baseline).
"""

import argparse
import base64
import difflib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "tools"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

CORE_KEYS = ("power", "mode", "temperature", "fan", "swing_v", "swing_h")
MODES = ("auto", "cool", "heat", "dry", "fan")
TEMPERATURE = re.compile(r"^\d+(\.\d+)?F?$")
NO_CAPTURE = "no usable capture: every Learn timed out or the log is empty"


@dataclass
class Capture:
    index: int  # 1-based, over the learn events that hold a code
    time: str  # UTC, ISO 8601
    note: str
    setting: Dict[str, str]  # the note over the baseline's keys
    packet: bytes


def parse_note(text: str) -> Dict[str, str]:
    """``key=value`` pairs separated by spaces; ``#`` starts a comment."""
    out = {}
    for token in text.split("#", 1)[0].split():
        key, sep, value = token.partition("=")
        if not sep or not key or not value:
            raise ValueError(f"{token!r} is not key=value")
        if key in out:
            raise ValueError(f"{key} given twice")
        out[key] = value
    return out


def load(path) -> Tuple[List[Capture], List[str]]:
    """The captures of an hvactest log, and the problems found reading it.

    Learn events without a code (timeouts, then retried) are not captures.
    """
    captures, problems, baseline, index = [], [], None, 0
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if event.get("event") != "learn" or not event.get("code"):
            continue
        index += 1
        note = event.get("note") or ""
        try:
            own = parse_note(note)
        except ValueError as exc:
            problems.append(f"capture {index}: {exc}")
            continue
        setting = own if baseline is None else {**baseline, **own}
        if baseline is None and own:
            baseline = own
        captures.append(
            Capture(
                index,
                event.get("time", ""),
                note,
                setting,
                base64.b64decode(event["code"]),
            )
        )
    return captures, problems


def _setting_errors(capture: Capture) -> List[str]:
    where = f"capture {capture.index}"
    if not capture.note.split("#", 1)[0].strip():
        return [f"{where}: no note (type the setting before Learn)"]
    errors, s = [], capture.setting
    if "power" in s and s["power"] not in ("on", "off"):
        errors.append(f"{where}: power={s['power']}, expected on or off")
    if "mode" in s and s["mode"] not in MODES:
        errors.append(f"{where}: mode={s['mode']}, expected one of {', '.join(MODES)}")
    if "temperature" in s and not TEMPERATURE.match(s["temperature"]):
        errors.append(
            f"{where}: temperature={s['temperature']}, expected a number"
            " (with F for a °F display)"
        )
    for key in parse_note(capture.note):
        if key in CORE_KEYS:
            continue
        close = [  # a misspelt core key, not a feature such as powerful
            k
            for k in difflib.get_close_matches(key, CORE_KEYS, n=1, cutoff=0.8)
            if abs(len(k) - len(key)) <= 2
        ]
        if close:
            errors.append(f"{where}: {key}: did you mean {close[0]}?")
    return errors


def check(captures: List[Capture]) -> Tuple[List[str], List[str]]:
    """(errors, warnings) about the captures."""
    if not captures:
        return [NO_CAPTURE], []
    errors, warnings = [], []
    for c in captures:
        errors += _setting_errors(c)
    by_packet: Dict[bytes, Capture] = {}
    by_setting: Dict[tuple, Capture] = {}
    for c in captures:
        key = tuple(sorted(c.setting.items()))
        first = by_packet.setdefault(c.packet, c)
        if first is not c and first.setting != c.setting:
            errors.append(
                f"capture {first.index} and capture {c.index}: the same code"
                " under different settings (a missed press?)"
            )
        same = by_setting.setdefault(key, c)
        if same is not c and same.packet != c.packet:
            warnings.append(
                f"capture {same.index} and capture {c.index}: the same setting,"
                " different codes (a toggle bit or a clock?)"
            )
    features = sorted(
        {k for c in captures for k in c.setting if k not in CORE_KEYS}
        - {e.split(": ")[1] for e in errors if "did you mean" in e}
    )
    if features:
        warnings.append(f"features (not core settings): {', '.join(features)}")
    return errors, warnings


def _cmd_check(args) -> int:
    captures, problems = load(args.log)
    for c in captures:
        print(f"{c.index:3}  {c.note}")
    errors, warnings = check(captures)
    for line in problems + errors:
        print(f"error: {line}")
    for line in warnings:
        print(f"warning: {line}")
    return 1 if problems or errors else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("check", help="check the captures and their notes")
    p.add_argument("log")
    p.set_defaults(run=_cmd_check)
    args = ap.parse_args(argv)
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())
