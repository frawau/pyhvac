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

from dataclasses import replace

from ..device import Device
from ..fields import Field, Layout
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_3, ON_OFF, SWING
from ..state import Capabilities, TemperatureRange

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
    # decodeKelon: _tolerance (25 %), mark excess 0.
    mark_excess=0,
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
KELON_MIN_TEMP = 18  # kKelonMinTemp
# The "dry-grade" variant: in dry mode the setpoint sets the dehumidifier
# grade (DryGrade, sign-magnitude -2..+2) relative to the 25 °C dry mode
# sends, as SmartIR climate 1522, 2200, 2500 and 5520 step it with the
# temperature keys. IRac::kelon passes grade 0.
KELON_DRY_GRADE = {-2: 0b110, -1: 0b101, 0: 0, 1: 0b001, 2: 0b010}
# The "16C" variant: 16-30 °C, the setpoint field holding degrees - 16, as
# SmartIR climate 1621 and 1624 (Tornado) send it.
KELON_16C_OFFSET = KELON_MIN_TEMP - 16


class KelonDevice(Device):
    """Kelon ON/OFF 9000-12000: the mode, fan, setpoint and sleep are sent
    in full; power (and swing) are toggles.

    As IRac::kelon sends it:
    - the setpoint is sent in cool and heat only; auto sends 26 °C and dry and
      fan send 25 °C, the temperatures IRKelonAc::setMode forces;
    - the dehumidifier grade and timer are never set (IRac passes dryGrade
      0 and has no timer);
    - SmartModeEnabled stays clear, as in the C output and the real smart
      mode capture 0x1679030683 (ir_Kelon_test.cpp, Timer12HSmartMode).

    PowerToggle: with ``previous`` it is set only when the power changes;
    this is the rule IRac::handleToggles applies to KELON when the IRac
    object has sent before (a persistent object). With ``previous=None`` it
    is ``target.power``, as a fresh IRac sends (its previous state is of
    protocol UNKNOWN, so handleToggles does nothing): an "on" toggles, an
    "off" toggles nothing.

    SwingVToggle follows the same rule for swing_v ("off" / "swing"):
    handleToggles' KELON case toggles when the swing changes between off
    and not-off, and IRac::sendAc passes ``swingv != kOff`` as the toggle;
    without ``previous`` it is set when the target swing is on. The legacy
    entity had no swing, so the oracle fixtures only hold it clear.

    Powerful is Super Cool, as IRac::kelon's setSupercool(turbo): both
    SuperCoolEnabled bits, and, as IRKelonAc::setSupercool(true) does, cool
    at kKelonMinTemp (18 °C) with the fan at kKelonFanMax, whatever the
    target's mode, setpoint and fan (the real SendDataOnly capture
    0x900002010683). The legacy entity had no powerful, so the fixtures only
    hold it clear.

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
    VARIANTS = ("dry-grade", "16C")
    capabilities = Capabilities(
        modes=("auto", "cool", "fan", "dry", "heat"),
        temperature=TemperatureRange(18.0, 32.0),
        fan=FAN_3,
        swing_v=SWING,
        features={"sleep": ON_OFF, "powerful": ON_OFF},
    )

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        if variant is None:  # built directly: the brands table's variant
            from ..registry import variant_of

            variant = variant_of(type(self), brand, model)
        if variant is not None and variant not in self.VARIANTS:
            raise ValueError(f"unknown Kelon variant {variant!r}")
        self.variant = variant
        if variant == "16C":
            self.capabilities = replace(
                self.capabilities, temperature=TemperatureRange(16.0, 30.0)
            )

    def frames(self, previous, target, actions):
        mode, fan = target.mode, target.fan
        temperature = KELON_FIXED_TEMPERATURE.get(mode, int(target.temperature))
        if self.variant == "16C" and mode not in KELON_FIXED_TEMPERATURE:
            temperature += KELON_16C_OFFSET  # the field's degrees - 18
        swing = target.swing_v != "off"
        if previous is None:
            toggle, swing_toggle = target.power, swing
        else:
            toggle = target.power != previous.power
            swing_toggle = swing != (previous.swing_v != "off")
        super_cool = target.features.get("powerful", False)
        if super_cool:  # IRKelonAc::setSupercool(true)
            mode, temperature, fan = "cool", KELON_MIN_TEMP, "3"
        grade = 0
        if self.variant == "dry-grade" and mode == "dry" and not super_cool:
            offset = int(target.temperature) - KELON_FIXED_TEMPERATURE["dry"]
            grade = KELON_DRY_GRADE[max(-2, min(2, offset))]
        data = KELON_LAYOUT.build(
            dry_grade=grade,
            fan=fan,
            power_toggle=toggle,
            sleep=target.features["sleep"],
            swing_toggle=swing_toggle,
            mode=mode,
            temperature=temperature,
            super_cool1=super_cool,
            super_cool2=super_cool,
        )
        return [Frame("main", bytes(data))]


KELON_MODELS = ("remote",)


# Now the match between models and objects
