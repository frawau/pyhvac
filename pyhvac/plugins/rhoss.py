#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Rhoss AC IR commands.
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
from ..choices import SWING
from ..device import Device
from ..fields import Field, Layout, Sum8
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import Capabilities, Choice, TemperatureRange


class Rhoss(PulseBased):

    STARTFRAME = [3042, 4248]
    ENDFRAME = None
    MARK = [648]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [457, 1545]  # ditto

    def __init__(self):
        super().__init__("RHOSS")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "highest", "medium", "lowest"],
            "swing": ["off", "on"],
        }


# ------------------------------------------------------------------ Rhoss
# Layout from IRremoteESP8266's RhossProtocol (ir_Rhoss.h): one 12-byte frame
# (kRhossStateLength), each byte LSB first, at 38 kHz (kRhossFreq). sendRhoss
# closes sendGeneric's bit-mark footer and kRhossZeroSpace with one more
# kRhossBitMark, then kRhossGap (kDefaultMessageGap).

RHOSS = Protocol(
    "rhoss",
    {
        "main": Section(
            PulseDistance(648, 457, 1545),  # kRhossBitMark/ZeroSpace/OneSpace
            header=(3042, 4248),  # kRhossHdrMark, kRhossHdrSpace
            # sendGeneric's footer (kRhossBitMark, kRhossZeroSpace), then
            # sendRhoss's extra mark(kRhossBitMark).
            footer=(648, 457, 648),
            gap=100000,  # kRhossGap
        ),
    },
    carrier=38000,  # kRhossFreq
)

RHOSS_MIN_TEMP = 16  # kRhossTempMin
RHOSS_MAX_TEMP = 30  # kRhossTempMax
RHOSS_MODE = {"heat": 1, "cool": 2, "dry": 3, "fan": 4, "auto": 5}  # kRhossMode*
RHOSS_FAN = {"auto": 0, "1": 1, "2": 2, "3": 3}  # kRhossFanAuto/Min/Med/Max
RHOSS_POWER = {False: 1, True: 2}  # kRhossPowerOff, kRhossPowerOn
RHOSS_SWING_V = {"off": 0, "swing": 1}  # kRhossSwingOff, kRhossSwingOn

# Skeleton: IRRhossAc::stateReset (every byte written, so no stale memory):
# 0xAA, Temp 21 (kRhossDefaultTemp), 0x60, Mode cool, 0x54, Power 0 (the
# bool kRhossDefaultPower, neither documented code), the sum cleared.
RHOSS_LAYOUT = Layout(
    bytes.fromhex("aa0560002000540000000000"),
    {
        "temperature": Field.at(  # whole degrees minus kRhossTempMin
            1,
            0,
            4,
            values={
                t: t - RHOSS_MIN_TEMP for t in range(RHOSS_MIN_TEMP, RHOSS_MAX_TEMP + 1)
            },
        ),
        "fan": Field.at(4, 0, 2, values=RHOSS_FAN),
        "mode": Field.at(4, 4, 4, values=RHOSS_MODE),
        "swing_v": Field.at(5, 0, 1, values=RHOSS_SWING_V),
        "power": Field.at(5, 6, 2, values=RHOSS_POWER),
    },
    checksum=Sum8(0, 11, 11),  # IRRhossAc::calcChecksum: bytes 0-10
)


class RhossDevice(Device):
    """Rhoss Idrowall MPCV: a full-state frame with a power field and a
    SwingV bit, no toggle bits, so ``previous`` is ignored (IRac::handleToggles
    has no RHOSS case either).

    As IRac::rhoss sends it:
    - fan lowest/medium/highest are kRhossFanMin/Med/Max (convertFan of
      kMin/kMedium/kMax), with nothing resetting them;
    - an off message carries mode cool: convertMode maps IRac's mode "off" to
      kRhossDefaultMode (kRhossModeCool), with the requested setpoint, fan
      and swing;
    - the setpoint is sent in every mode, in whole degrees from 16 to 30.

    Where the C path differs, the port sends the documented value (see the
    Defect in tests/test_rhoss_device.py): swing "on" sets the SwingV bit.
    """

    PROTOCOL = RHOSS
    LAYOUTS = (RHOSS_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "heat", "fan"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "lowest", "2": "medium", "3": "highest"},
        ),
        swing_v=SWING,
    )

    def frames(self, previous, target, actions):
        temperature = min(max(int(target.temperature), RHOSS_MIN_TEMP), RHOSS_MAX_TEMP)
        data = RHOSS_LAYOUT.build(
            temperature=temperature,
            fan=target.fan,
            mode=target.mode if target.power else "cool",
            # IRac::rhoss: setSwing(swing != kOff). The old glue never passed
            # swing "on"; the port sends the documented bit.
            swing_v=target.swing_v,
            power=target.power,
        )
        return [Frame("main", bytes(data))]


RHOSS_MODELS = ("Idrowall MPCV", "generic")


DEVICES = {}
DEVICES.update({m: RhossDevice for m in RHOSS_MODELS})


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "Idrowall MPCV": Rhoss,
        "generic": Rhoss,
    }

    def __init__(self):
        self.brand = "rhoss"
