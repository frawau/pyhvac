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


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "YALIF remote": Kelvinator,
        "KSV26CRC": Kelvinator,
        "KSV26HRC": Kelvinator,
        "KSV35CRC": Kelvinator,
        "KSV35HRC": Kelvinator,
        "KSV53HRC": Kelvinator,
        "KSV62HRC": Kelvinator,
        "KSV70CRC": Kelvinator,
        "KSV70HRC": Kelvinator,
        "KSV80HRC": Kelvinator,
        "generic": Kelvinator,
    }

    def __init__(self):
        self.brand = "kelvinator"
