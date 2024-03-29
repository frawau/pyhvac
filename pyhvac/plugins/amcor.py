#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Amcor AC IR commands.
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


class Amcor(PulseBased):
    STARTFRAME = [8200, 4200]
    ENDFRAME = [1900, 10000]
    MARK = [600, 1500]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [1500, 600]  # ditto

    def __init__(self):
        super().__init__("AMCOR")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [12, 32],
            "fan": ["auto", "highest", "medium", "lowest"],
        }


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        # Amcor
        "ADR-853H": Amcor,
        "TAC-495 remote": Amcor,
        "TAC-444 remote": Amcor,
        "generic": Amcor,
    }

    def __init__(self):
        self.brand = "amcor"
