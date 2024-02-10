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
from ..irhvac import DG11J13A, DG11J191


class Whirlpool(PulseBased):
    STARTFRAME = [3110, 9066]
    MARK = [520]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [480, 1535]  # ditto

    def __init__(self):
        super().__init__("VHIRLPOOL_AC", variant=DG11J13A)
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
        super().__init__("VHIRLPOOL_AC", variant=DG11J191)
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
        "DG11J1-3A remote": Whirlpool,
        "DG11J1-04 remote": Whirlpool,
        "DG11J1-91 remote": Whirlpoolv2,
        "SPIS409L": Whirlpool,
        "SPIS412L": Whirlpool,
        "SPIW409L": Whirlpool,
        "SPIW412L": Whirlpool,
        "SPIW418L": Whirlpool,
        "generic": Whirlpool,
        "generic 2": Whirlpoolv2,
    }

    def __init__(self):
        self.brand = "whirlpool"
