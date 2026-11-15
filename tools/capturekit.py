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
import gzip
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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


# --------------------------------------------------------------------- match

SMARTIR_MODE = {"fan": "fan_only"}  # pyhvac mode -> SmartIR's name for it


@dataclass
class Verdict:
    path: str  # "supported", "variant" or "new"
    candidate: Optional[str] = None  # pyhvac "Device class[/variant]"
    fans: Dict[str, str] = field(default_factory=dict)  # remote word -> pyhvac
    swings: Dict[str, str] = field(default_factory=dict)  # "v/h" -> pyhvac
    gaps: Dict[str, int] = field(default_factory=dict)  # field -> captures
    features: Dict[str, str] = field(default_factory=dict)  # "word=value" -> pyhvac
    reasons: List[str] = field(default_factory=list)


def _is_core(capture: Capture) -> bool:
    return all(k in CORE_KEYS for k in capture.setting)


def _fahrenheit(captures: List[Capture]) -> bool:
    return any(c.setting.get("temperature", "").endswith("F") for c in captures)


def _number(text: Optional[str]) -> Optional[float]:
    return None if text is None else float(text.rstrip("F"))


def _swing_label(setting: Dict[str, str]) -> Optional[str]:
    if "swing_v" not in setting and "swing_h" not in setting:
        return None
    return f"{setting.get('swing_v', '-')}/{setting.get('swing_h', '-')}"


def _key(setting: Dict[str, str]):
    from hvacir.codes import Key

    if setting.get("power") == "off":
        return Key("off", None, None, None)
    mode = setting.get("mode")
    return Key(
        SMARTIR_MODE.get(mode, mode),
        setting.get("fan"),
        _swing_label(setting),
        _number(setting.get("temperature")),
    )


def to_smartir(captures: List[Capture]):
    """The core captures (no feature keys) as a SmartIR file for hvacir."""
    from hvacir.codes import Code, SmartIRFile
    from hvactest.compare import packet_pulses

    core = [c for c in captures if _is_core(c)]
    temps = [_number(c.setting.get("temperature")) for c in core]
    temps = [t for t in temps if t is not None]
    keys = [_key(c.setting) for c in core]
    return SmartIRFile(
        number=0,
        manufacturer="",
        models=(),
        controller="Broadlink",
        encoding="Base64",
        min_temperature=min(temps, default=None),
        max_temperature=max(temps, default=None),
        precision=None,
        modes=tuple(dict.fromkeys(k.mode for k in keys if k.mode != "off")),
        fans=tuple(dict.fromkeys(k.fan for k in keys if k.fan is not None)),
        swings=tuple(dict.fromkeys(k.swing for k in keys if k.swing is not None)),
        codes=tuple(
            Code(k, tuple(packet_pulses(c.packet))) for k, c in zip(keys, core)
        ),
        skipped=0,
    )


def _not_one_to_one(mapping: Dict[str, object], what: str) -> List[str]:
    words: Dict[object, List[str]] = {}
    for word, value in mapping.items():
        words.setdefault(value, []).append(word)
    return [
        f"{what} words {', '.join(sorted(ws))} all send pyhvac {what} {v!r}:"
        " the note or the model is wrong"
        for v, ws in words.items()
        if len(ws) > 1
    ]


def _core_state(capture: Capture, device, found, fahrenheit: bool):
    """The HvacState pyhvac would send for the capture's core setting."""
    from hvacir import match as M
    from pyhvac.state import HvacState

    s = capture.setting
    key = _key(s)
    if key.mode == "off":
        return None
    t = None if key.temperature is None else M._celsius(key, found.units)
    kw = {"features": dict(found.features)}
    if key.fan is not None and key.fan in found.fans:
        kw["fan"] = found.fans[key.fan]
    if key.swing is not None and key.swing in found.swings:
        kw["swing_v"], kw["swing_h"] = found.swings[key.swing]
    caps = device.capabilities
    return HvacState(
        True, s.get("mode"), caps.temperature.min if t is None else t, **kw
    )


def _feature_value(word: str, choice):
    """The pyhvac values the remote's word could mean, for one feature."""
    if set(choice.values) == {False, True}:
        return {"on": [True], "off": [False]}.get(word, [])
    return [v for v in choice.values if str(v) == word] or list(choice.values)


def _unlike(device, base, capture, cand) -> str:
    """What the capture's code differs in from its core setting alone:
    a feature capture that differs only in core fields was mislabelled."""
    from hvactest.compare import compare

    if base is None:
        return ""
    try:
        seen = compare(device, base, capture.packet, name=cand.name)
    except ValueError:
        return ""
    if seen.verdict == "same":
        return "; it sends its core setting unchanged (re-record it)"
    if seen.verdict != "differs" or not seen.fields:
        return ""
    names = ", ".join(sorted(n.split("#")[0] for n in seen.fields))
    return f"; it differs from its core setting only in: {names}"


def _map_features(captures, cand, found, fahrenheit) -> Tuple[Dict, List[str]]:
    from hvactest.compare import compare

    device = cand.device
    mapped, reasons = {}, []
    for c in captures:
        if _is_core(c):
            continue
        base = _core_state(c, device, found, fahrenheit)
        for word, value in c.setting.items():
            if word in CORE_KEYS:
                continue
            hit = None
            if base is not None:
                for name, choice in device.capabilities.features.items():
                    for v in _feature_value(value, choice):
                        state = base.__class__(
                            base.power,
                            base.mode,
                            base.temperature,
                            fan=base.fan,
                            swing_v=base.swing_v,
                            swing_h=base.swing_h,
                            features={**base.features, name: v},
                        )
                        try:
                            same = compare(device, state, c.packet, name=cand.name)
                        except ValueError:
                            continue
                        if same.verdict == "same":
                            hit = f"{name}={v}"
                            break
                    if hit:
                        break
            if hit:
                mapped[f"{word}={value}"] = hit
            else:
                reasons.append(
                    f"capture {c.index}: feature {word}={value}:"
                    f" no pyhvac feature sends it{_unlike(device, base, c, cand)}"
                )
    return mapped, reasons


def match(captures: List[Capture], cands=None) -> Verdict:
    """Strictly: is the remote a pyhvac model, a variant of one, or new?"""
    from hvacir import match as M

    if not captures:
        raise ValueError(NO_CAPTURE)
    cands = M.candidates() if cands is None else cands
    found = M.match(to_smartir(captures), cands)
    if found.verdict not in ("covered", "near"):
        return Verdict("new", reasons=["no pyhvac protocol decodes these codes"])
    cand = next(c for c in cands if c.name == found.candidate)
    fans = {w: str(v) for w, v in found.fans.items()}
    swings = {w: "/".join(map(str, v)) for w, v in found.swings.items()}
    reasons = []
    if found.verdict == "near":
        reasons.append(
            f"{found.decoded - found.verified} of {found.decoded} captures"
            " decode but are not what pyhvac sends for their setting"
        )
    if found.decoded < found.usable:
        reasons.append(f"{found.usable - found.decoded} captures do not decode")
    if found.relabelled:
        shown = "; ".join(f"{k} looks like {st}" for k, st in found.relabels)
        reasons.append(
            f"{found.relabelled} captures are what pyhvac sends for another"
            f" setting ({shown}): the note or the model is wrong"
        )
    reasons += _not_one_to_one(found.fans, "fan")
    reasons += _not_one_to_one(found.swings, "swing")
    features, feature_reasons = _map_features(
        captures, cand, found, _fahrenheit(captures)
    )
    reasons += feature_reasons
    strict = (
        found.verdict == "covered"
        and found.verified == found.decoded == found.usable
        and not reasons
    )
    return Verdict(
        "supported" if strict else "variant",
        found.candidate,
        fans,
        swings,
        dict(found.gaps),
        features,
        reasons,
    )


def records(captures: List[Capture], out_dir, name: str) -> Path:
    """portkit's input: OUT_DIR/NAME.json.gz, one {state, pulses} per capture."""
    from hvactest.compare import packet_pulses

    if not captures:
        raise ValueError(NO_CAPTURE)
    out = Path(out_dir) / f"{name}.json.gz"
    out.parent.mkdir(parents=True, exist_ok=True)
    data = [{"state": c.setting, "pulses": packet_pulses(c.packet)} for c in captures]
    out.write_bytes(gzip.compress(json.dumps(data).encode()))
    return out


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


def _usable(log):
    captures, problems = load(log)
    if not captures:
        print(f"error: {NO_CAPTURE}")
        return None
    for line in problems:
        print(f"warning: left out, {line}")
    return captures


def _cmd_match(args) -> int:
    captures = _usable(args.log)
    if captures is None:
        return 1
    verdict = match(captures)
    if args.json:
        print(json.dumps(asdict(verdict), indent=1))
        return 0
    print(f"path: {verdict.path}")
    if verdict.candidate:
        print(f"pyhvac device: {verdict.candidate}")
    for title, table in (
        ("fan", verdict.fans),
        ("swing", verdict.swings),
        ("feature", verdict.features),
    ):
        for word, value in table.items():
            print(f"  {title} {word} -> {value}")
    if verdict.gaps:
        print(
            "fields that differ (captures): "
            + ", ".join(f"{k} ({n})" for k, n in verdict.gaps.items())
        )
    for reason in verdict.reasons:
        print(f"- {reason}")
    return 0


def _cmd_records(args) -> int:
    captures = _usable(args.log)
    if captures is None:
        return 1
    print(records(captures, args.out_dir, args.name))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("check", help="check the captures and their notes")
    p.add_argument("log")
    p.set_defaults(run=_cmd_check)
    p = sub.add_parser("match", help="supported, a variant, or a new protocol?")
    p.add_argument("log")
    p.add_argument("--json", action="store_true")
    p.set_defaults(run=_cmd_match)
    p = sub.add_parser("records", help="write portkit's input")
    p.add_argument("log")
    p.add_argument("out_dir")
    p.add_argument("name")
    p.set_defaults(run=_cmd_records)
    args = ap.parse_args(argv)
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())
