#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Daikin AC IR commands as done by the ARC480A44 and others
#
# This module  is in part based on the work/code from:
#      Scott Kyle https://gist.github.com/appden/42d5272bf128125b019c45bc2ed3311f
#      mat_fr     https://www.instructables.com/id/Reverse-engineering-of-an-Air-Conditioning-control/
#
# Copyright (c) 2023 François Wautier
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
##

import struct
from dataclasses import dataclass

from .hvaclib import HVAC, PulseBased, GenPluginObject, bit_reverse
from ..device import Device
from ..fields import Checksum, Field, Layout, NibbleSum, Sum8
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import Capabilities, Choice, TemperatureRange

DAIKIN_NATIVE = Protocol(
    "daikin-native",
    {
        "main": Section(
            PulseDistance(435, 435, 1300),
            header=(3500, 1750),
            footer=(435,),
            gap=10000,
            lsb_first=False,
        )
    },
)


class Daikinth(HVAC):
    """Generic Daikin HVAC object. It must have, at the very minimum
    "mode" and "temperature" capabilities"""

    PROTOCOL = DAIKIN_NATIVE

    FBODY = b"\x88\x5b\xe4\x00\x00\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x00\xa3\x00\x10"

    def __init__(self):
        super().__init__()
        self.brand = "Daikin"
        self.model = "Generic"
        self.capabilities = {
            "mode": ["off", "cool", "fan", "dry"],
            "temperature": [x for x in range(18, 32)],
        }
        # For functions that require their own frames
        self.xtra_capabilities = {}
        self.status = {"mode": "cool", "temperature": 25}

        self.to_set = {}

    def set_temperature(self, temp):
        if temp < self.capabilities["temperature"][0]:
            temp = self.capabilities["temperature"][0]
        elif temp > self.capabilities["temperature"][-1]:
            temp = self.capabilities["temperature"][-1]
        self.to_set["temperature"] = temp

    def code_temperature(self):
        if "temperature" in self.to_set:
            temp = self.to_set["temperature"]
            if "mode" in self.to_set and self.to_set["mode"] == "fan":
                temp = 25
        else:
            temp = self.status["temperature"]
        mask = bytearray(b"\x00" * 18)
        mask[6] = bit_reverse(temp * 2)
        return mask, False

    def set_fan(self, mode):
        if "fan" not in self.capabilities:
            return
        if mode not in self.capabilities["fan"]:
            return
        self.to_set["fan"] = mode

    def code_fan(self):
        """mode is one of auto, lowest, low, medium, high, highest"""
        if "fan" in self.to_set:
            mode = self.to_set["fan"]
        else:
            if "fan" in self.capabilities:
                mode = self.status["fan"]
            else:
                mode = "auto"
        rank = ["lowest", "low", "medium", "high", "highest"]
        if mode not in rank:
            mode = "auto"  # Just in case
        mask = bytearray(b"\x00" * 18)
        if mode == "auto":
            mask[8] = 0x05
        else:
            mask[8] = bit_reverse(48 + (16 * rank.index(mode)))
        return mask, False

    def set_swing(self, mode):
        if "swing" not in self.capabilities:
            return
        if mode not in self.capabilities["swing"]:
            return
        self.to_set["swing"] = mode

    def code_swing(self):
        if "swing" in self.to_set:
            mode = self.to_set["swing"]
        else:
            if "swing" in self.capabilities:
                mode = self.status["swing"]
            else:
                mode = False

        mask = bytearray(b"\x00" * 18)
        if mode == "on":
            mask[8] = 0xF0
        else:
            mask[8] = 0x00
        return mask, False

    def set_powerful(self, mode="off"):
        # print("\n\nDaikin set powerful {}\n\n".format(mode))
        if "powerful" not in self.capabilities:
            return
        if mode not in self.capabilities["powerful"]:
            return
        self.to_set["powerful"] = mode

    def code_powerful(self):

        if "powerful" in self.to_set:
            mode = self.to_set["powerful"]
        else:
            if "powerful" in self.capabilities:
                mode = self.status["powerful"]
            else:
                mode = False

        mask = bytearray(b"\x00" * 18)
        if mode == True:
            mask[13] = 0x80
        return mask, True

    def set_comfort(self, mode="off"):
        if "comfort" not in self.xtra_capabilities:
            return
        if mode not in self.xtra_capabilities["comfort"]:
            return
        # This is a toggling value AFAIK
        if self.status["comfort"] != mode:
            self.to_set["comfort"] = mode

    def code_comfort(self):
        """Some Daikin AC seem to have such"""
        return []

    def set_mode(self, mode):
        if mode not in self.capabilities["mode"]:
            mode = "cool"
        self.to_set["mode"] = mode
        if mode == "fan":
            self.to_set["temperature"] = 25
        if mode == "off":
            self.to_set = {"mode": "off"}

    def code_mode(self):
        if "mode" in self.to_set:
            mode = self.to_set["mode"]
        else:
            mode = self.status["mode"]

        mask = bytearray(b"\x00" * 18)
        if mode == "off":
            mask[16] = 0x02
            cmode = self.status["mode"]
            if cmode == "off":
                mask[5] = 0x0C
            elif cmode == "dry":
                mask[5] = 0x04
            elif cmode == "fan":
                mask[5] = 0x06
            elif cmode == "heat":
                mask[5] = 0x02
            elif cmode == "auto":
                mask[5] = 0x00
        elif mode == "dry":
            mask[5] = 0x84
            mask[6] = 0x03
        elif mode == "fan":
            mask[5] = 0x86
        elif mode == "heat":
            mask[5] = 0x82
        elif mode == "auto":
            mask[5] = 0x80
        else:
            mask[5] = 0x8C
        return mask, True

    def build_code(self):
        frames = []
        packet = bytearray(self.FBODY)
        # Note that set mod must be last for it replaces values
        for f in [
            self.code_temperature,
            self.code_fan,
            self.code_swing,
            self.code_powerful,
            self.code_mode,
        ]:
            mask, replace = f()
            if replace:
                packet = bytearray([y or x for x, y in zip(packet, mask)])
            else:
                packet = bytearray([x | y for x, y in zip(packet, mask)])
        frames += [packet]
        return frames

    def _build_ircode(self):
        frames = []
        frames += self.code_comfort()
        frames += self.build_code()
        idx = 0
        for x in frames:
            frames[idx] += self.crc(x)
            idx += 1
        return frames

    def crc(self, frame):
        crc = 0
        for x in frame:
            # print("Adding 0x%02x as 0x%02x"%(x,bit_reverse(x)))
            crc += bit_reverse(x)
            # print("crc now 0x%02x"%crc)
        return bit_reverse(crc & 0xFF).to_bytes(1, "big")


class Smash2(Daikinth):
    def __init__(self):
        super().__init__()
        self.model = "Smash 2"
        self.capabilities = {
            "mode": ["off", "cool", "fan", "dry"],
            "temperature": [x for x in range(18, 32)],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
            "powerful": ["off", "on"],
        }
        self.status = {
            "mode": "off",
            "temperature": 25,
            "fan": "auto",
            "swing": "off",
            "powerful": "off",
        }


class Daikin(PulseBased):
    STARTFRAME = [3650, 1623]
    ENDFRAME = None
    MARK = [428]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [428, 1280]  # ditto

    def __init__(self):
        super().__init__("DAIKIN")
        self.capabilities = {
            "mode": ["off", "auto", "dry", "cool", "heat", "fan"],
            "temperature": [10, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "economy": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
            "cleaning": ["off", "on"],
        }
        self.temperature_step = 0.5


class Daikin2(PulseBased):
    LEAD = [10024, 25180]
    STARTFRAME = [3500, 1728]
    ENDFRAME = None
    MARK = [460]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [420, 1270]  # ditto

    def __init__(self):
        super().__init__("DAIKIN2")
        self.capabilities = {
            "mode": ["off", "auto", "dry", "cool", "heat", "fan"],
            "temperature": [10, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto", "ceiling", "90°", "60°", "45°", "30°", "0°"],
            "hswing": [
                "off",
                "far left",
                "close left",
                "middle",
                "close right",
                "far right",
                "wide",
            ],
            "economy": ["off", "on"],
            "economy": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
            "cleaning": ["off", "on"],
            "purifier": ["off", "on"],
        }


class Daikin216(PulseBased):
    STARTFRAME = [3440, 1750]
    ENDFRAME = None
    MARK = [420]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [450, 1300]  # ditto

    def __init__(self):
        super().__init__("DAIKIN216")
        self.capabilities = {
            "mode": ["off", "auto", "dry", "cool", "heat", "fan"],
            "temperature": [10, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
        }


class Daikin160(PulseBased):
    STARTFRAME = [5000, 2145]
    ENDFRAME = None
    MARK = [342]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [700, 1786]  # ditto

    def __init__(self):
        super().__init__("DAIKIN160")
        self.capabilities = {
            "mode": ["off", "auto", "dry", "cool", "heat", "fan"],
            "temperature": [10, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto", "90°", "60°", "45°", "30°", "0°"],
        }


class Daikin176(PulseBased):
    STARTFRAME = [5070, 2140]
    ENDFRAME = None
    MARK = [370]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [710, 1780]  # ditto

    def __init__(self):
        super().__init__("DAIKIN176")
        self.capabilities = {
            "mode": ["off", "auto", "dry", "cool", "heat", "fan"],
            "temperature": [10, 32],
            "fan": ["high", "low"],
            "hswing": ["off", "on"],
        }


class Daikin128(PulseBased):
    LEAD = [9800, 9800]
    STARTFRAME = [4600, 2500]
    ENDFRAME = [4600, 20300]
    MARK = [350]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [382, 954]  # ditto

    def __init__(self):
        super().__init__("DAIKIN128")
        self.capabilities = {
            "mode": ["off", "auto", "dry", "cool", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
            "economy": ["off", "on"],
        }


class Daikin152(PulseBased):
    STARTFRAME = [3492, 1718]
    ENDFRAME = None
    MARK = [433]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [433, 1529]  # ditto

    def __init__(self):
        super().__init__("DAIKIN152")
        self.capabilities = {
            "mode": ["off", "auto", "dry", "cool", "heat", "fan"],
            "temperature": [10, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "economy": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
        }


class Daikin64(PulseBased):
    STARTFRAME = [4920, 2230]
    ENDFRAME = None
    MARK = [298]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [780, 1850]  # ditto

    def __init__(self):
        super().__init__("DAIKIN64")
        self.capabilities = {
            "mode": ["off", "dry", "cool", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
        }


class Daikin312(PulseBased):
    LEAD = [10024, 25180]
    STARTFRAME = [3518, 1688]
    ENDFRAME = None
    MARK = [453]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [414, 1275]  # ditto

    def __init__(self):
        super().__init__("DAIKIN312")
        self.capabilities = {
            "mode": ["off", "auto", "dry", "cool", "heat", "fan"],
            "temperature": [10, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "quiet": ["off", "on"],
            "powerful": ["off", "on"],
            "light": ["off", "on"],
            "economy": ["off", "on"],
            "purifier": ["off", "on"],
            "cleaning": ["off", "on"],
        }
        self.temperature_step = 0.5


# --------------------------------------------------------------- Daikin2
# Layout from IRremoteESP8266's Daikin2Protocol (ir_Daikin.h): 39 bytes in
# two sections of 20 and 19, each closed by a sum-of-bytes checksum; frame
# byte n of the second section is struct byte n + 20.

DAIKIN2 = Protocol(
    "daikin2",
    {
        "leader": Section(None, header=(10024,), gap=25180),
        "main": Section(
            PulseDistance(460, 420, 1270),
            header=(3500, 1728),
            footer=(460,),
            gap=35204,
        ),
    },
    carrier=36700,
)

DAIKIN2_SWING_V = {  # kDaikin2SwingV*
    "off": 0xE,
    "auto": 0xF,
    "1": 0x1,  # highest
    "2": 0x2,  # high
    "3": 0x3,  # upper middle
    "4": 0x4,  # lower middle
    "5": 0x5,  # low
    "6": 0x6,  # lowest
}
DAIKIN2_SWING_H = {  # kDaikin2SwingH*
    "off": 0xBF,
    "1": 0xA8,  # far left
    "2": 0xA9,  # left
    "3": 0xAA,  # middle
    "4": 0xAB,  # right
    "5": 0xAC,  # far right
    "6": 0xA3,  # wide
}

DAIKIN2_FIRST = Layout(
    bytes.fromhex("11da2700010040f0200c8004b01624000000d000"),
    {
        "power2": Field.at(6, 7, 1),  # inverse of power
        "mold": Field.at(8, 3, 1),
        "swing_h": Field.at(17, 0, 8, values=DAIKIN2_SWING_H),
        "swing_v": Field.at(18, 0, 4, values=DAIKIN2_SWING_V),
    },
    checksum=Sum8(0, 19, 19),
)
DAIKIN2_SECOND = Layout(
    bytes.fromhex("11da27000008000000000006600000c1806000"),
    {
        "power": Field.at(5, 0, 1),
        "mode": Field.at(
            5, 4, 3, values={"auto": 0, "dry": 2, "cool": 3, "heat": 4, "fan": 6}
        ),
        "temperature": Field.at(6, 1, 6, encode=int),  # whole °C
        "fan": Field.at(8, 4, 4, values={"auto": 0xA, "1": 3, "2": 5, "3": 6}),
        "powerful": Field.at(13, 0, 1),
        "quiet": Field.at(13, 5, 1),
        "economy": Field.at(16, 2, 1),
        "purifier": Field.at(16, 4, 1),
    },
    checksum=Sum8(0, 18, 18),
)
DAIKIN2_MIN_COOL = 18.0  # kDaikin2MinCoolTemp


class Daikin2Device(Device):
    """Daikin2 (ARC477A1): a full-state protocol, ``previous`` is ignored."""

    PROTOCOL = DAIKIN2
    LAYOUTS = (None, DAIKIN2_FIRST, DAIKIN2_SECOND)
    capabilities = Capabilities(
        modes=("auto", "dry", "cool", "heat", "fan"),
        temperature=TemperatureRange(10.0, 32.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
        ),
        swing_v=Choice(
            ("off", "auto", "1", "2", "3", "4", "5", "6"),
            {
                "off": "off",
                "auto": "auto",
                "1": "ceiling",
                "2": "90°",
                "3": "60°",
                "4": "45°",
                "5": "30°",
                "6": "0°",
            },
        ),
        swing_h=Choice(
            ("off", "1", "2", "3", "4", "5", "6"),
            {
                "off": "off",
                "1": "far left",
                "2": "close left",
                "3": "middle",
                "4": "close right",
                "5": "far right",
                "6": "wide",
            },
        ),
        features={
            name: Choice((False, True), {False: "off", True: "on"})
            for name in ("economy", "powerful", "quiet", "cleaning", "purifier")
        },
    )

    def frames(self, previous, target, actions):
        feat = target.features
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which Daikin2 maps to auto), so the cool minimum never
        # applies to it.
        mode = target.mode if target.power else "auto"
        temperature = target.temperature
        if mode == "cool":
            temperature = max(temperature, DAIKIN2_MIN_COOL)
        first = DAIKIN2_FIRST.build(
            power2=not target.power,
            mold=feat["cleaning"],
            swing_h=target.swing_h,
            swing_v=target.swing_v,
        )
        second = DAIKIN2_SECOND.build(
            power=target.power,
            mode=mode,
            temperature=temperature,
            fan=target.fan,
            powerful=feat["powerful"],
            quiet=feat["quiet"] and not feat["powerful"],  # powerful cancels quiet
            economy=feat["economy"],
            purifier=feat["purifier"],
        )
        return [
            Frame("leader", b""),
            Frame("main", bytes(first)),
            Frame("main", bytes(second)),
        ]


DAIKIN2_MODELS = (
    "ARC477A1 remote",
    "FTXZ25NV1B",
    "FTXZ35NV1B",
    "FTXZ50NV1B",
    "Daikin2",
)
DEVICES = {model: Daikin2Device for model in DAIKIN2_MODELS}


# --------------------------------------------------------------- Daikin (ARC433)
# Layout from IRremoteESP8266's DaikinESPProtocol (ir_Daikin.h): 35 bytes in
# three sections of 8, 8 and 19, each closed by a sum-of-bytes checksum
# (kDaikinByteChecksum1/2, Sum3); frame byte n of the third section is
# struct byte n + 16. The message opens with a headerless 5-bit all-zero
# leader (kDaikinHeaderLength). Every space after a footer mark is
# kDaikinZeroSpace + kDaikinGap.

DAIKIN_ARC = Protocol(
    "daikin",
    {
        "leader": Section(PulseDistance(428, 428, 1280), footer=(428,), gap=29428),
        "main": Section(
            PulseDistance(428, 428, 1280),
            header=(3650, 1623),
            footer=(428,),
            gap=29428,
        ),
    },
    carrier=38000,
)

DAIKIN_ARC_SWING = {"off": 0x0, "swing": 0xF}  # kDaikinSwingOff / kDaikinSwingOn

# The first two sections carry nothing the C path drives (Comfort, and the
# clock that IRac never sets): they are sent as the header's reset state.
DAIKIN_ARC_FIRST = Layout(bytes.fromhex("11da2700c5000000"), {}, checksum=Sum8(0, 7, 7))
DAIKIN_ARC_SECOND = Layout(
    bytes.fromhex("11da270042000000"), {}, checksum=Sum8(0, 7, 7)
)
DAIKIN_ARC_THIRD = Layout(
    # Hardwired: byte 5 bit 3 (always 1), timers unused (kDaikinUnusedTime
    # in bytes 10-12), byte 15 = 0xC0.
    bytes.fromhex("11da27000008000000000006600000c0000000"),
    {
        "power": Field.at(5, 0, 1),
        "mode": Field.at(
            5, 4, 3, values={"auto": 0, "dry": 2, "cool": 3, "heat": 4, "fan": 6}
        ),
        "half_degrees": Field.at(6, 0, 8),  # Temp: °C × 2
        "swing_v": Field.at(8, 0, 4, values=DAIKIN_ARC_SWING),
        "fan": Field.at(8, 4, 4, values={"auto": 0xA, "1": 3, "2": 5, "3": 6}),
        "swing_h": Field.at(9, 0, 4, values=DAIKIN_ARC_SWING),
        "powerful": Field.at(13, 0, 1),
        "quiet": Field.at(13, 5, 1),
        "economy": Field.at(16, 2, 1),
        "mold": Field.at(17, 1, 1),
    },
    checksum=Sum8(0, 18, 18),
)


class DaikinArcDevice(Device):
    """Daikin (ARC433 and others): a full-state protocol, ``previous`` is
    ignored."""

    PROTOCOL = DAIKIN_ARC
    LAYOUTS = (None, DAIKIN_ARC_FIRST, DAIKIN_ARC_SECOND, DAIKIN_ARC_THIRD)
    capabilities = Capabilities(
        modes=("auto", "dry", "cool", "heat", "fan"),
        temperature=TemperatureRange(10.0, 32.0, (0, 5)),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
        ),
        swing_v=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
        swing_h=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
        features={
            name: Choice((False, True), {False: "off", True: "on"})
            for name in ("economy", "powerful", "quiet", "cleaning")
        },
    )

    def frames(self, previous, target, actions):
        feat = target.features
        third = DAIKIN_ARC_THIRD.build(
            power=target.power,
            # As the C path: an off message carries mode auto (IRac passes
            # mode "off", which convertMode maps to auto).
            mode=target.mode if target.power else "auto",
            half_degrees=int(target.temperature * 2),
            swing_v=target.swing_v,
            fan=target.fan,
            swing_h=target.swing_h,
            # As IRDaikinESP's setters, called in IRac's order (quiet,
            # powerful, econo): powerful cancels quiet, econo cancels powerful.
            quiet=feat["quiet"] and not feat["powerful"],
            powerful=feat["powerful"] and not feat["economy"],
            economy=feat["economy"],
            mold=feat["cleaning"],
        )
        return [
            Frame("leader", b"\x00", 5),
            Frame("main", bytes(DAIKIN_ARC_FIRST.build())),
            Frame("main", bytes(DAIKIN_ARC_SECOND.build())),
            Frame("main", bytes(third)),
        ]


DAIKIN_ARC_MODELS = (
    "ARC433 remote",
    "M Series",
    "FTXM-M",
    "ARC466A12 remote",
    "ARC466A33 remote",
    "Daikin",
)


DEVICES.update({m: DaikinArcDevice for m in DAIKIN_ARC_MODELS})


DEVICES.update({m: DaikinArcDevice for m in DAIKIN_ARC_MODELS})


class PluginObject(GenPluginObject):
    MODELS = {
        "generic": Daikinth,
        "smash 2": Smash2,  # Daikin
        "ARC433 remote": Daikin,
        "ARC477A1 remote": Daikin2,
        "FTXZ25NV1B": Daikin2,
        "FTXZ35NV1B": Daikin2,
        "FTXZ50NV1B": Daikin2,
        "ARC433B69 remote": Daikin216,
        "ARC423A5 remote": Daikin160,
        "FTE12HV2S": Daikin160,
        "BRC4C153 remote": Daikin176,
        "FFQ35B8V1B": Daikin176,
        "BRC4C151 remote": Daikin176,
        "17 Series FTXB09AXVJU": Daikin128,
        "17 Series FTXB12AXVJU": Daikin128,
        "17 Series FTXB24AXVJU": Daikin128,
        "BRC52B63 remote": Daikin128,
        "ARC480A5 remote": Daikin152,
        "FFN-C/FCN-F Series": Daikin64,
        "DGS01 remote": Daikin64,
        "M Series": Daikin,
        "FTXM-M": Daikin,
        "ARC466A12 remote": Daikin,
        "ARC466A33 remote": Daikin,
        "FTWX35AXV1": Daikin64,
        "ARC484A4 remote": Daikin216,
        "FTQ60TV16U2": Daikin216,
        # "BRC4M150W16 remote": Daikin200,
        "FTXM20R5V1B": Daikin312,
        "ARC466A67 remote": Daikin312,
        "Daikin": Daikin,
        "Daikin2": Daikin2,
        "Daikin64": Daikin64,
        "Daikin128": Daikin128,
        "Daikin152": Daikin152,
        "Daikin160": Daikin160,
        "Daikin176": Daikin176,
        "Daikin216": Daikin216,
        "Daikin312": Daikin312,
    }

    def __init__(self):
        self.brand = "daikin"


def main():

    import argparse
    import base64

    parser = argparse.ArgumentParser(description="Decode LIRC IR code into frames.")
    # version="%prog " + __version__ + "/" + bl.__version__)
    parser.add_argument(
        "-M",
        "--model",
        type=str,
        default="generic",
        help="Set the A/C model. (default generic).",
    )
    parser.add_argument(
        "-L",
        "--list",
        action="store_true",
        default=False,
        help="List known models and return.",
    )
    parser.add_argument(
        "-t", "--temp", type=int, default=25, help="Temperature (°C). (default 25)."
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=["cool", "dry", "fan", "off"],
        default="cool",
        help="Mode to set. (default 'cool').",
    )
    parser.add_argument(
        "-f",
        "--fan",
        choices=["auto", "highest", "high", "medium", "low", "lowest"],
        default="auto",
        help="Fan mode. (default 'auto').",
    )
    parser.add_argument(
        "-s", "--swing", action="store_true", default=False, help="Set swing"
    )
    parser.add_argument(
        "-p", "--powerful", action="store_true", default=False, help="Set powerful"
    )
    parser.add_argument(
        "-l",
        "--lirc",
        action="store_true",
        default=False,
        help="Output LIRC compatible timing",
    )
    parser.add_argument(
        "-b",
        "--broadlink",
        action="store_true",
        default=False,
        help="Output Broadlink timing",
    )
    parser.add_argument(
        "-B",
        "--base64",
        action="store_true",
        default=False,
        help="Output Broadlink timing in base64 encoded",
    )

    try:
        opts = parser.parse_args()
    except Exception as e:
        parser.error("Error: " + str(e))

    if opts.list:
        print(f"Available modelas are: {PluginObject().MODELS.keys()}")

    device = PluginObject().get_device(opts.model)

    frames = []
    device.set_temperature(opts.temp)
    device.set_fan(opts.fan)
    device.set_swing(opts.swing)
    device.set_powerful(opts.powerful)
    device.set_mode(opts.mode)

    frames = device.build_ircode()

    if opts.lirc:
        lircf = device.to_lirc(frames)
        while lircf:
            print("\t".join(["%d" % x for x in lircf[:6]]))
            lircf = lircf[6:]
    elif opts.broadlink or opts.base64:
        bframe = device.to_broadlink(frames)
        if opts.base64:
            print("{}".format(str(base64.b64encode(bframe), "ascii")))
        else:
            print("{}".format(bframe.hex()))
    else:
        for f in frames:
            print(" ".join([hex(x) for x in f]))


if __name__ == "__main__":
    main()
