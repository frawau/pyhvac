#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Coolix AC IR commands.
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

from dataclasses import replace

from ..device import Device
from ..fields import Field, InvertedPairs, Layout
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_3, ON_OFF, SWING
from ..state import Capabilities, TemperatureRange

# --------------------------------------------------------------------- Coolix
# IRremoteESP8266's CoolixProtocol (ir_Coolix.h): a 24-bit word. Every
# message IRac::coolix sends is one such word or a sequence of them: a state
# word (mode, setpoint, fan) or a fixed command word (kCoolixOff, and the
# kCoolixSwing/Turbo/Led/Clean toggles). IRsend::sendCOOLIX sends the word
# most significant byte first, each byte MSB first and followed by its
# complement, so the logical frame is 6 bytes:
#   byte 0: raw bits 16-23 (bits 0-2 unnamed, ZoneFollow2 bit 3, fixed 0xB)
#   byte 1: ~byte 0
#   byte 2: raw bits 8-15 (SensorTemp bits 0-4, Fan bits 5-7)
#   byte 3: ~byte 2
#   byte 4: raw bits 0-7 (bit 0 unnamed, ZoneFollow1 bit 1, Mode bits 2-3,
#           Temp bits 4-7)
#   byte 5: ~byte 4
# Each frame is the kCoolixHdrMark/HdrSpace header, the 48 bits, a
# kCoolixBitMark footer and space(kCoolixMinGap). IRCoolixAC::send uses
# kCoolixDefaultRepeat (one repeat), so every word goes out twice: "main",
# then "repeat", after whose kCoolixMinGap sendCOOLIX adds
# space(kDefaultMessageGap); the two spaces are one on the wire (as
# ir_Coolix_test.cpp's SendWithRepeats shows: "m552s105244"). A decoder
# gap is a minimum that takes the whole space, so the repeat carries the
# merged gap rather than a bitless end section, which could not be decoded
# before the next word of a multi-word message.

_COOLIX_BITS = dict(
    # kCoolixBitMark/ZeroSpace/OneSpace
    bits=PulseDistance(552, 552, 1656),
    header=(4692, 4416),  # kCoolixHdrMark/HdrSpace
    footer=(552,),  # kCoolixBitMark
    lsb_first=False,
)
COOLIX = Protocol(
    "coolix",
    {
        "main": Section(gap=5244, **_COOLIX_BITS),  # kCoolixMinGap
        # kCoolixMinGap + kDefaultMessageGap
        "repeat": Section(gap=5244 + 100000, **_COOLIX_BITS),
    },
    carrier=38000,  # enableIROut(38)
    # decodeCOOLIX matches the bits with kTolerance + kCoolixExtraTolerance
    # (25 + 5 %) and mark excess 0 (header and footer with the defaults).
    tolerance=0.30,
    mark_excess=0,
)


COOLIX_MIN_TEMP, COOLIX_MAX_TEMP = 17, 30  # kCoolixTempMin/Max
COOLIX_TEMP_MAP = (  # kCoolixTempMap, 17 C to 30 C
    0b0000,
    0b0001,
    0b0011,
    0b0010,
    0b0110,
    0b0111,
    0b0101,
    0b0100,
    0b1100,
    0b1101,
    0b1001,
    0b1000,
    0b1010,
    0b1011,
)
COOLIX_FAN_TEMP_CODE = 0b1110  # kCoolixFanTempCode: "Part of Fan Mode"
COOLIX_TEMP = {
    **{COOLIX_MIN_TEMP + i: code for i, code in enumerate(COOLIX_TEMP_MAP)},
    "fan": COOLIX_FAN_TEMP_CODE,
}
COOLIX_MODE = {  # kCoolix{Cool,Dry,Auto,Heat}; fan mode is Dry + Temp
    "cool": 0b00,
    "dry": 0b01,
    "auto": 0b10,
    "heat": 0b11,
}
COOLIX_FAN = {  # kCoolixFan*
    "auto": 0b101,  # kCoolixFanAuto: cool, heat and fan modes
    "auto0": 0b000,  # kCoolixFanAuto0: auto and dry modes
    "1": 0b100,  # kCoolixFanMin (convertFan: kLow)
    "2": 0b010,  # kCoolixFanMed (kMedium)
    "3": 0b001,  # kCoolixFanMax (kHigh)
}
COOLIX_AUTO0_MODES = ("auto", "dry")  # setFan: "Only Dry & Auto mode can have"
COOLIX_SENSOR_TEMP_IGNORE = 0b11111  # kCoolixSensorTempIgnoreCode
COOLIX_DEFAULT_STATE = 0xB21FC8  # kCoolixDefaultState
COOLIX_OFF = 0xB27BE0  # kCoolixOff
COOLIX_SWING = 0xB26BE0  # kCoolixSwing: a swing toggle
COOLIX_TURBO = 0xB5F5A2  # kCoolixTurbo: a turbo toggle
COOLIX_LED = 0xB5F5A5  # kCoolixLed: a light toggle
COOLIX_CLEAN = 0xB5F5AA  # kCoolixClean: a clean toggle
# Not in ir_Coolix.h: SmartIR climate 1740 (Kelvinator KSV25HRG) sends this
# word alone under its "silent" fan label; read as a quiet toggle.
COOLIX_QUIET = 0xB5F5B6
# The toggle words IRac::coolix sends after the state word, in its order
# (IRac::coolix's kCoolixSleep word is not sent: sleep is deferred, it needs
# its own word).
COOLIX_TOGGLES = (
    ("powerful", COOLIX_TURBO),
    ("light", COOLIX_LED),
    ("cleaning", COOLIX_CLEAN),
)


def coolix_word(raw):
    """The logical bytes of a 24-bit Coolix word: each byte, most
    significant first, followed by its complement."""
    out = bytearray()
    for byte in raw.to_bytes(3, "big"):
        out += bytes([byte, ~byte & 0xFF])
    return bytes(out)


# Skeleton: kCoolixDefaultState, which IRCoolixAC::stateReset loads; no
# setter writes the unnamed bits or the fixed 0xB nibble, so they keep its
# values. The command words are fixed constants that read through it too.
COOLIX_LAYOUT = Layout(
    coolix_word(COOLIX_DEFAULT_STATE),
    {
        "zone_follow2": Field.at(0, 3, 1),
        "sensor_temp": Field.at(2, 0, 5),
        "fan": Field.at(2, 5, 3, values=COOLIX_FAN),
        "zone_follow1": Field.at(4, 1, 1),
        "mode": Field.at(4, 2, 2, values=COOLIX_MODE),
        "temp": Field.at(4, 4, 4, values=COOLIX_TEMP),
    },
    checksum=InvertedPairs(0, 6),
)


def coolix_message(raw):
    """One word as IRCoolixAC::send puts it on the wire: sent, then
    repeated."""
    word = coolix_word(raw) if isinstance(raw, int) else bytes(raw)
    return [Frame("main", word), Frame("repeat", word)]


class CoolixDevice(Device):
    """Coolix A/C (IRCoolixAC): a state word (mode, setpoint, fan) and fixed
    command words, each sent twice.

    As IRac::coolix sends it:
    - power off sends kCoolixOff alone, whatever the other settings (no
      toggle word goes with it);
    - otherwise the state word: the setpoint through kCoolixTempMap, fan
      mode as Dry with kCoolixFanTempCode, fan auto as kCoolixFanAuto0 in
      auto and dry modes and kCoolixFanAuto otherwise (IRCoolixAC::setFan's
      mode check), SensorTemp kCoolixSensorTempIgnoreCode and Zone Follow
      off (IRac passes no sensor temperature and iFeel off);
    - then a toggle word per feature, in IRac::coolix's order: kCoolixSwing
      (swing_v or swing_h), kCoolixTurbo (powerful), kCoolixLed (light),
      kCoolixClean (cleaning);
    - there is no quiet (IRac::coolix: "No Quiet setting available"; the
      header has no quiet word).

    The toggle words: with ``previous=None`` each is sent when its feature
    is on, as from a fresh IRac (its previous state is of protocol UNKNOWN,
    so IRac::handleToggles changes nothing). With ``previous`` each is sent
    when its feature changed (IRac::handleToggles' COOLIX rule, which a
    persistent IRac applies; the previous value counts even when the
    previous message was an off). The one swing word serves both swing
    axes: it is sent when "swinging" (swing_v or swing_h not off) changed.
    For swing_v this is handleToggles' rule; handleToggles leaves swingh
    alone, so a persistent IRac sends kCoolixSwing on every message while
    swing_h is on, toggling the swing each time: the port deliberately
    deviates there.

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_coolix_device.py): the old glue
    never passes swing "on" or swing_h "on" to C, so C never sends
    kCoolixSwing. The port sends the documented toggle word.
    """

    PROTOCOL = COOLIX
    # One layout per frame of a single-word message (the word and its
    # repeat); a multi-word message has the same layout for every frame.
    LAYOUTS = (COOLIX_LAYOUT, COOLIX_LAYOUT)
    capabilities = Capabilities(
        modes=("cool", "dry", "auto", "heat", "fan"),
        temperature=TemperatureRange(17.0, 30.0),
        fan=FAN_3,
        swing_v=SWING,
        swing_h=SWING,
        features={
            "powerful": ON_OFF,
            "cleaning": ON_OFF,
            "light": ON_OFF,
        },
    )

    @staticmethod
    def _swinging(state):
        return state.swing_v != "off" or state.swing_h != "off"

    # Variants beyond IRremoteESP8266, each from SmartIR captures:
    # - "16C" (climate 1941/1943, Electra): 16 °C in heat and cool, sent
    #   with kCoolixFanTempCode as the setpoint; cool at 16 °C carries the
    #   auto mode bits, as captured. Other modes send 17 °C at 16 °C.
    # - "quiet" (climate 1740, Kelvinator KSV25HRG): a quiet feature, the
    #   COOLIX_QUIET toggle word after the other toggles.
    VARIANTS = ("16C", "quiet")

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        if variant is None:  # built directly: the brands table's variant
            from ..registry import variant_of

            variant = variant_of(type(self), brand, model)
        if variant is not None and variant not in self.VARIANTS:
            raise ValueError(f"unknown Coolix variant {variant!r}")
        self.variant = variant
        self.toggles = COOLIX_TOGGLES
        if variant == "16C":
            self.capabilities = replace(
                self.capabilities, temperature=TemperatureRange(16.0, 30.0)
            )
        elif variant == "quiet":
            self.capabilities = replace(
                self.capabilities,
                features={**self.capabilities.features, "quiet": ON_OFF},
            )
            self.toggles = COOLIX_TOGGLES + (("quiet", COOLIX_QUIET),)

    def frames(self, previous, target, actions):
        if not target.power:
            return coolix_message(COOLIX_OFF)
        mode = target.mode
        fan = target.fan
        if fan == "auto" and mode in COOLIX_AUTO0_MODES:
            fan = "auto0"
        if mode == "fan":
            mode, temp = "dry", "fan"
        elif self.variant == "16C" and int(target.temperature) < COOLIX_MIN_TEMP:
            if mode in ("heat", "cool"):
                mode = "heat" if mode == "heat" else "auto"
                temp = "fan"  # the code SmartIR 1941/1943 send for 16 °C
            else:
                temp = COOLIX_MIN_TEMP
        else:
            temp = min(max(int(target.temperature), COOLIX_MIN_TEMP), COOLIX_MAX_TEMP)
        state = COOLIX_LAYOUT.build(
            fan=fan,
            temp=temp,
            mode=mode,
            sensor_temp=COOLIX_SENSOR_TEMP_IGNORE,
            zone_follow1=0,
            zone_follow2=0,
        )
        frames = coolix_message(state)
        was_swinging = previous is not None and self._swinging(previous)
        if self._swinging(target) != was_swinging:
            frames += coolix_message(COOLIX_SWING)
        for feature, word in self.toggles:
            was_on = previous is not None and previous.features[feature]
            if target.features[feature] != was_on:
                frames += coolix_message(word)
        return frames


COOLIX_MODELS = ("generic",)  # coolix plugin
COOLIX_AIRWELL_MODELS = ("RC08B remote",)  # airwell plugin
COOLIX_BEKO_MODELS = ("RG57K7(B)/BGEF Remote", "BINR 070/071")  # beko plugin
COOLIX_BOSCH_MODELS = (  # bosch plugin
    "RG36B4/BGE remote",
    "B1ZAI2441W",
    "B1ZAO2441W",
)
COOLIX_KASTRON_MODELS = ("RG57A7/BGEF remote",)  # kastron plugin
COOLIX_KAYSUN_MODELS = ("Casual CF Alt",)  # kaysun plugin
COOLIX_MIDEA_MODELS = (  # midea plugin
    "RG52D/BGE Remote",
    "MS12FU-10HRDN1-QRD0GW(B)",
    "MSABAU-07HRFN1-QRD0GW",
)
COOLIX_TOKIO_MODELS = ("AATOEMF17-12CHR1SW", "RG51|50/BGE Remote")  # tokio
COOLIX_TOSHIBA_MODELS = (  # toshiba plugin
    "RAS-M10YKV-E",
    "RAS-M13YKV-E",
    "RAS-4M27YAV-E",
    "WH-E1YE remote",
)


# Now the match between models and objects
