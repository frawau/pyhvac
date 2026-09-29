#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Panasonic AC IR commands
#
# This module is in part based on the work/code from:
#      Scott Kyle https://gist.github.com/appden/42d5272bf128125b019c45bc2ed3311f
#      mat_fr     https://www.instructables.com/id/Reverse-engineering-of-an-Air-Conditioning-control/
#      user two, mathieu, vincent
#                 https://www.analysir.com/blog/2014/12/27/reverse-engineering-panasonic-ac-infrared-protocol/
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

import struct
from dataclasses import dataclass

from .hvaclib import HVAC, PulseBased, GenPluginObject, bit_reverse
from ..device import Device
from ..fields import Checksums, Copy, Field, Layout, Sum8
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_5, ON_OFF, SWING, SWING_H_5, SWING_V_AUTO_ANGLES
from ..state import Capabilities, Choice, TemperatureRange

try:
    from ..irhvac import (
        kPanasonicLke,
        kPanasonicCkp,
        kPanasonicDke,
        kPanasonicJke,
        kPanasonicNke,
        kPanasonicRkr,
    )
except ImportError:
    # Only the C-backed classes use these; keep the pure-Python ones importable.
    kPanasonicLke = kPanasonicCkp = kPanasonicDke = None
    kPanasonicJke = kPanasonicNke = kPanasonicRkr = None


PANASONIC_NATIVE = Protocol(
    "panasonic-native",
    {
        "main": Section(
            PulseDistance(435, 435, 1300),
            header=(3500, 1750),
            footer=(435,),
            gap=10000,
            lsb_first=False,
        )
    },
)


class Panasonic(HVAC):
    """Generic Panasonic HVAC object. It must have, at the very minimum
    "mode" and "temperature" capabilities"""

    PROTOCOL = PANASONIC_NATIVE

    FHEADER = b"\x40\x04\x07\x20\x00"
    F1BODY = b"\x00\x00"
    F2COMMON1 = b"\x00\x00\x70\x07"
    F2COMMON2 = b"\x00\x91\x00"
    FODOUR = b"\x40\x04\x07\x20\x01\xd9\x4c"
    FECON = b"\x40\x04\x07\x20\x01\xa1\xac"
    FILLER = b"\x01"

    def __init__(self):
        super().__init__()
        self.brand = "Panasonic"
        self.model = "Generic"
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry"],
            "temperature": [x for x in range(16, 32)],
        }
        # For functions that require their own frames
        self.xtra_capabilities = {}
        self.status = {"mode": "off", "temperature": 25}

        self.to_set = {}
        self.base_temp = 16

    def set_temperature(self, temp):
        if temp < self.capabilities["temperature"][0]:
            temp = self.capabilities["temperature"][0]
        elif temp > self.capabilities["temperature"][-1]:
            temp = self.capabilities["temperature"][-1]
        self.to_set["temperature"] = temp

    def code_temperature(self):
        if "temperature" in self.to_set:
            temp = self.to_set["temperature"]
            if "mode" in self.to_set and self.to_set["mode"] == "fan":
                temp = 27
        else:
            temp = self.status["temperature"]
        t = 0x20 + ((temp - self.base_temp) << 1)
        return bit_reverse(t).to_bytes(1, "big")

    def set_mode(self, mode):
        if mode not in self.capabilities["mode"]:
            mode = "auto"
        self.to_set["mode"] = mode
        if mode == "fan":
            self.to_set["temperature"] = 27
        if mode == "off":
            self.to_set = {"mode": "off"}

    def code_mode(self):
        if "mode" in self.to_set:
            mode = self.to_set["mode"]
        else:
            mode = self.status["mode"]

        if mode == "off":
            return b"\x10"
        elif mode == "dry":
            return b"\x94"
        elif mode == "fan":
            return b"\x96"
        elif mode == "cool":
            return b"\x9c"
        elif mode == "heat":
            return b"\x92"
        else:
            # If we do not know, also auto mode
            return b"\x90"

    def set_fan(self, mode):
        if "fan" not in self.capabilities:
            return
        if mode not in self.capabilities["fan"]:
            return
        self.to_set["fan"] = mode

    def code_fan(self):
        if "fan" in self.to_set:
            mode = self.to_set["fan"]
        else:
            if "fan" in self.capabilities:
                mode = self.status["fan"]
            else:
                mode = None

        if mode == "auto":
            return b"\x05"
        elif mode == "highest":
            return b"\x0e"
        elif mode == "high":
            return b"\x06"
        elif mode == "medium":
            return b"\x0a"
        elif mode == "low":
            return b"\x02"
        elif mode == "lowest":
            return b"\x0c"
        else:
            # If we do not know.... 0
            return b"\x00"

    def set_swing(self, mode):
        if "swing" not in self.capabilities:
            return
        if mode not in self.capabilities["swing"]:
            if "auto" in self.capabilities["swing"] and "auto" in mode:
                self.to_set["swing"] = "auto"
            return
        self.to_set["swing"] = mode

    def code_swing(self):
        if "swing" in self.to_set:
            mode = self.to_set["swing"]
        else:
            if "swing" in self.capabilities:
                mode = self.status["swing"]
            else:
                mode = None

        if mode == "auto":
            return b"\xf0"
        elif mode == "auto high":
            return b"\x70"
        elif mode == "auto low":
            return b"\xb0"
        elif mode == "ceiling":
            return b"\x80"
        elif mode == "90°":
            return b"\x40"
        elif mode == "60°":
            return b"\xc0"
        elif mode == "45°":
            return b"\x20"
        elif mode == "30°":
            return b"\xa0"
        else:
            # If we do not know....0
            return b"\x00"

    def set_profile(self, mode):
        if "profile" not in self.capabilities:
            return
        if mode not in self.capabilities["profile"]:
            return
        self.to_set["profile"] = mode

    def code_profile(self):
        if "profile" in self.to_set:
            mode = self.to_set["profile"]
        else:
            if "profile" in self.capabilities:
                mode = self.status["profile"]
            else:
                mode = None
        if mode == "normal":
            return b"\x08"
        elif mode == "boost":
            return b"\x88"
        elif mode == "quiet":
            return b"\x0c"

        return b"\x00"

    def set_purifier(self, mode="off"):
        if "purifier" not in self.capabilities:
            return
        if mode not in self.capabilities["purifier"]:
            return
        self.to_set["purifier"] = mode

    def code_purifier(self):

        if "purifier" in self.to_set:
            mode = self.to_set["purifier"]
        else:
            if "purifier" in self.capabilities:
                mode = self.status["purifier"]
            else:
                mode = None

        if mode == "on":
            return b"\x20"
        else:
            return b"\x00"

    def set_cleaning(self, mode="off"):
        if "cleaning" not in self.xtra_capabilities:
            return
        if mode not in self.xtra_capabilities["cleaning"]:
            return
        # This is a toggling value AFAIK
        if self.status["cleaning"] != mode:
            self.to_set["cleaning"] = mode

    def code_cleaning(self):
        frames = []
        if "cleaning" in self.to_set:
            frames += [self.FHEADER + self.F1BODY]
            frames += [self.FODOUR]
        return frames

    def set_economy(self, mode="off"):
        if "economy" not in self.xtra_capabilities:
            return
        if mode not in self.xtra_capabilities["economy"]:
            return
        # This is a toggling value AFAIK
        if self.status["economy"] != mode:
            self.to_set["economy"] = mode

    def code_economy(self):
        frames = []
        if "economy" in self.to_set:
            frames += [self.FHEADER + self.F1BODY]
            frames += [self.FECON]
        return frames

    def crc(self, frame):
        crc = 0
        for x in frame:
            # print("Adding 0x%02x as 0x%02x"%(x,bit_reverse(x)))
            crc += bit_reverse(x)
            # print("crc now 0x%02x"%crc)
        return bit_reverse(crc & 0xFF).to_bytes(1, "big")

    def build_code(self):
        if "mode" not in self.to_set and self.status["mode"] == "fan":
            self.to_set["temperature"] = 27
        frames = [self.FHEADER + self.F1BODY]
        f2 = self.FHEADER + self.code_mode() + self.code_temperature() + self.FILLER
        f2 += (self.code_fan()[0] + self.code_swing()[0]).to_bytes(1, "big")
        f2 += self.F2COMMON1
        f2 += self.code_profile()
        f2 += self.F2COMMON2
        f2 += self.code_purifier()
        frames += [f2]
        return frames

    def _build_ircode(self):
        frames = []
        frames += self.code_cleaning()
        frames += self.code_economy()
        frames += self.build_code()
        idx = 0
        for x in frames:
            frames[idx] += self.crc(x)
            idx += 1
        return frames


class PanaCassette(Panasonic):
    """PX2T5 amd similar Panasonic HVAC object."""

    def __init__(self):
        super().__init__()
        self.model = "4 Way Cassette"
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry"],
            "temperature": [x for x in range(16, 32)],
            "fan": ["auto", "highest", "medium", "lowest"],
            "swing": ["auto", "auto high", "auto low", "90°", "60°", "45°", "30°"],
            "purifier": ["off", "on"],
        }
        # For functions that require their own frames
        self.xtra_capabilities = {"economy": ["off", "on"], "cleaning": ["off", "on"]}
        self.status = {
            "mode": "off",
            "temperature": 25,
            "fan": "auto",
            "swing": "auto",
            "purifier": "off",
            "economy": "off",
            "cleaning": "off",
        }


class PanasonicLke(PulseBased):

    STARTFRAME = [3456, 1728]
    ENDFRAME = None
    MARK = [432]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [432, 1296]  # ditto

    def __init__(self):
        super().__init__("PANASONIC_AC", variant=kPanasonicLke)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": ["off", "on"],
            "quiet": ["off", "on"],
            "powerful": ["off", "on"],
        }


class PanasonicNke(PulseBased):

    STARTFRAME = [3456, 1728]
    ENDFRAME = None
    MARK = [432]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [432, 1296]  # ditto

    def __init__(self):
        super().__init__("PANASONIC_AC", variant=kPanasonicNke)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": ["off", "on"],
            "quiet": ["off", "on"],
            "powerful": ["off", "on"],
        }


class PanasonicDke(PulseBased):

    STARTFRAME = [3456, 1728]
    ENDFRAME = None
    MARK = [432]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [432, 1296]  # ditto

    def __init__(self):
        super().__init__("PANASONIC_AC", variant=kPanasonicDke)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": ["auto", "far right", "right", "middle", "left", "far left"],
            "quiet": ["off", "on"],
            "powerful": ["off", "on"],
            "purifier": ["off", "on"],
        }


class PanasonicJke(PulseBased):

    STARTFRAME = [3456, 1728]
    ENDFRAME = None
    MARK = [432]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [432, 1296]  # ditto

    def __init__(self):
        super().__init__("PANASONIC_AC", variant=kPanasonicJke)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["auto", "90°", "60°", "45°", "30°", "0°"],
            "quiet": ["off", "on"],
            "powerful": ["off", "on"],
        }


class PanasonicCkp(PulseBased):

    STARTFRAME = [3456, 1728]
    ENDFRAME = None
    MARK = [432]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [432, 1296]  # ditto

    def __init__(self):
        super().__init__("PANASONIC_AC", variant=kPanasonicCkp)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["auto", "90°", "60°", "45°", "30°", "0°"],
            "quiet": ["off", "on"],
            "powerful": ["off", "on"],
        }


class PanasonicRkr(PulseBased):

    STARTFRAME = [3456, 1728]
    ENDFRAME = None
    MARK = [432]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [432, 1296]  # ditto

    def __init__(self):
        super().__init__("PANASONIC_AC", variant=kPanasonicRkr)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": ["auto", "far right", "right", "middle", "left", "far left"],
            "quiet": ["off", "on"],
            "powerful": ["off", "on"],
        }


class Panasonic32(PulseBased):

    STARTFRAME = [3543, 3450]
    ENDFRAME = [920, 13946]
    MARK = [920]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [828, 2575]  # ditto

    def __init__(self):
        super().__init__("PANASONIC_AC32")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": ["off", "on"],
        }


DEVICES = {}


# ------------------------------------------------------------- PanasonicAc
# Layout from IRremoteESP8266's IRPanasonicAc (ir_Panasonic.h/.cpp). The
# header has no bitfield struct for this protocol: the fields are its
# constants (kPanasonicAc*Offset/Size, kPanasonicAcIonFilterByte, the
# per-model bytes IRPanasonicAc::setModel writes) over the 27-byte
# kPanasonicKnownGoodState. IRsend::sendPanasonicAC sends it LSB first in two
# sections: bytes 0-7 (kPanasonicAcSection1Length), closed by
# kPanasonicAcSectionGap, then bytes 8-26, closed by kPanasonicAcMessageGap
# (kDefaultMessageGap). Second-frame byte n is state byte n + 8.

PANASONIC_AC = Protocol(
    "panasonic-ac",
    {
        "first": Section(
            PulseDistance(432, 432, 1296),  # kPanasonicBitMark/ZeroSpace/OneSpace
            header=(3456, 1728),  # kPanasonicHdrMark/HdrSpace
            footer=(432,),
            gap=10000,  # kPanasonicAcSectionGap
        ),
        "second": Section(
            PulseDistance(432, 432, 1296),
            header=(3456, 1728),
            footer=(432,),
            gap=100000,  # kPanasonicAcMessageGap = kDefaultMessageGap
        ),
    },
    carrier=36700,  # kPanasonicFreq
    # decodePanasonicAC: kPanasonicAcTolerance (40 %), kPanasonicAcExcess (0).
    tolerance=0.40,
    mark_excess=0,
)

PANASONIC_AC_MODE = {  # kPanasonicAc{Auto,Dry,Cool,Heat,Fan}
    "auto": 0b000,
    "dry": 0b010,
    "cool": 0b011,
    "heat": 0b100,
    "fan": 0b110,
}
PANASONIC_AC_FAN = {  # canonical fan -> kPanasonicAcFan* + kPanasonicAcFanDelta
    "auto": 7 + 3,  # FanAuto
    "1": 0 + 3,  # lowest: FanMin (kMin)
    "2": 1 + 3,  # low: FanLow
    "3": 2 + 3,  # medium: FanMed
    "4": 3 + 3,  # high: FanHigh
    "5": 4 + 3,  # highest: FanMax (kMax)
}
PANASONIC_AC_SWING_V = {  # canonical swing -> kPanasonicAcSwingV*, top to bottom
    "auto": 0xF,  # SwingVAuto
    "1": 0x1,  # 90°: SwingVHighest
    "2": 0x2,  # 60°: SwingVHigh
    "3": 0x3,  # 45°: SwingVMiddle
    "4": 0x4,  # 30°: SwingVLow
    "5": 0x5,  # 0°: SwingVLowest
}
PANASONIC_AC_SWING_H = {  # canonical position -> kPanasonicAcSwingH*
    "auto": 0xD,  # SwingHAuto
    "1": 0x9,  # far left: SwingHFullLeft
    "2": 0xA,  # left: SwingHLeft
    "3": 0x6,  # middle: SwingHMiddle
    "4": 0xB,  # right: SwingHRight
    "5": 0xC,  # far right: SwingHFullRight
}
PANASONIC_AC_MIN_TEMP, PANASONIC_AC_MAX_TEMP = 16, 30  # kPanasonicAcMin/MaxTemp
PANASONIC_AC_TIME_SPECIAL = 0x600  # kPanasonicAcTimeSpecial: "no time"

# The first section never changes: kPanasonicKnownGoodState bytes 0-7.
PANASONIC_AC_FIRST = Layout(bytes.fromhex("0220e00400000006"), {})


def _panasonic_ac_second(quiet_bit, powerful_bit):
    """The second section, with Quiet and Powerful at the given byte-21 bits."""
    return Layout(
        # kPanasonicKnownGoodState bytes 8-26 with every field the device
        # writes cleared. Byte 15 (0x80), byte 19 bit 3 and byte 20 bit 7 are
        # constants; both timers stay kPanasonicAcTimeSpecial and disabled,
        # as IRac::panasonic never sets them. stateReset copies the whole
        # known good state, so no byte comes from stale memory.
        bytes.fromhex("0220e004000000800000000ee0000000000000"),
        {
            "power": Field.at(5, 0, 1),  # kPanasonicAcPowerOffset
            "on_timer_enabled": Field.at(5, 1, 1),  # kPanasonicAcOnTimerOffset
            "off_timer_enabled": Field.at(5, 2, 1),  # kPanasonicAcOffTimerOffset
            "model_13": Field.at(5, 3, 1),  # setModel: RKR sets byte 13 |= 0x08
            "mode": Field.at(5, 4, 3, values=PANASONIC_AC_MODE),
            "temperature": Field.at(  # kPanasonicAcTempOffset/Size, in °C
                6,
                1,
                5,
                values={
                    t: t
                    for t in range(PANASONIC_AC_MIN_TEMP, PANASONIC_AC_MAX_TEMP + 1)
                },
            ),
            "swing_v": Field.at(8, 0, 4, values=PANASONIC_AC_SWING_V),
            "fan": Field.at(8, 4, 4, values=PANASONIC_AC_FAN),
            # Byte 17 low nibble: kPanasonicAcSwingH* on DKE/RKR, Middle on
            # NKE (forced by setSwingHorizontal), 0 on JKE/CKP (never written).
            "swing_h": Field.at(9, 0, 4),
            "on_timer": Field.at(10, 0, 11),  # bytes 18-19, _setTime
            "off_timer": Field.at(11, 4, 11),  # bytes 19-20, setOffTimer
            "quiet": Field.at(13, quiet_bit, 1),
            "model_21": Field.at(13, 4, 1),  # setModel: CKP sets byte 21 |= 0x10
            "powerful": Field.at(13, powerful_bit, 1),
            "ion": Field.at(14, 0, 1),  # kPanasonicAcIonFilterByte/Offset (DKE)
            "model_23": Field.at(15, 0, 8),  # setModel: 0x81, DKE/CKP 0x01, RKR 0x89
            "clock": Field.at(16, 0, 11),  # bytes 24-25, _setTime
        },
        # IRPanasonicAc::calcChecksum: sumBytes(state[0:26], kPanasonicAcChecksumInit
        # = 0xF4). The constant first section sums to 0x0C, and 0xF4 + 0x0C
        # = 0x100, so it is a plain sum of this section's bytes 0-17.
        checksum=Sum8(0, 18, 18),
    )


# kPanasonicAcQuietOffset / kPanasonicAcPowerfulOffset; CKP and RKR have them
# swapped (kPanasonicAcQuietCkpOffset / kPanasonicAcPowerfulCkpOffset).
PANASONIC_AC_SECOND = _panasonic_ac_second(quiet_bit=0, powerful_bit=5)
PANASONIC_AC_SECOND_CKP = _panasonic_ac_second(quiet_bit=5, powerful_bit=0)

# What IRPanasonicAc::setModel writes for each panasonic_ac_remote_model_t,
# and which of the per-model settings each remote has. "swing_h" is the
# setSwingHorizontal behaviour: "positions" (DKE, RKR), "middle" (NKE: always
# Middle) or None (JKE, CKP: byte 17 is never written).
PANASONIC_AC_VARIANTS = {
    "NKE": dict(model_13=0, model_21=0, model_23=0x81, clock=0, swing_h="middle"),
    "DKE": dict(
        model_13=0,
        model_21=0,
        model_23=0x01,
        clock=PANASONIC_AC_TIME_SPECIAL,  # setModel: byte 25 = 0x06
        swing_h="positions",
    ),
    "JKE": dict(model_13=0, model_21=0, model_23=0x81, clock=0, swing_h=None),
    "CKP": dict(model_13=0, model_21=1, model_23=0x01, clock=0, swing_h=None),
    "RKR": dict(model_13=1, model_21=0, model_23=0x89, clock=0, swing_h="positions"),
}

_PANASONIC_AC_ON_OFF = ON_OFF
_PANASONIC_AC_POSITIONS = SWING_H_5


def _panasonic_ac_capabilities(variant):
    swing_h = {
        "NKE": SWING,
        "DKE": _PANASONIC_AC_POSITIONS,
        "RKR": _PANASONIC_AC_POSITIONS,
    }.get(variant)
    features = {"quiet": _PANASONIC_AC_ON_OFF, "powerful": _PANASONIC_AC_ON_OFF}
    if variant == "DKE":
        features["purifier"] = _PANASONIC_AC_ON_OFF
    return Capabilities(
        modes=("auto", "cool", "dry", "heat", "fan"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=FAN_5,
        swing_v=SWING_V_AUTO_ANGLES,
        swing_h=swing_h,
        features=features,
    )


class PanasonicAcDevice(Device):
    """Panasonic 216-bit A/C (remote variants NKE, DKE, JKE, CKP and RKR,
    panasonic_ac_remote_model_t): full state in two sections.

    The variant comes from the model (PANASONIC_AC_MODELS) unless given, so
    the registry's ``cls(brand, model)`` call picks it. An unknown model gets
    JKE: IRPanasonicAc::setModel ignores an unknown model, and getModel reads
    the untouched kPanasonicKnownGoodState as JKE. The capabilities (swing_h,
    purifier) and the Quiet/Powerful bits depend on the variant.

    ``previous`` is ignored, except on CKP. There the Power bit is a toggle
    (setPower's warning): IRac::handleToggles sends ``power ^ prev->power``
    for kPanasonicCkp, so the port toggles only when the power changes.
    Without ``previous`` it sends what a fresh IRac does: its _prev has
    protocol UNKNOWN, so handleToggles does nothing and the bit is the
    target power (1 for on, 0 for off, which leaves a CKP unit as it is).
    The other variants carry the power as state.
    """

    PROTOCOL = PANASONIC_AC

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        self.variant = variant or PANASONIC_AC_MODELS.get(model, "JKE")
        if self.variant not in PANASONIC_AC_VARIANTS:
            raise ValueError(f"unknown PanasonicAc variant {self.variant!r}")
        self.capabilities = _panasonic_ac_capabilities(self.variant)
        second = (
            PANASONIC_AC_SECOND_CKP
            if self.variant in ("CKP", "RKR")
            else PANASONIC_AC_SECOND
        )
        self.LAYOUTS = (PANASONIC_AC_FIRST, second)

    def frames(self, previous, target, actions):
        variant = PANASONIC_AC_VARIANTS[self.variant]
        power = target.power
        if self.variant == "CKP" and previous is not None:
            power = target.power != previous.power
        # IRac::panasonic: setMode(convertMode(mode)) then setTemp(degrees).
        # An off message carries mode auto (convertMode's default for kOff),
        # and fan mode keeps the requested temperature: setMode's 27 °C
        # (kPanasonicAcFanModeTemp) is overwritten by the setTemp after it.
        mode = target.mode if target.power else "auto"
        temperature = min(
            max(int(target.temperature), PANASONIC_AC_MIN_TEMP), PANASONIC_AC_MAX_TEMP
        )
        if variant["swing_h"] == "positions":
            swing_h = PANASONIC_AC_SWING_H[target.swing_h]
        elif variant["swing_h"] == "middle":
            swing_h = PANASONIC_AC_SWING_H["3"]
        else:
            swing_h = 0
        # setQuiet then setPowerful: Powerful on clears Quiet.
        powerful = target.features["powerful"]
        quiet = target.features["quiet"] and not powerful
        # setIon only acts on DKE. The C path passes send.clock (-1, true) as
        # IRac::panasonic's filter argument, so it always sets Ion; the port
        # sends the documented purifier value (declared as a Defect).
        ion = target.features.get("purifier", False)
        second = self.LAYOUTS[1].build(
            power=power,
            model_13=variant["model_13"],
            mode=mode,
            temperature=temperature,
            # The documented positions: "1" (90°) is SwingVHighest. The old
            # glue sent kHigh for 90° and kUpperMiddle (-> Auto) for 60°.
            swing_v=target.swing_v,
            fan=target.fan,
            swing_h=swing_h,
            quiet=quiet,
            model_21=variant["model_21"],
            powerful=powerful,
            ion=ion,
            model_23=variant["model_23"],
            clock=variant["clock"],
        )
        return [
            Frame("first", bytes(PANASONIC_AC_FIRST.skeleton)),
            Frame("second", bytes(second)),
        ]


PANASONIC_AC_MODELS = {  # model -> remote variant (panasonic_ac_remote_model_t)
    "NKE series": "NKE",
    "DKE series": "DKE",
    "DKW series": "DKE",
    "PKR series": "DKE",
    "JKE series": "JKE",
    "CKP series": "CKP",
    "RKR series": "RKR",
    "CS-ME10CKPG": "CKP",
    "CS-ME12CKPG": "CKP",
    "CS-ME14CKPG": "CKP",
    "CS-E7PKR": "DKE",
    "CS-Z9RKR": "RKR",
    "CS-Z24RKR": "RKR",
    "CS-YW9MKD": "JKE",
    "CS-E12QKEW": "DKE",
    "A75C2311remote": "CKP",
    "A75C2616-1remote": "DKE",
    "A75C3704remote": "DKE",
    "PN1122Vremote": "DKE",
    "A75C3747remote": "JKE",
    "A75C4762remote": "RKR",
}


DEVICES.update({m: PanasonicAcDevice for m in PANASONIC_AC_MODELS})


# ------------------------------------------------------- PanasonicAc32
# Layout from IRremoteESP8266's PanasonicAc32Protocol (ir_Panasonic.h): one
# 32-bit word. sendPanasonicAC32 sends it as two sections, the upper 16 bits
# (bytes 2 and 3) first. Each section is sent twice ("block" + repeat), and
# each byte of it is doubled on the wire: b2 b2 b3 b3, then b0 b0 b1 b1, all
# LSB first. A block has no footer mark: the next kPanasonicAc32HdrMark closes
# its last bit. The section then ends with a data-less header, a bit mark and
# kPanasonicAc32SectionGap. So the "block" footer is the repeat's header, and
# the "repeat" footer is that closing header + mark.

PANASONIC_AC32 = Protocol(
    "panasonic-ac32",
    {
        "block": Section(
            PulseDistance(920, 828, 2575),
            header=(3543, 3450),
            footer=(3543, 3450),
        ),
        "repeat": Section(
            PulseDistance(920, 828, 2575),
            footer=(3543, 3450, 920),
            gap=13946,
        ),
    },
    carrier=36700,  # kPanasonicFreq
)


# sendPanasonicAC32 duplicates every byte: data[1] == data[0] and
# data[3] == data[2]. Not a checksum, but the same contract: the copies are
# derived from the fields, which live in bytes 0 and 2 only.
PANASONIC_AC32_DOUBLED = Checksums(Copy(0, 1, 1), Copy(2, 3, 3))

# The upper section, raw bytes 2 and 3 (doubled). Skeleton from
# kPanasonicAc32KnownGood (0x0AF136FC): byte 3 bits 4-7 are always 0.
PANASONIC_AC32_HIGH_LAYOUT = Layout(
    bytes.fromhex("f1f10a0a"),
    {
        "temperature": Field.at(0, 0, 4, values={t: t - 15 for t in range(16, 31)}),
        "fan": Field.at(  # kPanasonicAc32Fan*
            0,
            4,
            4,
            values={"auto": 0xF, "1": 2, "2": 3, "3": 4, "4": 5, "5": 6},
        ),
        "mode": Field.at(  # kPanasonicAc32*
            2, 0, 3, values={"fan": 1, "cool": 2, "dry": 3, "heat": 4, "auto": 6}
        ),
        # PowerToggle: 0 means toggle, 1 = keep the same.
        "power_toggle": Field.at(2, 3, 1, values={True: 0, False: 1}),
    },
    checksum=PANASONIC_AC32_DOUBLED,
)

# The lower section, raw bytes 0 and 1 (doubled). Byte 0 bits 0-2 (0b100)
# and bit 7 (1), and byte 1 (0x36), are fixed, as in kPanasonicAc32KnownGood.
PANASONIC_AC32_LOW_LAYOUT = Layout(
    bytes.fromhex("fcfc3636"),
    {
        "swing_h": Field.at(0, 3, 1, values={"off": 0, "swing": 1}),
        "swing_v": Field.at(  # kPanasonicAcSwingV*, kPanasonicAc32SwingVAuto
            0,
            4,
            3,
            values={"1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "auto": 7},
        ),
    },
    checksum=PANASONIC_AC32_DOUBLED,
)


class PanasonicAc32Device(Device):
    """Panasonic 32-bit (CS-E9CKP, A75C2295): full state, except that the
    power bit is a toggle.

    With ``previous`` the toggle is sent only when the power changes, which
    is also what the C path does from a persistent IRac object
    (IRac::handleToggles XORs the power for PANASONIC_AC32). Without
    ``previous`` the toggle is ``target.power``, as from a fresh IRac: an
    "on" toggles, an "off" toggles nothing.
    """

    PROTOCOL = PANASONIC_AC32
    LAYOUTS = (
        PANASONIC_AC32_HIGH_LAYOUT,
        PANASONIC_AC32_HIGH_LAYOUT,
        PANASONIC_AC32_LOW_LAYOUT,
        PANASONIC_AC32_LOW_LAYOUT,
    )
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "heat", "fan"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=FAN_5,
        swing_v=SWING_V_AUTO_ANGLES,
        swing_h=SWING,
    )

    def frames(self, previous, target, actions):
        if previous is None:
            toggle = target.power
        else:
            toggle = target.power != previous.power
        high = PANASONIC_AC32_HIGH_LAYOUT.build(
            temperature=int(target.temperature),
            fan=target.fan,
            # As the C path: an off message carries mode auto (IRac passes
            # mode "off", which convertMode maps to kPanasonicAc32Auto).
            mode=target.mode if target.power else "auto",
            power_toggle=toggle,
        )
        low = PANASONIC_AC32_LOW_LAYOUT.build(
            swing_h=target.swing_h, swing_v=target.swing_v
        )
        return [
            Frame("block", bytes(high)),
            Frame("repeat", bytes(high)),
            Frame("block", bytes(low)),
            Frame("repeat", bytes(low)),
        ]


PANASONIC_AC32_MODELS = ("CS-E9CKP series", "A75C2295remote", "generic 32")


DEVICES.update({m: PanasonicAc32Device for m in PANASONIC_AC32_MODELS})


# ------------------------------------------------------- Panasonic native
# The 0.1.x pure-Python Panasonic classes (Panasonic, PanaCassette) on
# PANASONIC_NATIVE. Their code is the spec. Bytes are as sent, MSB first,
# so each value is bit-reversed against the LSB-first convention: the
# classes store the reversed codes. Every frame ends with Panasonic.crc: the
# byte sum of the bit-reversed bytes, bit-reversed.
#
# A message is two frames (Panasonic.build_code):
# - the first frame: FHEADER + F1BODY, a constant;
# - the main frame: FHEADER, mode (code_mode; the power bit is the first
#   sent), temperature (code_temperature), FILLER, fan + swing
#   (code_fan + code_swing), F2COMMON1, profile (code_profile),
#   F2COMMON2, purifier (code_purifier).
# Economy and cleaning are toggles ("This is a toggling value AFAIK"): each
# change is the first frame plus a special frame (FECON, FODOUR), sent
# before the message (Panasonic._build_ircode: cleaning, economy, then the
# message).


@dataclass(frozen=True)
class _ReversedSum8(Sum8):
    """Panasonic.crc: Sum8 over the bit-reversed bytes, bit-reversed."""

    def compute(self, data):
        return bit_reverse(super().compute(data))


PANASONIC_NATIVE_SHORT = Layout(  # the 8-byte frames: FHEADER + 2 bytes + crc
    Panasonic.FHEADER + b"\x00\x00\x00",
    {
        # Bytes 4-6 (byte 4 lowest): F1BODY after FHEADER's zero, or the
        # tail of FECON / FODOUR.
        "frame": Field.at(
            4,
            0,
            24,
            values={
                "first": 0,  # FHEADER + F1BODY
                "economy": int.from_bytes(Panasonic.FECON[4:], "little"),
                "cleaning": int.from_bytes(Panasonic.FODOUR[4:], "little"),
            },
        ),
    },
    checksum=_ReversedSum8(0, 7, 7, reverse=True),
)
PANASONIC_NATIVE_MODE = {  # code_mode without its power bit (0x80)
    "auto": 0x10,
    "heat": 0x12,  # encoded, but no legacy class offers heat
    "dry": 0x14,
    "fan": 0x16,
    "cool": 0x1C,
}
PANASONIC_NATIVE_FAN = {  # code_fan (0: no fan capability)
    None: 0x0,
    "auto": 0x5,
    "highest": 0xE,
    "high": 0x6,
    "medium": 0xA,
    "low": 0x2,
    "lowest": 0xC,
}
PANASONIC_NATIVE_SWING = {  # code_swing, high nibble (0: no swing capability)
    None: 0x0,
    "auto": 0xF,
    "auto high": 0x7,
    "auto low": 0xB,
    "ceiling": 0x8,
    "90°": 0x4,
    "60°": 0xC,
    "45°": 0x2,
    "30°": 0xA,
}
PANASONIC_NATIVE_PROFILE = {  # code_profile; no legacy class offers profile
    None: 0x00,
    "normal": 0x08,
    "boost": 0x88,
    "quiet": 0x0C,
}
PANASONIC_NATIVE_MIN_TEMP = 16  # Panasonic.base_temp
PANASONIC_NATIVE_FAN_TEMP = 27  # set_mode/build_code: fan mode sends 27 °C
PANASONIC_NATIVE_MAIN = Layout(
    Panasonic.FHEADER
    + b"\x00\x00"
    + Panasonic.FILLER
    + b"\x00"
    + Panasonic.F2COMMON1
    + b"\x00"
    + Panasonic.F2COMMON2
    + b"\x00\x00",
    {
        "power": Field.at(5, 7, 1),
        "mode": Field.at(5, 0, 7, values=PANASONIC_NATIVE_MODE),
        # code_temperature: bit_reverse(0x20 + (celsius - base_temp) * 2),
        # for any value set_temperature can hold (16-31 °C)
        "temperature": Field.at(
            6,
            0,
            8,
            values={
                t: bit_reverse(0x20 + ((t - PANASONIC_NATIVE_MIN_TEMP) << 1))
                for t in range(PANASONIC_NATIVE_MIN_TEMP, 32)
            },
        ),
        "fan": Field.at(8, 0, 4, values=PANASONIC_NATIVE_FAN),
        "swing": Field.at(8, 4, 4, values=PANASONIC_NATIVE_SWING),
        "profile": Field.at(13, 0, 8, values=PANASONIC_NATIVE_PROFILE),
        "purifier": Field.at(17, 5, 1),  # code_purifier: 0x20
    },
    checksum=_ReversedSum8(0, 18, 18, reverse=True),
)

PANASONIC_NATIVE_VARIANTS = {
    # Panasonic.__init__: modes off/auto/cool/fan/dry, 16-31 °C, nothing else.
    "generic": Capabilities(
        modes=("auto", "cool", "fan", "dry"),
        temperature=TemperatureRange(16.0, 31.0),
    ),
    # PanaCassette.__init__
    "4 way cassette": Capabilities(
        modes=("auto", "cool", "fan", "dry"),
        temperature=TemperatureRange(16.0, 31.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "lowest", "2": "medium", "3": "highest"},
        ),
        swing_v=Choice(
            ("auto", "1", "2", "3", "4", "5", "6"),
            {
                "auto": "auto",
                "1": "90°",
                "2": "60°",
                "3": "45°",
                "4": "30°",
                "5": "auto high",
                "6": "auto low",
            },
        ),
        features={"purifier": ON_OFF, "economy": ON_OFF, "cleaning": ON_OFF},
    ),
}
PANASONIC_NATIVE_MODELS = {  # model -> variant, as PluginObject.MODELS
    "generic": "generic",
    "4 way cassette": "4 way cassette",
}
PANASONIC_NATIVE_TOGGLES = ("cleaning", "economy")  # _build_ircode's order


class PanasonicNativeDevice(Device):
    """The 0.1.x pure-Python Panasonic classes: Panasonic ("generic") and
    PanaCassette ("4 way cassette"). They share Panasonic's code and differ
    only by their tables (the variant's capabilities).

    The message is the full state (see PANASONIC_NATIVE_MAIN); a variant
    without fan or swing sends 0 there, as code_fan / code_swing. Fan mode
    sends 27 °C (set_mode), whatever the setpoint.

    Power off: the power bit clear and mode auto (code_mode's 0x10). The
    other settings are those the unit had, not the target's: set_mode("off")
    drops every pending change, so the legacy object sent its status. The
    port sends ``previous``'s settings (the target's without it).

    Economy and cleaning are toggles: their special frames go, with power
    on, when the setting differs from ``previous``. Without ``previous``
    the unit is taken to have them off, as a fresh legacy object. With power
    off no toggle goes (set_mode("off") dropped them).
    """

    PROTOCOL = PANASONIC_NATIVE
    # The message; each toggle adds two PANASONIC_NATIVE_SHORT frames before it.
    LAYOUTS = (PANASONIC_NATIVE_SHORT, PANASONIC_NATIVE_MAIN)
    capabilities = PANASONIC_NATIVE_VARIANTS["generic"]

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        self.variant = variant or PANASONIC_NATIVE_MODELS.get(model, "generic")
        if self.variant not in PANASONIC_NATIVE_VARIANTS:
            raise ValueError(f"unknown Panasonic native variant {self.variant!r}")
        self.capabilities = PANASONIC_NATIVE_VARIANTS[self.variant]

    @staticmethod
    def _short(name):
        return Frame("main", bytes(PANASONIC_NATIVE_SHORT.build(frame=name)))

    def _main(self, state, power):
        caps = self.capabilities
        fan = None if caps.fan is None else caps.fan.label(state.fan)
        swing = None if caps.swing_v is None else caps.swing_v.label(state.swing_v)
        if state.mode == "fan":
            temperature = PANASONIC_NATIVE_FAN_TEMP
        else:
            temperature = int(state.temperature)
        data = PANASONIC_NATIVE_MAIN.build(
            power=int(power),
            mode=state.mode if power else "auto",
            temperature=temperature,
            fan=fan,
            swing=swing,
            profile=None,
            purifier=int(state.features.get("purifier", False)),
        )
        return Frame("main", bytes(data))

    def frames(self, previous, target, actions):
        frames = []
        if target.power:
            for name in PANASONIC_NATIVE_TOGGLES:
                if name not in self.capabilities.features:
                    continue
                was = previous is not None and previous.features[name]
                if target.features[name] != was:
                    frames += [self._short("first"), self._short(name)]
            main = self._main(target, True)
        else:
            main = self._main(previous or target, False)
        return frames + [self._short("first"), main]


DEVICES.update({m: PanasonicNativeDevice for m in PANASONIC_NATIVE_MODELS})


class PluginObject(GenPluginObject):
    MODELS = {
        "generic": Panasonic,
        "4 way cassette": PanaCassette,
        "NKE series": PanasonicNke,
        "DKE series": PanasonicDke,
        "DKW series": PanasonicDke,
        "PKR series": PanasonicDke,
        "JKE series": PanasonicJke,
        "CKP series": PanasonicCkp,
        "RKR series": PanasonicRkr,
        "CS-ME10CKPG": PanasonicCkp,
        "CS-ME12CKPG": PanasonicCkp,
        "CS-ME14CKPG": PanasonicCkp,
        "CS-E7PKR": PanasonicDke,
        "CS-Z9RKR": PanasonicRkr,
        "CS-Z24RKR": PanasonicRkr,
        "CS-YW9MKD": PanasonicJke,
        "CS-E12QKEW": PanasonicDke,
        "A75C2311remote": PanasonicCkp,
        "A75C2616-1remote": PanasonicDke,
        "A75C3704remote": PanasonicDke,
        "PN1122Vremote": PanasonicDke,
        "A75C3747remote": PanasonicJke,
        "CS-E9CKP series": Panasonic32,
        "A75C2295remote": Panasonic32,
        "A75C4762remote": PanasonicRkr,
        "generic 32": Panasonic32,
    }

    def __init__(self):
        self.brand = "panasonic"


def main():
    import argparse
    import base64

    parser = argparse.ArgumentParser(description="Generate Panasonic A/C codes.")
    # version="%prog " + __version__ + "/" + bl.__version__)
    parser.add_argument(
        "-M",
        "--model",
        type=str,
        default="generic",
        help="Set the A/C model. (default generic).",
    )
    parser.add_argument(
        "-L",
        "--list",
        action="store_true",
        default=False,
        help="List known models and return.",
    )
    parser.add_argument(
        "-t", "--temp", type=int, default=25, help="Temperature (°C). (default 25)."
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=["auto", "cool", "dry", "fan", "off"],
        default="auto",
        help="Mode, one of 'off', 'auto', 'cool', 'dry' or 'fan'. (default 'auto').",
    )
    parser.add_argument(
        "-f",
        "--fan",
        choices=["auto", "high", "medium", "low"],
        default="auto",
        help="Fan, one of 'auto', 'high', 'medium' or 'low'. (default 'auto').",
    )
    parser.add_argument(
        "-s",
        "--swing",
        choices=["auto", "auto high", "auto low", "90°", "60°", "45°", "30°"],
        default="auto",
        help="Swing, one of 'auto','auto high','auto low', '90', '60', '45', '30'. (default 'auto').",
    )
    parser.add_argument(
        "-n", "--nanoex", action="store_true", default=False, help="nanoeX mode"
    )
    parser.add_argument(
        "-o", "--odour", action="store_true", default=False, help="Odour Wash mode"
    )
    parser.add_argument(
        "-e", "--economy", action="store_true", default=False, help="Economy mode"
    )
    parser.add_argument(
        "-l",
        "--lirc",
        action="store_true",
        default=False,
        help="Output LIRC compatible timing",
    )
    parser.add_argument(
        "-b",
        "--broadlink",
        action="store_true",
        default=False,
        help="Output Broadlink timing",
    )
    parser.add_argument(
        "-B",
        "--base64",
        action="store_true",
        default=False,
        help="Output Broadlink timing base64 encoded",
    )

    try:
        opts = parser.parse_args()
    except Exception as e:
        parser.error("Error: " + str(e))

    if opts.list:
        print(f"Available models are: {[x for x in PluginObject().MODELS.keys()]}")

    device = PluginObject().get_device(opts.model)
    frames = []
    device.set_temperature(opts.temp)
    device.set_fan(opts.fan)
    device.set_swing(opts.swing)
    device.set_purifier((opts.nanoex and "on") or "off")
    device.set_cleaning((opts.odour and "on") or "off")
    device.set_economy((opts.economy and "on") or "off")
    device.set_mode(opts.mode)

    frames = device.build_ircode()

    if opts.lirc:
        lircf = device.to_lirc(frames)
        while lircf:
            print("\t".join(["%d" % x for x in lircf[:6]]))
            lircf = lircf[6:]
    elif opts.broadlink or opts.base64:
        bframe = device.to_broadlink(frames)
        if opts.base64:
            print("{}".format(str(base64.b64encode(bframe), "ascii")))
        else:
            print("{}".format(bframe.hex()))
    else:
        for f in frames:
            print(" ".join(["%02x" % x for x in f]))


if __name__ == "__main__":
    main()
