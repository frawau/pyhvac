#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Vestel AC IR commands.
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
#

from .hvaclib import PulseBased, GenPluginObject


class Vestel(PulseBased):
    MARK = [1026]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [554, 2553]  # ditto

    def __init__(self):
        super().__init__("VESTEL_AC")
        self.capabilities = {
            "mode": ["auto", "cool", "dry", "fan", "heat"],
            "temperature": [16, 30],
            "fan": ["high", "medium", "low"],
            "swing": ["off", "on"],
            "sleep": ["off", "on"],
            "powerful": ["off", "on"],
            "purifier": ["off", "on"],
        }


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "BIOX CXP-9": Vestel,
        "generic": Vestel,
    }

    def __init__(self):
        self.brand = "vestel"
