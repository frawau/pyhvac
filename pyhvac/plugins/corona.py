#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Corona AC IR commands.
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
from ..device import Device
from ..fields import Field, InvertedPairs, Layout
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_3, ON_OFF, SWING
from ..state import Capabilities, TemperatureRange


class Corona(PulseBased):
    STARTFRAME = [3500, 1680]
    ENDFRAME = None
    MARK = [450]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [420, 1270]  # ditto

    def __init__(self):
        super().__init__("CORONA_AC")
        self.capabilities = {
            "mode": ["off", "heat", "dry", "cool", "fan"],
            "temperature": [17, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "economy": ["off", "on"],
        }


# ----- CoronaAc
# Layout from IRremoteESP8266's CoronaProtocol (ir_Corona.h): three 7-byte
# CoronaSection frames (kCoronaAcSectionBytes), each sent LSB first by
# sendCoronaAc with its own header, footer mark and kCoronaAcSpaceGap:
# the settings, the on timer and the off timer. Every section is
# Header0 (0x28), Header1 (0x61), Label, Data0, ~Data0, Data1, ~Data1
# (IRCoronaAc::checksum writes the constant bytes and the complements).
#
# IRCoronaAc::send sends the three sections twice when no timer is set:
# first with PowerButton clear, then with PowerButton set.

_CORONA_AC_SECTION = Section(
    PulseDistance(450, 420, 1270),  # kCoronaAcBitMark/ZeroSpace/OneSpace
    header=(3500, 1680),  # kCoronaAcHdrMark/HdrSpace
    footer=(450,),  # kCoronaAcBitMark
    gap=10800,  # kCoronaAcSpaceGap
)

CORONA_AC = Protocol(
    "corona-ac",
    {
        "settings": _CORONA_AC_SECTION,
        "on_timer": _CORONA_AC_SECTION,
        "off_timer": _CORONA_AC_SECTION,
    },
    carrier=38000,  # kCoronaAcFreq
)

# Data0 and Data1 are followed by their complements.
_CORONA_AC_INVERTED = InvertedPairs(3, 7)

# Skeleton: IRCoronaAc::stateReset with the written fields cleared. Label
# 0x3D is IRCoronaAc::getSectionByte(kCoronaAcSettingsSection); Data0 is
# kCoronaAcSectionData0Base (0x10: bit 4 always on), and every bit of Data1
# is a field.
CORONA_AC_SETTINGS_LAYOUT = Layout(
    bytes.fromhex("28613d10ef00ff"),
    {
        "fan": Field.at(3, 0, 2, values={"auto": 0, "1": 1, "2": 2, "3": 3}),
        "econo": Field.at(3, 3, 1),
        "swing_toggle": Field.at(3, 6, 1),  # SwingVToggle
        "temperature": Field.at(  # degrees - kCoronaAcMinTemp + 1
            5, 0, 4, values={t: t - 16 for t in range(17, 31)}
        ),
        "power": Field.at(5, 4, 1),
        "power_button": Field.at(5, 5, 1),
        "mode": Field.at(  # kCoronaAcMode*
            5, 6, 2, values={"heat": 0, "dry": 1, "cool": 2, "fan": 3}
        ),
    },
    checksum=_CORONA_AC_INVERTED,
)


def _corona_ac_timer_layout(label):
    """A timer section: Data0 is the low byte and Data1 the high byte of the
    time in kCoronaAcTimerUnitsPerMin units, kCoronaAcTimerOff (0xFFFF) when
    unset, as stateReset leaves it."""
    return Layout(
        bytes([0x28, 0x61, label, 0xFF, 0x00, 0xFF, 0x00]),
        {
            "timer": Field.over(
                *[(3, bit) for bit in range(8)], *[(5, bit) for bit in range(8)]
            ),
        },
        checksum=_CORONA_AC_INVERTED,
    )


# getSectionByte(kCoronaAcOnTimerSection) and (kCoronaAcOffTimerSection).
CORONA_AC_ON_TIMER_LAYOUT = _corona_ac_timer_layout(0x6D)
CORONA_AC_OFF_TIMER_LAYOUT = _corona_ac_timer_layout(0xCD)


class CoronaAcDevice(Device):
    """Corona (CSH-N2211 family, AR-01 remote): the mode, setpoint, fan and
    economy are sent in full; vertical swing is a toggle bit (SwingVToggle).

    As IRac::corona sends it:
    - the whole message twice, first with PowerButton clear and then with
      it set (IRCoronaAc::send without a timer); the timers stay off;
    - an off message carries mode cool (IRac passes mode "off", which
      convertMode maps to kCoronaAcModeCool) with the target's setpoint,
      fan, swing toggle and economy.

    SwingVToggle: with ``previous`` it is set only when swing changes
    between off and on, the rule IRac::handleToggles applies to CORONA_AC
    when the IRac object has sent before (a persistent object). With
    ``previous=None`` it is set whenever swing is on, as a fresh IRac sends
    it (its previous state is of protocol UNKNOWN, so handleToggles does
    nothing).
    """

    PROTOCOL = CORONA_AC
    LAYOUTS = (
        CORONA_AC_SETTINGS_LAYOUT,
        CORONA_AC_ON_TIMER_LAYOUT,
        CORONA_AC_OFF_TIMER_LAYOUT,
    ) * 2
    capabilities = Capabilities(
        modes=("heat", "dry", "cool", "fan"),
        temperature=TemperatureRange(17.0, 30.0),
        fan=FAN_3,
        swing_v=SWING,
        features={"economy": ON_OFF},
    )

    def frames(self, previous, target, actions):
        if previous is None:
            toggle = target.swing_v != "off"
        else:
            toggle = (target.swing_v != "off") != (previous.swing_v != "off")
        values = dict(
            fan=target.fan,
            econo=target.features["economy"],
            swing_toggle=toggle,
            temperature=int(target.temperature),
            power=target.power,
            mode=target.mode if target.power else "cool",
        )
        timers = [
            Frame("on_timer", bytes(CORONA_AC_ON_TIMER_LAYOUT.skeleton)),
            Frame("off_timer", bytes(CORONA_AC_OFF_TIMER_LAYOUT.skeleton)),
        ]
        out = []
        for button in (False, True):
            data = CORONA_AC_SETTINGS_LAYOUT.build(power_button=button, **values)
            out += [Frame("settings", bytes(data)), *timers]
        return out


CORONA_AC_MODELS = (
    "CSH-N2211",
    "CSH-N2511",
    "CSH-N2811",
    "CSH-N4011",
    "AR-01 remote",
    "generic",
)


DEVICES = {}
DEVICES.update({m: CoronaAcDevice for m in CORONA_AC_MODELS})


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {  # Corona
        "CSH-N2211": Corona,
        "CSH-N2511": Corona,
        "CSH-N2811": Corona,
        "CSH-N4011": Corona,
        "AR-01 remote": Corona,
        "generic": Corona,
    }

    def __init__(self):
        self.brand = "corona"
