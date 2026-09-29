#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Technibel AC IR commands.
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
from ..choices import FAN_3, FAN_3_FIXED, ON_OFF, SWING
from ..device import Device
from ..fields import Field, Layout, Sum8
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import Capabilities, TemperatureRange


class Technibel(PulseBased):

    STARTFRAME = [8836, 4380]
    MARK = [523]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [564, 1696]  # ditto

    def __init__(self):
        super().__init__("TECHNIBEL_AC")
        self.capabilities = {
            "mode": ["cool", "dry", "fan", "heat"],
            "temperature": [16, 31],
            "fan": ["high", "medium", "low"],
            "swing": ["off", "on"],
            "sleep": ["off", "on"],
        }


# ------------------------------------------------------------ TechnibelAc
# IRremoteESP8266's TechnibelProtocol (ir_Technibel.h): a 56-bit word
# (kTechnibelAcBits). IRsend::sendTechnibelAc passes MSBfirst=true to
# sendGeneric (despite its "LSB First" comment), so the word goes out most
# significant bit first. The logical frame is the word's 7 bytes, most
# significant first, each sent MSB first:
#   byte 0: Header (kTechnibelAcHeader)
#   byte 1: Mode (bits 0-3), FanChange, TempChange, TimerChange, Power
#   byte 2: Fan (bits 0-2), an unnamed bit, Sleep, Swing, UseFah, TimerEnable
#   byte 3: Temp (bits 0-6), an unnamed bit
#   byte 4: TimerHours (bits 0-4), 3 unnamed bits
#   byte 5: Footer
#   byte 6: Sum
# The kTechnibelAcHdrMark/HdrSpace header, a kTechnibelAcBitMark footer and
# kTechnibelAcGap (kDefaultMessageGap). No repeat (kTechnibelAcDefaultRepeat
# is kNoRepeat).

TECHNIBEL_AC = Protocol(
    "technibel_ac",
    {
        "main": Section(
            # kTechnibelAcBitMark/ZeroSpace/OneSpace
            PulseDistance(523, 564, 1696),
            header=(8836, 4380),  # kTechnibelAcHdrMark/HdrSpace
            footer=(523,),  # kTechnibelAcBitMark
            gap=100000,  # kTechnibelAcGap
            lsb_first=False,
        )
    },
    carrier=38000,  # kTechnibelAcFreq
)

TECHNIBEL_AC_MIN_TEMP = 16  # kTechnibelAcTempMinC
TECHNIBEL_AC_MAX_TEMP = 31  # kTechnibelAcTempMaxC
TECHNIBEL_AC_MODE = {"cool": 0b0001, "dry": 0b0010, "fan": 0b0100, "heat": 0b1000}
TECHNIBEL_AC_FAN = {"1": 0b001, "2": 0b010, "3": 0b100}  # kTechnibelAcFan*
TECHNIBEL_AC_RESET_STATE = 0x180101140000EA  # kTechnibelAcResetState


# Skeleton: kTechnibelAcResetState, which stateReset loads whole (no stale
# memory): Header 0x18, cool, power off, fan low, 20 C, Footer 0, the sum.
TECHNIBEL_AC_LAYOUT = Layout(
    TECHNIBEL_AC_RESET_STATE.to_bytes(7, "big"),
    {
        "mode": Field.at(1, 0, 4, values=TECHNIBEL_AC_MODE),  # kTechnibelAc*
        # No IRTechnibelAc setter writes the three Change bits: C always
        # sends 0, as the real capture does.
        "fan_change": Field.at(1, 4, 1),
        "temp_change": Field.at(1, 5, 1),
        "timer_change": Field.at(1, 6, 1),
        "power": Field.at(1, 7, 1),
        "fan": Field.at(2, 0, 3, values=TECHNIBEL_AC_FAN),
        "sleep": Field.at(2, 4, 1),
        "swing_v": Field.at(2, 5, 1, values={"off": 0, "swing": 1}),
        "use_fah": Field.at(2, 6, 1),  # IRac passes celsius: always 0
        "timer_enable": Field.at(2, 7, 1),  # IRac sets no timer: always 0
        "temp": Field.at(  # whole degrees C
            3,
            0,
            7,
            values={
                t: t for t in range(TECHNIBEL_AC_MIN_TEMP, TECHNIBEL_AC_MAX_TEMP + 1)
            },
        ),
        "timer_hours": Field.at(4, 0, 5),  # always 0 (no timer)
    },
    # calcChecksum: the bytes from kTechnibelAcTimerHoursOffset up to
    # kTechnibelAcHeaderOffset (TimerHours, Temp, the fan and mode bytes).
    checksum=Sum8(1, 5, 6, base=0),  # IRTechnibelAc::calcChecksum: ~sum + 1
)

TECHNIBEL_AC_CAPABILITIES = {  # variant -> the legacy entity (old class)
    "technibel": Capabilities(  # Technibel
        modes=("cool", "dry", "fan", "heat"),
        temperature=TemperatureRange(16.0, 31.0),
        fan=FAN_3_FIXED,
        swing_v=SWING,
        features={"sleep": ON_OFF},
    ),
    "teco": Capabilities(  # Teco
        modes=("auto", "cool", "dry", "fan", "heat"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=FAN_3,
        swing_v=SWING,
        features={"sleep": ON_OFF, "light": ON_OFF},
    ),
}
# brand -> variant. By brand, not model: "generic" is a teco and a
# technibel model.
TECHNIBEL_AC_BRAND_VARIANT = {
    "technibel": "technibel",
    "teco": "teco",
    "alaska": "teco",
}


class TechnibelAcDevice(Device):
    """Technibel A/C (IRTechnibelAc, protocol TECHNIBEL_AC): one full-state
    word, sent by the technibel, teco and alaska plugins.

    The variant ("technibel" or "teco", after the legacy Technibel and Teco
    classes) comes from the brand (TECHNIBEL_AC_BRAND_VARIANT) unless given,
    and picks the capabilities (the legacy entities). The variants send the
    same word.

    As IRac::technibel sends it:
    - an off message carries mode cool: convertMode maps IRac's mode "off"
      (and auto, which the protocol lacks) to its default, kTechnibelAcCool;
      the Power bit is clear, the other settings are sent as requested;
    - fan auto is kTechnibelAcFanLow (convertFan's default), and dry mode
      always sends kTechnibelAcFanLow (IRTechnibelAc::setFan's dry rule);
    - the setpoint is clamped to kTechnibelAcTempMinC..MaxC, in Celsius;
    - no timer; light (the teco entity's) sends nothing: the protocol has
      no light.

    ``previous`` is ignored: the word is a full state, the Fan/Temp/Timer
    Change bits are never written by IRTechnibelAc (0 in C and in the real
    capture), and IRac::handleToggles has no TECHNIBEL_AC case.

    Where the C path differs, the port sends the documented value (see the
    Defects in tests/test_technibel_ac_device.py): the old glue never passes
    swing "on" or sleep to C; the port sets the Swing and Sleep bits.
    """

    PROTOCOL = TECHNIBEL_AC
    LAYOUTS = (TECHNIBEL_AC_LAYOUT,)
    VARIANT_CAPABILITIES = TECHNIBEL_AC_CAPABILITIES
    capabilities = TECHNIBEL_AC_CAPABILITIES["technibel"]

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        self.variant = variant or TECHNIBEL_AC_BRAND_VARIANT.get(brand, "technibel")
        if self.variant not in self.VARIANT_CAPABILITIES:
            raise ValueError(f"unknown Technibel A/C variant {self.variant!r}")
        self.capabilities = self.VARIANT_CAPABILITIES[self.variant]

    def frames(self, previous, target, actions):
        mode = target.mode if target.power and target.mode != "auto" else "cool"
        fan = "1" if target.fan == "auto" or mode == "dry" else target.fan
        temp = min(
            max(int(target.temperature), TECHNIBEL_AC_MIN_TEMP), TECHNIBEL_AC_MAX_TEMP
        )
        data = TECHNIBEL_AC_LAYOUT.build(
            mode=mode,
            power=target.power,
            fan=fan,
            sleep=target.features.get("sleep", False),
            swing_v=target.swing_v,
            temp=temp,
        )
        return [Frame("main", bytes(data))]


TECHNIBEL_AC_MODELS = ("IRO PLUS", "generic")  # technibel plugin
TECHNIBEL_AC_TECO_MODELS = ("generic",)  # teco plugin
TECHNIBEL_AC_ALASKA_MODELS = ("SAC9010QC", "SAC9010QC remote")  # alaska plugin


DEVICES = {}
DEVICES.update({m: TechnibelAcDevice for m in TECHNIBEL_AC_MODELS})


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "IRO PLUS": Technibel,
        "generic": Technibel,
    }

    def __init__(self):
        self.brand = "technibel"
