#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Midea AC IR commands.
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
from .coolix import Coolix


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


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "generic": Midea,
        "RG52D/BGE Remote": Coolix,
        "MS12FU-10HRDN1-QRD0GW(B)": Coolix,
        "MSABAU-07HRFN1-QRD0GW": Coolix,
    }

    def __init__(self):
        self.brand = "midea"
