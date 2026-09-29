#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Toshiba AC IR commands.
#
# Copyright (c) 2024 François Wautier
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies
# or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
# IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE
#

from .hvaclib import PulseBased, GenPluginObject
from .coolix import Coolix
from ..device import Device
from ..fields import Checksums, Field, InvertedPairs, Layout, Xor8
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_5, ON_OFF, SWING
from ..state import Capabilities, TemperatureRange


class Toshiba(PulseBased):

    STARTFRAME = [9000, 4440]
    MARK = [620]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [580, 1650]  # ditto

    def __init__(self):
        super().__init__("TOSHIBA_AC")
        self.capabilities = {
            "mode": ["auto", "cool", "dry", "fan", "heat"],
            "temperature": [17, 30],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
            "powerful": ["off", "on"],
            "economy": ["off", "on"],
            "purifier": ["off", "on"],
        }


# ----------------------------------------------------------------- ToshibaAc
# Layout from IRremoteESP8266's ToshibaProtocol (ir_Toshiba.h). sendToshibaAC
# is sendGeneric with kToshibaAcHdrMark/HdrSpace, kToshibaAcBitMark,
# kToshibaAcOneSpace/ZeroSpace, a kToshibaAcBitMark footer and
# kToshibaAcUsualGap, MSB first, 38 kHz. A message is 7, 9 or 10 bytes:
# byte 2's Length nibble is the byte count minus kToshibaAcMinLength (6), and
# the last byte is the XOR of the others (calcChecksum).
#
# IRToshibaAC::send sends kToshibaACMinRepeat (kSingleRepeat) repeats, so
# every message goes out twice. IRac::toshiba always calls setSwing, which
# sets _send_swing, so send() follows the state message (9 bytes, or 10 with
# Eco/Turbo) with the 7-byte swing message: the state with Length 1, Temp
# kToshibaAcMinTemp and the Swing field, cut at byte 6 (its checksum).

TOSHIBA_AC = Protocol(
    "toshiba_ac",
    {
        "main": Section(
            PulseDistance(580, 490, 1600),  # kToshibaAcBitMark/ZeroSpace/OneSpace
            header=(4400, 4300),  # kToshibaAcHdrMark / HdrSpace
            footer=(580,),  # kToshibaAcBitMark
            gap=7400,  # kToshibaAcUsualGap
            lsb_first=False,
        )
    },
    carrier=38000,
)

TOSHIBA_AC_MIN_TEMP, TOSHIBA_AC_MAX_TEMP = 17, 30  # kToshibaAcMinTemp / MaxTemp
TOSHIBA_AC_TEMP = {
    t: t - TOSHIBA_AC_MIN_TEMP
    for t in range(TOSHIBA_AC_MIN_TEMP, TOSHIBA_AC_MAX_TEMP + 1)
}
# kToshibaAc{Auto,Cool,Dry,Heat,Fan,Off}
TOSHIBA_AC_MODE = {"auto": 0, "cool": 1, "dry": 2, "heat": 3, "fan": 4, "off": 7}
# IRac: setFan(convertFan(speed)). convertFan maps kMin..kMax to 1..5
# (kToshibaAcFanMax - 4 .. kToshibaAcFanMax) and setFan stores a speed above
# kToshibaAcFanAuto plus one, so the Fan field carries 2..6.
TOSHIBA_AC_FAN = {"auto": 0, "1": 2, "2": 3, "3": 4, "4": 5, "5": 6}
# kToshibaAcSwing{Step,On,Off,Toggle}
TOSHIBA_AC_SWING = {"step": 0, "on": 1, "off": 2, "toggle": 4}
# kToshibaAcTurboOn / kToshibaAcEconoOn
TOSHIBA_AC_ECO_TURBO = {"turbo": 1, "econo": 3}


def _toshiba_ac_fields(swing_values=None):
    return {
        "length": Field.at(2, 0, 4),  # Length: byte count - kToshibaAcMinLength
        "model": Field.at(2, 4, 4),  # kToshibaAcRemoteA (IRac never sets it)
        "long_msg": Field.at(4, 3, 1),  # LongMsg
        "short_msg": Field.at(4, 5, 1),  # ShortMsg
        "swing": Field.at(5, 0, 3, values=swing_values),
        "temperature": Field.at(5, 4, 4, values=TOSHIBA_AC_TEMP),
    }


def _toshiba_ac_state_fields():
    return {
        **_toshiba_ac_fields(),
        "mode": Field.at(6, 0, 3, values=TOSHIBA_AC_MODE),
        "fan": Field.at(6, 5, 3, values=TOSHIBA_AC_FAN),
        "filter": Field.at(7, 4, 1),  # Filter (Pure / Ion)
    }


# The state message, 9 bytes. Skeleton: stateReset's kReset (0xF2, 0x0D,
# 0x03, 0xFC, 0x01, then zeros) with the fields cleared but Length (3);
# kReset covers all 9 bytes, so no bit is stale. Bytes 0-3 are inverted
# pairs (invertBytePairs over kToshibaAcInvertedLength). The state messages'
# Swing bits stay 0: setSwing writes them only into a short message.
TOSHIBA_AC_LAYOUT = Layout(
    bytes.fromhex("f20d03fc0100000000"),
    _toshiba_ac_state_fields(),
    Checksums(InvertedPairs(0, 4), Xor8(0, 8, 8)),
)

# The long state message, 10 bytes (setTurbo / setEcono set Length 4 and
# checksum() sets LongMsg); byte 8 is EcoTurbo. Byte 9, past kReset, is
# always the checksum.
TOSHIBA_AC_LONG_LAYOUT = Layout(
    bytes.fromhex("f20d04fb090000000000"),
    {
        **_toshiba_ac_state_fields(),
        "eco_turbo": Field.at(8, 0, 8, values=TOSHIBA_AC_ECO_TURBO),
    },
    Checksums(InvertedPairs(0, 4), Xor8(0, 9, 9)),
)

# The swing message, 7 bytes (Length 1, ShortMsg set, Temp 17 C).
TOSHIBA_AC_SWING_LAYOUT = Layout(
    bytes.fromhex("f20d01fe210000"),
    _toshiba_ac_fields(TOSHIBA_AC_SWING),
    Checksums(InvertedPairs(0, 4), Xor8(0, 6, 6)),
)


class ToshibaAcDevice(Device):
    """Toshiba A/C (and the Carrier units that use its remote): every setting
    is sent in full; ``previous`` is ignored (IRac::handleToggles has no
    Toshiba rule, and IRac::toshiba sends swing on/off, never the
    kToshibaAcSwingToggle code).

    As IRac::toshiba sends it from a fresh IRToshibaAC object:
    - the state message twice, then the swing message twice;
    - powerful or economy make the state message long (Eco/Turbo in byte 8);
      economy wins when both are on (setEcono comes after setTurbo);
    - purifier sets Filter and cuts the state message back to 9 bytes
      (setFilter), which drops powerful and economy;
    - an off message carries mode kToshibaAcOff (convertMode(kOff), and
      setPower(false)) with the target setpoint, fan and filter, and is never
      long (setMode with a new mode resets the length);
    - the swing message carries Temp kToshibaAcMinTemp, whatever the
      setpoint.

    Where the C path contradicts the header, the port sends the documented
    value (see the Defect in tests/test_toshiba_ac_device.py): swing
    "swing" sends kToshibaAcSwingOn. The old glue has no swing "on", so
    IRac's swingv stays kOff and the swing message always carried
    kToshibaAcSwingOff.
    """

    PROTOCOL = TOSHIBA_AC
    LAYOUTS = (TOSHIBA_AC_LAYOUT,) * 2 + (TOSHIBA_AC_SWING_LAYOUT,) * 2
    LONG_LAYOUTS = (TOSHIBA_AC_LONG_LAYOUT,) * 2 + (TOSHIBA_AC_SWING_LAYOUT,) * 2
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "fan", "heat"),
        temperature=TemperatureRange(17.0, 30.0),
        fan=FAN_5,
        swing_v=SWING,
        features={"powerful": ON_OFF, "economy": ON_OFF, "purifier": ON_OFF},
    )

    @staticmethod
    def is_long(target):
        """Whether ``target``'s state message is the long (10-byte) one."""
        features = target.features
        return (
            target.power
            and not features["purifier"]
            and (features["powerful"] or features["economy"])
        )

    def layouts(self, target):
        """The layout of each frame ``frames`` returns for ``target``."""
        return self.LONG_LAYOUTS if self.is_long(target) else self.LAYOUTS

    def frames(self, previous, target, actions):
        features = target.features
        values = dict(
            temperature=int(target.temperature),
            mode=target.mode if target.power else "off",
            fan=target.fan,
            filter=features["purifier"],
        )
        if self.is_long(target):
            values["eco_turbo"] = "econo" if features["economy"] else "turbo"
            state = TOSHIBA_AC_LONG_LAYOUT.build(**values)
        else:
            state = TOSHIBA_AC_LAYOUT.build(**values)
        swing = TOSHIBA_AC_SWING_LAYOUT.build(
            swing="on" if target.swing_v == "swing" else "off",
            temperature=TOSHIBA_AC_MIN_TEMP,
        )
        state, swing = Frame("main", bytes(state)), Frame("main", bytes(swing))
        return [state, state, swing, swing]


TOSHIBA_AC_MODELS = (
    "RAS-B13N3KV2",
    "Akita EVO II",
    "RAS-B13N3KVP-E",
    "RAS 18SKP-ES",
    "WH-TA04NE",
    "WC-L03SE",
    "WH-UB03NJ remote",
    "RAS-2558V",
    "WH-TA01JE remote",
    "RAS-25SKVP2-ND",
    "generic",
)
TOSHIBA_AC_CARRIER_MODELS = (  # carrier plugin
    "42NQV060M2 / 38NYV060M2",
    "42NQV050M2 / 38NYV050M2",
    "42NQV035M2 / 38NYV035M2",
    "42NQV025M2 / 38NYV025M2",
)


DEVICES = {}
DEVICES.update({m: ToshibaAcDevice for m in TOSHIBA_AC_MODELS})


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "RAS-B13N3KV2": Toshiba,
        "Akita EVO II": Toshiba,
        "RAS-B13N3KVP-E": Toshiba,
        "RAS 18SKP-ES": Toshiba,
        "WH-TA04NE": Toshiba,
        "WC-L03SE": Toshiba,
        "WH-UB03NJ remote": Toshiba,
        "RAS-2558V": Toshiba,
        "WH-TA01JE remote": Toshiba,
        "RAS-25SKVP2-ND": Toshiba,
        "generic": Toshiba,
        "RAS-M10YKV-E": Coolix,
        "RAS-M13YKV-E": Coolix,
        "RAS-4M27YAV-E": Coolix,
        "WH-E1YE remote": Coolix,
    }

    def __init__(self):
        self.brand = "toshiba"
