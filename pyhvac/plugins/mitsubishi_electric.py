#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Mitsubishi AC IR commands.
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

from dataclasses import dataclass

from .hvaclib import PulseBased, GenPluginObject
from ..device import Device
from ..fields import Checksum, Field, Layout, Sum8
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import Capabilities, Choice, TemperatureRange


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


DEVICES = {}


# ------------------------------------------------------------- MitsubishiAc
# Layout from IRremoteESP8266's Mitsubishi144Protocol (ir_Mitsubishi.h): one
# 18-byte state (kMitsubishiACStateLength) sent LSB first, closed by a
# sum-of-bytes checksum (IRMitsubishiAC::calculateChecksum). sendMitsubishiAC
# sends it kMitsubishiACMinRepeat + 1 = 2 times, each copy with the header,
# a kMitsubishiAcRptMark footer and a kMitsubishiAcRptSpace gap.

MITSUBISHI_AC = Protocol(
    "mitsubishi-ac",
    {
        "main": Section(
            PulseDistance(450, 420, 1300),  # kMitsubishiAcBitMark/Zero/OneSpace
            header=(3400, 1750),  # kMitsubishiAcHdrMark/HdrSpace
            footer=(440,),  # kMitsubishiAcRptMark
            gap=15500,  # kMitsubishiAcRptSpace
        ),
    },
    carrier=38000,  # sendMitsubishiAC: 38 kHz
)

MITSUBISHI_AC_MODE = {  # kMitsubishiAc*, as IRMitsubishiAC::convertMode
    "auto": 0b100,
    "cool": 0b011,
    "dry": 0b010,
    "heat": 0b001,
    "fan": 0b111,
}
# IRMitsubishiAC::setMode also rewrites the whole of byte 8: the low nibble
# (unnamed in the struct) gets these values; the high nibble (WideVane) is
# then overwritten by IRac's setWideVane.
MITSUBISHI_AC_MODE_AUX = {"auto": 0b0000, "cool": 0b0110, "dry": 0b0010}
MITSUBISHI_AC_MODE_AUX.update({"heat": 0b0000, "fan": 0b0111})
MITSUBISHI_AC_FAN = {  # canonical fan -> (Fan, FanAuto), as setFan(convertFan)
    "auto": (0, 1),  # kMitsubishiAcFanAuto: the FanAuto bit
    "1": (5, 0),  # lowest: kMitsubishiAcFanSilent (6), stored as 5 by setFan
    "2": (1, 0),  # kMitsubishiAcFanRealMax - 3
    "3": (2, 0),  # kMitsubishiAcFanRealMax - 2
    "4": (3, 0),  # kMitsubishiAcFanRealMax - 1
    "5": (4, 0),  # kMitsubishiAcFanRealMax
}
MITSUBISHI_AC_VANE = {  # canonical swing_v -> kMitsubishiAcVane*
    "off": 0b000,  # VaneAuto: convertSwingV's choice for stdAc "off"
    "1": 0b001,  # VaneHighest
    "2": 0b010,  # VaneHigh
    "3": 0b011,  # VaneMiddle
    "4": 0b100,  # VaneLow
    "5": 0b101,  # VaneLowest
    "auto": 0b111,  # VaneSwing: convertSwingV's choice for stdAc "auto"
}
MITSUBISHI_AC_WIDE_VANE = {  # canonical swing_h -> kMitsubishiAcWideVane*
    "1": 0b0001,  # LeftMax
    "2": 0b0010,  # Left
    "3": 0b0011,  # Middle
    "4": 0b0100,  # Right
    "5": 0b0101,  # RightMax
    "6": 0b0110,  # Wide
    "auto": 0b1000,  # Auto
}
MITSUBISHI_AC_MIN_TEMP = 16  # kMitsubishiAcMinTemp

# Skeleton: IRMitsubishiAC::stateReset (kReset, zero-filled to 18 bytes) with
# the fields IRac writes cleared. Byte 10 keeps kReset's Clock (0x67): the
# pyhvac glue never sets a clock, so IRac skips setClock.
MITSUBISHI_AC_LAYOUT = Layout(
    bytes.fromhex("23cb26010000000000006700000000000000"),
    {
        "power": Field.at(5, 5, 1),
        "mode": Field.at(6, 3, 3, values=MITSUBISHI_AC_MODE),
        "isee": Field.at(6, 6, 1),
        "temperature": Field.at(  # whole °C, as an offset from 16
            7, 0, 4, values={t: t - MITSUBISHI_AC_MIN_TEMP for t in range(16, 32)}
        ),
        "half_degree": Field.at(7, 4, 1),
        "mode_aux": Field.at(8, 0, 4),  # struct padding that setMode writes
        "swing_h": Field.at(8, 4, 4, values=MITSUBISHI_AC_WIDE_VANE),
        "fan": Field.at(9, 0, 3),
        "swing_v": Field.at(9, 3, 3, values=MITSUBISHI_AC_VANE),
        "vane_bit": Field.at(9, 6, 1),
        "fan_auto": Field.at(9, 7, 1),
        "clock": Field.at(10, 0, 8),
        "stop_clock": Field.at(11, 0, 8),
        "start_clock": Field.at(12, 0, 8),
        "timer": Field.at(13, 0, 3),
        "weekly_timer": Field.at(13, 3, 1),
        "ecocool": Field.at(14, 5, 1),
        "direct_indirect": Field.at(15, 0, 2),
        "absense_detect": Field.at(15, 2, 1),
        "isave_10c": Field.at(15, 5, 1),
        "natural_flow": Field.at(16, 1, 1),
        "swing_v_left": Field.at(16, 3, 3, values=MITSUBISHI_AC_VANE),
    },
    checksum=Sum8(0, 17, 17),
)


class MitsubishiAcDevice(Device):
    """Mitsubishi 144-bit (MSZ-GV2519 and others): a full-state protocol,
    ``previous`` is ignored (Mitsubishi144Protocol has no toggle bits).

    The message is the same 18-byte frame sent twice, as sendMitsubishiAC
    does with kMitsubishiACMinRepeat. Vertical positions are the documented
    kMitsubishiAcVane* ones, "1" the highest; IRac sets the left vane
    (VaneLeft) to the same position as the right one (Vane).
    """

    PROTOCOL = MITSUBISHI_AC
    LAYOUTS = (MITSUBISHI_AC_LAYOUT, MITSUBISHI_AC_LAYOUT)
    capabilities = Capabilities(
        modes=("auto", "cool", "fan", "dry", "heat"),
        temperature=TemperatureRange(16.0, 31.0, decimals=(0, 5)),
        fan=Choice(
            ("auto", "1", "2", "3", "4", "5"),
            {
                "auto": "auto",
                "1": "lowest",
                "2": "low",
                "3": "medium",
                "4": "high",
                "5": "highest",
            },
        ),
        swing_v=Choice(
            ("off", "auto", "1", "2", "3", "4", "5"),
            {
                "off": "off",
                "auto": "auto",
                "1": "90°",
                "2": "60°",
                "3": "45°",
                "4": "30°",
                "5": "0°",
            },
        ),
        swing_h=Choice(
            ("auto", "1", "2", "3", "4", "5", "6"),
            {
                "auto": "auto",
                "1": "far left",
                "2": "left",
                "3": "middle",
                "4": "right",
                "5": "far right",
                "6": "wide",
            },
        ),
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to kMitsubishiAcAuto) and every other
        # setting as asked.
        mode = target.mode if target.power else "auto"
        # setTemp: half degrees, clamped to 16-31 (normalise already did).
        halves = int(target.temperature * 2)
        fan, fan_auto = MITSUBISHI_AC_FAN[target.fan]
        data = MITSUBISHI_AC_LAYOUT.build(
            power=target.power,
            mode=mode,
            temperature=halves // 2,
            half_degree=halves & 1,
            mode_aux=MITSUBISHI_AC_MODE_AUX[mode],
            swing_h=target.swing_h,
            fan=fan,
            fan_auto=fan_auto,
            swing_v=target.swing_v,
            vane_bit=1,  # setVane always sets it
            swing_v_left=target.swing_v,
            isave_10c=0,  # IRac calls setISave10C(false)
        )
        frame = Frame("main", bytes(data))
        return [frame, frame]


MITSUBISHI_AC_MODELS = (
    "MS-GK24VA",
    "KM14A 0179213 remote",
    "MLZ-RX5017AS",
    "SG153/M21EDF426 remote",
    "MSZ-GV2519",
    "RH151/M21ED6426 remote",
    "MSZ-SF25VE3",
    "SG15D remote",
    "MSZ-ZW4017S",
    "MSZ-FHnnVE",
    "RH151 remote",
    "generic",
)


DEVICES.update({m: MitsubishiAcDevice for m in MITSUBISHI_AC_MODELS})


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
