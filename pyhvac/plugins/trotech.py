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

from .hvaclib import PulseBased, GenPluginObject
from .midea import Midea


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
