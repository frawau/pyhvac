#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Panasonic AC IR commands
#
# This module without the work/code from:
#      Scott Kyle https://gist.github.com/appden/42d5272bf128125b019c45bc2ed3311f
#      mat_fr     https://www.instructables.com/id/Reverse-engineering-of-an-Air-Conditioning-control/
#      user two, mathieu, vincent
#                 https://www.analysir.com/blog/2014/12/27/reverse-engineering-panasonic-ac-infrared-protocol/
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
from .. import irhvac

# from hashlib import blake2b


def bit_reverse(i, n=8):
    return int(format(i, "0%db" % n)[::-1], 2)


class HVAC(object):
    # 90% of hvac remotes use this timing
    STARTFRAME = [3500, 1750]
    ENDFRAME = [435, 10000]
    MARK = 435
    SPACE0 = 435
    SPACE1 = 1300

    def __init__(self):
        self.brand = "Generic"
        self.model = "Generic"
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry"],
            "temperature": [x for x in range(18, 30)],
        }
        # For functions that require their own frames
        self.xtra_capabilities = {}
        self.status = {"mode": "auto", "temperature": 25}
        self.temperature_step = 1.0

        self.to_set = {}
        # Specify whether the bits order has to be swapped
        self.is_msb = False

    @property
    def all_capabilities(self):
        return self.capabilities | self.xtra_capabilities

    def get_timing(self):
        return {
            "start frame": self.STARTFRAME,
            "end frame": self.ENDFRAME,
            "mark": self.MARK,
            "space 0": self.SPACE0,
            "space 1": self.SPACE1,
        }

    def set_value(self, name, value):
        try:
            xx = getattr(self, "set_" + name)(value)
        except:
            # Does no exisat. Ignore
            pass

    def update_status(self):
        for x, y in self.to_set.items():
            self.status[x] = y
        self.to_set = {}

    def build_ircode(self):
        frames = self._build_ircode()
        if self.is_msb:
            newframes = []
            for f in frames:
                newframes.append(bytearray([bit_reverse(x) for x in f]))
            frames = newframes
        # print("Frame with msb {} are:".format(self.is_msb))
        # for f in frames:
        # print(["0x%02x"%x for x in f])
        return frames

    def to_lirc(self, frames):
        """Transform a list of frames into a LIRC compatible list of pulse timing pairs."""
        lircframe = []
        for frame in frames:
            lircframe += self.STARTFRAME
            for x in frame:
                idx = 0x80
                while idx:
                    lircframe.append(self.MARK)
                    if x & idx:
                        lircframe.append(self.SPACE1)
                    else:
                        lircframe.append(self.SPACE0)
                    idx >>= 1
            lircframe += self.ENDFRAME
        return lircframe

    def to_broadlink(self, frames):
        """Transform a list of frames to a Broadlink compatible byte string."""
        pulses = [int(x) for x in self.to_lirc(frames)]
        array = bytearray()
        for pulse in pulses:
            pulse = round(pulse * 269 / 8192)  # 32.84ms units

            if pulse < 256:
                array += bytearray(struct.pack(">B", pulse))  # big endian (1-byte)
            else:
                array += bytearray([0x00])  # indicate next number is 2-bytes
                array += bytearray(struct.pack(">H", pulse))  # big endian (2-bytes)

        packet = bytearray([0x26, 0x00])  # 0x26 = IR, 0x00 = no repeats
        packet += bytearray(struct.pack("<H", len(array)))  # little endian byte count
        packet += array
        packet += bytearray([0x0D, 0x05])  # IR terminator

        # Add 0s to make ultimate packet size a multiple of 16 for 128-bit AES encryption.
        remainder = (
            len(packet) + 4
        ) % 16  # rm.send_data() adds 4-byte header (02 00 00 00)
        if remainder:
            packet += bytearray(16 - remainder)

        return packet


class IRGHVAC(HVAC):
    """
    This is the main object handling IR code generated by IRremoteESP8266 library
    """

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


class GenPluginObject(object):
    MODELS = {"generic": HVAC}

    def __init__(self):
        self.brand = "Unknown"

    def get_device(self, model):
        if model not in self.MODELS:
            return self.MODELS["generic"]()
        return self.MODELS[model]()

    def all_models(self, dev):
        return [k for k, v in self.MODELS.items() if type(dev) is v]
