#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Daikin AC IR commands as done by the ARC480A44 and others
#
# This module  is in part based on the work/code from:
#      Scott Kyle https://gist.github.com/appden/42d5272bf128125b019c45bc2ed3311f
#      mat_fr     https://www.instructables.com/id/Reverse-engineering-of-an-Air-Conditioning-control/
#
# Copyright (c) 2023 François Wautier
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

from dataclasses import replace

from ..device import Device
from ..fields import (
    bit_reverse,
    Checksum,
    Field,
    HighNibbleSum,
    Layout,
    NibbleSum,
    Sum8,
)
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_5, ON_OFF, SWING, SWING_V_AUTO_ANGLES
from ..state import Capabilities, Choice, TemperatureRange

DAIKIN_NATIVE = Protocol(
    "daikin-native",
    {
        "main": Section(
            PulseDistance(435, 435, 1300),
            header=(3500, 1750),
            footer=(435,),
            gap=10000,
            lsb_first=False,
        )
    },
)


# ---------------------------------------------------------------- shared
# Values IRremoteESP8266 shares across the Daikin protocols (ir_Daikin.h),
# and the canonical capabilities the ports have in common.

DAIKIN_MODE = {  # kDaikinAuto/Dry/Cool/Heat/Fan
    "auto": 0,
    "dry": 2,
    "cool": 3,
    "heat": 4,
    "fan": 6,
}
# The fan field (setFan): kDaikinFanAuto, kDaikinFanQuiet, and speeds
# kDaikinFanMin (1) .. kDaikinFanMax (5), sent as the speed plus 2. Quiet is
# the slowest step ("1"), as convertFan maps kMin to it; the old
# vocabulary's low/medium/high are what IRac sent for kLow/kMedium/kHigh
# (kDaikinFanMin, kDaikinFanMed, kDaikinFanMax - 1).
DAIKIN_FAN = {
    "auto": 0xA,  # kDaikinFanAuto
    "1": 0xB,  # kDaikinFanQuiet
    "2": 3,  # speed 1, kDaikinFanMin
    "3": 4,  # speed 2
    "4": 5,  # speed 3, kDaikinFanMed
    "5": 6,  # speed 4
    "6": 7,  # speed 5, kDaikinFanMax
}
DAIKIN_FAN_CHOICE = Choice(
    tuple(DAIKIN_FAN),
    {
        "auto": "auto",
        "1": "quiet",
        "2": "low",
        "3": "medium-low",
        "4": "medium",
        "5": "high",
        "6": "highest",
    },
)
DAIKIN_SWING = {"off": 0x0, "swing": 0xF}  # kDaikinSwingOff / kDaikinSwingOn
DAIKIN_SWING_BIT = {"off": 0, "swing": 1}  # Daikin64/Daikin128 SwingV bit


def _bcd(n):
    return (n // 10) << 4 | n % 10


DAIKIN_MODES = ("auto", "dry", "cool", "heat", "fan")


# --------------------------------------------------------------- Daikin2
# Layout from IRremoteESP8266's Daikin2Protocol (ir_Daikin.h): 39 bytes in
# two sections of 20 and 19, each closed by a sum-of-bytes checksum; frame
# byte n of the second section is struct byte n + 20.

DAIKIN2 = Protocol(
    "daikin2",
    {
        "leader": Section(None, header=(10024,), gap=25180),
        "main": Section(
            PulseDistance(460, 420, 1270),
            header=(3500, 1728),
            footer=(460,),
            gap=35204,
        ),
    },
    carrier=36700,
    # decodeDaikin2: _tolerance + kDaikin2Tolerance (30 %), kDaikinMarkExcess
    # (kMarkExcess).
    tolerance=0.30,
)

DAIKIN2_SWING_V = {  # kDaikin2SwingV*
    "off": 0xE,
    "auto": 0xF,
    "1": 0x1,  # highest
    "2": 0x2,  # high
    "3": 0x3,  # upper middle
    "4": 0x4,  # lower middle
    "5": 0x5,  # low
    "6": 0x6,  # lowest
}
DAIKIN2_SWING_H = {  # kDaikin2SwingH*
    "off": 0xBF,
    "auto": 0xBE,  # kDaikin2SwingHAuto, a.k.a. swing
    "1": 0xA8,  # far left
    "2": 0xA9,  # left
    "3": 0xAA,  # middle
    "4": 0xAB,  # right
    "5": 0xAC,  # far right
    "6": 0xA3,  # wide
}

DAIKIN2_FIRST = Layout(
    bytes.fromhex("11da2700010040f0200c8004b01624000000d000"),
    {
        "power2": Field.at(6, 7, 1),  # inverse of power
        # kDaikinLightBright when on, kDaikinLightOff when off (as IRac)
        "light": Field.at(7, 4, 2, values={True: 1, False: 3}),
        "mold": Field.at(8, 3, 1),
        "swing_h": Field.at(17, 0, 8, values=DAIKIN2_SWING_H),
        "swing_v": Field.at(18, 0, 4, values=DAIKIN2_SWING_V),
    },
    checksum=Sum8(0, 19, 19),
)
DAIKIN2_SECOND = Layout(
    bytes.fromhex("11da27000008000000000006600000c1806000"),
    {
        "power": Field.at(5, 0, 1),
        "mode": Field.at(5, 4, 3, values=DAIKIN_MODE),
        "temperature": Field.at(6, 1, 6, encode=int),  # whole °C
        "fan": Field.at(8, 4, 4, values=DAIKIN_FAN),
        "powerful": Field.at(13, 0, 1),
        "quiet": Field.at(13, 5, 1),
        "economy": Field.at(16, 2, 1),
        "purifier": Field.at(16, 4, 1),
    },
    checksum=Sum8(0, 18, 18),
)
DAIKIN2_MIN_COOL = 18.0  # kDaikin2MinCoolTemp


def _raise_setpoint(state, mode, floor):
    """``state`` with its setpoint raised to ``floor`` when it runs in ``mode``.

    An off message carries mode auto on these protocols (see ``frames``), so
    the floor only applies while the unit is on.
    """
    if state.power and state.mode == mode and state.temperature < floor:
        return replace(state, temperature=floor)
    return state


class Daikin2Device(Device):
    """Daikin2 (ARC477A1): a full-state protocol, ``previous`` is ignored."""

    PROTOCOL = DAIKIN2
    LAYOUTS = (None, DAIKIN2_FIRST, DAIKIN2_SECOND)
    capabilities = Capabilities(
        modes=DAIKIN_MODES,
        temperature=TemperatureRange(10.0, 32.0),
        fan=DAIKIN_FAN_CHOICE,
        swing_v=Choice(
            ("off", "auto", "1", "2", "3", "4", "5", "6"),
            {
                "off": "off",
                "auto": "auto",
                "1": "ceiling",
                "2": "90°",
                "3": "60°",
                "4": "45°",
                "5": "30°",
                "6": "0°",
            },
        ),
        swing_h=Choice(
            ("off", "auto", "1", "2", "3", "4", "5", "6"),
            {
                "off": "off",
                "auto": "auto",
                "1": "far left",
                "2": "close left",
                "3": "middle",
                "4": "close right",
                "5": "far right",
                "6": "wide",
            },
        ),
        features=dict.fromkeys(
            ("economy", "powerful", "quiet", "cleaning", "purifier", "light"), ON_OFF
        ),
    )

    def normalise(self, state):
        # setTemp: kDaikin2MinCoolTemp in cool, kDaikinMinTemp otherwise.
        state = super().normalise(state)
        return _raise_setpoint(state, "cool", DAIKIN2_MIN_COOL)

    def frames(self, previous, target, actions):
        feat = target.features
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which Daikin2 maps to auto), so the cool minimum never
        # applies to it.
        mode = target.mode if target.power else "auto"
        temperature = target.temperature
        if mode == "cool":
            temperature = max(temperature, DAIKIN2_MIN_COOL)
        first = DAIKIN2_FIRST.build(
            power2=not target.power,
            light=feat["light"],
            mold=feat["cleaning"],
            swing_h=target.swing_h,
            swing_v=target.swing_v,
        )
        second = DAIKIN2_SECOND.build(
            power=target.power,
            mode=mode,
            temperature=temperature,
            fan=target.fan,
            powerful=feat["powerful"],
            quiet=feat["quiet"] and not feat["powerful"],  # powerful cancels quiet
            economy=feat["economy"],
            purifier=feat["purifier"],
        )
        return [
            Frame("leader", b""),
            Frame("main", bytes(first)),
            Frame("main", bytes(second)),
        ]


DAIKIN2_MODELS = (
    "ARC477A1 remote",
    "FTXZ25NV1B",
    "FTXZ35NV1B",
    "FTXZ50NV1B",
    "Daikin2",
)


# --------------------------------------------------------------- Daikin (ARC433)
# Layout from IRremoteESP8266's DaikinESPProtocol (ir_Daikin.h): 35 bytes in
# three sections of 8, 8 and 19, each closed by a sum-of-bytes checksum
# (kDaikinByteChecksum1/2, Sum3); frame byte n of the third section is
# struct byte n + 16. The message opens with a headerless 5-bit all-zero
# leader (kDaikinHeaderLength). Every space after a footer mark is
# kDaikinZeroSpace + kDaikinGap.

DAIKIN_ARC = Protocol(
    "daikin",
    {
        "leader": Section(PulseDistance(428, 428, 1280), footer=(428,), gap=29428),
        "main": Section(
            PulseDistance(428, 428, 1280),
            header=(3650, 1623),
            footer=(428,),
            gap=29428,
        ),
    },
    carrier=38000,
    # decodeDaikin: kDaikinTolerance (35 %), kDaikinMarkExcess (kMarkExcess).
    tolerance=0.35,
)

# The first two sections carry nothing the C path drives (Comfort, and the
# clock that IRac never sets): they are sent as the header's reset state.
DAIKIN_ARC_FIRST = Layout(bytes.fromhex("11da2700c5000000"), {}, checksum=Sum8(0, 7, 7))
DAIKIN_ARC_SECOND = Layout(
    bytes.fromhex("11da270042000000"), {}, checksum=Sum8(0, 7, 7)
)
DAIKIN_ARC_THIRD = Layout(
    # Hardwired: byte 5 bit 3 (always 1), timers unused (kDaikinUnusedTime
    # in bytes 10-12), byte 15 = 0xC0.
    bytes.fromhex("11da27000008000000000006600000c0000000"),
    {
        "power": Field.at(5, 0, 1),
        "mode": Field.at(5, 4, 3, values=DAIKIN_MODE),
        "half_degrees": Field.at(6, 0, 8),  # Temp: °C × 2
        "swing_v": Field.at(8, 0, 4, values=DAIKIN_SWING),
        "fan": Field.at(8, 4, 4, values=DAIKIN_FAN),
        "swing_h": Field.at(9, 0, 4, values=DAIKIN_SWING),
        "powerful": Field.at(13, 0, 1),
        "quiet": Field.at(13, 5, 1),
        "economy": Field.at(16, 2, 1),
        "mold": Field.at(17, 1, 1),
    },
    checksum=Sum8(0, 18, 18),
)


class DaikinArcDevice(Device):
    """Daikin (ARC433 and others): a full-state protocol, ``previous`` is
    ignored."""

    PROTOCOL = DAIKIN_ARC
    LAYOUTS = (None, DAIKIN_ARC_FIRST, DAIKIN_ARC_SECOND, DAIKIN_ARC_THIRD)
    capabilities = Capabilities(
        modes=DAIKIN_MODES,
        temperature=TemperatureRange(10.0, 32.0, (0, 5)),
        fan=DAIKIN_FAN_CHOICE,
        swing_v=SWING,
        swing_h=SWING,
        features=dict.fromkeys(("economy", "powerful", "quiet", "cleaning"), ON_OFF),
    )

    def frames(self, previous, target, actions):
        feat = target.features
        third = DAIKIN_ARC_THIRD.build(
            power=target.power,
            # As the C path: an off message carries mode auto (IRac passes
            # mode "off", which convertMode maps to auto).
            mode=target.mode if target.power else "auto",
            half_degrees=int(target.temperature * 2),
            swing_v=target.swing_v,
            fan=target.fan,
            swing_h=target.swing_h,
            # As IRDaikinESP's setters, called in IRac's order (quiet,
            # powerful, econo): powerful cancels quiet, econo cancels powerful.
            quiet=feat["quiet"] and not feat["powerful"],
            powerful=feat["powerful"] and not feat["economy"],
            economy=feat["economy"],
            mold=feat["cleaning"],
        )
        return [
            Frame("leader", b"\x00", 5),
            Frame("main", bytes(DAIKIN_ARC_FIRST.build())),
            Frame("main", bytes(DAIKIN_ARC_SECOND.build())),
            Frame("main", bytes(third)),
        ]


DAIKIN_ARC_MODELS = (
    "ARC433 remote",
    "M Series",
    "FTXM-M",
    "ARC466A12 remote",
    "ARC466A33 remote",
    "Daikin",
)


# -------------------------------------------------------------- Daikin64
# Layout from IRremoteESP8266's Daikin64Protocol (ir_Daikin.h): one 64-bit
# word sent LSB first, i.e. 8 bytes in order, each LSB first. The message is
# a bitless leader (two kDaikin64LdrMark/LdrSpace pairs), the frame, then a
# bare kDaikin64HdrMark followed by kDefaultMessageGap (sendDaikin64).

DAIKIN64 = Protocol(
    "daikin64",
    {
        "leader": Section(None, header=(9800, 9800, 9800, 9800)),
        "main": Section(
            PulseDistance(350, 382, 954),
            header=(4600, 2500),
            footer=(350,),
            gap=20300,
        ),
        "trailer": Section(None, header=(4600,), gap=100000),
    },
    # decodeDaikin64: the leader with the defaults, header, bits and footer #1
    # with _tolerance + kDaikin64ToleranceDelta (30 %), kMarkExcess.
    tolerance=0.30,
)


DAIKIN64_MODE = {"dry": 1, "cool": 2, "fan": 4, "heat": 8}  # kDaikin64*
DAIKIN64_FAN = {  # canonical fan -> kDaikin64Fan*
    "auto": 0b0001,
    "1": 0b1001,  # quiet
    "2": 0b1000,  # low
    "3": 0b0100,  # medium
    "4": 0b0010,  # high
    "5": 0b0011,  # turbo
}
# kDaikin64MinTemp..kDaikin64MaxTemp, whole °C, BCD
DAIKIN64_TEMPERATURE = {t: _bcd(t) for t in range(16, 31)}

# Skeleton from kDaikin64KnownGoodState with the written fields and the sum
# cleared: byte 0 is 0x16, the clock (07:20, BCD) and both timers (22 h,
# disabled) are never set by the C path, and byte 7 bit 2 is always set.
DAIKIN64_LAYOUT = Layout(
    bytes.fromhex("1600200716160004"),
    {
        "mode": Field.at(1, 0, 4, values=DAIKIN64_MODE),
        "fan": Field.at(1, 4, 4, values=DAIKIN64_FAN),
        "temperature": Field.at(6, 0, 8, values=DAIKIN64_TEMPERATURE),
        "swing_v": Field.at(7, 0, 1, values=DAIKIN_SWING_BIT),
        "sleep": Field.at(7, 1, 1),
        "power": Field.at(7, 3, 1),  # a toggle
    },
    checksum=HighNibbleSum(0, 7, 7, with_low=True),  # kDaikin64Checksum*
)


class Daikin64Device(Device):
    """Daikin64 (DGS01): full state, except that the power bit is a toggle.

    With ``previous`` the bit is set only when the power changes. This is a
    deliberate deviation from the C path: IRac::daikin64 calls
    setPowerToggle(on) on every message (handleToggles covers DAIKIN128, not
    DAIKIN64), so with a persistent object any change made while the unit is
    on, a setpoint change say, toggled it off. Without ``previous`` the bit
    is ``target.power``, as the C path sends: an "on" toggles, an "off"
    toggles nothing.
    """

    PROTOCOL = DAIKIN64
    LAYOUTS = (None, DAIKIN64_LAYOUT, None)
    capabilities = Capabilities(
        modes=("dry", "cool", "heat", "fan"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=FAN_5,
        swing_v=SWING,
        features={"sleep": ON_OFF},  # Sleep bit (setSleep)
    )

    def frames(self, previous, target, actions):
        if previous is None:
            toggle = target.power
        else:
            toggle = target.power != previous.power
        data = DAIKIN64_LAYOUT.build(
            # As the C path: an off message carries mode cool (IRac passes
            # mode "off", which convertMode maps to cool).
            mode=target.mode if target.power else "cool",
            fan=target.fan,
            temperature=int(target.temperature),
            swing_v=target.swing_v,
            sleep=target.features["sleep"],
            power=toggle,
        )
        return [
            Frame("leader", b""),
            Frame("main", bytes(data)),
            Frame("trailer", b""),
        ]


DAIKIN64_MODELS = ("FFN-C/FCN-F Series", "DGS01 remote", "FTWX35AXV1", "Daikin64")


# --------------------------------------------------------------- Daikin128
# Layout from IRremoteESP8266's Daikin128Protocol (ir_Daikin.h): 16 bytes
# sent as two headerless-joined sections of 8 (kDaikin128SectionLength);
# frame byte n of the second section is struct byte n + 8. The first
# section's checksum is the top nibble of its last byte, the second's is a
# nibble sum in its last byte (IRDaikin128::calcFirst/SecondChecksum).

DAIKIN128 = Protocol(
    "daikin128",
    {
        # kDaikin128LeaderMark/Space, sent twice
        "preamble": Section(None, header=(9800, 9800, 9800, 9800)),
        "first": Section(
            PulseDistance(350, 382, 954),
            header=(4600, 2500),
            footer=(350,),
            gap=20300,
        ),
        # No header: the bits follow the first section's gap directly, and
        # the section closes on kDaikin128FooterMark (= kDaikin128HdrMark).
        "second": Section(PulseDistance(350, 382, 954), footer=(4600,), gap=20300),
    },
    carrier=38000,  # kDaikin128Freq
    # decodeDaikin128: kDaikinTolerance (35 %), kDaikinMarkExcess (kMarkExcess).
    tolerance=0.35,
)


DAIKIN128_MODE = {  # kDaikin128*
    "dry": 0b0001,
    "cool": 0b0010,
    "fan": 0b0100,
    "heat": 0b1000,
    "auto": 0b1010,
}
DAIKIN128_FAN = {  # canonical fan -> kDaikin128Fan*
    "auto": 0b0001,  # kDaikin128FanAuto
    "1": 0b1001,  # lowest: kDaikin128FanQuiet
    "2": 0b1000,  # kDaikin128FanLow
    "3": 0b0100,  # kDaikin128FanMed
    "4": 0b0010,  # kDaikin128FanHigh
    "5": 0b0011,  # highest: kDaikin128FanPowerful
}
# kDaikin128MinTemp..kDaikin128MaxTemp, BCD (setTemp: uint8ToBcd)
DAIKIN128_TEMPERATURE = {t: _bcd(t) for t in range(16, 31)}

DAIKIN128_FIRST = Layout(
    bytes.fromhex("1600000000000004"),  # byte 7 bit 2: always 1
    {
        "mode": Field.at(1, 0, 4, values=DAIKIN128_MODE),
        "fan": Field.at(1, 4, 4, values=DAIKIN128_FAN),
        "clock_mins": Field.at(2, 0, 8),  # BCD
        "clock_hours": Field.at(3, 0, 8),  # BCD
        "on_hours": Field.at(4, 0, 6),  # BCD
        "on_half_hour": Field.at(4, 6, 1),
        "on_timer": Field.at(4, 7, 1),
        "off_hours": Field.at(5, 0, 6),  # BCD
        "off_half_hour": Field.at(5, 6, 1),
        "off_timer": Field.at(5, 7, 1),
        "temperature": Field.at(6, 0, 8, values=DAIKIN128_TEMPERATURE),
        "swing_v": Field.at(7, 0, 1, values=DAIKIN_SWING_BIT),
        "sleep": Field.at(7, 1, 1),
        "power": Field.at(7, 3, 1),  # a toggle, not a state
    },
    checksum=HighNibbleSum(0, 7, 7, with_low=True),
)
DAIKIN128_SECOND = Layout(
    bytes.fromhex("a100000000000000"),
    {
        "ceiling": Field.at(1, 0, 1),  # light toggle, ceiling unit
        "economy": Field.at(1, 2, 1),
        "wall": Field.at(1, 3, 1),  # light toggle, wall unit
    },
    checksum=NibbleSum(0, 7, 7),
)


class Daikin128Device(Device):
    """Daikin128 (BRC52B63): full state, but power and light are toggle bits.

    The power bit asks the unit to flip its power, so it is set only when
    the power changes: ``previous.power != target.power``. With no previous
    state it is set for "on" and clear for "off", as IRac sends from a fresh
    object (no previous state to toggle against). The light is the same kind
    of toggle (IRac::handleToggles treats DAIKIN128's light as it treats its
    power), sent on the wall-unit bit as IRac::daikin128 does
    (setLightToggle(kDaikin128BitWall)).
    """

    PROTOCOL = DAIKIN128
    LAYOUTS = (None, DAIKIN128_FIRST, DAIKIN128_SECOND)
    capabilities = Capabilities(
        modes=DAIKIN_MODES,
        temperature=TemperatureRange(16.0, 30.0),
        fan=FAN_5,
        swing_v=SWING,
        # Econo and Sleep bits; the light is a toggle (Wall bit)
        features={"economy": ON_OFF, "sleep": ON_OFF, "light": ON_OFF},
    )

    def frames(self, previous, target, actions):
        light = target.features["light"]
        if previous is None:
            toggle = target.power
        else:
            toggle = previous.power != target.power
            light = light != previous.features["light"]
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to auto).
        mode = target.mode if target.power else "auto"
        fan = target.fan
        if mode == "auto" and fan in ("1", "5"):
            fan = "auto"  # setFan: no quiet or powerful in auto
        first = DAIKIN128_FIRST.build(
            mode=mode,
            fan=fan,
            temperature=target.temperature,
            swing_v=target.swing_v,
            sleep=target.features["sleep"],
            power=toggle,
        )
        second = DAIKIN128_SECOND.build(
            wall=light,
            # setEcono: only in cool and heat
            economy=target.features["economy"] and mode in ("cool", "heat"),
        )
        return [
            Frame("preamble", b""),
            Frame("first", bytes(first)),
            Frame("second", bytes(second)),
        ]


DAIKIN128_MODELS = (
    "17 Series FTXB09AXVJU",
    "17 Series FTXB12AXVJU",
    "17 Series FTXB24AXVJU",
    "BRC52B63 remote",
    "Daikin128",
)


# --------------------------------------------------------------- Daikin152
# Layout from IRremoteESP8266's Daikin152Protocol (ir_Daikin.h): one 19-byte
# frame closed by a sum-of-bytes checksum, preceded by a 5-bit all-zero
# leader sent with the same bit timings but no header.

DAIKIN152 = Protocol(
    "daikin152",
    {
        "leader": Section(PulseDistance(433, 433, 1529), footer=(433,), gap=25182),
        "main": Section(
            PulseDistance(433, 433, 1529),  # kDaikin152BitMark/ZeroSpace/OneSpace
            header=(3492, 1718),  # kDaikin152HdrMark/HdrSpace
            footer=(433,),
            gap=25182,  # kDaikin152Gap
        ),
    },
    carrier=38000,  # kDaikin152Freq
)

DAIKIN152_LEADER = Frame("leader", b"\x00", 5)  # kDaikin152LeaderBits zeros
DAIKIN152_MAIN = Layout(
    bytes.fromhex("11da27000000000000000000000000c5000000"),
    {
        "power": Field.at(5, 0, 1),
        "mode": Field.at(5, 4, 3, values=DAIKIN_MODE),
        "temperature": Field.at(6, 1, 7, encode=int),  # whole °C
        "swing_v": Field.at(8, 0, 4, values=DAIKIN_SWING),
        "fan": Field.at(8, 4, 4, values=DAIKIN_FAN),
        "powerful": Field.at(13, 0, 1),
        "quiet": Field.at(13, 5, 1),
        "comfort": Field.at(16, 1, 1),  # never set through IRac
        "economy": Field.at(16, 2, 1),
        "sensor": Field.at(16, 3, 1),  # never set through IRac
    },
    checksum=Sum8(0, 18, 18),
)
DAIKIN152_MIN_TEMP = 10.0  # kDaikinMinTemp, heat only
DAIKIN152_MIN_OTHER = 18.0  # kDaikin2MinCoolTemp, every other mode
DAIKIN152_MAX_TEMP = 32.0  # kDaikinMaxTemp


class Daikin152Device(Device):
    """Daikin152 (ARC480A5): a full-state protocol, ``previous`` is ignored."""

    PROTOCOL = DAIKIN152
    LAYOUTS = (None, DAIKIN152_MAIN)
    capabilities = Capabilities(
        modes=DAIKIN_MODES,
        temperature=TemperatureRange(10.0, 32.0),
        fan=DAIKIN_FAN_CHOICE,
        swing_v=SWING,
        features=dict.fromkeys(("economy", "powerful", "quiet"), ON_OFF),
    )

    def normalise(self, state):
        # setTemp: kDaikinMinTemp in heat, kDaikin2MinCoolTemp in every other
        # mode (the union's 10 °C is heat only).
        state = super().normalise(state)
        if state.mode == "heat":
            return state
        return _raise_setpoint(state, state.mode, DAIKIN152_MIN_OTHER)

    def frames(self, previous, target, actions):
        feat = target.features
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which Daikin152 maps to auto).
        mode = target.mode if target.power else "auto"
        # IRac sets the mode before the setpoint, so the dry/fan setpoints
        # setMode writes are always overwritten; setTemp's floor is 10 °C in
        # heat and 18 °C in every other mode.
        floor = DAIKIN152_MIN_TEMP if mode == "heat" else DAIKIN152_MIN_OTHER
        temperature = min(max(target.temperature, floor), DAIKIN152_MAX_TEMP)
        # IRac sets quiet, then powerful (which clears quiet), then econo
        # (which clears powerful).
        main = DAIKIN152_MAIN.build(
            power=target.power,
            mode=mode,
            temperature=temperature,
            swing_v=target.swing_v,
            fan=target.fan,
            powerful=feat["powerful"] and not feat["economy"],
            quiet=feat["quiet"] and not feat["powerful"],
            economy=feat["economy"],
        )
        return [DAIKIN152_LEADER, Frame("main", bytes(main))]


DAIKIN152_MODELS = ("ARC480A5 remote", "Daikin152")


# --------------------------------------------------------------- Daikin160
# Layout from IRremoteESP8266's Daikin160Protocol (ir_Daikin.h): 20 bytes in
# two sections of 7 and 13, each closed by a sum-of-bytes checksum; frame
# byte n of the second section is struct byte n + 7.

DAIKIN160 = Protocol(
    "daikin160",
    {
        "main": Section(
            PulseDistance(342, 700, 1786),
            header=(5000, 2145),
            footer=(342,),
            gap=29650,
        ),
    },
    carrier=38000,
    # decodeDaikin160: kDaikinTolerance (35 %), kDaikinMarkExcess (kMarkExcess).
    tolerance=0.35,
)

DAIKIN160_SWING_V = {  # kDaikin160SwingV*; the header has no "off" value
    "auto": 0xF,
    "1": 0x5,  # highest
    "2": 0x4,  # high
    "3": 0x3,  # middle
    "4": 0x2,  # low
    "5": 0x1,  # lowest
}

# setFan: kDaikinFanAuto, speeds kDaikinFanMin (1) .. kDaikinFanMax (5) sent
# as the speed plus 2. convertFan maps kMin..kMax to speeds 1..5, so the old
# vocabulary's low/medium/high are speeds 2/3/4 (FAN_5's labels).
DAIKIN160_FAN = {"auto": 0xA, "1": 3, "2": 4, "3": 5, "4": 6, "5": 7}

DAIKIN160_FIRST = Layout(
    bytes.fromhex("11da27f00d0000"),
    {},
    checksum=Sum8(0, 6, 6),
)
DAIKIN160_SECOND = Layout(
    bytes.fromhex("11da2700d30001000000000800"),
    {
        "power": Field.at(5, 0, 1),
        "mode": Field.at(5, 4, 3, values=DAIKIN_MODE),
        "swing_v": Field.at(6, 4, 4, values=DAIKIN160_SWING_V),
        "temperature": Field.at(9, 1, 6),  # whole °C - 10
        "fan": Field.at(10, 0, 4, values=DAIKIN160_FAN),
    },
    checksum=Sum8(0, 12, 12),
)


class Daikin160Device(Device):
    """Daikin160 (ARC423A5): a full-state protocol, ``previous`` is ignored."""

    PROTOCOL = DAIKIN160
    LAYOUTS = (DAIKIN160_FIRST, DAIKIN160_SECOND)
    capabilities = Capabilities(
        modes=DAIKIN_MODES,
        temperature=TemperatureRange(10.0, 32.0),
        fan=FAN_5,
        # No "off": the header documents kDaikin160SwingVAuto and five
        # positions only (setSwingVertical sends anything else as auto).
        swing_v=SWING_V_AUTO_ANGLES,
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to auto).
        second = DAIKIN160_SECOND.build(
            power=target.power,
            mode=target.mode if target.power else "auto",
            swing_v=target.swing_v,
            temperature=int(target.temperature) - 10,
            fan=target.fan,
        )
        return [
            Frame("main", bytes(DAIKIN160_FIRST.build())),
            Frame("main", bytes(second)),
        ]


DAIKIN160_MODELS = ("ARC423A5 remote", "FTE12HV2S", "Daikin160")


# ------------------------------------------------------------- Daikin176
# Layout from IRremoteESP8266's Daikin176Protocol (ir_Daikin.h): 22 bytes in
# two sections of 7 and 15, each closed by a sum-of-bytes checksum; frame
# byte n of the second section is struct byte n + 7.

DAIKIN176 = Protocol(
    "daikin176",
    {
        "main": Section(
            PulseDistance(370, 710, 1780),
            header=(5070, 2140),
            footer=(370,),
            gap=29410,
        ),
    },
    carrier=38000,
    # decodeDaikin176: kDaikinTolerance (35 %), kDaikinMarkExcess (kMarkExcess).
    tolerance=0.35,
)

DAIKIN176_MODES = {"fan": 0, "heat": 1, "cool": 2, "auto": 3, "dry": 7}
# AltMode bits kept in line with the mode (IRDaikin176::setMode)
DAIKIN176_ALT_MODES = {"fan": 6, "heat": 7, "cool": 7, "auto": 7, "dry": 2}
DAIKIN176_DRY_FAN_TEMP = 17.0  # kDaikin176DryFanTemp

DAIKIN176_FIRST = Layout(
    bytes.fromhex("11da1718040000"),
    {"unit_id": Field.at(3, 0, 1)},  # Id1: 0 = unit A, 1 = unit B
    checksum=Sum8(0, 6, 6),
)
DAIKIN176_SECOND = Layout(
    bytes.fromhex("11da17180003000000000000002000"),
    {
        "unit_id": Field.at(3, 0, 1),  # Id2, always equal to Id1
        "alt_mode": Field.at(5, 4, 3),
        "mode_button": Field.at(6, 0, 8),  # kDaikin176ModeButton when set
        "power": Field.at(7, 0, 1),
        "mode": Field.at(7, 4, 3, values=DAIKIN176_MODES),
        "temperature": Field.at(10, 1, 6),  # whole °C - 9
        "swing_h": Field.at(11, 0, 4, values={"off": 0x6, "swing": 0x5}),
        "fan": Field.at(11, 4, 4, values={"1": 1, "2": 3}),  # kDaikinFanMin/176FanMax
    },
    checksum=Sum8(0, 14, 14),
)


class Daikin176Device(Device):
    """Daikin176 (BRC4C153): a full-state protocol, ``previous`` is ignored.

    The header's ModeButton byte marks a mode-button press, but the C path
    always clears it (IRac::daikin176 calls setTemp and setFan after
    setMode), so every message is a plain full state with ModeButton 0.
    """

    PROTOCOL = DAIKIN176
    LAYOUTS = (DAIKIN176_FIRST, DAIKIN176_SECOND)
    capabilities = Capabilities(
        modes=DAIKIN_MODES,
        temperature=TemperatureRange(10.0, 32.0),
        fan=Choice(("1", "2"), {"1": "low", "2": "high"}),
        swing_h=SWING,
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode cool (IRac passes mode
        # "off", which convertMode maps to cool) with the setpoint as given.
        mode = target.mode if target.power else "cool"
        temperature = target.temperature
        if mode in ("dry", "fan"):
            temperature = DAIKIN176_DRY_FAN_TEMP
        first = DAIKIN176_FIRST.build()
        second = DAIKIN176_SECOND.build(
            alt_mode=DAIKIN176_ALT_MODES[mode],
            mode_button=0,
            power=target.power,
            mode=mode,
            temperature=int(temperature) - 9,
            swing_h=target.swing_h,
            fan=target.fan,
        )
        return [Frame("main", bytes(first)), Frame("main", bytes(second))]


DAIKIN176_MODELS = ("BRC4C153 remote", "FFQ35B8V1B", "BRC4C151 remote", "Daikin176")


# --------------------------------------------------------------- Daikin216
# Layout from IRremoteESP8266's Daikin216Protocol (ir_Daikin.h): 27 bytes in
# two sections of 8 and 19 (kDaikin216Section1Length), each closed by a
# sum-of-bytes checksum; frame byte n of the second section is struct byte
# n + 8.

DAIKIN216 = Protocol(
    "daikin216",
    {
        "main": Section(
            PulseDistance(420, 450, 1300),
            header=(3440, 1750),
            footer=(420,),
            gap=29650,
        ),
    },
    carrier=38000,
    # decodeDaikin216: kDaikinTolerance (35 %), kDaikinMarkExcess (kMarkExcess).
    tolerance=0.35,
)

DAIKIN216_SWING = {"off": 0b0000, "swing": 0b1111}  # kDaikin216Swing{Off,On}

# setFan as DAIKIN_FAN, but quiet (kDaikinFanQuiet) is the quiet feature
# (setQuiet), not a fan step: speeds 1..5 are "1".."5".
DAIKIN216_FAN = {
    "auto": 0xA,  # kDaikinFanAuto
    "1": 3,  # speed 1, kDaikinFanMin
    "2": 4,
    "3": 5,  # kDaikinFanMed
    "4": 6,
    "5": 7,  # kDaikinFanMax
    "quiet": 0xB,  # kDaikinFanQuiet, written by the quiet feature
}
DAIKIN216_FAN_CHOICE = Choice(
    ("auto", "1", "2", "3", "4", "5"),
    {
        "auto": "auto",
        "1": "low",
        "2": "medium-low",
        "3": "medium",
        "4": "high",
        "5": "highest",
    },
)

DAIKIN216_FIRST = Layout(
    bytes.fromhex("11da27f000000000"),
    {},
    checksum=Sum8(0, 7, 7),
)
DAIKIN216_SECOND = Layout(
    bytes.fromhex("11da27000000000000000000000000c0000000"),
    {
        "power": Field.at(5, 0, 1),
        "mode": Field.at(5, 4, 3, values=DAIKIN_MODE),
        "temperature": Field.at(6, 1, 6, encode=int),  # whole °C
        "swing_v": Field.at(8, 0, 4, values=DAIKIN216_SWING),
        # kDaikinFan*, plus quiet as a fan value (kDaikinFanQuiet).
        "fan": Field.at(8, 4, 4, values=DAIKIN216_FAN),
        "swing_h": Field.at(9, 0, 4, values=DAIKIN216_SWING),
        "powerful": Field.at(13, 0, 1),
    },
    checksum=Sum8(0, 18, 18),
)


class Daikin216Device(Device):
    """Daikin216 (ARC433B69): a full-state protocol, ``previous`` is ignored."""

    PROTOCOL = DAIKIN216
    LAYOUTS = (DAIKIN216_FIRST, DAIKIN216_SECOND)
    capabilities = Capabilities(
        modes=DAIKIN_MODES,
        temperature=TemperatureRange(10.0, 32.0),
        fan=DAIKIN216_FAN_CHOICE,
        swing_v=SWING,
        swing_h=SWING,
        features=dict.fromkeys(("powerful", "quiet"), ON_OFF),
    )

    def frames(self, previous, target, actions):
        feat = target.features
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode turns into auto).
        mode = target.mode if target.power else "auto"
        # Quiet is a fan speed (kDaikinFanQuiet); powerful cancels quiet and
        # then leaves the fan on auto (IRDaikin216::setPowerful/setQuiet).
        fan = target.fan
        if feat["quiet"]:
            fan = "auto" if feat["powerful"] else "quiet"
        second = DAIKIN216_SECOND.build(
            power=target.power,
            mode=mode,
            temperature=target.temperature,
            swing_v=target.swing_v,
            fan=fan,
            swing_h=target.swing_h,
            powerful=feat["powerful"],
        )
        return [
            Frame("main", bytes(DAIKIN216_FIRST.build())),
            Frame("main", bytes(second)),
        ]


DAIKIN216_MODELS = ("ARC433B69 remote", "ARC484A4 remote", "FTQ60TV16U2", "Daikin216")


# --------------------------------------------------------------- Daikin312
# Layout from IRremoteESP8266's Daikin312Protocol (ir_Daikin.h): 39 bytes in
# two sections of 20 and 19, each closed by a sum-of-bytes checksum; frame
# byte n of the second section is struct byte n + 20. The sections follow a
# headerless leader of five zero bits (sendDaikin312).

DAIKIN312_BITS = PulseDistance(453, 414, 1275)  # kDaikin312BitMark/Zero/OneSpace
DAIKIN312 = Protocol(
    "daikin312",
    {
        "leader": Section(DAIKIN312_BITS, footer=(453,), gap=25100),
        "main": Section(DAIKIN312_BITS, header=(3518, 1688), footer=(453,), gap=35512),
    },
    carrier=36700,  # kDaikin312Freq
    # decodeDaikin312: kDaikinTolerance (35 %), mark excess 0.
    tolerance=0.35,
    mark_excess=0,
)

DAIKIN312_SWING_V = {  # kDaikin312SwingV*
    "off": 0x0,  # kDaikin312SwingVOff
    "swing": 0xF,  # kDaikin312SwingVAuto, a.k.a. swing
    "1": 0x1,  # highest
    "2": 0x2,  # high
    "3": 0x3,  # upper middle
    "4": 0x4,  # lower middle
    "5": 0x5,  # low
    "6": 0x6,  # lowest
}

# Skeleton bits the port never changes, as IRac::daikin312 sends them: beep
# off (Beep = 3, byte 7) and auto clean hardwired on (Clean, byte 14 bit 4).
DAIKIN312_FIRST = Layout(
    bytes.fromhex("11da2700025864d8640600000000100000000000"),
    {
        "power2": Field.at(6, 7, 1),  # inverse of power
        "mold": Field.at(8, 3, 1),
        "light": Field.at(12, 0, 2, values={True: 1, False: 3}),  # as IRac
    },
    checksum=Sum8(0, 19, 19),
)
DAIKIN312_SECOND = Layout(
    bytes.fromhex("11da27000008000000000006600000c5000800"),
    {
        "power": Field.at(5, 0, 1),
        "mode": Field.at(5, 4, 3, values=DAIKIN_MODE),
        "temperature": Field.at(6, 0, 7),  # in half degrees
        "swing_v": Field.at(8, 0, 4, values=DAIKIN312_SWING_V),
        "fan": Field.at(8, 4, 4, values=DAIKIN_FAN),
        "swing_h": Field.at(9, 0, 4, values=DAIKIN_SWING),
        "powerful": Field.at(13, 0, 1),
        "quiet": Field.at(13, 5, 1),
        "economy": Field.at(16, 2, 1),
        "purifier": Field.at(16, 4, 1),
    },
    checksum=Sum8(0, 18, 18),
)
DAIKIN312_MIN_COOL = 18.0  # kDaikin312MinCoolTemp


class Daikin312Device(Device):
    """Daikin312 (ARC466A67): a full-state protocol, ``previous`` is ignored."""

    PROTOCOL = DAIKIN312
    LAYOUTS = (None, DAIKIN312_FIRST, DAIKIN312_SECOND)
    capabilities = Capabilities(
        modes=DAIKIN_MODES,
        temperature=TemperatureRange(10.0, 32.0, (0, 5)),
        fan=DAIKIN_FAN_CHOICE,
        # The positions carry Daikin2's labels: the same kDaikin*SwingV*
        # values.
        swing_v=Choice(
            ("off", "swing", "1", "2", "3", "4", "5", "6"),
            {
                "off": "off",
                "swing": "on",
                "1": "ceiling",
                "2": "90°",
                "3": "60°",
                "4": "45°",
                "5": "30°",
                "6": "0°",
            },
        ),
        # Only off/swing: kDaikin312SwingH{Wide,LeftMax,...} are 8-bit
        # values that do not fit the header's 4-bit SwingH field.
        swing_h=SWING,
        features=dict.fromkeys(
            (
                "quiet",
                "powerful",
                "light",
                "economy",
                "purifier",
                "cleaning",
            ),
            ON_OFF,
        ),
    )

    def normalise(self, state):
        # setTemp: kDaikin312MinCoolTemp in cool, kDaikinMinTemp otherwise.
        state = super().normalise(state)
        return _raise_setpoint(state, "cool", DAIKIN312_MIN_COOL)

    def frames(self, previous, target, actions):
        feat = target.features
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which Daikin312 maps to auto), so the cool minimum never
        # applies to it.
        mode = target.mode if target.power else "auto"
        temperature = target.temperature
        if mode == "cool":
            temperature = max(temperature, DAIKIN312_MIN_COOL)
        first = DAIKIN312_FIRST.build(
            power2=not target.power,
            mold=feat["cleaning"],
            light=feat["light"],
        )
        second = DAIKIN312_SECOND.build(
            power=target.power,
            mode=mode,
            temperature=int(temperature * 2),
            fan=target.fan,
            swing_v=target.swing_v,
            swing_h=target.swing_h,
            powerful=feat["powerful"],
            quiet=feat["quiet"] and not feat["powerful"],  # powerful cancels quiet
            economy=feat["economy"],
            purifier=feat["purifier"],
        )
        return [
            Frame("leader", b"\x00", 5),
            Frame("main", bytes(first)),
            Frame("main", bytes(second)),
        ]


DAIKIN312_MODELS = ("FTXM20R5V1B", "ARC466A67 remote", "Daikin312")


# ----- Daikinth / Smash2 (the 0.1.x native Daikin protocol)
# Layout from the legacy classes above (Daikinth.code_*, build_code, crc):
# one 18-byte body plus a checksum byte, sent MSB first (DAIKIN_NATIVE). The
# legacy code writes wire bytes, so values that read naturally LSB first
# (Daikin's usual mode and fan codes) appear bit-reversed here: mode 0xC on
# the wire is 3 (cool), fan 0xC is 3 (lowest), and so on.


def _bit_reverse_nibble(n):
    return int(f"{n:04b}"[::-1], 2)


class ReflectedSum8(Checksum):
    """Daikinth.crc: the sum of the bit-reversed bytes, bit-reversed back."""

    def compute(self, data):
        return bit_reverse(sum(self._input(data)) & 0xFF)


# code_mode: auto 0x80, heat 0x82, dry 0x84, fan 0x86, cool 0x8C (FBODY)
DAIKIN_NATIVE_MODE = {"auto": 0x0, "heat": 0x2, "dry": 0x4, "fan": 0x6, "cool": 0xC}
# code_fan: auto 0x05, else bit_reverse(48 + 16 * rank) for lowest..highest
DAIKIN_NATIVE_FAN = {"auto": 0x5}
DAIKIN_NATIVE_FAN.update({str(n): _bit_reverse_nibble(n + 2) for n in range(1, 6)})

# The 0.1.x Daikinth.FBODY frame body.
DAIKIN_NATIVE_BODY = (
    b"\x88\x5b\xe4\x00\x00\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x00\xa3\x00\x10"
)
DAIKIN_NATIVE_LAYOUT = Layout(
    DAIKIN_NATIVE_BODY + b"\x00",
    {
        # byte 5: power 0x80 | mode (code_mode; FBODY holds cool, 0x0C)
        "mode": Field.at(5, 0, 4, values=DAIKIN_NATIVE_MODE),
        "power": Field.at(5, 7, 1),
        # byte 6: bit_reverse(2 * setpoint) (code_temperature); dry replaces
        # it with 0x03 (code_mode)
        "temperature": Field.at(6, 0, 8),
        # byte 8: fan in the low nibble, swing in the high one (code_fan,
        # code_swing)
        "fan": Field.at(8, 0, 4, values=DAIKIN_NATIVE_FAN),
        "swing_v": Field.at(8, 4, 4, values={"off": 0x0, "swing": 0xF}),
        "powerful": Field.at(13, 7, 1),  # code_powerful: mask[13] = 0x80
        "off": Field.at(16, 1, 1),  # code_mode: mask[16] = 0x02 when off
    },
    checksum=ReflectedSum8(0, 18, 18, reverse=True),
)
DAIKIN_NATIVE_FAN_TEMPERATURE = 25  # set_mode("fan") forces 25 °C
DAIKIN_NATIVE_DRY_BYTE = 0x03  # code_mode("dry"): mask[6] = 0x03


class DaikinNativeDevice(Device):
    """Daikin's 0.1.x native protocol (Daikinth "generic", Smash2 "smash 2").

    A full-state protocol: ``previous`` is ignored. An off message carries
    the target's mode (without the power bit) and settings, as the legacy
    object sent its stored status with only the mode changed to off.
    """

    PROTOCOL = DAIKIN_NATIVE
    LAYOUTS = (DAIKIN_NATIVE_LAYOUT,)
    capabilities = Capabilities(
        modes=("cool", "fan", "dry", "heat", "auto"),
        temperature=TemperatureRange(18.0, 31.0),
        fan=FAN_5,
        swing_v=SWING,
        features={"powerful": ON_OFF},
    )

    def frames(self, previous, target, actions):
        if target.mode == "fan":
            temperature = bit_reverse(2 * DAIKIN_NATIVE_FAN_TEMPERATURE)
        elif target.mode == "dry" and target.power:
            temperature = DAIKIN_NATIVE_DRY_BYTE
        else:
            temperature = bit_reverse(int(2 * target.temperature))
        data = DAIKIN_NATIVE_LAYOUT.build(
            mode=target.mode,
            power=target.power,
            temperature=temperature,
            fan=target.fan,
            swing_v=target.swing_v,
            powerful=target.features["powerful"],
            off=not target.power,
        )
        return [Frame("main", bytes(data))]
