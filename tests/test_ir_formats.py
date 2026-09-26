import pytest

from pyhvac.ir.codec import encode
from pyhvac.ir.formats import (
    broadlink_packet,
    from_broadlink,
    from_pronto,
    to_broadlink,
    to_pronto,
    to_raw,
)
from pyhvac.ir.model import Frame, Protocol, PulseDistance, Section, Signal

SMALL = Signal(38000, (9000, 4500, 560, 1690, 560, 40000))

# Output of HVAC().to_lirc([bytearray(b"\x12\x34")]) with the pre-migration code
LEGACY_PULSES = (
    [3500, 1750]
    + [435, 435, 435, 435, 435, 435, 435, 1300, 435, 435, 435, 435, 435, 1300, 435, 435]
    + [
        435,
        435,
        435,
        435,
        435,
        1300,
        435,
        1300,
        435,
        435,
        435,
        1300,
        435,
        435,
        435,
        435,
    ]
    + [435, 10000]
)
# ... and the matching HVAC().to_broadlink output
LEGACY_BROADLINK = "2600260073390e0e0e0e0e0e0e2b0e0e0e0e0e2b0e0e0e0e0e0e0e2b0e2b0e0e0e2b0e0e0e0e0e0001480d05"

NEC = Protocol(
    "nec",
    {
        "nec": Section(
            PulseDistance(560, 560, 1690), header=(9000, 4500), footer=(560,), gap=40000
        )
    },
)


def test_broadlink_matches_legacy_implementation():
    assert to_broadlink(Signal(38000, tuple(LEGACY_PULSES))).hex() == LEGACY_BROADLINK
    assert broadlink_packet(LEGACY_PULSES).hex() == LEGACY_BROADLINK


def test_broadlink_small_signal_uses_two_byte_escape():
    assert to_broadlink(SMALL).hex() == "26000a00000128941237120005210d05" + "00" * 12


def test_from_broadlink_quantises_to_broadlink_units():
    data = bytes.fromhex("26000a00000128941237120005210d05" + "00" * 12)
    assert from_broadlink(data) == [9014, 4507, 548, 1675, 548, 39985]


def test_broadlink_round_trip_within_quantisation():
    signal = encode(NEC, [Frame("nec", b"\x5a\xa5\x12")])
    back = from_broadlink(to_broadlink(signal))
    assert len(back) == len(signal.pulses)
    assert all(abs(a - b) <= 16 for a, b in zip(back, signal.pulses))


def test_from_broadlink_rejects_non_ir_packet():
    with pytest.raises(ValueError):
        from_broadlink(bytes.fromhex("b2000200"))


def test_from_broadlink_rejects_truncated_packet():
    with pytest.raises(ValueError):
        from_broadlink(bytes.fromhex("26000a000001"))


def test_pronto():
    assert to_pronto(SMALL) == "0000 006D 0003 0000 0156 00AB 0015 0040 0015 05F1"


def test_from_pronto():
    text = "0000 006D 0003 0000 0156 00AB 0015 0040 0015 05F1"
    assert from_pronto(text) == [8993, 4497, 552, 1683, 552, 39996]


def test_pronto_round_trip_within_one_unit():
    signal = encode(NEC, [Frame("nec", b"\x5a\xa5\x12")])
    back = from_pronto(to_pronto(signal))
    assert all(abs(a - b) <= 14 for a, b in zip(back, signal.pulses))


def test_from_pronto_rejects_non_learned_codes():
    with pytest.raises(ValueError):
        from_pronto("5000 0073 0000 0001 0001 0001")


def test_from_pronto_rejects_short_body():
    with pytest.raises(ValueError):
        from_pronto("0000 006D 0003 0000 0156 00AB")


def test_raw_is_signed():
    assert to_raw(SMALL) == [9000, -4500, 560, -1690, 560, -40000]
