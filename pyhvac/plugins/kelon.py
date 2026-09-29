#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Kelon AC IR commands.
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
from ..state import Capabilities, Choice, TemperatureRange


class Kelon(PulseBased):

    STARTFRAME = [9000, 4600]
    ENDFRAME = None
    MARK = [560]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [600, 1680]  # ditto

    def __init__(self):
        super().__init__("KELON")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [18, 32],
            "fan": ["auto", "high", "medium", "low"],
            "sleep": ["off", "on"],
        }


class Kelon168(PulseBased):
    # Not yet exposed
    STARTFRAME = [9000, 4600]
    ENDFRAME = [560, 8000]
    MARK = [560]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [600, 1680]  # ditto

    def __init__(self):
        super().__init__("KELON168")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [18, 32],
            "fan": ["auto", "high", "medium", "low"],
            "sleep": ["off", "on"],
        }


DEVICES = {}


# ------------------------------------------------------------------ Kelon
# Layout from IRremoteESP8266's KelonProtocol (ir_Kelon.h): one 48-bit word
# sent LSB first by sendKelon, i.e. 6 bytes in order, each LSB first, with a
# kKelonHdrMark/HdrSpace header, a kKelonBitMark footer and kKelonGap
# (2 * kDefaultMessageGap) after it. No checksum.

KELON = Protocol(
    "kelon",
    {
        "main": Section(
            PulseDistance(560, 600, 1680),  # kKelonBitMark/ZeroSpace/OneSpace
            header=(9000, 4600),  # kKelonHdrMark/HdrSpace
            footer=(560,),
            gap=200000,  # kKelonGap
        )
    },
    carrier=38000,  # kKelonFreq
)

# Skeleton: stateReset clears the whole word and writes the preamble
# (0x83, 0x06). pad1/pad2 (byte 5) are never written, so they stay 0.
KELON_LAYOUT = Layout(
    bytes.fromhex("830600000000"),
    {
        # Raw fan codes: 0 auto, 1 max, 2 medium, 3 min (the header's note:
        # IRKelonAc::setFan inverts the public 1..3 into these).
        "fan": Field.at(2, 0, 2, values={"auto": 0, "1": 3, "2": 2, "3": 1}),
        "power_toggle": Field.at(2, 2, 1),
        "sleep": Field.at(2, 3, 1),
        "dry_grade": Field.at(2, 4, 3),  # sign-magnitude, -2..+2
        "swing_toggle": Field.at(2, 7, 1),
        "mode": Field.at(  # kKelonMode*
            3, 0, 3, values={"heat": 0, "auto": 1, "cool": 2, "dry": 3, "fan": 4}
        ),
        "timer": Field.at(3, 3, 1),  # TimerEnabled
        "temperature": Field.at(  # degrees - kKelonMinTemp
            3, 4, 4, values={t: t - 18 for t in range(18, 33)}
        ),
        "timer_half_hour": Field.at(4, 0, 1),
        "timer_hours": Field.at(4, 1, 6),
        "smart": Field.at(4, 7, 1),  # SmartModeEnabled
        "super_cool1": Field.at(5, 4, 1),
        "super_cool2": Field.at(5, 7, 1),
    },
)

# The temperature IRKelonAc::setMode forces in these modes (the header's
# kKelonModeSmart "temp = 26C" and kKelonModeDry/Fan "temp = 25C" notes).
# This follows the C path. Real remotes differ: the dry captures in
# ir_Kelon_test.cpp (0x83040683, 0x83800683) carry 26C and the smart mode
# capture (0x1679030683) carries 25C.
KELON_FIXED_TEMPERATURE = {"auto": 26, "dry": 25, "fan": 25}


class KelonDevice(Device):
    """Kelon ON/OFF 9000-12000: the mode, fan, setpoint and sleep are sent
    in full; power (and swing) are toggles.

    As IRac::kelon sends it:
    - the setpoint is sent in cool and heat only; auto sends 26 °C and dry and
      fan send 25 °C, the temperatures IRKelonAc::setMode forces;
    - the dehumidifier grade, timer and super cool are never set (IRac passes
      dryGrade 0 and the glue never passes turbo), and the swing toggle is
      never set (the entity has no swing: IRac's swingv stays kOff);
    - SmartModeEnabled stays clear, as in the C output and the real smart
      mode capture 0x1679030683 (ir_Kelon_test.cpp, Timer12HSmartMode).

    PowerToggle: with ``previous`` it is set only when the power changes;
    this is the rule IRac::handleToggles applies to KELON when the IRac
    object has sent before (a persistent object). With ``previous=None`` it
    is ``target.power``, as a fresh IRac sends (its previous state is of
    protocol UNKNOWN, so handleToggles does nothing): an "on" toggles, an
    "off" toggles nothing.

    An off message carries the target's mode, with that mode's temperature
    rule. It does not carry what C's convertMode maps IRac's "off" to
    (kKelonModeSmart): power is only a toggle, so an off message without the
    toggle just sets the state, and the header's ensurePower note says that
    smart mode switches the unit on. C itself sends heat there, at 26 C (see
    the mode defect below). This was decided by a coordinator ruling.

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_kelon_device.py):
    - mode: IRac::kelon calls setSupercool(false), whose else branch calls
      setMode(_previousMode); _previousMode is kKelonModeHeat (0) from
      stateReset, so every C message is mode heat. The port sends the
      requested kKelonMode* value;
    - sleep: the old glue never passes sleep, so setSleep(sleep >= 0) always
      clears SleepEnabled; the port sets it.
    """

    PROTOCOL = KELON
    LAYOUTS = (KELON_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "fan", "dry", "heat"),
        temperature=TemperatureRange(18.0, 32.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
        ),
        features={"sleep": Choice((False, True), {False: "off", True: "on"})},
    )

    def frames(self, previous, target, actions):
        mode = target.mode
        if previous is None:
            toggle = target.power
        else:
            toggle = target.power != previous.power
        data = KELON_LAYOUT.build(
            fan=target.fan,
            power_toggle=toggle,
            sleep=target.features["sleep"],
            mode=mode,
            temperature=KELON_FIXED_TEMPERATURE.get(mode, int(target.temperature)),
        )
        return [Frame("main", bytes(data))]


KELON_MODELS = ("remote",)


DEVICES.update({m: KelonDevice for m in KELON_MODELS})


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "remote": Kelon,
    }

    def __init__(self):
        self.brand = "kelon"
