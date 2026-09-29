#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Sharp AC IR commands as done by the CRMC-B028JBEZ and others
#
# This module  is in part based on the work/code from:
#      ToniA      https://github.com/adafruit/Raw-IR-decoder-for-Arduino/pull/3/commits/887ed4204711c0b911571f3090b7fd066e93f006
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

from dataclasses import dataclass, replace

from .hvaclib import HVAC, PulseBased, GenPluginObject
from ..choices import FAN_3, ON_OFF
from ..device import Device
from ..fields import Checksum, Field, Layout
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import BOOL, Capabilities, Choice, TemperatureRange
from .kelvinator import KELVINATOR_SHARP_MODELS, Kelvinator, KelvinatorDevice

try:
    from ..irhvac import A907, A903, A705
except ImportError:
    # Only the C-backed classes use these; keep the pure-Python ones importable.
    A907 = A903 = A705 = None


SHARP_NATIVE = Protocol(
    "sharp",
    {
        "main": Section(
            PulseDistance(435, 435, 1400),
            header=(3800, 1900),
            footer=(435,),
            gap=10000,
            lsb_first=True,
        )
    },
)


class Sharp(HVAC):
    """Generic Sharp HVAC object. It must have, at the very minimum
    "mode" and "temperature" capabilities"""

    PROTOCOL = SHARP_NATIVE

    def __init__(self):
        super().__init__()
        self.brand = "Sharp"
        self.model = "Generic"
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry"],
            "temperature": [x for x in range(18, 38)],
        }
        # For functions that require their own frames
        self.xtra_capabilities = {}
        self.status = {"mode": "cool", "temperature": 25, "economy": "off"}

        self.to_set = {}
        self.FBODY = b"\xaa\x5a\xcf\x10\x00\x00\x00\x00\x00\x80\x00\xe0"
        self.crc_special = 0x01

    def set_temperature(self, temp):
        if temp < self.capabilities["temperature"][0]:
            temp = self.capabilities["temperature"][0]
        elif temp > self.capabilities["temperature"][-1]:
            temp = self.capabilities["temperature"][-1]
        if self.status["temperature"] != temp:
            self.to_set["temperature"] = temp

    def code_temperature(self):
        if "temperature" in self.to_set:
            temp = self.to_set["temperature"]
            if "mode" in self.to_set and self.to_set["mode"] != "cool":
                temp = 17
            elif self.status["mode"] != "cool":
                temp = 17
            else:
                if "mode" in self.to_set and self.to_set["mode"] != "cool":
                    temp = 17
                else:
                    temp = self.status["temperature"]
        else:
            temp = self.status["temperature"]
        mask = bytearray(b"\x00" * len(self.FBODY))
        mask[6] = temp - 17
        return mask, False

    def set_fan(self, mode):
        if "fan" not in self.capabilities:
            return
        if mode not in self.capabilities["fan"]:
            return
        if self.status["fan"] != mode:
            self.to_set["fan"] = mode

    def code_fan(self):
        """mode is one of auto, lowest, low, medium, high, highest"""
        if "mode" in self.to_set and self.to_set["mode"] == "dry":
            mode = "auto"
            self.to_set["fan"] = mode
        elif self.status["mode"] == "dry":
            mode = "auto"
            self.to_set["fan"] = mode
        else:
            if "fan" in self.to_set:
                mode = self.to_set["fan"]
            else:
                if "fan" in self.capabilities:
                    mode = self.status["fan"]
                else:
                    mode = None
        rank = ["auto", "low", "lowest", "medium", "high", "highest"]
        mask = bytearray(b"\x00" * len(self.FBODY))
        if mode:
            fval = (rank.index(mode) + 2) << 4
            mask[6] = fval
        return mask, False

    def set_swing(self, mode):
        if "swing" not in self.capabilities:
            return
        if mode not in self.capabilities["swing"]:
            return
        if self.status["swing"] != mode:
            self.to_set["swing"] = mode

    def code_swing(self):
        if "swing" in self.to_set:
            mode = self.to_set["swing"]
        else:
            if "swing" in self.capabilities:
                mode = self.status["swing"]
            else:
                mode = False

        rank = ["auto", "ceiling", "90°", "60°", "45°", "30°" "swing"]
        if mode not in rank:
            mode = "auto"  # Just in case
        mask = bytearray(b"\x00" * len(self.FBODY))
        fval = rank.index(mode) + 8
        mask[8] = fval
        return mask, False

    def set_powerful(self, mode="off"):
        # print("\n\nSharp set powerful {}\n\n".format(mode))
        if "powerful" not in self.status:
            return

        if "powerful" in self.capabilities:
            checkwith = self.capabilities
        elif "powerful" in self.xtra_capabilities:
            checkwith = self.xtra_capabilities
        # print("Setting powerful as {} from {}".format(mode,checkwith))
        if mode not in checkwith["powerful"]:
            return
        if self.status["powerful"] != mode:
            self.to_set["powerful"] = mode

    def code_powerful(self, toggle=False):
        b10code = 0x00
        if toggle:
            if "powerful" in self.to_set:
                b10code = 0x01

        mask = bytearray(b"\x00" * len(self.FBODY))
        mask[10] = b10code
        # Nothing to set... I know... it's the mode that will do this
        return mask, False

    def set_economy(self, mode="off"):
        if "economy" not in self.status:
            return

        if "exonomy" in self.capabilities:
            checkwith = self.capabilities
        elif "economy" in self.xtra_capabilities:
            checkwith = self.xtra_capabilities

        if mode not in checkwith["economy"]:
            return
        if self.status["economy"] != mode:
            self.to_set["economy"] = mode

    def code_economy(self, toggle=False):
        if not toggle:
            mode = self.status["economy"]
        elif "economy" in self.to_set:
            mode = self.to_set["economy"]
        else:
            if "economy" not in self.status:
                mode = "off"
            else:
                mode = self.status["economy"]

        mask = bytearray(b"\x00" * len(self.FBODY))
        if mode == "on":
            mask[11] |= 0x10
        return mask, False

    def set_purifier(self, mode="off"):
        if "purifier" not in self.capabilities:
            return
        if mode not in self.capabilities["purifier"]:
            return
        if self.status["purifier"] != mode:
            self.to_set["purifier"] = mode

    def code_purifier(self):

        mask = bytearray(b"\x00" * len(self.FBODY))

        return mask, False

    def set_mode(self, mode):
        if mode not in self.capabilities["mode"]:
            mode = "cool"
        if mode != self.status["mode"]:
            self.to_set["mode"] = mode

    def code_mode(self, option=None):
        if "mode" in self.to_set:
            mode = self.to_set["mode"]
        else:
            mode = self.status["mode"]

        mask = bytearray(b"\x00" * len(self.FBODY))
        if option is None or mode == "off":
            if mode != self.status["mode"]:
                if mode == "off":
                    b5val = 0x21
                    b6mode = self.status["mode"]
                elif self.status["mode"] == "off":
                    b5val = 0x11
                    b6mode = mode
                else:
                    b5val = 0x31
                    b6mode = mode
            else:
                b5val = 0x31
                b6mode = mode if mode != "off" else "cool"
        else:
            # Caller should not send option if off
            if option == "on":
                b5val = 0x61
            else:
                b5val = 0x71
            b6mode = mode
        mask[5] = b5val
        mask[6] = ["auto", "heat", "cool", "dry"].index(b6mode)
        return mask, False

    def build_code(self, withmode=True):
        packet = bytearray(self.FBODY)
        # Note that set mod must be last for it replaces values
        if withmode:
            lof = [
                self.code_temperature,
                self.code_fan,
                self.code_swing,
                self.code_purifier,
                self.code_economy,
                self.code_mode,
            ]
        else:
            lof = [
                self.code_temperature,
                self.code_fan,
                self.code_swing,
                self.code_purifier,
                self.code_economy,
            ]
        for f in lof:
            mask, replace = f()
            if replace:
                packet = bytearray([y or x for x, y in zip(packet, mask)])
            else:
                packet = bytearray([x | y for x, y in zip(packet, mask)])
        return packet

    def _build_ircode(self):
        frames = []
        normalframe = False
        for x in self.capabilities:
            if x in self.to_set:
                normalframe = True
                break
        if normalframe:
            frames += [self.build_code()]

        if ("mode" in self.to_set and (self.to_set["mode"] != "off")) or self.status[
            "mode"
        ] != "off":
            for prop in self.xtra_capabilities:
                # print("Looking at {} with {} and {}".format(prop,self.to_set,self.status))
                if prop in self.to_set and self.to_set[prop] != self.status[prop]:
                    f = getattr(self, "code_" + prop, None)
                    if f:
                        packet = self.build_code(withmode=False)
                        for mask, replace in [
                            self.code_mode(option=self.to_set[prop]),
                            f(toggle=True),
                        ]:
                            if replace:
                                packet = bytearray(
                                    [y or x for x, y in zip(packet, mask)]
                                )
                            else:
                                packet = bytearray(
                                    [x | y for x, y in zip(packet, mask)]
                                )
                        frames.append(packet)
        else:
            # We are off, so xtra_capabilities should also be off
            for x in self.xtra_capabilities:
                self.to_set[x] = "off"
        idx = 0
        for x in frames:
            frames[idx] += self.crc(x)
            idx += 1
        return frames

    def crc(self, frame):
        crc = 0
        for x in frame:
            crc ^= x
        crc ^= self.crc_special
        crc ^= crc >> 4
        crc = (crc & 0x0F) << 4
        crc += self.crc_special
        return crc.to_bytes(1, "big")


class JTech(Sharp):
    def __init__(self):
        super().__init__()
        self.model = "FTM-PV2S"
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry"],
            "temperature": [x for x in range(14, 30)],
            "fan": ["auto", "highest", "medium", "low", "lowest"],
            "swing": ["auto", "ceiling", "90°", "60°", "45°", "30°", "swing"],
            "hswing": ["left", "middle", "right", "swing"],
            "target": [
                "off",
                "close left",
                "close middle",
                "close right",
                "far left",
                "far middle",
                "far right",
            ],
            "purifier": ["off", "on"],
        }
        self.xtra_capabilities = {"powerful": ["off", "on"], "economy": ["off", "on"]}
        self.status = {
            "mode": "off",
            "temperature": 25,
            "fan": "auto",
            "swing": "auto",
            "hswing": "middle",
            "target": "off",
            "purifier": "off",
            "economy": "off",
            "powerful": "off",
        }
        self.temperature_step = 0.5

    def code_purifier(self):

        mask = bytearray(b"\x00" * len(self.FBODY))

        if "purifier" in self.to_set:
            mode = self.to_set["purifier"]
        else:
            mode = self.status["purifier"]
        if mode == "on":
            mask[11] |= 0x04

        # Nothing to set... I know... it's the mode that will do this
        return mask, False

    def code_swing(self):
        """This one takes care of "swing", "horizontal swing" and "spot" (AKA target"""
        if ("target" in self.to_set and self.to_set["target"] == "off") or self.status[
            "target"
        ] == "off":
            # OK, swing and horizontal swing are on
            if "swing" in self.to_set:
                smode = self.to_set["swing"]
            else:
                smode = self.status["swing"]
            if "hswing" in self.to_set:
                hsmode = self.to_set["hswing"]
            else:
                hsmode = self.status["hswing"]
            b8val = (["", "middle", "left", "right"] + 11 * [""] + ["swing"]).index(
                hsmode
            ) << 4
            b8val += 8 + ["auto", "ceiling", "90°", "60°", "45°", "30°", "swing"].index(
                smode
            )
            b9val = 0x0
        else:
            # Target is on
            b9val = 0x01
            front, side = (
                ("target" in self.to_set and self.to_set["target"])
                or self.status["target"]
            ).split(" ")
            b8val = (["", "middle", "left", "right"]).index(side) << 4
            if front == "close":
                b8val += 0xC
            else:
                b8val += 0x9

        mask = bytearray(b"\x00" * len(self.FBODY))
        mask[9] |= b9val
        mask[8] = b8val
        return mask, False

    def set_hswing(self, mode):
        if "hswing" not in self.capabilities:
            return
        if mode not in self.capabilities["hswing"]:
            return
        if self.status["hswing"] != mode:
            self.to_set["hswing"] = mode

    def code_hswing(self):
        """Nothing to do. hNalded by code_swing"""
        return bytearray(b"\x00" * len(self.FBODY)), False

    def set_target(self, mode):
        if "target" not in self.capabilities:
            return
        if mode not in self.capabilities["target"]:
            return
        if self.status["target"] != mode:
            self.to_set["target"] = mode

    def code_target(self):
        """Nothing to do. hNalded by code_swing"""
        return bytearray(b"\x00" * len(self.FBODY)), False

    def code_temperature(self):
        if "temperature" in self.to_set:
            temp = self.to_set["temperature"]
        else:
            temp = self.status["temperature"]
        if "mode" in self.to_set:
            if self.to_set["mode"] != "cool":
                temp = None
        elif self.status["mode"] != "cool":
            temp = None
        mask = bytearray(b"\x00" * len(self.FBODY))
        if temp:
            if (temp * 10) % 10:
                deci = True
                temp = int(temp)
            else:
                deci = False
            if temp < 16:
                temp += 0x3E
                if deci:
                    temp += 0x20
            else:
                if not deci:
                    temp = 0xC0 + (temp - 15)
                else:
                    temp = 0x70 + (temp - 15)
            mask[4] = temp
        return mask, True


class SharpA907(PulseBased):

    STARTFRAME = [3800, 1900]
    MARK = [470]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [500, 1500]  # ditto

    def __init__(self):
        super().__init__("SHARP_AC", variant=A907)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat"],
            "temperature": [15, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "90°", "45°", "30°"],
            "cleaning": ["off", "on"],
            "powerful": ["off", "on"],
            "economy": ["off", "on"],
            "purifier": ["off", "on"],
        }


class SharpA903(PulseBased):

    STARTFRAME = [3800, 1900]
    MARK = [470]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [500, 1500]  # ditto

    def __init__(self):
        super().__init__("SHARP_AC", variant=A903)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "fan"],
            "temperature": [15, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "90°", "45°", "30°"],
            "cleaning": ["off", "on"],
            "powerful": ["off", "on"],
            "light": ["off", "on"],
            "purifier": ["off", "on"],
        }


class SharpA705(PulseBased):

    STARTFRAME = [3800, 1900]
    MARK = [470]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [500, 1500]  # ditto

    def __init__(self):
        super().__init__("SHARP_AC", variant=A705)
        self.capabilities = {
            "mode": ["off", "cool", "dry", "fan"],
            "temperature": [15, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "90°", "45°", "30°"],
            "cleaning": ["off", "on"],
            "powerful": ["off", "on"],
            "light": ["off", "on"],
            "purifier": ["off", "on"],
        }


# --------------------------------------------------------------- Device API

JTECH_BODY = b"\xaa\x5a\xcf\x10\x00\x00\x00\x00\x00\x80\x00\xe0"
JTECH_MODE = {"auto": 0x00, "cool": 0x02, "dry": 0x03}  # byte 6 low bits
JTECH_FAN = {"auto": 0x20, "1": 0x40, "2": 0x30, "3": 0x50, "4": 0x70}  # byte 6 high
JTECH_SWING_V = {"auto": 8, "1": 9, "2": 10, "3": 11, "4": 12, "5": 13, "swing": 14}
JTECH_SWING_H = {"1": 0x20, "2": 0x10, "3": 0x30, "swing": 0xF0}  # byte 8 high
JTECH_SPOT_SIDE = {"middle": 0x10, "left": 0x20, "right": 0x30}
POWER_ON, POWER_OFF, POWER_CHANGE = 0x11, 0x21, 0x31  # byte 5 transitions
SPECIAL_ON, SPECIAL_OFF = 0x61, 0x71  # byte 5 of a powerful/economy frame


def sharp_crc(body, special=0x01):
    crc = 0
    for x in body:
        crc ^= x
    crc ^= special
    crc ^= crc >> 4
    return ((crc & 0x0F) << 4) + special


def jtech_temperature(celsius):
    """Byte 4 for a setpoint; the unit takes whole and half degrees."""
    tenths = round(celsius * 10)
    whole, half = tenths // 10, tenths % 10 != 0
    if whole < 16:
        return whole + 0x3E + (0x20 if half else 0)
    return (0x70 if half else 0xC0) + whole - 15


class JTechDevice(Device):
    """Sharp J-Tech (FTM-PV2S): byte 5 encodes a power transition, so the
    frames depend on ``previous``; see the spec's transition table."""

    PROTOCOL = SHARP_NATIVE
    capabilities = Capabilities(
        modes=("auto", "cool", "dry"),
        temperature=TemperatureRange(14.0, 29.0, (0, 5)),
        fan=Choice(
            ("auto", "1", "2", "3", "4"),
            {"1": "lowest", "2": "low", "3": "medium", "4": "highest"},
        ),
        swing_v=Choice(
            ("auto", "swing", "1", "2", "3", "4", "5"),
            {"1": "ceiling", "2": "90°", "3": "60°", "4": "45°", "5": "30°"},
        ),
        swing_h=Choice(
            ("1", "2", "3", "swing"), {"1": "left", "2": "middle", "3": "right"}
        ),
        features={
            "purifier": BOOL,
            "powerful": BOOL,
            "economy": BOOL,
            "spot": Choice(
                (
                    "off",
                    "close left",
                    "close middle",
                    "close right",
                    "far left",
                    "far middle",
                    "far right",
                )
            ),
        },
    )

    def normalise(self, state):
        state = super().normalise(state)
        if state.mode == "dry" and state.fan != "auto":
            state = replace(state, fan="auto")  # the unit ignores fan in dry
        return state

    def _body(self, previous, target):
        """Every byte except the power byte (5) and the mode bits of byte 6."""
        body = bytearray(JTECH_BODY)
        if target.power and target.mode == "cool":
            body[4] = jtech_temperature(target.temperature)
        body[6] |= JTECH_FAN[target.fan]
        spot = target.features["spot"]
        if spot == "off":
            body[8] = JTECH_SWING_H[target.swing_h] | JTECH_SWING_V[target.swing_v]
        else:
            front, side = spot.split(" ")
            body[8] = JTECH_SPOT_SIDE[side] | (0x0C if front == "close" else 0x09)
            body[9] |= 0x01
        if target.features["purifier"]:
            body[11] |= 0x04
        # The main frame carries the economy state the unit is in; the
        # economy frame below is what changes it.
        if (previous or target).features["economy"]:
            body[11] |= 0x10
        return body

    def frames(self, previous, target, actions):
        body = self._body(previous, target)
        if not target.power:
            body[5] = POWER_OFF
        elif previous is None or not previous.power:
            body[5] = POWER_ON
        else:
            body[5] = POWER_CHANGE
        body[6] |= JTECH_MODE[target.mode]
        frames = [body]
        if target.power:
            for name in ("powerful", "economy"):
                wanted = target.features[name]
                if previous is not None and previous.features[name] == wanted:
                    continue
                extra = self._body(previous, target)
                extra[5] = SPECIAL_ON if wanted else SPECIAL_OFF
                extra[6] |= JTECH_MODE[target.mode]
                if name == "powerful":
                    extra[10] |= 0x01
                elif wanted:
                    extra[11] |= 0x10
                frames.append(extra)
        return [Frame("main", bytes(f) + bytes([sharp_crc(f)])) for f in frames]


DEVICES = {"j-tech": JTechDevice}
DEVICES.update({m: KelvinatorDevice for m in KELVINATOR_SHARP_MODELS})


# ----- SharpAc
# Layout from IRremoteESP8266's SharpProtocol (ir_Sharp.h): one 13-byte state,
# sent by sendSharpAc with sendGeneric (kSharpAcHdrMark/HdrSpace header,
# kSharpAcBitMark/OneSpace/ZeroSpace bits LSB first, a kSharpAcBitMark footer
# and kSharpAcGap = kDefaultMessageGap), no repeat (kSharpAcDefaultRepeat is
# kNoRepeat), at 38 kHz. IRac::sharp may send two or three such messages
# (see SharpAcDevice). IRSharpAc::stateReset writes all 13 bytes, so no bit
# comes from stale memory.

SHARP_AC = Protocol(
    "sharp_ac",
    {
        "main": Section(
            PulseDistance(470, 500, 1400),  # kSharpAcBitMark/ZeroSpace/OneSpace
            header=(3800, 1900),  # kSharpAcHdrMark/HdrSpace
            footer=(470,),  # kSharpAcBitMark
            gap=100000,  # kSharpAcGap
        )
    },
    carrier=38000,
)


@dataclass(frozen=True)
class HighNibbleXor(Checksum):
    """The XOR of the nibbles of data[start:end], and of the low nibble of
    data[at] when ``with_low``, in the high nibble of data[at]
    (IRSharpAc::calcChecksum). The low nibble of data[at] may hold fields."""

    with_low: bool = False

    def compute(self, data):
        total = 0
        for b in self._input(data):
            total ^= (b >> 4) ^ (b & 0x0F)
        if self.with_low:
            total ^= data[self.at] & 0x0F
        return total

    def bits(self):
        return set(range(8 * self.at + 4, 8 * self.at + 8))

    def apply(self, data):
        data[self.at] = (data[self.at] & 0x0F) | self.compute(data) << 4

    def check(self, data):
        return data[self.at] >> 4 == self.compute(data)


SHARP_AC_POWER_SPECIAL = {  # kSharpAcPower*
    "unknown": 0,
    "on_from_off": 1,
    "off": 2,
    "on": 3,
    "special_on": 6,
    "special_off": 7,
    "timer": 8,
}
SHARP_AC_SPECIAL = {  # kSharpAcSpecial*
    "power": 0x00,
    "turbo": 0x01,
    "temp_econo": 0x04,
    "fan": 0x05,
    "swing": 0x06,
    "timer": 0xC0,
    "timer_half_hour": 0xDE,
}
# kSharpAcAuto (A907) and kSharpAcFan (A705) share 0b00; the A903 has neither
# a fan nor a heat mode, and IRSharpAc::convertMode has no fan case, so its
# "fan" is 0b00 too. IRSharpAc::setMode turns heat into fan for the A705 and
# A903, which the legacy entities do not offer.
SHARP_AC_MODE = {"auto": 0b00, "fan": 0b00, "heat": 0b01, "cool": 0b10, "dry": 0b11}
SHARP_AC_FAN = {  # variant -> canonical fan -> kSharpAcFan*
    # kSharpAcFanAuto, FanMin (FAN1), FanMed (FAN2), FanHigh (FAN3), as
    # IRSharpAc::convertFan maps kLow/kMedium/kHigh for the A907.
    "A907": {"auto": 0b010, "1": 0b100, "2": 0b011, "3": 0b101},
    # kSharpAcFanA705Low, FanA705Med and FanMax: the three speeds these
    # remotes have (IRSharpAc::toString names 7 "High" for them). C sends
    # kSharpAcFanHigh (= FanA705Med) for "high" (declared as a Defect).
    "A903": {"auto": 0b010, "1": 0b011, "2": 0b101, "3": 0b111},
    "A705": {"auto": 0b010, "1": 0b011, "2": 0b101, "3": 0b111},
}
SHARP_AC_FAN_AUTO = 0b010  # kSharpAcFanAuto, which setClean(true) sets
SHARP_AC_FAN_MAX = 0b111  # kSharpAcFanMax, which setTurbo(true) sets
SHARP_AC_SWING_V = {  # canonical swing -> kSharpAcSwingV*, as convertSwingV
    "off": 0b000,  # kSharpAcSwingVIgnore: IRac sends no swing setting
    "1": 0b001,  # 90° (kHigh): kSharpAcSwingVHigh
    "2": 0b011,  # 45° (kMiddle): kSharpAcSwingVMid
    "3": 0b100,  # 30° (kLow): kSharpAcSwingVLow
}
SHARP_AC_TEMP_FLAGS = 0b110  # the 0xC0 IRSharpAc::setTemp writes into byte 4
SHARP_AC_MIN = 15  # kSharpAcMinTemp
SHARP_AC_MAX = 30  # kSharpAcMaxTemp

# Skeleton: IRSharpAc::stateReset's reset state with every written field and
# the Sum cleared (bytes 0-3, 5's low nibble, 8's bit 3, 9, 11's top bits and
# 12's low nibble are fixed).
SHARP_AC_LAYOUT = Layout(
    bytes.fromhex("aa5acf10000100000880" "00e001"),
    {
        "temperature": Field.at(4, 0, 4),  # Temp: degrees - kSharpAcMinTemp
        "model": Field.at(4, 4, 1),  # Model
        # Byte 4's unnamed top bits: setTemp writes 0xC0 (0xD0 with the A705
        # Model bit) when the mode takes a setpoint, 0 in auto/fan and dry.
        "temp_flags": Field.at(4, 5, 3),
        "power_special": Field.at(5, 4, 4, values=SHARP_AC_POWER_SPECIAL),
        "mode": Field.at(6, 0, 2),  # Mode (SHARP_AC_MODE)
        "clean": Field.at(6, 3, 1),
        "fan": Field.at(6, 4, 3),  # Fan (SHARP_AC_FAN)
        "timer_hours": Field.at(7, 0, 4),
        "timer_type": Field.at(7, 6, 1),
        "timer_enabled": Field.at(7, 7, 1),
        "swing": Field.at(8, 0, 3),  # Swing (SHARP_AC_SWING_V)
        "special": Field.at(10, 0, 8, values=SHARP_AC_SPECIAL),
        "ion": Field.at(11, 2, 1),
        "model2": Field.at(11, 4, 1),  # Model2
    },
    checksum=HighNibbleXor(0, 12, 12, with_low=True),  # IRSharpAc::checksum: Sum
)


def _sharp_ac_capabilities(modes, toggle):
    """The legacy SharpA907 / A903 / A705 entities: they differ in modes and
    in one feature (economy for the A907, light for the others)."""
    return Capabilities(
        modes=modes,
        temperature=TemperatureRange(float(SHARP_AC_MIN), float(SHARP_AC_MAX)),
        fan=FAN_3,
        swing_v=Choice(
            ("off", "1", "2", "3"), {"off": "off", "1": "90°", "2": "45°", "3": "30°"}
        ),
        features={
            "cleaning": ON_OFF,
            "powerful": ON_OFF,
            toggle: ON_OFF,
            "purifier": ON_OFF,
        },
    )


SHARP_AC_CAPABILITIES = {  # variant (sharp_ac_remote_model_t) -> legacy entity
    "A907": _sharp_ac_capabilities(("auto", "cool", "dry", "heat"), "economy"),
    "A903": _sharp_ac_capabilities(("auto", "cool", "dry", "fan"), "light"),
    "A705": _sharp_ac_capabilities(("cool", "dry", "fan"), "light"),
}

SHARP_AC_MODEL_VARIANT = {  # model -> remote variant (sharp_ac_remote_model_t)
    "Sharp AY-ZP40KR": "A907",
    "AH-AxSAY": "A907",
    "CRMC-A907 JBEZ remote": "A907",
    "CRMC-A950 JBEZ": "A907",
    "generic A907": "A907",
    "AH-PR13-GL": "A903",
    "CRMC-A903JBEZ remote": "A903",
    "AH-XP10NRY": "A903",
    "CRMC-820 JBEZ remote": "A903",
    "AH-A12REVP-1": "A903",
    "CRMC-A863 JBEZ remote": "A903",
    "generic A903": "A903",
    "CRMC-A705 JBEZ remote": "A705",
    "generic A705": "A705",
}


class SharpAcDevice(Device):
    """Sharp A/C (SHARP_AC): the A907, A903 and A705 remotes, as IRac::sharp
    sends them.

    The variant (a sharp_ac_remote_model_t name) comes from the model
    (SHARP_AC_MODEL_VARIANT) unless given, and picks the capabilities (the
    legacy SharpA907/A903/A705 entities) and the fan codes; unknown models
    get the A907, as IRSharpAc::setModel does. Model2 is set for the A903 and
    A705; the Model bit only for the A705, and only in a mode that takes a
    setpoint (setTemp rewrites byte 4 after setModel set it).

    The state message:
    - PowerSpecial is Off for an off message; on, it is OnFromOff unless
      ``previous`` was on (then On), as IRac::sendAc passes prev->power
      (a fresh C object's previous state is off). Special is always Power:
      IRac calls setPower last;
    - an off message carries mode auto (IRac passes mode "off", which
      convertMode maps to its default, kSharpAcAuto); auto/fan and dry send
      byte 4 as 0 (no setpoint), cool and heat the setpoint;
    - the fan is sent in every mode: IRac's setClean(false) restores the
      requested speed after setMode forced auto (except in the first
      message of a cleaning request, below);
    - swing positions are sent, "off" sends kSharpAcSwingVIgnore; purifier
      sets Ion.

    Extra messages, as IRac::sharp sends them:
    - cleaning: an off message first, with fan auto in the modes without a
      setpoint (it is sent before setClean(false) restores the fan). When the target is on, the port then
      sends the documented clean message (setClean(true): dry, fan auto, no
      setpoint, Clean, PowerSpecial OnFromOff). C never sends it: IRac calls
      setPower after setClean, and setPower clears Clean and restores the
      mode (declared as a Defect). When the target is off, both messages are
      off messages, as in C;
    - powerful: the state message, then the same with setTurbo(true)
      (PowerSpecial SpecialOn, Special Turbo, fan kSharpAcFanMax), off or on.

    Economy (A907) and light (A903/A705) send nothing, as the C path:
    IRac::sharp never calls setEconoToggle, and the PowerSpecial/Special
    values setLightToggle writes are overwritten by the setMode and setPower
    calls that follow it.

    ``previous`` only sets PowerSpecial (above). IRac::handleToggles turns
    SHARP_AC swing changes into kAuto (swing toggle) or kOff, which with the
    entity's positions makes a persistent C object send SwingVToggle or
    SwingVOff instead of the requested position. The port sends the
    position, as a fresh C object does (declared as a Defect in the
    sequence test).
    """

    PROTOCOL = SHARP_AC
    LAYOUTS = (SHARP_AC_LAYOUT,)
    NAME = "Sharp A/C"

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        self.variant = variant or SHARP_AC_MODEL_VARIANT.get(model, "A907")
        if self.variant not in SHARP_AC_CAPABILITIES:
            raise ValueError(f"unknown {self.NAME} variant {self.variant!r}")
        self.capabilities = SHARP_AC_CAPABILITIES[self.variant]

    @staticmethod
    def layouts(frames):
        """One layout per frame: every message is a state message."""
        return (SHARP_AC_LAYOUT,) * len(frames)

    def _values(self, mode, temperature, fan, target):
        code = SHARP_AC_MODE[mode]
        setpoint = code not in (SHARP_AC_MODE["auto"], SHARP_AC_MODE["dry"])
        degrees = min(max(int(temperature), SHARP_AC_MIN), SHARP_AC_MAX)
        return dict(
            temperature=degrees - SHARP_AC_MIN if setpoint else 0,
            model=int(setpoint and self.variant == "A705"),
            temp_flags=SHARP_AC_TEMP_FLAGS if setpoint else 0,
            mode=code,
            fan=fan,
            swing=SHARP_AC_SWING_V[target.swing_v],
            special="power",
            ion=target.features["purifier"],
            model2=int(self.variant != "A907"),
        )

    def frames(self, previous, target, actions):
        fan = SHARP_AC_FAN[self.variant][target.fan]
        mode = target.mode if target.power else "auto"
        state = self._values(mode, target.temperature, fan, target)
        if not target.power:
            power = "off"
        elif previous is not None and previous.power:
            power = "on"
        else:
            power = "on_from_off"
        messages = []
        plain = state  # what IRac::sharp's setPower restores
        if target.features["cleaning"]:
            # Sent before IRac's setClean restores the fan: setMode left it
            # at auto in the modes without a setpoint.
            first = dict(state, power_special="off")
            if not state["temp_flags"]:
                first.update(fan=SHARP_AC_FAN_AUTO)
            messages.append(first)
            if target.power:
                # setClean(true): dry (fan auto, no setpoint), Clean, and
                # setPower(true, false).
                state = self._values(
                    "dry", target.temperature, SHARP_AC_FAN_AUTO, target
                )
                state.update(clean=1)
                power = "on_from_off"
        messages.append(dict(state, power_special=power))
        if target.features["powerful"]:
            # setTurbo after setPower: built from the plain state, never
            # from the clean message (setPower cleared Clean in C).
            messages.append(
                dict(
                    plain,
                    fan=SHARP_AC_FAN_MAX,
                    power_special="special_on",
                    special="turbo",
                )
            )
        return [Frame("main", bytes(SHARP_AC_LAYOUT.build(**m))) for m in messages]


SHARP_AC_MODELS = tuple(SHARP_AC_MODEL_VARIANT)


DEVICES.update({m: SharpAcDevice for m in SHARP_AC_MODELS})


class PluginObject(GenPluginObject):
    MODELS = {
        "generic": Sharp,
        "j-tech": JTech,
        "YB1FA remote": Kelvinator,
        "A5VEY": Kelvinator,
        "Sharp AY-ZP40KR": SharpA907,
        "AH-AxSAY": SharpA907,
        "CRMC-A907 JBEZ remote": SharpA907,
        "CRMC-A950 JBEZ": SharpA907,
        "AH-PR13-GL": SharpA903,
        "CRMC-A903JBEZ remote": SharpA903,
        "AH-XP10NRY": SharpA903,
        "CRMC-820 JBEZ remote": SharpA903,
        "CRMC-A705 JBEZ remote": SharpA705,
        "AH-A12REVP-1": SharpA903,
        "CRMC-A863 JBEZ remote": SharpA903,
        "generic A907": SharpA907,
        "generic A903": SharpA903,
        "generic A705": SharpA705,
    }

    def __init__(self):
        self.brand = "sharp"


def main():

    import argparse
    import base64

    parser = argparse.ArgumentParser(description="Decode LIRC IR code into frames.")
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
        choices=["auto", "cool", "dry", "off"],
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
    spotgroup = parser.add_mutually_exclusive_group()
    swinggroup = spotgroup.add_argument_group()
    swinggroup.add_argument(
        "-s",
        "--swing",
        choices=["auto", "ceiling", "90°", "60°", "45°", "30°", "swing"],
        default="auto",
        help="Set swing",
    )
    swinggroup.add_argument(
        "-H",
        "--hswing",
        choices=["middle", "left", "right", "swing"],
        default="middle",
        help="Set horizontal swing",
    )
    spotgroup.add_argument(
        "-S",
        "--spot",
        choices=[
            "off",
            "close left",
            "close middle",
            "close right",
            "far left",
            "far middle",
            "far right",
        ],
        default="off",
        help="Set spot",
    )
    parser.add_argument(
        "-p", "--powerful", action="store_true", default=False, help="Set super jet"
    )
    parser.add_argument(
        "-P",
        "--plasma",
        action="store_true",
        default=False,
        help="Set Plasmacluster purifier",
    )
    parser.add_argument(
        "-e", "--economy", action="store_true", default=False, help="Set economy mode"
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
        print(f"Available modelas are: {PluginObject().MODELS.keys()}")

    device = PluginObject().get_device(opts.model)
    frames = []
    device.set_temperature(opts.temp)
    device.set_fan(opts.fan)
    device.set_swing(opts.swing)
    try:
        device.set_hswing(opts.hswing)
    except:
        pass
    try:
        device.set_target(opts.spot)
    except:
        pass
    try:
        device.set_purifier((opts.plasma and "on") or "off")
    except:
        pass
    try:
        device.set_powerful((opts.powerful and "on") or "off")
    except:
        pass
    try:
        device.set_economy((opts.economy and "on") or "off")
    except:
        pass

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
