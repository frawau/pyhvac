import base64

import pytest

from hvacir import match as M
from hvactest.compare import (
    NOT_THIS_PROTOCOL,
    compare,
    match_code,
    packet_from_base64,
)
from pyhvac import registry
from pyhvac.ir.codec import encode as ir_encode
from pyhvac.ir.formats import to_broadlink
from pyhvac.protocols.electra import ELECTRA_AC_LAYOUT
from pyhvac.state import HvacState


def electra():
    return registry.get_device("Electra", "AXW12DCS")


def packet(device, state):
    return to_broadlink(device.encode(None, state).signal)


def test_the_same_state_is_the_same():
    dev = electra()
    st = HvacState(True, "cool", 24.0, fan="2")
    assert compare(dev, st, packet(dev, st)).verdict == "same"


def test_another_setpoint_differs_in_that_field():
    dev = electra()
    learned = packet(dev, HvacState(True, "cool", 22.0, fan="2"))
    result = compare(dev, HvacState(True, "cool", 24.0, fan="2"), learned)
    assert result.verdict == "differs"
    assert result.fields == {"temperature": (22, 24)}


def test_a_field_pyhvac_never_sets_is_named():
    dev = electra()
    st = HvacState(True, "cool", 24.0)
    (frame,) = dev.frames(None, dev.normalise(st), ())
    data = bytearray(frame.data)
    ELECTRA_AC_LAYOUT.write_raw(data, "sensor_temp", 0x19)
    ELECTRA_AC_LAYOUT.checksum.apply(data)
    signal = ir_encode(dev.PROTOCOL, [type(frame)(frame.section, bytes(data))])
    result = compare(dev, st, to_broadlink(signal))
    assert result.verdict == "differs" and set(result.fields) == {"sensor_temp"}


def test_another_protocol_is_not_this_protocol():
    gree = registry.get_device("Gree", registry.models("Gree")[0])
    st = HvacState(True, "cool", 24.0)
    assert compare(electra(), st, packet(gree, st)).verdict == NOT_THIS_PROTOCOL


def test_match_finds_the_device_and_the_state():
    dev = electra()
    code = packet(dev, HvacState(True, "heat", 26.0, fan="3"))
    rows = match_code(code, M.candidates())
    assert rows[0].name == "ElectraAcDevice"
    assert rows[0].state.startswith("heat 26 fan 3")


def test_a_pasted_code_is_read():
    dev = electra()
    code = packet(dev, HvacState(True, "cool", 24.0))
    assert packet_from_base64(base64.b64encode(code).decode()) == code
    with pytest.raises(ValueError):
        packet_from_base64("bm90IGEgcGFja2V0")  # "not a packet"
