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


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "AR09FSSDAWKNFA": Samsung,
        "AR09HSFSBWKN": Samsung,
        "AR12KSFPEWQNET": Samsung,
        "AR12HSSDBWKNEU": Samsung,
        "AR12NXCXAWKXEU": Samsung,
        "AR12TXEAAWKNEU": Samsung,
        "DB93-14195A remote": Samsung,
        "DB96-24901C remote": Samsung,
        "generic": Samsung,
    }

    def __init__(self):
        self.brand = "samsung"
