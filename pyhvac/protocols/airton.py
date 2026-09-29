#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Airton AC IR commands
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


from ..device import Device
from ..fields import Field, Layout, Sum8
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_5, ON_OFF, SWING
from ..state import Capabilities, TemperatureRange

# ----------------------------------------------------------------- Airton
# Layout from IRremoteESP8266's AirtonProtocol (ir_Airton.h): one 56-bit word
# sent LSB first by sendAirton, i.e. 7 bytes in order, each LSB first, with a
# kAirtonHdrMark/HdrSpace header, a kAirtonBitMark footer and
# kDefaultMessageGap after it.

AIRTON = Protocol(
    "airton",
    {
        "main": Section(
            PulseDistance(400, 430, 1260),  # kAirtonBitMark/ZeroSpace/OneSpace
            header=(6630, 3350),  # kAirtonHdrMark/HdrSpace
            footer=(400,),  # kAirtonBitMark
            gap=100000,  # kDefaultMessageGap
        )
    },
    carrier=38000,  # kAirtonFreq
)


# Skeleton: stateReset writes the header (0x11D3) and clears every other
# bit, so the unused bits of bytes 3, 4 and 5 are always 0.
AIRTON_LAYOUT = Layout(
    bytes.fromhex("d3110000000000"),
    {
        "mode": Field.at(  # kAirton{Auto,Cool,Dry,Fan,Heat}
            2, 0, 3, values={"auto": 0, "cool": 1, "dry": 2, "fan": 3, "heat": 4}
        ),
        "power": Field.at(2, 3, 1),
        "fan": Field.at(  # kAirtonFan{Auto,Min,Low,Med,High,Max}
            2, 4, 3, values={"auto": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5}
        ),
        "turbo": Field.at(2, 7, 1),
        "temperature": Field.at(  # degrees - kAirtonMinTemp
            3, 0, 4, values={t: t - 16 for t in range(16, 32)}
        ),
        "swing_v": Field.at(4, 0, 1),
        "econo": Field.at(5, 0, 1),
        "sleep": Field.at(5, 1, 1),
        "not_auto_on": Field.at(5, 2, 1),
        # Unknown / Unused: stays 0 in the C output, but is set (with
        # NotAutoOn clear) in the real light captures of ir_Airton_test.cpp.
        "unknown5_3": Field.at(5, 3, 1),
        "heat_on": Field.at(5, 4, 1),
        "health": Field.at(5, 6, 1),
        "light": Field.at(5, 7, 1),
    },
    # IRAirtonAc::calcChecksum: (0x7F - sum) ^ 0x2C
    Sum8(0, 6, 6, base=0x7F, xor=0x2C),
)

# The temperature IRAirtonAc::setTemp forces in mode auto (kAirtonMaxTemp).
AIRTON_AUTO_TEMPERATURE = 31


class AirtonDevice(Device):
    """Airton: one 56-bit state message, no toggles (``previous`` is
    ignored).

    As IRac::airton sends it:
    - an off message carries mode auto (the glue sends opmode kOff, which
      convertMode maps to kAirtonAuto), and hence auto's rules;
    - mode auto sends 31 °C whatever the setpoint (setTemp forces
      kAirtonMaxTemp), and sets NotAutoOn only when powered off; every other
      mode sets NotAutoOn;
    - HeatOn is set in heat when powered on;
    - economy is sent in cool only (setEcono);
    - powerful sets Turbo and forces the fan to kAirtonFanMax (setTurbo);
    - purifier is the Health bit;
    - sleep is the Sleep bit, cleared in auto and fan (setSleep: "Sleep not
      available in fan or auto mode"), and so in off messages too.

    The setpoint is kAirtonMinTemp..kAirtonMaxTemp (16-31 °C). Quiet is not
    offered: the header has no quiet bit ("No Quiet setting available").

    The real light captures in ir_Airton_test.cpp clear NotAutoOn and set
    the unknown bit 5.3 in cool and dry; the port follows the C path there.

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_airton_device.py): the old glue's
    trans_swing has no "on" key, so swing "on" never reached C; the port sets
    SwingV.
    """

    PROTOCOL = AIRTON
    LAYOUTS = (AIRTON_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "fan", "dry", "heat"),
        temperature=TemperatureRange(16.0, 31.0),  # kAirtonMinTemp..MaxTemp
        fan=FAN_5,
        swing_v=SWING,
        features={
            "purifier": ON_OFF,
            "powerful": ON_OFF,
            "economy": ON_OFF,
            "light": ON_OFF,
            "sleep": ON_OFF,
        },
    )

    def frames(self, previous, target, actions):
        power = target.power
        mode = target.mode if power else "auto"
        features = target.features
        powerful = features["powerful"]
        data = AIRTON_LAYOUT.build(
            mode=mode,
            power=power,
            fan="5" if powerful else target.fan,
            turbo=powerful,
            temperature=(
                AIRTON_AUTO_TEMPERATURE if mode == "auto" else int(target.temperature)
            ),
            swing_v=target.swing_v != "off",
            econo=features["economy"] and mode == "cool",
            # IRAirtonAc::setSleep: not available in fan or auto mode.
            sleep=features.get("sleep", False) and mode not in ("auto", "fan"),
            not_auto_on=mode != "auto" or not power,
            heat_on=mode == "heat" and power,
            health=features["purifier"],
            light=features["light"],
        )
        return [Frame("main", bytes(data))]


AIRTON_MODELS = ("SMVH09B-2A2A3NH", "RD1A1", "generic")


# Now the match between models and objects
