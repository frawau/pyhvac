"""Compare a learned Broadlink code with what pyhvac sends (no I/O).

Built on the hvacir matcher: the same loose decoding, the same comparison
modulo the fields a capture cannot pin down (the key pressed, toggles, the
remote's clock, checksums).
"""

import base64
import binascii
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from hvacir import match as M
from hvacir.codes import to_pulses
from pyhvac.state import HvacState

NOT_THIS_PROTOCOL = "not this protocol"


@dataclass
class Comparison:
    verdict: str  # "same", "differs" or NOT_THIS_PROTOCOL
    learned: Optional[Tuple[bytes, ...]] = None  # the learned code's frames
    sent: Optional[Tuple[bytes, ...]] = None  # pyhvac's frames for the state
    fields: Dict[str, Tuple[object, object]] = field(default_factory=dict)


@dataclass
class MatchRow:
    name: str  # candidate: "Class" or "Class/variant"
    state: Optional[str]  # a state that sends the code, or None


def packet_pulses(packet):
    """µs pulses of a Broadlink IR packet (bytes)."""
    return to_pulses(base64.b64encode(bytes(packet)).decode(), "Broadlink", "Base64")


def packet_from_base64(text):
    """The packet of a pasted base64 Broadlink code (ValueError if not)."""
    try:
        packet = base64.b64decode(text.strip() + "=" * (-len(text.strip()) % 4))
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"not base64: {exc}") from None
    packet_pulses(packet)  # raises ValueError if it is no Broadlink IR packet
    return packet


def _values(device, frames):
    """Field name -> value over every layout placed on ``frames`` (a name
    a later frame repeats gets "#<n>")."""
    joined = b"".join(frames)
    lengths = tuple(len(f) for f in frames)
    out = {}
    for offset, layout in M._place(getattr(device, "LAYOUTS", ()), lengths):
        data = joined[offset : offset + len(layout.skeleton)]
        for name, value in layout.read(data).items():
            key, n = name, 1
            while key in out:
                n += 1
                key = f"{name}#{n}"
            out[key] = value
    return out


def _differing(device, learned, sent):
    if tuple(len(f) for f in learned) != tuple(len(f) for f in sent):
        return {"frames": ([len(f) for f in learned], [len(f) for f in sent])}
    got, want = _values(device, learned), _values(device, sent)
    out = {
        name: (got[name], want.get(name))
        for name in got
        if got[name] != want.get(name) and not M.UNRECORDED.match(name.split("#")[0])
    }
    if not out:  # no layout names the bits: show the bytes
        out = {
            f"byte {i}": (f"{a:02x}", f"{b:02x}")
            for i, (a, b) in enumerate(zip(b"".join(learned), b"".join(sent)))
            if a != b
        }
    return out


def compare(device, state, packet, previous=None, name=None):
    """How the learned ``packet`` compares with what ``device`` sends for
    ``state`` (after ``previous``, if given)."""
    cand = M.candidate(device, name or type(device).__name__)
    if cand is None:
        raise ValueError(f"{type(device).__name__} has no IR protocol")
    learned = M.decode_code(cand, packet_pulses(packet))
    if learned is None or not M._valid(device, learned):
        return Comparison(NOT_THIS_PROTOCOL)
    target = device.normalise(state)
    before = None if previous is None else device.normalise(previous)
    sent = tuple(f.data for f in device.frames(before, target, ()))
    seen = M._comparable(device, learned)
    if seen in {M._comparable(device, part) for part in M._parts(sent)}:
        return Comparison("same", learned, sent)
    return Comparison("differs", learned, sent, _differing(device, learned, sent))


def _state_for(cand, frames):
    """A state pyhvac sends ``frames`` for (any mode, setpoint, fan, swing,
    one feature changed; on or off), described, or None."""
    device = cand.device
    seen = M._comparable(device, frames)
    caps = device.capabilities
    defaults = {n: c.values[0] for n, c in caps.features.items()}
    reach = M._reachable(device, [], "C", defaults)
    if seen in reach:
        return M._describe(reach[seen])
    if M._powered_off(device, frames):
        return "off"
    return None


def match_code(packet, cands):
    """Candidates that decode ``packet`` with valid checksums, those with a
    state that sends it first."""
    pulses = packet_pulses(packet)
    rows = []
    for cand in cands:
        frames = M.decode_code(cand, pulses)
        if frames is None or not M._valid(cand.device, frames):
            continue
        rows.append(MatchRow(cand.name, _state_for(cand, frames)))
    return sorted(rows, key=lambda r: (r.state is None, r.name))
