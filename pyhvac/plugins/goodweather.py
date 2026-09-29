#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate GoodWeather AC IR commands.
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
from ..choices import FAN_3, ON_OFF
from ..device import Device
from ..fields import Field, InvertedPairs, Layout
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import Capabilities, Choice, TemperatureRange


class Goodweather(PulseBased):

    STARTFRAME = [6820, 6820]
    ENDFRAME = None
    MARK = [580]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [1860, 580]  # ditto

    def __init__(self):
        super().__init__("GOODWEATHER")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [16, 31],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto low", "auto high"],
            "powerful": ["off", "on"],
            "light": ["off", "on"],
            "quiet": ["off", "on"],
        }


DEVICES = {}


# ------------------------------------------------------------ Goodweather
# Layout from IRremoteESP8266's GoodweatherProtocol (ir_Goodweather.h): a
# 48-bit state (kGoodweatherBits), sent by sendGoodweather one byte at a
# time, LSB first, each byte followed by its complement. The frame holds the
# 12 bytes on the wire: struct byte k is frame byte 2k, its complement 2k + 1.

GOODWEATHER = Protocol(
    "goodweather",
    {
        "main": Section(
            # kGoodweatherBitMark/ZeroSpace/OneSpace: a one has the short space.
            PulseDistance(580, 1860, 580),
            header=(6820, 6820),  # kGoodweatherHdrMark/HdrSpace
            # sendGoodweather closes with a bit mark, a kGoodweatherHdrSpace
            # space and a second bit mark, then kDefaultMessageGap.
            footer=(580, 6820, 580),
            gap=100000,
        ),
    },
    carrier=38000,  # enableIROut(38)
    # decodeGoodweather: header with the defaults, bits and footer marks with
    # _tolerance + kGoodweatherExtraTolerance (37 %), kMarkExcess.
    tolerance=0.37,
)

GOODWEATHER_COMMAND = {  # kGoodweatherCmd*: the button the frame says was pressed
    "power": 0x00,
    "mode": 0x01,
    "temp_up": 0x02,
    "temp_down": 0x03,
    "swing": 0x04,
    "fan": 0x05,
    "timer": 0x06,
    "air_flow": 0x07,
    "hold": 0x08,
    "sleep": 0x09,
    "turbo": 0x0A,
    "light": 0x0B,
}
GOODWEATHER_MODE = {  # kGoodweather{Auto,Cool,Dry,Fan,Heat}
    "auto": 0b000,
    "cool": 0b001,
    "dry": 0b010,
    "fan": 0b011,
    "heat": 0b100,
}
GOODWEATHER_FAN = {  # canonical fan -> kGoodweatherFan*, as convertFan
    "auto": 0b00,  # kGoodweatherFanAuto
    "1": 0b11,  # kGoodweatherFanLow (kLow)
    "2": 0b10,  # kGoodweatherFanMed (kMedium)
    "3": 0b01,  # kGoodweatherFanHigh (kHigh)
}
GOODWEATHER_SWING = {  # kGoodweatherSwing*: swing speeds, not positions
    "fast": 0b00,
    "slow": 0b01,
    "off": 0b10,
}
# canonical swing_v -> kGoodweatherSwing*: the two swing speeds, slowest
# first. (IRac::goodweather itself sends Slow for any swing but off.)
GOODWEATHER_SWING_BY_LEVEL = {"off": "off", "1": "slow", "2": "fast"}
GOODWEATHER_MIN_TEMP = 16  # kGoodweatherTempMin
GOODWEATHER_MAX_TEMP = 31  # kGoodweatherTempMax

# Skeleton: IRGoodweatherAc::stateReset (kGoodweatherStateInit, 0xD50000000000:
# every sent byte is written, so no stale bits), each byte followed by its
# complement.
GOODWEATHER_LAYOUT = Layout(
    bytes.fromhex("00ff00ff00ff00ff00ffd52a"),
    {
        "light": Field.at(2, 0, 1),
        "turbo": Field.at(2, 3, 1),
        "command": Field.at(4, 0, 4, values=GOODWEATHER_COMMAND),
        "sleep": Field.at(6, 0, 1),
        "power": Field.at(6, 1, 1),
        "swing_v": Field.at(6, 2, 2, values=GOODWEATHER_SWING),
        "air_flow": Field.at(6, 4, 1),
        "fan": Field.at(6, 5, 2, values=GOODWEATHER_FAN),
        "temperature": Field.at(  # whole °C, minus kGoodweatherTempMin
            8,
            0,
            4,
            values={
                t: t - GOODWEATHER_MIN_TEMP
                for t in range(GOODWEATHER_MIN_TEMP, GOODWEATHER_MAX_TEMP + 1)
            },
        ),
        "mode": Field.at(8, 5, 3, values=GOODWEATHER_MODE),
    },
    checksum=InvertedPairs(0, 12),  # sendGoodweather's complement bytes
)


class GoodweatherDevice(Device):
    """Goodweather (ZH/JT-03 remote): a full-state frame that also names a
    button (Command), and ``previous`` is ignored.

    The C path always sends kGoodweatherCmdPower: IRac::goodweather ends with
    setPower, overwriting the Mode/UpTemp/DownTemp/Fan/Swing/Turbo/Light/
    Sleep commands its earlier setters wrote. The header calls the Light,
    Turbo and Sleep bits "toggles", but IRac::goodweather writes them from
    the desired state on every message and IRac::handleToggles has no
    GOODWEATHER case, so C never looks at a previous state; neither does the
    port. The real remote names the key actually pressed (the issue #697
    captures carry UpTemp, DownTemp and Swing); the port does not invent
    that rule.

    Swing is a speed, not a position: swing_v "1" (the legacy "auto low")
    sends kGoodweatherSwingSlow and "2" ("auto high") kGoodweatherSwingFast.
    IRac::goodweather sends Slow for any swing but off, so C never sent
    Fast (a Defect in tests/test_goodweather_device.py). Sleep is the Sleep
    bit (IRac: setSleep(sleep >= 0)). Quiet is not offered: the header has
    no quiet bit ("No Quiet setting available").
    """

    PROTOCOL = GOODWEATHER
    LAYOUTS = (GOODWEATHER_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "fan", "dry", "heat"),
        temperature=TemperatureRange(16.0, 31.0),
        fan=FAN_3,
        swing_v=Choice(
            ("off", "1", "2"), {"off": "off", "1": "auto low", "2": "auto high"}
        ),
        features={"powerful": ON_OFF, "light": ON_OFF, "sleep": ON_OFF},
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to kGoodweatherAuto).
        mode = target.mode if target.power else "auto"
        temperature = min(
            max(int(target.temperature), GOODWEATHER_MIN_TEMP), GOODWEATHER_MAX_TEMP
        )
        data = GOODWEATHER_LAYOUT.build(
            light=target.features.get("light", False),
            turbo=target.features.get("powerful", False),  # IRac's turbo
            # IRac::goodweather calls setPower last.
            command="power",
            power=target.power,
            swing_v=GOODWEATHER_SWING_BY_LEVEL[target.swing_v],
            fan=target.fan,
            temperature=temperature,
            mode=mode,
            sleep=target.features.get("sleep", False),
        )
        return [Frame("main", bytes(data))]


GOODWEATHER_MODELS = ("ZH/JT-03 remote", "generic")


DEVICES.update({m: GoodweatherDevice for m in GOODWEATHER_MODELS})


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        # Goodweather
        "ZH/JT-03 remote": Goodweather,
        "generic": Goodweather,
    }

    def __init__(self):
        self.brand = "goodweather"
