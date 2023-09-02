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

from hashlib import blake2b


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
        # Specify wether the bits order has to be swapped
        self.is_msb = False
        # Names of 'functions' used by this object
        self.functions = []

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
        """Transform a list of frames into a LIRC compatible list of pulse timing pairs"""
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

    def to_broadlink(self, pulses):
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


class GenPluginObject(object):
    MODELS = {"generic": HVAC}

    def __init__(self):
        self.brand = "Unknown"

    def factory(self, model):
        if model not in self.MODELS:
            return self.MODELS["generic"]()
        return self.MODELS[model]()
