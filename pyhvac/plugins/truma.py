#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Truma AC IR commands.
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
from ..ir.model import Frame, Protocol, PulseWidth, Section
from ..choices import ON_OFF
from ..state import Capabilities, Choice, TemperatureRange


class Truma(PulseBased):
    LEAD = [20200, 1000]
    STARTFRAME = [1800, 630]
    MARK = [1200, 600]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [630]  # ditto
    TAIL = [500, 100000]

    def __init__(self):
        super().__init__("TRUMA")
        self.capabilities = {
            "mode": ["auto", "cool", "fan"],
            "temperature": [16, 31],
            "fan": ["high", "medium", "low"],
            "quiet": ["off", "on"],
        }


DEVICES = {}


# ------------------------------------------------------------------ Truma
# Layout from IRremoteESP8266's TrumaProtocol (ir_Truma.h): one 56-bit word
# (kTrumaBits) sent LSB first by sendTruma, i.e. 7 bytes in order, each LSB
# first. The mark carries the bit (kTrumaOneMark 600, kTrumaZeroMark 1200,
# kTrumaSpace 630). A leader (kTrumaLdrMark/LdrSpace) precedes the
# kTrumaHdrMark/kTrumaSpace header; a kTrumaFooterMark footer and kTrumaGap
# (kDefaultMessageGap) follow.

TRUMA = Protocol(
    "truma",
    {
        "main": Section(
            PulseWidth(1200, 600, 630),  # kTrumaZeroMark/OneMark/Space
            header=(20200, 1000, 1800, 630),  # leader, then kTrumaHdrMark/Space
            footer=(600,),  # kTrumaFooterMark
            gap=100000,  # kTrumaGap
        )
    },
    carrier=38000,  # enableIROut(38000)
)


@dataclass(frozen=True)
class TrumaChecksum(Sum8):
    """IRTrumaAc::calcChecksum: kTrumaChecksumInit (5) plus the sum of
    data[start:end]."""

    def compute(self, data):
        return (5 + super().compute(data)) & 0xFF


# Skeleton: kTrumaDefaultState (0x50FFFFFFE6E781) with the written fields
# and the sum cleared: byte 0 is 0x81, the top bits of bytes 1 (0b11) and 2
# (0b111) are set, bytes 3-5 are 0xFF.
TRUMA_LAYOUT = Layout(
    bytes.fromhex("81c0e0ffffff00"),
    {
        "mode": Field.at(1, 0, 2, values={"auto": 0, "cool": 2, "fan": 3}),
        "power_off": Field.at(1, 2, 1),  # PowerOff
        "fan": Field.at(  # kTrumaFan{Low,Med,High,Quiet}
            1, 3, 3, values={"1": 6, "2": 5, "3": 4, "quiet": 3}
        ),
        "temperature": Field.at(  # degrees - kTrumaTempOffset
            2, 0, 5, values={t: t - 10 for t in range(16, 32)}
        ),
    },
    TrumaChecksum(0, 6, 6),
)


class TrumaDevice(Device):
    """Truma Aventa: the power, mode, setpoint and fan are sent in full;
    quiet is a fan code.

    As IRac::truma sends it:
    - quiet replaces the fan speed with kTrumaFanQuiet in cool only
      (IRTrumaAc::setQuiet: "Quiet is only available in Cool mode"); in auto
      and fan mode, and in off messages, the fan speed is sent;
    - an off message sets PowerOff and carries mode fan (IRTrumaAc::setPower:
      "Off temporarily sets mode to Fan"), as the real off capture
      0x50FFFFFFE6E781 in ir_Truma_test.cpp does, with the target setpoint
      and fan speed.

    ``previous`` is ignored: the protocol has no toggle bits, and IRac builds
    a fresh IRTrumaAc for every message.
    """

    PROTOCOL = TRUMA
    LAYOUTS = (TRUMA_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "fan"),
        temperature=TemperatureRange(16.0, 31.0),
        fan=Choice(("1", "2", "3"), {"1": "low", "2": "medium", "3": "high"}),
        features={"quiet": ON_OFF},
    )

    def frames(self, previous, target, actions):
        power = target.power
        quiet = power and target.mode == "cool" and target.features["quiet"]
        data = TRUMA_LAYOUT.build(
            mode=target.mode if power else "fan",
            power_off=not power,
            fan="quiet" if quiet else target.fan,
            temperature=int(target.temperature),
        )
        return [Frame("main", bytes(data))]


TRUMA_MODELS = ("Aventa", "40091-86700 remote", "generic")


DEVICES.update({m: TrumaDevice for m in TRUMA_MODELS})


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "Aventa": Truma,
        "40091-86700 remote": Truma,
        "generic": Truma,
    }

    def __init__(self):
        self.brand = "truma"
