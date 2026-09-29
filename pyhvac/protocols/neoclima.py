#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Neoclima AC IR commands.
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

from ..choices import FAN_3, ON_OFF, SWING
from ..device import Device
from ..fields import Field, Layout, Sum8
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import Capabilities, TemperatureRange

# --------------------------------------------------------------- Neoclima
# Layout from IRremoteESP8266's NeoclimaProtocol (ir_Neoclima.h): one
# 12-byte frame, each byte LSB first. IRsend::sendNeoclima: sendGeneric with
# kNeoclimaHdrMark/HdrSpace, kNeoclimaBitMark, kNeoclimaOneSpace/ZeroSpace,
# a kNeoclimaBitMark + kNeoclimaHdrSpace footer, then an extra
# kNeoclimaBitMark and kNeoclimaMinGap (kDefaultMessageGap). No repeat
# (kNeoclimaMinRepeat is kNoRepeat). Carrier 38 kHz (enableIROut(38)).

NEOCLIMA = Protocol(
    "neoclima",
    {
        "main": Section(
            # kNeoclimaBitMark, kNeoclimaZeroSpace, kNeoclimaOneSpace
            PulseDistance(537, 571, 1651),
            header=(6112, 7391),  # kNeoclimaHdrMark, kNeoclimaHdrSpace
            # sendGeneric's footer (kNeoclimaBitMark, kNeoclimaHdrSpace as its
            # gap), then sendNeoclima's extra footer mark.
            footer=(537, 7391, 537),
            gap=100000,  # kNeoclimaMinGap
        )
    },
    carrier=38000,
    # decodeNeoclima: _tolerance (25 %), mark excess 0.
    mark_excess=0,
)

NEOCLIMA_MIN_TEMP, NEOCLIMA_MAX_TEMP = 16, 32  # kNeoclimaMinTempC/MaxTempC
NEOCLIMA_MODE = {  # kNeoclima{Auto,Cool,Dry,Fan,Heat}
    "auto": 0b000,
    "cool": 0b001,
    "dry": 0b010,
    "fan": 0b011,
    "heat": 0b100,
}
NEOCLIMA_FAN = {  # kNeoclimaFan*: canonical "1" low .. "3" high
    "auto": 0b00,
    "3": 0b01,  # kNeoclimaFanHigh
    "2": 0b10,  # kNeoclimaFanMed
    "1": 0b11,  # kNeoclimaFanLow
}
NEOCLIMA_SWING_V = {"swing": 0b01, "off": 0b10}  # kNeoclimaSwingVOn/Off
NEOCLIMA_SWING_H = {"swing": 0, "off": 1}  # setSwingH: the bit is cleared when on
NEOCLIMA_BUTTON = {  # kNeoclimaButton*
    "power": 0x00,
    "mode": 0x01,
    "temp_up": 0x02,
    "temp_down": 0x03,
    "swing": 0x04,
    "fan_speed": 0x05,
    "air_flow": 0x07,
    "hold": 0x08,
    "sleep": 0x09,
    "turbo": 0x0A,
    "light": 0x0B,
    "econo": 0x0D,
    "eye": 0x0E,
    "follow": 0x13,
    "ion": 0x14,
    "fresh": 0x15,
    "8c_heat": 0x1D,
    "temp_unit": 0x1E,
}

# Skeleton: IRNeoclimaAc::stateReset's kReset (cool, 26C, fan low, swing_v
# off, swing_h on, power on, button power; byte 10 is 0xA5) and its Sum8.
# kReset lists 11 bytes and setRaw copies 12, but byte 11 is the checksum,
# which getRaw always rewrites: no stale byte reaches the wire. The unnamed
# bits are never written after stateReset.
NEOCLIMA_LAYOUT = Layout(
    bytes.fromhex("000000000000006a002aa539"),
    {
        "c_heat": Field.at(1, 1, 1),  # CHeat: 8C heat
        "ion": Field.at(1, 2, 1),
        "light": Field.at(3, 0, 1),
        "hold": Field.at(3, 2, 1),
        "turbo": Field.at(3, 3, 1),
        "econo": Field.at(3, 4, 1),
        "eye": Field.at(3, 6, 1),
        "button": Field.at(5, 0, 5, values=NEOCLIMA_BUTTON),
        "fresh": Field.at(5, 7, 1),
        "sleep": Field.at(7, 0, 1),
        "power": Field.at(7, 1, 1),
        "swing_v": Field.at(7, 2, 2, values=NEOCLIMA_SWING_V),
        "swing_h": Field.at(7, 4, 1, values=NEOCLIMA_SWING_H),
        "fan": Field.at(7, 5, 2, values=NEOCLIMA_FAN),
        "use_fah": Field.at(7, 7, 1),
        "follow": Field.at(8, 0, 8),
        "temp": Field.at(  # degrees - kNeoclimaMinTempC
            9,
            0,
            5,
            values={
                t: t - NEOCLIMA_MIN_TEMP
                for t in range(NEOCLIMA_MIN_TEMP, NEOCLIMA_MAX_TEMP + 1)
            },
        ),
        "mode": Field.at(9, 5, 3, values=NEOCLIMA_MODE),
    },
    checksum=Sum8(0, 11, 11),  # IRNeoclimaAc::calcChecksum: sumBytes(state, 11)
)


class NeoclimaDevice(Device):
    """Neoclima (NS-09AHTI, ZH/TY-01 remote, and the Soleus Air models): a
    full-state protocol, ``previous`` is ignored.

    IRac::neoclima builds every message on a fresh IRNeoclimaAc (stateReset)
    and calls setPower last, so the "pressed button" field always carries
    kNeoclimaButtonPower. The frame carries the whole state, so the port
    sends the same with or without ``previous``; there are no toggle bits.

    As the C path sends it:
    - an off message carries mode auto (convertMode's default for IRac's
      "off"), with the requested setpoint, fan and settings;
    - mode dry sends fan low whatever fan is asked (IRNeoclimaAc::setFan:
      "Dry mode only allows low speed"); mode fan (kNeoclimaFan) sends the
      setpoint and fan as asked;
    - the setpoint is sent in Celsius (UseFah clear), 16-32 C as setTemp
      clamps it (the entity's range);
    - hold, eye, fresh, 8C heat and follow me stay clear (IRac never sets
      them); powerful is Turbo, purifier is Ion, economy is Econo.

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_neoclima_device.py):
    - swing_v and swing_h "swing": the old glue (IRGHVAC.trans_swing /
      trans_hswing) has no "on", so IRac passed kOff; the port sends
      kNeoclimaSwingVOn and clears the SwingH bit;
    - sleep: the old glue never passes sleep, so setSleep(sleep >= 0) always
      cleared the Sleep bit; the port sets it.
    """

    PROTOCOL = NEOCLIMA
    LAYOUTS = (NEOCLIMA_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "fan", "heat"),  # kNeoclima{Auto,..,Heat}
        temperature=TemperatureRange(16.0, 32.0),
        fan=FAN_3,
        swing_v=SWING,
        swing_h=SWING,
        features={
            "sleep": ON_OFF,
            "powerful": ON_OFF,
            "purifier": ON_OFF,
            "economy": ON_OFF,
            "light": ON_OFF,
        },
    )

    def frames(self, previous, target, actions):
        mode = target.mode if target.power else "auto"
        features = target.features
        data = NEOCLIMA_LAYOUT.build(
            button="power",
            power=target.power,
            mode=mode,
            temp=int(target.temperature),
            fan="1" if mode == "dry" else target.fan,
            swing_v=target.swing_v,
            swing_h=target.swing_h,
            sleep=features["sleep"],
            turbo=features["powerful"],
            ion=features["purifier"],
            econo=features["economy"],
            light=features["light"],
        )
        return [Frame("main", bytes(data))]


NEOCLIMA_MODELS = ("NS-09AHTI", "ZH/TY-01 remote", "generic")  # neoclima plugin
NEOCLIMA_SOLEUS_MODELS = ("Air TTWM1-10-01", "Air ZCF/TL-05 remote")  # soleus plugin


# Now the match between models and objects
