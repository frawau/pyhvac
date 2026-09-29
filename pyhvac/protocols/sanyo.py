#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Sanyo AC IR commands.
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

from ..device import Device
from ..fields import Field, Layout, NibbleSum
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_3, ON_OFF, SWING
from ..state import Capabilities, Choice, TemperatureRange

# ---------------------------------------------------------------- SanyoAc
# Layout from IRremoteESP8266's SanyoProtocol (ir_Sanyo.h): 9 bytes, one
# frame sent LSB first (sendSanyoAc -> sendGeneric with MSBfirst false, at
# kSanyoAcFreq), closed by the sum of every nibble of bytes 0-7
# (IRSanyoAc::calcChecksum: sumNibbles over length - 1 bytes).

SANYO_AC = Protocol(
    "sanyo_ac",
    {
        "main": Section(
            # kSanyoAcBitMark / ZeroSpace / OneSpace
            PulseDistance(500, 550, 1600),
            header=(8500, 4200),  # kSanyoAcHdrMark / HdrSpace
            footer=(500,),
            gap=100000,  # kSanyoAcGap (kDefaultMessageGap)
        ),
    },
    carrier=38000,  # kSanyoAcFreq
)

SANYO_AC_MODE = {  # kSanyoAc{Heat,Cool,Dry,Auto}
    "heat": 1,
    "cool": 2,
    "dry": 3,
    "auto": 4,
}
SANYO_AC_FAN = {  # canonical fan -> kSanyoAcFan*
    "auto": 0,  # kSanyoAcFanAuto
    "1": 2,  # low: kSanyoAcFanLow
    "2": 3,  # medium: kSanyoAcFanMedium
    "3": 1,  # high: kSanyoAcFanHigh
}
SANYO_AC_SWING_V = {  # canonical swing_v -> kSanyoAcSwingV*, top to bottom
    "auto": 0,  # kSanyoAcSwingVAuto
    "1": 7,  # kSanyoAcSwingVHighest
    "2": 6,  # kSanyoAcSwingVHigh
    "3": 5,  # kSanyoAcSwingVUpperMiddle
    "4": 4,  # kSanyoAcSwingVLowerMiddle
    "5": 3,  # kSanyoAcSwingVLow
    "6": 2,  # kSanyoAcSwingVLowest
}
# Six positions: the angle labels of the five-position choices do not fit,
# so the labels are the header's names.
SANYO_AC_SWING_V_CHOICE = Choice(
    tuple(SANYO_AC_SWING_V),
    {
        "auto": "auto",
        "1": "highest",
        "2": "high",
        "3": "upper middle",
        "4": "lower middle",
        "5": "low",
        "6": "lowest",
    },
)
SANYO_AC_POWER_OFF, SANYO_AC_POWER_ON = 0b01, 0b10  # kSanyoAcPowerOff / On
SANYO_AC_MIN_TEMP, SANYO_AC_MAX_TEMP = 16, 30  # kSanyoAcTempMin / Max
SANYO_AC_TEMP_DELTA = 4  # kSanyoAcTempDelta: native = degrees - 4

# Skeleton: IRSanyoAc::stateReset (kReset; memcpy writes all 9 bytes, so
# nothing comes from stale memory) with the named fields cleared. Byte 0 is
# the fixed 0x6A, byte 1 bits 5-7 stay 0b011 as in kReset and the issue
# #1211 capture (0x71).
SANYO_AC_LAYOUT = Layout(
    bytes.fromhex("6a6000000000000000"),
    {
        "temp": Field.at(1, 0, 5),  # °C - kSanyoAcTempDelta
        "sensor_temp": Field.at(2, 0, 5),  # °C - kSanyoAcTempDelta
        "sensor": Field.at(2, 5, 1),  # 0 = remote (wall), 1 = A/C (room)
        "beep": Field.at(2, 6, 1),
        "off_hour": Field.at(3, 0, 4),
        "fan": Field.at(4, 0, 2, values=SANYO_AC_FAN),
        "off_timer": Field.at(4, 2, 1),
        "mode": Field.at(4, 4, 3, values=SANYO_AC_MODE),
        "swing_v": Field.at(5, 0, 3, values=SANYO_AC_SWING_V),
        "power": Field.at(5, 6, 2),
        "sleep": Field.at(6, 3, 1),
    },
    checksum=NibbleSum(0, 8, 8),
)


class SanyoAcDevice(Device):
    """Sanyo 72-bit A/C (SAP-K121AHA, RCS-2HS4E, SAP-K242AH, RCS-2S4E): a
    full-state protocol with no toggle bits, ``previous`` is ignored.

    As the C path (IRac::sanyo, fed by the legacy glue): an off message
    carries mode auto (IRac passes mode "off", convertMode's default) and
    kSanyoAcPowerOff; the setpoint is whole degrees clamped to 16-30; the
    sensor temperature is the setpoint (IRac has no sensor reading and uses
    the desired temperature); the sensor is the A/C's own (setSensor(!iFeel),
    iFeel off); beep is off (the glue never sets it); the off timer is off.

    Vertical swing offers auto and the six kSanyoAcSwingV* positions,
    highest ("1") to lowest ("6"), LowerMiddle ("4") included.

    Two documented values differ from the C output (declared Defects):
    - swing_v "1" (the legacy 90°) and "2" (60°): the old glue maps them to
      kHigh and kUpperMiddle, which convertSwingV sends as High and Auto;
      the port sends the documented Highest and High. The legacy 45°, 30°
      and 0° are C's UpperMiddle, Low and Lowest ("3", "5", "6");
    - sleep: the old glue never passes sleep, so setSleep(sleep >= 0) never
      sets the Sleep bit; the port sets it.
    """

    PROTOCOL = SANYO_AC
    LAYOUTS = (SANYO_AC_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "heat"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=FAN_3,
        swing_v=SANYO_AC_SWING_V_CHOICE,
        features={"sleep": ON_OFF},
    )

    def frames(self, previous, target, actions):
        degrees = min(
            max(int(target.temperature), SANYO_AC_MIN_TEMP), SANYO_AC_MAX_TEMP
        )
        native = degrees - SANYO_AC_TEMP_DELTA
        data = SANYO_AC_LAYOUT.build(
            temp=native,
            sensor_temp=native,
            sensor=1,
            beep=0,
            off_hour=0,
            fan=target.fan,
            off_timer=0,
            mode=target.mode if target.power else "auto",
            swing_v=target.swing_v,
            power=SANYO_AC_POWER_ON if target.power else SANYO_AC_POWER_OFF,
            sleep=target.features["sleep"],
        )
        return [Frame("main", bytes(data))]


SANYO_AC_MODELS = (
    "SAP-K121AHA",
    "RCS-2HS4E remote",
    "SAP-K242AH",
    "RCS-2S4E remote",
    "generic",
)


# ----------------------------------------------------------------- SanyoAc88
# Layout from IRremoteESP8266's SanyoAc88Protocol (ir_Sanyo.h): 11 bytes sent
# LSB first (sendSanyoAc88: sendGeneric with MSBfirst false), no checksum.
# IRSanyoAc88::send sends the message kSanyoAc88MinRepeat + 1 = 3 times, each
# closed by kSanyoAc88BitMark and kSanyoAc88Gap, then adds a
# kDefaultMessageGap space: the wire ends on 500 µs mark + 103 675 µs space
# (as ir_Sanyo_test.cpp's SyntheticSelfDecode shows). stateReset writes every
# byte, so no bit is left to stale memory.

SANYO_AC88 = Protocol(
    "sanyo-ac88",
    {
        "main": Section(
            # kSanyoAc88BitMark / ZeroSpace / OneSpace
            PulseDistance(500, 750, 1500),
            header=(5400, 2000),  # kSanyoAc88HdrMark / HdrSpace
            footer=(500,),
            gap=3675,  # kSanyoAc88Gap
        ),
        # sendSanyoAc88: space(kDefaultMessageGap) after the last repeat.
        "end": Section(None, gap=100000),
    },
    carrier=38000,  # kSanyoAc88Freq
    # decodeSanyoAc88: _tolerance + kSanyoAc88ExtraTolerance (30 %),
    # kMarkExcess.
    tolerance=0.30,
)

SANYO_AC88_MODE = {  # kSanyoAc88{Auto,Cool,Heat,Fan}
    "auto": 0,
    "cool": 2,
    "heat": 4,
    "fan": 5,
}
SANYO_AC88_FAN = {  # canonical fan -> kSanyoAc88Fan*
    "auto": 0,  # FanAuto
    "1": 1,  # low: FanLow
    "2": 2,  # medium: FanMedium
    "3": 3,  # high: FanHigh
    # Not offered: the legacy "highest" (kMax), which convertFan also sends
    # as FanHigh; the protocol has no faster speed.
    "4": 3,
}
SANYO_AC88_SWING = {"off": 0, "swing": 1}  # SwingV

# Skeleton: IRSanyoAc88::stateReset (kReset) with Power, Mode, Fan and Temp
# cleared: bytes 0-1 0xAA 0x55, byte 7 0x01, EnableStartTimer (byte 10 bit 4)
# set, the clock (bytes 4-6) zero, as IRac never calls setClock (clock -1).
# The one real capture (ir_Sanyo_test.cpp, issue 1503) has 0x59, 0x00 and
# 0x80 in bytes 1, 7 and 10: undocumented bits, so the port follows C.
SANYO_AC88_LAYOUT = Layout(
    bytes.fromhex("aa550000000000010000" "10"),
    {
        "fan": Field.at(2, 0, 2, values=SANYO_AC88_FAN),
        "mode": Field.at(2, 4, 3, values=SANYO_AC88_MODE),
        "power": Field.at(2, 7, 1),
        "temperature": Field.at(3, 0, 5),  # whole °C, 10-30
        "filter": Field.at(3, 5, 1),
        "swing_v": Field.at(3, 6, 1, values=SANYO_AC88_SWING),
        "clock_secs": Field.at(4, 0, 8),
        "clock_mins": Field.at(5, 0, 8),
        "clock_hours": Field.at(6, 0, 8),
        "turbo": Field.at(10, 3, 1),
        "start_timer": Field.at(10, 4, 1),  # EnableStartTimer
        "stop_timer": Field.at(10, 5, 1),  # EnableStopTimer
        "sleep": Field.at(10, 6, 1),
    },
)


class SanyoAc88Device(Device):
    """Sanyo 88-bit: a full-state protocol with an explicit power bit and no
    toggles, so ``previous`` is ignored. The frame is sent three times.

    As the C path: an off message carries mode auto; the EnableStartTimer
    bit of stateReset stays set. The fan offers auto and the three
    kSanyoAc88Fan* speeds (the legacy "highest" sent FanHigh, as "high").
    Swing "on" and sleep send the documented SwingV and Sleep bits; the
    C path of the oracle fixtures never received them (pyhvac's glue).
    """

    PROTOCOL = SANYO_AC88
    LAYOUTS = (SANYO_AC88_LAYOUT,) * 3 + (None,)
    capabilities = Capabilities(
        modes=("auto", "cool", "heat", "fan"),
        temperature=TemperatureRange(10.0, 30.0),
        fan=FAN_3,
        swing_v=SWING,
        features={name: ON_OFF for name in ("powerful", "purifier", "sleep")},
    )

    def frames(self, previous, target, actions):
        feat = target.features
        data = bytes(
            SANYO_AC88_LAYOUT.build(
                power=target.power,
                # As the C path: IRac passes mode "off" for an off message,
                # which convertMode maps to kSanyoAc88Auto.
                mode=target.mode if target.power else "auto",
                # setTemp clamps to kSanyoAc88TempMin-Max, whole degrees.
                temperature=int(target.temperature),
                fan=target.fan,
                swing_v=target.swing_v,
                turbo=feat["powerful"],
                filter=feat["purifier"],
                sleep=feat["sleep"],
            )
        )
        return [Frame("main", data)] * 3 + [Frame("end", b"", 0)]


SANYO_AC88_MODELS = ("generic 88",)


# Now the match between models and objects
