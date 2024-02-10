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
from ..irhvac import TAC09CHSD, GZ055BE1


class Tclv1(PulseBased):

    STARTFRAME = [3800, 1650]
    MARK = [500]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [325, 1050]  # ditto

    def __init__(self):
        super().__init__("TCL112AC", variant=TAC09CHSD)
        self.capabilities = {
            "mode": ["off", "cool", "dry", "fan", "heat"],
            "temperature": [16, 31],
            "fan": ["auto", "high", "medium", "low", "lowest"],
            "swing": ["off", "auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": ["off", "on"],
            "quiet": ["off", "on"],
            "purifier": ["off", "on"],
            "light": ["off", "on"],
            "powerful": ["off", "on"],
            "economy": ["off", "on"],
        }


class Tclv2(PulseBased):

    STARTFRAME = [3800, 1650]
    MARK = [500]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [325, 1050]  # ditto

    def __init__(self):
        super().__init__("TCL112AC", variant=GZ055BE1)
        self.capabilities = {
            "mode": ["off", "cool", "dry", "fan", "heat"],
            "temperature": [16, 31],
            "fan": ["auto", "high", "medium", "low", "lowest"],
            "swing": ["off", "auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": ["off", "on"],
            "quiet": ["off", "on"],
            "purifier": ["off", "on"],
            "light": ["off", "on"],
            "powerful": ["off", "on"],
            "economy": ["off", "on"],
        }


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "TAC-09CHSD/XA31I": Tclv1,
        "generic": Tclv1,
        "generic v1": Tclv1,
        "generic v2": Tclv2,
    }

    def __init__(self):
        self.brand = "tcl"
