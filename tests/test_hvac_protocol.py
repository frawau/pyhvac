import pytest

pytest.skip("old API: deleted in Task 6", allow_module_level=True)

import pytest

from pyhvac.ir.codec import encode
from pyhvac.ir.formats import to_broadlink
from pyhvac.ir.model import Frame, Protocol, PulseDistance, Section
from pyhvac.protocols.hvaclib import HVAC

TOY = Protocol(
    "toy",
    {
        "main": Section(
            PulseDistance(500, 500, 1500), header=(4000, 2000), footer=(500,), gap=20000
        ),
        "short": Section(
            PulseDistance(500, 500, 1500), header=(2000, 1000), footer=(500,), gap=20000
        ),
    },
)
TOY_PULSES = [4000, 2000, 500, 1500] + [500, 500] * 7 + [500, 20000]


class Toy(HVAC):
    PROTOCOL = TOY

    def __init__(self):
        super().__init__()
        self.is_msb = True  # must be ignored once PROTOCOL is set

    def _build_ircode(self):
        return [bytearray(b"\x01")]


def test_to_lirc_encodes_bytearray_frames_with_first_section():
    assert Toy().to_lirc([bytearray(b"\x01")]) == TOY_PULSES


def test_to_lirc_accepts_frame_objects():
    frames = [Frame("short", b"\x01", 1)]
    assert Toy().to_lirc(frames) == list(encode(TOY, frames).pulses)


def test_build_ircode_does_not_bit_reverse_with_protocol():
    assert Toy().build_ircode() == [bytearray(b"\x01")]


def test_build_signal():
    assert Toy().build_signal().pulses == tuple(TOY_PULSES)


def test_to_broadlink_goes_through_formatter():
    dev = Toy()
    assert dev.to_broadlink([bytearray(b"\x01")]) == to_broadlink(dev.build_signal())


def test_legacy_class_output_unchanged():
    dev = HVAC()
    frames = [bytearray(b"\x12\x34")]
    assert dev.to_lirc(frames)[:4] == [3500, 1750, 435, 435]
    assert dev.to_broadlink(frames).hex() == (
        "2600260073390e0e0e0e0e0e0e2b0e0e0e0e0e2b0e0e0e0e0e0e0e2b0e2b0e0e0e2b0e0e0e0e0e0001480d05"
    )


def test_build_signal_needs_protocol():
    with pytest.raises(NotImplementedError):
        HVAC().build_signal()
