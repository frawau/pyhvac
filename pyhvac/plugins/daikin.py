#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Daikin AC IR commands as done by the ARC480A44
#
# This module  is in part based on the work/code from:
#      Scott Kyle https://gist.github.com/appden/42d5272bf128125b019c45bc2ed3311f
#      mat_fr     https://www.instructables.com/id/Reverse-engineering-of-an-Air-Conditioning-control/
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

from .hvaclib import HVAC, PulseBased, GenPluginObject, bit_reverse


class Daikinth(HVAC):
    """Generic Daikin HVAC object. It must have, at the very minimum
    "mode" and "temperature" capabilities"""

    FBODY = b"\x88\x5b\xe4\x00\x00\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x00\xa3\x00\x10"

    def __init__(self):
        super().__init__()
        self.brand = "Daikin"
        self.model = "Generic"
        self.capabilities = {
            "mode": ["off", "cool", "fan", "dry"],
            "temperature": [x for x in range(18, 32)],
        }
        # For functions that require their own frames
        self.xtra_capabilities = {}
        self.status = {"mode": "cool", "temperature": 25}

        self.to_set = {}
        # Specify wether the bits order has to be swapped
        self.is_msb = False

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
                temp = 25
        else:
            temp = self.status["temperature"]
        mask = bytearray(b"\x00" * 18)
        mask[6] = bit_reverse(temp * 2)
        return mask, False

    def set_fan(self, mode):
        if "fan" not in self.capabilities:
            return
        if mode not in self.capabilities["fan"]:
            return
        self.to_set["fan"] = mode

    def code_fan(self):
        """mode is one of auto, lowest, low, medium, high, highest"""
        if "fan" in self.to_set:
            mode = self.to_set["fan"]
        else:
            if "fan" in self.capabilities:
                mode = self.status["fan"]
            else:
                mode = "auto"
        rank = ["lowest", "low", "medium", "high", "highest"]
        if mode not in rank:
            mode = "auto"  # Just in case
        mask = bytearray(b"\x00" * 18)
        if mode == "auto":
            mask[8] = 0x05
        else:
            mask[8] = bit_reverse(48 + (16 * rank.index(mode)))
        return mask, False

    def set_swing(self, mode):
        if "swing" not in self.capabilities:
            return
        if mode not in self.capabilities["swing"]:
            return
        self.to_set["swing"] = mode

    def code_swing(self):
        if "swing" in self.to_set:
            mode = self.to_set["swing"]
        else:
            if "swing" in self.capabilities:
                mode = self.status["swing"]
            else:
                mode = False

        mask = bytearray(b"\x00" * 18)
        if mode == "on":
            mask[8] = 0xF0
        else:
            mask[8] = 0x00
        return mask, False

    def set_powerful(self, mode="off"):
        # print("\n\nDaikin set powerful {}\n\n".format(mode))
        if "powerful" not in self.capabilities:
            return
        if mode not in self.capabilities["powerful"]:
            return
        self.to_set["powerful"] = mode

    def code_powerful(self):

        if "powerful" in self.to_set:
            mode = self.to_set["powerful"]
        else:
            if "powerful" in self.capabilities:
                mode = self.status["powerful"]
            else:
                mode = False

        mask = bytearray(b"\x00" * 18)
        if mode == True:
            mask[13] = 0x80
        return mask, True

    def set_comfort(self, mode="off"):
        if "comfort" not in self.xtra_capabilities:
            return
        if mode not in self.xtra_capabilities["comfort"]:
            return
        # This is a toggling value AFAIK
        if self.status["comfort"] != mode:
            self.to_set["comfort"] = mode

    def code_comfort(self):
        """Some Daikin AC seem to have such"""
        return []

    def set_mode(self, mode):
        if mode not in self.capabilities["mode"]:
            mode = "cool"
        self.to_set["mode"] = mode
        if mode == "fan":
            self.to_set["temperature"] = 25
        if mode == "off":
            self.to_set = {"mode": "off"}

    def code_mode(self):
        if "mode" in self.to_set:
            mode = self.to_set["mode"]
        else:
            mode = self.status["mode"]

        mask = bytearray(b"\x00" * 18)
        if mode == "off":
            mask[16] = 0x02
            cmode = self.status["mode"]
            if cmode == "off":
                mask[5] = 0x0C
            elif cmode == "dry":
                mask[5] = 0x04
            elif cmode == "fan":
                mask[5] = 0x06
            elif cmode == "heat":
                mask[5] = 0x02
            elif cmode == "auto":
                mask[5] = 0x00
        elif mode == "dry":
            mask[5] = 0x84
            mask[6] = 0x03
        elif mode == "fan":
            mask[5] = 0x86
        elif mode == "heat":
            mask[5] = 0x82
        elif mode == "auto":
            mask[5] = 0x80
        else:
            mask[5] = 0x8C
        return mask, True

    def build_code(self):
        frames = []
        packet = bytearray(self.FBODY)
        # Note that set mod must be last for it replaces values
        for f in [
            self.code_temperature,
            self.code_fan,
            self.code_swing,
            self.code_powerful,
            self.code_mode,
        ]:
            mask, replace = f()
            if replace:
                packet = bytearray([y or x for x, y in zip(packet, mask)])
            else:
                packet = bytearray([x | y for x, y in zip(packet, mask)])
        frames += [packet]
        return frames

    def _build_ircode(self):
        frames = []
        frames += self.code_comfort()
        frames += self.build_code()
        idx = 0
        for x in frames:
            frames[idx] += self.crc(x)
            idx += 1
        return frames

    def crc(self, frame):
        crc = 0
        for x in frame:
            # print("Adding 0x%02x as 0x%02x"%(x,bit_reverse(x)))
            crc += bit_reverse(x)
            # print("crc now 0x%02x"%crc)
        return bit_reverse(crc & 0xFF).to_bytes(1, "big")


class Smash2(Daikinth):
    def __init__(self):
        super().__init__()
        self.model = "Smash 2"
        self.capabilities = {
            "mode": ["off", "cool", "fan", "dry"],
            "temperature": [x for x in range(18, 32)],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
            "powerful": ["off", "on"],
        }
        self.status = {
            "mode": "off",
            "temperature": 25,
            "fan": "auto",
            "swing": "off",
            "powerful": "off",
        }


class Daikin(PulseBased):
    STARTFRAME = [3650, 1623]
    ENDFRAME = None
    MARK = [428]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [428, 1280]  # ditto

    def __init__(self):
        super().__init__("DAIKIN")
        self.capabilities = {
            "mode": ["off", "auto", "dry", "cool", "heat", "fan"],
            "temperature": [10, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "economy": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
            "cleaning": ["off", "on"],
        }
        self.temperature_step = 0.5


class Daikin2(PulseBased):
    LEAD = [10024, 25180]
    STARTFRAME = [3500, 1728]
    ENDFRAME = None
    MARK = [460]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [420, 1270]  # ditto

    def __init__(self):
        super().__init__("DAIKIN2")
        self.capabilities = {
            "mode": ["off", "auto", "dry", "cool", "heat", "fan"],
            "temperature": [10, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto", "ceiling", "90°", "60°", "45°", "30°", "0°"],
            "hswing": [
                "off",
                "far left",
                "close left",
                "middle",
                "close right",
                "far right",
                "wide",
            ],
            "economy": ["off", "on"],
            "economy": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
            "cleaning": ["off", "on"],
            "purifier": ["off", "on"],
        }


class Daikin216(PulseBased):
    STARTFRAME = [3440, 1750]
    ENDFRAME = None
    MARK = [420]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [450, 1300]  # ditto

    def __init__(self):
        super().__init__("DAIKIN216")
        self.capabilities = {
            "mode": ["off", "auto", "dry", "cool", "heat", "fan"],
            "temperature": [10, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
        }


class Daikin160(PulseBased):
    STARTFRAME = [5000, 2145]
    ENDFRAME = None
    MARK = [342]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [700, 1786]  # ditto

    def __init__(self):
        super().__init__("DAIKIN160")
        self.capabilities = {
            "mode": ["off", "auto", "dry", "cool", "heat", "fan"],
            "temperature": [10, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto", "90°", "60°", "45°", "30°", "0°"],
        }


class Daikin176(PulseBased):
    STARTFRAME = [5070, 2140]
    ENDFRAME = None
    MARK = [370]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [710, 1780]  # ditto

    def __init__(self):
        super().__init__("DAIKIN176")
        self.capabilities = {
            "mode": ["off", "auto", "dry", "cool", "heat", "fan"],
            "temperature": [10, 32],
            "fan": ["high", "low"],
            "hswing": ["off", "on"],
        }


class Daikin128(PulseBased):
    LEAD = [9800, 9800]
    STARTFRAME = [4600, 2500]
    ENDFRAME = [4600, 20300]
    MARK = [350]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [382, 954]  # ditto

    def __init__(self):
        super().__init__("DAIKIN128")
        self.capabilities = {
            "mode": ["off", "auto", "dry", "cool", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
            "economy": ["off", "on"],
        }


class Daikin152(PulseBased):
    STARTFRAME = [3492, 1718]
    ENDFRAME = None
    MARK = [433]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [433, 1529]  # ditto

    def __init__(self):
        super().__init__("DAIKIN152")
        self.capabilities = {
            "mode": ["off", "auto", "dry", "cool", "heat", "fan"],
            "temperature": [10, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "economy": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
        }


class Daikin64(PulseBased):
    STARTFRAME = [4920, 2230]
    ENDFRAME = None
    MARK = [298]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [780, 1850]  # ditto

    def __init__(self):
        super().__init__("DAIKIN64")
        self.capabilities = {
            "mode": ["off", "dry", "cool", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
        }


class PluginObject(GenPluginObject):
    MODELS = {
        "generic": Daikinth,
        "smash 2": Smash2,  # Daikin
        "ARC433 remote": Daikin,
        "ARC477A1 remote": Daikin2,
        "FTXZ25NV1B": Daikin2,
        "FTXZ35NV1B": Daikin2,
        "FTXZ50NV1B": Daikin2,
        "ARC433B69 remote": Daikin216,
        "ARC423A5 remote": Daikin160,
        "FTE12HV2S": Daikin160,
        "BRC4C153 remote": Daikin176,
        "FFQ35B8V1B": Daikin176,
        "BRC4C151 remote": Daikin176,
        "17 Series FTXB09AXVJU": Daikin128,
        "17 Series FTXB12AXVJU": Daikin128,
        "17 Series FTXB24AXVJU": Daikin128,
        "BRC52B63 remote": Daikin128,
        "ARC480A5 remote": Daikin152,
        "FFN-C/FCN-F Series": Daikin64,
        "DGS01 remote": Daikin64,
        "M Series": Daikin,
        "FTXM-M": Daikin,
        "ARC466A12 remote": Daikin,
        "ARC466A33 remote": Daikin,
        "FTWX35AXV1": Daikin64,
        "ARC484A4 remote": Daikin216,
        "FTQ60TV16U2": Daikin216,
        # "BRC4M150W16 remote": Daikin200,
        # "FTXM20R5V1B": Daikin312,
        # "ARC466A67 remote": Daikin312,
        "Daikin": Daikin,
        "Daikin2": Daikin2,
        "Daikin64": Daikin64,
        "Daikin128": Daikin128,
        "Daikin152": Daikin152,
        "Daikin160": Daikin160,
        "Daikin176": Daikin176,
        "Daikin216": Daikin216,
    }

    def __init__(self):
        self.brand = "daikin"


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
        choices=["cool", "dry", "fan", "off"],
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
        "-s", "--swing", action="store_true", default=False, help="Set swing"
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
        print(f"Available modelas are: {PluginObject().MODELS.keys()}")

    device = PluginObject().get_device(opts.model)

    frames = []
    device.set_temperature(opts.temp)
    device.set_fan(opts.fan)
    device.set_swing(opts.swing)
    device.set_powerful(opts.powerful)
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
