#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Amcor AC IR commands.
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
# Description of the various ": Greev1, devices supported. Can be a remote control name

from .hvaclib import PulseBased, GenPluginObject
from ..device import Device
from ..fields import Field, Layout, NibbleSum
from ..ir.model import Frame, Protocol, PulseWidth, Section
from ..state import Capabilities, Choice, TemperatureRange


class Amcor(PulseBased):
    STARTFRAME = [8200, 4200]
    ENDFRAME = [1900, 10000]
    MARK = [600, 1500]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [1500, 600]  # ditto

    def __init__(self):
        super().__init__("AMCOR")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [12, 32],
            "fan": ["auto", "highest", "medium", "lowest"],
        }


DEVICES = {}


# ------------------------------------------------------------------ Amcor
# Layout from IRremoteESP8266's AmcorProtocol (ir_Amcor.h): 8 bytes sent LSB
# first (sendAmcor -> sendGeneric with MSBfirst false, 38 kHz), closed by the
# sum of every nibble of bytes 0-6 (IRAmcorAc::calcChecksum: sumNibbles over
# length - 1 bytes). A bit is a complementary pulse pair: a one is a
# 1 500 µs mark and a 600 µs space, a zero the reverse. IRAmcorAc::send sends
# kAmcorDefaultRepeat (kSingleRepeat) repeats: the frame goes out twice, each
# copy with its footer mark and gap.

AMCOR = Protocol(
    "amcor",
    {
        "main": Section(
            # kAmcorZeroMark / OneMark, kAmcorZeroSpace / OneSpace
            PulseWidth(600, 1500, 1500, one_space=600),
            header=(8200, 4200),  # kAmcorHdrMark / HdrSpace
            footer=(1900,),  # kAmcorFooterMark
            gap=34300,  # kAmcorGap
        ),
    },
    carrier=38000,
)

AMCOR_MODE = {  # kAmcor{Cool,Heat,Fan,Dry,Auto}
    "cool": 0b001,
    "heat": 0b010,
    "fan": 0b011,
    "dry": 0b100,
    "auto": 0b101,
}
AMCOR_FAN = {  # canonical fan -> kAmcorFan*, as convertFan
    "auto": 0b100,  # kAmcorFanAuto
    "1": 0b001,  # lowest (kMin): kAmcorFanMin
    "2": 0b010,  # medium: kAmcorFanMed
    "3": 0b011,  # highest (kMax): kAmcorFanMax
}
AMCOR_POWER_ON, AMCOR_POWER_OFF = 0b0011, 0b1100  # kAmcorPowerOn / Off
AMCOR_VENT_ON = 0b11  # kAmcorVentOn: set with mode fan (setMode)
AMCOR_MIN_TEMP, AMCOR_MAX_TEMP = 12, 32  # kAmcorMinTemp / MaxTemp

# Skeleton: IRAmcorAc::stateReset (byte 0 0x01, every other byte written
# as 0, so nothing comes from stale memory) with the named fields cleared.
AMCOR_LAYOUT = Layout(
    bytes.fromhex("0100000000000000"),
    {
        "mode": Field.at(1, 0, 3, values=AMCOR_MODE),
        "fan": Field.at(1, 4, 3, values=AMCOR_FAN),
        "temp": Field.at(2, 1, 6),  # whole °C
        "power": Field.at(5, 4, 4),
        "max": Field.at(6, 0, 2),  # kAmcorMax: cool at 12 / heat at 32
        "vent": Field.at(6, 6, 2),
    },
    checksum=NibbleSum(0, 7, 7),
)


class AmcorDevice(Device):
    """Amcor (ADR-853H, TAC-495, TAC-444): a full-state protocol with an
    explicit power nibble and no toggles, so ``previous`` is ignored. The
    frame is sent twice.

    As the C path (IRac::amcor, fed by the legacy glue): an off message
    carries kAmcorPowerOff and mode auto (IRac passes mode "off", which
    convertMode maps to kAmcorAuto), with the requested setpoint and fan;
    the Vent bits are set in mode fan only (setMode); the setpoint is whole
    degrees clamped to 12-32; Max stays off (IRac never calls setMax).
    Fan lowest and highest are kAmcorFanMin and kAmcorFanMax, as C sends.
    """

    PROTOCOL = AMCOR
    LAYOUTS = (AMCOR_LAYOUT, AMCOR_LAYOUT)
    capabilities = Capabilities(
        modes=("auto", "cool", "fan", "dry", "heat"),
        temperature=TemperatureRange(12.0, 32.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "lowest", "2": "medium", "3": "highest"},
        ),
    )

    def frames(self, previous, target, actions):
        mode = target.mode if target.power else "auto"
        data = bytes(
            AMCOR_LAYOUT.build(
                mode=mode,
                fan=target.fan,
                temp=min(max(int(target.temperature), AMCOR_MIN_TEMP), AMCOR_MAX_TEMP),
                power=AMCOR_POWER_ON if target.power else AMCOR_POWER_OFF,
                max=0,
                vent=AMCOR_VENT_ON if mode == "fan" else 0,
            )
        )
        return [Frame("main", data)] * 2


AMCOR_MODELS = ("ADR-853H", "TAC-495 remote", "TAC-444 remote", "generic")


DEVICES.update({m: AmcorDevice for m in AMCOR_MODELS})


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        # Amcor
        "ADR-853H": Amcor,
        "TAC-495 remote": Amcor,
        "TAC-444 remote": Amcor,
        "generic": Amcor,
    }

    def __init__(self):
        self.brand = "amcor"
