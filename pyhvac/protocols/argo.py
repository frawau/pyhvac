#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Argo AC IR commands.
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
##
# Description of the various ": Greev1, devices supported. Can be a remote control name

from dataclasses import dataclass

from ..device import Device
from ..fields import Field, Layout, Sum8
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_3, ON_OFF
from ..state import Capabilities, Choice, TemperatureRange

# ---------------------------------------------------------------------- Argo
# Layouts from IRremoteESP8266's ArgoProtocol (WREM2 remote, 12 bytes,
# kArgoStateLength) and ArgoProtocolWREM3 (WREM3 remote; its AC control
# message, 6 bytes, kArgo3AcControlStateLength) in ir_Argo.h. Both are sent
# by sendArgo: sendGeneric with kArgoHdrMark/HdrSpace, kArgoBitMark,
# kArgoOneSpace/ZeroSpace, LSB first, at kArgoFrequency.
#
# - WREM3 (sendArgoWREM3, sendFooter=true): a kArgoBitMark footer and
#   kArgoGap (kDefaultMessageGap).
# - WREM2 (IRArgoACBase::send, sendFooter=false): no footer mark and no gap,
#   so the message ends on the last bit's space. A PulseDistance section needs
#   a footer mark to delimit its bits, so the section carries bits 0-94 and
#   sends bit 95 (byte 11 bit 7, unnamed padding that every message keeps 0)
#   as its footer: kArgoBitMark then kArgoZeroSpace.

ARGO = Protocol(
    "argo",
    {
        "wrem2": Section(
            PulseDistance(400, 900, 2200),  # kArgoBitMark/ZeroSpace/OneSpace
            header=(6400, 3300),  # kArgoHdrMark/HdrSpace
            footer=(400, 900),  # bit 95 (always 0): kArgoBitMark, kArgoZeroSpace
        ),
        "wrem3": Section(
            PulseDistance(400, 900, 2200),
            header=(6400, 3300),
            footer=(400,),  # kArgoBitMark
            gap=100000,  # kArgoGap (kDefaultMessageGap)
        ),
    },
    carrier=38000,  # kArgoFrequency
    # decodeArgo / decodeArgoWREM3: _tolerance (25 %), mark excess 0.
    mark_excess=0,
)
ARGO_WREM2_BITS = 95  # kArgoBits - 1: the last bit is the section footer

ARGO_TEMP_DELTA = 4  # kArgoTempDelta: Temp and RoomTemp are stored minus 4
ARGO_MIN_TEMP, ARGO_MAX_TEMP = 10, 32  # kArgoMinTemp / kArgoMaxTemp
ARGO_TEMP = {t: t - ARGO_TEMP_DELTA for t in range(ARGO_MIN_TEMP, ARGO_MAX_TEMP + 1)}
# RoomTemp: IRac passes no sensor temperature (kNoTempValue), so every
# message keeps stateReset's setSensorTemp(25): 25 - kArgoTempDelta.
ARGO_ROOM_TEMP = 25
# SwingV, both remotes (IRArgoACBase::convertSwingV): canonical "1" is
# argoFlap_t FLAP_1 ("Highest"), down to "6", FLAP_6 ("Lowest"). FLAP_FULL
# (7) is what convertSwingV gives swing off, which the entity does not offer.
ARGO_FLAP = {
    "auto": 0,  # FLAP_AUTO
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "full": 7,  # FLAP_FULL
}

# WREM2 raw modes, as IRArgoACBase<ArgoProtocol>::setMode stores them.
ARGO_WREM2_MODE = {
    "cool": 0b000,  # kArgoCool
    "dry": 0b001,  # kArgoDry
    "auto": 0b010,  # kArgoAuto
    "fan": 0b011,  # kArgoOff: setMode's value for argoMode_t::FAN
    "heat": 0b100,  # kArgoHeat
}
# WREM2 fan: canonical -> kArgoFan*, as setFan(convertFan(speed)) stores it:
# low (kLow) -> FAN_LOWER -> kArgoFan1, medium (kMedium) -> FAN_LOW ->
# kArgoFan2, high (kHigh) -> FAN_HIGH -> kArgoFan3.
ARGO_WREM2_FAN = {"auto": 0, "1": 1, "2": 2, "3": 3}


@dataclass(frozen=True)
class ArgoChecksum:
    """IRArgoACBase<ArgoProtocol>::_checksum: Sum, the 8 bits from bit 82
    (byte 10 bits 2-7, byte 11 bits 0-1), is calcChecksum's
    sumBytes(state, kArgoStateLength - 2, 2): bytes 0-9 plus 2, mod 256."""

    at: int = 82
    end: int = 10
    init: int = 2

    def compute(self, data):
        return (self.init + sum(data[: self.end])) & 0xFF

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


# Skeleton: IRArgoACBase<ArgoProtocol>::_stateReset (bytes 2-11 zeroed, so
# nothing is stale; Pre1 kArgoPreamble1, Pre2 kArgoPreamble2, Post
# kArgoPost) with every field and the sum cleared. The timer bits (bytes 4-9,
# unnamed in the struct) stay 0: IRac never sets them.
ARGO_WREM2_LAYOUT = Layout(
    bytes.fromhex("acf500000000000000000200"),
    {
        "mode": Field.at(2, 3, 3, values=ARGO_WREM2_MODE),
        "temperature": Field.at(2, 6, 5, values=ARGO_TEMP),  # Temp
        "fan": Field.at(3, 3, 2, values=ARGO_WREM2_FAN),
        "room_temp": Field.at(3, 5, 5),  # RoomTemp: celsius - kArgoTempDelta
        "flap": Field.at(4, 2, 3, values=ARGO_FLAP),
        "night": Field.at(9, 2, 1),
        "max": Field.at(9, 3, 1),
        "filter": Field.at(9, 4, 1),  # unnamed in the struct ("Filter")
        "power": Field.at(9, 5, 1),
        "ifeel": Field.at(9, 7, 1),
    },
    checksum=ArgoChecksum(),
)

# WREM3 modes: argoMode_t raw values.
ARGO_WREM3_MODE = {
    "cool": 0b001,
    "dry": 0b010,
    "heat": 0b011,
    "fan": 0b100,
    "auto": 0b101,
}
# WREM3 fan: every argoFan_t speed, canonical "1" FAN_LOWEST .. "6"
# FAN_HIGHEST. The labels are convertFan's stdAc speeds, so the legacy low,
# medium and high keep their codes (FAN_LOWER, FAN_LOW, FAN_HIGH).
ARGO_WREM3_FAN = {
    "auto": 0b000,  # FAN_AUTO
    "1": 0b001,  # FAN_LOWEST (kMin)
    "2": 0b010,  # FAN_LOWER (kLow)
    "3": 0b011,  # FAN_LOW (kMedium)
    "4": 0b100,  # FAN_MEDIUM (kMediumHigh; toString "Med-High")
    "5": 0b101,  # FAN_HIGH (kHigh)
    "6": 0b110,  # FAN_HIGHEST (kMax)
}
ARGO_WREM3_FAN_CHOICE = Choice(
    tuple(ARGO_WREM3_FAN),
    {
        "auto": "auto",
        "1": "lowest",
        "2": "low",
        "3": "medium",
        "4": "midhigh",
        "5": "high",
        "6": "highest",
    },
)

# Skeleton: IRArgoACBase<ArgoProtocolWREM3>::_stateReset for AC_CONTROL
# (bytes 1-11 zeroed; Pre1 kArgoWrem3Preamble, IrChannel 0, IrCommandType
# AC_CONTROL, Post1 kArgoWrem3Postfix_ACControl) with every field and the
# sum cleared.
ARGO_WREM3_LAYOUT = Layout(
    bytes.fromhex("0b000000c000"),
    {
        "channel": Field.at(0, 4, 2),  # IrChannel: IRac never sets it
        "command_type": Field.at(0, 6, 2),  # IrCommandType: AC_CONTROL (0)
        "room_temp": Field.at(1, 0, 5),  # RoomTemp: celsius - kArgoTempDelta
        "mode": Field.at(1, 5, 3, values=ARGO_WREM3_MODE),
        "temperature": Field.at(2, 0, 5, values=ARGO_TEMP),  # Temp
        "fan": Field.at(2, 5, 3, values=ARGO_WREM3_FAN),
        "flap": Field.at(3, 0, 3, values=ARGO_FLAP),
        "power": Field.at(3, 3, 1),
        "ifeel": Field.at(3, 4, 1),
        "night": Field.at(3, 5, 1),
        "eco": Field.at(3, 6, 1),
        "max": Field.at(3, 7, 1),
        "filter": Field.at(4, 0, 1),
        "light": Field.at(4, 1, 1),
    },
    checksum=Sum8(0, 5, 5),  # calcChecksum: sumBytes of bytes 0-4
)

ARGO_SWING_V = Choice(
    ("auto", "1", "2", "3", "4", "5", "6"),
    {
        "auto": "auto",
        "1": "ceiling",
        "2": "90°",
        "3": "60°",
        "4": "45°",
        "5": "30°",
        "6": "0°",
    },
)


def _argo_capabilities(fan, **features):
    return Capabilities(
        modes=("auto", "cool", "fan", "dry", "heat"),
        # kArgoMinTemp .. kArgoMaxTemp (setTemp clamps to them), both remotes.
        temperature=TemperatureRange(float(ARGO_MIN_TEMP), float(ARGO_MAX_TEMP)),
        fan=fan,
        swing_v=ARGO_SWING_V,
        features={"powerful": ON_OFF, **features},
    )


ARGO_CAPABILITIES = {  # variant -> what the remote's message can carry
    # WREM2: Fan is 2 bits (kArgoFan1..3); Night is IRac::argo's sleep.
    # Quiet is not offered: IRac::argo has "No Quiet setting available".
    "WREM2": _argo_capabilities(FAN_3, sleep=ON_OFF),
    # WREM3: every argoFan_t speed; Night is IRac's quiet, Eco, Filter and
    # Light their own bits.
    "WREM3": _argo_capabilities(
        ARGO_WREM3_FAN_CHOICE,
        quiet=ON_OFF,
        economy=ON_OFF,
        purifier=ON_OFF,
        light=ON_OFF,
    ),
}


class ArgoDevice(Device):
    """Argo Ulisse: one full-state message, WREM2 (argo_ac_remote_model_t
    SAC_WREM2, IRArgoAC) or WREM3 (SAC_WREM3, IRArgoAC_WREM3, its AC control
    message). The variant comes from the model (ARGO_MODELS) unless given;
    unknown models get WREM2, IRac's default Argo model. ``previous`` is
    ignored: neither struct has toggle bits and IRac::handleToggles has no
    Argo case.

    As IRac::argo / IRac::argoWrem3_ACCommand send it from a fresh object:
    - an off message clears Power and carries mode auto (convertMode maps
      kOff to its default, argoMode_t::AUTO) with the target setpoint, fan
      and swing;
    - RoomTemp is always 25 °C (stateReset; IRac has no sensor reading), and
      iFeel is off;
    - powerful sets Max (setMax(turbo)), in every mode;
    - WREM2: sleep sets Night (IRac::argo's setNight(sleep >= 0)); there
      is no quiet (IRac::argo: "No Quiet setting available"); Filter
      (unnamed in the struct) is never set;
    - WREM3: quiet sets Night (IRac passes its quiet as argoWrem3_ACCommand's
      night), economy sets Eco, purifier sets Filter, light sets Light.
    """

    PROTOCOL = ARGO

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        # The registry always passes the variant; the table maps the 0.1.x
        # model names (oracle records, direct use) to theirs.
        self.variant = variant or ARGO_MODELS.get(model)
        if self.variant is None:
            raise ValueError(
                f"unknown model {model!r}: pass variant= (see pyhvac.brands)"
            )
        if self.variant not in ARGO_CAPABILITIES:
            raise ValueError(f"unknown Argo variant {self.variant!r}")
        self.capabilities = ARGO_CAPABILITIES[self.variant]
        self.LAYOUTS = (
            (ARGO_WREM2_LAYOUT,) if self.variant == "WREM2" else (ARGO_WREM3_LAYOUT,)
        )

    def frames(self, previous, target, actions):
        features = target.features
        values = dict(
            power=target.power,
            # An off message carries mode auto (convertMode(kOff)).
            mode=target.mode if target.power else "auto",
            temperature=min(max(int(target.temperature), ARGO_MIN_TEMP), ARGO_MAX_TEMP),
            room_temp=ARGO_ROOM_TEMP - ARGO_TEMP_DELTA,
            fan=target.fan,
            flap=target.swing_v,
            max=features["powerful"],
        )
        if self.variant == "WREM2":
            data = ARGO_WREM2_LAYOUT.build(night=features.get("sleep", False), **values)
            return [Frame("wrem2", bytes(data), ARGO_WREM2_BITS)]
        data = ARGO_WREM3_LAYOUT.build(
            night=features["quiet"],
            eco=features["economy"],
            filter=features["purifier"],
            light=features.get("light", False),
            **values,
        )
        return [Frame("wrem3", bytes(data))]


ARGO_MODELS = {  # model -> remote variant (argo_ac_remote_model_t)
    "Ulisse 13 DCI": "WREM2",
    "WREM2 remote": "WREM2",
    "generic": "WREM2",
    "Ulisse Eco Mobile": "WREM3",
    "WREM3 remote": "WREM3",
    "generic 2": "WREM3",
}


# Now the match between models and objects
