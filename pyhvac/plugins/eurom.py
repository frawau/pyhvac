#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Eurom AC IR commands.
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
##

from .hvaclib import PulseBased, GenPluginObject
from ..device import Device
from ..fields import Field, Layout, NibbleSum
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_3_FIXED, ON_OFF, SWING
from ..state import Capabilities, TemperatureRange


class Eurom(PulseBased):

    STARTFRAME = [3257, 3187]
    ENDFRAME = None
    MARK = [454]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [355, 1162]  # ditto

    def __init__(self):
        super().__init__("EUROM")
        self.capabilities = {
            "mode": ["off", "cool", "heat", "fan", "dry"],
            "temperature": [16, 32],
            "fan": ["low", "medium", "high"],
            "swing": ["off", "on"],
            "sleep": ["off", "on"],
        }


# ------------------------------------------------------------------ Eurom
# Layout from IRremoteESP8266's EuromProtocol (ir_Eurom.h): one 12-byte frame
# (kEuromStateLength), sent MSB first by sendEurom's sendGeneric, with a
# kEuromHdrMark/HdrSpace header, a kEuromBitMark footer and kEuromSpaceGap.

EUROM = Protocol(
    "eurom",
    {
        "main": Section(
            PulseDistance(454, 355, 1162),  # kEuromBitMark/ZeroSpace/OneSpace
            header=(3257, 3187),  # kEuromHdrMark, kEuromHdrSpace
            footer=(454,),
            gap=50058,  # kEuromSpaceGap
            lsb_first=False,
        ),
    },
    carrier=38000,  # kEuromFreq
)

# Mode_Celsius (byte 2): the mode in the low nibble (kEuromCool, kEuromHeat,
# and the low nibbles of kEuromDehumidify/kEuromVentilate), the setpoint
# minus kEuromMinTempC in the high nibble, and kEuromMaxTempFlag (bit 3) with
# a zero nibble for kEuromMaxTempC.
EUROM_MODE = {"cool": 0x1, "heat": 0x4, "dry": 0x2, "fan": 0x3}
EUROM_MIN_TEMP = 16  # kEuromMinTempC
EUROM_MAX_TEMP = 32  # kEuromMaxTempC
# The high nibble of kEuromDehumidify (0x72) and kEuromVentilate (0x73):
# these modes carry no setpoint.
EUROM_NO_SETPOINT = 0x7


# Skeleton: the constants IREuromAc::stateReset writes (it writes every byte,
# so there is no stale memory): Sum1 0x18, Sum2 0x27, Sum3 0x00, Sum4 0x80
# and OffTimer's kEuromOffTimer base 0x80; fields and checksum cleared.
EUROM_LAYOUT = Layout(
    bytes.fromhex("182700000000008000800000"),
    {
        "mode": Field.at(2, 0, 3, values=EUROM_MODE),
        "max_temperature": Field.at(2, 3, 1),  # kEuromMaxTempFlag
        "temperature": Field.at(2, 4, 4),  # degrees - kEuromMinTempC
        "swing_v": Field.at(3, 6, 1, values={"off": 0, "swing": 1}),  # kEuromSwingOn
        "power": Field.at(3, 7, 1),  # kEuromPowerOn
        "fahrenheit": Field.at(4, 0, 8),  # kEuromFahrenheitEnabled + degrees F
        "on_timer": Field.at(5, 0, 6),  # BCD hours, up to kEuromTimerMax
        "sleep": Field.at(5, 6, 1),  # kEuromSleepEnabled
        "off_timer": Field.at(7, 0, 6),  # BCD hours over kEuromOffTimer
        "off_timer_enabled": Field.at(8, 7, 1),  # kEuromOffTimerEnabled
        "fan": Field.at(  # kEuromFan{Low,Med,High}
            10, 0, 8, values={"1": 0x10, "2": 0x20, "3": 0x40}
        ),
    },
    # IREuromAc::calcChecksum: the nibbles of bytes 1-10 minus those of Sum1
    # (0x18). Sum2 (0x27) has the same nibble sum as Sum1 and both are
    # constant, so this is the nibble sum of bytes 2-10.
    checksum=NibbleSum(2, 11, 11),
)


class EuromDevice(Device):
    """Eurom Polar 16CH: a full-state frame with a power bit and no toggle
    bits, so ``previous`` is ignored (IRac::handleToggles has no EUROM case).

    As IRac::eurom sends it:
    - an off message carries mode fan (IRac passes mode "off", which
      convertMode maps to kEuromVentilate) and no setpoint;
    - the setpoint goes out in cool and heat only, in Celsius (IRac passes
      fahrenheit = !celsius, false), so the Fahrenheit byte stays 0; 32 °C
      is sent as kEuromMaxTempFlag;
    - the timers are never set.

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_eurom_device.py):
    - swing: the old glue never passed swing "on"; the port sets SwingOn;
    - sleep: IRac::eurom takes sleep as a bool, so IRac's "off" (-1) arrives
      as true and every C message has kEuromSleepEnabled; the port sends
      kEuromSleepOnTimerDisabled for sleep off.
    """

    PROTOCOL = EUROM
    LAYOUTS = (EUROM_LAYOUT,)
    capabilities = Capabilities(
        modes=("cool", "heat", "fan", "dry"),
        temperature=TemperatureRange(16.0, 32.0),
        fan=FAN_3_FIXED,
        swing_v=SWING,
        features={"sleep": ON_OFF},
    )

    def frames(self, previous, target, actions):
        mode = target.mode if target.power else "fan"
        temperature = min(max(int(target.temperature), EUROM_MIN_TEMP), EUROM_MAX_TEMP)
        if mode not in ("cool", "heat"):
            nibble, max_flag = EUROM_NO_SETPOINT, 0
        elif temperature >= EUROM_MAX_TEMP:
            nibble, max_flag = 0, 1
        else:
            nibble, max_flag = temperature - EUROM_MIN_TEMP, 0
        data = EUROM_LAYOUT.build(
            mode=mode,
            max_temperature=max_flag,
            temperature=nibble,
            swing_v=target.swing_v,
            power=target.power,
            sleep=target.features.get("sleep", False),
            fan=target.fan,
        )
        return [Frame("main", bytes(data))]


EUROM_MODELS = ("Polar 16CH", "generic")


DEVICES = {}
DEVICES.update({m: EuromDevice for m in EUROM_MODELS})


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "Polar 16CH": Eurom,
        "generic": Eurom,
    }

    def __init__(self):
        self.brand = "eurom"
