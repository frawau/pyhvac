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

from ..device import Device
from ..fields import Checksum, Field, InvertedPairs, Layout, NibbleSum, bit_reverse
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_3, FAN_4, FAN_5, ON_OFF, SWING, SWING_H_5
from ..state import Capabilities, Choice, TemperatureRange

# ------------------------------------------------------------ shared parts
# The 28-, 264-, 296- and 344-byte messages go through sendHitachiAC with
# the same timings; only the bit order changes (LSB first for
# kHitachiAc264/296/344StateLength, MSB first otherwise).


def _hitachi_ac_protocol(name, lsb_first=True, tolerance=0.30, mark_excess=50):
    """The sendHitachiAC message: one frame, 38 kHz.

    decodeHitachiAC (kHitachiAcBits, kHitachiAc264Bits, kHitachiAc344Bits)
    matches with k_tolerance = _tolerance + 5 (30 %) and kMarkExcess;
    decodeHitachiAc296 with kUseDefTol (25 %) and mark excess 0.
    """
    return Protocol(
        name,
        {
            "main": Section(
                PulseDistance(400, 500, 1250),  # kHitachiAcBitMark/ZeroSpace/OneSpace
                header=(3300, 1700),  # kHitachiAcHdrMark/HdrSpace
                footer=(400,),
                gap=100000,  # kHitachiAcMinGap = kDefaultMessageGap
                lsb_first=lsb_first,
            ),
        },
        carrier=38000,  # kHitachiAcFreq
        tolerance=tolerance,
        mark_excess=mark_excess,
    )


# --------------------------------------------------------------- HitachiAc
# Layout from IRremoteESP8266's HitachiProtocol (ir_Hitachi.h): one 28-byte
# frame (kHitachiAcStateLength), sent MSB first (sendHitachiAC), so frame
# byte n is struct byte n. Every field holds its value bit-reversed
# (IRHitachiAc stores reverseBits(value, 8)), and so do the value tables.

HITACHI_AC = _hitachi_ac_protocol("hitachi-ac", lsb_first=False)


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
    "3": 4,  # kHitachiAcFanHigh - 1 (kHigh)
    "4": 5,  # kHitachiAcFanHigh (kMax)
}
# The four speeds IRHitachiAc::setFan allows (kHitachiAcFanLow up to
# kHitachiAcFanHigh), with the legacy labels for the first three.
HITACHI_AC_FAN = Choice(
    ("auto", "1", "2", "3", "4"),
    {"auto": "auto", "1": "low", "2": "medium", "3": "high", "4": "highest"},
)
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
        temperature=TemperatureRange(16.0, 32.0),  # kHitachiAcMin/MaxTemp
        fan=HITACHI_AC_FAN,
        swing_v=SWING,
        swing_h=SWING,
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to kHitachiAcAuto).
        mode = target.mode if target.power else "auto"
        # IRHitachiAc::setFan clamps by mode: dry only has low and medium
        # (kHitachiAcFanLow..+1), fan has no auto (minimum kHitachiAcFanLow).
        fan = target.fan
        if mode == "dry":
            fan = {"auto": "1", "3": "2", "4": "2"}.get(fan, fan)
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
    # decodeHitachiAC (kHitachiAc1Bits): k_tolerance = _tolerance + 5
    # (30 %), kMarkExcess.
    tolerance=0.30,
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
        fan=FAN_3,
        swing_v=SWING,
        swing_h=SWING,
        features={"sleep": ON_OFF},
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


# ------------------------------------------------- the Hitachi424 family
# Layouts from IRremoteESP8266's Hitachi424Protocol (ir_Hitachi.h), which
# IRHitachiAc344 and IRHitachiAc264 (both derived from IRHitachiAc424) share,
# and HitachiAC296Protocol, whose fields sit at the same offsets. Each byte is
# sent LSB first. From byte 3 on, every even byte is the complement of the
# byte before it (IRHitachiAc424::setInvertedStates, and
# IRHitachiAc296::setInvertedStates), so every field sits in an odd byte.

HITACHI424_MODE = {  # kHitachiAc424{Fan,Cool,Dry,Heat}, = kHitachiAc264*
    "fan": 1,
    "cool": 3,
    "dry": 5,
    "heat": 6,
}
HITACHI424_BUTTON = {  # kHitachiAc424Button*, = kHitachiAc344Button*
    "power_mode": 0x13,
    "fan": 0x42,
    "temp_down": 0x43,
    "temp_up": 0x44,
    "swing_v": 0x81,
    "swing_h": 0x8C,
}
HITACHI424_FAN = {  # canonical fan -> kHitachiAc424Fan*, = kHitachiAc344Fan*
    "auto": 5,  # Auto
    "1": 1,  # Min
    "2": 2,  # Low
    "3": 3,  # Medium
    "4": 4,  # High
    "5": 6,  # Max
}
# IRHitachiAc424::stateReset, odd bytes only (the complements follow).
HITACHI424_RESET = {
    0: 0x01,
    1: 0x10,
    3: 0x40,
    5: 0xFF,
    7: 0xCC,
    27: 0xE1,
    33: 0x80,
    35: 0x03,
    37: 0x01,
    39: 0x88,
    45: 0xFF,
    47: 0xFF,
    49: 0xFF,
    51: 0xFF,
}


def _reset_state(length, raw):
    """``length`` bytes: ``raw`` (byte -> value) over zeros, with the
    complements of the inverted pairs from byte 3 filled in."""
    data = bytearray(length)
    for i, value in raw.items():
        if i < length:
            data[i] = value
    InvertedPairs(3, length).apply(data)
    return bytes(data)


def _hitachi424_layout(
    reset, length, modes, fans, buttons=None, temp_width=6, fan_width=4, **fields
):
    """A Hitachi424Protocol-shaped layout over ``length`` bytes of the reset
    state ``reset``: temperature (byte 13), mode and fan (byte 25) and power
    (byte 27), the button (byte 11) if ``buttons`` is given, plus ``fields``.
    """
    common = {
        "temperature": Field.at(13, 2, temp_width, encode=int),  # whole °C
        "mode": Field.at(25, 0, 4, values=modes),
        "fan": Field.at(25, 4, fan_width, values=fans),
        "power": Field.at(27, 4, 1),
    }
    if buttons is not None:
        common["button"] = Field.at(11, 0, 8, values=buttons)
    return Layout(
        _reset_state(length, reset),
        {**common, **fields},
        checksum=InvertedPairs(3, length),
    )


# ------------------------------------------------------------- Hitachi424
# 53 bytes after a bitless leader (kHitachiAc424LdrMark/Space).

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
    # decodeHitachiAc424: the leader with the defaults, the frame with
    # kUseDefTol (25 %) and mark excess 0.
    mark_excess=0,
)

# raw[9] and raw[29] are not in the struct (padding), but
# IRHitachiAc424::setFan writes them: 0x92/0x00, 0x98 for FanMin, and
# 0xA9/0x30 for FanMax.
_FAN_BYTES = {
    "fan_byte9": Field.at(9, 0, 8),
    "fan_byte29": Field.at(29, 0, 8),
}

HITACHI424_LAYOUT = _hitachi424_layout(
    HITACHI424_RESET,
    53,  # kHitachiAc424StateLength
    HITACHI424_MODE,
    HITACHI424_FAN,
    HITACHI424_BUTTON,
    **_FAN_BYTES,
    # IRHitachiAc344 only: the 424 class has no setter, skeleton kept.
    swing_h_344=Field.at(35, 0, 3),
    swing_v_344=Field.at(37, 5, 1),
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
        fan=FAN_5,
        swing_v=SWING,
    )

    def _values(self, previous, target):
        """The fields IRHitachiAc424 writes, shared with IRHitachiAc344."""
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
        return dict(
            fan_byte9={"1": 0x98, "5": 0xA9}.get(fan, 0x92),
            button="swing_v" if swing else "power_mode",
            # IRac's setTemp(degrees) comes after setMode, so fan mode's
            # kHitachiAc424FanTemp never survives.
            temperature=int(target.temperature),
            mode=mode,
            fan=fan,
            power=target.power,
            fan_byte29=0x30 if fan == "5" else 0x00,
        )

    def frames(self, previous, target, actions):
        data = HITACHI424_LAYOUT.build(**self._values(previous, target))
        return [Frame("leader", b""), Frame("main", bytes(data))]


HITACHI424_MODELS = ("RAR-8P2 remote", "RAS-AJ25H", "generic 424")


# ------------------------------------------------------------- Hitachi344
# IRHitachiAc344 reuses Hitachi424Protocol for its 43 bytes
# (kHitachiAc344StateLength), with the kHitachiAc344* values and the
# 344-only SwingH (byte 35) and SwingV (byte 37) fields. Sent by
# sendHitachiAC: one frame, LSB first (MSBfirst is false for
# kHitachiAc344StateLength), closed by kHitachiAcMinGap.

HITACHI344 = _hitachi_ac_protocol("hitachi344")

HITACHI344_SWING_H = {  # canonical position -> kHitachiAc344SwingH*
    "auto": 0,  # kHitachiAc344SwingHAuto
    "1": 5,  # far left: kHitachiAc344SwingHLeftMax
    "2": 4,  # kHitachiAc344SwingHLeft
    "3": 3,  # kHitachiAc344SwingHMiddle
    "4": 2,  # kHitachiAc344SwingHRight
    "5": 1,  # far right: kHitachiAc344SwingHRightMax
}

HITACHI344_LAYOUT = _hitachi424_layout(
    # IRHitachiAc344::stateReset: IRHitachiAc424's, then raw[37] and raw[39]
    # cleared.
    {**HITACHI424_RESET, 37: 0x00, 39: 0x00},
    43,  # kHitachiAc344StateLength
    HITACHI424_MODE,
    HITACHI424_FAN,
    HITACHI424_BUTTON,
    **_FAN_BYTES,
    swing_h=Field.at(35, 0, 3, values=HITACHI344_SWING_H),
    # The SwingV state bit (IRHitachiAc344::setSwingV). IRac::hitachi344
    # never calls setSwingV, only setSwingVToggle (the button), so the C
    # path always sends it clear; the port does too.
    swing_v=Field.at(37, 5, 1),
)


class Hitachi344Device(Hitachi424Device):
    """Hitachi344 (RAS-22NK, RF11T1): Hitachi424's state and swing button
    (IRHitachiAc344 derives from IRHitachiAc424), plus horizontal swing
    positions, in one frame without the leader.

    The swing button follows Hitachi424Device's rule, as IRac::handleToggles
    does for HITACHI_AC344: with ``previous`` it is pressed only when swing_v
    changes, with ``previous=None`` whenever swing_v is "swing".
    """

    PROTOCOL = HITACHI344
    LAYOUTS = (HITACHI344_LAYOUT,)
    capabilities = Capabilities(
        modes=("cool", "fan", "dry", "heat"),
        temperature=TemperatureRange(16.0, 32.0),
        fan=FAN_5,
        swing_v=SWING,
        swing_h=SWING_H_5,
    )

    def frames(self, previous, target, actions):
        data = HITACHI344_LAYOUT.build(
            **self._values(previous, target), swing_h=target.swing_h, swing_v=0
        )
        return [Frame("main", bytes(data))]


HITACHI344_MODELS = ("RAS-22NK", "RF11T1", "generic 344")


# --------------------------------------------------------------- Hitachi264
# IRHitachiAc264 derives from IRHitachiAc424 and writes Hitachi424Protocol's
# field offsets into its 33 bytes (kHitachiAc264StateLength), with the
# kHitachiAc264* values. One frame sent LSB first (sendHitachiAC: MSBfirst
# is false for kHitachiAc264StateLength).

HITACHI264 = _hitachi_ac_protocol("hitachi264")

HITACHI264_LAYOUT = _hitachi424_layout(
    # IRHitachiAc264::stateReset: IRHitachiAc424::stateReset, then
    # raw[9] = 0x92 and raw[27] = 0xC1.
    {**HITACHI424_RESET, 9: 0x92, 27: 0xC1},
    33,  # kHitachiAc264StateLength
    HITACHI424_MODE,  # kHitachiAc264{Fan,Cool,Dry,Heat}
    {"1": 1, "2": 3, "3": 4, "auto": 5},  # kHitachiAc264Fan{Low,Medium,High,Auto}
    # kHitachiAc264Button*: kHitachiAc424's, without SwingH.
    {k: v for k, v in HITACHI424_BUTTON.items() if k != "swing_h"},
)


class Hitachi264Device(Device):
    """Hitachi264 (RAR-2P2): a full-state protocol, ``previous`` is ignored.

    The button byte names the key "pressed". IRac::hitachi264 builds every
    message on a fresh IRHitachiAc264 and calls setPower last, so the C path
    always sends kHitachiAc264ButtonPowerMode; the port does the same, with
    or without ``previous`` (the frame carries the full state either way).

    Capabilities are what HitachiAC264Protocol can carry: kHitachiAc264
    has no auto mode (IRHitachiAc424::convertMode sends cool for it), and
    no swing or feature bits. The legacy entity offered auto, swing and
    purifier/powerful/quiet/economy/light, none of which changed the frame:
    IRac::hitachi264 has "No Swing(V) setting available" and
    IRHitachiAc264::toCommon forces swingv off. The swing button
    (kHitachiAc264ButtonSwingV) would need a toggle rule (as Hitachi424's),
    which the C path never sends; it is not offered.
    """

    PROTOCOL = HITACHI264
    LAYOUTS = (HITACHI264_LAYOUT,)
    capabilities = Capabilities(
        modes=("cool", "fan", "dry", "heat"),  # kHitachiAc264{Cool,Fan,Dry,Heat}
        temperature=TemperatureRange(16.0, 32.0),  # kHitachiAc264Min/MaxTemp
        fan=FAN_3,  # kHitachiAc264Fan{Low,Medium,High,Auto}
    )

    def frames(self, previous, target, actions):
        # As the C path: IRHitachiAc424::convertMode has no auto (nor off),
        # so auto and every off message carry cool. setTemp runs after
        # setMode, so fan mode keeps the setpoint (not kHitachiAc424FanTemp).
        mode = target.mode if target.power and target.mode != "auto" else "cool"
        data = HITACHI264_LAYOUT.build(
            button="power_mode",
            temperature=target.temperature,
            mode=mode,
            fan=target.fan,
            power=target.power,
        )
        return [Frame("main", bytes(data))]


HITACHI264_MODELS = ("RAR-2P2 remote", "RAK-25NH5", "generic 264")


# ----------------------------------------------------------- Hitachi296
# HitachiAC296Protocol: 37 bytes (kHitachiAc296StateLength) sent LSB first
# in one frame (sendHitachiAC with MSBfirst false for
# kHitachiAc296StateLength), fields at Hitachi424Protocol's offsets but a
# 5-bit Temp and a 3-bit Fan.

# decodeHitachiAc296: kUseDefTol (25 %), mark excess 0.
HITACHI296 = _hitachi_ac_protocol("hitachi296", tolerance=0.25, mark_excess=0)

HITACHI296_MODE = {  # kHitachiAc296*, as IRHitachiAc296::convertMode
    "cool": 0b0011,  # kHitachiAc296Cool
    "dry": 0b0101,  # kHitachiAc296Dehumidify
    "heat": 0b0110,  # kHitachiAc296Heat
    "auto": 0b0111,  # kHitachiAc296Auto
}
HITACHI296_FAN = {  # canonical fan -> kHitachiAc296Fan*, as convertFan
    "1": 0b001,  # lowest: kHitachiAc296FanSilent
    "2": 0b010,  # kHitachiAc296FanLow
    "3": 0b011,  # kHitachiAc296FanMedium
    "4": 0b100,  # kHitachiAc296FanHigh (convertFan: kHigh and kMax)
    "auto": 0b101,  # kHitachiAc296FanAuto
}
HITACHI296_TEMP_AUTO = 1  # kHitachiAc296TempAuto
HITACHI296_MIN_TEMP = 16  # kHitachiAc296MinTemp
HITACHI296_MAX_TEMP = 31  # kHitachiAc296MaxTemp

# IRHitachiAc296::stateReset, odd bytes only (the complements follow).
# Byte 13 bits 0-1 ("unset_low") and bit 7 ("unset_high"), and byte 25
# bit 7 ("unset") are never written by stateReset; see Hitachi296Device.
HITACHI296_RESET = {
    0: 0x01,
    1: 0x10,
    3: 0x40,
    5: 0xFF,
    7: 0xCC,
    9: 0x92,
    11: 0x43,
    27: 0xF1,
    35: 0x03,
}
HITACHI296_LAYOUT = _hitachi424_layout(
    HITACHI296_RESET,
    37,  # kHitachiAc296StateLength
    HITACHI296_MODE,
    None,  # raw kHitachiAc296Fan* codes (HITACHI296_FAN)
    temp_width=5,  # whole °C, or kHitachiAc296TempAuto
    fan_width=3,
    unset_low=Field.at(13, 0, 2),  # padding the C path never initialises
    unset_high=Field.at(13, 7, 1),  # padding the C path never initialises
    unset=Field.at(25, 7, 1),  # padding bit the C path never initialises
)


class Hitachi296Device(Device):
    """Hitachi296 (RAR-3U3): a full-state protocol, ``previous`` is ignored.

    Byte 13 bits 0-1 and bit 7 (padding around Temp) and byte 25 bit 7
    (padding after Fan) are unnamed in HitachiAC296Protocol and never
    written by IRHitachiAc296::stateReset. IRac builds the object on the
    stack, so the C path sends whatever memory held: byte 25 bit 7 differs
    from process to process, byte 13 bits 0-1 came out 0b11 in every process
    tried and bit 7 came out 0, both by accident. The port sends 0 for all
    four bits, as the RAR-3U3 remote does in the library's captured messages
    (ir_Hitachi_test.cpp).
    """

    PROTOCOL = HITACHI296
    LAYOUTS = (HITACHI296_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "heat"),
        temperature=TemperatureRange(16.0, 31.0),  # kHitachiAc296Min/MaxTemp
        fan=FAN_4,  # kHitachiAc296Fan{Silent,Low,Medium,High,Auto}
    )

    def frames(self, previous, target, actions):
        # As the C path: an off message carries mode auto (IRac passes mode
        # "off", which convertMode maps to auto), and in auto setTemp stores
        # kHitachiAc296TempAuto instead of the setpoint.
        mode = target.mode if target.power else "auto"
        if mode == "auto":
            temperature = HITACHI296_TEMP_AUTO
        else:
            temperature = min(
                max(int(target.temperature), HITACHI296_MIN_TEMP), HITACHI296_MAX_TEMP
            )
        data = HITACHI296_LAYOUT.build(
            temperature=temperature,
            mode=mode,
            fan=HITACHI296_FAN[target.fan],
            unset_low=0,
            unset_high=0,
            unset=0,
            power=target.power,
        )
        return [Frame("main", bytes(data))]


HITACHI296_MODELS = ("RAR-3U3 remote", "RAS-70YHA3", "generic 296")


# Now the match between models and objects
