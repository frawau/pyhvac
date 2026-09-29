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


# ---------------------------------------------------- MitsubishiHeavy88
# Layout from IRremoteESP8266's Mitsubishi88Protocol (ir_MitsubishiHeavy.h):
# 11 bytes sent LSB first in one frame (sendMitsubishiHeavy88: sendGeneric
# with MSBfirst false). Bytes 0-4 are kMitsubishiHeavyZjsSig; from byte 3 on,
# every second byte is the complement of the one before it
# (IRMitsubishiHeavy88Ac::checksum, invertBytePairs from byte 3). stateReset
# zeroes bytes 5-10, so no bit is left to stale memory. The vertical and
# horizontal swing codes are split across the struct (SwingV5/SwingV7,
# SwingH1/SwingH2).

MITSUBISHI_HEAVY88 = Protocol(
    "mitsubishi-heavy88",
    {
        "main": Section(
            # kMitsubishiHeavyBitMark/ZeroSpace/OneSpace: a one is the short space
            PulseDistance(370, 1220, 420),
            header=(3140, 1630),  # kMitsubishiHeavyHdrMark/HdrSpace
            footer=(370,),
            gap=100000,  # kMitsubishiHeavyGap = kDefaultMessageGap
        ),
    },
    carrier=38000,  # sendMitsubishiHeavy88: 38 kHz
)


MITSUBISHI_HEAVY88_MODE = {  # kMitsubishiHeavy{Auto,Cool,Dry,Heat}
    "auto": 0,
    "cool": 1,
    "dry": 2,
    "heat": 4,
}
MITSUBISHI_HEAVY88_FAN = {  # canonical fan -> kMitsubishiHeavy88Fan*, as convertFan
    "auto": 0,  # Auto: not in the entity; what C falls back to (see the device)
    "1": 7,  # lowest (kMin): Econo
    "2": 2,  # Low
    "3": 3,  # Med
    "4": 6,  # highest (kMax): Turbo
}
MITSUBISHI_HEAVY88_SWING_V = {  # canonical -> kMitsubishiHeavy88SwingV*
    "off": 0b000,
    "auto": 0b100,
    "1": 0b110,  # Highest
    "2": 0b001,  # High
    "3": 0b011,  # Middle
    "4": 0b101,  # Low
    "5": 0b111,  # Lowest
}
MITSUBISHI_HEAVY88_SWING_H = {  # canonical -> kMitsubishiHeavy88SwingH*
    "off": 0b0000,
    "auto": 0b1000,
    "1": 0b0001,  # LeftMax
    "2": 0b0101,  # Left
    "3": 0b1001,  # Middle
    "4": 0b1101,  # Right
    "5": 0b0010,  # RightMax
}
MITSUBISHI_HEAVY88_MIN_TEMP = 17  # kMitsubishiHeavyMinTemp

# Skeleton: IRMitsubishiHeavy88Ac::stateReset (signature, then zeroes) with
# the inverted bytes filled in.
MITSUBISHI_HEAVY88_LAYOUT = Layout(
    bytes.fromhex("ad513cd92600ff00ff00ff"),
    {
        "swing_v": Field.over(
            (5, 1), (7, 3), (7, 4), values=MITSUBISHI_HEAVY88_SWING_V
        ),
        "swing_h": Field.over(
            (5, 2), (5, 3), (5, 6), (5, 7), values=MITSUBISHI_HEAVY88_SWING_H
        ),
        "clean": Field.at(5, 5, 1),
        "fan": Field.at(7, 5, 3, values=MITSUBISHI_HEAVY88_FAN),
        "mode": Field.at(9, 0, 3, values=MITSUBISHI_HEAVY88_MODE),
        "power": Field.at(9, 3, 1),
        "temperature": Field.at(9, 4, 4),  # whole °C - kMitsubishiHeavyMinTemp
    },
    checksum=InvertedPairs(3, 11),
)


class MitsubishiHeavy88Device(Device):
    """Mitsubishi Heavy 88-bit (RKX502A001C): a full-state protocol with an
    explicit power bit and no toggles, so ``previous`` is ignored.

    Powerful and economy are fan codes (Turbo, Econo), not separate bits:
    as IRac::mitsubishiHeavy88 calls setFan, then setTurbo, then setEcono,
    powerful overrides the fan speed and economy overrides both.

    Fan lowest and highest send the documented Econo and Turbo codes that
    convertFan maps them to. The C path sends auto instead: IRac's
    setTurbo(false) / setEcono(false) reset a Turbo / Econo fan to auto.
    Vertical swing positions count down from the topmost documented one
    (Highest); the C path sends High for "90°" and Off for "60°"
    (kUpperMiddle has no case in convertSwingV).
    """

    PROTOCOL = MITSUBISHI_HEAVY88
    LAYOUTS = (MITSUBISHI_HEAVY88_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "heat"),
        temperature=TemperatureRange(17.0, 31.0),
        fan=Choice(
            ("1", "2", "3", "4"),
            {"1": "lowest", "2": "low", "3": "medium", "4": "highest"},
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
            ("off", "auto", "1", "2", "3", "4", "5"),
            {
                "off": "off",
                "auto": "auto",
                "1": "far left",
                "2": "left",
                "3": "middle",
                "4": "right",
                "5": "far right",
            },
        ),
        features={
            "cleaning": Choice((False, True), {False: "off", True: "on"}),
            "powerful": Choice((False, True), {False: "off", True: "on"}),
            "economy": Choice((False, True), {False: "off", True: "on"}),
        },
    )

    def frames(self, previous, target, actions):
        # setTurbo(true) stores the Turbo fan code ("4"), then setEcono(true)
        # the Econo code ("1"), whatever the requested speed.
        fan = target.fan
        if target.features["powerful"]:
            fan = "4"
        if target.features["economy"]:
            fan = "1"
        data = MITSUBISHI_HEAVY88_LAYOUT.build(
            power=target.power,
            # As the C path: an off message carries mode auto (IRac passes
            # mode "off", which convertMode maps to kMitsubishiHeavyAuto).
            mode=target.mode if target.power else "auto",
            # setTemp clamps to 17-31 and stores the offset from 17.
            temperature=int(target.temperature) - MITSUBISHI_HEAVY88_MIN_TEMP,
            fan=fan,
            swing_v=target.swing_v,
            swing_h=target.swing_h,
            clean=target.features["cleaning"],
        )
        return [Frame("main", bytes(data))]


MITSUBISHI_HEAVY88_MODELS = ("RKX502A001C remote", "SRKxxZJ-S A/C", "generic 88")


DEVICES.update({m: MitsubishiHeavy88Device for m in MITSUBISHI_HEAVY88_MODELS})


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
