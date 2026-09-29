#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Airspool (Tuya-style mini-split) AC IR commands.
#
# Protocol reverse-engineered and documented at:
#   https://twosortoftechguys.wordpress.com/2026/06/14/sending-ir-codes-to-an-airspool-mini-split-using-a-raspberry-pi-ai-failed-us-2/
#
# Several fields are only partially understood; they are flagged UNVERIFIED /
# UNKNOWN in the code below and should not be trusted blindly.
#
# Copyright (c) 2026 François Wautier
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

from ..device import Device
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import BOOL, Capabilities, Choice, TemperatureRange

# Physical layer: 38 kHz, pulse-distance, LSB-first within each byte.
AIRSPOOL = Protocol(
    "airspool",
    {
        "main": Section(
            PulseDistance(480, 360, 1180),
            header=(3200, 1400),
            # Final stop mark, then a long trailing gap before any repeat.  The
            # exact gap length is not part of the documented capture; 100 ms is
            # a safe value.
            footer=(480,),
            gap=100_000,
            lsb_first=True,
        )
    },
)


# --------------------------------------------------------------- Device API

# Canonical fan level -> airflow enum (byte 8, bits 0-2); see Airspool.FAN_ENUM.
AIRSPOOL_FAN = {"auto": 0, "1": 2, "2": 4, "3": 3, "4": 6, "5": 5}
# From the 0.1.x Airspool class: the frame body (FBODY), the mode nibbles
# (MODE_NIBBLE) and the sleep fan value (SLEEP_ENUM).
AIRSPOOL_BODY = b"\x23\xcb\x26\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00"
AIRSPOOL_MODE_NIBBLE = {"heat": 0x01, "dry": 0x02, "cool": 0x03}
AIRSPOOL_SLEEP_ENUM = 1


def airspool_c_to_f(temp_c):
    """Airspool.c_to_f: the unit is °F-native; the nearest whole °F."""
    return round(temp_c * 9 / 5 + 32)


class AirspoolDevice(Device):
    """Stateless Airspool device: a full-state protocol, previous is ignored."""

    PROTOCOL = AIRSPOOL
    capabilities = Capabilities(
        modes=("cool", "dry", "heat"),
        temperature=TemperatureRange(16.0, 30.0, (0, 5)),
        fan=Choice(
            ("auto", "1", "2", "3", "4", "5"),
            {"1": "fan1", "2": "fan2", "3": "fan3", "4": "fan4", "5": "fan5"},
        ),
        swing_v=Choice(("off", "swing")),
        swing_h=Choice(("off", "swing")),
        features={
            "sleep": BOOL,
            "powerful": BOOL,
            "light": Choice((True, False)),  # display on by default
            "power_limit": BOOL,
        },
        actions={"se_step": "SE speed step"},
    )

    def frames(self, previous, target, actions):
        body = bytearray(AIRSPOOL_BODY)
        feat = target.features
        temp_f = airspool_c_to_f(target.temperature)
        body[4] = ((temp_f // 10) << 4) | (temp_f % 10)
        if target.power:
            body[5] |= 0x04
        if feat["power_limit"]:
            body[5] |= 0x80
        if feat["powerful"]:
            body[5] |= 0x40
            body[8] |= 0x40
        body[6] |= AIRSPOOL_MODE_NIBBLE[target.mode]
        if target.mode == "heat":
            body[6] |= 0xE0
        if feat["light"]:
            body[6] |= 0x20
        if "se_step" in actions:
            body[6] |= 0x40
        body[8] |= AIRSPOOL_SLEEP_ENUM if feat["sleep"] else AIRSPOOL_FAN[target.fan]
        if target.swing_v == "swing":
            body[8] |= 0x38
        if target.swing_h != "swing":
            body[11] |= 0xE0
        body.append(sum(body) & 0xFF)
        return [Frame("main", bytes(body))]
