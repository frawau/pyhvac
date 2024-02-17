#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Pioneer System AC IR commands.
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
from .midea import Midea


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "RYBO12GMFILCAD": Midea,
        "RUBO18GMFILCAD": Midea,
        "WS012GMFI22HLD": Midea,
        "WS018GMFI22HLD": Midea,
        "UB018GMFILCFHD": Midea,
        "RG66B6(B)/BGEFU1 remote": Midea,
    }

    def __init__(self):
        self.brand = "pioneer system"
