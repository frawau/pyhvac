#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate DeLonghi AC IR commands.
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

from dataclasses import replace

from ..device import Device
from ..fields import Field, Layout, Sum8
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_3, ON_OFF
from ..state import Capabilities, TemperatureRange

# ------------------------------------------------------------------ DelonghiAc
# Layout from IRremoteESP8266's DelonghiProtocol (ir_Delonghi.h): one 64-bit
# word sent LSB first by sendDelonghiAc, i.e. 8 bytes in order, each LSB
# first, with a kDelonghiAcHdrMark/HdrSpace header, a kDelonghiAcBitMark
# footer and kDelonghiAcGap (kDefaultMessageGap) after it. Byte 7 is the sum
# of bytes 0-6 (IRDelonghiAc::calcChecksum).

DELONGHI_AC = Protocol(
    "delonghi_ac",
    {
        "main": Section(
            PulseDistance(572, 510, 1558),  # kDelonghiAcBitMark/Zero/OneSpace
            header=(8984, 4200),  # kDelonghiAcHdrMark/HdrSpace
            footer=(572,),
            gap=100000,  # kDelonghiAcGap
        )
    },
    carrier=38000,  # kDelonghiAcFreq
)

# Skeleton: stateReset's 0x5400000000000153 (header byte 0x53, Temp 1,
# cool, power off). stateReset writes the whole word, so no padding bit is
# stale.
DELONGHI_AC_LAYOUT = Layout(
    bytes.fromhex("5301000000000054"),
    {
        # degrees - kDelonghiAcTempMin{C,F} + 1, in the unit Fahrenheit names.
        "temperature": Field.at(1, 0, 5),
        # kDelonghiAcFan*: 0 auto, 1 high, 2 medium, 3 low.
        "fan": Field.at(1, 5, 2, values={"auto": 0, "3": 1, "2": 2, "1": 3}),
        "fahrenheit": Field.at(1, 7, 1),
        "power": Field.at(2, 0, 1),
        "mode": Field.at(  # kDelonghiAc{Cool,Dry,Fan,Auto}
            2, 1, 3, values={"cool": 0, "dry": 1, "fan": 2, "auto": 4}
        ),
        "boost": Field.at(2, 4, 1),
        "sleep": Field.at(2, 5, 1),
        "on_timer": Field.at(3, 0, 1),
        "on_hours": Field.at(3, 1, 5),
        "on_mins": Field.at(4, 0, 6),
        "off_timer": Field.at(5, 0, 1),
        "off_hours": Field.at(5, 1, 5),
        "off_mins": Field.at(6, 0, 6),
    },
    checksum=Sum8(0, 7, 7),
)

# The fan speed IRDelonghiAc::setFan leaves when asked for auto: fan mode
# can't have auto (it becomes high), every other mode keeps auto.
DELONGHI_AC_FAN = {"fan": "3"}
# setFan: "Auto & Dry modes only allows auto fan speed".
DELONGHI_AC_AUTO_FAN_MODES = ("auto", "dry")


def delonghi_ac_fan(mode, fan):
    """The fan IRDelonghiAc::setFan leaves in ``mode`` when asked for ``fan``."""
    if mode in DELONGHI_AC_AUTO_FAN_MODES:
        return "auto"
    if fan == "auto":
        return DELONGHI_AC_FAN.get(mode, "auto")
    return fan


class DelonghiAcDevice(Device):
    """DeLonghi PAC A95: power, mode, setpoint, fan, boost and sleep are
    sent in full.

    As IRac::delonghiac sends it:
    - an off message carries mode auto (convertMode's default for IRac's
      "off"), with the setpoint and boost;
    - the setpoint is sent in every mode: IRac calls setTemp after setMode,
      which overwrites the special temperatures setMode writes for auto, dry
      (kDelonghiAcTempAutoDryMode) and fan (kDelonghiAcTempFanMode). The
      range is kDelonghiAcTempMinC..MaxC (18-32 C);
    - the fan follows setFan's mode rules, which ``normalise`` applies to
      the target: auto and dry allow auto only; fan mode can't have auto
      and sends high for it (the stateReset fan is auto); an off message
      (mode auto) sends auto;
    - "powerful" is the Boost (Turbo) bit, "sleep" the Sleep bit;
    - Celsius and no timers.

    Quiet is not offered: the header has no quiet bit and IRac::delonghiac
    takes none.

    ``previous`` is ignored: the protocol has no toggle bits.
    """

    PROTOCOL = DELONGHI_AC
    LAYOUTS = (DELONGHI_AC_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "fan", "dry"),
        # kDelonghiAcTempMinC..kDelonghiAcTempMaxC
        temperature=TemperatureRange(18.0, 32.0),
        fan=FAN_3,  # kDelonghiAcFan{Auto,Low,Medium,High}
        features={"powerful": ON_OFF, "sleep": ON_OFF},  # Boost, Sleep
    )

    def normalise(self, state):
        state = super().normalise(state)
        fan = delonghi_ac_fan(state.mode, state.fan)
        return state if fan == state.fan else replace(state, fan=fan)

    def frames(self, previous, target, actions):
        mode = target.mode if target.power else "auto"
        data = DELONGHI_AC_LAYOUT.build(
            temperature=min(max(int(target.temperature), 18), 32) - 17,
            fan=delonghi_ac_fan(mode, target.fan),
            power=target.power,
            mode=mode,
            boost=target.features["powerful"],
            sleep=target.features.get("sleep", False),
        )
        return [Frame("main", bytes(data))]


DELONGHI_AC_MODELS = ("PAC A95", "generic")


# Now the match between models and objects
