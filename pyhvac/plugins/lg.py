#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate LG AC IR commands as done by the AXB74515402 and others
#
# Found the info about 4 bits somewhere on the  Internet...Can't find
# it again. Apologies for not being able to thanks that person.
#
# Copyright (c) 2023 François Wautier
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

from .hvaclib import HVAC, PulseBased, GenPluginObject
from ..device import Device
from ..fields import Field, HighNibbleSum, Layout
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import Capabilities, Choice, TemperatureRange

try:
    from ..irhvac import (
        GE6711AR2853M,
        LG6711A20083V,
        AKB75215403,
        AKB74955603,
        AKB73757604,
    )
except ImportError:
    # Only the C-backed classes use these; keep the pure-Python ones importable.
    GE6711AR2853M = LG6711A20083V = AKB75215403 = AKB74955603 = AKB73757604 = None


# Frames are 4 bytes (32 bits) on the wire, as the legacy emitter sent them.
LG_NATIVE = Protocol(
    "lg-native",
    {
        "main": Section(
            PulseDistance(520, 520, 1530),
            header=(3100, 9850),
            footer=(520,),
            gap=12000,
            lsb_first=False,
        )
    },
)


class LG(HVAC):
    """Generic LG HVAC object. It must have, at the very minimum
    "mode" and "temperature" capabilities"""

    PROTOCOL = LG_NATIVE

    def __init__(self):
        super().__init__()
        self.brand = "LG"
        self.model = "Generic"
        self.capabilities = {
            "mode": ["off", "cool", "fan", "dry"],
            "temperature": [x for x in range(18, 30)],
        }
        # For functions that require their own frames
        self.xtra_capabilities = {}
        self.status = {"mode": "off", "temperature": 25}

        self.to_set = {}
        self.FBODY = b"\x88\x00\x00"

    def set_temperature(self, temp):
        if temp < self.capabilities["temperature"][0]:
            temp = self.capabilities["temperature"][0]
        elif temp > self.capabilities["temperature"][-1]:
            temp = self.capabilities["temperature"][-1]
        if temp != self.status["temperature"]:
            self.to_set["temperature"] = temp

    def code_temperature(self):
        if "temperature" in self.to_set:
            temp = self.to_set["temperature"]
        else:
            temp = self.status["temperature"]

        if "mode" in self.to_set:
            mode = self.to_set["mode"]
        else:
            mode = self.status["mode"]

        if mode == "fan":
            temp = 18
        elif mode == "auto":
            if "auto_bias" in self.status:
                try:  # Getting ahead of oneself...
                    if "auto_bias" in self.to_set:
                        temp = 15 + self.capabilities["auto_bias"].index(
                            self.to_set["auto_bias"]
                        )
                    else:
                        temp = 15 + self.capabilities["auto_bias"].index(
                            self.status["auto_bias"]
                        )
                except:
                    temp = 17
            else:
                temp = 17
        elif mode == "dry":
            temp = 24
        mask = bytearray(b"\x00" * 3)
        mask[2] = (temp - 15) << 4
        return mask, False

    def set_auto_bias(self, mode):
        if "auto_bias" not in self.capabilities:
            return
        if mode not in self.capabilities["auto_bias"]:
            return
        if self.status["auto_bias"] != mode:
            self.to_set["auto_bias"] = mode

    def set_fan(self, mode):
        if "fan" not in self.capabilities:
            return
        if mode not in self.capabilities["fan"]:
            return
        if self.status["fan"] != mode:
            self.to_set["fan"] = mode

    def code_fan(self):
        """mode is one of auto, lowest, low, medium, high, highest"""
        if "fan" in self.to_set:
            fmode = self.to_set["fan"]
        else:
            if "fan" in self.capabilities:
                fmode = self.status["fan"]
            else:
                fmode = "auto"
        rank = {
            "lowest": 0x0,
            "low": 0x09,
            "medium": 0x02,
            "high": 0x0A,
            "highest": 0x04,
            "auto": 0x05,
        }

        if "mode" in self.to_set:
            mode = self.to_set["mode"]
        else:
            mode = self.status["mode"]

        if mode == "auto":
            fmode = "auto"
        if fmode not in rank:
            fmode = "auto"  # Just in case
        mask = bytearray(b"\x00" * 3)
        mask[2] = rank[fmode]
        return mask, False

    def set_swing(self, mode):
        if "swing" not in self.xtra_capabilities:
            return
        if mode not in self.xtra_capabilities["swing"]:
            return
        if self.status["swing"] != mode:
            self.to_set["swing"] = mode

    def code_swing(self):
        if "swing" in self.to_set:
            mode = self.to_set["swing"]

            if mode in ["swing", "on"]:
                return bytearray(b"\x88\x13\x14")
            elif mode == "off":
                return bytearray(b"\x88\x13\x15")
            elif mode == "0°":
                return bytearray(b"\x88\x13\x04")
            elif mode == "30°":
                return bytearray(b"\x88\x13\x05")
            elif mode == "45°":
                return bytearray(b"\x88\x13\x06")
            elif mode == "60°":
                return bytearray(b"\x88\x13\x07")
            elif mode == "90°":
                return bytearray(b"\x88\x13\x08")
            elif mode == "ceiling":
                return bytearray(b"\x88\x13\x09")

        return bytearray()

    def set_hswing(self, mode):
        if "hswing" not in self.xtra_capabilities:
            return
        if mode not in self.xtra_capabilities["hswing"]:
            return
        if self.status["hswing"] != mode:
            self.to_set["hswing"] = mode

    def code_hswing(self):
        if "hswing" in self.to_set:
            mode = self.to_set["hswing"]

            if mode in ["swing", "on"]:
                return bytearray(b"\x88\x13\x16")
            elif mode == "off":
                return bytearray(b"\x88\x13\x17")
            elif mode == "left":
                return bytearray(b"\x88\x13\x0b")
            elif mode == "centre left":
                return bytearray(b"\x88\x13\x0c")
            elif mode == "centre":
                return bytearray(b"\x88\x13\x0d")
            elif mode == "centre right":
                return bytearray(b"\x88\x13\x0e")
            elif mode == "right":
                return bytearray(b"\x88\x13\x0f")
            elif mode == "swing left":
                return bytearray(b"\x88\x13\x10")
            elif mode == "swing right":
                return bytearray(b"\x88\x13\x11")
        return bytearray()

    def set_powerful(self, mode="off"):
        # print("\n\nLG set powerful {}\n\n".format(mode))
        if "powerful" not in self.xtra_capabilities:
            return
        if mode not in self.xtra_capabilities["powerful"]:
            return
        if self.status["powerful"] != mode:
            self.to_set["powerful"] = mode

    def code_powerful(self):

        if "powerful" in self.to_set:
            mode = self.to_set["powerful"]
            if mode == "on":
                return bytearray(b"\x88\x10\x08")
            # Off... send the "normal" code
            dosend = True
            for x in self.capabilities:
                if x in self.to_set:
                    dosend = False
                    break
            if dosend:
                otoset = self.to_set
                self.to_set = {"mode": self.status["mode"]}
                frame = self.build_code()
                self.to_set = otoset
                return frame
        return []

    def set_purifier(self, mode="off"):
        if "purifier" not in self.xtra_capabilities:
            return
        if mode not in self.xtra_capabilities["purifier"]:
            return
        # This is a toggling value AFAIK
        if self.status["purifier"] != mode:
            self.to_set["purifier"] = mode

    def code_purifier(self):
        """Some LG AC seem to have such"""
        if self.to_set["purifier"] == "on":
            return bytearray(b"\x88\xc0\x00")
        else:
            return bytearray(b"\x88\xc0\x08")

    def set_economy(self, mode):
        if "economy" not in self.xtra_capabilities:
            return
        if mode not in self.xtra_capabilities["economy"]:
            return
        if self.status["economy"] != mode:
            self.to_set["economy"] = mode

    def code_economy(self):
        if "economy" in self.to_set:
            mode = self.to_set["economy"]

            if mode == "off":
                return bytearray(b"\x88\xc0\x7f")
            elif mode == "80":
                return bytearray(b"\x88\xc0\x7d")
            elif mode == "60":
                return bytearray(b"\x88\xc0\x7e")
            elif mode == "40":
                return bytearray(b"\x88\xc0\x80")

        return bytearray()

    def set_cleaning(self, mode):
        if "cleaning" not in self.xtra_capabilities:
            return
        if mode not in self.xtra_capabilities["cleaning"]:
            return
        if self.status["cleaning"] != mode:
            self.to_set["cleaning"] = mode

    def code_cleaning(self):
        if "cleaning" in self.to_set:
            mode = self.to_set["cleaning"]

            if mode == "off":
                return bytearray(b"\x88\xc0\x0b")
            elif mode == "on":
                return bytearray(b"\x88\xc0\x0c")

        return bytearray()

    def set_diagnostic(self, mode):
        if "diagnostic" not in self.xtra_capabilities:
            return
        if mode not in self.xtra_capabilities["diagnostic"]:
            return
        if self.status["diagnostic"] != mode:
            self.to_set["diagnostic"] = mode

    def code_diagnostic(self):
        if "diagnostic" in self.to_set:
            mode = self.to_set["diagnostic"]
            self.to_set["diagnostic"] = "off"  # It is a request, not a toggle
            if mode == "on":
                return bytearray(b"\x88\xc0\xce")
        return bytearray()

    def set_mode(self, mode):
        if mode not in self.capabilities["mode"]:
            mode = "cool"
        if mode != self.status["mode"]:
            self.to_set["mode"] = mode

    def code_mode(self):
        if "mode" in self.to_set:
            mode = self.to_set["mode"]
        else:
            mode = self.status["mode"]

        mask = bytearray(b"\x88\x00\x00")
        if mode == "off":
            return bytearray(b"\x00\xc0\x05"), True
        if self.status["mode"] != "off":
            addit = 8
        else:
            addit = 0
        mask = bytearray(b"\x00\x00\x00")
        if mode == "auto":
            mask[1] = 3 + addit
        elif mode == "cool":
            mask[1] = addit
        elif mode == "dry":
            mask[1] = 1 + addit
        elif mode == "fan":
            mask[1] = 2 + addit

        return mask, False

    def build_code(self):
        frames = []
        packet = bytearray(self.FBODY)
        # Note that set mod must be last for it replaces values
        if {"mode", "temperature", "fan"}.intersection(set(self.to_set.keys())):
            for f in [self.code_temperature, self.code_fan, self.code_mode]:
                mask, replace = f()
                if replace:
                    packet = bytearray([y or x for x, y in zip(packet, mask)])
                else:
                    packet = bytearray([x | y for x, y in zip(packet, mask)])
            frames += [packet]
        if "mode" in self.to_set:
            mode = self.to_set["mode"]
        else:
            mode = self.status["mode"]
        if mode != "off":
            # print("Mode is {} from {}".format(mode, self.to_set))
            for prop in self.xtra_capabilities:
                # print("Looking at {} with {} and {}".format(prop,self.to_set,self.status))
                if prop in self.to_set and self.to_set[prop] != self.status[prop]:
                    f = getattr(self, "code_" + prop, None)
                    if f:
                        frames.append(f())
        return frames

    def _build_ircode(self):
        frames = []
        frames += self.build_code()
        idx = 0
        for x in frames:
            frames[idx] += self.crc(x)
            idx += 1
        return frames

    def crc(self, frame):
        crc = 0
        for x in frame:
            crc += (x & 0xF0) >> 4
            crc += x & 0x0F
        return ((crc & 0x0F) << 4).to_bytes(1, "big")


class InverterV(LG):
    def __init__(self):
        super().__init__()
        self.model = "Inverter V"
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry"],
            "temperature": [x for x in range(16, 30)],
            "auto_bias": ["-2", "-1", "default", "+1", "+2"],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
        }
        self.xtra_capabilities = {
            "swing": ["off", "swing", "90°", "0°"],
            "powerful": ["off", "on"],
            "cleaning": ["off", "on"],
            "economy": ["off", "80", "60", "40"],
        }
        self.status = {
            "mode": "off",
            "temperature": 25,
            "fan": "auto",
            "swing": "off",
            "auto_bias": "default",
            "powerful": "off",
            "cleaning": "off",
            "economy": "off",
        }


class DualInverter(LG):
    def __init__(self):
        super().__init__()
        self.model = "Dual Imverter"
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry"],
            "temperature": [x for x in range(16, 30)],
            "auto_bias": ["-2", "-1", "default", "+1", "+2"],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
        }
        self.xtra_capabilities = {
            "swing": ["off", "swing", "ceiling", "90°", "60°", "45°", "30°", "0°"],
            "hswing": [
                "off",
                "swing",
                "left",
                "centre left",
                "centre",
                "centre right",
                "right",
                "swing left",
                "swing right",
            ],
            "powerful": ["off", "on"],
            "purifier": ["off", "on"],
            "cleaning": ["off", "on"],
            "economy": ["off", "80", "60", "40"],
            "diagnostic": ["off", "on"],
        }
        self.status = {
            "mode": "off",
            "temperature": 25,
            "fan": "auto",
            "swing": "off",
            "auto_bias": "default",
            "powerful": "off",
            "purifier": "off",
            "cleaning": "off",
            "economy": "off",
            "diagnostic": "off",
        }


class LGv1(PulseBased):

    STARTFRAME = [8500, 4250]
    ENDFRAME = [400, 39750]
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [430, 1260]  # ditto

    def __init__(self):
        super().__init__("LG", variant=GE6711AR2853M)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [16, 25],
            "fan": ["auto", "high", "medium", "low", "lowest"],
            "swing": ["off", "auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": ["off", "on"],
            "light": ["off", "on"],
        }


class LGv2(PulseBased):

    STARTFRAME = [8500, 4250]
    ENDFRAME = [400, 39750]
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [430, 1260]  # ditto

    def __init__(self):
        super().__init__("LG", variant=LG6711A20083V)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [16, 25],
            "fan": ["auto", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "light": ["off", "on"],
        }


class LG2v1(PulseBased):

    STARTFRAME = [3200, 9900]
    ENDFRAME = [400, 39750]
    MARK = [480]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [430, 1260]  # ditto

    def __init__(self):
        super().__init__("LG2", variant=AKB75215403)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [16, 25],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": ["off", "on"],
            "light": ["off", "on"],
        }


class LG2v2(PulseBased):

    STARTFRAME = [3200, 9900]
    ENDFRAME = [400, 39750]
    MARK = [480]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [430, 1260]  # ditto

    def __init__(self):
        super().__init__("LG2", variant=AKB74955603)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [16, 25],
            "fan": ["auto", "high", "medium", "low", "lowest"],
            "swing": ["off", "auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": ["off", "on"],
            "light": ["off", "on"],
        }


class LG2v3(PulseBased):

    STARTFRAME = [3200, 9900]
    ENDFRAME = [400, 39750]
    MARK = [480]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [430, 1260]  # ditto

    def __init__(self):
        super().__init__("LG2", variant=AKB73757604)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [16, 25],
            "fan": ["auto", "high", "medium", "low", "lowest"],
            "swing": ["off", "auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": ["off", "on"],
            "light": ["off", "on"],
        }


DEVICES = {}


# ------------------------------------------------------------------ LgAc
# Layout from IRremoteESP8266's LGProtocol (ir_LG.h): one 28-bit word, sent
# MSB first (IRsend::sendLG: sendGeneric with kLgHdrMark/kLgHdrSpace,
# kLgBitMark, kLgOneSpace/kLgZeroSpace, MSBfirst). As logical bytes the word
# is (raw << 4) big-endian: byte 0 is Sign, byte 1 holds Power, the unnamed
# bits and Mode, byte 2 Temp and Fan, and the top nibble of byte 3 is Sum;
# the low nibble of byte 3 is not sent (nbits=28). IRLgAc::send sends the
# state word, then, for LG6711A20083V only, the swing word when it changed;
# each word is a separate burst with the same timings. No repeat
# (kLgDefaultRepeat is kNoRepeat). Carrier 38 kHz (sendGeneric's 38).

LG_AC = Protocol(
    "lg-ac",
    {
        "main": Section(
            PulseDistance(550, 550, 1600),  # kLgBitMark/kLgZeroSpace/kLgOneSpace
            header=(8500, 4250),  # kLgHdrMark, kLgHdrSpace
            footer=(550,),  # kLgBitMark
            # sendGeneric's space(max(kLgMinGap, kLgMinMessageLength -
            # elapsed)): the C build's timer does not advance, so the oracle
            # records the whole kLgMinMessageLength.
            gap=108050,
            lsb_first=False,
        )
    },
    carrier=38000,
)


LG_AC_SIGNATURE = 0x88  # kLgAcSignature
LG_AC_TEMP_ADJUST = 15  # kLgAcTempAdjust: Temp = celsius - 15
LG_AC_MIN_TEMP, LG_AC_MAX_TEMP = 16, 30  # kLgAcMinTemp, kLgAcMaxTemp
LG_AC_MODE = {  # kLgAc{Cool,Dry,Fan,Auto,Heat}
    "cool": 0b000,
    "dry": 0b001,
    "fan": 0b010,
    "auto": 0b011,
    "heat": 0b100,
}
LG_AC_FAN = {  # canonical fan -> the Fan value IRLgAc::setFan stores
    "auto": 5,  # kLgAcFanAuto (kAuto)
    "1": 0,  # lowest: kLgAcFanLowest (kMin)
    "2": 1,  # low: kLgAcFanLow (kLow)
    "3": 2,  # medium: kLgAcFanMedium (kMedium)
    # high: convertFan gives kLgAcFanHigh, which setFan turns into
    # kLgAcFanMax on every model but AKB74955603 (a designed mapping).
    "4": 4,
}
LG_AC_POWER = {"on": 0b00, "off": 0b11}  # kLgAcPowerOn, kLgAcPowerOff
LG_AC_OFF_COMMAND = 0x88C0051  # kLgAcOffCommand
LG_AC_SWINGV_TOGGLE = 0x8810001  # kLgAcSwingVToggle (LG6711A20083V)


def lg_ac_word(raw):
    """The logical bytes of a 28-bit LG word (sent MSB first)."""
    return (raw << 4).to_bytes(4, "big")


# Skeleton: Sign kLgAcSignature, everything else (and Sum) clear. The C
# object never carries stale bits: stateReset loads kLgAcOffCommand and
# every message is either that constant or setRaw'd state plus setters.
LG_AC_LAYOUT = Layout(
    bytes([LG_AC_SIGNATURE, 0, 0, 0]),
    {
        "sign": Field.at(0, 0, 8),  # raw bits 20-27
        "power": Field.at(1, 6, 2, values=LG_AC_POWER),  # raw bits 18-19
        # The struct's unnamed 3 bits (raw bits 15-17). C never sets them in
        # a state word; special words use them (kLgAcSwingVToggle has bit 16),
        # and real LG remotes set bit 15 (see the tests).
        "unused": Field.at(1, 3, 3),
        "mode": Field.at(1, 0, 3, values=LG_AC_MODE),  # raw bits 12-14
        "temp": Field.at(2, 4, 4),  # raw bits 8-11: celsius - kLgAcTempAdjust
        "fan": Field.at(2, 0, 4, values=LG_AC_FAN),  # raw bits 4-7
    },
    checksum=HighNibbleSum(1, 3, 3),  # IRLgAc::calcChecksum
)


_LG_AC_BASE = dict(
    modes=("auto", "cool", "fan", "dry", "heat"),
    temperature=TemperatureRange(16.0, 25.0),
    fan=Choice(
        ("auto", "1", "2", "3", "4"),
        {"auto": "auto", "1": "lowest", "2": "low", "3": "medium", "4": "high"},
    ),
    swing_h=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
    features={"light": Choice((False, True), {False: "off", True: "on"})},
)
LG_AC_CAPABILITIES = {  # variant -> the legacy entity (LGv2 / LGv1)
    "LG6711A20083V": Capabilities(
        swing_v=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
        **_LG_AC_BASE,
    ),
    # The legacy LGv1 entity offers swing positions, but IRLgAc::send sends
    # no swing word for GE6711AR2853M (its default case): they send nothing.
    "GE6711AR2853M": Capabilities(
        swing_v=Choice(
            ("off", "auto", "1", "2", "3", "4", "5"),
            {
                "off": "off",
                "auto": "auto",
                "1": "90°",
                "2": "60°",
                "3": "45°",
                "4": "30°",
                "5": "0°",
            },
        ),
        **_LG_AC_BASE,
    ),
}


class LgAcDevice(Device):
    """LG 28-bit A/C (IRLgAc, protocol LG): a full-state word, plus a swing
    toggle word for the LG6711A20083V remote.

    The variant (an lg_ac_remote_model_t name: LG6711A20083V, or
    GE6711AR2853M for the "ge" plugin's models) comes from the model
    (LG_AC_MODEL_VARIANT) unless given, and picks the capabilities (the
    legacy LGv2 / LGv1 entities). The variants share the state word.

    Power off sends only kLgAcOffCommand, whatever the other settings
    (IRLgAc::send). Light and horizontal swing send nothing for either
    variant: IRLgAc::send sends the light toggle for AKB74955603 and the
    SwingH words for AKB73757604 only.

    Swing: GE6711AR2853M sends no swing word at all. LG6711A20083V has one
    vertical swing button: IRac::lg sends kLgAcSwingVToggle when the swing
    changes between off and not-off, comparing with the previous state
    IRac::sendAc passes (prev->swingv, kOff without one);
    IRac::handleToggles has no LG case, the rule lives in IRac::lg. The port
    does the same: with ``previous`` the toggle word follows the state word
    when the swing changes, without it when the target swing is on. No
    toggle word goes with an off message.
    """

    PROTOCOL = LG_AC
    # One layout per word: the toggle word, when sent, reads with it too.
    LAYOUTS = (LG_AC_LAYOUT,)
    capabilities = LG_AC_CAPABILITIES["LG6711A20083V"]

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        self.variant = variant or LG_AC_MODEL_VARIANT.get(model, "LG6711A20083V")
        if self.variant not in LG_AC_CAPABILITIES:
            raise ValueError(f"unknown LG A/C variant {self.variant!r}")
        self.capabilities = LG_AC_CAPABILITIES[self.variant]

    def frames(self, previous, target, actions):
        if not target.power:
            return [Frame("main", lg_ac_word(LG_AC_OFF_COMMAND), 28)]
        temperature = min(max(int(target.temperature), LG_AC_MIN_TEMP), LG_AC_MAX_TEMP)
        data = LG_AC_LAYOUT.build(
            sign=LG_AC_SIGNATURE,
            power="on",
            mode=target.mode,
            temp=temperature - LG_AC_TEMP_ADJUST,
            fan=target.fan,
        )
        frames = [Frame("main", bytes(data), 28)]
        if self.variant != "LG6711A20083V":
            return frames
        was_swinging = previous is not None and previous.swing_v != "off"
        if (target.swing_v != "off") != was_swinging:
            # The documented toggle word. The old glue never passed swing
            # "on" to C (declared as a Defect in the tests).
            frames.append(Frame("main", lg_ac_word(LG_AC_SWINGV_TOGGLE), 28))
        return frames


LG_AC_MODEL_VARIANT = {  # model -> remote variant (lg_ac_remote_model_t)
    "6711A20083V  remote": "LG6711A20083V",
    "TS-H122ERM1  remote": "LG6711A20083V",
    "AG1BH09AW101": "GE6711AR2853M",  # ge plugin
    "6711AR2853M Remote": "GE6711AR2853M",  # ge plugin
}
LG_AC_MODELS = ("6711A20083V  remote", "TS-H122ERM1  remote")  # lg plugin
LG_AC_GE_MODELS = ("AG1BH09AW101", "6711AR2853M Remote")  # ge plugin


DEVICES.update({m: LgAcDevice for m in LG_AC_MODELS})


# ------------------------------------------------------------------- Lg2
# Layout from IRremoteESP8266's LGProtocol (ir_LG.h): one 28-bit word, sent
# MSB first by sendLG2 (sendGeneric: kLg2HdrMark/kLg2HdrSpace header,
# kLg2BitMark, kLgOneSpace/kLgZeroSpace, a kLg2BitMark footer; 38 kHz).
# The word is held in Frame.data as 4 bytes, the last nibble unused:
#   byte 0: Sign (kLgAcSignature 0x88)
#   byte 1: Power (bits 6-7), unnamed (bits 3-5), Mode (bits 0-2)
#   byte 2: Temp (bits 4-7), Fan (bits 0-3)
#   byte 3: Sum (bits 4-7)
# Settings the state word cannot carry (swing, light) are separate "special"
# words (kLgAc*Command/Toggle, kLgAcSwing*, kLgAcVaneSwingVBase + ...), each
# a frame of its own, all with the same Sign and Sum.
#
# The gap closing each word is kLgMinMessageLength (108 050 µs): sendGeneric
# spaces max(kLgMinGap, message length - elapsed), and the C library's timing
# recorder (the oracle) elapses no time, so every word is followed by the
# full message length.

LG2 = Protocol(
    "lg2",
    {
        "main": Section(
            PulseDistance(480, 550, 1600),  # kLg2BitMark, kLgZeroSpace/OneSpace
            header=(3200, 9900),  # kLg2HdrMark, kLg2HdrSpace
            footer=(480,),  # kLg2BitMark
            gap=108050,  # kLgMinMessageLength, as recorded
            lsb_first=False,
        )
    },
    carrier=38000,
)
LG2_NBITS = 28  # kLgBits


def _lg2_command(code):
    """A 28-bit special word (ir_LG.h constant) -> the 16 bits of bytes 1-2,
    as the "command" field stores them (byte 1 low, byte 2 high)."""
    return ((code >> 12) & 0xFF) | ((code >> 4) & 0xFF) << 8


LG2_VANE_POSITION = {  # kLgAcVaneSwingV*
    "highest": 1,
    "high": 2,
    "upper_middle": 3,
    "middle": 4,
    "low": 5,
    "lowest": 6,
}
LG2_COMMANDS = {
    "off": _lg2_command(0x88C0051),  # kLgAcOffCommand
    "light_toggle": _lg2_command(0x88C00A6),  # kLgAcLightToggle
    "swing_v_toggle": _lg2_command(0x8810001),  # kLgAcSwingVToggle
    "swing_v_lowest": _lg2_command(0x8813048),  # kLgAcSwingVLowest
    "swing_v_low": _lg2_command(0x8813059),  # kLgAcSwingVLow
    "swing_v_middle": _lg2_command(0x881306A),  # kLgAcSwingVMiddle
    "swing_v_upper_middle": _lg2_command(0x881307B),  # kLgAcSwingVUpperMiddle
    "swing_v_high": _lg2_command(0x881308C),  # kLgAcSwingVHigh
    "swing_v_highest": _lg2_command(0x881309D),  # kLgAcSwingVHighest
    "swing_v_swing": _lg2_command(0x8813149),  # kLgAcSwingVSwing (= Auto)
    "swing_v_off": _lg2_command(0x881315A),  # kLgAcSwingVOff
    "swing_h_auto": _lg2_command(0x881316B),  # kLgAcSwingHAuto
    "swing_h_off": _lg2_command(0x881317C),  # kLgAcSwingHOff
    # IRLgAc::calcVaneSwingV: kLgAcVaneSwingVBase (0x8813200) +
    # ((vane * kLgAcVaneSwingVSize + position) << 4), for the
    # kLgAcSwingVMaxVanes (4) vanes.
    **{
        f"vane{vane}_{name}": _lg2_command(0x8813200 + ((vane * 8 + pos) << 4))
        for vane in range(4)
        for name, pos in LG2_VANE_POSITION.items()
    },
}
LG2_MODE = {"cool": 0, "dry": 1, "fan": 2, "auto": 3, "heat": 4}  # kLgAc*
LG2_FAN = {  # kLgAcFan*
    "lowest": 0,
    "low": 1,
    "medium": 2,
    "max": 4,
    "auto": 5,
    "low_alt": 9,
    "high": 10,
}
LG2_MIN_TEMP, LG2_MAX_TEMP = 16, 30  # kLgAcMinTemp, kLgAcMaxTemp
LG2_TEMP_ADJUST = 15  # kLgAcTempAdjust

# Skeleton: Sign = kLgAcSignature, the rest cleared. IRLgAc::stateReset
# starts from kLgAcOffCommand, whose unnamed bits (byte 1, bits 3-5) are 0
# and which no setter writes, so no bit comes from stale memory. The device
# never sets "unnamed" (C sends 0).
LG2_LAYOUT = Layout(
    bytes([0x88, 0, 0, 0]),
    {
        "power": Field.at(1, 6, 2, values={True: 0, False: 3}),  # kLgAcPowerOn/Off
        # LGProtocol's unnamed bits. Real AKB74955603 words set bit 3; C
        # never writes them, so they keep kLgAcOffCommand's 0.
        "unnamed": Field.at(1, 3, 3),
        "mode": Field.at(1, 0, 3, values=LG2_MODE),
        "temperature": Field.at(  # Temp: degrees - kLgAcTempAdjust
            2,
            4,
            4,
            values={
                t: t - LG2_TEMP_ADJUST for t in range(LG2_MIN_TEMP, LG2_MAX_TEMP + 1)
            },
        ),
        "fan": Field.at(2, 0, 4, values=LG2_FAN),
    },
    checksum=HighNibbleSum(1, 3, 3),  # IRLgAc::calcChecksum
)
# The special words: Sign, a 16-bit command, Sum.
LG2_COMMAND_LAYOUT = Layout(
    bytes([0x88, 0, 0, 0]),
    {"command": Field.at(1, 0, 16, values=LG2_COMMANDS)},
    checksum=HighNibbleSum(1, 3, 3),  # IRLgAc::calcChecksum
)

LG2_FAN_BY_VARIANT = {  # canonical fan -> kLgAcFan*, as IRLgAc::setFan stores it
    # AKB75215403: convertFan(kHigh) = kLgAcFanHigh, which setFan turns into
    # kLgAcFanMax on any model but AKB74955603; kMax is kLgAcFanMax too.
    "AKB75215403": {
        "auto": "auto",
        "1": "lowest",
        "2": "low",
        "3": "medium",
        "4": "max",
        "5": "max",
    },
    # AKB74955603: setFan keeps kLgAcFanHigh and turns low into kLgAcFanLowAlt.
    "AKB74955603": {
        "auto": "auto",
        "1": "lowest",
        "2": "low_alt",
        "3": "medium",
        "4": "high",
    },
    "AKB73757604": {
        "auto": "auto",
        "1": "lowest",
        "2": "low",
        "3": "medium",
        "4": "max",
    },
}
LG2_SWING_V = {  # canonical swing -> kLgAcSwingV* (AKB74955603), top to bottom
    "off": "swing_v_off",
    "auto": "swing_v_swing",  # convertSwingV(kAuto): kLgAcSwingVSwing
    "1": "swing_v_highest",  # 90°: the topmost documented position
    "2": "swing_v_high",  # 60°
    "3": "swing_v_middle",  # 45°
    "4": "swing_v_low",  # 30°
    "5": "swing_v_lowest",  # 0°
}
LG2_VANE = {  # canonical swing -> kLgAcVaneSwingV* (AKB73757604)
    # convertVaneSwingV has no off or auto: both fall to its default, Highest.
    "off": "highest",
    "auto": "highest",
    "1": "highest",  # 90°: the topmost documented position
    "2": "high",  # 60°
    "3": "middle",  # 45°
    "4": "low",  # 30°
    "5": "lowest",  # 0°
}


def _lg2_capabilities(fan_names):
    return Capabilities(
        modes=("auto", "cool", "fan", "dry", "heat"),
        temperature=TemperatureRange(16.0, 25.0),
        fan=Choice(
            ("auto",) + tuple(str(i) for i in range(1, len(fan_names) + 1)),
            {"auto": "auto", **{str(i): n for i, n in enumerate(fan_names, 1)}},
        ),
        swing_v=Choice(
            ("off", "auto", "1", "2", "3", "4", "5"),
            {
                "off": "off",
                "auto": "auto",
                "1": "90°",
                "2": "60°",
                "3": "45°",
                "4": "30°",
                "5": "0°",
            },
        ),
        swing_h=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
        features={"light": Choice((False, True), {False: "off", True: "on"})},
    )


LG2_CAPABILITIES = {
    "AKB75215403": _lg2_capabilities(("lowest", "low", "medium", "high", "highest")),
    "AKB74955603": _lg2_capabilities(("lowest", "low", "medium", "high")),
    "AKB73757604": _lg2_capabilities(("lowest", "low", "medium", "high")),
}


class Lg2Device(Device):
    """LG2 (28-bit LG protocol, remotes AKB75215403, AKB74955603 and
    AKB73757604, lg_ac_remote_model_t): a state word plus, depending on the
    remote, special words for swing and light, as IRac::lg / IRLgAc::send
    send them.

    The variant comes from the model (LG2_MODELS) unless given, so the
    registry's ``cls(brand, model)`` call picks it; unknown models get
    AKB75215403, the model IRLgAc::setRaw assumes for LG2.

    Power off is always the single kLgAcOffCommand word, whatever the mode,
    setpoint or variant. Power on sends the state word (Power on, Mode,
    Temp, Fan), then:
    - AKB75215403: nothing else. IRLgAc::send has no swing or light for it,
      so swing_v, swing_h and light (in the legacy entity) have no effect.
    - AKB74955603: the swing_v word when the swing differs from the previous
      one, then kLgAcLightToggle when light is off (every state word turns
      the light on, ir_LG.cpp). swing_h is not sent (as C).
    - AKB73757604: one kLgAcVaneSwingV word per vane (4) for swing_v, then
      kLgAcSwingHAuto/Off. light is not sent (as C).

    ``previous``, as the C path:
    - The swing_v word (AKB74955603) goes only when its code differs from
      the previous swing's: IRac::sendAc passes prev->swingv and IRac::lg
      seeds IRLgAc's previous swing with it, and IRLgAc::send compares. A
      fresh IRac's previous state has swing off, so without ``previous`` the
      word goes when swing_v is not "off". The port matches C in both cases.
      (IRac::handleToggles has no LG case: this rule is in IRac::lg/send.)
    - The vane words are sent every time: IRLgAc::send only sends vanes that
      changed, but IRac::lg never seeds the previous vanes (they stay 0, an
      unused position), so every vane always counts as changed.
    - The swing_h word (AKB73757604) goes without ``previous`` (as every
      fresh C message recorded, and as the vane words), and with
      ``previous`` only when swing_h changed. IRLgAc::send means that rule
      (it compares _swingh with _swingh_prev) but nothing ever writes
      _swingh_prev, so C compares with stale memory and in practice sends
      the word every time; stale memory is not a reference (house rule 3a),
      so the port deliberately applies the documented change rule.
    - light: no previous state is used, as C: the toggle goes whenever light
      is off. It is a real toggle, but IRLgAc::send only sends it right after
      a state word, which always turns the light on (ir_LG.cpp, issue 1513),
      so each message leaves the light as asked; toggling only on change
      would leave it on.

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_lg2_device.py):
    - swing_v "1"/"2" (90°/60°): the glue maps them to kHigh/kUpperMiddle;
      convertSwingV sends kLgAcSwingVHigh for kHigh and has no kUpperMiddle
      case (kLgAcSwingVOff, so no swing word at all), and convertVaneSwingV
      sends High for kHigh and Highest for kUpperMiddle. The port sends
      Highest/High (canonical "1" is the topmost documented position).
    - swing_h "swing" (the legacy "on"): IRGHVAC.trans_hswing has no "on",
      so C sends kLgAcSwingHOff; the port sends kLgAcSwingHAuto.
    """

    PROTOCOL = LG2
    LAYOUTS = (LG2_LAYOUT, LG2_COMMAND_LAYOUT)

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        self.variant = variant or LG2_MODELS.get(model, "AKB75215403")
        if self.variant not in LG2_CAPABILITIES:
            raise ValueError(f"unknown LG2 variant {self.variant!r}")
        self.capabilities = LG2_CAPABILITIES[self.variant]

    @staticmethod
    def _word(layout, **values):
        return Frame("main", bytes(layout.build(**values)), LG2_NBITS)

    def _command(self, name):
        return self._word(LG2_COMMAND_LAYOUT, command=name)

    def frames(self, previous, target, actions):
        if not target.power:
            # IRLgAc::send: "Always send the special Off command".
            return [self._command("off")]
        frames = [
            self._word(
                LG2_LAYOUT,
                power=True,
                mode=target.mode,
                temperature=int(target.temperature),
                fan=LG2_FAN_BY_VARIANT[self.variant][target.fan],
            )
        ]
        if self.variant == "AKB74955603":
            before = "off" if previous is None else previous.swing_v
            if LG2_SWING_V[target.swing_v] != LG2_SWING_V[before]:
                frames.append(self._command(LG2_SWING_V[target.swing_v]))
            if not target.features["light"]:  # must be sent last
                frames.append(self._command("light_toggle"))
        elif self.variant == "AKB73757604":
            position = LG2_VANE[target.swing_v]
            frames += [self._command(f"vane{v}_{position}") for v in range(4)]
            if previous is None or previous.swing_h != target.swing_h:
                frames.append(
                    self._command(
                        "swing_h_auto" if target.swing_h == "swing" else "swing_h_off"
                    )
                )
        return frames


LG2_MODELS = {  # model -> remote (lg_ac_remote_model_t), as the old LG2v1-3
    "AKB74395308  remote": "AKB75215403",
    "S4-W12JA3AA": "AKB75215403",
    "AKB75215403  remote": "AKB75215403",
    "AKB74955603  remote": "AKB74955603",
    "A4UW30GFA2": "AKB74955603",
    "AMNW09GSJA0": "AKB74955603",
    "AKB73315611  remote": "AKB74955603",
    "MS05SQ NW0": "AKB74955603",
    "AMNW24GTPA1": "AKB73757604",
    "AKB73757604  remote": "AKB73757604",
}


DEVICES.update({m: Lg2Device for m in LG2_MODELS})


class PluginObject(GenPluginObject):

    MODELS = {
        "generic": LG,
        "inverter v": InverterV,
        "dual inverter": DualInverter,
        "6711A20083V  remote": LGv2,
        "TS-H122ERM1  remote": LGv2,
        "AKB74395308  remote": LG2v1,
        "S4-W12JA3AA": LG2v1,
        "AKB75215403  remote": LG2v1,
        "AKB74955603  remote": LG2v2,
        "A4UW30GFA2": LG2v2,
        "AMNW09GSJA0": LG2v2,
        "AMNW24GTPA1": LG2v3,
        "AKB73757604  remote": LG2v3,
        "AKB73315611  remote": LG2v2,
        "MS05SQ NW0": LG2v2,
    }

    def __init__(self):
        self.brand = "lg"


def main():

    import argparse
    import base64

    parser = argparse.ArgumentParser(description="Generate LG A/C codes.")
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
        default="cool",
        help="Mode to set. (default 'cool').",
    )
    parser.add_argument(
        "-f",
        "--fan",
        choices=["auto", "highest", "high", "medium", "low", "lowest"],
        default="auto",
        help="Fan mode. (default 'auto').",
    )
    parser.add_argument(
        "-s",
        "--swing",
        choices=["off", "swing", "90°", "0°"],
        default="off",
        help="Swing mode. (default 'off').",
    )
    parser.add_argument(
        "-e",
        "--economy",
        choices=["off", "80", "60", "40"],
        default="off",
        help="Economy mode. (default 'off').",
    )
    parser.add_argument(
        "-A",
        "--bias",
        choices=["-2", "-1", "default", "1", "2"],
        default="default",
        help="Auto mode temperature bias. (default 'default').",
    )
    parser.add_argument(
        "-P", "--purifier", action="store_true", default=False, help="Set plasma"
    )
    parser.add_argument(
        "-p", "--powerful", action="store_true", default=False, help="Set powerful"
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
        help="Output Broadlink timing in base64 encoded",
    )

    try:
        opts = parser.parse_args()
    except Exception as e:
        parser.error("Error: " + str(e))

    if opts.list:
        print(f"Available models are: {PluginObject().MODELS.keys()}")

    device = PluginObject().get_device(opts.model)
    frames = []
    device.set_temperature(opts.temp)
    device.set_fan(opts.fan)
    device.set_swing(opts.swing)
    device.set_powerful((opts.powerful and "on") or "off")
    device.set_auto_bias(opts.bias)
    device.set_economy(opts.economy)
    device.set_purifier((opts.purifier and "on") or "off")
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
            print(" ".join([hex(x) for x in f]))


if __name__ == "__main__":
    main()
