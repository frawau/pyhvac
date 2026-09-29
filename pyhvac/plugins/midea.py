#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Midea AC IR commands.
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
from .coolix import COOLIX_MIDEA_MODELS, Coolix, CoolixDevice
from ..device import Device
from ..fields import Checksum, Checksums, Copy, Field, Joined, Layout, bit_reverse
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_3, ON_OFF, SWING
from ..state import Capabilities, TemperatureRange


class Midea(PulseBased):

    STARTFRAME = [4480, 4480]
    ENDFRAME = [560, 5600]
    MARK = [560]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [560, 1680]  # ditto

    def __init__(self):
        super().__init__("MIDEA")
        self.capabilities = {
            "mode": ["off", "auto", "cool", "fan", "dry", "heat"],
            "temperature": [17, 30],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "powerful": ["off", "on"],
            "quiet": ["off", "on"],
            "economy": ["off", "on"],
            "light": ["off", "on"],
            "cleaning": ["off", "on"],
            "sleep": ["off", "on"],
        }


DEVICES = {}
DEVICES.update({m: CoolixDevice for m in COOLIX_MIDEA_MODELS})


# ---------------------------------------------------------------- Midea
# Layout from IRremoteESP8266's MideaProtocol (ir_Midea.h): one 48-bit state
# (kMideaBits), a uint64_t whose bytes IRsend::sendMidea sends most
# significant first, each byte MSB first, at 38 kHz: kMideaHdrMark/HdrSpace,
# kMideaBitMark with kMideaOneSpace/ZeroSpace, a kMideaBitMark footer and a
# kMideaMinGap space; then the whole message again, every bit inverted, and
# kDefaultMessageGap more (kMideaMinRepeat is kNoRepeat). A frame's data is
# the state in wire order: data[0] is the struct's byte 5 (Header, Type),
# data[5] its byte 0 (Sum).
#
# Toggle settings are separate "special" messages (Type kMideaACTypeSpecial),
# each a fixed kMideaAC* 48-bit code, sent the same way after the state:
# IRMideaAC::send sends swing, econo, turbo, light, clean, then quiet on/off.

MIDEA_BITS = PulseDistance(560, 560, 1680)  # kMideaBitMark/ZeroSpace/OneSpace
MIDEA_HEADER = (4480, 4480)  # kMideaHdrMark/HdrSpace
MIDEA_GAP = 5600  # kMideaMinGap
MIDEA_END_GAP = MIDEA_GAP + 100000  # kMideaMinGap, then kDefaultMessageGap


def _midea_section(gap):
    return Section(
        MIDEA_BITS, header=MIDEA_HEADER, footer=(560,), gap=gap, lsb_first=False
    )


MIDEA = Protocol(
    "midea",
    {
        "state": _midea_section(MIDEA_GAP),
        "state_inverted": _midea_section(MIDEA_END_GAP),
        "special": _midea_section(MIDEA_GAP),
        "special_inverted": _midea_section(MIDEA_END_GAP),
    },
    carrier=38000,
)


@dataclass(frozen=True)
class MideaChecksum(Checksum):
    """IRMideaAC::calcChecksum: the bit-reversed bytes of data[start:end]
    summed, negated mod 256, and bit-reversed back (use reverse=True)."""

    def compute(self, data):
        return bit_reverse(-sum(self._input(data)) & 0xFF)


# A message and its inverted copy, as one 12-byte Joined layout: the sum over
# the state's first five bytes, then the copy complemented.
MIDEA_CHECKSUM = Checksums(MideaChecksum(0, 5, 5, reverse=True), Copy(0, 6, 6, True))
MIDEA_TYPE = {"command": 0b001, "special": 0b010, "follow": 0b100}  # kMideaACType*
MIDEA_MIN = 17  # kMideaACMinTempC
MIDEA_MAX = 30  # kMideaACMaxTempC

# Skeleton: IRMideaAC::stateReset's 0xA1826FFFFF62 as IRac::midea leaves it
# (setUseCelsius(true), setEnableSensorTemp(false)), with the fields the device
# always writes and the sums cleared; stateReset writes every bit, so nothing
# comes from stale memory. The two unnamed bits after useFahrenheit (data[2]
# bits 6-7) keep the reset 0b01, and data[3] bit 0 its 1.
MIDEA_LAYOUT = Layout(
    bytes([0xA0, 0x00, 0x40, 0xFF, 0xFF, 0x00]) + bytes(6),
    {
        "type": Field.at(0, 0, 3, values=MIDEA_TYPE),
        "mode": Field.at(  # kMideaAC{Cool,Dry,Auto,Heat,Fan}
            1, 0, 3, values={"cool": 0, "dry": 1, "auto": 2, "heat": 3, "fan": 4}
        ),
        "fan": Field.at(  # kMideaACFan{Auto,Low,Med,High}
            1, 3, 2, values={"auto": 0, "1": 1, "2": 2, "3": 3}
        ),
        "unknown": Field.at(1, 5, 1),  # set on some Pioneer System units
        "sleep": Field.at(1, 6, 1),
        "power": Field.at(1, 7, 1),
        "temperature": Field.at(  # degrees - kMideaACMinTempC (setTemp)
            2, 0, 5, values={t: t - MIDEA_MIN for t in range(MIDEA_MIN, MIDEA_MAX + 1)}
        ),
        "fahrenheit": Field.at(2, 5, 1),  # useFahrenheit
        "off_timer": Field.at(3, 1, 6),  # kMideaACTimerOff: off
        "beep_disable": Field.at(3, 7, 1),
        "sensor_temp": Field.at(4, 0, 7),  # kMideaACSensorTempOnTimerOff: off
        "disable_sensor": Field.at(4, 7, 1),
    },
    MIDEA_CHECKSUM,
)

# The special messages: byte 4 of each documented code (kMideaACToggleSwingV,
# kMideaACToggleEcono, kMideaACToggleTurbo, kMideaACToggleLight,
# kMideaACToggleSelfClean, kMideaACToggle8CHeat, kMideaACQuietOn/Off), whose
# other bytes are 0xA2, then 0xFF 0xFF 0xFF, then the sum.
MIDEA_COMMAND = {
    "swing": 0x01,
    "econo": 0x02,
    "light": 0x08,
    "turbo": 0x09,
    "clean": 0x0D,
    "8c_heat": 0x0F,
    "quiet_on": 0x12,
    "quiet_off": 0x13,
}
MIDEA_SPECIAL_LAYOUT = Layout(
    bytes([0xA0, 0x00, 0xFF, 0xFF, 0xFF, 0x00]) + bytes(6),
    {
        "type": Field.at(0, 0, 3, values=MIDEA_TYPE),
        "command": Field.at(1, 0, 8, values=MIDEA_COMMAND),
    },
    MIDEA_CHECKSUM,
)


def _midea_pair(name, layout, **values):
    data = bytes(layout.build(**values))
    return [Frame(name, data[:6]), Frame(f"{name}_inverted", data[6:])]


class MideaDevice(Device):
    """Midea 48-bit (MIDEA): the state message, then one special message per
    toggle to send, each followed by its inverted copy.

    As IRac::midea sends it, the state carries power, mode, setpoint (Celsius),
    fan and sleep; an off message carries mode auto (IRac passes mode "off",
    which convertMode maps to its default, kMideaACAuto); IRac leaves the
    sensor temperature (follow me) and the timers off.

    Swing, economy, powerful (turbo), light and cleaning are toggles, and quiet
    has its own on and off messages. With ``previous``, a toggle is sent when
    its setting changes and quiet when quiet changes, as IRac::handleToggles
    and IRac::sendAc's prev_quiet do for a persistent IRac. With
    ``previous=None`` the port sends what a fresh IRac sends: every toggle
    that is on, and quiet on (a fresh IRac's last quiet is off). Cleaning is
    only sent in cool, dry and auto (setCleanToggle; an off message counts as
    auto). 8C heat is not in the entity.

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_midea_device.py):
    - swing: the old glue has no swing "on", so IRac's swingv stays kOff and
      the swing toggle is never sent; the port sends kMideaACToggleSwingV;
    - sleep: the old glue never passes sleep, so setSleep(false); the port
      sets Sleep.
    """

    PROTOCOL = MIDEA
    LAYOUTS = (Joined(MIDEA_LAYOUT, 2),)
    capabilities = Capabilities(
        modes=("auto", "cool", "fan", "dry", "heat"),
        temperature=TemperatureRange(float(MIDEA_MIN), float(MIDEA_MAX)),
        fan=FAN_3,
        swing_v=SWING,
        features={
            "powerful": ON_OFF,
            "quiet": ON_OFF,
            "economy": ON_OFF,
            "light": ON_OFF,
            "cleaning": ON_OFF,
            "sleep": ON_OFF,
        },
    )

    @staticmethod
    def layouts(frames):
        """One Joined layout per message pair: the state, then the specials."""
        special = Joined(MIDEA_SPECIAL_LAYOUT, 2)
        return (Joined(MIDEA_LAYOUT, 2),) + (special,) * (len(frames) // 2 - 1)

    @staticmethod
    def specials(previous, target):
        """The special messages to send after the state, in IRMideaAC::send's
        order."""
        mode = target.mode if target.power else "auto"

        def toggled(settings):
            now = settings(target)
            return now if previous is None else now != settings(previous)

        out = []
        toggles = (
            ("swing", lambda s: s.swing_v != "off"),
            ("econo", lambda s: s.features["economy"]),
            ("turbo", lambda s: s.features["powerful"]),
            ("light", lambda s: s.features["light"]),
            ("clean", lambda s: s.features["cleaning"]),
        )
        for command, settings in toggles:
            if command == "clean" and mode not in ("cool", "dry", "auto"):
                continue  # setCleanToggle: only in cool, dry or auto
            if toggled(settings):
                out.append(command)
        quiet = target.features["quiet"]
        if toggled(lambda s: s.features["quiet"]):
            out.append("quiet_on" if quiet else "quiet_off")
        return out

    def frames(self, previous, target, actions):
        out = _midea_pair(
            "state",
            MIDEA_LAYOUT,
            type="command",
            power=target.power,
            mode=target.mode if target.power else "auto",
            fan=target.fan,
            sleep=target.features["sleep"],
            temperature=min(max(int(target.temperature), MIDEA_MIN), MIDEA_MAX),
        )
        for command in self.specials(previous, target):
            out += _midea_pair(
                "special", MIDEA_SPECIAL_LAYOUT, type="special", command=command
            )
        return out


MIDEA_MODELS = ("generic",)  # midea plugin
MIDEA_COMFEE_MODELS = ("MPD1-12CRN7",)  # comfee plugin
MIDEA_DANBY_MODELS = (  # danby plugin
    "DAC080BGUWDB",
    "DAC100BGUWDB",
    "DAC120BGUWDB",
    "R09C/BCGE remote",
)
MIDEA_KAYSUN_MODELS = ("Casual CF",)  # kaysun plugin
MIDEA_KEYSTONE_MODELS = ("RG57H4(B)BGEF remote",)  # keystone plugin
MIDEA_LENNOX_MODELS = (  # lennox plugin
    "RG57A6/BGEFU1 remote",
    "MWMA009S4-3P",
    "MWMA012S4-3P",
    "MCFA",
    "MCFB",
    "MMDA",
    "MMDB",
    "MWMA",
    "MWMB",
    "M22A",
    "M33A",
    "M33B",
)
MIDEA_MRCOOL_MODELS = ("RG57A6/BGEFU1 remote",)  # mrcool plugin
MIDEA_PIONEER_SYSTEM_MODELS = (  # pioneer_system plugin
    "RYBO12GMFILCAD",
    "RUBO18GMFILCAD",
    "WS012GMFI22HLD",
    "WS018GMFI22HLD",
    "UB018GMFILCFHD",
    "RG66B6(B)/BGEFU1 remote",
)
MIDEA_TROTECH_MODELS = (  # trotech plugin
    "PAC 2100 X",
    "PAC 3900 X",
    "RG57H(B)/BGE remote",
    "RG57H3(B)/BGCEF-M remote",
)


DEVICES.update({m: MideaDevice for m in MIDEA_MODELS})


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "generic": Midea,
        "RG52D/BGE Remote": Coolix,
        "MS12FU-10HRDN1-QRD0GW(B)": Coolix,
        "MSABAU-07HRFN1-QRD0GW": Coolix,
    }

    def __init__(self):
        self.brand = "midea"
