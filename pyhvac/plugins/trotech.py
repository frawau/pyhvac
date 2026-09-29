#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Trotech AC IR commands.
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
from .midea import MIDEA_TROTECH_MODELS, Midea, MideaDevice
from ..device import Device
from ..fields import Field, Layout, Sum8
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_3_FIXED, ON_OFF, SWING
from ..state import Capabilities, TemperatureRange


class Trotech(PulseBased):

    STARTFRAME = [5952, 7364]
    MARK = [592]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [592, 1560]  # ditto
    TAIL = [592, 6184]

    def __init__(self):
        super().__init__("TROTEC")
        self.capabilities = {
            "mode": ["auto", "cool", "dry", "fan"],
            "temperature": [16, 30],
            "fan": ["high", "medium", "low"],
            "sleep": ["off", "on"],
        }


class Trotech3550(PulseBased):

    STARTFRAME = [12000, 5130]
    MARK = [550]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [500, 1950]  # ditto

    def __init__(self):
        super().__init__("TROTEC_3550")
        self.capabilities = {
            "mode": ["auto", "cool", "dry", "fan"],
            "temperature": [16, 30],
            "fan": ["high", "medium", "low"],
            "swing": ["off", "on"],
        }


DEVICES = {}


# ----------------------------------------------------------------- Trotec
# Layout from IRremoteESP8266's TrotecProtocol (ir_Trotec.h): one 9-byte frame
# (kTrotecStateLength), sent LSB first at 36 kHz. IRsend::sendTrotec follows
# sendGeneric's footer (kTrotecBitMark + kTrotecGap) with one more
# kTrotecBitMark and a kTrotecGapEnd space: a bitless "end" section.

TROTEC = Protocol(
    "trotec",
    {
        "main": Section(
            PulseDistance(592, 592, 1560),  # kTrotecBitMark/ZeroSpace/OneSpace
            header=(5952, 7364),  # kTrotecHdrMark, kTrotecHdrSpace
            footer=(592,),
            gap=6184,  # kTrotecGap
        ),
        "end": Section(None, header=(592,), gap=1500),  # kTrotecGapEnd
    },
    carrier=36000,  # sendTrotec's enableIROut(36)
)

TROTEC_MODE = {  # kTrotec{Auto,Cool,Dry,Fan}
    "auto": 0,
    "cool": 1,
    "dry": 2,
    "fan": 3,
}
TROTEC_FAN = {  # kTrotecFan{Low,Med,High}, as IRTrotecESP::convertFan
    "1": 1,  # low
    "2": 2,  # medium
    "3": 3,  # high
}
TROTEC_MIN_TEMP = 18  # kTrotecMinTemp
TROTEC_MAX_TEMP = 32  # kTrotecMaxTemp

# Skeleton: IRTrotecESP::stateReset (bytes 2-8 zeroed, so no stale memory)
# with Intro1/Intro2 (0x12, 0x34), Temp kTrotecDefTemp and Fan kTrotecFanMed,
# and the sum cleared.
TROTEC_LAYOUT = Layout(
    bytes.fromhex("123420070000000000"),
    {
        "mode": Field.at(2, 0, 2, values=TROTEC_MODE),
        "power": Field.at(2, 3, 1),
        "fan": Field.at(2, 4, 2, values=TROTEC_FAN),
        "temperature": Field.at(  # whole °C, minus kTrotecMinTemp
            3,
            0,
            4,
            values={
                t: t - TROTEC_MIN_TEMP
                for t in range(TROTEC_MIN_TEMP, TROTEC_MAX_TEMP + 1)
            },
        ),
        "sleep": Field.at(3, 7, 1),
        "timer": Field.at(5, 6, 1),
        "hours": Field.at(6, 0, 8),
    },
    checksum=Sum8(2, 8, 8),  # IRTrotecESP::checksum: sumBytes of bytes 2-7
)


class TrotecDevice(Device):
    """Trotec PAC 3200 (and the Duux Blizzard): a full-state frame with a
    power bit, no toggle bits, so ``previous`` is ignored (IRac::handleToggles
    has no TROTEC case either).
    """

    PROTOCOL = TROTEC
    LAYOUTS = (TROTEC_LAYOUT, None)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "fan"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=FAN_3_FIXED,
        features={"sleep": ON_OFF},
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to kTrotecAuto), and setTemp clamps to
        # kTrotecMinTemp..kTrotecMaxTemp, so 16 and 17 °C go out as 18.
        mode = target.mode if target.power else "auto"
        temperature = min(
            max(int(target.temperature), TROTEC_MIN_TEMP), TROTEC_MAX_TEMP
        )
        data = TROTEC_LAYOUT.build(
            mode=mode,
            power=target.power,
            fan=target.fan,
            temperature=temperature,
            # IRac::trotec: setSleep(sleep >= 0). The old glue never passed
            # sleep; the port sends the documented bit (see the tests).
            sleep=target.features.get("sleep", False),
        )
        return [Frame("main", bytes(data)), Frame("end", b"")]


TROTEC_MODELS = ("PAC 3200", "Duux Blizzard Smart 10K / DXMA04", "generic")


# ------------------------------------------------------------- Trotec3550
# Layout from IRremoteESP8266's Trotec3550Protocol (ir_Trotec.h): one 9-byte
# frame (kTrotecStateLength), sent MSB first (sendTrotec3550's sendGeneric
# MSBfirst=true) at 38 kHz, with a kDefaultMessageGap gap.

TROTEC3550 = Protocol(
    "trotec-3550",
    {
        "main": Section(
            PulseDistance(550, 500, 1950),  # kTrotec3550BitMark/Zero/OneSpace
            header=(12000, 5130),  # kTrotec3550HdrMark, kTrotec3550HdrSpace
            footer=(550,),
            gap=100000,  # kDefaultMessageGap
            lsb_first=False,
        ),
    },
    carrier=38000,  # sendGeneric(..., 38, ...)
)

TROTEC3550_SWING_V = {"off": 0, "swing": 1}  # SwingV bit
TROTEC3550_MIN_TEMP = 16  # kTrotec3550MinTempC
TROTEC3550_MAX_TEMP = 30  # kTrotec3550MaxTempC
TROTEC3550_MIN_TEMP_F = 59  # kTrotec3550MinTempF

# Skeleton: IRTrotec3550::stateReset's kReset (all nine bytes written, so no
# stale memory) with the sum cleared: Intro 0x55, TempC 22, TempF 72, Fan
# low, the unknown byte 7 bit 3 and Celsius set.
TROTEC3550_LAYOUT = Layout(
    bytes.fromhex("5560000d0000108800"),
    {
        "swing_v": Field.at(1, 0, 1, values=TROTEC3550_SWING_V),
        "power": Field.at(1, 1, 1),
        "timer_set": Field.at(1, 3, 1),
        "temperature": Field.at(  # whole °C, minus kTrotec3550MinTempC
            1,
            4,
            4,
            values={
                t: t - TROTEC3550_MIN_TEMP
                for t in range(TROTEC3550_MIN_TEMP, TROTEC3550_MAX_TEMP + 1)
            },
        ),
        "timer_hours": Field.at(2, 0, 4),
        "temp_f": Field.at(3, 0, 5),  # whole °F, minus kTrotec3550MinTempF
        "mode": Field.at(6, 0, 2, values=TROTEC_MODE),
        "fan": Field.at(6, 4, 2, values=TROTEC_FAN),
        "celsius": Field.at(7, 7, 1),
    },
    checksum=Sum8(0, 8, 8),  # IRTrotec3550::calcChecksum: bytes 0-7
)


class Trotec3550Device(Device):
    """Trotec PAC 3550 Pro: a full-state frame with a power bit and a SwingV
    bit, no toggle bits, so ``previous`` is ignored (IRac::handleToggles has
    no TROTEC_3550 case either).
    """

    PROTOCOL = TROTEC3550
    LAYOUTS = (TROTEC3550_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "fan"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=FAN_3_FIXED,
        swing_v=SWING,
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode auto (convertMode maps
        # IRac's mode "off" to kTrotecAuto). IRac passes celsius (true), so
        # setTemp stores TempC and the truncated Fahrenheit equivalent.
        mode = target.mode if target.power else "auto"
        temperature = min(
            max(int(target.temperature), TROTEC3550_MIN_TEMP), TROTEC3550_MAX_TEMP
        )
        data = TROTEC3550_LAYOUT.build(
            # IRac::trotec3550: setSwingV(swingv != kOff). The old glue never
            # passed swing "on"; the port sends the documented bit.
            swing_v=target.swing_v,
            power=target.power,
            temperature=temperature,
            temp_f=temperature * 9 // 5 + 32 - TROTEC3550_MIN_TEMP_F,
            mode=mode,
            fan=target.fan,
            celsius=True,
        )
        return [Frame("main", bytes(data))]


TROTEC3550_MODELS = ("PAC 3550 Pro", "generic 3550")


DEVICES.update({m: TrotecDevice for m in TROTEC_MODELS})
DEVICES.update({m: Trotec3550Device for m in TROTEC3550_MODELS})
DEVICES.update({m: MideaDevice for m in MIDEA_TROTECH_MODELS})


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "PAC 2100 X": Midea,
        "PAC 3900 X": Midea,
        "RG57H(B)/BGE remote": Midea,
        "RG57H3(B)/BGCEF-M remote": Midea,
        "PAC 3200": Trotech,
        "PAC 3550 Pro": Trotech3550,
        "Duux Blizzard Smart 10K / DXMA04": Trotech,
        "generic": Trotech,
        "generic 3550": Trotech3550,
    }

    def __init__(self):
        self.brand = "trotech"
