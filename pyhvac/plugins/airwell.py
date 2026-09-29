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
from .coolix import COOLIX_AIRWELL_MODELS, Coolix, CoolixDevice
from ..device import Device
from ..fields import Field, Layout
from ..ir.model import Frame, Manchester as ManchesterBits, Protocol, Section
from ..choices import FAN_3
from ..state import Capabilities, TemperatureRange


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


DEVICES = {}


# ---------------------------------------------------------------- Airwell
# Layout from IRremoteESP8266's AirwellProtocol (ir_Airwell.h): a 34-bit
# word (kAirwellBits) sent MSB first. As logical bytes the word is
# (raw << 6) big-endian, the last 6 bits unsent. No checksum.
#
# IRsend::sendAirwell: sendManchester with a kAirwellHdrMark mark and a
# kAirwellHdrMark space as header, kAirwellHalfClockPeriod halves, no
# footer and no gap, IEEE 802.3 coding (GEThomas false: a 1 is space then
# mark) and kAirwellMinRepeats (2) repeats, so the word goes three times
# back to back; then one kAirwellHdrMark + kAirwellHalfClockPeriod mark and
# kDefaultMessageGap. Neighbouring halves of the same level merge on the
# wire (e.g. a leading "space" half lengthens the header space).

AIRWELL = Protocol(
    "airwell",
    {
        "main": Section(
            ManchesterBits(950, one_is_mark_first=False),  # kAirwellHalfClockPeriod
            header=(2850, 2850),  # kAirwellHdrMark, kAirwellHdrSpace
            lsb_first=False,
        ),
        "footer": Section(None, header=(3800,), gap=100000),
    },
    carrier=38000,  # sendManchester's 38 kHz
)

AIRWELL_BITS = 34  # kAirwellBits
AIRWELL_REPEATS = 2  # kAirwellMinRepeats: the word is sent 1 + 2 times
AIRWELL_KNOWN_GOOD_STATE = 0x140500002  # kAirwellKnownGoodState (stateReset)
AIRWELL_MIN_TEMP, AIRWELL_MAX_TEMP = 16, 30  # kAirwellMinTemp, kAirwellMaxTemp
AIRWELL_MODE = {"cool": 1, "heat": 2, "auto": 3, "dry": 4, "fan": 5}  # kAirwell*
AIRWELL_FAN_CODE = {"low": 0, "medium": 1, "high": 2, "auto": 3}  # kAirwellFan*
# canonical fan -> kAirwellFan*: the header has three speeds and auto
# (IRAirwellAc::convertFan maps both kMin and kLow to kAirwellFanLow).
AIRWELL_FAN_BY_LEVEL = {
    "auto": "auto",
    "1": "low",  # kAirwellFanLow
    "2": "medium",  # kAirwellFanMedium
    "3": "high",  # kAirwellFanHigh
}


def airwell_word(raw):
    """The logical bytes of a 34-bit Airwell word (sent MSB first)."""
    return (raw << 6).to_bytes(5, "big")


def _airwell_field(first, width, **kw):
    """A field over raw bits first..first + width - 1 of AirwellProtocol."""
    positions = []
    for n in range(first, first + width):
        at = n + 6  # bit of the 40-bit big-endian (raw << 6)
        positions.append((4 - at // 8, at % 8))
    return Field.over(*positions, **kw)


# Skeleton: kAirwellKnownGoodState with its named members cleared, i.e.
# only raw bit 1. Every message starts from stateReset and IRac::airwell
# sets the four named members only, so the unnamed bits never change.
AIRWELL_LAYOUT = Layout(
    airwell_word(0x2),
    {
        "unnamed_low": _airwell_field(0, 19),
        "temperature": _airwell_field(  # Temp = celsius - kAirwellMinTemp + 1
            19,
            4,
            values={
                t: t - AIRWELL_MIN_TEMP + 1
                for t in range(AIRWELL_MIN_TEMP, AIRWELL_MAX_TEMP + 1)
            },
        ),
        "unnamed_high": _airwell_field(23, 5),
        "fan": _airwell_field(28, 2, values=AIRWELL_FAN_CODE),
        "mode": _airwell_field(30, 3, values=AIRWELL_MODE),
        "power_toggle": _airwell_field(33, 1),
    },
)


class AirwellDevice(Device):
    """Airwell Manchester-coded A/C (IRAirwellAc, protocol AIRWELL): mode,
    fan and setpoint are sent in full; power is a toggle.

    As IRac::airwell sets it on a stateReset object:
    - an off message carries mode auto (IRac passes mode "off", which
      convertMode maps to kAirwellAuto), with the target's fan and setpoint;
    - in dry the fan is always Low (IRAirwellAc::setFan locks it);
    - the setpoint is whole degrees, 16 to 30 °C.

    PowerToggle: with ``previous`` it is set only when the power changes,
    the rule IRac::handleToggles applies to AIRWELL once the IRac object has
    sent before (a persistent object). With ``previous=None`` it is
    ``target.power``, as a fresh IRac sends (its previous state is of
    protocol UNKNOWN, so handleToggles does nothing): an "on" toggles, an
    "off" toggles nothing.

    The port sends the word as IRsend::sendAirwell does. The legacy
    C-backed class never did: its timing recorder stores each mark() and
    space() call as the next pulse, so a Manchester "space, mark" bit was
    recorded, and sent, as "mark, space", and every message came out as the
    all-zero word whatever the state (see tests/test_airwell_device.py).
    """

    PROTOCOL = AIRWELL
    # The word, its two repeats, then the bitless footer.
    LAYOUTS = (AIRWELL_LAYOUT,) * (1 + AIRWELL_REPEATS) + (None,)
    capabilities = Capabilities(
        modes=("auto", "cool", "fan", "dry", "heat"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=FAN_3,  # kAirwellFanLow/Medium/High/Auto
    )

    def frames(self, previous, target, actions):
        if previous is None:
            toggle = target.power
        else:
            toggle = target.power != previous.power
        mode = target.mode if target.power else "auto"
        fan = "low" if mode == "dry" else AIRWELL_FAN_BY_LEVEL[target.fan]
        temperature = min(
            max(int(target.temperature), AIRWELL_MIN_TEMP), AIRWELL_MAX_TEMP
        )
        data = AIRWELL_LAYOUT.build(
            temperature=temperature, fan=fan, mode=mode, power_toggle=toggle
        )
        word = Frame("main", bytes(data), AIRWELL_BITS)
        return [word] * (1 + AIRWELL_REPEATS) + [Frame("footer", b"")]


AIRWELL_MODELS = ("DC Series", "RC08W remote", "RC04 remote", "generic")


DEVICES.update({m: AirwellDevice for m in AIRWELL_MODELS})
DEVICES.update({m: CoolixDevice for m in COOLIX_AIRWELL_MODELS})


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
