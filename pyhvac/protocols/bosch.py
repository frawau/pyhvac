#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Bosch AC IR commands.
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

from ..choices import FAN_5, ON_OFF
from ..device import Device
from ..fields import Field, InvertedPairs, Layout, Sum8
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import Capabilities, TemperatureRange

# --------------------------------------------------------------- Bosch144
# Layout from IRremoteESP8266's Bosch144Protocol (ir_Bosch.h). A state
# message is three 6-byte sections, each sent MSB first by sendBosch144
# (sendGeneric, MSBfirst true) with a kBoschHdrMark/HdrSpace header, a
# kBoschBitMark footer and a kBoschFooterSpace gap; a kDefaultMessageGap
# space follows the last section. Sections 1 and 2 are identical, every odd
# byte the complement of the byte before it (setInvertBytes). Section 3
# ends with the sum of its first five bytes (setCheckSumS3). An off message
# is the fixed 12-byte kBosch144Off: two sections, no third.
#
# Mode, fan and setpoint codes are split across the sections: the high bits
# go to sections 1 and 2 (ModeS1, FanS1, TempS1), the low bits to section 3
# (ModeS3, FanS3, TempS3/TempS4).

BOSCH144 = Protocol(
    "bosch144",
    {
        "section": Section(
            PulseDistance(456, 610, 1645),  # kBoschBitMark/ZeroSpace/OneSpace
            header=(4366, 4415),  # kBoschHdrMark/HdrSpace
            footer=(456,),  # kBoschBitMark
            gap=5235,  # kBoschFooterSpace
            lsb_first=False,
        ),
        # sendBosch144: space(kDefaultMessageGap) after the last section.
        "end": Section(None, gap=100000),
    },
    carrier=38000,  # kBoschFreq
)

BOSCH144_MODE = {  # kBosch144*: bit 0 to section 3, bits 1-2 to sections 1-2
    "cool": 0b000,
    "dry": 0b011,
    "auto": 0b101,
    "heat": 0b110,
    "fan": 0b010,
}
BOSCH144_FAN = {  # canonical fan -> kBosch144Fan*, as convertFan
    "auto": 0b101110011,  # kBosch144FanAuto
    "1": 0b111001010,  # lowest (kMin): Fan20
    "2": 0b100010100,  # low: Fan40
    "3": 0b010011110,  # medium: Fan60
    "4": 0b001101000,  # high: Fan80
    "5": 0b001110010,  # highest (kMax): Fan100
}
# setMode's fan for auto and dry: FanS1 0b000, FanS3 kBosch144FanAuto0.
BOSCH144_FAN_AUTO0 = 0b000110011
BOSCH144_CELSIUS = {  # kBosch144CelsiusMap: bits 2-5 TempS1, 1 TempS3, 0 TempS4
    16: 0b000010,
    17: 0b000000,
    18: 0b000100,
    19: 0b001100,
    20: 0b001000,
    21: 0b011000,
    22: 0b011100,
    23: 0b010100,
    24: 0b010000,
    25: 0b110000,
    26: 0b110100,
    27: 0b100100,
    28: 0b100000,
    29: 0b101000,
    30: 0b101100,
}

# Sections 1 and 2. Skeleton: kBosch144DefaultState with the fields
# cleared: 0xB2, and the timer bits of byte 2 (0b11111, "not used without
# timer use"). stateReset writes every byte, so no bit is stale.
BOSCH144_SECTION_LAYOUT = Layout(
    bytes.fromhex("b2001f000000"),
    {
        "fan_s1": Field.at(2, 5, 3),  # FanS1: fan code bits 6-8
        "mode_s1": Field.at(4, 2, 2),  # ModeS1: mode code bits 1-2
        "temp_s1": Field.at(4, 4, 4),  # TempS1: setpoint code bits 2-5
    },
    checksum=InvertedPairs(0, 6),  # InnvertS1_1..3 (setInvertBytes)
)

# Section 3. Skeleton: kBosch144DefaultState's 0xD5 with the fields cleared;
# the unknown bits are 0 there.
BOSCH144_SECTION3_LAYOUT = Layout(
    bytes.fromhex("d50000000000"),
    {
        "mode_s3": Field.at(1, 0, 1),  # ModeS3: mode code bit 0
        "fan_s3": Field.at(1, 1, 6),  # FanS3: fan code bits 0-5
        # TempS4 (setpoint code bit 0) and TempS3 (bit 1).
        "temp_s3": Field.over((2, 5), (3, 4)),
        "quiet": Field.at(2, 7, 1),
        "fahrenheit": Field.at(3, 0, 1),  # UseFahrenheit
    },
    checksum=Sum8(0, 5, 5),  # ChecksumS3 (setCheckSumS3)
)

# kBosch144Off: the same section twice, "the same as Coolix protocol".
BOSCH144_OFF_LAYOUT = Layout(
    bytes.fromhex("b24d7b84e01f"), {}, checksum=InvertedPairs(0, 6)
)


class Bosch144Device(Device):
    """Bosch 144-bit: a full-state protocol with no toggles, so ``previous``
    is ignored. Power off is the fixed kBosch144Off message, whatever the
    mode (IRac::bosch144 sends it and returns).

    As IRac::bosch144 sends it (setTemp, setFan, setMode, setQuiet, in
    that order):
    - the setpoint is sent in Celsius (UseFahrenheit clear);
    - auto and dry send setMode's fan code kBosch144FanAuto0, whatever fan
      is requested;
    - quiet sends the fan code kBosch144FanAuto, whatever the mode and fan
      (setQuiet runs last).
    """

    PROTOCOL = BOSCH144
    LAYOUTS = (BOSCH144_SECTION_LAYOUT,) * 2 + (BOSCH144_SECTION3_LAYOUT, None)
    OFF_LAYOUTS = (BOSCH144_OFF_LAYOUT,) * 2 + (None,)
    capabilities = Capabilities(
        modes=("auto", "cool", "fan", "dry", "heat"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=FAN_5,
        features={"quiet": ON_OFF},
    )

    def frames(self, previous, target, actions):
        end = Frame("end", b"", 0)
        if not target.power:
            off = bytes(BOSCH144_OFF_LAYOUT.build())
            return [Frame("section", off), Frame("section", off), end]
        quiet = target.features["quiet"]
        mode = BOSCH144_MODE[target.mode]
        if quiet:
            fan = BOSCH144_FAN["auto"]
        elif target.mode in ("auto", "dry"):
            fan = BOSCH144_FAN_AUTO0
        else:
            fan = BOSCH144_FAN[target.fan]
        # setTemp clamps to kBosch144CelsiusMin-Max, whole degrees.
        temp = BOSCH144_CELSIUS[int(target.temperature)]
        section = bytes(
            BOSCH144_SECTION_LAYOUT.build(
                fan_s1=fan >> 6, mode_s1=mode >> 1, temp_s1=temp >> 2
            )
        )
        section3 = bytes(
            BOSCH144_SECTION3_LAYOUT.build(
                mode_s3=mode & 1,
                fan_s3=fan & 0b111111,
                temp_s3=temp & 0b11,
                quiet=quiet,
                fahrenheit=0,
            )
        )
        return [
            Frame("section", section),
            Frame("section", section),
            Frame("section", section3),
            end,
        ]


BOSCH144_MODELS = ("CL3000i-Set 26 E", "RG10A(G2S)BGEF remote", "generic")


# Now the match between models and objects
