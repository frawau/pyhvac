#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Voltas AC IR commands.
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
from ..fields import Field, Layout, Sum8
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_3, ON_OFF, SWING
from ..state import Capabilities, TemperatureRange

# ------------------------------------------------------------------ Voltas
# Layout from IRremoteESP8266's VoltasProtocol (ir_Voltas.h): 10 bytes
# (kVoltasStateLength), sent by sendVoltas (sendGeneric, MSB first) with no
# header, kVoltasBitMark marks, kVoltasOneSpace/ZeroSpace spaces, a
# kVoltasBitMark footer and kDefaultMessageGap. No repeat (kNoRepeat).
# Carrier kVoltasFreq (38 kHz).

VOLTAS = Protocol(
    "voltas",
    {
        "main": Section(
            PulseDistance(1026, 554, 2553),  # kVoltasBitMark/ZeroSpace/OneSpace
            footer=(1026,),  # kVoltasBitMark
            gap=100000,  # kDefaultMessageGap
            lsb_first=False,
        )
    },
    carrier=38000,  # kVoltasFreq
)


# Skeleton: stateReset's kReset {0x33, 0x28, 0x00, 0x17, 0x3B, 0x3B, 0x3B,
# 0x11, 0x00} with the sum cleared. stateReset writes every byte, so nothing
# comes from stale memory. The timers (disabled, bytes 4-8) and the unnamed
# bits (byte 3 bits 4-5 "Typically 0b01", byte 6 "Typically 0x3B") keep it.
VOLTAS_LAYOUT = Layout(
    bytes.fromhex("33280017" "3b3b3b110000"),
    {
        "swing_h": Field.at(0, 0, 1),  # SwingH
        # kVoltasSwingHChange / kVoltasSwingHNoChange
        "swing_h_change": Field.at(
            0, 1, 7, values={"change": 0b1111100, "no change": 0b0011001}
        ),
        "mode": Field.at(  # kVoltas{Fan,Heat,Dry,Cool}
            1,
            0,
            4,
            values={"fan": 0b0001, "heat": 0b0010, "dry": 0b0100, "cool": 0b1000},
        ),
        "fan": Field.at(  # kVoltasFan{Auto,Low,Med,High}
            1, 5, 3, values={"auto": 0b111, "1": 0b100, "2": 0b010, "3": 0b001}
        ),
        "swing_v": Field.at(2, 0, 3, values={"off": 0b000, "swing": 0b111}),
        "wifi": Field.at(2, 3, 1),
        "turbo": Field.at(2, 5, 1),
        "sleep": Field.at(2, 6, 1),
        "power": Field.at(2, 7, 1),
        "temperature": Field.at(  # degrees - kVoltasMinTemp
            3, 0, 4, values={t: t - 16 for t in range(16, 31)}
        ),
        "econo": Field.at(3, 6, 1),
        "temp_set": Field.at(3, 7, 1),
        "on_timer_mins": Field.at(4, 0, 6),
        "on_timer_12hr": Field.at(4, 7, 1),
        "off_timer_mins": Field.at(5, 0, 6),
        "off_timer_12hr": Field.at(5, 7, 1),
        "on_timer_hrs": Field.at(7, 0, 4),
        "off_timer_hrs": Field.at(7, 4, 4),
        "light": Field.at(8, 5, 1),
        "off_timer_enable": Field.at(8, 6, 1),
        "on_timer_enable": Field.at(8, 7, 1),
    },
    Sum8(0, 9, 9, base=0xFF),  # IRVoltas::calcChecksum: ~sum
)

VOLTAS_MIN_TEMP = 16  # kVoltasMinTemp
VOLTAS_MAX_TEMP = 30  # kVoltasMaxTemp


def _voltas_capabilities(swing_h):
    return Capabilities(
        modes=("cool", "dry", "fan", "heat"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=FAN_3,
        swing_v=SWING,
        swing_h=swing_h,
        features={
            "economy": ON_OFF,
            "powerful": ON_OFF,
            "light": ON_OFF,
            "sleep": ON_OFF,
        },
    )


# Remote variant (voltas_ac_remote_model_t) -> the legacy entity: Voltas
# (kVoltasUnknown, "Full Function") has horizontal swing, Voltasv2
# (kVoltas122LZF, "No SwingH support") has none.
VOLTAS_CAPABILITIES = {
    "Unknown": _voltas_capabilities(SWING),
    "122LZF": _voltas_capabilities(None),
}


class VoltasDevice(Device):
    """Voltas (VOLTAS, remote variants Unknown and 122LZF,
    voltas_ac_remote_model_t): every setting is sent in full.

    The variant comes from the model (VOLTAS_MODELS) unless given, so the
    registry's ``cls(brand, model)`` call picks it; an unknown model gets
    122LZF, the model stateReset's kReset reads as (IRsend.h: "(Default)").
    The variant picks the capabilities and byte 0:
    - Unknown: IRVoltas::setSwingH writes SwingH and sets SwingHChange to
      kVoltasSwingHChange on every message (IRac::voltas always calls it);
    - 122LZF: IRVoltas::setModel sets kVoltasSwingHNoChange, which also sets
      SwingH, and setSwingH does nothing.

    As IRac::voltas sends it:
    - an off message clears Power and carries mode cool (IRac's kOff mode
      falls to convertMode's default, kVoltasCool) with the rest of the
      target state;
    - fan mode has no auto speed: IRVoltas::setFan sends kVoltasFanHigh;
    - dry keeps the requested setpoint and fan: setMode's kVoltasDryTemp
      and kVoltasFanLow are overwritten by IRac's setTemp and setFan after
      it;
    - powerful (Turbo), economy (Econo) and sleep are only sent in cool
      (IRVoltas::setTurbo/setEcono/setSleep); light sets Light;
    - Wifi, TempSet and the timers keep kReset's values.

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_voltas_device.py):
    - swing "swing": the old glue has no swing "on", so IRac's swingv stays
      kOff and setSwingV(false) writes 0; the port sends 0b111;
    - swing_h "swing" (Unknown): likewise, the port sends SwingH 1;
    - sleep: the old glue never passes sleep; the port sends the Sleep bit.

    ``previous`` is ignored. Every field is state: SwingHChange marks SwingH
    as valid rather than toggling it, so sending it with the current value
    is idempotent. IRac::handleToggles has no Voltas rule and IRac builds a
    fresh IRVoltas for every message, so C sends the same frame whatever
    came before.
    """

    PROTOCOL = VOLTAS
    LAYOUTS = (VOLTAS_LAYOUT,)
    capabilities = VOLTAS_CAPABILITIES["122LZF"]

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        self.variant = variant or VOLTAS_MODELS.get(model, "122LZF")
        if self.variant not in VOLTAS_CAPABILITIES:
            raise ValueError(f"unknown Voltas variant {self.variant!r}")
        self.capabilities = VOLTAS_CAPABILITIES[self.variant]

    def frames(self, previous, target, actions):
        mode = target.mode if target.power else "cool"
        cool = mode == "cool"
        features = target.features
        fan = target.fan
        if mode == "fan" and fan == "auto":
            fan = "3"
        if self.variant == "Unknown":
            swing_h = dict(swing_h=target.swing_h != "off", swing_h_change="change")
        else:
            swing_h = dict(swing_h=1, swing_h_change="no change")
        temperature = min(
            max(int(target.temperature), VOLTAS_MIN_TEMP), VOLTAS_MAX_TEMP
        )
        data = VOLTAS_LAYOUT.build(
            **swing_h,
            mode=mode,
            fan=fan,
            swing_v=target.swing_v,
            turbo=cool and features["powerful"],
            sleep=cool and features["sleep"],
            power=target.power,
            temperature=temperature,
            econo=cool and features["economy"],
            light=features["light"],
        )
        return [Frame("main", bytes(data))]


VOLTAS_MODELS = {  # model -> remote variant (voltas_ac_remote_model_t)
    "122LZF 4011252": "122LZF",
    "generic": "Unknown",
    "generic 2": "122LZF",
}


# Now the match between models and objects
