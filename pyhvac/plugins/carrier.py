#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Carrier AC IR commands.
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
from .toshiba import Toshiba


class Carrier(PulseBased):

    STARTFRAME = [8940, 4556]
    ENDFRAME = None
    MARK = [503]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [615, 1736]  # ditto

    def __init__(self):
        super().__init__("CARRIER_AC64")
        self.capabilities = {
            "mode": ["off", "cool", "fan" "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
        }


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "42QG5A55970 remote": Carrier,
        "619EGX0090E0": Carrier,
        "619EGX0120E0": Carrier,
        "619EGX0180E0": Carrier,
        "619EGX0220E0": Carrier,
        "53NGK009/012": Carrier,
        "generic": Carrier,
        "42NQV060M2 / 38NYV060M2": Toshiba,
        "42NQV050M2 / 38NYV050M2": Toshiba,
        "42NQV035M2 / 38NYV035M2": Toshiba,
        "42NQV025M2 / 38NYV025M2": Toshiba,
    }

    def __init__(self):
        self.brand = "carrier"
