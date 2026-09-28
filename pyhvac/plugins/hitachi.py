#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Hitachi AC IR commands.
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
from ..fields import Checksum, Field, InvertedPairs, Layout, NibbleSum, bit_reverse
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import Capabilities, Choice, TemperatureRange

try:
    from ..irhvac import R_LT0541_HTA_A, R_LT0541_HTA_B
except ImportError:
    # Only the C-backed classes use these; keep the ported ones importable.
    R_LT0541_HTA_A = R_LT0541_HTA_B = None


class Hitachi(PulseBased):

    STARTFRAME = [3300, 1700]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [500, 1250]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC")
        self.capabilities = {
            "mode": ["off", "auto", "heat", "cool", "dry", "fan"],
            "temperature": [16, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
        }


class Hitachi1A(PulseBased):

    STARTFRAME = [3400, 3400]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [372, 1208]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC1", variant=R_LT0541_HTA_A)
        self.capabilities = {
            "mode": ["off", "auto", "heat", "cool", "dry", "fan"],
            "temperature": [16, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "sleep": ["off", "on"],
        }


class Hitachi1B(PulseBased):

    STARTFRAME = [3400, 3400]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [372, 1208]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC1", variant=R_LT0541_HTA_B)
        self.capabilities = {
            "mode": ["off", "auto", "heat", "cool", "dry", "fan"],
            "temperature": [16, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "hswing": ["off", "on"],
            "sleep": ["off", "on"],
        }


class Hitachi424(PulseBased):

    LEAD = [29784, 49290]
    STARTFRAME = [3416, 1604]
    ENDFRAME = None
    MARK = [463]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [500, 1250]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC424")
        self.capabilities = {
            "mode": ["off", "fan", "heat", "cool", "dry"],
            "temperature": [16, 32],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
        }


class Hitachi3(PulseBased):

    STARTFRAME = [3400, 1660]
    ENDFRAME = None
    MARK = [460]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [410, 1250]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC3")
        self.capabilities = {
            "mode": ["off", "fan", "heat", "cool", "dry"],
            "temperature": [16, 32],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
        }


class Hitachi344(PulseBased):

    STARTFRAME = [3300, 1700]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [500, 1250]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC344")
        self.capabilities = {
            "mode": ["off", "cool", "fan", "dry", "heat"],
            "temperature": [16, 32],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
            "swing": ["off", "on"],
            "hswing": ["auto", "far right", "right", "middle", "left", "far left"],
        }


class Hitachi264(PulseBased):

    STARTFRAME = [3300, 1700]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [500, 1250]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC264")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [16, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "purifier": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
            "economy": ["off", "on"],
            "light": ["off", "on"],
        }


class Hitachi296(PulseBased):

    STARTFRAME = [3300, 1700]
    ENDFRAME = None
    MARK = [400]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [500, 1250]  # ditto

    def __init__(self):
        super().__init__("HITACHI_AC296")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "dry", "heat"],
            "temperature": [16, 25],
            "fan": ["auto", "highest", "high", "medium", "low", "lowest"],
        }


DEVICES = {}


# --------------------------------------------------------------- HitachiAc
# Layout from IRremoteESP8266's HitachiProtocol (ir_Hitachi.h): one 28-byte
# frame (kHitachiAcStateLength), sent MSB first (sendHitachiAC), so frame
# byte n is struct byte n. Every field holds its value bit-reversed
# (IRHitachiAc stores reverseBits(value, 8)), and so do the value tables.

HITACHI_AC = Protocol(
    "hitachi-ac",
    {
        "main": Section(
            PulseDistance(400, 500, 1250),  # kHitachiAcBitMark/ZeroSpace/OneSpace
            header=(3300, 1700),  # kHitachiAcHdrMark/HdrSpace
            footer=(400,),
            gap=100000,  # kHitachiAcMinGap = kDefaultMessageGap
            lsb_first=False,
        ),
    },
    carrier=38000,  # kHitachiAcFreq
)


@dataclass(frozen=True)
class HitachiAcChecksum(Checksum):
    """IRHitachiAc::calcChecksum: 62 minus the sum of the bit-reversed bytes
    before ``at``, bit-reversed."""

    def compute(self, data):
        return bit_reverse((62 - sum(self._input(data))) & 0xFF)


HITACHI_AC_MODES = {  # kHitachiAc{Auto,Heat,Cool,Dry,Fan}
    "auto": 2,
    "heat": 3,
    "cool": 4,
    "dry": 5,
    "fan": 0xC,
}
HITACHI_AC_FANS = {  # IRHitachiAc::convertFan
    "auto": 1,  # kHitachiAcFanAuto
    "1": 2,  # kHitachiAcFanLow (kLow)
    "2": 3,  # kHitachiAcFanMed (kMedium)
    "3": 4,  # kHitachiAcFanHigh - 1 (kHigh; kMax would be kHitachiAcFanHigh)
}
HITACHI_AC_MIN_TEMP = 16  # kHitachiAcMinTemp

# Skeleton: IRHitachiAc::stateReset with the written fields and the sum
# cleared. Bytes 0-8, 14/15 (0x60 below the swing bits) and 24 (0x80) are
# fixed; byte 9 is 0x10, or 0x90 at kHitachiAcMinTemp (setTemp).
HITACHI_AC_LAYOUT = Layout(
    bytes.fromhex("80080c02fd807f884810000000006060000000000000000080000000"),
    {
        "min_temp": Field.at(9, 7, 1),
        "mode": Field.at(
            10, 0, 8, values={k: bit_reverse(v) for k, v in HITACHI_AC_MODES.items()}
        ),
        "temperature": Field.at(  # whole °C, doubled
            11, 0, 8, values={t: bit_reverse(t << 1) for t in range(16, 33)}
        ),
        "fan": Field.at(
            13, 0, 8, values={k: bit_reverse(v) for k, v in HITACHI_AC_FANS.items()}
        ),
        "swing_v": Field.at(14, 7, 1, values={"off": 0, "swing": 1}),
        "swing_h": Field.at(15, 7, 1, values={"off": 0, "swing": 1}),
        "power": Field.at(17, 0, 1),
    },
    checksum=HitachiAcChecksum(0, 27, 27, reverse=True),
)


class HitachiAcDevice(Device):
    """Hitachi (RAS-35THA6): a full-state protocol, ``previous`` is ignored."""

    PROTOCOL = HITACHI_AC
    LAYOUTS = (HITACHI_AC_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "heat", "cool", "dry", "fan"),
        temperature=TemperatureRange(16.0, 32.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
        ),
        swing_v=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
        swing_h=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to kHitachiAcAuto).
        mode = target.mode if target.power else "auto"
        # IRHitachiAc::setFan clamps by mode: dry only has low and medium
        # (kHitachiAcFanLow..+1), fan has no auto (minimum kHitachiAcFanLow).
        fan = target.fan
        if mode == "dry":
            fan = {"auto": "1", "3": "2"}.get(fan, fan)
        elif mode == "fan" and fan == "auto":
            fan = "1"
        # setMode(kHitachiAcFan) writes the special temperature 64, but IRac
        # calls setTemp(degrees) after setMode, so the setpoint is always sent.
        temperature = int(target.temperature)
        data = HITACHI_AC_LAYOUT.build(
            min_temp=temperature == HITACHI_AC_MIN_TEMP,
            mode=mode,
            temperature=temperature,
            fan=fan,
            swing_v=target.swing_v,
            swing_h=target.swing_h,
            power=target.power,
        )
        return [Frame("main", bytes(data))]


HITACHI_AC_MODELS = ("RAS-35THA6 remote", "generic")


DEVICES.update({m: HitachiAcDevice for m in HITACHI_AC_MODELS})


# ------------------------------------------------------------- Hitachi1
# Layout from IRremoteESP8266's Hitachi1Protocol (ir_Hitachi.h): one 13-byte
# frame, bytes in order, each sent MSB first (sendHitachiAC1: sendGeneric
# with MSBfirst). Header kHitachiAc1HdrMark/HdrSpace, bits
# kHitachiAcBitMark/ZeroSpace/OneSpace, gap kHitachiAcMinGap
# (kDefaultMessageGap), carrier kHitachiAcFreq.

HITACHI1 = Protocol(
    "hitachi1",
    {
        "main": Section(
            PulseDistance(400, 500, 1250),
            header=(3400, 3400),
            footer=(400,),
            gap=100000,
            lsb_first=False,
        )
    },
    carrier=38000,
)


@dataclass(frozen=True)
class Hitachi1Checksum(NibbleSum):
    """IRHitachiAc1::calcChecksum: the sum of every nibble of data[start:end],
    each nibble bit-reversed, stored bit-reversed.

    ``reverse=True`` covers the per-nibble reversal (the nibbles of a
    reversed byte are its nibbles reversed); NibbleSum writes its result as
    computed, so the final reversal needs this subclass. The checksum is a
    whole byte (kHitachiAc1ChecksumStartByte..Sum).
    """

    reverse: bool = True

    def compute(self, data):
        return bit_reverse(super().compute(data))


def _rev5(n):
    return int(f"{n:05b}"[::-1], 2)


HITACHI1_MIN_TEMP, HITACHI1_MAX_TEMP = 16, 32  # kHitachiAcMin/MaxTemp
HITACHI1_TEMP_AUTO = 25  # kHitachiAc1TempAuto
HITACHI1_SLEEP = 0b010  # kHitachiAc1Sleep2: what IRac sends for any sleep

HITACHI1_LAYOUT = Layout(
    # IRHitachiAc1::stateReset with the written fields and the sum cleared:
    # byte 6 bit 7 stays set, the timers (bytes 7-10) are never set by IRac.
    bytes.fromhex("b2ae4d11f00080000000000000"),
    {
        "model": Field.at(3, 6, 2, values={"A": 0b10, "B": 0b01}),
        "fan": Field.at(  # kHitachiAc1Fan*
            5, 0, 4, values={"auto": 1, "1": 8, "2": 4, "3": 2}
        ),
        "mode": Field.at(  # kHitachiAc1*
            5,
            4,
            4,
            values={
                "dry": 0b0010,
                "fan": 0b0100,
                "cool": 0b0110,
                "heat": 0b1001,
                "auto": 0b1110,
            },
        ),
        # (celsius - kHitachiAc1TempDelta), 5 bits reversed
        "temperature": Field.at(
            6,
            2,
            5,
            values={
                t: _rev5(t - 7) for t in range(HITACHI1_MIN_TEMP, HITACHI1_MAX_TEMP + 1)
            },
        ),
        "swing_toggle": Field.at(11, 0, 1),
        "sleep": Field.at(11, 1, 3),  # kHitachiAc1Sleep*
        "power_toggle": Field.at(11, 4, 1),
        "power": Field.at(11, 5, 1),
        "swing_v": Field.at(11, 6, 1, values={"off": 0, "swing": 1}),
        "swing_h": Field.at(11, 7, 1, values={"off": 0, "swing": 1}),
    },
    checksum=Hitachi1Checksum(5, 12, 12),
)


class Hitachi1Device(Device):
    """Hitachi AC1 (R-LT0541-HTA, remote variants A and B): full state plus a
    power toggle and a swing toggle bit.

    The variant ("A" or "B", kHitachiAc1Model_A/B) comes from the model
    (HITACHI1_MODELS) unless given, so the registry's ``cls(brand, model)``
    call picks it; unknown models get A, as IRHitachiAc1::setModel does.

    Toggles, as IRac::sendAc does for HITACHI_AC1 (not handleToggles): the
    power toggle is set when the power changes, the swing toggle when
    swing_v or swing_h changes. IRac compares against its previous state,
    and a fresh IRac's previous state is the stdAc default (power off, both
    swings off), so without ``previous`` this device compares against that:
    power toggle = target.power, swing toggle = any swing on. This matches
    the C path in both cases.
    """

    PROTOCOL = HITACHI1
    LAYOUTS = (HITACHI1_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "heat", "cool", "dry", "fan"),
        temperature=TemperatureRange(16.0, 32.0),
        fan=Choice(
            ("auto", "1", "2", "3"),
            {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
        ),
        swing_v=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
        swing_h=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
        features={"sleep": Choice((False, True), {False: "off", True: "on"})},
    )

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        self.variant = variant or HITACHI1_MODELS.get(model, "A")
        if self.variant not in ("A", "B"):
            raise ValueError(f"unknown Hitachi1 variant {self.variant!r}")

    def frames(self, previous, target, actions):
        if previous is None:  # a fresh IRac: its previous state is all off
            power_toggle = target.power
            swing_toggle = target.swing_v != "off" or target.swing_h != "off"
        else:
            power_toggle = previous.power != target.power
            swing_toggle = (
                previous.swing_v != target.swing_v or previous.swing_h != target.swing_h
            )
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to auto).
        mode = target.mode if target.power else "auto"
        # setTemp is ignored in auto: the reset state's kHitachiAc1TempAuto.
        temperature = HITACHI1_TEMP_AUTO if mode == "auto" else int(target.temperature)
        fan = target.fan
        if mode == "auto":
            fan = "auto"  # setFan: auto is locked to auto speed
        elif mode == "dry":
            fan = "1"  # setFan: dry is locked to low speed
        elif mode in ("heat", "fan") and fan == "auto":
            fan = "1"  # setFan: no auto speed in heat and fan, low instead
        data = HITACHI1_LAYOUT.build(
            model=self.variant,
            mode=mode,
            temperature=temperature,
            fan=fan,
            swing_v=target.swing_v,
            swing_h=target.swing_h,
            # IRac's Sleep2 for any sleep; setSleep: only in auto and cool.
            sleep=(
                HITACHI1_SLEEP
                if target.features["sleep"] and mode in ("auto", "cool")
                else 0
            ),
            power=target.power,
            power_toggle=power_toggle,
            swing_toggle=swing_toggle,
        )
        return [Frame("main", bytes(data))]


HITACHI1_MODELS = {  # model -> remote variant (hitachi_ac1_remote_model_t)
    "LT0541-HTA remote": "A",
    "Series VI": "A",
    "KAZE-312KSDP": "A",
    "R-LT0541-HTA/Y.K.1.1-1 V2.3 remote": "A",
    "generic 1 code a": "A",
    "generic 1 code b": "B",
}


DEVICES.update({m: Hitachi1Device for m in HITACHI1_MODELS})


# ------------------------------------------------------------- Hitachi424
# Layout from IRremoteESP8266's Hitachi424Protocol (ir_Hitachi.h): 53 bytes,
# each sent LSB first, after a bitless leader (kHitachiAc424LdrMark/Space).
# From byte 3 on, every even byte is the complement of the byte before it
# (IRHitachiAc424::setInvertedStates), so every field sits in an odd byte.

HITACHI424 = Protocol(
    "hitachi424",
    {
        "leader": Section(None, header=(29784,), gap=49290),
        "main": Section(
            PulseDistance(463, 372, 1208),  # kHitachiAc424BitMark/Zero/OneSpace
            header=(3416, 1604),  # kHitachiAc424HdrMark/HdrSpace
            footer=(463,),
            gap=100000,  # kHitachiAcMinGap
        ),
    },
    carrier=38000,  # kHitachiAcFreq
)

HITACHI424_BUTTON = {  # kHitachiAc424Button*
    "power_mode": 0x13,
    "fan": 0x42,
    "temp_down": 0x43,
    "temp_up": 0x44,
    "swing_v": 0x81,
    "swing_h": 0x8C,
}
HITACHI424_FAN = {  # canonical fan -> kHitachiAc424Fan*
    "auto": 5,  # Auto
    "1": 1,  # Min
    "2": 2,  # Low
    "3": 3,  # Medium
    "4": 4,  # High
    "5": 6,  # Max
}

# Skeleton: IRHitachiAc424::stateReset's bytes, pairs inverted, with every
# field cleared. Bytes 9 and 29 are struct padding, but setFan writes them.
HITACHI424_LAYOUT = Layout(
    bytes.fromhex(
        "01100040bfff00cc3300ff00ff00ff00ff00ff00ff00ff00ff00ff"
        "e11e00ff00ff807f03fc01fe887700ff00ffff00ff00ff00ff00"
    ),
    {
        "fan_aux9": Field.at(9, 0, 8),  # 0x98 fan Min, 0xA9 Max, else 0x92
        "button": Field.at(11, 0, 8, values=HITACHI424_BUTTON),
        "temperature": Field.at(13, 2, 6),  # whole °C
        "mode": Field.at(25, 0, 4, values={"fan": 1, "cool": 3, "dry": 5, "heat": 6}),
        "fan": Field.at(25, 4, 4, values=HITACHI424_FAN),
        "power": Field.at(27, 4, 1),
        "fan_aux29": Field.at(29, 0, 8),  # 0x30 fan Max, else 0x00
        # IRHitachiAc344 only: the 424 class has no setter, skeleton kept.
        "swing_h_344": Field.at(35, 0, 3),
        "swing_v_344": Field.at(37, 5, 1),
    },
    checksum=InvertedPairs(3, 53),
)


class Hitachi424Device(Device):
    """Hitachi424 (RAR-8P2): full state, except that vertical swing is a
    button (byte 11): the remote keeps no swing state.

    Every message carries kHitachiAc424ButtonPowerMode, as the C path does
    (IRac::hitachi424 calls setPower last, whatever changed), unless swing is
    toggled: then kHitachiAc424ButtonSwingV. With ``previous`` the swing
    button is sent only when swing changes between off and on, the rule
    IRac::handleToggles applies to HITACHI_AC424 when it is given a previous
    state. Without ``previous`` it is sent whenever swing is on, as a fresh
    IRac sends it (no previous state, no toggle handling).
    """

    PROTOCOL = HITACHI424
    LAYOUTS = (None, HITACHI424_LAYOUT)
    capabilities = Capabilities(
        modes=("fan", "heat", "cool", "dry"),
        temperature=TemperatureRange(16.0, 32.0),
        fan=Choice(
            ("auto", "1", "2", "3", "4", "5"),
            {
                "auto": "auto",
                "1": "lowest",
                "2": "low",
                "3": "medium",
                "4": "high",
                "5": "highest",
            },
        ),
        swing_v=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode cool (IRac passes mode
        # "off", which convertMode maps to cool).
        mode = target.mode if target.power else "cool"
        fan = target.fan
        # IRHitachiAc424::setFan: dry allows auto, Min and Low only
        # (kHitachiAc424FanMaxDry); fan mode has no auto and uses Min.
        if mode == "dry" and fan in ("3", "4", "5"):
            fan = "2"
        elif mode == "fan" and fan == "auto":
            fan = "1"
        if previous is None:
            swing = target.swing_v != "off"
        else:
            swing = (target.swing_v != "off") != (previous.swing_v != "off")
        data = HITACHI424_LAYOUT.build(
            fan_aux9={"1": 0x98, "5": 0xA9}.get(fan, 0x92),
            button="swing_v" if swing else "power_mode",
            # IRac's setTemp(degrees) comes after setMode, so fan mode's
            # kHitachiAc424FanTemp never survives.
            temperature=int(target.temperature),
            mode=mode,
            fan=fan,
            power=target.power,
            fan_aux29=0x30 if fan == "5" else 0x00,
        )
        return [Frame("leader", b""), Frame("main", bytes(data))]


HITACHI424_MODELS = ("RAR-8P2 remote", "RAS-AJ25H", "generic 424")


DEVICES.update({m: Hitachi424Device for m in HITACHI424_MODELS})


# ------------------------------------------------------------- Hitachi344
# Layout from IRremoteESP8266's Hitachi424Protocol (ir_Hitachi.h), which
# IRHitachiAc344 reuses for its 43 bytes (kHitachiAc344StateLength), with the
# kHitachiAc344* values and the 344-only SwingH (byte 35) and SwingV (byte 37)
# fields. Sent by sendHitachiAC: one frame, LSB first (MSBfirst is false for
# kHitachiAc344StateLength), closed by kHitachiAcMinGap. From byte 3 on,
# every second byte is the complement of the one before it
# (IRHitachiAc424::setInvertedStates).

HITACHI344 = Protocol(
    "hitachi344",
    {
        "main": Section(
            PulseDistance(400, 500, 1250),  # kHitachiAcBitMark/ZeroSpace/OneSpace
            header=(3300, 1700),  # kHitachiAcHdrMark/HdrSpace
            footer=(400,),
            gap=100000,  # kHitachiAcMinGap = kDefaultMessageGap
        )
    },
    carrier=38000,  # kHitachiAcFreq
)

HITACHI344_BUTTON = {  # kHitachiAc344Button*
    "power_mode": 0x13,
    "fan": 0x42,
    "temp_down": 0x43,
    "temp_up": 0x44,
    "swing_v": 0x81,
    "swing_h": 0x8C,
}
HITACHI344_FAN = {  # canonical fan -> kHitachiAc344Fan*
    "1": 1,  # lowest: kHitachiAc344FanMin
    "2": 2,  # kHitachiAc344FanLow
    "3": 3,  # kHitachiAc344FanMedium
    "4": 4,  # kHitachiAc344FanHigh
    "auto": 5,  # kHitachiAc344FanAuto
    "5": 6,  # highest: kHitachiAc344FanMax
}
HITACHI344_SWING_H = {  # canonical position -> kHitachiAc344SwingH*
    "auto": 0,  # kHitachiAc344SwingHAuto
    "1": 5,  # far left: kHitachiAc344SwingHLeftMax
    "2": 4,  # kHitachiAc344SwingHLeft
    "3": 3,  # kHitachiAc344SwingHMiddle
    "4": 2,  # kHitachiAc344SwingHRight
    "5": 1,  # far right: kHitachiAc344SwingHRightMax
}

# Skeleton from IRHitachiAc344::stateReset with the written fields cleared
# (the complements are recomputed by the checksum).
HITACHI344_LAYOUT = Layout(
    bytes.fromhex(
        "01100040bfff00cc3300ff00ff00ff00ff00ff00ff00ff00ff00ffe11e00ff00ff807f00ff00ff00ff00ff"
    ),
    {
        # raw[9] and raw[29] are not in the struct: IRHitachiAc424::setFan
        # writes 0x92/0x00, 0x98 for FanMin, and 0xA9/0x30 for FanMax.
        "fan_byte9": Field.at(9, 0, 8),
        "button": Field.at(11, 0, 8, values=HITACHI344_BUTTON),
        "temperature": Field.at(13, 2, 6, encode=int),  # whole °C
        "mode": Field.at(25, 0, 4, values={"fan": 1, "cool": 3, "dry": 5, "heat": 6}),
        "fan": Field.at(25, 4, 4, values=HITACHI344_FAN),
        "power": Field.at(27, 4, 1),
        "fan_byte29": Field.at(29, 0, 8),
        "swing_h": Field.at(35, 0, 3, values=HITACHI344_SWING_H),
        # The SwingV state bit (IRHitachiAc344::setSwingV). IRac::hitachi344
        # never calls setSwingV, only setSwingVToggle (the button), so the C
        # path always sends it clear; the port does too.
        "swing_v": Field.at(37, 5, 1),
    },
    checksum=InvertedPairs(3, 43),
)


class Hitachi344Device(Device):
    """Hitachi344 (RAS-22NK, RF11T1): full state, plus a swing toggle.

    Vertical swing is sent as a button press (``button`` = swing_v, byte 11),
    which toggles the louvre. With ``previous`` the button is pressed only
    when swing_v changes, as IRac::handleToggles does for HITACHI_AC344 with
    a previous state. With ``previous=None`` it is pressed when swing_v is
    "swing", as a fresh IRac sends. Otherwise the button is power/mode:
    IRac::hitachi344 calls setPower last, and setSwingVToggle only replaces
    the button when swing is asked for.
    """

    PROTOCOL = HITACHI344
    LAYOUTS = (HITACHI344_LAYOUT,)
    capabilities = Capabilities(
        modes=("cool", "fan", "dry", "heat"),
        temperature=TemperatureRange(16.0, 32.0),
        fan=Choice(
            ("auto", "1", "2", "3", "4", "5"),
            {
                "auto": "auto",
                "1": "lowest",
                "2": "low",
                "3": "medium",
                "4": "high",
                "5": "highest",
            },
        ),
        swing_v=Choice(("off", "swing"), {"off": "off", "swing": "on"}),
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
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode cool (IRac passes mode
        # "off", which convertMode maps to cool).
        mode = target.mode if target.power else "cool"
        # IRHitachiAc424::setFan: dry allows auto or up to low; fan mode has
        # no auto and falls back to min.
        fan = HITACHI344_FAN[target.fan]
        if mode == "dry" and fan != HITACHI344_FAN["auto"]:
            fan = min(fan, 2)  # kHitachiAc424FanMaxDry
        elif mode == "fan" and fan == HITACHI344_FAN["auto"]:
            fan = 1  # kHitachiAc424FanMin
        if previous is None:
            press = target.swing_v != "off"
        else:
            press = target.swing_v != previous.swing_v
        data = HITACHI344_LAYOUT.build(
            fan_byte9={1: 0x98, 6: 0xA9}.get(fan, 0x92),
            button="swing_v" if press else "power_mode",
            # IRac's setTemp comes after setMode, so fan mode keeps the
            # setpoint rather than kHitachiAc424FanTemp.
            temperature=int(target.temperature),
            mode=mode,
            fan=HITACHI344_LAYOUT.fields["fan"].from_int(fan),
            power=target.power,
            fan_byte29=0x30 if fan == 6 else 0x00,
            swing_h=target.swing_h,
            swing_v=0,
        )
        return [Frame("main", bytes(data))]


HITACHI344_MODELS = ("RAS-22NK", "RF11T1", "generic 344")


DEVICES.update({m: Hitachi344Device for m in HITACHI344_MODELS})


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "RAS-35THA6 remote": Hitachi,
        "LT0541-HTA remote": Hitachi1A,
        "Series VI": Hitachi1A,
        "RAR-8P2 remote": Hitachi424,
        "RAS-AJ25H": Hitachi424,
        "PC-LH3B": Hitachi3,
        "KAZE-312KSDP": Hitachi1A,
        "R-LT0541-HTA/Y.K.1.1-1 V2.3 remote": Hitachi1A,
        "RAS-22NK": Hitachi344,
        "RF11T1": Hitachi344,
        "RAR-2P2 remote": Hitachi264,
        "RAK-25NH5": Hitachi264,
        "RAR-3U3 remote": Hitachi296,
        "RAS-70YHA3": Hitachi296,
        "generic": Hitachi,
        "generic 1 code a": Hitachi1A,
        "generic 1 code b": Hitachi1B,
        "generic 424": Hitachi424,
        "generic 3": Hitachi3,
        "generic 344": Hitachi344,
        "generic 264": Hitachi264,
        "generic 296": Hitachi296,
    }

    def __init__(self):
        self.brand = "hitachi"
