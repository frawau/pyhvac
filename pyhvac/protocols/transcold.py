#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Transcold AC IR commands.
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
from ..fields import Field, InvertedPairs, Layout
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_3, SWING
from ..state import Capabilities, TemperatureRange

# ------------------------------------------------------------------ Transcold
# IRremoteESP8266's TranscoldProtocol (ir_Transcold.h): a 24-bit word.
# IRsend::sendTranscold sends it most significant byte first, each byte MSB
# first and followed by its complement, so the logical frame is 6 bytes:
#   byte 0: raw bits 16-23 (Fan in bits 0-3, bits 4-7 unnamed)
#   byte 1: ~byte 0
#   byte 2: raw bits 8-15 (Temp in bits 0-3, Mode in bits 4-7)
#   byte 3: ~byte 2
#   byte 4: raw bits 0-7 (unnamed)
#   byte 5: ~byte 4
# The kTranscoldHdrMark/HdrSpace header, then a footer of kTranscoldBitMark,
# kTranscoldHdrSpace, kTranscoldBitMark and kDefaultMessageGap. No repeat
# (kTranscoldDefaultRepeat is kNoRepeat).

TRANSCOLD = Protocol(
    "transcold",
    {
        "main": Section(
            # kTranscoldBitMark/ZeroSpace/OneSpace
            PulseDistance(555, 1526, 3556),
            header=(5944, 7563),  # kTranscoldHdrMark/HdrSpace
            footer=(555, 7563, 555),
            gap=100000,  # kDefaultMessageGap
            lsb_first=False,
        )
    },
    carrier=38000,  # enableIROut(38)
)

TRANSCOLD_MIN_TEMP, TRANSCOLD_MAX_TEMP = 18, 30  # kTranscoldTempMin/Max
TRANSCOLD_FAN_TEMP_CODE = 0b1111  # kTranscoldFanTempCode: "Part of Fan Mode"
TRANSCOLD_MODE = {  # kTranscold{Auto,Cool,Dry,Heat}; fan mode is Dry + Temp
    "auto": 0b1110,
    "cool": 0b0110,
    "dry": 0b1100,
    "heat": 0b1010,
}
TRANSCOLD_FAN = {  # kTranscoldFan*
    "auto": 0b1111,  # kTranscoldFanAuto: cool, heat and fan modes
    "auto0": 0b0110,  # kTranscoldFanAuto0: auto and dry modes
    "1": 0b1001,  # kTranscoldFanMin (convertFan: kLow)
    "2": 0b1101,  # kTranscoldFanMed (kMedium)
    "3": 0b1011,  # kTranscoldFanMax (kHigh)
}
TRANSCOLD_AUTO0_MODES = ("auto", "dry")  # setFan: "can't have speed Auto"
TRANSCOLD_KNOWN_GOOD_STATE = 0xE96554  # kTranscoldKnownGoodState
TRANSCOLD_OFF = 0xEF7954  # kTranscoldOff
TRANSCOLD_SWING = 0xE76154  # kTranscoldSwing: a swing toggle


def _transcold_temp_code(celsius):
    """IRTranscoldAc::setTemp: celsius - 17, inverted and bit-reversed (4 bits)."""
    inverted = ~(celsius - TRANSCOLD_MIN_TEMP + 1) & 0x0F
    return int(f"{inverted:04b}"[::-1], 2)


TRANSCOLD_TEMP = {
    **{
        t: _transcold_temp_code(t)
        for t in range(TRANSCOLD_MIN_TEMP, TRANSCOLD_MAX_TEMP + 1)
    },
    "fan": TRANSCOLD_FAN_TEMP_CODE,
}


def transcold_word(raw):
    """The logical bytes of a 24-bit Transcold word: each byte, most
    significant first, followed by its complement."""
    out = bytearray()
    for byte in raw.to_bytes(3, "big"):
        out += bytes([byte, ~byte & 0xFF])
    return bytes(out)


# Skeleton: kTranscoldKnownGoodState, which IRTranscoldAc::stateReset loads;
# no setter writes the unnamed bits, so they keep its values.
TRANSCOLD_LAYOUT = Layout(
    transcold_word(TRANSCOLD_KNOWN_GOOD_STATE),
    {
        "fan": Field.at(0, 0, 4, values=TRANSCOLD_FAN),
        "temp": Field.at(2, 0, 4, values=TRANSCOLD_TEMP),
        "mode": Field.at(2, 4, 4, values=TRANSCOLD_MODE),
    },
    checksum=InvertedPairs(0, 6),
)


class TranscoldDevice(Device):
    """Transcold A/C (IRTranscoldAc): a state word (mode, setpoint, fan),
    and two command words, kTranscoldOff and the swing toggle
    kTranscoldSwing.

    As IRac::transcold sends it:
    - power off sends kTranscoldOff alone, whatever the other settings;
    - the setpoint is kTranscoldTempMin..Max (18-30 C; the 0.1.x entity's
      17 C, which setTemp sent as 18 C, normalises to 18);
    - fan auto is kTranscoldFanAuto0 in auto and dry modes and
      kTranscoldFanAuto otherwise (IRTranscoldAc::setFan's mode check).

    Swing is a toggle: kTranscoldSwing is sent before the state word when the
    swing changes between off and on. With ``previous`` this is
    IRac::handleToggles' TRANSCOLD rule, which a persistent IRac applies (the
    previous swing counts even when the previous message was an off); with
    ``previous=None`` it is sent when the target swing is on, as from a
    fresh IRac, whose previous state is of protocol UNKNOWN. No toggle goes
    with an off message.

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_transcold_device.py):
    - fan mode: the header documents it as Dry with Temp
      kTranscoldFanTempCode; IRac::transcold calls setTemp after setMode,
      which overwrites that code, so C sends dry mode. The port sends the
      fan temp code, and kTranscoldFanAuto for fan auto (setMode's value for
      kTranscoldFan);
    - swing: the old glue never passes swing "on" to C, so C never sends
      kTranscoldSwing. The port sends the documented toggle.
    """

    PROTOCOL = TRANSCOLD
    # One layout per word: the swing toggle, when sent, reads with it too.
    LAYOUTS = (TRANSCOLD_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "fan", "heat"),
        temperature=TemperatureRange(18.0, 30.0),  # kTranscoldTempMin..Max
        fan=FAN_3,
        swing_v=SWING,
    )

    def frames(self, previous, target, actions):
        if not target.power:
            return [Frame("main", transcold_word(TRANSCOLD_OFF))]
        mode = target.mode
        fan = target.fan
        if fan == "auto" and mode in TRANSCOLD_AUTO0_MODES:
            fan = "auto0"
        if mode == "fan":
            mode, temp = "dry", "fan"
        else:
            temp = min(
                max(int(target.temperature), TRANSCOLD_MIN_TEMP), TRANSCOLD_MAX_TEMP
            )
        state = TRANSCOLD_LAYOUT.build(fan=fan, temp=temp, mode=mode)
        frames = [Frame("main", bytes(state))]
        was_swinging = previous is not None and previous.swing_v != "off"
        if (target.swing_v != "off") != was_swinging:
            frames.insert(0, Frame("main", transcold_word(TRANSCOLD_SWING)))
        return frames


TRANSCOLD_MODELS = ("M1-F-NO-6", "generic")


# Now the match between models and objects
