"""Edge formatters: convert a Signal to and from device-specific formats."""

from __future__ import annotations

import struct

# One Broadlink tick is 8192/269 µs (~30.45 µs).
_BROADLINK_TICK_NUM = 269
_BROADLINK_TICK_DEN = 8192
# One Pronto unit is (frequency word * 0.241246) µs.
_PRONTO_CLOCK = 0.241246


def broadlink_packet(pulses):
    """Broadlink IR packet for any mark/space pulse list in µs."""
    body = bytearray()
    for pulse in pulses:
        ticks = round(int(pulse) * _BROADLINK_TICK_NUM / _BROADLINK_TICK_DEN)
        if ticks < 256:
            body += struct.pack(">B", ticks)
        else:
            body += b"\x00" + struct.pack(">H", ticks)  # 0x00 escapes a 2-byte value
    packet = bytearray([0x26, 0x00])  # 0x26 = IR, 0x00 = no repeat
    packet += struct.pack("<H", len(body))
    packet += body
    packet += bytes([0x0D, 0x05])
    # The device prepends a 4-byte header and AES-encrypts in 16-byte blocks.
    remainder = (len(packet) + 4) % 16
    if remainder:
        packet += bytes(16 - remainder)
    return bytes(packet)


def to_broadlink(signal):
    return broadlink_packet(signal.pulses)


def from_broadlink(data):
    """µs pulses from a Broadlink IR packet (e.g. a learned code)."""
    data = bytes(data)
    if len(data) < 4 or data[0] != 0x26:
        raise ValueError("not a Broadlink IR packet (expected 0x26 header)")
    (length,) = struct.unpack("<H", data[2:4])
    body = data[4 : 4 + length]
    if len(body) < length:
        raise ValueError("truncated Broadlink packet")
    pulses = []
    i = 0
    while i < len(body):
        ticks = body[i]
        i += 1
        if ticks == 0:
            if i + 2 > len(body):
                raise ValueError("truncated 2-byte value in Broadlink packet")
            (ticks,) = struct.unpack(">H", body[i : i + 2])
            i += 2
        pulses.append(round(ticks * _BROADLINK_TICK_DEN / _BROADLINK_TICK_NUM))
    return pulses


def to_pronto(signal):
    """Learned-format (0000) Pronto hex."""
    freq = round(1_000_000 / (signal.carrier * _PRONTO_CLOCK))
    unit = freq * _PRONTO_CLOCK
    words = [0x0000, freq, len(signal.pulses) // 2, 0x0000]
    words += [round(d / unit) for d in signal.pulses]
    return " ".join(f"{w:04X}" for w in words)


def from_pronto(text):
    """µs pulses from a learned-format (0000) Pronto hex string."""
    words = [int(w, 16) for w in text.split()]
    if len(words) < 4 or words[0] != 0x0000:
        raise ValueError("only learned (0000) Pronto codes are supported")
    freq, once, repeat = words[1], words[2], words[3]
    count = 2 * (once + repeat)
    body = words[4 : 4 + count]
    if len(body) != count:
        raise ValueError(f"Pronto code announces {count} durations, has {len(body)}")
    unit = freq * _PRONTO_CLOCK
    return [round(w * unit) for w in body]


def to_raw(signal):
    """Signed µs list: positive marks, negative spaces."""
    return [d if i % 2 == 0 else -d for i, d in enumerate(signal.pulses)]
