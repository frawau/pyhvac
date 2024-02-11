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
from .kelvinator import Kelvinator
from ..irhvac import YAW1F, YBOFB, YX1FSF


class Greev1(PulseBased):

    STARTFRAME = [9000, 4500]
    ENDFRAME = None
    MARK = [620]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [540, 1600]  # ditto

    def __init__(self):
        super().__init__("GREE", variant=YAW1F)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "fan", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["auto", "90°", "60°", "45°", "30°", "0°"],
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
        super().__init__("GREE", variant=YBOFB)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "fan", "heat"],
            "temperature": [16, 30],
            "economy": ["off", "on"],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["auto", "90°", "60°", "45°", "30°", "0°"],
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
        super().__init__("GREE", variant=YX1FSF)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "fan", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["auto", "90°", "60°", "45°", "30°", "0°"],
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


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "YAA1FBF remote": Greev1,
        "YB1F2F remote": Greev1,
        "YAN1F1 remote": Greev1,
        "YX1F2F remote": Greev3,
        "VIR09HP115V1AH": Greev1,
        "VIR12HP230V1AH": Greev1,
        "gemeric": Greev1,
        "YAPOF3 remote": Kelvinator,
        "YAP0F8 remote": Kelvinator,
    }

    def __init__(self):
        self.brand = "gree"
