#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Mitsubishi Heavy Industries AC IR commands.
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
from ..fields import Field, InvertedPairs, Layout
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import Capabilities, Choice, TemperatureRange


class Mitsubishi152(PulseBased):

    STARTFRAME = [3140, 1630]
    ENDFRAME = None
    MARK = [370]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [1220, 420]  # ditto

    def __init__(self):
        super().__init__("MITSUBISHI_HEAVY_152")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "fan", "heat"],
            "temperature": [17, 31],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": [
                "auto",
                "wide",
                "far right",
                "right",
                "middle",
                "left",
                "far left",
            ],
            "quiet": ["off", "on"],
            "sleep": ["off", "on"],
            "purifier": ["off", "on"],
            "cleaning": ["off", "on"],
            "powerful": ["off", "on"],
            "economy": ["off", "on"],
        }


class Mitsubishi88(PulseBased):

    STARTFRAME = [3140, 1630]
    ENDFRAME = None
    MARK = [370]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [1220, 420]  # ditto

    def __init__(self):
        super().__init__("MITSUBISHI_HEAVY_88")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat"],
            "temperature": [17, 31],
            "fan": ["highest", "medium", "low", "lowest"],
            "swing": ["off", "auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": [
                "off",
                "auto",
                "far right",
                "right",
                "middle",
                "left",
                "far left",
            ],
            "cleaning": ["off", "on"],
            "powerful": ["off", "on"],
            "economy": ["off", "on"],
        }


DEVICES = {}


# --------------------------------------------------------- MitsubishiHeavy152
# Layout from IRremoteESP8266's Mitsubishi152Protocol (ir_MitsubishiHeavy.h):
# 19 bytes, one frame sent LSB first (sendMitsubishiHeavy152 ->
# sendMitsubishiHeavy88: sendGeneric with MSBfirst false, 38 kHz). Bytes 0-4
# are kMitsubishiHeavyZmsSig; from byte 3 on every second byte is the
# complement of the one before it (IRMitsubishiHeavy152Ac::checksum:
# invertBytePairs(raw + 3, 16)), so every field sits in an odd byte.

MITSUBISHI_HEAVY152 = Protocol(
    "mitsubishi_heavy152",
    {
        "main": Section(
            # kMitsubishiHeavyBitMark / ZeroSpace / OneSpace
            PulseDistance(370, 1220, 420),
            header=(3140, 1630),  # kMitsubishiHeavyHdrMark / HdrSpace
            footer=(370,),
            gap=100000,  # kMitsubishiHeavyGap (kDefaultMessageGap)
        ),
    },
    carrier=38000,
)

MITSUBISHI_HEAVY152_MODE = {  # kMitsubishiHeavy{Auto,Cool,Dry,Fan,Heat}
    "auto": 0,
    "cool": 1,
    "dry": 2,
    "fan": 3,
    "heat": 4,
}
MITSUBISHI_HEAVY152_FAN = {  # kMitsubishiHeavy152Fan*
    "auto": 0x0,
    "low": 0x1,
    "med": 0x2,
    "high": 0x3,
    "max": 0x4,
    "econo": 0x6,
    "turbo": 0x8,
}
MITSUBISHI_HEAVY152_FAN_OF = {  # canonical fan -> code name, as convertFan
    "auto": "auto",
    "1": "econo",  # lowest: kMin -> kMitsubishiHeavy152FanEcono
    "2": "low",
    "3": "med",
    "4": "high",
    "5": "max",
}
MITSUBISHI_HEAVY152_SWING_V = {  # kMitsubishiHeavy152SwingV*
    "auto": 0,
    "highest": 1,
    "high": 2,
    "middle": 3,
    "low": 4,
    "lowest": 5,
    "off": 6,
}
MITSUBISHI_HEAVY152_SWING_V_OF = {  # canonical swing_v -> code name
    "off": "off",
    "auto": "auto",
    "1": "highest",  # 90°: the topmost documented position
    "2": "high",  # 60°
    "3": "middle",  # 45°
    "4": "low",  # 30°
    "5": "lowest",  # 0°
}
MITSUBISHI_HEAVY152_SWING_H = {  # kMitsubishiHeavy152SwingH*
    "auto": 0,
    "left_max": 1,
    "left": 2,
    "middle": 3,
    "right": 4,
    "right_max": 5,
    "right_left": 6,
    "left_right": 7,
    "off": 8,
}
MITSUBISHI_HEAVY152_SWING_H_OF = {  # canonical swing_h -> code name
    "auto": "auto",
    "1": "left_max",  # far left
    "2": "left",
    "3": "middle",
    "4": "right",
    "5": "right_max",  # far right
    # "wide": convertSwingH has no kWide case and falls back to SwingHOff;
    # the header documents no wide position.
    "6": "off",
}
MITSUBISHI_HEAVY152_MIN_TEMP = 17  # kMitsubishiHeavyMinTemp

# Skeleton: IRMitsubishiHeavy152Ac::stateReset (the signature, raw[17] =
# 0x80, every other odd byte 0), the complements left for the checksum.
MITSUBISHI_HEAVY152_LAYOUT = Layout(
    bytes.fromhex("ad513ce51a0000000000000000000000008000"),
    {
        "mode": Field.at(5, 0, 3, values=MITSUBISHI_HEAVY152_MODE),
        "power": Field.at(5, 3, 1),
        "clean": Field.at(5, 5, 1),
        "filter": Field.at(5, 6, 1),
        "temp": Field.at(7, 0, 4),  # °C - kMitsubishiHeavyMinTemp
        "fan": Field.at(9, 0, 4, values=MITSUBISHI_HEAVY152_FAN),
        "three": Field.at(11, 1, 1),  # 3D, with "d"
        "d": Field.at(11, 4, 1),
        "swing_v": Field.at(11, 5, 3, values=MITSUBISHI_HEAVY152_SWING_V),
        "swing_h": Field.at(13, 0, 4, values=MITSUBISHI_HEAVY152_SWING_H),
        "night": Field.at(15, 6, 1),
        "silent": Field.at(15, 7, 1),
    },
    checksum=InvertedPairs(3, 19),
)


class MitsubishiHeavy152Device(Device):
    """Mitsubishi Heavy 152-bit (RLA502A700B, SRKxxZM-S): a full-state
    protocol, ``previous`` is ignored (the struct has no toggle bits).

    As IRac::mitsubishiHeavy152 does: an off message carries mode auto
    (convertMode maps IRac's "off" to kMitsubishiHeavyAuto); powerful sets
    the fan to kMitsubishiHeavy152FanTurbo (setTurbo after setFan), and
    economy to kMitsubishiHeavy152FanEcono, which wins over turbo (setEcono
    comes last); cleaning sets Clean and purifier sets Filter (setClean
    writes both bits, then setFilter overwrites Filter); 3D is never set.

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_mitsubishi_heavy152_device.py):
    - fan lowest: convertFan gives kMitsubishiHeavy152FanEcono, but IRac's
      setEcono(false) then resets it to auto; the port sends Econo;
    - swing_v "1" (90°) and "2" (60°): the old glue maps them to kHigh and
      kUpperMiddle, which convertSwingV sends as High and Off; the port sends
      the documented Highest and High (positions counted from the top);
    - sleep: the old glue never passes sleep, so setNight(sleep >= 0) never
      sets Night; the port sets it.
    """

    PROTOCOL = MITSUBISHI_HEAVY152
    LAYOUTS = (MITSUBISHI_HEAVY152_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "fan", "heat"),
        temperature=TemperatureRange(17.0, 31.0),
        fan=Choice(
            ("auto", "1", "2", "3", "4", "5"),
            {
                "auto": "auto",
                "1": "lowest",
                "2": "low",
                "3": "medium",
                "4": "high",
                "5": "highest",
            },
        ),
        swing_v=Choice(
            ("off", "auto", "1", "2", "3", "4", "5"),
            {
                "off": "off",
                "auto": "auto",
                "1": "90°",
                "2": "60°",
                "3": "45°",
                "4": "30°",
                "5": "0°",
            },
        ),
        swing_h=Choice(
            ("auto", "1", "2", "3", "4", "5", "6"),
            {
                "auto": "auto",
                "1": "far left",
                "2": "left",
                "3": "middle",
                "4": "right",
                "5": "far right",
                "6": "wide",
            },
        ),
        features={
            name: Choice((False, True), {False: "off", True: "on"})
            for name in (
                "quiet",
                "sleep",
                "purifier",
                "cleaning",
                "powerful",
                "economy",
            )
        },
    )

    def frames(self, previous, target, actions):
        features = target.features
        fan = MITSUBISHI_HEAVY152_FAN_OF[target.fan]
        if features["powerful"]:
            fan = "turbo"
        if features["economy"]:
            fan = "econo"
        data = MITSUBISHI_HEAVY152_LAYOUT.build(
            mode=target.mode if target.power else "auto",
            power=target.power,
            clean=features["cleaning"],
            filter=features["purifier"],
            temp=int(target.temperature) - MITSUBISHI_HEAVY152_MIN_TEMP,
            fan=fan,
            three=0,
            d=0,
            swing_v=MITSUBISHI_HEAVY152_SWING_V_OF[target.swing_v],
            swing_h=MITSUBISHI_HEAVY152_SWING_H_OF[target.swing_h],
            night=features["sleep"],
            silent=features["quiet"],
        )
        return [Frame("main", bytes(data))]


MITSUBISHI_HEAVY152_MODELS = (
    "RLA502A700B remote",
    "SRKxxZM-S A/C",
    "SRKxxZMXA-S A/C",
    "gemeric",
    "gemeric 152",
)


DEVICES.update({m: MitsubishiHeavy152Device for m in MITSUBISHI_HEAVY152_MODELS})


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "RLA502A700B remote": Mitsubishi152,
        "SRKxxZM-S A/C": Mitsubishi152,
        "SRKxxZMXA-S A/C": Mitsubishi152,
        "RKX502A001C remote": Mitsubishi88,
        "SRKxxZJ-S A/C": Mitsubishi88,
        "gemeric": Mitsubishi152,
        "gemeric 152": Mitsubishi152,
        "generic 88": Mitsubishi88,
    }

    def __init__(self):
        self.brand = "mitsubishi heavy industries"
