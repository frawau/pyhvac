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
from ..irhvac import ARRAH2E, ARDB1, ARREB1E, ARJW2, ARRY4, ARREW4E


class Fujitsuv1(PulseBased):

    STARTFRAME = [3324, 1574]
    ENDFRAME = None
    MARK = [440]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [390, 1182]  # ditto

    def __init__(self):
        super().__init__("FUJITSU_AC", variant=ARRAH2E)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "fan", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "quiet": ["off", "on"],
        }


class Fujitsuv2(PulseBased):

    STARTFRAME = [3324, 1574]
    ENDFRAME = None
    MARK = [440]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [390, 1182]  # ditto

    def __init__(self):
        super().__init__("FUJITSU_AC", variant=ARDB1)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "fan", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
            "quiet": ["off", "on"],
        }


class Fujitsuv3(PulseBased):

    STARTFRAME = [3324, 1574]
    ENDFRAME = None
    MARK = [440]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [390, 1182]  # ditto

    def __init__(self):
        super().__init__("FUJITSU_AC", variant=ARREB1E)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "fan", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
            "economy": ["off", "on"],
        }


class Fujitsuv4(PulseBased):

    STARTFRAME = [3324, 1574]
    ENDFRAME = None
    MARK = [440]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [390, 1182]  # ditto

    def __init__(self):
        super().__init__("FUJITSU_AC", variant=ARJW2)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "fan", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "quiet": ["off", "on"],
        }


class Fujitsuv5(PulseBased):

    STARTFRAME = [3324, 1574]
    ENDFRAME = None
    MARK = [440]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [390, 1182]  # ditto

    def __init__(self):
        super().__init__("FUJITSU_AC", variant=ARRY4)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "fan", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
            "purifier": ["off", "on"],
            "quiet": ["off", "on"],
            "cleaning": ["off", "on"],
        }


class Fujitsuv6(PulseBased):

    STARTFRAME = [3324, 1574]
    ENDFRAME = None
    MARK = [440]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [390, 1182]  # ditto

    def __init__(self):
        super().__init__("FUJITSU_AC", variant=ARREW4E)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "fan", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
            "economy": ["off", "on"],
        }


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "AR-RAH2E remote": Fujitsuv1,
        "ASYG30LFCA": Fujitsuv1,
        "General AR-RCE1E remote": Fujitsuv1,
        "General ASHG09LLCA": Fujitsuv1,
        "General AOHG09LLC": Fujitsuv1,
        "AR-DB1 remote": Fujitsuv2,
        "AST9RSGCW": Fujitsuv2,
        "AR-REB1E remote": Fujitsuv3,
        "ASYG7LMCA": Fujitsuv3,
        "AR-RAE1E remote": Fujitsuv1,
        "AGTV14LAC": Fujitsuv1,
        "AR-RAC1E remote": Fujitsuv1,
        "ASTB09LBC": Fujitsuv5,
        "AR-RY4 remote": Fujitsuv5,
        "General AR-JW2 remote": Fujitsuv4,
        "AR-DL10 remote": Fujitsuv2,
        "ASU30C1": Fujitsuv2,
        "AR-RAH1U remote": Fujitsuv3,
        "AR-RAH2U remote": Fujitsuv1,
        "ASU12RLF": Fujitsuv3,
        "AR-REW4E remote": Fujitsuv6,
        "ASYG09KETA-B": Fujitsuv6,
        "AR-REB4E remote": Fujitsuv3,
        "ASTG09K": Fujitsuv6,
        "ASTG18K": Fujitsuv6,
        "AR-REW1E remote": Fujitsuv6,
        "AR-REG1U remote": Fujitsuv1,
        "General AR-RCL1E remote": Fujitsuv1,
        "General AR-JW17 remote": Fujitsuv2,
        "generic": Fujitsuv1,
        "generic 2": Fujitsuv2,
        "generic 3": Fujitsuv3,
        "generic 4": Fujitsuv4,
        "generic 5": Fujitsuv5,
        "generic 6": Fujitsuv6,
    }

    def __init__(self):
        self.brand = "fujitsu"
