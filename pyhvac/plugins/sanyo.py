#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Sanyo AC IR commands.
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
from ..fields import Field, Layout, NibbleSum
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import Capabilities, Choice, TemperatureRange


class Sanyo(PulseBased):

    STARTFRAME = [8500, 4200]
    MARK = [500]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [550, 1600]  # ditto

    def __init__(self):
        super().__init__("SANYO_AC")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["auto", "90°", "60°", "45°", "30°", "0°"],
            "sleep": ["off", "on"],
        }


class Sanyo88(PulseBased):

    STARTFRAME = [5400, 2000]
    MARK = [500]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [750, 1500]  # ditto
    TAIL = [500, 3675]

    def __init__(self):
        super().__init__("SANYO_AC88")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "heat", "fan"],
            "temperature": [10, 30],
            "fan": ["auto", "highest", "high", "medium", "lowest"],
            "swing": ["off", "on"],
            "powerful": ["off", "on"],
            "purifier": ["off", "on"],
            "sleep": ["off", "on"],
        }


DEVICES = {}


# ---------------------------------------------------------------- SanyoAc
# Layout from IRremoteESP8266's SanyoProtocol (ir_Sanyo.h): 9 bytes, one
# frame sent LSB first (sendSanyoAc -> sendGeneric with MSBfirst false, at
# kSanyoAcFreq), closed by the sum of every nibble of bytes 0-7
# (IRSanyoAc::calcChecksum: sumNibbles over length - 1 bytes).

SANYO_AC = Protocol(
    "sanyo_ac",
    {
        "main": Section(
            # kSanyoAcBitMark / ZeroSpace / OneSpace
            PulseDistance(500, 550, 1600),
            header=(8500, 4200),  # kSanyoAcHdrMark / HdrSpace
            footer=(500,),
            gap=100000,  # kSanyoAcGap (kDefaultMessageGap)
        ),
    },
    carrier=38000,  # kSanyoAcFreq
)

SANYO_AC_MODE = {  # kSanyoAc{Heat,Cool,Dry,Auto}
    "heat": 1,
    "cool": 2,
    "dry": 3,
    "auto": 4,
}
SANYO_AC_FAN = {  # canonical fan -> kSanyoAcFan*
    "auto": 0,  # kSanyoAcFanAuto
    "1": 2,  # low: kSanyoAcFanLow
    "2": 3,  # medium: kSanyoAcFanMedium
    "3": 1,  # high: kSanyoAcFanHigh
}
SANYO_AC_SWING_V = {  # canonical swing_v -> kSanyoAcSwingV*
    "auto": 0,  # kSanyoAcSwingVAuto
    "1": 7,  # 90°: kSanyoAcSwingVHighest (topmost, counting down)
    "2": 6,  # 60°: kSanyoAcSwingVHigh
    "3": 5,  # 45°: kSanyoAcSwingVUpperMiddle, as C
    "4": 3,  # 30°: kSanyoAcSwingVLow, as C
    "5": 2,  # 0°: kSanyoAcSwingVLowest, as C
}
SANYO_AC_POWER_OFF, SANYO_AC_POWER_ON = 0b01, 0b10  # kSanyoAcPowerOff / On
SANYO_AC_MIN_TEMP, SANYO_AC_MAX_TEMP = 16, 30  # kSanyoAcTempMin / Max
SANYO_AC_TEMP_DELTA = 4  # kSanyoAcTempDelta: native = degrees - 4

# Skeleton: IRSanyoAc::stateReset (kReset; memcpy writes all 9 bytes, so
# nothing comes from stale memory) with the named fields cleared. Byte 0 is
# the fixed 0x6A, byte 1 bits 5-7 stay 0b011 as in kReset and the issue
# #1211 capture (0x71).
SANYO_AC_LAYOUT = Layout(
    bytes.fromhex("6a6000000000000000"),
    {
        "temp": Field.at(1, 0, 5),  # °C - kSanyoAcTempDelta
        "sensor_temp": Field.at(2, 0, 5),  # °C - kSanyoAcTempDelta
        "sensor": Field.at(2, 5, 1),  # 0 = remote (wall), 1 = A/C (room)
        "beep": Field.at(2, 6, 1),
        "off_hour": Field.at(3, 0, 4),
        "fan": Field.at(4, 0, 2, values=SANYO_AC_FAN),
        "off_timer": Field.at(4, 2, 1),
        "mode": Field.at(4, 4, 3, values=SANYO_AC_MODE),
        "swing_v": Field.at(5, 0, 3, values=SANYO_AC_SWING_V),
        "power": Field.at(5, 6, 2),
        "sleep": Field.at(6, 3, 1),
    },
    checksum=NibbleSum(0, 8, 8),
)


class SanyoAcDevice(Device):
    """Sanyo 72-bit A/C (SAP-K121AHA, RCS-2HS4E, SAP-K242AH, RCS-2S4E): a
    full-state protocol with no toggle bits, ``previous`` is ignored.

    As the C path (IRac::sanyo, fed by the legacy glue): an off message
    carries mode auto (IRac passes mode "off", convertMode's default) and
    kSanyoAcPowerOff; the setpoint is whole degrees clamped to 16-30; the
    sensor temperature is the setpoint (IRac has no sensor reading and uses
    the desired temperature); the sensor is the A/C's own (setSensor(!iFeel),
    iFeel off); beep is off (the glue never sets it); the off timer is off.

    Two documented values differ from the C output (declared Defects):
    - swing_v "1" (90°) and "2" (60°): the old glue maps them to kHigh and
      kUpperMiddle, which convertSwingV sends as High and Auto; the port
      sends the documented Highest and High. 45°, 30° and 0° keep C's
      UpperMiddle, Low and Lowest (LowerMiddle is not reachable);
    - sleep: the old glue never passes sleep, so setSleep(sleep >= 0) never
      sets the Sleep bit; the port sets it.
    """

    PROTOCOL = SANYO_AC
    LAYOUTS = (SANYO_AC_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "heat"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
        ),
        swing_v=Choice(
            ("auto", "1", "2", "3", "4", "5"),
            {
                "auto": "auto",
                "1": "90°",
                "2": "60°",
                "3": "45°",
                "4": "30°",
                "5": "0°",
            },
        ),
        features={"sleep": Choice((False, True), {False: "off", True: "on"})},
    )

    def frames(self, previous, target, actions):
        degrees = min(
            max(int(target.temperature), SANYO_AC_MIN_TEMP), SANYO_AC_MAX_TEMP
        )
        native = degrees - SANYO_AC_TEMP_DELTA
        data = SANYO_AC_LAYOUT.build(
            temp=native,
            sensor_temp=native,
            sensor=1,
            beep=0,
            off_hour=0,
            fan=target.fan,
            off_timer=0,
            mode=target.mode if target.power else "auto",
            swing_v=target.swing_v,
            power=SANYO_AC_POWER_ON if target.power else SANYO_AC_POWER_OFF,
            sleep=target.features["sleep"],
        )
        return [Frame("main", bytes(data))]


SANYO_AC_MODELS = (
    "SAP-K121AHA",
    "RCS-2HS4E remote",
    "SAP-K242AH",
    "RCS-2S4E remote",
    "generic",
)


DEVICES.update({m: SanyoAcDevice for m in SANYO_AC_MODELS})


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "SAP-K121AHA": Sanyo,
        "RCS-2HS4E remote": Sanyo,
        "SAP-K242AH": Sanyo,
        "RCS-2S4E remote": Sanyo,
        "generic": Sanyo,
        "generic 88": Sanyo88,
    }

    def __init__(self):
        self.brand = "sanyo"
