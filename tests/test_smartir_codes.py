import base64
import struct

import pytest

from pyhvac.ir.formats import broadlink_packet
from smartir.codes import Key, UnsupportedFormat, parse, to_pulses

PULSES = [3000, 1500, 500, 500, 500, 1500, 500, 100000]


def b64(pulses):
    return base64.b64encode(broadlink_packet(pulses)).decode()


def test_broadlink_base64_becomes_pulses():
    out = to_pulses(b64(PULSES), "Broadlink", "Base64")
    assert len(out) == len(PULSES)
    assert all(abs(a - b) <= 0.02 * b + 31 for a, b in zip(out, PULSES))


@pytest.mark.parametrize(
    "controller, code",
    [
        ("ESPHome", "[3000, -1500, 500, -500, 500, -1500, 500, -100000]"),
        ("LOOKin", "3000 -1500 500 -500 500 -1500 500 -100000"),
    ],
)
def test_signed_raw_lists_become_pulses(controller, code):
    assert to_pulses(code, controller, "Raw") == PULSES


def z6(pulses):
    """A Xiaomi (Chuangmi) "Z6" raw code: 0x67 0xA5, the pulse count (uint16
    LE), 16 durations (uint32 LE), then one table index per pulse, two per
    byte, low nibble first."""
    table = sorted(set(pulses))
    body = bytes([0x67, 0xA5]) + struct.pack("<H", len(pulses))
    body += b"".join(struct.pack("<I", d) for d in table + [0] * (16 - len(table)))
    idx = [table.index(p) for p in pulses] + [0] * (len(pulses) % 2)
    body += bytes(idx[i] | idx[i + 1] << 4 for i in range(0, len(idx), 2))
    return base64.b64encode(body).decode()


def test_xiaomi_z6_codes_become_pulses():
    assert to_pulses(z6(PULSES), "Xiaomi", "Raw") == PULSES


def test_other_xiaomi_codes_are_unsupported():
    # the compressed "m..."/"n..." codes
    with pytest.raises(UnsupportedFormat):
        to_pulses("m0wmssmM4mIApTOYTKbSycgEnNJzOQA4mM1mEwAQwAPw", "Xiaomi", "Raw")


def test_parse_walks_modes_fans_swings_and_temperatures():
    data = {
        "manufacturer": "Acme",
        "supportedModels": ["X1"],
        "supportedController": "Broadlink",
        "commandsEncoding": "Base64",
        "minTemperature": 16,
        "maxTemperature": 17,
        "precision": 1,
        "operationModes": ["cool"],
        "fanModes": ["low", "high"],
        "swingModes": ["off", "on"],
        "commands": {
            "off": b64(PULSES),
            "cool": {
                "low": {"off": {"16": b64(PULSES), "17": "!!bad!!"}},
                "high": {"on": {"16": b64(PULSES)}},
            },
        },
    }
    f = parse(42, data)
    assert f.number == 42 and f.manufacturer == "Acme" and f.models == ("X1",)
    keys = [c.key for c in f.codes]
    assert Key("off", None, None, None) in keys
    assert Key("cool", "low", "off", 16.0) in keys
    assert Key("cool", "high", "on", 16.0) in keys
    assert f.skipped == 1 and len(f.codes) == 3


def test_parse_without_swing_level():
    data = {
        "supportedController": "Broadlink",
        "commandsEncoding": "Base64",
        "commands": {"heat": {"auto": {"20": b64(PULSES)}}},
    }
    (code,) = parse(1, data).codes
    assert code.key == Key("heat", "auto", None, 20.0)


def test_missing_base64_padding_is_tolerated():
    code = b64(PULSES).rstrip("=")
    assert len(to_pulses(code, "Broadlink", "Base64")) == len(PULSES)


def test_a_truncated_packet_keeps_the_pulses_it_has():
    packet = bytearray(broadlink_packet(PULSES))
    packet[2] += 4  # declared length overruns the data
    code = base64.b64encode(bytes(packet[: 4 + 8])).decode()  # cut inside the body
    out = to_pulses(code, "Broadlink", "Base64")
    assert 0 < len(out) < len(PULSES)


def test_a_null_code_is_skipped():
    data = {
        "supportedController": "Broadlink",
        "commandsEncoding": "Base64",
        "commands": {"off": None, "heat": {"auto": {"20": b64(PULSES)}}},
    }
    f = parse(1, data)
    assert len(f.codes) == 1 and f.skipped == 1
