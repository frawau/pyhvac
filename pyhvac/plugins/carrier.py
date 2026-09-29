#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Carrier AC IR commands.
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

from dataclasses import dataclass

from .hvaclib import PulseBased, GenPluginObject
from .toshiba import TOSHIBA_AC_CARRIER_MODELS, Toshiba, ToshibaAcDevice
from ..device import Device
from ..fields import Checksum, Field, Layout
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_3
from ..state import Capabilities, TemperatureRange


class Carrier(PulseBased):

    STARTFRAME = [8940, 4556]
    ENDFRAME = None
    MARK = [503]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [615, 1736]  # ditto

    def __init__(self):
        super().__init__("CARRIER_AC64")
        self.capabilities = {
            "mode": ["off", "cool", "fan", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
        }


DEVICES = {}


# ------------------------------------------------------------ CarrierAc64
# Layout from IRremoteESP8266's CarrierProtocol (ir_Carrier.h): one 64-bit
# word (kCarrierAc64Bits) sent LSB first by sendCarrierAC64, i.e. 8 bytes in
# order, each LSB first, with a kCarrierAc64HdrMark/HdrSpace header, a
# kCarrierAc64BitMark footer and kCarrierAc64Gap (kDefaultMessageGap) after
# it.

CARRIER_AC64 = Protocol(
    "carrier-ac64",
    {
        "main": Section(
            PulseDistance(503, 615, 1736),  # kCarrierAc64BitMark/Zero/OneSpace
            header=(8940, 4556),  # kCarrierAc64HdrMark/HdrSpace
            footer=(503,),
            gap=100000,  # kCarrierAc64Gap
        )
    },
    carrier=38000,  # kCarrierAcFreq
)


@dataclass(frozen=True)
class CarrierAc64Checksum(Checksum):
    """IRCarrierAc64::calcChecksum: the sum of every nibble above the
    checksum (bits kCarrierAc64ChecksumOffset + kCarrierAc64ChecksumSize
    to 63), i.e. the high nibble of data[at] and every nibble of
    data[start:end], mod 16, in the low nibble of data[at]
    (kCarrierAc64ChecksumOffset 16, kCarrierAc64ChecksumSize 4). The high
    nibble of data[at] holds fields."""

    def compute(self, data):
        total = sum((b >> 4) + (b & 0x0F) for b in self._input(data))
        return (total + (data[self.at] >> 4)) & 0x0F

    def bits(self):
        return set(range(8 * self.at, 8 * self.at + 4))

    def apply(self, data):
        data[self.at] = (data[self.at] & 0xF0) | self.compute(data)

    def check(self, data):
        return data[self.at] & 0x0F == self.compute(data)


CARRIER_AC64_MIN_TEMP, CARRIER_AC64_MAX_TEMP = 16, 30  # kCarrierAc64Min/MaxTemp

# Skeleton: IRCarrierAc64::stateReset (0x109000002C2A5584) with the fields
# IRac::carrier64 always writes and the sum cleared. It sets every bit, so
# there is no stale padding. The timers keep their reset values (OnTimer 9,
# OffTimer 1, both disabled): IRac never sets them, and setSleep(false)
# leaves them alone.
CARRIER_AC64_LAYOUT = Layout(
    bytes.fromhex("8455000000009010"),
    {
        "mode": Field.at(  # kCarrierAc64Heat/Cool/Fan
            2, 4, 2, values={"heat": 1, "cool": 2, "fan": 3}
        ),
        "fan": Field.at(  # kCarrierAc64FanAuto/Low/Medium/High
            2, 6, 2, values={"auto": 0, "1": 1, "2": 2, "3": 3}
        ),
        "temperature": Field.at(  # degrees - kCarrierAc64MinTemp
            3,
            0,
            4,
            values={
                t: t - CARRIER_AC64_MIN_TEMP
                for t in range(CARRIER_AC64_MIN_TEMP, CARRIER_AC64_MAX_TEMP + 1)
            },
        ),
        "swing_v": Field.at(3, 5, 1),
        "power": Field.at(4, 4, 1),
        "off_timer_enable": Field.at(4, 5, 1),
        "on_timer_enable": Field.at(4, 6, 1),
        "sleep": Field.at(4, 7, 1),
        "on_timer": Field.at(6, 4, 4),  # hours
        "off_timer": Field.at(7, 4, 4),  # hours
    },
    CarrierAc64Checksum(3, 8, 2),
)


class CarrierAc64Device(Device):
    """Carrier 64-bit (42QG5A55970 remote and others): power, mode, setpoint
    and fan, as IRac::carrier64 sends them from a fresh IRCarrierAc64.

    - An off message clears Power and carries kCarrierAc64Cool (IRac's "off"
      mode falls to convertMode's default), with the target's setpoint and
      fan.
    - The setpoint is sent in every mode, fan included.
    - SwingV and Sleep stay clear: the entity has neither, so IRac gets
      swingv kOff and sleep -1. The timers keep their reset values, disabled.

    Nothing here is a toggle, so ``previous`` is ignored. The C path follows
    the header throughout: no Defect is declared.
    """

    PROTOCOL = CARRIER_AC64
    LAYOUTS = (CARRIER_AC64_LAYOUT,)
    capabilities = Capabilities(
        modes=("cool", "fan", "heat"),
        temperature=TemperatureRange(
            float(CARRIER_AC64_MIN_TEMP), float(CARRIER_AC64_MAX_TEMP)
        ),
        fan=FAN_3,
    )

    def frames(self, previous, target, actions):
        data = CARRIER_AC64_LAYOUT.build(
            power=target.power,
            mode=target.mode if target.power else "cool",
            temperature=int(target.temperature),
            fan=target.fan,
            swing_v=0,
            sleep=0,
        )
        return [Frame("main", bytes(data))]


CARRIER_AC64_MODELS = (
    "42QG5A55970 remote",
    "619EGX0090E0",
    "619EGX0120E0",
    "619EGX0180E0",
    "619EGX0220E0",
    "53NGK009/012",
    "generic",
)


DEVICES.update({m: CarrierAc64Device for m in CARRIER_AC64_MODELS})
DEVICES.update({m: ToshibaAcDevice for m in TOSHIBA_AC_CARRIER_MODELS})


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "42QG5A55970 remote": Carrier,
        "619EGX0090E0": Carrier,
        "619EGX0120E0": Carrier,
        "619EGX0180E0": Carrier,
        "619EGX0220E0": Carrier,
        "53NGK009/012": Carrier,
        "generic": Carrier,
        "42NQV060M2 / 38NYV060M2": Toshiba,
        "42NQV050M2 / 38NYV050M2": Toshiba,
        "42NQV035M2 / 38NYV035M2": Toshiba,
        "42NQV025M2 / 38NYV025M2": Toshiba,
    }

    def __init__(self):
        self.brand = "carrier"
