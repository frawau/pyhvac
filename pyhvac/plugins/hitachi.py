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
from ..irhvac import R_LT0541_HTA_A, R_LT0541_HTA_B


class Hitachi(PulseBased):

    STARTFRAME = [3300, 1700]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [500, 1250]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC")
        self.capabilities = {
            "mode": ["off", "auto", "heat", "cool", "dry", "fan"],
            "temperature": [16, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
        }


class Hitachi1A(PulseBased):

    STARTFRAME = [3400, 3400]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [372, 1208]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC1", variant=R_LT0541_HTA_A)
        self.capabilities = {
            "mode": ["off", "auto", "heat", "cool", "dry", "fan"],
            "temperature": [16, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "sleep": ["off", "on"],
        }


class Hitachi1B(PulseBased):

    STARTFRAME = [3400, 3400]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [372, 1208]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC1", variant=R_LT0541_HTA_B)
        self.capabilities = {
            "mode": ["off", "auto", "heat", "cool", "dry", "fan"],
            "temperature": [16, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "sleep": ["off", "on"],
        }


class Hitachi424(PulseBased):

    LEAD = [29784, 49290]
    STARTFRAME = [3416, 1604]
    ENDFRAME = None
    MARK = [463]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [500, 1250]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC424")
        self.capabilities = {
            "mode": ["off", "fan", "heat", "cool", "dry"],
            "temperature": [16, 32],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
        }


class Hitachi3(PulseBased):

    STARTFRAME = [3400, 1660]
    ENDFRAME = None
    MARK = [460]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [410, 1250]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC3")
        self.capabilities = {
            "mode": ["off", "fan", "heat", "cool", "dry"],
            "temperature": [16, 32],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
        }


class Hitachi344(PulseBased):

    STARTFRAME = [3300, 1700]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [500, 1250]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC344")
        self.capabilities = {
            "mode": ["off", "cool", "fan", "dry", "heat"],
            "temperature": [16, 32],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
            "hswing": ["auto", "far right", "right", "middle", "left", "far left"],
        }


class Hitachi264(PulseBased):

    STARTFRAME = [3300, 1700]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [500, 1250]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC264")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [16, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "purifier": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
            "economy": ["off", "on"],
            "light": ["off", "on"],
        }


class Hitachi296(PulseBased):

    STARTFRAME = [3300, 1700]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [500, 1250]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC296")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat"],
            "temperature": [16, 25],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
        }


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "RAS-35THA6 remote": Hitachi,
        "LT0541-HTA remote": Hitachi1A,
        "Series VI": Hitachi1A,
        "RAR-8P2 remote": Hitachi424,
        "RAS-AJ25H": Hitachi424,
        "PC-LH3B": Hitachi3,
        "KAZE-312KSDP": Hitachi1A,
        "R-LT0541-HTA/Y.K.1.1-1 V2.3 remote": Hitachi1A,
        "RAS-22NK": Hitachi344,
        "RF11T1": Hitachi344,
        "RAR-2P2 remote": Hitachi264,
        "RAK-25NH5": Hitachi264,
        "RAR-3U3 remote": Hitachi296,
        "RAS-70YHA3": Hitachi296,
        "generic": Hitachi,
        "generic 1 code a": Hitachi1A,
        "generic 1 code b": Hitachi1B,
        "generic 424": Hitachi424,
        "generic 3": Hitachi3,
        "generic 344": Hitachi344,
        "generic 264": Hitachi264,
        "generic 296": Hitachi296,
    }

    def __init__(self):
        self.brand = "hitachi"
