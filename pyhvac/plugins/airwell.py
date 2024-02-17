#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Airwell AC IR commands
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

from .hvaclib import Manchester, GenPluginObject
from .coolix import Coolix


class Airwell(Manchester):
    HALFPULSE = 950
    STARTFRAME = [3 * 950, 3 * 950]
    ENDFRAME = [5 * 950]

    def __init__(self):
        super().__init__("AIRWELL")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low", "lowest"],
        }


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        # Airwell
        "DC Series": Airwell,
        "RC08W remote": Airwell,
        "RC04 remote": Airwell,
        "generic": Airwell,
        "RC08B remote": Coolix,
    }

    def __init__(self):
        self.brand = "airwell"
