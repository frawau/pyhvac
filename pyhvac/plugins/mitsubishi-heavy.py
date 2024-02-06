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


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "RLA502A700B remote": Mitsubishi152,
        "SRKxxZM-S A/C": Mitsubishi152,
        "SRKxxZMXA-S A/C": Mitsubishi152,
        "RKX502A001C remote": Mitsubishi88,
        "SRKxxZJ-S A/C": Mitsubishi88,
        "gemeric": Mitsubishi152,
        "gemeric 152": Mitsubishi152,
        "generic 88": Mitsubishi88,
    }

    def __init__(self):
        self.brand = "mitsubishi heavy industries"
