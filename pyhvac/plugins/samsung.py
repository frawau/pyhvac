#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Samsung AC IR commands.
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
from ..fields import Field, Layout
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_3, ON_OFF, SWING
from ..state import Capabilities, TemperatureRange


class Samsung(PulseBased):

    LEAD = [690, 17844]
    STARTFRAME = [3086, 8864]
    TAIL = [2886, 97114]
    MARK = [586]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [436, 1432]  # ditto

    def __init__(self):
        super().__init__("SAMSUNG_AC")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "cleaning": ["off", "on"],
            "quiet": ["off", "on"],
            "powerful": ["off", "on"],
            "economy": ["off", "on"],
            "light": ["off", "on"],
            "purifier": ["off", "on"],
        }


DEVICES = {}


# ------------------------------------------------------------------ SamsungAc
# Layout from IRremoteESP8266's SamsungProtocol (ir_Samsung.h). IRac::samsung
# always sends the extended message (IRac.h's forceextended defaults to true,
# so IRSamsungAc::send calls sendExtended): 21 bytes in three 7-byte sections.
# Sections 1 and 3 are the standard message's two sections; section 2 is
# sendExtended's extended_middle_section, which carries the timers and the
# second sleep bit. sendSamsungAC sends a kSamsungAcHdrMark/HdrSpace leader,
# then each section with sendGeneric (kSamsungAcSectionMark/SectionSpace
# header, kSamsungAcBitMark/OneSpace/ZeroSpace bits LSB first, a
# kSamsungAcBitMark footer and a kSamsungAcSectionGap), then
# space(kDefaultMessageGap - kSamsungAcSectionGap): the last section's gap is
# 100 000 µs in all. No repeat (kSamsungAcDefaultRepeat is kNoRepeat).
# Carrier 38 kHz (enableIROut(38)).

SAMSUNG_AC_BITS = PulseDistance(586, 436, 1432)  # kSamsungAcBitMark/Zero/OneSpace

SAMSUNG_AC = Protocol(
    "samsung_ac",
    {
        "leader": Section(None, header=(690,), gap=17844),  # kSamsungAcHdr*
        "section": Section(
            SAMSUNG_AC_BITS,
            header=(3086, 8864),  # kSamsungAcSectionMark/SectionSpace
            footer=(586,),  # kSamsungAcBitMark
            gap=2886,  # kSamsungAcSectionGap
        ),
        "last": Section(
            SAMSUNG_AC_BITS,
            header=(3086, 8864),
            footer=(586,),
            gap=100000,  # kSamsungAcSectionGap + the final space: kDefaultMessageGap
        ),
    },
    carrier=38000,
)


@dataclass(frozen=True)
class SamsungAcChecksum:
    """IRSamsungAc::calcSectionChecksum over one 7-byte section: the number
    of set bits outside the checksum, bitwise inverted, in the 8 bits from
    bit ``at`` (Sum<n>Lower in the high nibble of byte 1, Sum<n>Upper in the
    low nibble of byte 2)."""

    at: int = 12

    def compute(self, data):
        ones = sum(
            (data[bit // 8] >> (bit % 8)) & 1
            for bit in range(8 * len(data))
            if not self.at <= bit < self.at + 8
        )
        return (ones ^ 0xFF) & 0xFF

    def positions(self):
        return {self.at // 8, (self.at + 7) // 8}

    def bits(self):
        return set(range(self.at, self.at + 8))

    def _read(self, data):
        return sum(
            ((data[(self.at + k) // 8] >> ((self.at + k) % 8)) & 1) << k
            for k in range(8)
        )

    def apply(self, data):
        value = self.compute(data)
        for k in range(8):
            bit = self.at + k
            if (value >> k) & 1:
                data[bit // 8] |= 1 << (bit % 8)
            else:
                data[bit // 8] &= ~(1 << (bit % 8)) & 0xFF

    def check(self, data):
        return self._read(data) == self.compute(data)


SAMSUNG_AC_POWER = {False: 0b00, True: 0b11}

# Section 1: bytes 0-6 of stateReset's kReset (the whole message is
# initialised: kReset is a static array, zero past its 14 given bytes, and
# sendExtended writes the middle section in full). Power1 and the first sleep
# bit (Sleep5) live here.
SAMSUNG_AC_LAYOUT_1 = Layout(
    bytes.fromhex("02920f000000f0"),
    {
        "sleep": Field.at(5, 4, 1),  # Sleep5
        "quiet": Field.at(5, 5, 1),
        "power": Field.at(6, 4, 2, values=SAMSUNG_AC_POWER),  # Power1
    },
    SamsungAcChecksum(),
)

# Section 2: sendExtended's extended_middle_section (bytes 7-13 of the
# extended map). The hours of each timer are split: OffTimeHrs1 is their
# lowest bit, OffTimeHrs2 the four above it (likewise OnTimeHrs1/2).
SAMSUNG_AC_LAYOUT_2 = Layout(
    bytes.fromhex("01d20f00000000"),
    {
        "off_time_mins": Field.at(2, 4, 3),  # tens of minutes
        "off_time_hours": Field.over((2, 7), (3, 0), (3, 1), (3, 2), (3, 3)),
        "on_time_mins": Field.at(3, 4, 3),
        "on_time_hours": Field.over((3, 7), (4, 0), (4, 1), (4, 2), (4, 3)),
        "off_time_day": Field.at(5, 0, 1),
        "on_timer_enable": Field.at(5, 1, 1),
        "off_timer_enable": Field.at(5, 2, 1),
        "sleep": Field.at(5, 3, 1),  # Sleep12
        "on_time_day": Field.at(5, 4, 1),
    },
    SamsungAcChecksum(),
)

# Section 3: bytes 7-13 of kReset (the standard map's second section).
SAMSUNG_AC_LAYOUT_3 = Layout(
    bytes.fromhex("0102ae710015f0"),
    {
        # kSamsungAcSwingV / SwingH / SwingBoth / SwingOff (ir_Samsung.cpp)
        "swing": Field.at(
            2, 4, 3, values={"vertical": 2, "horizontal": 3, "both": 4, "off": 7}
        ),
        # kSamsungAcFanSpecialOff / PowerfulOn / BreezeOn / EconoOn
        "fan_special": Field.at(
            3, 1, 3, values={"off": 0, "powerful": 3, "breeze": 5, "econo": 7}
        ),
        "display": Field.at(3, 4, 1),
        # CleanToggle10 and CleanToggle11, set and cleared together.
        "clean": Field.over((3, 7), (4, 1), values={False: 0b00, True: 0b11}),
        "ion": Field.at(4, 0, 1),
        "temperature": Field.at(  # degrees - kSamsungAcMinTemp
            4, 4, 4, values={t: t - 16 for t in range(16, 31)}
        ),
        # kSamsungAcFanAuto / Low / Med / High / Auto2 / Turbo
        "fan": Field.at(
            5,
            1,
            3,
            values={"auto": 0, "1": 2, "2": 4, "3": 5, "auto2": 6, "turbo": 7},
        ),
        "mode": Field.at(  # kSamsungAc{Auto,Cool,Dry,Fan,Heat}
            5, 4, 3, values={"auto": 0, "cool": 1, "dry": 2, "fan": 3, "heat": 4}
        ),
        "beep": Field.at(6, 2, 1),  # BeepToggle
        "power": Field.at(6, 4, 2, values=SAMSUNG_AC_POWER),  # Power2
    },
    SamsungAcChecksum(),
)

SAMSUNG_AC_MIN = 16  # kSamsungAcMinTemp
SAMSUNG_AC_MAX = 30  # kSamsungAcMaxTemp


class SamsungAcDevice(Device):
    """Samsung A/C: every message is the extended one (leader and three
    sections), with the full state.

    As IRac::samsung sends it:
    - power sets Power1 and Power2 (0b11 on, 0b00 off); an off message
      carries mode auto (convertMode's default, which IRac's kOff mode falls
      to), and so fan Auto2, with the rest of the target state;
    - in mode auto the fan is kSamsungAcFanAuto2 (setMode), whatever the
      requested speed (setFan refuses every other code in auto);
    - quiet sets the fan to auto; powerful sets FanSpecial to Powerful and the
      fan to Turbo, and clears quiet; economy sets FanSpecial to Econo, the fan
      to auto and turns vertical swing on (setQuiet, setPowerful and setEcono,
      in IRac's order). In mode auto, powerful sends nothing: the fan cannot be
      Turbo there, so setEcono(false) clears FanSpecial (getPowerful needs
      both);
    - light sets Display, purifier sets Ion; beep, the timers and sleep are
      never sent (the entity has none).

    Cleaning is a toggle (CleanToggle10/11). IRac::handleToggles sends
    ``clean ^ previous clean`` for SAMSUNG_AC, so with ``previous`` the bits
    are set only when cleaning changes, as a persistent C object sends; with
    ``previous=None`` they are ``cleaning``, as a fresh C object (whose
    previous state is not a SAMSUNG_AC one) sends.

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_samsung_ac_device.py): the old glue
    has no swing "on" key (IRGHVAC.trans_swing/trans_hswing), so IRac's swingv
    and swingh stay kOff; the port sends kSamsungAcSwingV, SwingH or
    SwingBoth.
    """

    PROTOCOL = SAMSUNG_AC
    LAYOUTS = (None, SAMSUNG_AC_LAYOUT_1, SAMSUNG_AC_LAYOUT_2, SAMSUNG_AC_LAYOUT_3)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "heat", "fan"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=FAN_3,
        swing_v=SWING,
        swing_h=SWING,
        features={
            "cleaning": ON_OFF,
            "quiet": ON_OFF,
            "powerful": ON_OFF,
            "economy": ON_OFF,
            "light": ON_OFF,
            "purifier": ON_OFF,
        },
    )

    def frames(self, previous, target, actions):
        features = target.features
        mode = target.mode if target.power else "auto"
        econo, powerful = features["economy"], features["powerful"]
        quiet = features["quiet"] and not powerful
        if mode == "auto":
            fan = "auto2"
        elif econo or quiet:
            fan = "auto"
        elif powerful:
            fan = "turbo"
        else:
            fan = target.fan
        if econo:
            special = "econo"
        elif powerful and mode != "auto":
            special = "powerful"
        else:
            special = "off"
        vertical = target.swing_v == "swing" or econo
        horizontal = target.swing_h == "swing"
        swing = {
            (False, False): "off",
            (True, False): "vertical",
            (False, True): "horizontal",
            (True, True): "both",
        }[vertical, horizontal]
        clean = features["cleaning"]
        if previous is not None:
            clean = clean != previous.features["cleaning"]
        temperature = min(max(int(target.temperature), SAMSUNG_AC_MIN), SAMSUNG_AC_MAX)
        first = SAMSUNG_AC_LAYOUT_1.build(sleep=0, quiet=quiet, power=target.power)
        middle = SAMSUNG_AC_LAYOUT_2.build()
        last = SAMSUNG_AC_LAYOUT_3.build(
            swing=swing,
            fan_special=special,
            display=features["light"],
            clean=clean,
            ion=features["purifier"],
            temperature=temperature,
            fan=fan,
            mode=mode,
            beep=0,
            power=target.power,
        )
        return [
            Frame("leader", b""),
            Frame("section", bytes(first)),
            Frame("section", bytes(middle)),
            Frame("last", bytes(last)),
        ]


SAMSUNG_AC_MODELS = (
    "AR09FSSDAWKNFA",
    "AR09HSFSBWKN",
    "AR12KSFPEWQNET",
    "AR12HSSDBWKNEU",
    "AR12NXCXAWKXEU",
    "AR12TXEAAWKNEU",
    "DB93-14195A remote",
    "DB96-24901C remote",
    "generic",
)

DEVICES.update({m: SamsungAcDevice for m in SAMSUNG_AC_MODELS})


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "AR09FSSDAWKNFA": Samsung,
        "AR09HSFSBWKN": Samsung,
        "AR12KSFPEWQNET": Samsung,
        "AR12HSSDBWKNEU": Samsung,
        "AR12NXCXAWKXEU": Samsung,
        "AR12TXEAAWKNEU": Samsung,
        "DB93-14195A remote": Samsung,
        "DB96-24901C remote": Samsung,
        "generic": Samsung,
    }

    def __init__(self):
        self.brand = "samsung"
