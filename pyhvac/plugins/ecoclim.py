#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Ecoclim AC IR commands.
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
from ..fields import Field, Layout
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_3
from ..state import Capabilities, TemperatureRange


class Ecoclim(PulseBased):

    STARTFRAME = [6630, 3350]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [430, 1260]  # ditto

    def __init__(self):
        super().__init__("ECOCLIM")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [5, 31],
            "fan": ["auto", "high", "medium", "low"],
        }


DEVICES = {}


# ------------------------------------------------------------------ Ecoclim
# Layout from IRremoteESP8266's EcoclimProtocol (ir_Ecoclim.h): one 56-bit
# word, its fields numbered from the word's LSB. sendEcoclim sends the word
# MSB first, three times (kEcoclimSections), each copy after a
# kEcoclimHdrMark/HdrSpace header, then one kEcoclimFooterMark and
# kEcoclimGap (kDefaultMessageGap). So frame byte 0 is the word's top byte
# (SensorTemp) and byte 6 its low byte (DipConfig), each byte MSB first.
# A copy has no footer mark of its own: the next header closes its last bit,
# so that header is the footer of the first two sections. No checksum.

ECOCLIM = Protocol(
    "ecoclim",
    {
        "first": Section(
            PulseDistance(440, 637, 1739),  # kEcoclimBitMark/ZeroSpace/OneSpace
            header=(5730, 1935),  # kEcoclimHdrMark/HdrSpace
            footer=(5730, 1935),  # the second copy's header
            lsb_first=False,
        ),
        "second": Section(
            PulseDistance(440, 637, 1739),
            footer=(5730, 1935),  # the third copy's header
            lsb_first=False,
        ),
        "last": Section(
            PulseDistance(440, 637, 1739),
            footer=(7820,),  # kEcoclimFooterMark
            gap=100000,  # kEcoclimGap
            lsb_first=False,
        ),
    },
    carrier=38000,  # enableIROut(38)
    # decodeEcoclim: matchGeneric(..., _tolerance + kEcoclimExtraTolerance
    # (30 %)), default kMarkExcess (50).
    tolerance=0.30,
)


def _ecoclim_temperature(low, high):
    # Temp and SensorTemp: degrees - kEcoclimTempMin.
    return {t: t - 5 for t in range(low, high + 1)}


# Skeleton: kEcoclimDefaultState (0x11063000FFFF02), which stateReset writes
# whole: both timers disabled (hours 0x1F, tens of minutes 7), clock 00:00,
# DIP master, the fixed 0b010 in the low bits.
ECOCLIM_LAYOUT = Layout(
    bytes.fromhex("11063000ffff02"),
    {
        "sensor_temperature": Field.at(0, 0, 5, values=_ecoclim_temperature(5, 36)),
        "temperature": Field.at(1, 0, 5, values=_ecoclim_temperature(5, 36)),
        "mode": Field.at(  # kEcoclim* modes
            1,
            5,
            3,
            values={
                "auto": 0,
                "cool": 1,
                "dry": 2,
                "recycle": 3,
                "fan": 4,
                "heat": 5,
                "sleep": 7,
            },
        ),
        # Clock: 11 bits, minutes past midnight; its top 3 bits are in byte 2.
        "clock": Field.over(*[(3, b) for b in range(8)], (2, 0), (2, 1), (2, 2)),
        "unknown_clock": Field.at(2, 3, 1),
        "fan": Field.at(  # kEcoclimFanMin/Med/Max/Auto
            2, 4, 2, values={"1": 0, "2": 1, "3": 2, "auto": 3}
        ),
        "power": Field.at(2, 6, 1),
        "clear": Field.at(2, 7, 1),
        "on_ten_minutes": Field.at(4, 0, 3),
        "on_hours": Field.at(4, 3, 5),
        "off_ten_minutes": Field.at(5, 0, 3),
        "off_hours": Field.at(5, 3, 5),
        "unknown_type": Field.at(6, 3, 1),
        "dip_config": Field.at(  # kEcoclimDipMaster/Slave
            6, 4, 4, values={"master": 0, "slave": 7}
        ),
    },
)


class EcoclimDevice(Device):
    """EcoClim (HYSFR-P348 remote): the whole state in every message.

    As IRac::ecoclim sends it:
    - the power bit is absolute (no toggle), so ``previous`` is ignored;
    - SensorTemp is the setpoint (IRac sets it to the desired temperature
      when no sensor reading is given, and the entity has none);
    - the clock stays 00:00, both timers stay disabled and the DIP setting
      stays master, as in kEcoclimDefaultState (IRac passes no clock, and
      never sets the timers or the type);

    An off message carries mode auto, what IRac::ecoclim's convertMode
    makes of the "off" mode the glue passes; the C output itself is sleep
    there (the mode defect below).

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_ecoclim_device.py):
    - mode: IRac::sendAc passes ``send.iFeel`` (false, i.e. 0) as
      IRac::ecoclim's ``sleep`` minutes, and ``sleep >= 0`` selects
      kEcoclimSleep, so every C message is mode sleep. The port sends the
      requested kEcoclim* mode.
    """

    PROTOCOL = ECOCLIM
    LAYOUTS = (ECOCLIM_LAYOUT, ECOCLIM_LAYOUT, ECOCLIM_LAYOUT)
    capabilities = Capabilities(
        modes=("auto", "cool", "fan", "dry", "heat"),
        temperature=TemperatureRange(5.0, 31.0),
        fan=FAN_3,
    )

    def frames(self, previous, target, actions):
        temperature = int(target.temperature)
        data = bytes(
            ECOCLIM_LAYOUT.build(
                sensor_temperature=temperature,
                temperature=temperature,
                mode=target.mode if target.power else "auto",
                fan=target.fan,
                power=target.power,
            )
        )
        return [Frame("first", data), Frame("second", data), Frame("last", data)]


ECOCLIM_MODELS = ("HYSFR-P348 remote", "ZC200DPO", "generic")


DEVICES.update({m: EcoclimDevice for m in ECOCLIM_MODELS})


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {"HYSFR-P348 remote": Ecoclim, "ZC200DPO": Ecoclim, "generic": Ecoclim}

    def __init__(self):
        self.brand = "ecoclim"
