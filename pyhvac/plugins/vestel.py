#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Vestel AC IR commands.
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
from ..choices import ON_OFF, SWING
from ..state import Capabilities, Choice, TemperatureRange


class Vestel(PulseBased):
    MARK = [1026]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [554, 2553]  # ditto

    def __init__(self):
        super().__init__("VESTEL_AC")
        self.capabilities = {
            "mode": ["auto", "cool", "dry", "fan", "heat"],
            "temperature": [16, 30],
            "fan": ["high", "medium", "low"],
            "swing": ["off", "on"],
            "sleep": ["off", "on"],
            "powerful": ["off", "on"],
            "purifier": ["off", "on"],
        }


DEVICES = {}


# ------------------------------------------------------------------ VestelAc
# Layout from IRremoteESP8266's VestelProtocol (ir_Vestel.h): the 56-bit
# command state (cmdState), sent LSB first by sendVestelAc (sendGeneric with
# kVestelAcHdrMark/HdrSpace, kVestelAcBitMark, kVestelAcOneSpace/ZeroSpace, a
# kVestelAcBitMark footer and a 100 000 µs gap), i.e. 7 bytes in order, each
# LSB first. No repeat (kNoRepeat). Carrier 38 kHz (sendGeneric's 38).
# IRac::vestel sends the time message (timeState) only for a clock, which the
# entity has no way to set, so only the command state is laid out.

VESTEL_AC = Protocol(
    "vestel_ac",
    {
        "main": Section(
            PulseDistance(520, 480, 1535),  # kVestelAcBitMark/ZeroSpace/OneSpace
            header=(3110, 9066),  # kVestelAcHdrMark/HdrSpace
            footer=(520,),  # kVestelAcBitMark
            gap=100000,
        )
    },
    carrier=38000,
)


@dataclass(frozen=True)
class VestelAcChecksum:
    """IRVestelAc::calcChecksum: 0xFF minus (2 + the number of set bits from
    bit ``start`` up), in the 8 bits from ``at`` (CmdSum, bits 12-19: the
    high nibble of byte 1 and the low nibble of byte 2)."""

    start: int = 20
    at: int = 12

    def compute(self, data):
        ones = sum(
            (data[bit // 8] >> (bit % 8)) & 1
            for bit in range(self.start, 8 * len(data))
        )
        return (0xFF - 2 - ones) & 0xFF

    def positions(self):
        return {self.at // 8, (self.at + 7) // 8}

    def bits(self):
        return set(range(self.at, self.at + 8))

    def _write(self, data, value):
        for k in range(8):
            bit = self.at + k
            if (value >> k) & 1:
                data[bit // 8] |= 1 << (bit % 8)
            else:
                data[bit // 8] &= ~(1 << (bit % 8)) & 0xFF

    def _read(self, data):
        return sum(
            ((data[(self.at + k) // 8] >> ((self.at + k) % 8)) & 1) << k
            for k in range(8)
        )

    def apply(self, data):
        self._write(data, self.compute(data))

    def check(self, data):
        return self._read(data) == self.compute(data)


# Skeleton: kVestelAcStateDefault (stateReset writes the whole state, so
# nothing comes from stale memory). Signature 0x201 (bits 0-11) is fixed;
# pad4 (bit 55) is set in the default and in the real capture
# 0xF4410001FF1201 (ir_Vestel_test.cpp, RealNormalExample).
VESTEL_AC_LAYOUT = Layout(
    (0x0F00D9001FEF201).to_bytes(7, "little"),
    {
        "swing": Field.at(2, 4, 4, values={"off": 0xF, "swing": 0xA}),
        # kVestelAcNormal / kVestelAcSleep / kVestelAcTurbo
        "turbo_sleep": Field.at(3, 0, 4, values={"normal": 1, "sleep": 3, "turbo": 7}),
        "pad1": Field.at(3, 4, 8),
        "temperature": Field.at(  # degrees - kVestelAcMinTempH
            4, 4, 4, values={t: t - 16 for t in range(16, 31)}
        ),
        # kVestelAcFan*: the entity has no auto, auto cool or auto heat.
        "fan": Field.at(
            5,
            0,
            4,
            values={
                "auto": 1,
                "1": 5,
                "2": 9,
                "3": 0xB,
                "auto cool": 0xC,
                "auto heat": 0xD,
            },
        ),
        "mode": Field.at(  # kVestelAc{Auto,Cool,Dry,Fan,Heat}
            5, 4, 3, values={"auto": 0, "cool": 1, "dry": 2, "fan": 3, "heat": 4}
        ),
        "pad2": Field.at(5, 7, 3),
        "ion": Field.at(6, 2, 1),
        "pad3": Field.at(6, 3, 1),
        "power": Field.at(6, 4, 2, values={False: 0b00, True: 0b11}),
        "use_cmd": Field.at(6, 6, 1),
        "pad4": Field.at(6, 7, 1),
    },
    VestelAcChecksum(),
)

# The lowest setpoint per mode: kVestelAcMinTempH (16) in heat, as the real
# heat capture 0xF4410001FF1201 carries; kVestelAcMinTempC (18) otherwise,
# the clamp of IRVestelAc::setTemp.
VESTEL_AC_MIN_HEAT = 16
VESTEL_AC_MIN = 18
VESTEL_AC_MAX = 30


class VestelAcDevice(Device):
    """Vestel BIOX CXP-9: every setting is sent in full, in the command
    message; ``previous`` is ignored (IRac::handleToggles has no Vestel rule
    and the protocol has no toggles).

    As IRac::vestel sends it:
    - power sets Power (0b11 on, 0b00 off) and UseCmd;
    - an off message carries mode auto (convertMode's default, which IRac's
      kOff mode falls to) with the rest of the target state;
    - below 18 °C, the setpoint is sent as 18 °C (setTemp clamps to
      kVestelAcMinTempC), except in heat (see below);
    - sleep wins over powerful (setSleep comes after setTurbo; they share
      the TurboSleep field);
    - purifier sets Ion.

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_vestel_ac_device.py):
    - swing "swing": the old glue has no swing "on", so IRac's swingv stays
      kOff and setSwing(false) writes 0xF (stop); the port sends
      kVestelAcSwing (0xA);
    - sleep: the old glue never passes sleep; the port sends kVestelAcSleep;
    - powerful: IRac::vestel's setSleep(sleep >= 0) comes after setTurbo, and
      with sleep off it writes kVestelAcNormal over kVestelAcTurbo, so C never
      sends turbo; the port sends kVestelAcTurbo;
    - heat at 16-17 °C: setTemp clamps to kVestelAcMinTempC (18) in every
      mode, while the header's kVestelAcMinTempH (16) is the offset of the
      Temp field and the real heat capture 0xF4410001FF1201 carries 16 °C;
      the port sends 16 and 17 in heat.
    """

    PROTOCOL = VESTEL_AC
    LAYOUTS = (VESTEL_AC_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "fan", "heat"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=Choice(("1", "2", "3"), {"1": "low", "2": "medium", "3": "high"}),
        swing_v=SWING,
        features={"sleep": ON_OFF, "powerful": ON_OFF, "purifier": ON_OFF},
    )

    def frames(self, previous, target, actions):
        mode = target.mode if target.power else "auto"
        low = VESTEL_AC_MIN_HEAT if mode == "heat" else VESTEL_AC_MIN
        features = target.features
        if features["sleep"]:
            turbo_sleep = "sleep"
        elif features["powerful"]:
            turbo_sleep = "turbo"
        else:
            turbo_sleep = "normal"
        data = VESTEL_AC_LAYOUT.build(
            swing=target.swing_v,
            turbo_sleep=turbo_sleep,
            temperature=min(max(int(target.temperature), low), VESTEL_AC_MAX),
            fan=target.fan,
            mode=mode,
            ion=features["purifier"],
            power=target.power,
            use_cmd=1,
        )
        return [Frame("main", bytes(data))]


VESTEL_AC_MODELS = ("BIOX CXP-9", "generic")


DEVICES.update({m: VestelAcDevice for m in VESTEL_AC_MODELS})


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "BIOX CXP-9": Vestel,
        "generic": Vestel,
    }

    def __init__(self):
        self.brand = "vestel"
