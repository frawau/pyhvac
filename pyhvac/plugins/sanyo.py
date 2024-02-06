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


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "SAP-K121AHA": Sanyo,
        "RCS-2HS4E remote": Sanyo,
        "SAP-K242AH": Sanyo,
        "RCS-2S4E remote": Sanyo,
        "generic": Sanyo,
        "generic 88": Sanyo88,
    }

    def __init__(self):
        self.brand = "sanyo"
