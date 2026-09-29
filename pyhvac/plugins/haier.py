#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Haier AC IR commands.
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
from ..fields import Field, Layout, Sum8
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import Capabilities, Choice, TemperatureRange

try:
    from ..irhvac import V9014557_A, V9014557_B
except ImportError:
    # Only the C-backed classes use these; keep the ported ones importable.
    V9014557_A = V9014557_B = None


class Haier(PulseBased):

    STARTFRAME = [3000, 4300]
    ENDFRAME = None
    MARK = [520]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [650, 1650]  # ditto

    def __init__(self):
        super().__init__("HAIER_AC")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto high", "auto low"],
            "purifier": ["off", "on"],
            "sleep": ["off", "on"],
        }


class Haier176A(PulseBased):

    STARTFRAME = [3000, 4300]
    ENDFRAME = None
    MARK = [520]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [650, 1650]  # ditto

    def __init__(self):
        super().__init__("HAIER_AC176", variant=V9014557_A)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto", "ceiling", "45°", "30°", "0°"],
            "hswing": ["auto", "far right", "right", "middle", "left", "far left"],
            "purifier": ["off", "on"],
            "sleep": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
        }


class Haier176B(PulseBased):

    STARTFRAME = [3000, 4300]
    ENDFRAME = None
    MARK = [520]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [650, 1650]  # ditto

    def __init__(self):
        super().__init__("HAIER_AC176", variant=V9014557_B)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto", "ceiling", "45°", "30°", "0°"],
            "hswing": ["auto", "far right", "right", "middle", "left", "far left"],
            "purifier": ["off", "on"],
            "sleep": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
        }


class HaierYRW02A(PulseBased):

    STARTFRAME = [3000, 4300]
    ENDFRAME = None
    MARK = [520]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [650, 1650]  # ditto

    def __init__(self):
        super().__init__("HAIER_AC_YRW02", variant=V9014557_A)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto", "ceiling", "45°", "30°", "0°"],
            "hswing": ["auto", "far right", "right", "middle", "left", "far left"],
            "purifier": ["off", "on"],
            "sleep": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
        }


class HaierYRW02B(PulseBased):

    STARTFRAME = [3000, 4300]
    ENDFRAME = None
    MARK = [520]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [650, 1650]  # ditto

    def __init__(self):
        super().__init__("HAIER_AC_YRW02", variant=V9014557_B)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto", "ceiling", "45°", "30°", "0°"],
            "hswing": ["auto", "far right", "right", "middle", "left", "far left"],
            "purifier": ["off", "on"],
            "sleep": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
        }


class Haier160(PulseBased):

    STARTFRAME = [3000, 4300]
    ENDFRAME = None
    MARK = [520]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [650, 1650]  # ditto

    def __init__(self):
        super().__init__("HAIER_AC160")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto", "ceiling", "90°", "45°", "30°", "0°"],
            "purifier": ["off", "on"],
            "sleep": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
            "cleaning": ["off", "on"],
            "light": ["off", "on"],
        }


DEVICES = {}


# ---------------------------------------------------------------- HaierAc
# Layout from IRremoteESP8266's HaierProtocol (ir_Haier.h): one 9-byte frame
# (kHaierACStateLength), sent MSB first. IRsend::sendHaierAC opens with a
# kHaierAcHdr mark and space before sendGeneric's kHaierAcHdr/kHaierAcHdrGap
# header, so the section header holds both pairs.

HAIER_AC = Protocol(
    "haier-ac",
    {
        "main": Section(
            PulseDistance(520, 650, 1650),  # kHaierAcBitMark/ZeroSpace/OneSpace
            header=(3000, 3000, 3000, 4300),  # kHaierAcHdr x3, kHaierAcHdrGap
            footer=(520,),
            gap=150000,  # kHaierAcMinGap
            lsb_first=False,
        ),
    },
    carrier=38000,  # sendHaierAC's enableIROut(38000)
)

HAIER_AC_COMMAND = {  # kHaierAcCmd*: the button the frame says was pressed
    "off": 0b0000,
    "on": 0b0001,
    "mode": 0b0010,
    "fan": 0b0011,
    "temp_up": 0b0110,
    "temp_down": 0b0111,
    "sleep": 0b1000,
    "timer_set": 0b1001,
    "timer_cancel": 0b1010,
    "health": 0b1100,
    "swing": 0b1101,
}
HAIER_AC_MODE = {  # kHaierAc{Auto,Cool,Dry,Heat,Fan}
    "auto": 0,
    "cool": 1,
    "dry": 2,
    "heat": 3,
    "fan": 4,
}
HAIER_AC_FAN = {  # canonical fan -> the raw Fan value IRHaierAC::setFan stores
    "auto": 0,  # kHaierAcFanAuto
    "1": 3,  # kHaierAcFanLow (kLow)
    "2": 2,  # kHaierAcFanMed (kMedium)
    "3": 1,  # kHaierAcFanHigh (kHigh)
}
HAIER_AC_SWING_V = {  # kHaierAcSwingV*, as IRHaierAC::convertSwingV
    "off": 0b00,  # Off (kOff)
    "1": 0b01,  # Up ("auto high" = kHigh)
    "2": 0b10,  # Down ("auto low" = kLow)
    "change": 0b11,  # Chg (kAuto): not offered by the entity
}
HAIER_AC_MIN_TEMP = 16  # kHaierAcMinTemp
HAIER_AC_MAX_TEMP = 30  # kHaierAcMaxTemp

# Skeleton: IRHaierAC::stateReset (memset 0, so no stale bytes) with the
# fields the device always writes (Command, Temp, Fan) and the sum cleared:
# Prefix kHaierAcPrefix, the constant "unknown" bit (byte 2 bit 5) and
# OffHours 12 stay.
HAIER_AC_LAYOUT = Layout(
    bytes.fromhex("a50020000c00000000"),
    {
        "command": Field.at(1, 0, 4, values=HAIER_AC_COMMAND),
        "temperature": Field.at(  # whole °C, minus kHaierAcMinTemp
            1,
            4,
            4,
            values={
                t: t - HAIER_AC_MIN_TEMP
                for t in range(HAIER_AC_MIN_TEMP, HAIER_AC_MAX_TEMP + 1)
            },
        ),
        "curr_hours": Field.at(2, 0, 5),
        "swing_v": Field.at(2, 6, 2, values=HAIER_AC_SWING_V),
        "curr_mins": Field.at(3, 0, 6),
        "off_timer": Field.at(3, 6, 1),
        "on_timer": Field.at(3, 7, 1),
        "off_hours": Field.at(4, 0, 5),
        "health": Field.at(4, 5, 1),
        "off_mins": Field.at(5, 0, 6),
        "fan": Field.at(5, 6, 2, values=HAIER_AC_FAN),
        "on_hours": Field.at(6, 0, 5),
        "mode": Field.at(6, 5, 3, values=HAIER_AC_MODE),
        "on_mins": Field.at(7, 0, 6),
        "sleep": Field.at(7, 6, 1),  # kHaierAcSleepBit
    },
    checksum=Sum8(0, 8, 8),  # IRHaierAC::checksum: sumBytes of bytes 0-7
)


class HaierAcDevice(Device):
    """Haier HSU07-HEA03: a full-state frame that also names a button
    (Command), and ``previous`` is ignored.

    The C path always sends kHaierAcCmdOn or kHaierAcCmdOff: IRac::haier ends
    with setCommand(on ? On : Off), overwriting the Mode/TempUp/TempDown/Fan/
    Swing/Health/Sleep commands its earlier setters wrote, and
    IRac::handleToggles has no HAIER_AC case. So C never picks the button
    from a previous state, and neither does the port. The real remote names
    the key actually pressed (the issue #404/#668 captures carry TempUp,
    TempDown and Health); the port does not invent that rule.
    """

    PROTOCOL = HAIER_AC
    LAYOUTS = (HAIER_AC_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "heat", "fan"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
        ),
        swing_v=Choice(
            ("off", "1", "2"), {"off": "off", "1": "auto high", "2": "auto low"}
        ),
        features={
            "purifier": Choice((False, True), {False: "off", True: "on"}),
            "sleep": Choice((False, True), {False: "off", True: "on"}),
        },
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to kHaierAcAuto).
        mode = target.mode if target.power else "auto"
        temperature = min(
            max(int(target.temperature), HAIER_AC_MIN_TEMP), HAIER_AC_MAX_TEMP
        )
        data = HAIER_AC_LAYOUT.build(
            command="on" if target.power else "off",
            temperature=temperature,
            swing_v=target.swing_v,
            health=target.features.get("purifier", False),  # IRac's filter
            fan=target.fan,
            mode=mode,
            # IRac::haier: setSleep(sleep >= 0). The old glue never passed
            # sleep; the port sends the documented bit (see the tests).
            sleep=target.features.get("sleep", False),
        )
        return [Frame("main", bytes(data))]


HAIER_AC_MODELS = ("HSU07-HEA03 remote", "generic")


DEVICES.update({m: HaierAcDevice for m in HAIER_AC_MODELS})


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "HSU07-HEA03 remote": Haier,
        "YR-W02 remote": HaierYRW02A,
        "HSU-09HMC203": HaierYRW02A,
        "V9014557 M47 8D remote": Haier176A,
        "Daichi D-H": Haier176A,
        "KFR-26GW/83@UI-Ge": Haier160,
        "generic": Haier,
        "YR-W02 Code A": HaierYRW02A,
        "YR-W02 Code B": HaierYRW02B,
        "generic 176 code a": Haier176A,
        "generic 176 code b": Haier176B,
        "generic 160": Haier160,
    }

    def __init__(self):
        self.brand = "haier"
