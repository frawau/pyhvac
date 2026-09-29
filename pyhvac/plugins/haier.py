#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Haier AC IR commands.
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
from ..fields import Field, Layout, Sum8
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import Capabilities, Choice, TemperatureRange

try:
    from ..irhvac import V9014557_A, V9014557_B
except ImportError:
    # Only the C-backed classes use these; keep the ported ones importable.
    V9014557_A = V9014557_B = None


class Haier(PulseBased):

    STARTFRAME = [3000, 4300]
    ENDFRAME = None
    MARK = [520]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [650, 1650]  # ditto

    def __init__(self):
        super().__init__("HAIER_AC")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto high", "auto low"],
            "purifier": ["off", "on"],
            "sleep": ["off", "on"],
        }


class Haier176A(PulseBased):

    STARTFRAME = [3000, 4300]
    ENDFRAME = None
    MARK = [520]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [650, 1650]  # ditto

    def __init__(self):
        super().__init__("HAIER_AC176", variant=V9014557_A)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto", "ceiling", "45°", "30°", "0°"],
            "hswing": ["auto", "far right", "right", "middle", "left", "far left"],
            "purifier": ["off", "on"],
            "sleep": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
        }


class Haier176B(PulseBased):

    STARTFRAME = [3000, 4300]
    ENDFRAME = None
    MARK = [520]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [650, 1650]  # ditto

    def __init__(self):
        super().__init__("HAIER_AC176", variant=V9014557_B)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto", "ceiling", "45°", "30°", "0°"],
            "hswing": ["auto", "far right", "right", "middle", "left", "far left"],
            "purifier": ["off", "on"],
            "sleep": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
        }


class HaierYRW02A(PulseBased):

    STARTFRAME = [3000, 4300]
    ENDFRAME = None
    MARK = [520]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [650, 1650]  # ditto

    def __init__(self):
        super().__init__("HAIER_AC_YRW02", variant=V9014557_A)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto", "ceiling", "45°", "30°", "0°"],
            "hswing": ["auto", "far right", "right", "middle", "left", "far left"],
            "purifier": ["off", "on"],
            "sleep": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
        }


class HaierYRW02B(PulseBased):

    STARTFRAME = [3000, 4300]
    ENDFRAME = None
    MARK = [520]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [650, 1650]  # ditto

    def __init__(self):
        super().__init__("HAIER_AC_YRW02", variant=V9014557_B)
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto", "ceiling", "45°", "30°", "0°"],
            "hswing": ["auto", "far right", "right", "middle", "left", "far left"],
            "purifier": ["off", "on"],
            "sleep": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
        }


class Haier160(PulseBased):

    STARTFRAME = [3000, 4300]
    ENDFRAME = None
    MARK = [520]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [650, 1650]  # ditto

    def __init__(self):
        super().__init__("HAIER_AC160")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat", "fan"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto", "ceiling", "90°", "45°", "30°", "0°"],
            "purifier": ["off", "on"],
            "sleep": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
            "cleaning": ["off", "on"],
            "light": ["off", "on"],
        }


DEVICES = {}


# ---------------------------------------------------------------- HaierAc
# Layout from IRremoteESP8266's HaierProtocol (ir_Haier.h): one 9-byte frame
# (kHaierACStateLength), sent MSB first. IRsend::sendHaierAC opens with a
# kHaierAcHdr mark and space before sendGeneric's kHaierAcHdr/kHaierAcHdrGap
# header, so the section header holds both pairs.

HAIER_AC = Protocol(
    "haier-ac",
    {
        "main": Section(
            PulseDistance(520, 650, 1650),  # kHaierAcBitMark/ZeroSpace/OneSpace
            header=(3000, 3000, 3000, 4300),  # kHaierAcHdr x3, kHaierAcHdrGap
            footer=(520,),
            gap=150000,  # kHaierAcMinGap
            lsb_first=False,
        ),
    },
    carrier=38000,  # sendHaierAC's enableIROut(38000)
)

HAIER_AC_COMMAND = {  # kHaierAcCmd*: the button the frame says was pressed
    "off": 0b0000,
    "on": 0b0001,
    "mode": 0b0010,
    "fan": 0b0011,
    "temp_up": 0b0110,
    "temp_down": 0b0111,
    "sleep": 0b1000,
    "timer_set": 0b1001,
    "timer_cancel": 0b1010,
    "health": 0b1100,
    "swing": 0b1101,
}
HAIER_AC_MODE = {  # kHaierAc{Auto,Cool,Dry,Heat,Fan}
    "auto": 0,
    "cool": 1,
    "dry": 2,
    "heat": 3,
    "fan": 4,
}
HAIER_AC_FAN = {  # canonical fan -> the raw Fan value IRHaierAC::setFan stores
    "auto": 0,  # kHaierAcFanAuto
    "1": 3,  # kHaierAcFanLow (kLow)
    "2": 2,  # kHaierAcFanMed (kMedium)
    "3": 1,  # kHaierAcFanHigh (kHigh)
}
HAIER_AC_SWING_V = {  # kHaierAcSwingV*, as IRHaierAC::convertSwingV
    "off": 0b00,  # Off (kOff)
    "1": 0b01,  # Up ("auto high" = kHigh)
    "2": 0b10,  # Down ("auto low" = kLow)
    "change": 0b11,  # Chg (kAuto): not offered by the entity
}
HAIER_AC_MIN_TEMP = 16  # kHaierAcMinTemp
HAIER_AC_MAX_TEMP = 30  # kHaierAcMaxTemp

# Skeleton: IRHaierAC::stateReset (memset 0, so no stale bytes) with the
# fields the device always writes (Command, Temp, Fan) and the sum cleared:
# Prefix kHaierAcPrefix, the constant "unknown" bit (byte 2 bit 5) and
# OffHours 12 stay.
HAIER_AC_LAYOUT = Layout(
    bytes.fromhex("a50020000c00000000"),
    {
        "command": Field.at(1, 0, 4, values=HAIER_AC_COMMAND),
        "temperature": Field.at(  # whole °C, minus kHaierAcMinTemp
            1,
            4,
            4,
            values={
                t: t - HAIER_AC_MIN_TEMP
                for t in range(HAIER_AC_MIN_TEMP, HAIER_AC_MAX_TEMP + 1)
            },
        ),
        "curr_hours": Field.at(2, 0, 5),
        "swing_v": Field.at(2, 6, 2, values=HAIER_AC_SWING_V),
        "curr_mins": Field.at(3, 0, 6),
        "off_timer": Field.at(3, 6, 1),
        "on_timer": Field.at(3, 7, 1),
        "off_hours": Field.at(4, 0, 5),
        "health": Field.at(4, 5, 1),
        "off_mins": Field.at(5, 0, 6),
        "fan": Field.at(5, 6, 2, values=HAIER_AC_FAN),
        "on_hours": Field.at(6, 0, 5),
        "mode": Field.at(6, 5, 3, values=HAIER_AC_MODE),
        "on_mins": Field.at(7, 0, 6),
        "sleep": Field.at(7, 6, 1),  # kHaierAcSleepBit
    },
    checksum=Sum8(0, 8, 8),  # IRHaierAC::checksum: sumBytes of bytes 0-7
)


class HaierAcDevice(Device):
    """Haier HSU07-HEA03: a full-state frame that also names a button
    (Command), and ``previous`` is ignored.

    The C path always sends kHaierAcCmdOn or kHaierAcCmdOff: IRac::haier ends
    with setCommand(on ? On : Off), overwriting the Mode/TempUp/TempDown/Fan/
    Swing/Health/Sleep commands its earlier setters wrote, and
    IRac::handleToggles has no HAIER_AC case. So C never picks the button
    from a previous state, and neither does the port. The real remote names
    the key actually pressed (the issue #404/#668 captures carry TempUp,
    TempDown and Health); the port does not invent that rule.
    """

    PROTOCOL = HAIER_AC
    LAYOUTS = (HAIER_AC_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "heat", "fan"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
        ),
        swing_v=Choice(
            ("off", "1", "2"), {"off": "off", "1": "auto high", "2": "auto low"}
        ),
        features={
            "purifier": Choice((False, True), {False: "off", True: "on"}),
            "sleep": Choice((False, True), {False: "off", True: "on"}),
        },
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to kHaierAcAuto).
        mode = target.mode if target.power else "auto"
        temperature = min(
            max(int(target.temperature), HAIER_AC_MIN_TEMP), HAIER_AC_MAX_TEMP
        )
        data = HAIER_AC_LAYOUT.build(
            command="on" if target.power else "off",
            temperature=temperature,
            swing_v=target.swing_v,
            health=target.features.get("purifier", False),  # IRac's filter
            fan=target.fan,
            mode=mode,
            # IRac::haier: setSleep(sleep >= 0). The old glue never passed
            # sleep; the port sends the documented bit (see the tests).
            sleep=target.features.get("sleep", False),
        )
        return [Frame("main", bytes(data))]


HAIER_AC_MODELS = ("HSU07-HEA03 remote", "generic")


DEVICES.update({m: HaierAcDevice for m in HAIER_AC_MODELS})


# ------------------------------------------------------------- Haier176
# Layout from IRremoteESP8266's HaierAc176Protocol (ir_Haier.h): 22 bytes,
# each sent MSB first (sendHaierAC: sendGeneric with MSBfirst), in one burst.
# The message opens with a kHaierAcHdr mark and space, then the
# kHaierAcHdr/kHaierAcHdrGap header; bits kHaierAcBitMark/ZeroSpace/OneSpace,
# closed by kHaierAcMinGap; carrier 38 kHz. Bytes 0-13 are the YRW02 section
# (checksum Sum, byte 13), bytes 14-21 the 176-only section (Sum2, byte 21).

HAIER176 = Protocol(
    "haier176",
    {
        "main": Section(
            PulseDistance(520, 650, 1650),  # kHaierAcBitMark/ZeroSpace/OneSpace
            header=(3000, 3000, 3000, 4300),  # kHaierAcHdr x3, kHaierAcHdrGap
            footer=(520,),
            gap=150000,  # kHaierAcMinGap
            lsb_first=False,
        )
    },
    carrier=38000,
)


@dataclass(frozen=True)
class Haier176Checksum:
    """IRHaierAC176::checksum: two byte sums, one per section.

    Sum (byte 13) = sumBytes(raw[0:13]); Sum2 (byte 21) = sumBytes(raw[14:21]).
    """

    parts: tuple = (Sum8(0, 13, 13), Sum8(14, 21, 21))

    def positions(self):
        return {p.at for p in self.parts}

    def apply(self, data):
        for p in self.parts:
            p.apply(data)

    def check(self, data):
        return all(p.check(data) for p in self.parts)


HAIER176_MODEL = {"A": 0xA6, "B": 0x59}  # kHaierAcYrw02ModelA/B
HAIER176_BUTTON = {  # kHaierAcYrw02Button*
    "temp_up": 0b00000,
    "temp_down": 0b00001,
    "swing_v": 0b00010,
    "swing_h": 0b00011,
    "fan": 0b00100,
    "power": 0b00101,
    "mode": 0b00110,
    "health": 0b00111,
    "turbo": 0b01000,
    "sleep": 0b01011,
    "timer": 0b10000,
    "lock": 0b10100,
    "cfab": 0b11010,
}
HAIER176_MODE = {  # kHaierAcYrw02*
    "auto": 0b000,
    "cool": 0b001,
    "dry": 0b010,
    "heat": 0b100,
    "fan": 0b110,
}
HAIER176_FAN = {  # canonical fan -> kHaierAcYrw02Fan*
    "auto": 0b101,  # FanAuto
    "1": 0b011,  # low: FanLow
    "2": 0b010,  # medium: FanMed
    "3": 0b001,  # high: FanHigh
}
HAIER176_SWING_V = {  # canonical swing -> kHaierAcYrw02SwingV*, top to bottom
    "off": 0x0,  # SwingVOff
    "auto": 0xC,  # SwingVAuto (airflow)
    "1": 0x1,  # ceiling: SwingVTop
    "2": 0x2,  # 45°: SwingVMiddle (not available in heat mode)
    "3": 0xA,  # 30°: SwingVDown
    "4": 0x3,  # 0°: SwingVBottom (only available in heat mode)
}
HAIER176_SWING_H = {  # canonical position -> kHaierAcYrw02SwingH*
    "auto": 0x7,  # SwingHAuto
    "1": 0x3,  # far left: SwingHLeftMax
    "2": 0x4,  # left: SwingHLeft
    "3": 0x0,  # middle: SwingHMiddle
    "4": 0x5,  # right: SwingHRight
    "5": 0x6,  # far right: SwingHRightMax
}
HAIER176_MIN_TEMP, HAIER176_MAX_TEMP = 16, 30  # kHaierAcYrw02Min/MaxTempC

# Skeleton: IRHaierAC176::stateReset (all zero, then Prefix2 = kHaierAc176Prefix)
# with every written field cleared. Timers, Lock and the unnamed bits stay 0:
# stateReset zeroes the whole state, so there is no stale memory.
HAIER176_LAYOUT = Layout(
    bytes(14) + bytes([0xB7]) + bytes(7),
    {
        "model": Field.at(0, 0, 8, values=HAIER176_MODEL),
        "swing_v": Field.at(1, 0, 4, values=HAIER176_SWING_V),
        "temperature": Field.at(  # Temp: celsius - kHaierAcYrw02MinTempC
            1,
            4,
            4,
            values={
                t: t - HAIER176_MIN_TEMP
                for t in range(HAIER176_MIN_TEMP, HAIER176_MAX_TEMP + 1)
            },
        ),
        "swing_h": Field.at(2, 5, 3, values=HAIER176_SWING_H),
        "health": Field.at(3, 1, 1),
        "timer_mode": Field.at(3, 5, 3),
        "power": Field.at(4, 6, 1),
        "off_timer_hrs": Field.at(5, 0, 5),
        "fan": Field.at(5, 5, 3, values=HAIER176_FAN),
        "off_timer_mins": Field.at(6, 0, 6),
        "turbo": Field.at(6, 6, 1),
        "quiet": Field.at(6, 7, 1),
        "on_timer_hrs": Field.at(7, 0, 5),
        "mode": Field.at(7, 5, 3, values=HAIER176_MODE),
        "on_timer_mins": Field.at(8, 0, 6),
        "sleep": Field.at(8, 7, 1),
        "extra_degree_f": Field.at(10, 0, 1),
        "use_fahrenheit": Field.at(10, 5, 1),
        "button": Field.at(12, 0, 5, values=HAIER176_BUTTON),
        "lock": Field.at(12, 5, 1),
        "prefix2": Field.at(14, 0, 8),  # kHaierAc176Prefix
        # Fan2: 0 for auto (kHaierAcYrw02FanAuto), else the Fan code.
        "fan2": Field.at(16, 6, 2),
    },
    checksum=Haier176Checksum(),
)


class Haier176Device(Device):
    """Haier 176-bit (V9014557 remote, variants A and B): full state.

    The variant ("A" or "B", haier_ac176_remote_model_t V9014557_A/B) comes
    from the model (HAIER176_MODELS) unless given, so the registry's
    ``cls(brand, model)`` call picks it; unknown models get A, as
    IRHaierAC176::setModel does.

    ``previous`` is ignored. The frame carries every setting as state; the
    only "which key" field, Button (byte 12), is kHaierAcYrw02ButtonPower in
    every C message: IRac::haier176 calls setPower last, and each setter
    overwrites Button. IRac::handleToggles has no Haier case and
    IRac::haier176 takes no previous state, so the C path never uses one.
    """

    PROTOCOL = HAIER176
    LAYOUTS = (HAIER176_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "heat", "fan"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
        ),
        swing_v=Choice(
            ("off", "auto", "1", "2", "3", "4"),
            {
                "off": "off",
                "auto": "auto",
                "1": "ceiling",
                "2": "45°",
                "3": "30°",
                "4": "0°",
            },
        ),
        swing_h=Choice(
            ("auto", "1", "2", "3", "4", "5"),
            {
                "auto": "auto",
                "1": "far left",
                "2": "left",
                "3": "middle",
                "4": "right",
                "5": "far right",
            },
        ),
        features={
            "purifier": Choice((False, True), {False: "off", True: "on"}),
            "sleep": Choice((False, True), {False: "off", True: "on"}),
            "powerful": Choice((False, True), {False: "off", True: "on"}),
            "quiet": Choice((False, True), {False: "off", True: "on"}),
        },
    )

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        self.variant = variant or HAIER176_MODELS.get(model, "A")
        if self.variant not in HAIER176_MODEL:
            raise ValueError(f"unknown Haier176 variant {self.variant!r}")

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to its default, auto).
        mode = target.mode if target.power else "auto"
        # setTurbo/setQuiet only act in cool and heat (setMode clears both in
        # the other modes); IRac calls setQuiet then setTurbo, and turbo on
        # clears quiet.
        boost = mode in ("cool", "heat")
        turbo = boost and target.features["powerful"]
        quiet = boost and target.features["quiet"] and not turbo
        # setSwingV (after setMode): heat has no Middle, it uses Bottom;
        # Bottom only exists in heat, the other modes use Middle.
        swing_v = target.swing_v
        if mode == "heat" and swing_v == "2":
            swing_v = "4"
        elif mode != "heat" and swing_v == "4":
            swing_v = "2"
        fan = HAIER176_FAN[target.fan]
        data = HAIER176_LAYOUT.build(
            model=self.variant,
            swing_v=swing_v,
            temperature=target.temperature,
            swing_h=target.swing_h,
            health=target.features["purifier"],  # setHealth(filter)
            power=target.power,
            fan=target.fan,
            fan2=0 if fan == HAIER176_FAN["auto"] else fan,
            turbo=turbo,
            quiet=quiet,
            mode=mode,
            # The documented Sleep bit. The C path never sets it: the old
            # glue's key map has no "sleep" (declared as a Defect).
            sleep=target.features["sleep"],
            # IRac::haier176 calls setPower last: Button is always Power.
            button="power",
            prefix2=0xB7,  # kHaierAc176Prefix
        )
        return [Frame("main", bytes(data))]


HAIER176_MODELS = {  # model -> remote variant (haier_ac176_remote_model_t)
    "V9014557 M47 8D remote": "A",
    "Daichi D-H": "A",
    "generic 176 code a": "A",
    "generic 176 code b": "B",
}


DEVICES.update({m: Haier176Device for m in HAIER176_MODELS})


# ------------------------------------------------------------ HaierYrw02
# Layout from IRremoteESP8266's HaierAc176Protocol (ir_Haier.h): the YR-W02
# message is its first 14 bytes (kHaierACYRW02StateLength; IRHaierACYRW02
# derives from IRHaierAC176), each sent MSB first (sendHaierAC: sendGeneric
# with MSBfirst). sendHaierAC opens with a kHaierAcHdr mark and space before
# sendGeneric's kHaierAcHdr/kHaierAcHdrGap header; bits kHaierAcBitMark/
# ZeroSpace/OneSpace, gap kHaierAcMinGap, 38 kHz, no repeat
# (kHaierAcYrw02DefaultRepeat = kNoRepeat).

HAIER_YRW02 = Protocol(
    "haier_yrw02",
    {
        "main": Section(
            PulseDistance(520, 650, 1650),
            header=(3000, 3000, 3000, 4300),
            footer=(520,),
            gap=150000,
            lsb_first=False,
        )
    },
    carrier=38000,
)

HAIER_YRW02_BUTTON = {  # kHaierAcYrw02Button*
    "temp_up": 0b00000,
    "temp_down": 0b00001,
    "swing_v": 0b00010,
    "swing_h": 0b00011,
    "fan": 0b00100,
    "power": 0b00101,
    "mode": 0b00110,
    "health": 0b00111,
    "turbo": 0b01000,
    "sleep": 0b01011,
    "timer": 0b10000,
    "lock": 0b10100,
    "cfab": 0b11010,
}
HAIER_YRW02_SWING_V = {  # kHaierAcYrw02SwingV*
    "off": 0x0,
    "top": 0x1,
    "middle": 0x2,  # not available in heat mode
    "bottom": 0x3,  # only available in heat mode
    "down": 0xA,
    "auto": 0xC,
}
# Canonical swing_v -> documented position, from the top down (Top, Middle,
# Down, Bottom: IRHaierAC176::toCommonSwingV's Highest, Middle, Low, Lowest).
HAIER_YRW02_SWING_V_POSITION = {
    "off": "off",
    "auto": "auto",
    "1": "top",
    "2": "middle",
    "3": "down",
    "4": "bottom",
}
HAIER_YRW02_SWING_H = {  # kHaierAcYrw02SwingH*
    "middle": 0x0,
    "left_max": 0x3,
    "left": 0x4,
    "right": 0x5,
    "right_max": 0x6,
    "auto": 0x7,
}
HAIER_YRW02_SWING_H_POSITION = {  # canonical swing_h -> position, as convertSwingH
    "auto": "auto",
    "1": "left_max",
    "2": "left",
    "3": "middle",
    "4": "right",
    "5": "right_max",
}
HAIER_YRW02_MIN_TEMP, HAIER_YRW02_MAX_TEMP = 16, 30  # kHaierAcYrw02Min/MaxTempC

HAIER_YRW02_LAYOUT = Layout(
    # IRHaierAC176::stateReset clears the whole state (memset) and every
    # byte it then sets is a field below: no stale padding.
    bytes(14),
    {
        "model": Field.at(0, 0, 8, values={"A": 0xA6, "B": 0x59}),  # Model A/B
        "swing_v": Field.at(1, 0, 4, values=HAIER_YRW02_SWING_V),
        "temperature": Field.at(  # celsius - kHaierAcYrw02MinTempC
            1,
            4,
            4,
            values={
                t: t - HAIER_YRW02_MIN_TEMP
                for t in range(HAIER_YRW02_MIN_TEMP, HAIER_YRW02_MAX_TEMP + 1)
            },
        ),
        "swing_h": Field.at(2, 5, 3, values=HAIER_YRW02_SWING_H),
        "health": Field.at(3, 1, 1),
        "timer_mode": Field.at(3, 5, 3),  # kHaierAcYrw02*Timer*: never set
        "power": Field.at(4, 6, 1),
        "off_timer_hrs": Field.at(5, 0, 5),
        "fan": Field.at(  # kHaierAcYrw02Fan*, as IRHaierAC176::convertFan
            5, 5, 3, values={"auto": 0b101, "1": 0b011, "2": 0b010, "3": 0b001}
        ),
        "off_timer_mins": Field.at(6, 0, 6),
        "turbo": Field.at(6, 6, 1),
        "quiet": Field.at(6, 7, 1),
        "on_timer_hrs": Field.at(7, 0, 5),
        "mode": Field.at(  # kHaierAcYrw02{Auto,Cool,Dry,Heat,Fan}
            7,
            5,
            3,
            values={
                "auto": 0b000,
                "cool": 0b001,
                "dry": 0b010,
                "heat": 0b100,
                "fan": 0b110,
            },
        ),
        "on_timer_mins": Field.at(8, 0, 6),
        "sleep": Field.at(8, 7, 1),
        "extra_degree_f": Field.at(10, 0, 1),
        "use_fahrenheit": Field.at(10, 5, 1),
        "button": Field.at(12, 0, 5, values=HAIER_YRW02_BUTTON),
        "lock": Field.at(12, 5, 1),
    },
    checksum=Sum8(0, 13, 13),  # IRHaierAC176::checksum: Sum
)


class HaierYrw02Device(Device):
    """Haier YR-W02 (HAIER_AC_YRW02, remote variants A and B): full state in
    one 14-byte frame.

    The variant ("A" or "B", kHaierAcYrw02ModelA/B in byte 0) comes from the
    model (HAIER_YRW02_MODELS) unless given, so the registry's
    ``cls(brand, model)`` call picks it; unknown models get A, as
    IRHaierAC176::setModel does.

    The Button field (the key the remote reports as pressed) is always
    kHaierAcYrw02ButtonPower, as the C path sends: IRac::haierYrwo2 calls
    setPower last, on a fresh object, whatever changed. IRac::sendAc uses no
    previous state for HAIER_AC_YRW02 and IRac::handleToggles has no case
    for it, and the struct has no toggle bits (power, swing and the features
    are states), so ``previous`` is ignored, with or without it.
    """

    PROTOCOL = HAIER_YRW02
    LAYOUTS = (HAIER_YRW02_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "heat", "fan"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
        ),
        swing_v=Choice(
            ("off", "auto", "1", "2", "3", "4"),
            {
                "off": "off",
                "auto": "auto",
                "1": "ceiling",
                "2": "45°",
                "3": "30°",
                "4": "0°",
            },
        ),
        swing_h=Choice(
            ("auto", "1", "2", "3", "4", "5"),
            {
                "auto": "auto",
                "1": "far left",
                "2": "left",
                "3": "middle",
                "4": "right",
                "5": "far right",
            },
        ),
        features={
            "purifier": Choice((False, True), {False: "off", True: "on"}),
            "sleep": Choice((False, True), {False: "off", True: "on"}),
            "powerful": Choice((False, True), {False: "off", True: "on"}),
            "quiet": Choice((False, True), {False: "off", True: "on"}),
        },
    )

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        self.variant = variant or HAIER_YRW02_MODELS.get(model, "A")
        if self.variant not in ("A", "B"):
            raise ValueError(f"unknown Haier YR-W02 variant {self.variant!r}")

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to auto).
        mode = target.mode if target.power else "auto"
        swing_v = HAIER_YRW02_SWING_V_POSITION[target.swing_v]
        # IRHaierAC176::setSwingV: heat has no Middle (Bottom instead), and
        # Bottom exists in heat only (Middle instead).
        if swing_v == "middle" and mode == "heat":
            swing_v = "bottom"
        elif swing_v == "bottom" and mode != "heat":
            swing_v = "middle"
        # setQuiet then setTurbo, both only in cool and heat (setMode clears
        # them elsewhere); turbo on clears quiet.
        features = target.features
        boost = mode in ("cool", "heat")
        turbo = boost and features["powerful"]
        quiet = boost and features["quiet"] and not turbo
        data = HAIER_YRW02_LAYOUT.build(
            model=self.variant,
            swing_v=swing_v,
            temperature=int(target.temperature),
            swing_h=HAIER_YRW02_SWING_H_POSITION[target.swing_h],
            health=features["purifier"],
            power=target.power,
            fan=target.fan,
            turbo=turbo,
            quiet=quiet,
            mode=mode,
            sleep=features["sleep"],
            button="power",
        )
        return [Frame("main", bytes(data))]


HAIER_YRW02_MODELS = {  # model -> remote variant (haier_ac176_remote_model_t)
    "YR-W02 remote": "A",
    "HSU-09HMC203": "A",
    "YR-W02 Code A": "A",
    "YR-W02 Code B": "B",
}


DEVICES.update({m: HaierYrw02Device for m in HAIER_YRW02_MODELS})


# --------------------------------------------------------------- Haier160
# Layout from IRremoteESP8266's HaierAc160Protocol (ir_Haier.h): 20 bytes in
# two checksummed sections, bytes 0-13 (Sum at byte 13) and 14-19 (Sum2 at
# byte 19). Sent by sendHaierAC as one frame, MSB first, after a lone
# kHaierAcHdr mark and space, the kHaierAcHdr/kHaierAcHdrGap header, and
# closed by kHaierAcMinGap. IRHaierAC160::stateReset zeroes every byte, so
# no bit comes from stale memory.

HAIER160 = Protocol(
    "haier160",
    {
        "main": Section(
            PulseDistance(520, 650, 1650),  # kHaierAcBitMark/ZeroSpace/OneSpace
            # mark(kHaierAcHdr), space(kHaierAcHdr), then sendGeneric's
            # kHaierAcHdr/kHaierAcHdrGap header.
            header=(3000, 3000, 3000, 4300),
            footer=(520,),
            gap=150000,  # kHaierAcMinGap
            lsb_first=False,
        )
    },
    carrier=38000,
)


@dataclass(frozen=True)
class Haier160Checksum:
    """IRHaierAC160::checksum: Sum = sumBytes(raw, 13) at byte 13, and
    Sum2 = sumBytes(raw + 14, 5) at byte 19."""

    parts: tuple = (Sum8(0, 13, 13), Sum8(14, 19, 19))

    def positions(self):
        return set().union(*(p.positions() for p in self.parts))

    def apply(self, data):
        for part in self.parts:
            part.apply(data)

    def check(self, data):
        return all(part.check(data) for part in self.parts)


HAIER160_BUTTON = {  # kHaierAcYrw02Button* / kHaierAc160Button*
    "temp_up": 0b00000,
    "temp_down": 0b00001,
    "swing_v": 0b00010,
    "swing_h": 0b00011,
    "fan": 0b00100,
    "power": 0b00101,
    "mode": 0b00110,
    "health": 0b00111,
    "turbo": 0b01000,
    "sleep": 0b01011,
    "timer": 0b10000,
    "lock": 0b10100,
    "light": 0b10101,
    "aux_heating": 0b10110,
    "clean": 0b11001,
    "cfab": 0b11010,
}
HAIER160_FAN = {  # canonical fan -> kHaierAcYrw02Fan*, as convertFan
    "auto": 0b101,
    "1": 0b011,  # low
    "2": 0b010,  # medium
    "3": 0b001,  # high
}
HAIER160_SWING_V = {  # canonical swing -> kHaierAc160SwingV*, as convertSwingV
    "off": 0b0000,
    "auto": 0b1100,  # airflow
    "1": 0b0001,  # ceiling (kHighest): kHaierAc160SwingVTop
    "2": 0b0100,  # 90° (kHigh): kHaierAc160SwingVHigh
    "3": 0b0110,  # 45° (kMiddle): kHaierAc160SwingVMiddle
    "4": 0b1000,  # 30° (kLow): kHaierAc160SwingVLow
    "5": 0b0011,  # 0° (kLowest): kHaierAc160SwingVLowest
}
HAIER160_MIN_TEMP, HAIER160_MAX_TEMP = 16, 30  # kHaierAcYrw02Min/MaxTempC

# Skeleton: IRHaierAC160::stateReset (Model kHaierAcYrw02ModelA, Prefix
# kHaierAc160Prefix) with every field cleared; the device writes them all.
HAIER160_LAYOUT = Layout(
    bytes.fromhex("a6000000000000000000000000" "00b50000000000"),
    {
        "swing_v": Field.at(1, 0, 4, values=HAIER160_SWING_V),
        "temperature": Field.at(  # whole °C, stored as degrees - 16
            1,
            4,
            4,
            values={
                t: t - HAIER160_MIN_TEMP
                for t in range(HAIER160_MIN_TEMP, HAIER160_MAX_TEMP + 1)
            },
        ),
        "swing_h": Field.at(2, 5, 3),  # IRHaierAC160 has no setter
        "health": Field.at(3, 1, 1),
        "timer_mode": Field.at(3, 5, 3),
        "power": Field.at(4, 6, 1),
        "aux_heating": Field.at(4, 7, 1),
        "off_timer_hrs": Field.at(5, 0, 5),
        "fan": Field.at(5, 5, 3, values=HAIER160_FAN),
        "off_timer_mins": Field.at(6, 0, 6),
        "turbo": Field.at(6, 6, 1),
        "quiet": Field.at(6, 7, 1),
        "on_timer_hrs": Field.at(7, 0, 5),
        "mode": Field.at(
            7, 5, 3, values={"auto": 0, "cool": 1, "dry": 2, "heat": 4, "fan": 6}
        ),
        "on_timer_mins": Field.at(8, 0, 6),
        "sleep": Field.at(8, 7, 1),
        "extra_degree_f": Field.at(10, 0, 1),
        "clean": Field.at(10, 4, 1),
        "use_fahrenheit": Field.at(10, 5, 1),
        "button": Field.at(12, 0, 5, values=HAIER160_BUTTON),
        "lock": Field.at(12, 5, 1),
        "clean2": Field.at(15, 6, 1),
        # setFan: Fan2 is 0 for auto, else the Fan code.
        "fan2": Field.at(16, 5, 3, values={**HAIER160_FAN, "auto": 0}),
    },
    checksum=Haier160Checksum(),
)


class Haier160Device(Device):
    """Haier 160-bit (KFR-26GW/83@UI-Ge): full state, plus a light button.

    As IRac::haier160 sends it: an off message carries mode auto
    (convertMode maps IRac's "off" to kHaierAcYrw02Auto), so it also clears
    turbo, quiet and AuxHeating; setMode sets AuxHeating in heat mode only;
    turbo and quiet are kept in cool and heat only, and turbo wins when both
    are asked (setQuiet, then setTurbo(true) clears Quiet); cleaning sets
    Clean and Clean2; purifier sets Health; the temperature is Celsius.

    The Button field (byte 12) is whatever setter ran last. IRac::haier160
    ends with setPower (kHaierAcYrw02ButtonPower), then setLightToggle(light
    ^ prevlight), which presses kHaierAc160ButtonLight when the light changes.
    IRac::sendAc computes prevlight itself (not in handleToggles): the
    previous state's light, and a fresh IRac's previous state has light off.
    So with ``previous`` the light button is pressed only when the light
    changes, as a persistent IRac does; with ``previous=None`` it is pressed
    when the light is on, as a fresh IRac does. The port matches C in both.

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_haier160_device.py):
    - sleep: the old glue never passes sleep, so setSleep(sleep >= 0) always
      clears Sleep; the port sets it.
    """

    PROTOCOL = HAIER160
    LAYOUTS = (HAIER160_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "heat", "fan"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
        ),
        swing_v=Choice(
            ("off", "auto", "1", "2", "3", "4", "5"),
            {
                "off": "off",
                "auto": "auto",
                "1": "ceiling",
                "2": "90°",
                "3": "45°",
                "4": "30°",
                "5": "0°",
            },
        ),
        features={
            name: Choice((False, True), {False: "off", True: "on"})
            for name in ("purifier", "sleep", "powerful", "quiet", "cleaning", "light")
        },
    )

    def frames(self, previous, target, actions):
        f = target.features
        mode = target.mode if target.power else "auto"
        # setTurbo/setQuiet only act in cool and heat; setMode(auto/dry/fan)
        # clears both.
        boost = mode in ("cool", "heat")
        turbo = boost and f["powerful"]
        quiet = boost and f["quiet"] and not f["powerful"]
        if previous is None:
            light = f["light"]
        else:
            light = f["light"] != previous.features["light"]
        data = HAIER160_LAYOUT.build(
            swing_v=target.swing_v,
            temperature=int(target.temperature),
            health=f["purifier"],
            power=target.power,
            aux_heating=mode == "heat",
            fan=target.fan,
            turbo=turbo,
            quiet=quiet,
            mode=mode,
            sleep=f["sleep"],
            clean=f["cleaning"],
            clean2=f["cleaning"],
            button="light" if light else "power",
            fan2=target.fan,
        )
        return [Frame("main", bytes(data))]


HAIER160_MODELS = ("KFR-26GW/83@UI-Ge", "generic 160")


DEVICES.update({m: Haier160Device for m in HAIER160_MODELS})


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "HSU07-HEA03 remote": Haier,
        "YR-W02 remote": HaierYRW02A,
        "HSU-09HMC203": HaierYRW02A,
        "V9014557 M47 8D remote": Haier176A,
        "Daichi D-H": Haier176A,
        "KFR-26GW/83@UI-Ge": Haier160,
        "generic": Haier,
        "YR-W02 Code A": HaierYRW02A,
        "YR-W02 Code B": HaierYRW02B,
        "generic 176 code a": Haier176A,
        "generic 176 code b": Haier176B,
        "generic 160": Haier160,
    }

    def __init__(self):
        self.brand = "haier"
