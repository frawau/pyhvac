#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate LG AC IR commands as done by the AXB74515402
#
# Found the info about 4 bits somewhere on the  Internet...Can't find
# it again. Apologies for not being able to thanks that person.
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

from .. import irhvac

from .hvaclib import HVAC, GenPluginObject

# Let's create a basic  Gen


class IRGHVAC(HVAC):
    def __init__(self, protocol, variant=None):
        self.brand = "Irgen"
        self.model = "Irgen"
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry"],
            "temperature": [x for x in range(18, 30)],
        }
        # For functions that require their own frames
        self.xtra_capabilities = {}
        self.status = {"mode": "auto", "temperature": 25}
        self.temperature_step = 1.0
        self.irac = irhvac.IRac(
            4
        )  # Why 4? Don't ask... in the lib is for some Arduino pin.
        self.protocol = protocol
        self.variant = variant

        self.to_set = {}
        # Specify whether the bits order has to be swapped
        self.is_msb = False

    def update_status(self):
        for x, y in self.to_set.items():
            self.status[x] = y
        self.to_set = {}

    def trans_mode(self, mode):
        trad = {
            "auto": irhvac.opmode_t_kAuto,
            "cool": irhvac.opmode_t_kCool,
            "dry": irhvac.opmode_t_kDry,
            "fan": irhvac.opmode_t_kFan,
            "heat": irhvac.opmode_t_kHeat,
            "off": irhvac.opmode_t_kOff,
        }
        return trad[mode]

    def trans_temperature(self, temp):
        return temp

    def trans_fan(self, fan):
        trad = {
            "auto": irhvac.fanspeed_t_kAuto,
            "highest": irhvac.fanspeed_t_kMax,
            "high": irhvac.fanspeed_t_kHigh,
            "midhigh": irhvac.fanspeed_t_kMediumHigh,
            "medium": irhvac.fanspeed_t_kMedium,
            "low": irhvac.fanspeed_t_kLow,
            "lowest": irhvac.fanspeed_t_kMin,
        }

        return trad[fan]

    def trans_swing(self, swing):
        trad = {
            "auto": iregen.swingv_t_kAuto,
            "auto high": irhvac.swingv_t_kHigh,
            "auto low": irhvac.swingv_t_kLow,
            "ceiling": swingv_t_kHighest,
            "90°": irhvac.swingv_t_kHigh,
            "60°": irhvac.swingv_t_kUpperMiddle,
            "45°": irhvac.swingv_t_kMiddle,
            "30°": irhvac.swingv_t_kLow,
            "0°": irhvac.swingv_t_kLowest,
            "off": swingv_t_kOff,
        }

        return trad[swing]

    def trans_hswing(self, swing):
        trad = {
            "off": irhvac.swingh_t_kOff,
            "left": irhvac.swingh_t_kLeft,
            "close left": irhvac.swingh_t_kLeft,
            "close middle": irhvac.swingh_t_kMiddle,
            "right": irhvac.swingh_t_kRight,
            "close right": irhvac.swingh_t_kRight,
            "far left": irhvac.swingh_t_kLeftMax,
            "far middle": irhvac.swingh_t_kMiddle,
            "far right": irhvac.swingh_t_kRightMax,
            "middle": irhvac.swingh_t_kMiddle,
            "wide": irhvac.swingh_t_kWide,
            "auto": irhvac.swingh_t_kAuto,
        }

        return trad[swing]

    def trans_purifier(self, val):
        return val == "on"

    def trans_economy(self, val):
        return val == "on"

    def trans_powerful(self, val):
        return val == "on"

    def trans_cleaning(self, val):
        return val == "on"

    def trans_quiet(self, val):
        return val == "on"

    def trans_light(self, val):
        return val == "on"

    def trans_sleep(self, val):
        return val == "on"

    def set_mode(self, mode="off"):
        if mode not in self.capabilities["mode"]:
            mode = "auto"
        self.to_set["mode"] = mode

    def set_fan(self, mode="off"):
        if mode not in self.capabilities["mode"]:
            mode = self.capabilities["mode"][0]
        self.to_set["mode"] = mode

    def set_swing(self, mode="off"):
        if mode not in self.capabilities["swing"]:
            mode = self.capabilities["swing"][0]
        self.to_set["swing"] = mode

    def set_hswing(self, mode="off"):
        if mode not in self.capabilities["hswing"]:
            mode = self.capabilities["hswing"][0]
        self.to_set["hswing"] = mode

    def set_temperature(self, temp=25):
        if temp < self.capabilities["temperature"][0]:
            temp = self.capabilities["temperature"][0]
        elif temp > self.capabilities["temperature"][-1]:
            temp = self.capabilities["temperature"][-1]
        self.to_set["temperature"] = temp

    def set_purifier(self, mode=False):
        if "purifier" not in self.capabilities:
            return
        if mode not in self.capabilities["purifier"]:
            return
        if self.status["purifier"] != mode:
            self.to_set["purifier"] = mode

    def set_powerful(self, mode=False):
        if "powerful" not in self.capabilities:
            return
        if mode not in self.capabilities["powerful"]:
            return
        if self.status["powerful"] != mode:
            self.to_set["powerful"] = mode

    def set_cleaning(self, mode=False):
        if "cleaning" not in self.capabilities:
            return
        if mode not in self.capabilities["cleaning"]:
            return
        if self.status["cleaning"] != mode:
            self.to_set["cleaning"] = mode

    def set_economy(self, mode=False):
        if "economy" not in self.capabilities:
            return
        if mode not in self.capabilities["economy"]:
            return
        if self.status["economy"] != mode:
            self.to_set["economy"] = mode

    def set_light(self, mode=False):
        if "light" not in self.capabilities:
            return
        if mode not in self.capabilities["light"]:
            return
        if self.status["light"] != mode:
            self.to_set["light"] = mode

    def set_quiet(self, mode=False):
        if "quiet" not in self.capabilities:
            return
        if mode not in self.capabilities["quiet"]:
            return
        if self.status["quiet"] != mode:
            self.to_set["quiet"] = mode

    def set_sleep(self, mode=False):
        if "sleep" not in self.capabilities:
            return
        if mode not in self.capabilities["sleep"]:
            return
        if self.status["sleep"] != mode:
            self.to_set["sleep"] = mode

    def to_lirc(self, frames):
        res = []
        for x in frames:
            res += x
        return res

    def build_ircode(self):
        map = {
            "mode": "mode",
            "temperature": "degrees",
            "fan": "fanspeed",
            "swing": "swingv",
            "hswing": "swingh",
            "quiet": "quiet",
            "powerful": "turbo",
            "economy": "econo",
            "light": "light",
            "purifier": "filter",
            "cleaning": "clean",
        }

        self.update_status()

        self.irac.next.protocol = getattr(irhvac, self.protocol)
        if self.variant:
            self.irac.next.model = self.variant
        if self.status["mode"] == "off":
            self.irac.next.power = False
        else:
            self.irac.next.power = True
        for k, v in self.status.items():
            try:
                setattr(self.irac.next, map[k], getattr(self, "trans_" + k)(v))
            except Exception as e:
                print(f"Error: Failed to set {k} to {v}: {e}")
        self.irac.sendAc()
        code = self.irac.getTiming()
        _ = self.irac.resetTiming()
        return [code]


class Manchester(IRGHVAC):
    # Encoding is manchester"""
    LEAD = None
    HALFPULSE = 950
    STARTFRAME = [3 * 950, 3 * 950]
    ENDFRAME = [5 * 950]

    def decode_pulse(self, pulse, endian="msb"):
        """Decode a pulse encoded with Manchester encoding."""
        # TODO
        return []


class PulseBased(IRGHVAC):
    # Encoding is pulse length"""
    LEAD = None
    TAIL = None
    STARTFRAME = [0, 0]
    ENDFRAME = None
    MARK = [0]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [0]  # ditto

    def decode_pulse(self, pulse, endian="msb"):
        """Decode a pulse encoded with Manchester encoding."""
        # TODO
        return []

    def generate_to_lirc(self, frames):
        """Transform a list of frames into a LIRC compatible list of pulse timing pairs."""
        lircframe = []
        if self.LEAD:
            lircframe += self.LEAD
        for frame in frames:
            if not self.STARTFRAME is None:
                lircframe += self.STARTFRAME
            for x in frame:
                idx = 0x80
                while idx:
                    if x & idx:
                        lircframe.append(self.MARK[-1])
                        lircframe.append(self.SPACE[-1])
                    else:
                        lircframe.append(self.MARK[0])
                        lircframe.append(self.SPACE[0])
                    idx >>= 1
            if not self.ENDFRAME is None:
                lircframe += self.ENDFRAME
        if self.TAIL:
            lircframe += self.TAIL
        return lircframe


# Real "A/C, Inverters (and remote)


class Airton(PulseBased):

    STARTFRAME = [6630, 3350]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [430, 1260]  # ditto

    def __init__(self):
        super().__init__("AIRTON")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [16, 25],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
            "purifier": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
            "economy": ["off", "on"],
            "light": ["off", "on"],
        }


class Airwell(Manchester):
    HALFPULSE = 950
    STARTFRAME = [3 * 950, 3 * 950]
    ENDFRAME = [5 * 950]

    def __init__(self):
        super().__init__("AIRWELL")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low", "lowest"],
        }


class Amcor(PulseBased):
    STARTFRAME = [8200, 4200]
    ENDFRAME = [1900, 10000]
    MARK = [600, 1500]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [1500, 600]  # ditto

    def __init__(self):
        super().__init__("AMCOR")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [12, 32],
            "fan": ["auto", "highest", "medium", "lowest"],
        }


class Argo(PulseBased):

    STARTFRAME = [6400, 3300]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [900, 2200]  # ditto

    def __init__(self):
        super().__init__("ARGO", variant=irhvac.SAC_WREM2)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [16, 25],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["auto", "ceiling", "90°", "60°", "45°", "30°", "0°"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
        }


class Argo2(PulseBased):

    STARTFRAME = [6400, 3300]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [900, 2200]  # ditto

    def __init__(self):
        super().__init__("ARGO", variant=irhvac.SAC_WREM3)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [16, 25],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["auto", "ceiling", "90°", "60°", "45°", "30°", "0°"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
            "economy": ["off", "on"],
            "purifier": ["off", "on"],
        }


class Bosh(PulseBased):

    STARTFRAME = [4366, 4415]
    ENDFRAME = [5235, int(5235 * 1.5)]
    MARK = [502]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [571, 1645]  # ditto

    def __init__(self):
        super().__init__("BOSCH144")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "quiet": ["off", "on"],
        }


class Carrier(PulseBased):

    STARTFRAME = [8940, 4556]
    ENDFRAME = None
    MARK = [503]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [615, 1736]  # ditto

    def __init__(self):
        super().__init__("CARRIER_AC64")
        self.capabilities = {
            "mode": ["off", "cool", "fan" "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
        }


class Coolix(PulseBased):
    STARTFRAME = [4692, 4416]
    ENDFRAME = None
    MARK = [552]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [552, 1656]  # ditto

    def __init__(self):
        super().__init__("COOLIX")
        self.capabilities = {
            "mode": ["off", "cool", "dry", "auto", "heat", "fan"],
            "temperature": [17, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
            "cleaning": ["off", "on"],
            "light": ["off", "on"],
        }


class Corona(PulseBased):
    STARTFRAME = [3500, 1680]
    ENDFRAME = None
    MARK = [450]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [420, 1270]  # ditto

    def __init__(self):
        super().__init__("CORONA_AC")
        self.capabilities = {
            "mode": ["off", "heat", "dry", "cool", "fan"],
            "temperature": [17, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "economy": ["off", "on"],
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


class Delonghi(PulseBased):

    STARTFRAME = [8984, 4200]
    ENDFRAME = None
    MARK = [572]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [510, 1558]  # ditto

    def __init__(self):
        super().__init__("DELONGHI_AC")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry"],
            "temperature": [16, 25],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
        }


class Ecoclim(PulseBased):

    STARTFRAME = [6630, 3350]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [430, 1260]  # ditto

    def __init__(self):
        super().__init__("ECOCLIM")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [5, 31],
            "fan": ["auto", "high", "medium", "low"],
        }


class Electra(PulseBased):

    STARTFRAME = [9166, 4470]
    ENDFRAME = None
    MARK = [646]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [547, 1647]  # ditto

    def __init__(self):
        super().__init__("ELECTRA_AC")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [16, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "light": ["off", "on"],
            "cleaning": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
        }


class Fujitsuv1(PulseBased):

    STARTFRAME = [3324, 1574]
    ENDFRAME = None
    MARK = [440]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [390, 1182]  # ditto

    def __init__(self):
        super().__init__("FUJITSU_AC", variant=irhvac.ARRAH2E)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "fan", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "quiet": ["off", "on"],
        }


class Fujitsuv2(PulseBased):

    STARTFRAME = [3324, 1574]
    ENDFRAME = None
    MARK = [440]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [390, 1182]  # ditto

    def __init__(self):
        super().__init__("FUJITSU_AC", variant=irhvac.ARDB1)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "fan", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
            "quiet": ["off", "on"],
        }


class Fujitsuv3(PulseBased):

    STARTFRAME = [3324, 1574]
    ENDFRAME = None
    MARK = [440]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [390, 1182]  # ditto

    def __init__(self):
        super().__init__("FUJITSU_AC", variant=irhvac.ARREB1E)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "fan", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
            "economy": ["off", "on"],
        }


class Fujitsuv4(PulseBased):

    STARTFRAME = [3324, 1574]
    ENDFRAME = None
    MARK = [440]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [390, 1182]  # ditto

    def __init__(self):
        super().__init__("FUJITSU_AC", variant=irhvac.ARJW2)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "fan", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "quiet": ["off", "on"],
        }


class Fujitsuv5(PulseBased):

    STARTFRAME = [3324, 1574]
    ENDFRAME = None
    MARK = [440]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [390, 1182]  # ditto

    def __init__(self):
        super().__init__("FUJITSU_AC", variant=irhvac.ARRY4)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "fan", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
            "purifier": ["off", "on"],
            "quiet": ["off", "on"],
            "cleaning": ["off", "on"],
        }


class Fujitsuv6(PulseBased):

    STARTFRAME = [3324, 1574]
    ENDFRAME = None
    MARK = [440]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [390, 1182]  # ditto

    def __init__(self):
        super().__init__("FUJITSU_AC", variant=irhvac.ARREW4E)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "fan", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
            "economy": ["off", "on"],
        }


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


class Greev1(PulseBased):

    STARTFRAME = [9000, 4500]
    ENDFRAME = None
    MARK = [620]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [540, 1600]  # ditto

    def __init__(self):
        super().__init__("GREE", variant=irhvac.YAW1F)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "fan", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["auto", "90°", "60°", "46", "30°", "0°"],
            "hswing": [
                "off",
                "auto",
                "far left",
                "close left",
                "middle",
                "close right",
                "far right",
            ],
            "powerful": ["off", "on"],
            "light": ["off", "on"],
            "cleaning": ["off", "on"],
        }


class Greev2(PulseBased):

    STARTFRAME = [9000, 4500]
    ENDFRAME = None
    MARK = [620]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [540, 1600]  # ditto

    def __init__(self):
        super().__init__("GREE", variant=irhvac.YBOFB)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "fan", "heat"],
            "temperature": [16, 30],
            "economy": ["off", "on"],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["auto", "90°", "60°", "46", "30°", "0°"],
            "hswing": [
                "off",
                "auto",
                "far left",
                "close left",
                "middle",
                "close right",
                "far right",
            ],
            "powerful": ["off", "on"],
            "light": ["off", "on"],
            "cleaning": ["off", "on"],
        }


class Greev3(PulseBased):

    STARTFRAME = [9000, 4500]
    ENDFRAME = None
    MARK = [620]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [540, 1600]  # ditto

    def __init__(self):
        super().__init__("GREE", variant=irhvac.YX1FSF)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "fan", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["auto", "90°", "60°", "46", "30°", "0°"],
            "hswing": [
                "off",
                "auto",
                "far left",
                "close left",
                "middle",
                "close right",
                "far right",
            ],
            "powerful": ["off", "on"],
            "light": ["off", "on"],
            "economy": ["off", "on"],
            "cleaning": ["off", "on"],
        }


class Haier(PulseBased):

    STARTFRAME = [3000, 4300]
    ENDFRAME = None
    MARK = [520]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [650, 1650]  # ditto

    def __init__(self):
        super().__init__("HAIER_AC")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto high", "auto low"],
            "purifier": ["off", "on"],
            "sleep": ["off", "on"],
        }


class Haier176A(PulseBased):

    STARTFRAME = [3000, 4300]
    ENDFRAME = None
    MARK = [520]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [650, 1650]  # ditto

    def __init__(self):
        super().__init__("HAIER_AC176", variant=irhvac.V9014557_A)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto", "ceiling", "45°", "30°", "0°"],
            "hswing": ["auto", "far right", "right", "middle", "left", "far left"],
            "purifier": ["off", "on"],
            "sleep": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
        }


class Haier176B(PulseBased):

    STARTFRAME = [3000, 4300]
    ENDFRAME = None
    MARK = [520]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [650, 1650]  # ditto

    def __init__(self):
        super().__init__("HAIER_AC176", variant=irhvac.V9014557_B)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto", "ceiling", "45°", "30°", "0°"],
            "hswing": ["auto", "far right", "right", "middle", "left", "far left"],
            "purifier": ["off", "on"],
            "sleep": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
        }


class HaierYRW02A(PulseBased):

    STARTFRAME = [3000, 4300]
    ENDFRAME = None
    MARK = [520]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [650, 1650]  # ditto

    def __init__(self):
        super().__init__("HAIER_AC_YRW02", variant=irhvac.V9014557_A)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto", "ceiling", "45°", "30°", "0°"],
            "hswing": ["auto", "far right", "right", "middle", "left", "far left"],
            "purifier": ["off", "on"],
            "sleep": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
        }


class HaierYRW02B(PulseBased):

    STARTFRAME = [3000, 4300]
    ENDFRAME = None
    MARK = [520]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [650, 1650]  # ditto

    def __init__(self):
        super().__init__("HAIER_AC_YRW02", variant=irhvac.V9014557_B)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto", "ceiling", "45°", "30°", "0°"],
            "hswing": ["auto", "far right", "right", "middle", "left", "far left"],
            "purifier": ["off", "on"],
            "sleep": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
        }


class Haier160(PulseBased):

    STARTFRAME = [3000, 4300]
    ENDFRAME = None
    MARK = [520]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [650, 1650]  # ditto

    def __init__(self):
        super().__init__("HAIER_AC160")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto", "ceiling", "90°", "45°", "30°", "0°"],
            "purifier": ["off", "on"],
            "sleep": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
            "cleaning": ["off", "on"],
            "light": ["off", "on"],
        }


class Hitachi(PulseBased):

    STARTFRAME = [3300, 1700]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [500, 1250]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC")
        self.capabilities = {
            "mode": ["off", "auto", "heat", "cool", "dry", "fan"],
            "temperature": [16, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
        }


class Hitachi1A(PulseBased):

    STARTFRAME = [3400, 3400]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [372, 1208]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC1", variant=irhvac.R_LT0541_HTA_A)
        self.capabilities = {
            "mode": ["off", "auto", "heat", "cool", "dry", "fan"],
            "temperature": [16, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "sleep": ["off", "on"],
        }


class Hitachi1B(PulseBased):

    STARTFRAME = [3400, 3400]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [372, 1208]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC1", variant=irhvac.R_LT0541_HTA_B)
        self.capabilities = {
            "mode": ["off", "auto", "heat", "cool", "dry", "fan"],
            "temperature": [16, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "sleep": ["off", "on"],
        }


class Hitachi424(PulseBased):

    LEAD = [29784, 49290]
    STARTFRAME = [3416, 1604]
    ENDFRAME = None
    MARK = [463]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [500, 1250]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC424")
        self.capabilities = {
            "mode": ["off", "fan", "heat", "cool", "dry"],
            "temperature": [16, 32],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
        }


class Hitachi3(PulseBased):

    STARTFRAME = [3400, 1660]
    ENDFRAME = None
    MARK = [460]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [410, 1250]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC3")
        self.capabilities = {
            "mode": ["off", "fan", "heat", "cool", "dry"],
            "temperature": [16, 32],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
        }


class Hitachi344(PulseBased):

    STARTFRAME = [3300, 1700]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [500, 1250]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC344")
        self.capabilities = {
            "mode": ["off", "cool", "fan", "dry", "heat"],
            "temperature": [16, 32],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
            "hswing": ["auto", "far right", "right", "middle", "left", "far left"],
        }


class Hitachi264(PulseBased):

    STARTFRAME = [3300, 1700]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [500, 1250]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC264")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [16, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "purifier": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
            "economy": ["off", "on"],
            "light": ["off", "on"],
        }


class Hitachi296(PulseBased):

    STARTFRAME = [3300, 1700]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [500, 1250]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC296")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat"],
            "temperature": [16, 25],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
        }


class Kelon(PulseBased):

    STARTFRAME = [9000, 4600]
    ENDFRAME = None
    MARK = [560]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [600, 1680]  # ditto

    def __init__(self):
        super().__init__("KELON")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [18, 32],
            "fan": ["auto", "high", "medium", "low"],
            "sleep": ["off", "on"],
        }


class Kelon168(PulseBased):
    # Not yet exposed
    STARTFRAME = [9000, 4600]
    ENDFRAME = [560, 8000]
    MARK = [560]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [600, 1680]  # ditto

    def __init__(self):
        super().__init__("KELON168")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [18, 32],
            "fan": ["auto", "high", "medium", "low"],
            "sleep": ["off", "on"],
        }


class Kelvinator(PulseBased):

    STARTFRAME = [9010, 4505]
    ENDFRAME = [600, 19975]
    MARK = [680]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [510, 1530]  # ditto

    def __init__(self):
        super().__init__("KELVINATOR")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": ["off", "on"],
            "purifier": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
            "cleaning": ["off", "on"],
            "light": ["off", "on"],
        }


class LGv1(PulseBased):

    STARTFRAME = [8500, 4250]
    ENDFRAME = [400, 39750]
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [430, 1260]  # ditto

    def __init__(self):
        super().__init__("LG", variant=irhvac.GE6711AR2853M)
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
        super().__init__("LG", variant=irhvac.LG6711A20083V)
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
        super().__init__("LG2", variant=irhvac.AKB75215403)
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
        super().__init__("LG2", variant=irhvac.AKB74955603)
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
        super().__init__("LG2", variant=irhvac.AKB73757604)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [16, 25],
            "fan": ["auto", "high", "medium", "low", "lowest"],
            "swing": ["off", "auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": ["off", "on"],
            "light": ["off", "on"],
        }


class Midea(PulseBased):

    STARTFRAME = [4480, 4480]
    ENDFRAME = [560, 5600]
    MARK = [560]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [560, 1680]  # ditto

    def __init__(self):
        super().__init__("MIDEA")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [17, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
            "economy": ["off", "on"],
            "light": ["off", "on"],
            "cleaning": ["off", "on"],
            "sleep": ["off", "on"],
        }


class Miragev1(PulseBased):

    STARTFRAME = [8360, 4248]
    ENDFRAME = [554, 20000]
    MARK = [554]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [545, 1592]  # ditto

    def __init__(self):
        super().__init__("MIRAGE", variant=irhvac.KKG9AC1)
        self.capabilities = {
            "mode": ["off", "cool", "fan", "dry", "heat"],
            "temperature": [16, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto", "90°", "60°", "45°", "30°", "0°"],
            "powerful": ["off", "on"],
            "sleep": ["off", "on"],
            "light": ["off", "on"],
        }


class Miragev2(PulseBased):

    STARTFRAME = [8360, 4248]
    ENDFRAME = [554, 20000]
    MARK = [554]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [545, 1592]  # ditto

    def __init__(self):
        super().__init__("MIRAGE", variant=irhvac.KKG29AC1)
        self.capabilities = {
            "mode": ["off", "cool", "fan", "dry", "heat"],
            "temperature": [16, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": ["off", "on"],
            "powerful": ["off", "on"],
            "sleep": ["off", "on"],
            "light": ["off", "on"],
            "quiet": ["off", "on"],
            "cleaning": ["off", "on"],
            "purifier": ["off", "on"],
        }


class Mitsubishi(PulseBased):

    STARTFRAME = [3400, 1750]
    ENDFRAME = [440, 15500]
    MARK = [450]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [420, 1300]  # ditto

    def __init__(self):
        super().__init__("MITSUBISHI_AC")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [16, 31],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": [
                "auto",
                "wide",
                "far right",
                "right",
                "middle",
                "left",
                "far left",
            ],
        }
        self.temperature_step = 0.5


class Mitsubishi136(PulseBased):

    STARTFRAME = [3324, 1474]
    ENDFRAME = None
    MARK = [467]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [351, 1137]  # ditto

    def __init__(self):
        super().__init__("MITSUBISHI136")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [16, 25],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "auto", "90°", "60°", "30°", "0°"],
            "quiet": ["off", "on"],
        }


class Mitsubishi112(PulseBased):

    STARTFRAME = [3450, 1696]
    ENDFRAME = None
    MARK = [450]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [385, 1250]  # ditto

    def __init__(self):
        super().__init__("MITSUBISHI112")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat"],
            "temperature": [16, 25],
            "fan": ["highest", "medium", "low", "lowest"],
            "swing": ["off", "auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": [
                "auto",
                "wide",
                "far right",
                "right",
                "middle",
                "left",
                "far left",
            ],
            "quiet": ["off", "on"],
        }


class Mitsubishi152(PulseBased):

    STARTFRAME = [3140, 1630]
    ENDFRAME = None
    MARK = [370]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [1220, 420]  # ditto

    def __init__(self):
        super().__init__("MITSUBISHI_HEAVY_152")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "fan", "heat"],
            "temperature": [17, 31],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": [
                "auto",
                "wide",
                "far right",
                "right",
                "middle",
                "left",
                "far left",
            ],
            "quiet": ["off", "on"],
            "sleep": ["off", "on"],
            "purifier": ["off", "on"],
            "cleaning": ["off", "on"],
            "powerful": ["off", "on"],
            "economy": ["off", "on"],
        }


class Mitsubishi88(PulseBased):

    STARTFRAME = [3140, 1630]
    ENDFRAME = None
    MARK = [370]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [1220, 420]  # ditto

    def __init__(self):
        super().__init__("MITSUBISHI_HEAVY_88")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat"],
            "temperature": [17, 31],
            "fan": ["highest", "medium", "low", "lowest"],
            "swing": ["off", "auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": [
                "off",
                "auto",
                "far right",
                "right",
                "middle",
                "left",
                "far left",
            ],
            "cleaning": ["off", "on"],
            "powerful": ["off", "on"],
            "economy": ["off", "on"],
        }


class Neoclima(PulseBased):

    STARTFRAME = [6112, 7391]
    ENDFRAME = None
    MARK = [537]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [571, 1651]  # ditto

    def __init__(self):
        super().__init__("NEOCLIMA")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat"],
            "temperature": [16, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "sleep": ["off", "on"],
            "powerful": ["off", "on"],
            "purifier": ["off", "on"],
            "economy": ["off", "on"],
            "light": ["off", "on"],
        }


class PanasonicLke(PulseBased):

    STARTFRAME = [3456, 1728]
    ENDFRAME = None
    MARK = [432]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [432, 1296]  # ditto

    def __init__(self):
        super().__init__("PANASONIC_AC", variant=irhvac.kPanasonicLke)
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
        super().__init__("PANASONIC_AC", variant=irhvac.kPanasonicNke)
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
        super().__init__("PANASONIC_AC", variant=irhvac.kPanasonicDke)
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
        super().__init__("PANASONIC_AC", variant=irhvac.kPanasonicJke)
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
        super().__init__("PANASONIC_AC", variant=irhvac.kPanasonicCkp)
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
        super().__init__("PANASONIC_AC", variant=irhvac.kPanasonicRkr)
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


class Rhoss(PulseBased):

    STARTFRAME = [3042, 4248]
    ENDFRAME = None
    MARK = [648]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [457, 1545]  # ditto

    def __init__(self):
        super().__init__("RHOSS")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "highest", "medium", "lowest"],
            "swing": ["off", "on"],
        }


class Samsung(PulseBased):

    LEAD = [690, 17844]
    STARTFRAME = [3086, 8864]
    TAIL = [2886, 97114]
    MARK = [586]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [436, 1432]  # ditto

    def __init__(self):
        super().__init__("SAMSUNG_AC")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "cleaning": ["off", "on"],
            "quiet": ["off", "on"],
            "powerful": ["off", "on"],
            "economy": ["off", "on"],
            "light": ["off", "on"],
            "purifier": ["off", "on"],
        }


class Sanyo(PulseBased):

    STARTFRAME = [8500, 4200]
    MARK = [500]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [550, 1600]  # ditto

    def __init__(self):
        super().__init__("SANYO_AC")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["auto", "90°", "60°", "45°", "30°", "0°"],
            "sleep": ["off", "on"],
        }


class Sanyo88(PulseBased):

    STARTFRAME = [5400, 2000]
    MARK = [500]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [750, 1500]  # ditto
    TAIL = [500, 3675]

    def __init__(self):
        super().__init__("SANYO_AC88")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "heat", "fan"],
            "temperature": [10, 30],
            "fan": ["auto", "highest", "high", "medium", "lowest"],
            "swing": ["off", "on"],
            "powerful": ["off", "on"],
            "purifier": ["off", "on"],
            "sleep": ["off", "on"],
        }


class SharpA907(PulseBased):

    STARTFRAME = [3800, 1900]
    MARK = [470]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [500, 1500]  # ditto

    def __init__(self):
        super().__init__("SHARP_AC", variant=irhvac.A907)
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
        super().__init__("SHARP_AC", variant=irhvac.A903)
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
        super().__init__("SHARP_AC", variant=irhvac.A705)
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


class Tclv1(PulseBased):

    STARTFRAME = [3800, 1650]
    MARK = [500]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [325, 1050]  # ditto

    def __init__(self):
        super().__init__("TCL112AC", variant=irhvac.TAC09CHSD)
        self.capabilities = {
            "mode": ["off", "cool", "dry", "fan", "heat"],
            "temperature": [16, 31],
            "fan": ["auto", "high", "medium", "low", "lowest"],
            "swing": ["off", "auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": ["off", "on"],
            "quiet": ["off", "on"],
            "purifier": ["off", "on"],
            "light": ["off", "on"],
            "powerful": ["off", "on"],
            "economy": ["off", "on"],
        }


class Tclv2(PulseBased):

    STARTFRAME = [3800, 1650]
    MARK = [500]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [325, 1050]  # ditto

    def __init__(self):
        super().__init__("TCL112AC", variant=irhvac.GZ055BE1)
        self.capabilities = {
            "mode": ["off", "cool", "dry", "fan", "heat"],
            "temperature": [16, 31],
            "fan": ["auto", "high", "medium", "low", "lowest"],
            "swing": ["off", "auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": ["off", "on"],
            "quiet": ["off", "on"],
            "purifier": ["off", "on"],
            "light": ["off", "on"],
            "powerful": ["off", "on"],
            "economy": ["off", "on"],
        }


class Technibel(PulseBased):

    STARTFRAME = [8836, 4380]
    MARK = [523]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [564, 1696]  # ditto

    def __init__(self):
        super().__init__("TECHNIBEL_AC")
        self.capabilities = {
            "mode": ["cool", "dry", "fan", "heat"],
            "temperature": [16, 31],
            "fan": ["high", "medium", "low"],
            "swing": ["off", "on"],
            "sleep": ["off", "on"],
        }


class Teco(PulseBased):

    STARTFRAME = [9000, 4440]
    MARK = [620]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [580, 1650]  # ditto

    def __init__(self):
        super().__init__("TECHNIBEL_AC")
        self.capabilities = {
            "mode": ["auto", "cool", "dry", "fan", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "sleep": ["off", "on"],
            "light": ["off", "on"],
        }


class Toshiba(PulseBased):

    STARTFRAME = [9000, 4440]
    MARK = [620]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [580, 1650]  # ditto

    def __init__(self):
        super().__init__("TOSHIBA_AC")
        self.capabilities = {
            "mode": ["auto", "cool", "dry", "fan", "heat"],
            "temperature": [17, 30],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
            "powerful": ["off", "on"],
            "economy": ["off", "on"],
            "purifier": ["off", "on"],
        }


class Transcold(PulseBased):

    STARTFRAME = [5944, 7563]
    MARK = [555]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [1526, 3556]  # ditto

    def __init__(self):
        super().__init__("TRANSCOLD")
        self.capabilities = {
            "mode": ["auto", "cool", "dry", "fan", "heat"],
            "temperature": [17, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
        }


class Trotech(PulseBased):

    STARTFRAME = [5952, 7364]
    MARK = [592]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [592, 1560]  # ditto
    TAIL = [592, 6184]

    def __init__(self):
        super().__init__("TROTECH")
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
        super().__init__("TROTECH_3550")
        self.capabilities = {
            "mode": ["auto", "cool", "dry", "fan"],
            "temperature": [16, 30],
            "fan": ["high", "medium", "low"],
            "swing": ["off", "on"],
        }


class Truma(PulseBased):
    LEAD = [20200, 1000]
    STARTFRAME = [1800, 630]
    MARK = [1200, 600]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [630]  # ditto
    TAIL = [500, 100000]

    def __init__(self):
        super().__init__("TRUMA")
        self.capabilities = {
            "mode": ["auto", "cool", "fan"],
            "temperature": [16, 31],
            "fan": ["high", "medium", "low"],
            "quiet": ["off", "on"],
        }


class Vestel(PulseBased):
    MARK = [1026]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [554, 2553]  # ditto

    def __init__(self):
        super().__init__("VESTEL_AC")
        self.capabilities = {
            "mode": ["auto", "cool", "dry", "fan", "heat"],
            "temperature": [16, 30],
            "fan": ["high", "medium", "low"],
            "swing": ["off", "on"],
            "sleep": ["off", "on"],
            "powerful": ["off", "on"],
            "purifier": ["off", "on"],
        }


class Voltas(PulseBased):
    STARTFRAME = [3110, 9066]
    MARK = [520]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [480, 1535]  # ditto

    def __init__(self):
        super().__init__("VOLTAS", variant=irhvac.kVoltasUnknown)
        self.capabilities = {
            "mode": ["cool", "dry", "fan", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "economy": ["off", "on"],
            "powerful": ["off", "on"],
            "light": ["off", "on"],
            "sleep": ["off", "on"],
        }


class Voltasv2(PulseBased):
    STARTFRAME = [3110, 9066]
    MARK = [520]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [480, 1535]  # ditto

    def __init__(self):
        super().__init__("VOLTAS", variant=irhvac.kVoltas122LZF)
        self.capabilities = {
            "mode": ["cool", "dry", "fan", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "economy": ["off", "on"],
            "powerful": ["off", "on"],
            "light": ["off", "on"],
            "sleep": ["off", "on"],
        }


# HERE HERE hereby


class Whirlpool(PulseBased):
    STARTFRAME = [3110, 9066]
    MARK = [520]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [480, 1535]  # ditto

    def __init__(self):
        super().__init__("VHIRLPOOL_AC", variant=irhvac.DG11J13A)
        self.capabilities = {
            "mode": ["auto", "cool", "dry", "fan", "heat"],
            "temperature": [18, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "light": ["off", "on"],
            "sleep": ["off", "on"],
            "powerful": ["off", "on"],
        }


class Whirlpoolv2(PulseBased):
    STARTFRAME = [3110, 9066]
    MARK = [520]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [480, 1535]  # ditto

    def __init__(self):
        super().__init__("VHIRLPOOL_AC", variant=irhvac.DG11J191)
        self.capabilities = {
            "mode": ["auto", "cool", "dry", "fan", "heat"],
            "temperature": [18, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "light": ["off", "on"],
            "sleep": ["off", "on"],
            "powerful": ["off", "on"],
        }


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        # Airton
        "Airton SMVH09B-2A2A3NH": Airton,
        "Airton RD1A1": Airton,
        "Airton": Airton,
        # Airwell
        "Airwell DC Series": Airwell,
        "Airwell RC08W remote": Airwell,
        "Airwell RC04 remote": Airwell,
        "Airwell": Airwell,
        # Amcor
        "Amcor ADR-853H": Amcor,
        "Amcor TAC-495 remote": Amcor,
        "Amcor TAC-444 remote": Amcor,
        "Amcor": Amcor,
        # Argo
        "Argo Ulisse 13 DCI": Argo,
        "Argo WREM2 remote": Argo,
        "Argo Ulisse Eco Mobile": Argo2,
        "Argo WREM3 remote": Argo2,
        # Bosh
        "Bosh CL3000i-Set 26 E": Bosh,
        "Bosh RG10A(G2S)BGEF remote": Bosh,
        "Bosh": Bosh,
        # Carrier
        "Carrier 42QG5A55970 remote": Carrier,
        "Carrier 619EGX0090E0": Carrier,
        "Carrier 619EGX0120E0": Carrier,
        "Carrier 619EGX0180E0": Carrier,
        "Carrier 619EGX0220E0": Carrier,
        "Carrier 53NGK009/012": Carrier,
        # Coolix
        "Beko RG57K7(B)/BGEF Remote": Coolix,
        "Beko BINR 070/071": Coolix,
        "Midea RG52D/BGE Remote": Coolix,
        "Midea MS12FU-10HRDN1-QRD0GW(B)": Coolix,
        "Midea MSABAU-07HRFN1-QRD0GW": Coolix,
        "Tokio AATOEMF17-12CHR1SW": Coolix,
        "Tokio RG51|50/BGE Remote": Coolix,
        "Airwell RC08B remote": Coolix,
        "Kastron RG57A7/BGEF remote": Coolix,
        "Kaysun Casual CF": Coolix,
        "Toshiba RAS-M10YKV-E": Coolix,
        "Toshiba RAS-M13YKV-E": Coolix,
        "Toshiba RAS-4M27YAV-E": Coolix,
        "Toshiba WH-E1YE remote": Coolix,
        "Bosch RG36B4/BGE remote": Coolix,
        "Bosch B1ZAI2441W": Coolix,
        "Bosch B1ZAO2441W": Coolix,
        "Coolix": Coolix,
        # Corona
        "Corona CSH-N2211": Corona,
        "Corona CSH-N2511": Corona,
        "Corona CSH-N2811": Corona,
        "Corona CSH-N4011": Corona,
        "Corona AR-01 remote": Corona,
        "Corona": Corona,
        # Daikin
        "Daikin ARC433 remote": Daikin,
        "Daikin ARC477A1 remote": Daikin2,
        "Daikin FTXZ25NV1B": Daikin2,
        "Daikin FTXZ35NV1B": Daikin2,
        "Daikin FTXZ50NV1B": Daikin2,
        "Daikin ARC433B69 remote": Daikin216,
        "Daikin ARC423A5 remote": Daikin160,
        "Daikin FTE12HV2S": Daikin160,
        "Daikin BRC4C153 remote": Daikin176,
        "Daikin FFQ35B8V1B": Daikin176,
        "Daikin BRC4C151 remote": Daikin176,
        "Daikin 17 Series FTXB09AXVJU": Daikin128,
        "Daikin 17 Series FTXB12AXVJU": Daikin128,
        "Daikin 17 Series FTXB24AXVJU": Daikin128,
        "Daikin BRC52B63 remote": Daikin128,
        "Daikin ARC480A5 remote": Daikin152,
        "Daikin FFN-C/FCN-F Series": Daikin64,
        "Daikin DGS01 remote": Daikin64,
        "Daikin M Series": Daikin,
        "Daikin FTXM-M": Daikin,
        "Daikin ARC466A12 remote": Daikin,
        "Daikin ARC466A33 remote": Daikin,
        "Daikin FTWX35AXV1": Daikin64,
        "Daikin ARC484A4 remote": Daikin216,
        "Daikin FTQ60TV16U2": Daikin216,
        # "Daikin BRC4M150W16 remote": Daikin200,
        # "Daikin FTXM20R5V1B": Daikin312,
        # "Daikin ARC466A67 remote": Daikin312,
        "Daikin": Daikin,
        "Daikin2": Daikin2,
        "Daikin64": Daikin64,
        "Daikin128": Daikin128,
        "Daikin152": Daikin152,
        "Daikin160": Daikin160,
        "Daikin176": Daikin176,
        "Daikin216": Daikin216,
        # Delonghi
        "Delonghi PAC A95": Delonghi,
        "Delonghi": Delonghi,
        # Electra
        "AUX KFR-35GW/BpNFW=3": Electra,
        "AUX YKR-T/011 remote": Electra,
        "Electra Classic INV 17": Electra,
        "Electra AXW12DCS": Electra,
        "Electra YKR-M/003E remote": Electra,
        "Frigidaire FGPC102AB1": Electra,
        "Subtropic SUB-07HN1_18Y": Electra,
        "Subtropic YKR-H/102E remote": Electra,
        "Centek SCT-65Q09": Electra,
        "Centek YKR-P/002E remote": Electra,
        "AEG Chillflex Pro AXP26U338CW": Electra,
        "Electrolux YKR-H/531E": Electra,
        "Delonghi PAC EM90": Electra,
        "Electra": Electra,
        # Fujitsu
        "Fujitsu AR-RAH2E remote": Fujitsuv1,
        "Fujitsu ASYG30LFCA": Fujitsuv1,
        "Fujitsu General AR-RCE1E remote": Fujitsuv1,
        "Fujitsu General ASHG09LLCA": Fujitsuv1,
        "Fujitsu General AOHG09LLC": Fujitsuv1,
        "Fujitsu AR-DB1 remote": Fujitsuv2,
        "Fujitsu AST9RSGCW": Fujitsuv2,
        "Fujitsu AR-REB1E remote": Fujitsuv3,
        "Fujitsu ASYG7LMCA": Fujitsuv3,
        "Fujitsu AR-RAE1E remote": Fujitsuv1,
        "Fujitsu AGTV14LAC": Fujitsuv1,
        "Fujitsu AR-RAC1E remote": Fujitsuv1,
        "Fujitsu ASTB09LBC": Fujitsuv5,
        "Fujitsu AR-RY4 remote": Fujitsuv5,
        "Fujitsu General AR-JW2 remote": Fujitsuv4,
        "Fujitsu AR-DL10 remote": Fujitsuv2,
        "Fujitsu ASU30C1": Fujitsuv2,
        "Fujitsu AR-RAH1U remote": Fujitsuv3,
        "Fujitsu AR-RAH2U remote": Fujitsuv1,
        "Fujitsu ASU12RLF": Fujitsuv3,
        "Fujitsu AR-REW4E remote": Fujitsuv6,
        "Fujitsu ASYG09KETA-B": Fujitsuv6,
        "Fujitsu AR-REB4E remote": Fujitsuv3,
        "Fujitsu ASTG09K": Fujitsuv6,
        "Fujitsu ASTG18K": Fujitsuv6,
        "Fujitsu AR-REW1E remote": Fujitsuv6,
        "Fujitsu AR-REG1U remote": Fujitsuv1,
        "OGeneral AR-RCL1E remote": Fujitsuv1,
        "Fujitsu General AR-JW17 remote": Fujitsuv2,
        # Goodweather
        "Goodweather ZH/JT-03 remote": Goodweather,
        "Goodweather": Goodweather,
        # Gree
        "Ultimate Heat Pump": Greev1,
        "EKOKAI": Greev1,
        "RusClimate EACS/I-09HAR_X/N3": Greev1,
        "RusClimate YAW1F remote": Greev1,
        "Green YBOFB remote": Greev2,
        "Green YBOFB2 remote": Greev2,
        "Gree YAA1FBF remote": Greev1,
        "Gree YB1F2F remote": Greev1,
        "Gree YAN1F1 remote": Greev1,
        "Gree YX1F2F remote": Greev3,
        "Gree VIR09HP115V1AH": Greev1,
        "Gree VIR12HP230V1AH": Greev1,
        "Amana PBC093G00CC": Greev1,
        "Amana YX1FF remote": Greev1,
        "Cooper & Hunter YB1F2 remote": Greev1,
        "Cooper & Hunter CH-S09FTXG": Greev1,
        "Vailland YACIFB remote": Greev1,
        "Vailland VAI5-035WNI": Greev1,
        "Soleus Air window": Greev3,
        # Haier
        "Haier HSU07-HEA03 remote": Haier,
        "Haier YR-W02 remote": HaierYRW02A,
        "Haier HSU-09HMC203": HaierYRW02A,
        "Haier V9014557 M47 8D remote": Haier176A,
        "Mabe MMI18HDBWCA6MI8": Haier176A,
        "Mabe V12843 HJ200223 remote": Haier176A,
        "Daichi D-H": Haier176A,
        "Haier KFR-26GW/83@UI-Ge": Haier160,
        "Haier": Haier,
        "Haier YR-W02 Code A": HaierYRW02A,
        "Haier YR-W02 Code B": HaierYRW02B,
        "Haier 176 Code A": Haier176A,
        "Haier 176 Code B": Haier176B,
        "Haier 160": Haier160,
        # Hitachi
        "Hitachi RAS-35THA6 remote": Hitachi,
        "Hitachi LT0541-HTA remote": Hitachi1A,
        "Hitachi Series VI": Hitachi1A,
        "Hitachi RAR-8P2 remote": Hitachi424,
        "Hitachi RAS-AJ25H": Hitachi424,
        "Hitachi PC-LH3B": Hitachi3,
        "Hitachi KAZE-312KSDP": Hitachi1A,
        "Hitachi R-LT0541-HTA/Y.K.1.1-1 V2.3 remote": Hitachi1A,
        "Hitachi RAS-22NK": Hitachi344,
        "Hitachi RF11T1": Hitachi344,
        "Hitachi RAR-2P2 remote": Hitachi264,
        "Hitachi RAK-25NH5": Hitachi264,
        "Hitachi RAR-3U3 remote": Hitachi296,
        "Hitachi RAS-70YHA3": Hitachi296,
        "Hitachi": Hitachi,
        "Hitachi1 Code A": Hitachi1A,
        "Hitachi1 Code B": Hitachi1B,
        "Hitachi424": Hitachi424,
        "Hitachi3": Hitachi3,
        "Hitachi344": Hitachi344,
        "Hitachi264": Hitachi264,
        "Hitachi296": Hitachi296,
        # Kelon
        "Kelon remote": Kelon,
        # Kelvinator
        "Kelvinator YALIF remote": Kelvinator,
        "Kelvinator KSV26CRC": Kelvinator,
        "Kelvinator KSV26HRC": Kelvinator,
        "Kelvinator KSV35CRC": Kelvinator,
        "Kelvinator KSV35HRC": Kelvinator,
        "Kelvinator KSV53HRC": Kelvinator,
        "Kelvinator KSV62HRC": Kelvinator,
        "Kelvinator KSV70CRC": Kelvinator,
        "Kelvinator KSV70HRC": Kelvinator,
        "Kelvinator KSV80HRC": Kelvinator,
        "Gree YAPOF3 remote": Kelvinator,
        "Gree YAP0F8 remote": Kelvinator,
        "Sharp YB1FA remote": Kelvinator,
        "Sharp A5VEY": Kelvinator,
        # LG
        "LG 6711A20083V  remote": LGv2,
        "LG TS-H122ERM1  remote": LGv2,
        "LG AKB74395308  remote": LG2v1,
        "LG S4-W12JA3AA": LG2v1,
        "LG AKB75215403  remote": LG2v1,
        "LG AKB74955603  remote": LG2v2,
        "LG A4UW30GFA2": LG2v2,
        "LG AMNW09GSJA0": LG2v2,
        "LG AMNW24GTPA1": LG2v3,
        "LG AKB73757604  remote": LG2v3,
        "LG AKB73315611  remote": LG2v2,
        "LG MS05SQ NW0": LG2v2,
        "General Electric AG1BH09AW101": LGv1,
        "General Electric 6711AR2853M Remote": LGv1,
        # Midea
        "Pioneer System RYBO12GMFILCAD": Midea,
        "Pioneer System RUBO18GMFILCAD": Midea,
        "Pioneer System WS012GMFI22HLD": Midea,
        "Pioneer System WS018GMFI22HLD": Midea,
        "Pioneer System UB018GMFILCFHD": Midea,
        "Pioneer System RG66B6(B)/BGEFU1 remote": Midea,
        "Comfee MPD1-12CRN7": Midea,
        "Kaysun Casual CF": Midea,
        "Keystone RG57H4(B)BGEF remote": Midea,
        "MrCool RG57A6/BGEFU1 remote": Midea,
        "Danby DAC080BGUWDB": Midea,
        "Danby DAC100BGUWDB": Midea,
        "Danby DAC120BGUWDB": Midea,
        "Danby R09C/BCGE remote": Midea,
        "Trotec TROTEC PAC 2100 X": Midea,
        "Trotec TROTEC PAC 3900 X": Midea,
        "Trotec RG57H(B)/BGE remote": Midea,
        "Trotec RG57H3(B)/BGCEF-M remote": Midea,
        "Lennox RG57A6/BGEFU1 remote": Midea,
        "Lennox MWMA009S4-3P": Midea,
        "Lennox MWMA012S4-3P": Midea,
        "Lennox MCFA": Midea,
        "Lennox MCFB": Midea,
        "Lennox MMDA": Midea,
        "Lennox MMDB": Midea,
        "Lennox MWMA": Midea,
        "Lennox MWMB": Midea,
        "Lennox M22A": Midea,
        "Lennox M33A": Midea,
        "Lennox M33B": Midea,
        "Midea": Midea,
        # Mirage
        "Mirage VLU series": Miragev1,
        "Maxell MX-CH18CF": Miragev1,
        "Maxell KKG9A-C1 remote": Miragev1,
        "Tronitechnik Reykir 9000": Miragev2,
        "Tronitechnik KKG29A-C1 remote": Miragev2,
        # Mitsubishi
        "Mitsubishi MS-GK24VA": Mitsubishi,
        "Mitsubishi KM14A 0179213 remote": Mitsubishi,
        "Mitsubishi Electric PEAD-RP71JAA Ducted": Mitsubishi136,
        "Mitsubishi Electric 001CP T7WE10714 remote": Mitsubishi136,
        "Mitsubishi Electric MSH-A24WV": Mitsubishi112,
        "Mitsubishi Electric MUH-A24WV": Mitsubishi112,
        "Mitsubishi Electric KPOA remote": Mitsubishi112,
        "Mitsubishi Electric MLZ-RX5017AS": Mitsubishi,
        "Mitsubishi Electric SG153/M21EDF426 remote": Mitsubishi,
        "Mitsubishi Electric MSZ-GV2519": Mitsubishi,
        "Mitsubishi Electric RH151/M21ED6426 remote": Mitsubishi,
        "Mitsubishi Electric MSZ-SF25VE3": Mitsubishi,
        "Mitsubishi Electric SG15D remote": Mitsubishi,
        "Mitsubishi Electric MSZ-ZW4017S": Mitsubishi,
        "Mitsubishi Electric MSZ-FHnnVE": Mitsubishi,
        "Mitsubishi Electric RH151 remote": Mitsubishi,
        "Mitsubishi Electric PAR-FA32MA remote": Mitsubishi136,
        "Mitsubishi": Mitsubishi,
        "Mitsubishi136": Mitsubishi136,
        "Mitsubishi112": Mitsubishi112,
        "Mitsubishi Heavy Industries RLA502A700B remote": Mitsubishi152,
        "Mitsubishi Heavy Industries SRKxxZM-S A/C": Mitsubishi152,
        "Mitsubishi Heavy Industries SRKxxZMXA-S A/C": Mitsubishi152,
        "Mitsubishi Heavy Industries RKX502A001C remote": Mitsubishi88,
        "Mitsubishi Heavy Industries SRKxxZJ-S A/C": Mitsubishi88,
        "Mitsubishi152": Mitsubishi152,
        "Mitsubishi88": Mitsubishi88,
        # Neoclima
        "Neoclima NS-09AHTI": Neoclima,
        "Neoclima ZH/TY-01 remote": Neoclima,
        "Soleus Air TTWM1-10-01": Neoclima,
        "Soleus Air ZCF/TL-05 remote": Neoclima,
        "Neoclima": Neoclima,
        # Panasonic
        "Panasonic NKE series": PanasonicNke,
        "Panasonic DKE series": PanasonicDke,
        "Panasonic DKW series": PanasonicDke,
        "Panasonic PKR series": PanasonicDke,
        "Panasonic JKE series": PanasonicJke,
        "Panasonic CKP series": PanasonicCkp,
        "Panasonic RKR series": PanasonicRkr,
        "Panasonic CS-ME10CKPG": PanasonicCkp,
        "Panasonic CS-ME12CKPG": PanasonicCkp,
        "Panasonic CS-ME14CKPG": PanasonicCkp,
        "Panasonic CS-E7PKR": PanasonicDke,
        "Panasonic CS-Z9RKR": PanasonicRkr,
        "Panasonic CS-Z24RKR": PanasonicRkr,
        "Panasonic CS-YW9MKD": PanasonicJke,
        "Panasonic CS-E12QKEW": PanasonicDke,
        "Panasonic A75C2311remote": PanasonicCkp,
        "Panasonic A75C2616-1remote": PanasonicDke,
        "Panasonic A75C3704remote": PanasonicDke,
        "Panasonic PN1122Vremote": PanasonicDke,
        "Panasonic A75C3747remote": PanasonicJke,
        "Panasonic CS-E9CKP series": Panasonic32,
        "Panasonic A75C2295remote": Panasonic32,
        "Panasonic A75C4762remote": PanasonicRkr,
        "Panasonic32": Panasonic32,
        # Rhoss
        "Rhoss, Idrowall MPCV": Rhoss,
        "Rhoss": Rhoss,
        # Samsung
        "Samsung AR09FSSDAWKNFA": Samsung,
        "Samsung AR09HSFSBWKN": Samsung,
        "Samsung AR12KSFPEWQNET": Samsung,
        "Samsung AR12HSSDBWKNEU": Samsung,
        "Samsung AR12NXCXAWKXEU": Samsung,
        "Samsung AR12TXEAAWKNEU": Samsung,
        "Samsung DB93-14195A remote": Samsung,
        "Samsung DB96-24901C remote": Samsung,
        "Samsung": Samsung,
        # Sanyo
        "Sanyo SAP-K121AHA": Sanyo,
        "Sanyo RCS-2HS4E remote": Sanyo,
        "Sanyo SAP-K242AH": Sanyo,
        "Sanyo RCS-2S4E remote": Sanyo,
        "Sanyo": Sanyo,
        "Sanyo88": Sanyo88,
        # Sharp
        "Sharp AY-ZP40KR": SharpA907,
        "Sharp AH-AxSAY": SharpA907,
        "Sharp CRMC-A907 JBEZ remote": SharpA907,
        "Sharp CRMC-A950 JBEZ": SharpA907,
        "Sharp AH-PR13-GL": SharpA903,
        "Sharp CRMC-A903JBEZ remote": SharpA903,
        "Sharp AH-XP10NRY": SharpA903,
        "Sharp CRMC-820 JBEZ remote": SharpA903,
        "Sharp CRMC-A705 JBEZ remote": SharpA705,
        "Sharp AH-A12REVP-1": SharpA903,
        "Sharp CRMC-A863 JBEZ remote": SharpA903,
        "Sharp A907": SharpA907,
        "Sharp A903": SharpA903,
        "Sharp A705": SharpA705,
        # TCL
        "Leberg LBS-TOR07": Tclv1,
        "TCL TAC-09CHSD/XA31I": Tclv1,
        "Teknopoint Allegro SSA-09H": Tclv2,
        "Teknopoint GZ-055B-E1 remote": Tclv2,
        "Daewoo DSB-F0934ELH-V": Tclv2,
        "Daewoo GYKQ-52E remote": Tclv2,
        "TCLvc1": Tclv1,
        "TCLv2": Tclv2,
        # Technibel
        "Technibel IRO PLUS": Technibel,
        "Technibel": Technibel,
        # Teco
        "Alaska SAC9010QC": Teco,
        "Alaska SAC9010QC remote": Teco,
        "Teco": Teco,
        # Toshiba
        "Toshiba RAS-B13N3KV2": Toshiba,
        "Toshiba Akita EVO II": Toshiba,
        "Toshiba RAS-B13N3KVP-E": Toshiba,
        "Toshiba RAS 18SKP-ES": Toshiba,
        "Toshiba WH-TA04NE": Toshiba,
        "Toshiba WC-L03SE": Toshiba,
        "Toshiba WH-UB03NJ remote": Toshiba,
        "Toshiba RAS-2558V": Toshiba,
        "Toshiba WH-TA01JE remote": Toshiba,
        "Toshiba RAS-25SKVP2-ND": Toshiba,
        "Carrier 42NQV060M2 / 38NYV060M2": Toshiba,
        "Carrier 42NQV050M2 / 38NYV050M2": Toshiba,
        "Carrier 42NQV035M2 / 38NYV035M2": Toshiba,
        "Carrier 42NQV025M2 / 38NYV025M2": Toshiba,
        "Toshiba": Toshiba,
        # Transcold
        "Transcold M1-F-NO-6": Transcold,
        "Transcold": Transcold,
        # Trotech
        "Trotec PAC 3200": Trotech,
        "Trotec PAC 3550 Pro": Trotech3550,
        "Duux Blizzard Smart 10K / DXMA04": Trotech,
        "Trotech": Trotech,
        "Trotech 3550": Trotech3550,
        # Truma
        "Truma Aventa": Truma,
        "Truma 40091-86700 remote": Truma,
        "Truma": Truma,
        # Vestel
        "Vestel BIOX CXP-9": Vestel,
        "Vesatel": Vestel,
        # Voltas
        "Voltas 122LZF 4011252": Voltasv2,
        "Voltas": Voltas,
        "Voltas Alt": Voltasv2,
        # Whirlpool
        "WhirlpoolDG11J1-3A remote": Whirlpool,
        "WhirlpoolDG11J1-04 remote": Whirlpool,
        "WhirlpoolDG11J1-91 remote": Whirlpoolv2,
        "WhirlpoolSPIS409L": Whirlpool,
        "WhirlpoolSPIS412L": Whirlpool,
        "WhirlpoolSPIW409L": Whirlpool,
        "WhirlpoolSPIW412L": Whirlpool,
        "WhirlpoolSPIW418L": Whirlpool,
        "Whirlpool": Whirlpool,
        "Whirlpool Alt": Whirlpoolv2,
    }

    def __init__(self):
        self.brand = "arduino"
