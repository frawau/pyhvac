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


from dataclasses import replace

from ..device import Device
from ..fields import Copy, Field, Layout, Sum8
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_5, ON_OFF, SWING_H_6, SWING_V_ANGLES, SWING_V_AUTO_ANGLES
from ..state import Capabilities, Choice, TemperatureRange

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
    # decodeMitsubishiAC: _tolerance + kMitsubishiAcExtraTolerance (30 %),
    # mark excess 0.
    tolerance=0.30,
    mark_excess=0,
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

    Economy is the Ecocool bit (Mitsubishi144Protocol byte 14 bit 5,
    IRMitsubishiAC::setEcocool; toString reports it as "Econo"). IRac never
    sets it, so the oracle fixtures only hold it clear. Quiet is not offered:
    it has no bit of its own (IRac's quiet sends kMitsubishiAcFanSilent,
    which fan "1" already sends).
    """

    PROTOCOL = MITSUBISHI_AC
    LAYOUTS = (MITSUBISHI_AC_LAYOUT, MITSUBISHI_AC_LAYOUT)
    capabilities = Capabilities(
        modes=("auto", "cool", "fan", "dry", "heat"),
        temperature=TemperatureRange(16.0, 31.0, decimals=(0, 5)),
        fan=FAN_5,
        swing_v=SWING_V_ANGLES,
        swing_h=SWING_H_6,
        features={"economy": ON_OFF},
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
            ecocool=target.features.get("economy", False),
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


# -------------------------------------------------------- Mitsubishi136
# Layout from IRremoteESP8266's Mitsubishi136Protocol (ir_Mitsubishi.h):
# 17 bytes sent LSB first in one frame, no repeat (sendMitsubishi136:
# kMitsubishi136MinRepeat = kNoRepeat). Bytes 11-16 are the complements of
# bytes 5-10 (IRMitsubishi136::checksum): the inverted section.

MITSUBISHI136 = Protocol(
    "mitsubishi136",
    {
        "main": Section(
            PulseDistance(467, 351, 1137),  # kMitsubishi136BitMark/Zero/OneSpace
            header=(3324, 1474),  # kMitsubishi136HdrMark/HdrSpace
            footer=(467,),
            gap=100000,  # kMitsubishi136Gap (kDefaultMessageGap)
        ),
    },
    carrier=38000,  # sendMitsubishi136: 38 kHz
    # decodeMitsubishi136: _tolerance (25 %), mark excess 0.
    mark_excess=0,
)


MITSUBISHI136_MODE = {  # kMitsubishi136*, as IRMitsubishi136::convertMode
    "fan": 0b000,  # kMitsubishi136Fan
    "cool": 0b001,  # kMitsubishi136Cool
    "heat": 0b010,  # kMitsubishi136Heat
    "auto": 0b011,  # kMitsubishi136Auto
    "dry": 0b101,  # kMitsubishi136Dry
}
MITSUBISHI136_FAN = {  # canonical fan -> kMitsubishi136Fan*
    # Not offered (no code of their own): auto is convertFan's default,
    # kMitsubishi136FanMed; "5" (kMax) is kMitsubishi136FanMax, as "4".
    "auto": 0b10,
    "1": 0b00,  # lowest: kMitsubishi136FanMin (see Mitsubishi136Device)
    "2": 0b01,  # kMitsubishi136FanLow
    "3": 0b10,  # kMitsubishi136FanMed
    "4": 0b11,  # highest: kMitsubishi136FanMax
    "5": 0b11,
}
MITSUBISHI136_FAN_QUIET = 0b00  # kMitsubishi136FanQuiet (= FanMin)
MITSUBISHI136_SWING_V = {  # canonical swing -> kMitsubishi136SwingV*
    # Not offered: convertSwingV(kOff) is kMitsubishi136SwingVAuto (no off).
    "off": 0b1100,
    "auto": 0b1100,  # kMitsubishi136SwingVAuto
    "1": 0b0011,  # 90°: kMitsubishi136SwingVHighest (topmost, counting down)
    "2": 0b0010,  # 60°: kMitsubishi136SwingVHigh
    "3": 0b0001,  # 30°: kMitsubishi136SwingVLow
    "4": 0b0000,  # 0°: kMitsubishi136SwingVLowest
}
MITSUBISHI136_MIN_TEMP, MITSUBISHI136_MAX_TEMP = 17, 30  # kMitsubishi136Min/MaxTemp
MITSUBISHI136_TEMP_OFFSET = 16  # setTemp stores degrees - kMitsubishiAcMinTemp

# Skeleton: IRMitsubishi136::stateReset (kReset, zero-padded to 17 bytes;
# memcpy writes every byte, so nothing comes from stale memory) with the
# fields and the inverted section cleared. Byte 7 bit 0 stays set, as in
# kReset and the PEAD-RP71JAA capture of ir_Mitsubishi_test.cpp.
MITSUBISHI136_LAYOUT = Layout(
    bytes.fromhex("23cb262100000001040000000000000000"),
    {
        "power": Field.at(5, 6, 1),
        "mode": Field.at(6, 0, 3, values=MITSUBISHI136_MODE),
        "temperature": Field.at(6, 4, 4),  # °C - 16 (kMitsubishiAcMinTemp)
        "fan": Field.at(7, 1, 2),
        "swing_v": Field.at(7, 4, 4),
    },
    checksum=Copy(5, 11, 11, invert=True),  # IRMitsubishi136::checksum
)


class Mitsubishi136Device(Device):
    """Mitsubishi136 (PEAD-RP71JAA, PAR-FA32MA): a full-state protocol with
    no toggle bits, ``previous`` is ignored.

    As the C path (IRac::mitsubishi136): an off message carries mode auto
    (IRac passes mode "off", convertMode's default), the setpoint is whole
    degrees clamped to 17-30 (kMitsubishi136MinTemp/MaxTemp), and quiet
    forces kMitsubishi136FanQuiet. The protocol has no auto fan and no swing
    off, so neither is offered (C sends Med and SwingVAuto for them).

    Two documented values differ from the C output (declared Defects):
    - fan lowest sends kMitsubishi136FanMin: convertFan maps kMin there,
      but IRac's setQuiet(false) then turns it into FanLow because FanMin is
      also FanQuiet;
    - swing positions count down from kMitsubishi136SwingVHighest: the
      legacy labels 90° and 60° reach C as kHigh and kUpperMiddle, which
      convertSwingV maps to High and Auto.
    """

    PROTOCOL = MITSUBISHI136
    LAYOUTS = (MITSUBISHI136_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "fan", "dry", "heat"),
        temperature=TemperatureRange(MITSUBISHI136_MIN_TEMP, MITSUBISHI136_MAX_TEMP),
        fan=Choice(
            ("1", "2", "3", "4"),
            {"1": "lowest", "2": "low", "3": "medium", "4": "highest"},
        ),
        swing_v=Choice(
            ("auto", "1", "2", "3", "4"),
            {"auto": "auto", "1": "90°", "2": "60°", "3": "30°", "4": "0°"},
        ),
        features={"quiet": ON_OFF},
    )

    def normalise(self, state):
        # No auto fan: a fan the protocol lacks (the default "auto") is sent
        # as C sent IRac's kAuto, kMitsubishi136FanMed (canonical "3").
        if state.fan not in self.capabilities.fan.values:
            state = replace(state, fan="3")
        return super().normalise(state)

    def frames(self, previous, target, actions):
        mode = target.mode if target.power else "auto"
        degrees = min(
            max(int(target.temperature), MITSUBISHI136_MIN_TEMP),
            MITSUBISHI136_MAX_TEMP,
        )
        if target.features.get("quiet"):
            fan = MITSUBISHI136_FAN_QUIET
        else:
            fan = MITSUBISHI136_FAN[target.fan]
        data = MITSUBISHI136_LAYOUT.build(
            power=target.power,
            mode=mode,
            temperature=degrees - MITSUBISHI136_TEMP_OFFSET,
            fan=fan,
            swing_v=MITSUBISHI136_SWING_V[target.swing_v],
        )
        return [Frame("main", bytes(data))]


MITSUBISHI136_MODELS = (
    "PEAD-RP71JAA Ducted",
    "001CP T7WE10714 remote",
    "PAR-FA32MA remote",
    "generic 136",
)


# ----------------------------------------------------------- Mitsubishi112
# Layout from IRremoteESP8266's Mitsubishi112Protocol (ir_Mitsubishi.h): 14
# bytes sent LSB first in one frame (sendMitsubishi112 -> sendGeneric with
# MSBfirst false), closed by a sum of bytes 0-12 (IRMitsubishi112::checksum
# uses IRTcl112Ac::calcChecksum; byte 3 is never 0x02, so no offset).

MITSUBISHI112 = Protocol(
    "mitsubishi112",
    {
        "main": Section(
            PulseDistance(450, 385, 1250),  # kMitsubishi112BitMark/Zero/OneSpace
            header=(3450, 1696),  # kMitsubishi112HdrMark/HdrSpace
            footer=(450,),
            gap=100000,  # kMitsubishi112Gap (kDefaultMessageGap)
        ),
    },
    carrier=38000,  # sendGeneric(..., 38, ...)
    # decodeMitsubishi112: _tolerance + kTcl112AcTolerance (30 %), mark
    # excess 0 (the header mark with kMitsubishi112HdrMarkTolerance).
    tolerance=0.30,
    mark_excess=0,
)

MITSUBISHI112_MODE = {  # kMitsubishi112*, as convertMode (no fan-only mode)
    "auto": 0b111,
    "cool": 0b011,
    "heat": 0b001,
    "dry": 0b010,
}
MITSUBISHI112_FAN = {  # canonical fan -> kMitsubishi112Fan*, as convertFan
    "1": 0b010,  # lowest: kMitsubishi112FanMin (= kMitsubishi112FanQuiet)
    "2": 0b011,  # kMitsubishi112FanLow
    "3": 0b101,  # kMitsubishi112FanMed
    "4": 0b000,  # highest: kMitsubishi112FanMax
}
MITSUBISHI112_SWING_V = {  # kMitsubishi112SwingV*; the header has no "off"
    "auto": 0b111,
    # Not offered: the C path's convertSwingV maps kOff to auto.
    "off": 0b111,
    "1": 0b001,  # highest
    "2": 0b010,  # high
    "3": 0b011,  # middle
    "4": 0b100,  # low
    "5": 0b101,  # lowest
}
MITSUBISHI112_SWING_H = {  # kMitsubishi112SwingH*, as convertSwingH
    "auto": 0b1100,
    "1": 0b0001,  # far left: kMitsubishi112SwingHLeftMax
    "2": 0b0010,  # left
    "3": 0b0011,  # middle
    "4": 0b0100,  # right
    "5": 0b0101,  # far right: kMitsubishi112SwingHRightMax
    "6": 0b1000,  # wide
}
MITSUBISHI112_MAX_TEMP = 31  # kMitsubishiAcMaxTemp: Temp holds 31 - setpoint
MITSUBISHI112_RANGE = (16, 31)  # kMitsubishi112MinTemp, kMitsubishi112MaxTemp

# Skeleton: IRMitsubishi112::stateReset (kReset, byte 13 zero-initialised),
# which writes every byte, so no padding bit comes from stale memory.
MITSUBISHI112_LAYOUT = Layout(
    bytes.fromhex("23cb260100240308100000003000"),
    {
        "power": Field.at(5, 2, 1),
        "mode": Field.at(6, 0, 3, values=MITSUBISHI112_MODE),
        "temperature": Field.at(7, 0, 4),  # 31 - whole °C
        "fan": Field.at(8, 0, 3, values=MITSUBISHI112_FAN),
        "swing_v": Field.at(8, 3, 3, values=MITSUBISHI112_SWING_V),
        "swing_h": Field.at(12, 2, 4, values=MITSUBISHI112_SWING_H),
    },
    checksum=Sum8(0, 13, 13),
)


class Mitsubishi112Device(Device):
    """Mitsubishi112 (KPOA remote): a full-state protocol, ``previous`` is
    ignored (no toggle bits; IRac::handleToggles has no MITSUBISHI112 case).

    Quiet has no bit of its own: as IRMitsubishi112::setQuiet, it sends
    kMitsubishi112FanQuiet (= kMitsubishi112FanMin) whatever the fan.
    The vertical swing has no off code, so none is offered (C sends auto).
    """

    PROTOCOL = MITSUBISHI112
    LAYOUTS = (MITSUBISHI112_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "heat"),
        temperature=TemperatureRange(*MITSUBISHI112_RANGE),
        fan=Choice(
            ("1", "2", "3", "4"),
            {"1": "lowest", "2": "low", "3": "medium", "4": "highest"},
        ),
        swing_v=SWING_V_AUTO_ANGLES,
        swing_h=SWING_H_6,
        features={"quiet": ON_OFF},
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to auto) and the setpoint as given.
        # Quiet overrides the fan (setQuiet runs after setFan).
        fan = "1" if target.features["quiet"] else target.fan
        data = MITSUBISHI112_LAYOUT.build(
            power=target.power,
            mode=target.mode if target.power else "auto",
            temperature=MITSUBISHI112_MAX_TEMP - int(target.temperature),
            fan=fan,
            swing_v=target.swing_v,
            swing_h=target.swing_h,
        )
        return [Frame("main", bytes(data))]


MITSUBISHI112_MODELS = ("MSH-A24WV", "MUH-A24WV", "KPOA remote", "generic 112")


# Now the match between models and objects
