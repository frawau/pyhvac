"""Does a pyhvac device generate a SmartIR file's codes?

For each candidate (a Device class and variant from pyhvac.brands):
1. decode: every code must decode with the candidate's protocol, in full
   or as a prefix cut at a long space (learned codes often repeat);
2. infer: the features held constant over the file and the canonical
   value of each fan and swing label are those whose encoding differs from
   a sample of the codes in the fewest bits (coordinate descent);
   temperature keys are read as °C, or as °F converted to °C;
3. verify (the gate): every usable code is encoded with
   ``device.encode(None, state)`` and must decode to the same frames.

Verdicts: covered (all codes verified), near (decodes and a consistent
mapping, but some codes not reproduced: the layout fields that differ are
counted per code), unknown (no candidate decodes the file).
"""

import collections
import functools
import itertools
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from pyhvac import brands
from pyhvac.fields import Joined, checksum_bits
from pyhvac.ir.codec import DecodeError, decode
from pyhvac.state import HvacState

from .codes import Key

MODE = {
    "heat": "heat",
    "cool": "cool",
    "fan_only": "fan",
    "fan": "fan",
    "dry": "dry",
    "auto": "auto",
    "heat_cool": "auto",
}
CUT_SPACE = 7000  # µs: a learned code may be cut after any space this long
DECODE_SHARE = 0.9  # a candidate must decode this share of the codes
SAMPLE = 24  # codes the mapping is fitted on
PASSES = 2  # coordinate descent rounds


@dataclass
class Candidate:
    name: str  # "Device class/variant"
    device: object
    sequences: Tuple[Tuple[str, ...], ...]


@dataclass
class Match:
    verdict: str  # "covered", "near", "unknown", "unsupported"
    candidate: Optional[str] = None
    units: Optional[str] = None  # "C" or "F" (the file's temperature keys)
    fans: Dict[str, str] = field(default_factory=dict)
    swings: Dict[str, str] = field(default_factory=dict)
    features: Dict[str, object] = field(default_factory=dict)
    decoded: int = 0
    verified: int = 0
    usable: int = 0
    unexplained: Tuple[object, ...] = ()  # the first keys not reproduced
    relabelled: int = 0  # codes pyhvac produces, but for another state
    relabels: Tuple[object, ...] = ()  # the first (key, state as text) of those
    gaps: Dict[str, int] = field(default_factory=dict)  # field -> codes


def _probe_states(device):
    caps = device.capabilities
    t = caps.temperature.snap((caps.temperature.min + caps.temperature.max) / 2)
    base = HvacState(True, caps.modes[0], t)
    yield base
    yield HvacState(False, caps.modes[0], t)
    for name, choice in caps.features.items():
        on = next((v for v in choice.values if v), None)
        if on is not None:
            yield HvacState(True, caps.modes[0], t, features={name: on})
    if caps.swing_v is not None:
        for v in caps.swing_v.values:
            yield HvacState(True, caps.modes[0], t, swing_v=v)


def candidates():
    """One Candidate per distinct (Device class, variant) in pyhvac.brands,
    and per variant a class declares in ``VARIANTS`` (one may have no row
    yet: the import is how it gets one)."""
    rows = list(brands.MODELS)
    for brand, model, kind, cls, variant in brands.MODELS:
        rows += [(brand, model, kind, cls, v) for v in getattr(cls, "VARIANTS", ())]
    out, seen = [], set()
    for brand, model, kind, cls, variant in rows:
        if (cls, variant) in seen:
            continue
        seen.add((cls, variant))
        try:
            device = (
                cls(brand, model, variant=variant) if variant else cls(brand, model)
            )
        except (TypeError, ValueError):
            continue
        if device.PROTOCOL is None:
            continue
        sequences = set()
        for state in _probe_states(device):
            try:
                frames = device.frames(None, device.normalise(state), ())
            except (TypeError, ValueError, KeyError):
                continue
            sequences.add(tuple(f.section for f in frames))
        name = cls.__name__ + (f"/{variant}" if variant else "")
        out.append(Candidate(name, device, tuple(sorted(sequences, key=len))))
    return out


def decode_code(candidate, pulses):
    """The frames a code decodes to (bytes per frame), or None."""
    cuts = [len(pulses)] + [
        i + 1 for i, d in enumerate(pulses) if i % 2 and d >= CUT_SPACE
    ]
    for end in cuts:
        for seq in candidate.sequences:
            try:
                frames = decode(candidate.device.PROTOCOL, pulses[:end], expected=seq)
            except (DecodeError, ValueError):
                continue
            return tuple(f.data for f in frames)
    return None


def _frames(device, state):
    try:
        return tuple(f.data for f in device.frames(None, device.normalise(state), ()))
    except (TypeError, ValueError, KeyError):
        return None


def _celsius(key, units):
    if key.temperature is None:
        return None
    if units == "C":
        return key.temperature
    return round((key.temperature - 32) * 5 / 9, 1)


def _state(device, key, units, fan, swing, features, power=True, mode=None):
    caps = device.capabilities
    mode = mode or MODE.get(key.mode)
    if mode is None:
        return None
    t = _celsius(key, units)
    kw = {"features": dict(features)}
    if fan is not None:
        kw["fan"] = fan
    if swing is not None:
        kw["swing_v"] = swing
    try:
        return HvacState(power, mode, caps.temperature.min if t is None else t, **kw)
    except ValueError:
        return None


BIG = 10**6  # distance between frames of different shapes


def _place(layouts, lengths):
    """[(byte offset in the joined message, Layout)] covering frames of
    ``lengths``: a Joined layout where its frames' total length fits, else a
    per-frame Layout of the frame's length."""
    out, i, offset = [], 0, 0
    while i < len(lengths):
        for entry in layouts:
            if isinstance(entry, Joined):
                size = sum(lengths[i : i + entry.count])
                if size == len(entry.layout.skeleton):
                    out.append((offset, entry.layout))
                    i, offset = i + entry.count, offset + size
                    break
            elif entry is not None and len(entry.skeleton) == lengths[i]:
                out.append((offset, entry))
                i, offset = i + 1, offset + lengths[i]
                break
        else:
            i, offset = i + 1, offset + lengths[i]
    return out


@functools.lru_cache(maxsize=None)
def _owners(device, lengths):
    """Joined-message bit -> field name ("checksum" for checksum bits)."""
    owners = {}
    for offset, layout in _place(getattr(device, "LAYOUTS", ()), lengths):
        base = 8 * offset
        for name, fl in layout.fields.items():
            owners.update({base + b: name for b in fl.bits})
        if layout.checksum is not None:
            owners.update(
                {base + b: "checksum" for b in checksum_bits(layout.checksum)}
            )
    return owners


@functools.lru_cache(maxsize=None)
def _mask(device, lengths):
    """Joined-message mask clearing the checksum bits: a checksum follows
    the other fields, so it is not counted as a difference."""
    mask = bytearray(b"\xff" * sum(lengths))
    for bit, name in _owners(device, lengths).items():
        if name == "checksum":
            mask[bit // 8] &= ~(1 << bit % 8) & 0xFF
    return bytes(mask)


def _valid(device, frames):
    """Whether every checksum of the layouts placed over ``frames`` holds: a
    protocol sharing the timing but not the checksums is another one."""
    joined = bytearray(b"".join(frames))
    for offset, layout in _place(
        getattr(device, "LAYOUTS", ()), tuple(len(f) for f in frames)
    ):
        if layout.checksum is None:
            continue
        data = joined[offset : offset + len(layout.skeleton)]
        if not layout.checksum.check(data):
            return False
    return True


def _distance(device, a, b):
    """Differing non-checksum bits between two frame tuples (BIG if their
    shapes differ)."""
    if (
        a is None
        or b is None
        or len(a) != len(b)
        or any(len(x) != len(y) for x, y in zip(a, b))
    ):
        return BIG
    mask = _mask(device, tuple(len(x) for x in a))
    return sum(
        bin((p ^ q) & m).count("1") for p, q, m in zip(b"".join(a), b"".join(b), mask)
    )


def _sample(on, size=SAMPLE):
    """Up to ``size`` codes spread over the file, every fan and swing label
    included."""
    out, seen = [], set()
    for k, f in on:
        if (k.fan, k.swing) not in seen:
            seen.add((k.fan, k.swing))
            out.append((k, f))
    step = max(1, len(on) // size)
    out += [c for c in on[::step] if c not in out]
    return out[: max(size, len(seen))]


def _fit(device, decoded, units):
    """Mapping (fans, swings, features) closest to the codes: coordinate
    descent on the differing bits over a sample of codes."""
    caps = device.capabilities
    on = [(k, f) for k, f in decoded if k.mode != "off" and MODE.get(k.mode)]
    if not on:
        return None
    sample = _sample(on)
    fans = caps.fan.values if caps.fan else (None,)
    swings = caps.swing_v.values if caps.swing_v else (None,)
    features = {n: c.values[0] for n, c in caps.features.items()}
    fan_map = {k.fan: fans[0] for k, _ in on}
    swing_map = {k.swing: swings[0] for k, _ in on}

    def cost(codes):
        total = 0
        for k, f in codes:
            st = _state(device, k, units, fan_map[k.fan], swing_map[k.swing], features)
            total += BIG if st is None else _distance(device, _frames(device, st), f)
        return total

    def descend(table, name, values, codes):
        scores = {}
        for v in values:
            table[name] = v
            scores[v] = cost(codes)
        table[name] = min(values, key=lambda v: (scores[v], values.index(v)))

    for _ in range(PASSES):
        for label in fan_map:
            descend(fan_map, label, fans, [c for c in sample if c[0].fan == label])
        for label in swing_map:
            descend(
                swing_map, label, swings, [c for c in sample if c[0].swing == label]
            )
        for name, choice in caps.features.items():
            descend(features, name, choice.values, sample)
    return fan_map, swing_map, features


def _gaps(device, frames, expected):
    """Names of the layout fields where ``frames`` differ from ``expected``."""
    if _distance(device, frames, expected) >= BIG:
        return {"frames"}
    owners = _owners(device, tuple(len(x) for x in frames))
    out = set()
    for i, (p, q) in enumerate(zip(b"".join(frames), b"".join(expected))):
        for bit in range(8):
            if (p ^ q) >> bit & 1:
                out.add(owners.get(8 * i + bit, f"byte {i} bit {bit}"))
    if len(out) > 1:
        out.discard("checksum")  # it follows the other fields
    return out


def _off_frames(device, decoded, units, fan_map, swing_map, features, modes):
    """Every frame tuple an "off" code may be: a learned off code carries the
    mode, setpoint and fan last sent, which the file does not record."""
    on_keys = {k for k, _ in decoded if k.mode != "off"}
    temps = {k.temperature for k in on_keys} or {None}
    modes = [MODE[m] for m in modes if m in MODE] or ["cool"]
    fans = set(fan_map.values()) | {None}
    swings = set(swing_map.values()) | {None}
    out = set()
    for mode, t, fan, swing in itertools.product(modes, temps, fans, swings):
        key = Key(mode, None, None, t)
        st = _state(device, key, units, fan, swing, features, False, mode)
        if st is not None:
            out.add(_frames(device, st))
    return out


def _temperatures(device, decoded, units):
    """The setpoints worth trying: the file's keys and the device's whole
    degrees (and its half degrees, if it has them)."""
    caps = device.capabilities.temperature
    out = {_celsius(k, units) for k, _ in decoded if k.temperature is not None}
    step = 5 if 5 in caps.decimals else 10
    out |= {t / 10 for t in range(round(caps.min * 10), round(caps.max * 10) + 1, step)}
    return sorted(t for t in out if t is not None)


def _reachable(device, decoded, units, features):
    """Frame tuple -> a state that sends it, over power on and off and every
    mode, setpoint, fan and swing with the file's features, and with each feature changed alone.
    The tail of a multi-frame message counts too (a remote may send a
    toggle word alone, pyhvac sends it after the state word)."""
    caps = device.capabilities
    fans = caps.fan.values if caps.fan else ("auto",)
    swings = caps.swing_v.values if caps.swing_v else ("off",)
    temps = _temperatures(device, decoded, units)
    variants = [dict(features)]
    for name, choice in caps.features.items():
        for value in choice.values:
            if value != features.get(name):
                variants.append({**features, name: value})
    size = 2 * len(caps.modes) * len(temps) * len(fans) * len(swings)
    if size * len(variants) > REACH_LIMIT:
        variants = variants[: max(1, REACH_LIMIT // max(size, 1))]
    out = {}
    for feats in variants:
        product = itertools.product((True, False), caps.modes, temps, fans, swings)
        for power, mode, t, fan, swing in product:
            try:
                st = HvacState(power, mode, t, fan=fan, swing_v=swing, features=feats)
            except ValueError:
                continue
            frames = _frames(device, st)
            if frames is None:
                continue
            for i in range(len(frames)):
                out.setdefault(frames[i:], st)
    return out


def _describe(state):
    """A state as text (the report shows it; worker processes return it)."""
    if not state.power:
        return "off"
    on = sorted(n for n, v in state.features.items() if v)
    text = f"{state.mode} {state.temperature:g} fan {state.fan} swing {state.swing_v}"
    return text + "".join(f" +{n}" for n in on)


def _verify(device, decoded, units, fan_map, swing_map, features, smartir_modes):
    """(verified count, relabels [(key, state)], unexplained keys, Counter of
    differing fields). A code pyhvac sends for its labelled state is
    verified; one it sends for another state is relabelled (SmartIR's labels
    are crowd-sourced: indicative, not definitive)."""
    verified, unexplained, off, gaps = 0, [], None, collections.Counter()
    relabels, reach = [], None
    for key, frames in decoded:
        if key.mode == "off":
            if off is None:
                off = _off_frames(
                    device, decoded, units, fan_map, swing_map, features, smartir_modes
                )
            ok = frames in off
            want = min(off, key=lambda o: _distance(device, frames, o)) if off else None
        else:
            st = _state(
                device,
                key,
                units,
                fan_map.get(key.fan),
                swing_map.get(key.swing),
                features,
            )
            want = None if st is None else _frames(device, st)
            ok = want == frames
        if ok:
            verified += 1
            continue
        if reach is None:
            reach = _reachable(device, decoded, units, features)
        if frames in reach:
            relabels.append((key, _describe(reach[frames])))
        else:
            unexplained.append(key)
            gaps.update(_gaps(device, frames, want))
    return verified, relabels, unexplained, gaps


def _rank(m):
    return (
        m.verdict != "unknown",
        m.verified + m.relabelled,
        m.verified,
        -sum(m.gaps.values()),
    )


VALID_SHARE = 0.5  # codes whose checksums hold: below this, another protocol
SHAPE_SHARE = 0.5  # a candidate whose frames differ in shape this often is wrong
REACH_LIMIT = 60000  # states enumerated per file and candidate, at most


def match(smartir_file, cands):
    """The best Match of a parsed SmartIRFile against the candidates."""
    if smartir_file.unsupported:
        return Match("unsupported")
    codes = smartir_file.codes
    usable = len(codes)
    if not usable:
        return Match("unknown")
    best = Match("unknown", usable=usable)
    units_order = (
        ("F", "C") if (smartir_file.max_temperature or 0) >= 50 else ("C", "F")
    )
    for cand in cands:
        probe = codes[len(codes) // 2]
        if decode_code(cand, list(probe.pulses)) is None:
            continue
        decoded = [(c.key, decode_code(cand, list(c.pulses))) for c in codes]
        decoded = [(k, f) for k, f in decoded if f is not None]
        if len(decoded) < DECODE_SHARE * usable:
            continue
        for units in units_order:
            fit = _fit(cand.device, decoded, units)
            if fit is None:
                continue
            fan_map, swing_map, features = fit
            verified, relabels, unexplained, gaps = _verify(
                cand.device,
                decoded,
                units,
                fan_map,
                swing_map,
                features,
                smartir_file.modes,
            )
            explained = verified + len(relabels)
            valid = sum(_valid(cand.device, f) for _, f in decoded)
            if valid < VALID_SHARE * len(decoded):
                continue
            if gaps["frames"] > SHAPE_SHARE * len(decoded):
                continue
            result = Match(
                "covered" if explained == len(decoded) else "near",
                cand.name,
                units,
                fan_map,
                swing_map,
                features,
                len(decoded),
                verified,
                usable,
                tuple(unexplained[:10]),
                len(relabels),
                tuple(relabels[:10]),
                dict(gaps.most_common()),
            )
            if _rank(result) > _rank(best):
                best = result
            if result.verdict == "covered":
                return best
    return best
