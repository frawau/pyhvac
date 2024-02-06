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


class Mitsubishi(PulseBased):

    STARTFRAME = [3400, 1750]
    ENDFRAME = [440, 15500]
    MARK = [450]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [420, 1300]  # ditto

    def __init__(self):
        super().__init__("MITSUBISHI_AC")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [16, 31],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": [
                "auto",
                "wide",
                "far right",
                "right",
                "middle",
                "left",
                "far left",
            ],
        }
        self.temperature_step = 0.5


class Mitsubishi136(PulseBased):

    STARTFRAME = [3324, 1474]
    ENDFRAME = None
    MARK = [467]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [351, 1137]  # ditto

    def __init__(self):
        super().__init__("MITSUBISHI136")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [16, 25],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "auto", "90°", "60°", "30°", "0°"],
            "quiet": ["off", "on"],
        }


class Mitsubishi112(PulseBased):

    STARTFRAME = [3450, 1696]
    ENDFRAME = None
    MARK = [450]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [385, 1250]  # ditto

    def __init__(self):
        super().__init__("MITSUBISHI112")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat"],
            "temperature": [16, 25],
            "fan": ["highest", "medium", "low", "lowest"],
            "swing": ["off", "auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": [
                "auto",
                "wide",
                "far right",
                "right",
                "middle",
                "left",
                "far left",
            ],
            "quiet": ["off", "on"],
        }


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "MS-GK24VA": Mitsubishi,
        "KM14A 0179213 remote": Mitsubishi,
        "PEAD-RP71JAA Ducted": Mitsubishi136,
        "001CP T7WE10714 remote": Mitsubishi136,
        "MSH-A24WV": Mitsubishi112,
        "MUH-A24WV": Mitsubishi112,
        "KPOA remote": Mitsubishi112,
        "MLZ-RX5017AS": Mitsubishi,
        "SG153/M21EDF426 remote": Mitsubishi,
        "MSZ-GV2519": Mitsubishi,
        "RH151/M21ED6426 remote": Mitsubishi,
        "MSZ-SF25VE3": Mitsubishi,
        "SG15D remote": Mitsubishi,
        "MSZ-ZW4017S": Mitsubishi,
        "MSZ-FHnnVE": Mitsubishi,
        "RH151 remote": Mitsubishi,
        "PAR-FA32MA remote": Mitsubishi136,
        "generic": Mitsubishi,
        "generic 136": Mitsubishi136,
        "generic 112": Mitsubishi112,
    }

    def __init__(self):
        self.brand = "mitsubishi electric"
