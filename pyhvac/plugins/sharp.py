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

from dataclasses import replace

from .hvaclib import HVAC, PulseBased, GenPluginObject
from ..device import Device
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import BOOL, Capabilities, Choice, TemperatureRange
from .kelvinator import Kelvinator

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
        self.status = {"mode": "cool", "temperature": 25}

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
