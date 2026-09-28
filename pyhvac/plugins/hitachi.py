#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Hitachi AC IR commands.
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

from dataclasses import dataclass

from .hvaclib import PulseBased, GenPluginObject
from ..device import Device
from ..fields import Checksum, Field, InvertedPairs, Layout, NibbleSum, bit_reverse
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import Capabilities, Choice, TemperatureRange

try:
    from ..irhvac import R_LT0541_HTA_A, R_LT0541_HTA_B
except ImportError:
    # Only the C-backed classes use these; keep the ported ones importable.
    R_LT0541_HTA_A = R_LT0541_HTA_B = None


class Hitachi(PulseBased):

    STARTFRAME = [3300, 1700]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [500, 1250]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC")
        self.capabilities = {
            "mode": ["off", "auto", "heat", "cool", "dry", "fan"],
            "temperature": [16, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
        }


class Hitachi1A(PulseBased):

    STARTFRAME = [3400, 3400]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [372, 1208]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC1", variant=R_LT0541_HTA_A)
        self.capabilities = {
            "mode": ["off", "auto", "heat", "cool", "dry", "fan"],
            "temperature": [16, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "sleep": ["off", "on"],
        }


class Hitachi1B(PulseBased):

    STARTFRAME = [3400, 3400]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [372, 1208]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC1", variant=R_LT0541_HTA_B)
        self.capabilities = {
            "mode": ["off", "auto", "heat", "cool", "dry", "fan"],
            "temperature": [16, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "sleep": ["off", "on"],
        }


class Hitachi424(PulseBased):

    LEAD = [29784, 49290]
    STARTFRAME = [3416, 1604]
    ENDFRAME = None
    MARK = [463]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [500, 1250]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC424")
        self.capabilities = {
            "mode": ["off", "fan", "heat", "cool", "dry"],
            "temperature": [16, 32],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
        }


class Hitachi3(PulseBased):

    STARTFRAME = [3400, 1660]
    ENDFRAME = None
    MARK = [460]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [410, 1250]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC3")
        self.capabilities = {
            "mode": ["off", "fan", "heat", "cool", "dry"],
            "temperature": [16, 32],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
        }


class Hitachi344(PulseBased):

    STARTFRAME = [3300, 1700]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [500, 1250]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC344")
        self.capabilities = {
            "mode": ["off", "cool", "fan", "dry", "heat"],
            "temperature": [16, 32],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
            "hswing": ["auto", "far right", "right", "middle", "left", "far left"],
        }


class Hitachi264(PulseBased):

    STARTFRAME = [3300, 1700]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [500, 1250]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC264")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [16, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "purifier": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
            "economy": ["off", "on"],
            "light": ["off", "on"],
        }


class Hitachi296(PulseBased):

    STARTFRAME = [3300, 1700]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [500, 1250]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC296")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat"],
            "temperature": [16, 25],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
        }


DEVICES = {}


# --------------------------------------------------------------- HitachiAc
# Layout from IRremoteESP8266's HitachiProtocol (ir_Hitachi.h): one 28-byte
# frame (kHitachiAcStateLength), sent MSB first (sendHitachiAC), so frame
# byte n is struct byte n. Every field holds its value bit-reversed
# (IRHitachiAc stores reverseBits(value, 8)), and so do the value tables.

HITACHI_AC = Protocol(
    "hitachi-ac",
    {
        "main": Section(
            PulseDistance(400, 500, 1250),  # kHitachiAcBitMark/ZeroSpace/OneSpace
            header=(3300, 1700),  # kHitachiAcHdrMark/HdrSpace
            footer=(400,),
            gap=100000,  # kHitachiAcMinGap = kDefaultMessageGap
            lsb_first=False,
        ),
    },
    carrier=38000,  # kHitachiAcFreq
)


@dataclass(frozen=True)
class HitachiAcChecksum(Checksum):
    """IRHitachiAc::calcChecksum: 62 minus the sum of the bit-reversed bytes
    before ``at``, bit-reversed."""

    def compute(self, data):
        return bit_reverse((62 - sum(self._input(data))) & 0xFF)


HITACHI_AC_MODES = {  # kHitachiAc{Auto,Heat,Cool,Dry,Fan}
    "auto": 2,
    "heat": 3,
    "cool": 4,
    "dry": 5,
    "fan": 0xC,
}
HITACHI_AC_FANS = {  # IRHitachiAc::convertFan
    "auto": 1,  # kHitachiAcFanAuto
    "1": 2,  # kHitachiAcFanLow (kLow)
    "2": 3,  # kHitachiAcFanMed (kMedium)
    "3": 4,  # kHitachiAcFanHigh - 1 (kHigh; kMax would be kHitachiAcFanHigh)
}
HITACHI_AC_MIN_TEMP = 16  # kHitachiAcMinTemp

# Skeleton: IRHitachiAc::stateReset with the written fields and the sum
# cleared. Bytes 0-8, 14/15 (0x60 below the swing bits) and 24 (0x80) are
# fixed; byte 9 is 0x10, or 0x90 at kHitachiAcMinTemp (setTemp).
HITACHI_AC_LAYOUT = Layout(
    bytes.fromhex("80080c02fd807f884810000000006060000000000000000080000000"),
    {
        "min_temp": Field.at(9, 7, 1),
        "mode": Field.at(
            10, 0, 8, values={k: bit_reverse(v) for k, v in HITACHI_AC_MODES.items()}
        ),
        "temperature": Field.at(  # whole °C, doubled
            11, 0, 8, values={t: bit_reverse(t << 1) for t in range(16, 33)}
        ),
        "fan": Field.at(
            13, 0, 8, values={k: bit_reverse(v) for k, v in HITACHI_AC_FANS.items()}
        ),
        "swing_v": Field.at(14, 7, 1, values={"off": 0, "swing": 1}),
        "swing_h": Field.at(15, 7, 1, values={"off": 0, "swing": 1}),
        "power": Field.at(17, 0, 1),
    },
    checksum=HitachiAcChecksum(0, 27, 27, reverse=True),
)


class HitachiAcDevice(Device):
    """Hitachi (RAS-35THA6): a full-state protocol, ``previous`` is ignored."""

    PROTOCOL = HITACHI_AC
    LAYOUTS = (HITACHI_AC_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "heat", "cool", "dry", "fan"),
        temperature=TemperatureRange(16.0, 32.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
        ),
        swing_v=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
        swing_h=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to kHitachiAcAuto).
        mode = target.mode if target.power else "auto"
        # IRHitachiAc::setFan clamps by mode: dry only has low and medium
        # (kHitachiAcFanLow..+1), fan has no auto (minimum kHitachiAcFanLow).
        fan = target.fan
        if mode == "dry":
            fan = {"auto": "1", "3": "2"}.get(fan, fan)
        elif mode == "fan" and fan == "auto":
            fan = "1"
        # setMode(kHitachiAcFan) writes the special temperature 64, but IRac
        # calls setTemp(degrees) after setMode, so the setpoint is always sent.
        temperature = int(target.temperature)
        data = HITACHI_AC_LAYOUT.build(
            min_temp=temperature == HITACHI_AC_MIN_TEMP,
            mode=mode,
            temperature=temperature,
            fan=fan,
            swing_v=target.swing_v,
            swing_h=target.swing_h,
            power=target.power,
        )
        return [Frame("main", bytes(data))]


HITACHI_AC_MODELS = ("RAS-35THA6 remote", "generic")


DEVICES.update({m: HitachiAcDevice for m in HITACHI_AC_MODELS})


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "RAS-35THA6 remote": Hitachi,
        "LT0541-HTA remote": Hitachi1A,
        "Series VI": Hitachi1A,
        "RAR-8P2 remote": Hitachi424,
        "RAS-AJ25H": Hitachi424,
        "PC-LH3B": Hitachi3,
        "KAZE-312KSDP": Hitachi1A,
        "R-LT0541-HTA/Y.K.1.1-1 V2.3 remote": Hitachi1A,
        "RAS-22NK": Hitachi344,
        "RF11T1": Hitachi344,
        "RAR-2P2 remote": Hitachi264,
        "RAK-25NH5": Hitachi264,
        "RAR-3U3 remote": Hitachi296,
        "RAS-70YHA3": Hitachi296,
        "generic": Hitachi,
        "generic 1 code a": Hitachi1A,
        "generic 1 code b": Hitachi1B,
        "generic 424": Hitachi424,
        "generic 3": Hitachi3,
        "generic 344": Hitachi344,
        "generic 264": Hitachi264,
        "generic 296": Hitachi296,
    }

    def __init__(self):
        self.brand = "hitachi"
