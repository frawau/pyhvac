#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Electra AC IR commands.
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
from ..fields import Field, Layout, Sum8
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_3, ON_OFF, SWING
from ..state import Capabilities, TemperatureRange

# ------------------------------------------------------------- ElectraAc
# Layout from IRremoteESP8266's ElectraProtocol (ir_Electra.h): one 13-byte
# frame, each byte sent LSB first by sendElectraAC, with a
# kElectraAcHdrMark/HdrSpace header, a kElectraAcBitMark footer and
# kElectraAcMessageGap (kDefaultMessageGap) after it. Byte 12 is the sum of
# bytes 0-11.

ELECTRA_AC = Protocol(
    "electra_ac",
    {
        "main": Section(
            PulseDistance(646, 547, 1647),  # kElectraAcBitMark/ZeroSpace/OneSpace
            header=(9166, 4470),  # kElectraAcHdrMark/HdrSpace
            footer=(646,),
            gap=100000,  # kElectraAcMessageGap
        )
    },
    carrier=38000,  # sendElectraAC's "complete guess"
    # decodeElectraAC: _tolerance (25 %), mark excess 0.
    mark_excess=0,
)

# kElectraAcSwingOn / kElectraAcSwingOff, for SwingV and SwingH.
ELECTRA_AC_SWING = {"off": 0b111, "swing": 0b000}
# kElectraAcLightToggleOn / kElectraAcLightToggleOff.
ELECTRA_AC_LIGHT_TOGGLE_ON = 0x15
ELECTRA_AC_LIGHT_TOGGLE_OFF = 0x08

# Skeleton: stateReset clears bytes 1-10, writes 0xC3 in byte 0 and
# kElectraAcLightToggleOff in byte 11; every byte is written, so there is no
# stale padding.
ELECTRA_AC_LAYOUT = Layout(
    bytes.fromhex("c3000000000000000000000800"),
    {
        "swing_v": Field.at(1, 0, 3, values=ELECTRA_AC_SWING),
        "temperature": Field.at(  # degrees - kElectraAcTempDelta
            1, 3, 5, values={t: t - 8 for t in range(16, 33)}
        ),
        "swing_h": Field.at(2, 5, 3, values=ELECTRA_AC_SWING),
        "sensor_update": Field.at(3, 6, 1),
        "fan": Field.at(  # kElectraAcFan*
            4, 5, 3, values={"auto": 0b101, "1": 0b011, "2": 0b010, "3": 0b001}
        ),
        "turbo": Field.at(5, 6, 1),
        "quiet": Field.at(5, 7, 1),
        "ifeel": Field.at(6, 3, 1),
        "mode": Field.at(  # kElectraAc{Auto,Cool,Dry,Heat,Fan}
            6, 5, 3, values={"auto": 0, "cool": 1, "dry": 2, "heat": 4, "fan": 6}
        ),
        "sensor_temp": Field.at(7, 0, 8),  # degrees + kElectraAcSensorTempDelta
        "clean": Field.at(9, 2, 1),
        "power": Field.at(9, 5, 1),
        # Raw: real remotes send other codes too (see the header's notes).
        "light_toggle": Field.at(11, 0, 8),
    },
    Sum8(0, 12, 12),
)

# The "aux" variant: AUX-family remotes, from SmartIR captures (climate 1703
# Electrolux, 1622 Tornado, 1800 Ballu, 1961 AUX, ...). Byte 11 holds the
# key just pressed (ELECTRA_AUX_KEY, the values the captures confirm), byte
# 9 bit 4 is set in heat mode while on, byte 3 bit 7 adds half a degree,
# and fan mode sends setpoint 0 (the raw field).
ELECTRA_AUX_LAYOUT = Layout(
    bytes.fromhex("c3000000000000000000000000"),
    {
        **{
            name: field
            for name, field in ELECTRA_AC_LAYOUT.fields.items()
            if name != "light_toggle"
        },
        "half_degree": Field.at(3, 7, 1),  # setpoint + 0.5 °C
        "heat_flag": Field.at(9, 4, 1),
        "button": Field.at(11, 0, 8),
    },
    Sum8(0, 12, 12),
)
ELECTRA_AUX_KEY = {"temp_up": 0x00, "temp_down": 0x01, "power": 0x05}


class ElectraAcDevice(Device):
    """Electra A/C (ELECTRA_AC, IRElectraAc): the power, mode, setpoint, fan,
    swings, turbo, quiet and clean are sent in full; the light is a toggle.

    As IRac::electra sends it:
    - the setpoint is sent in every mode, whole degrees;
    - an off message carries mode auto (IRac passes mode "off", which
      convertMode maps to kElectraAcAuto), with the target's other values;
    - iFeel, the sensor temperature and SensorUpdate are never set (the
      entity has neither).

    LightToggle: with ``previous`` it is kElectraAcLightToggleOn only when
    the light changes; this is the rule IRac::handleToggles applies to
    ELECTRA_AC when the IRac object has sent before (a persistent object).
    With ``previous=None`` it is on when the target's light is on, as a fresh
    IRac sends (its previous state is of protocol UNKNOWN, so handleToggles
    does nothing).

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_electra_ac_device.py): swing "on"
    and hswing "on" never reached C through the old glue (IRGHVAC.trans_swing
    and trans_hswing had no "on" key), so C sends kElectraAcSwingOff; the
    port sends kElectraAcSwingOn.
    """

    PROTOCOL = ELECTRA_AC
    LAYOUTS = (ELECTRA_AC_LAYOUT,)
    VARIANTS = ("aux",)
    capabilities = Capabilities(
        modes=("auto", "cool", "fan", "dry", "heat"),
        temperature=TemperatureRange(16.0, 32.0),
        fan=FAN_3,
        swing_v=SWING,
        swing_h=SWING,
        features={
            "light": ON_OFF,
            "cleaning": ON_OFF,
            "powerful": ON_OFF,
            "quiet": ON_OFF,
        },
    )

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        if variant is not None and variant not in self.VARIANTS:
            raise ValueError(f"unknown Electra A/C variant {variant!r}")
        self.variant = variant
        if variant == "aux":
            self.LAYOUTS = (ELECTRA_AUX_LAYOUT,)
            features = dict(self.capabilities.features)
            del features["light"]  # byte 11 is the key code
            self.capabilities = replace(
                self.capabilities,
                features=features,
                temperature=TemperatureRange(16.0, 32.0, (0, 5)),
            )

    def frames(self, previous, target, actions):
        if self.variant == "aux":
            return [Frame("main", bytes(self._aux(previous, target)))]
        feat = target.features
        if previous is None:
            light = feat["light"]
        else:
            light = feat["light"] != previous.features["light"]
        data = ELECTRA_AC_LAYOUT.build(
            power=target.power,
            mode=target.mode if target.power else "auto",
            temperature=int(target.temperature),
            fan=target.fan,
            swing_v=target.swing_v,
            swing_h=target.swing_h,
            quiet=feat["quiet"],
            turbo=feat["powerful"],
            clean=feat["cleaning"],
            light_toggle=(
                ELECTRA_AC_LIGHT_TOGGLE_ON if light else ELECTRA_AC_LIGHT_TOGGLE_OFF
            ),
        )
        return [Frame("main", bytes(data))]

    @staticmethod
    def _aux_key(previous, target):
        """The key an AUX remote reports for previous -> target: power when
        the power changes (or for an off without previous), the setpoint
        keys when it moves, else temp_up (the commonest captured value)."""
        if previous is None:
            return ELECTRA_AUX_KEY["temp_up" if target.power else "power"]
        if previous.power != target.power:
            return ELECTRA_AUX_KEY["power"]
        if target.temperature < previous.temperature:
            return ELECTRA_AUX_KEY["temp_down"]
        return ELECTRA_AUX_KEY["temp_up"]

    def _aux(self, previous, target):
        feat = target.features
        layout = ELECTRA_AUX_LAYOUT
        fan_mode = target.mode == "fan"
        data = layout.build(
            checksum=False,
            power=target.power,
            mode=target.mode,  # an off carries the last mode, as captured
            fan=target.fan,
            swing_v=target.swing_v,
            swing_h=target.swing_h,
            quiet=feat["quiet"],
            turbo=feat["powerful"],
            clean=feat["cleaning"],
            heat_flag=target.power and target.mode == "heat",
            button=self._aux_key(previous, target),
        )
        if fan_mode:
            layout.write_raw(data, "temperature", 0)
        else:
            half = round(target.temperature * 10) % 10 == 5
            layout.write_raw(data, "half_degree", int(half))
            layout.write_raw(
                data,
                "temperature",
                layout.fields["temperature"].to_int(
                    "temperature", int(target.temperature)
                ),
            )
        layout.checksum.apply(data)
        return data


ELECTRA_AC_MODELS = (  # electra plugin
    "Classic INV 17",
    "AXW12DCS",
    "YKR-M/003E remote",
    "generic",
)
ELECTRA_AC_AEG_MODELS = ("Chillflex Pro AXP26U338CW",)  # aeg plugin
ELECTRA_AC_AUX_MODELS = ("KFR-35GW/BpNFW=3", "YKR-T/011 remote")  # aux plugin
ELECTRA_AC_CENTEK_MODELS = ("SCT-65Q09", "YKR-P/002E remote")  # centek plugin
ELECTRA_AC_DELONGHI_MODELS = ("PAC EM90",)  # delonghi plugin
ELECTRA_AC_ELECTROLUX_MODELS = ("YKR-H/531E",)  # electrolux plugin
ELECTRA_AC_FRIGIDAIRE_MODELS = ("FGPC102AB1",)  # frigidaire plugin
ELECTRA_AC_SUBTROPIC_MODELS = ("SUB-07HN1_18Y", "YKR-H/102E remote")  # subtropic


# Now the match between models and objects
