#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Kelvinator AC IR commands.
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
from ..choices import FAN_5, ON_OFF, SWING, SWING_V_ANGLES
from ..device import Device
from ..fields import Checksums, Copy, Field, Joined, Layout
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import Capabilities, TemperatureRange


class Kelvinator(PulseBased):

    STARTFRAME = [9010, 4505]
    ENDFRAME = [600, 19975]
    MARK = [680]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [510, 1530]  # ditto

    def __init__(self):
        super().__init__("KELVINATOR")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [16, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": ["off", "on"],
            "purifier": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
            "cleaning": ["off", "on"],
            "light": ["off", "on"],
        }


DEVICES = {}


# ------------------------------------------------------------- Kelvinator
# Layout from IRremoteESP8266's KelvinatorProtocol (ir_Kelvinator.h): a
# 16-byte state, each byte LSB first. IRsend::sendKelvinator sends it as two
# blocks of 8 bytes, each a command (bytes 0-3, with a kKelvinatorHdrMark /
# HdrSpace header, then the 3-bit kKelvinatorCmdFooter b010, a
# kKelvinatorBitMark and kKelvinatorGapSpace) and options (bytes 4-7, no
# header, a kKelvinatorBitMark and kKelvinatorGapSpace * 2). No repeat
# (kKelvinatorDefaultRepeat is kNoRepeat). Carrier 38 kHz (sendGeneric's 38).
#
# The command footer carries no data: it is a fixed burst in the "command"
# section's footer. Byte 7's Sum1 covers bytes 0-6 and bytes 8-10 repeat
# bytes 0-2, so the checksums span frames: the Layout is over the whole
# message, the four frames' data joined in order.

# kKelvinatorBitMark, kKelvinatorZeroSpace, kKelvinatorOneSpace: 8, 6 and 18
# ticks of kKelvinatorTick (85 µs).
_KELVINATOR_MARK, _KELVINATOR_ZERO, _KELVINATOR_ONE = 680, 510, 1530
_KELVINATOR_BITS = PulseDistance(_KELVINATOR_MARK, _KELVINATOR_ZERO, _KELVINATOR_ONE)

KELVINATOR = Protocol(
    "kelvinator",
    {
        "command": Section(
            _KELVINATOR_BITS,
            header=(9010, 4505),  # kKelvinatorHdrMark, kKelvinatorHdrSpace
            # kKelvinatorCmdFooter (b010, LSB first) and kKelvinatorBitMark.
            footer=(
                _KELVINATOR_MARK,
                _KELVINATOR_ZERO,
                _KELVINATOR_MARK,
                _KELVINATOR_ONE,
                _KELVINATOR_MARK,
                _KELVINATOR_ZERO,
                _KELVINATOR_MARK,
            ),
            gap=19975,  # kKelvinatorGapSpace
        ),
        "options": Section(
            _KELVINATOR_BITS,
            footer=(_KELVINATOR_MARK,),  # kKelvinatorBitMark
            gap=39950,  # kKelvinatorGapSpace * 2
        ),
    },
    carrier=38000,
)

KELVINATOR_MIN_TEMP, KELVINATOR_MAX_TEMP = 16, 30  # kKelvinatorMinTemp/MaxTemp
KELVINATOR_MODE = {  # kKelvinator{Auto,Cool,Dry,Fan,Heat}
    "auto": 0,
    "cool": 1,
    "dry": 2,
    "fan": 3,
    "heat": 4,
}
# Fan: kKelvinatorFanAuto (0), then speeds kKelvinatorFanMin (1) to
# kKelvinatorFanMax (5), as setFan takes them ("0 is auto, 1-5 is the
# speed"). IRac::kelvinator passes the stdAc fan speed unconverted ("No
# conversion needed"): kLow 2, kMedium 3, kHigh 4, so the legacy entity's
# low/medium/high are "2"/"3"/"4" (FAN_5's labels).
KELVINATOR_FAN = {"auto": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5}
KELVINATOR_BASIC_FAN_MAX = 3  # kKelvinatorBasicFanMax
KELVINATOR_SWING_V = {  # kKelvinatorSwingV*: canonical "1" highest .. "5" lowest
    "off": 0b0000,
    "auto": 0b0001,
    "1": 0b0010,  # Highest
    "2": 0b0011,  # UpperMiddle
    "3": 0b0100,  # Middle
    "4": 0b0101,  # LowerMiddle
    "5": 0b0110,  # Lowest
    "low_auto": 0b0111,
    "middle_auto": 0b1001,
    "high_auto": 0b1011,
}
KELVINATOR_CHECKSUM_START = 10  # kKelvinatorChecksumStart


@dataclass(frozen=True)
class KelvinatorBlockSum:
    """IRKelvinatorAC::calcBlockChecksum over the 8-byte block at ``start``:
    kKelvinatorChecksumStart plus the low nibbles of its bytes 0-3 and the
    high nibbles of its bytes 4-6, mod 16, in the high nibble of byte 7.
    The low nibble of byte 7 is left alone."""

    start: int

    def compute(self, data):
        block = data[self.start : self.start + 7]
        total = KELVINATOR_CHECKSUM_START
        total += sum(b & 0x0F for b in block[:4]) + sum(b >> 4 for b in block[4:])
        return total & 0x0F

    def positions(self):
        return {self.start + 7}

    def bits(self):
        return set(range(8 * (self.start + 7) + 4, 8 * (self.start + 8)))

    def apply(self, data):
        at = self.start + 7
        data[at] = (data[at] & 0x0F) | self.compute(data) << 4

    def check(self, data):
        return data[self.start + 7] >> 4 == self.compute(data)


# Skeleton: IRKelvinatorAC::stateReset (all zero, byte 3 0x50, byte 11 0x70)
# with its checksums, as getRaw returns it. stateReset writes every byte, so
# no bit is stale; the unnamed bits are never written after it.
KELVINATOR_LAYOUT = Layout(
    bytes.fromhex("00000050000000a0" "00000070000000a0"),
    {
        # Byte 0 (repeated in byte 8).
        "mode": Field.at(0, 0, 3, values=KELVINATOR_MODE),
        "power": Field.at(0, 3, 1),
        "basic_fan": Field.at(0, 4, 2),  # BasicFan: min(Fan, BasicFanMax)
        "swing_auto": Field.at(0, 6, 1),  # SwingAuto
        "sleep_1_3": Field.at(0, 7, 1),  # Sleep modes 1 & 3
        # Byte 1: degrees - kKelvinatorMinTemp.
        "temp": Field.at(
            1,
            0,
            4,
            values={
                t: t - KELVINATOR_MIN_TEMP
                for t in range(KELVINATOR_MIN_TEMP, KELVINATOR_MAX_TEMP + 1)
            },
        ),
        # Byte 2.
        "turbo": Field.at(2, 4, 1),
        "light": Field.at(2, 5, 1),
        "ion_filter": Field.at(2, 6, 1),
        "xfan": Field.at(2, 7, 1),
        # Byte 4.
        "swing_v": Field.at(4, 0, 4, values=KELVINATOR_SWING_V),
        "swing_h": Field.at(4, 4, 1, values={"off": 0, "swing": 1}),
        "timer": Field.at(5, 0, 16),  # pad0: timer related
        # Byte 12.
        "sleep_2": Field.at(12, 0, 1),  # Sleep mode 2
        "quiet": Field.at(12, 7, 1),
        # Byte 14.
        "fan": Field.at(14, 4, 3, values=KELVINATOR_FAN),
    },
    # fixup: bytes 8-10 repeat bytes 0-2, then checksum() writes Sum1 and
    # Sum2.
    checksum=Checksums(Copy(0, 3, 8), KelvinatorBlockSum(0), KelvinatorBlockSum(8)),
)


class KelvinatorDevice(Device):
    """Kelvinator (YALIF remote, KSV* units), and the Gree YAPOF3/YAP0F8 and
    Sharp YB1FA/A5VEY models on the same protocol: a full-state protocol
    with no toggles, so ``previous`` is ignored.

    As IRac::kelvinator sends it (setPower, setMode, setTemp, setFan,
    setSwingVertical, setSwingHorizontal, then the features, on a fresh
    IRKelvinatorAC):
    - an off message carries mode auto (convertMode's default for IRac's
      "off"), with the requested setpoint, fan and settings;
    - the requested setpoint is sent in every mode: setMode's 25 C for auto
      and dry is overwritten by setTemp;
    - fan "1".."5" is Fan 1..5 (kKelvinatorFanMin..kKelvinatorFanMax;
      the legacy low/medium/high, IRac's stdAc speeds 2/3/4, are "2"/"3"/
      "4"), BasicFan being the same capped at kKelvinatorBasicFanMax;
    - cleaning (XFan) is cleared outside cool and dry (fixup), so also in
      every off message;
    - powerful is Turbo, purifier is IonFilter; the sleep and timer bits
      stay clear (IRac has no sleep or timer for this protocol).

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_kelvinator_device.py):
    - swing_v "1", "2" and "4" (90°, 60°, 30°): the old glue passes kHigh,
      kUpperMiddle and kLow; convertSwingV turns them into auto codes (or
      its default, kKelvinatorSwingVAuto) that setSwingVertical(false, ...)
      replaces with kKelvinatorSwingVOff. The port sends the documented
      positions, highest to lowest: Highest, UpperMiddle, Middle,
      LowerMiddle, Lowest ("3" and "5" are what C sends);
    - swing_h "swing": the old glue (IRGHVAC.trans_hswing) has no "on", so
      IRac passed kOff; the port sets SwingH, and SwingAuto with it, as
      setSwingHorizontal does.

    SwingAuto is set for swing_v auto or swing_h on (setSwingVertical's
    rule). setSwingHorizontal re-derives it from bit 0 of SwingV, which
    would also set it for UpperMiddle and LowerMiddle (odd codes, yet fixed
    positions); the C path never sends those, and the port does not.
    """

    PROTOCOL = KELVINATOR
    LAYOUTS = (Joined(KELVINATOR_LAYOUT, 4),)  # the four frames, joined
    capabilities = Capabilities(
        modes=("auto", "cool", "fan", "dry", "heat"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=FAN_5,  # kKelvinatorFanMin..kKelvinatorFanMax, and auto
        swing_v=SWING_V_ANGLES,
        swing_h=SWING,
        features={
            "purifier": ON_OFF,
            "powerful": ON_OFF,
            "quiet": ON_OFF,
            "cleaning": ON_OFF,
            "light": ON_OFF,
        },
    )

    def frames(self, previous, target, actions):
        mode = target.mode if target.power else "auto"
        features = target.features
        fan = KELVINATOR_FAN[target.fan]
        swing_h = target.swing_h == "swing"
        data = KELVINATOR_LAYOUT.build(
            power=target.power,
            mode=mode,
            temp=int(target.temperature),
            basic_fan=min(fan, KELVINATOR_BASIC_FAN_MAX),
            fan=target.fan,
            swing_v=target.swing_v,
            swing_h=target.swing_h,
            swing_auto=target.swing_v == "auto" or swing_h,
            quiet=features["quiet"],
            turbo=features["powerful"],
            light=features["light"],
            ion_filter=features["purifier"],
            xfan=features["cleaning"] and mode in ("cool", "dry"),
        )
        return [
            Frame(name, bytes(data[i : i + 4]))
            for i, name in zip(
                range(0, 16, 4), ("command", "options", "command", "options")
            )
        ]


KELVINATOR_MODELS = (  # kelvinator plugin
    "YALIF remote",
    "KSV26CRC",
    "KSV26HRC",
    "KSV35CRC",
    "KSV35HRC",
    "KSV53HRC",
    "KSV62HRC",
    "KSV70CRC",
    "KSV70HRC",
    "KSV80HRC",
    "generic",
)
KELVINATOR_GREE_MODELS = ("YAPOF3 remote", "YAP0F8 remote")  # gree plugin
KELVINATOR_SHARP_MODELS = ("YB1FA remote", "A5VEY")  # sharp plugin


DEVICES.update({m: KelvinatorDevice for m in KELVINATOR_MODELS})


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "YALIF remote": Kelvinator,
        "KSV26CRC": Kelvinator,
        "KSV26HRC": Kelvinator,
        "KSV35CRC": Kelvinator,
        "KSV35HRC": Kelvinator,
        "KSV53HRC": Kelvinator,
        "KSV62HRC": Kelvinator,
        "KSV70CRC": Kelvinator,
        "KSV70HRC": Kelvinator,
        "KSV80HRC": Kelvinator,
        "generic": Kelvinator,
    }

    def __init__(self):
        self.brand = "kelvinator"
