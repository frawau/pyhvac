#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Sharp AC IR commands as done by the CRMC-B028JBEZ and others
#
# This module  is in part based on the work/code from:
#      ToniA      https://github.com/adafruit/Raw-IR-decoder-for-Arduino/pull/3/commits/887ed4204711c0b911571f3090b7fd066e93f006
#
# Copyright (c) 2023 François Wautier
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


from dataclasses import dataclass, replace

from ..choices import FAN_3, ON_OFF
from ..device import Device
from ..fields import Checksum, Field, Layout
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import BOOL, Capabilities, Choice, TemperatureRange

SHARP_NATIVE = Protocol(
    "sharp",
    {
        "main": Section(
            PulseDistance(435, 435, 1400),
            header=(3800, 1900),
            footer=(435,),
            gap=10000,
            lsb_first=True,
        )
    },
)


# --------------------------------------------------------------- Device API

JTECH_BODY = b"\xaa\x5a\xcf\x10\x00\x00\x00\x00\x00\x80\x00\xe0"
JTECH_MODE = {"auto": 0x00, "cool": 0x02, "dry": 0x03}  # byte 6 low bits
JTECH_FAN = {"auto": 0x20, "1": 0x40, "2": 0x30, "3": 0x50, "4": 0x70}  # byte 6 high
JTECH_SWING_V = {"auto": 8, "1": 9, "2": 10, "3": 11, "4": 12, "5": 13, "swing": 14}
JTECH_SWING_H = {"1": 0x20, "2": 0x10, "3": 0x30, "swing": 0xF0}  # byte 8 high
JTECH_SPOT_SIDE = {"middle": 0x10, "left": 0x20, "right": 0x30}
POWER_ON, POWER_OFF, POWER_CHANGE = 0x11, 0x21, 0x31  # byte 5 transitions
SPECIAL_ON, SPECIAL_OFF = 0x61, 0x71  # byte 5 of a powerful/economy frame


def sharp_crc(body, special=0x01):
    crc = 0
    for x in body:
        crc ^= x
    crc ^= special
    crc ^= crc >> 4
    return ((crc & 0x0F) << 4) + special


def jtech_temperature(celsius):
    """Byte 4 for a setpoint; the unit takes whole and half degrees."""
    tenths = round(celsius * 10)
    whole, half = tenths // 10, tenths % 10 != 0
    if whole < 16:
        return whole + 0x3E + (0x20 if half else 0)
    return (0x70 if half else 0xC0) + whole - 15


class JTechDevice(Device):
    """Sharp J-Tech (FTM-PV2S): byte 5 encodes a power transition, so the
    frames depend on ``previous``; see the spec's transition table."""

    PROTOCOL = SHARP_NATIVE
    capabilities = Capabilities(
        modes=("auto", "cool", "dry"),
        temperature=TemperatureRange(14.0, 29.0, (0, 5)),
        fan=Choice(
            ("auto", "1", "2", "3", "4"),
            {"1": "lowest", "2": "low", "3": "medium", "4": "highest"},
        ),
        swing_v=Choice(
            ("auto", "swing", "1", "2", "3", "4", "5"),
            {"1": "ceiling", "2": "90°", "3": "60°", "4": "45°", "5": "30°"},
        ),
        swing_h=Choice(
            ("1", "2", "3", "swing"), {"1": "left", "2": "middle", "3": "right"}
        ),
        features={
            "purifier": BOOL,
            "powerful": BOOL,
            "economy": BOOL,
            "spot": Choice(
                (
                    "off",
                    "close left",
                    "close middle",
                    "close right",
                    "far left",
                    "far middle",
                    "far right",
                )
            ),
        },
    )

    def normalise(self, state):
        state = super().normalise(state)
        if state.mode == "dry" and state.fan != "auto":
            state = replace(state, fan="auto")  # the unit ignores fan in dry
        return state

    def _body(self, previous, target):
        """Every byte except the power byte (5) and the mode bits of byte 6."""
        body = bytearray(JTECH_BODY)
        if target.power and target.mode == "cool":
            body[4] = jtech_temperature(target.temperature)
        body[6] |= JTECH_FAN[target.fan]
        spot = target.features["spot"]
        if spot == "off":
            body[8] = JTECH_SWING_H[target.swing_h] | JTECH_SWING_V[target.swing_v]
        else:
            front, side = spot.split(" ")
            body[8] = JTECH_SPOT_SIDE[side] | (0x0C if front == "close" else 0x09)
            body[9] |= 0x01
        if target.features["purifier"]:
            body[11] |= 0x04
        # The main frame carries the economy state the unit is in; the
        # economy frame below is what changes it.
        if (previous or target).features["economy"]:
            body[11] |= 0x10
        return body

    def frames(self, previous, target, actions):
        body = self._body(previous, target)
        if not target.power:
            body[5] = POWER_OFF
        elif previous is None or not previous.power:
            body[5] = POWER_ON
        else:
            body[5] = POWER_CHANGE
        body[6] |= JTECH_MODE[target.mode]
        frames = [body]
        if target.power:
            for name in ("powerful", "economy"):
                wanted = target.features[name]
                if previous is not None and previous.features[name] == wanted:
                    continue
                extra = self._body(previous, target)
                extra[5] = SPECIAL_ON if wanted else SPECIAL_OFF
                extra[6] |= JTECH_MODE[target.mode]
                if name == "powerful":
                    extra[10] |= 0x01
                elif wanted:
                    extra[11] |= 0x10
                frames.append(extra)
        return [Frame("main", bytes(f) + bytes([sharp_crc(f)])) for f in frames]


# ----- SharpAc
# Layout from IRremoteESP8266's SharpProtocol (ir_Sharp.h): one 13-byte state,
# sent by sendSharpAc with sendGeneric (kSharpAcHdrMark/HdrSpace header,
# kSharpAcBitMark/OneSpace/ZeroSpace bits LSB first, a kSharpAcBitMark footer
# and kSharpAcGap = kDefaultMessageGap), no repeat (kSharpAcDefaultRepeat is
# kNoRepeat), at 38 kHz. IRac::sharp may send two or three such messages
# (see SharpAcDevice). IRSharpAc::stateReset writes all 13 bytes, so no bit
# comes from stale memory.

SHARP_AC = Protocol(
    "sharp_ac",
    {
        "main": Section(
            PulseDistance(470, 500, 1400),  # kSharpAcBitMark/ZeroSpace/OneSpace
            header=(3800, 1900),  # kSharpAcHdrMark/HdrSpace
            footer=(470,),  # kSharpAcBitMark
            gap=100000,  # kSharpAcGap
        )
    },
    carrier=38000,
)


@dataclass(frozen=True)
class HighNibbleXor(Checksum):
    """The XOR of the nibbles of data[start:end], and of the low nibble of
    data[at] when ``with_low``, in the high nibble of data[at]
    (IRSharpAc::calcChecksum). The low nibble of data[at] may hold fields."""

    with_low: bool = False

    def compute(self, data):
        total = 0
        for b in self._input(data):
            total ^= (b >> 4) ^ (b & 0x0F)
        if self.with_low:
            total ^= data[self.at] & 0x0F
        return total

    def bits(self):
        return set(range(8 * self.at + 4, 8 * self.at + 8))

    def apply(self, data):
        data[self.at] = (data[self.at] & 0x0F) | self.compute(data) << 4

    def check(self, data):
        return data[self.at] >> 4 == self.compute(data)


SHARP_AC_POWER_SPECIAL = {  # kSharpAcPower*
    "unknown": 0,
    "on_from_off": 1,
    "off": 2,
    "on": 3,
    "special_on": 6,
    "special_off": 7,
    "timer": 8,
}
SHARP_AC_SPECIAL = {  # kSharpAcSpecial*
    "power": 0x00,
    "turbo": 0x01,
    "temp_econo": 0x04,
    "fan": 0x05,
    "swing": 0x06,
    "timer": 0xC0,
    "timer_half_hour": 0xDE,
}
# kSharpAcAuto (A907) and kSharpAcFan (A705) share 0b00; the A903 has neither
# a fan nor a heat mode, and IRSharpAc::convertMode has no fan case, so its
# "fan" is 0b00 too. IRSharpAc::setMode turns heat into fan for the A705 and
# A903, which their capabilities do not offer.
SHARP_AC_MODE = {"auto": 0b00, "fan": 0b00, "heat": 0b01, "cool": 0b10, "dry": 0b11}
SHARP_AC_FAN = {  # variant -> canonical fan -> kSharpAcFan*
    # kSharpAcFanAuto, FanMin (FAN1), FanMed (FAN2), FanHigh (FAN3), FanMax
    # (FAN4), as IRSharpAc::convertFan maps kLow/kMedium/kHigh/kMax for the
    # A907.
    "A907": {"auto": 0b010, "1": 0b100, "2": 0b011, "3": 0b101, "4": 0b111},
    # kSharpAcFanA705Low, FanA705Med and FanMax: the three speeds these
    # remotes have (IRSharpAc::toString names 7 "High" for them). C sends
    # kSharpAcFanHigh (= FanA705Med) for "high" (declared as a Defect).
    "A903": {"auto": 0b010, "1": 0b011, "2": 0b101, "3": 0b111},
    "A705": {"auto": 0b010, "1": 0b011, "2": 0b101, "3": 0b111},
}
SHARP_AC_FAN_AUTO = 0b010  # kSharpAcFanAuto, which setClean(true) sets
SHARP_AC_FAN_MAX = 0b111  # kSharpAcFanMax, which setTurbo(true) sets
SHARP_AC_SWING_V = {  # canonical swing -> kSharpAcSwingV*, as convertSwingV
    "off": 0b000,  # kSharpAcSwingVIgnore: IRac sends no swing setting
    "1": 0b001,  # 90° (kHigh): kSharpAcSwingVHigh
    "2": 0b011,  # 45° (kMiddle): kSharpAcSwingVMid
    "3": 0b100,  # 30° (kLow): kSharpAcSwingVLow
}
SHARP_AC_TEMP_FLAGS = 0b110  # the 0xC0 IRSharpAc::setTemp writes into byte 4
SHARP_AC_MIN = 15  # kSharpAcMinTemp
SHARP_AC_MAX = 30  # kSharpAcMaxTemp

# Skeleton: IRSharpAc::stateReset's reset state with every written field and
# the Sum cleared (bytes 0-3, 5's low nibble, 8's bit 3, 9, 11's top bits and
# 12's low nibble are fixed).
SHARP_AC_LAYOUT = Layout(
    bytes.fromhex("aa5acf10000100000880" "00e001"),
    {
        "temperature": Field.at(4, 0, 4),  # Temp: degrees - kSharpAcMinTemp
        "model": Field.at(4, 4, 1),  # Model
        # Byte 4's unnamed top bits: setTemp writes 0xC0 (0xD0 with the A705
        # Model bit) when the mode takes a setpoint, 0 in auto/fan and dry.
        "temp_flags": Field.at(4, 5, 3),
        "power_special": Field.at(5, 4, 4, values=SHARP_AC_POWER_SPECIAL),
        "mode": Field.at(6, 0, 2),  # Mode (SHARP_AC_MODE)
        "clean": Field.at(6, 3, 1),
        "fan": Field.at(6, 4, 3),  # Fan (SHARP_AC_FAN)
        "timer_hours": Field.at(7, 0, 4),
        "timer_type": Field.at(7, 6, 1),
        "timer_enabled": Field.at(7, 7, 1),
        "swing": Field.at(8, 0, 3),  # Swing (SHARP_AC_SWING_V)
        "special": Field.at(10, 0, 8, values=SHARP_AC_SPECIAL),
        "ion": Field.at(11, 2, 1),
        "model2": Field.at(11, 4, 1),  # Model2
    },
    checksum=HighNibbleXor(0, 12, 12, with_low=True),  # IRSharpAc::checksum: Sum
)


SHARP_AC_SWING_V_CHOICE = Choice(
    ("off", "1", "2", "3"), {"off": "off", "1": "90°", "2": "45°", "3": "30°"}
)
# The A907's four speeds: FAN1 (kSharpAcFanMin) .. FAN4 (kSharpAcFanMax).
# The labels keep the legacy low/medium/high on their codes; FanMax is
# convertFan's kMax.
SHARP_AC_FAN_A907 = Choice(
    ("auto", "1", "2", "3", "4"),
    {"auto": "auto", "1": "low", "2": "medium", "3": "high", "4": "highest"},
)


def _sharp_ac_capabilities(modes, fan):
    """What IRac::sharp's state message carries for a remote: they differ in
    modes and fan speeds.

    Economy (A907) and light (A903/A705) are not offered: they are
    setEconoToggle / setLightToggle special messages (Special
    kSharpAcSpecialTempEcono), which IRac::sharp never sends (see
    SharpAcDevice)."""
    return Capabilities(
        modes=modes,
        temperature=TemperatureRange(float(SHARP_AC_MIN), float(SHARP_AC_MAX)),
        fan=fan,
        swing_v=SHARP_AC_SWING_V_CHOICE,
        features={
            "cleaning": ON_OFF,
            "powerful": ON_OFF,
            "purifier": ON_OFF,
        },
    )


SHARP_AC_CAPABILITIES = {  # variant (sharp_ac_remote_model_t)
    "A907": _sharp_ac_capabilities(("auto", "cool", "dry", "heat"), SHARP_AC_FAN_A907),
    # kSharpAcFanA705Low, FanA705Med, FanMax: three speeds.
    "A903": _sharp_ac_capabilities(("auto", "cool", "dry", "fan"), FAN_3),
    "A705": _sharp_ac_capabilities(("cool", "dry", "fan"), FAN_3),
}

SHARP_AC_MODEL_VARIANT = {  # model -> remote variant (sharp_ac_remote_model_t)
    "Sharp AY-ZP40KR": "A907",
    "AH-AxSAY": "A907",
    "CRMC-A907 JBEZ remote": "A907",
    "CRMC-A950 JBEZ": "A907",
    "generic A907": "A907",
    "AH-PR13-GL": "A903",
    "CRMC-A903JBEZ remote": "A903",
    "AH-XP10NRY": "A903",
    "CRMC-820 JBEZ remote": "A903",
    "AH-A12REVP-1": "A903",
    "CRMC-A863 JBEZ remote": "A903",
    "generic A903": "A903",
    "CRMC-A705 JBEZ remote": "A705",
    "generic A705": "A705",
}


class SharpAcDevice(Device):
    """Sharp A/C (SHARP_AC): the A907, A903 and A705 remotes, as IRac::sharp
    sends them.

    The variant (a sharp_ac_remote_model_t name) comes from the model
    (SHARP_AC_MODEL_VARIANT) unless given, and picks the capabilities and
    the fan codes; unknown models
    get the A907, as IRSharpAc::setModel does. Model2 is set for the A903 and
    A705; the Model bit only for the A705, and only in a mode that takes a
    setpoint (setTemp rewrites byte 4 after setModel set it).

    The state message:
    - PowerSpecial is Off for an off message; on, it is OnFromOff unless
      ``previous`` was on (then On), as IRac::sendAc passes prev->power
      (a fresh C object's previous state is off). Special is always Power:
      IRac calls setPower last;
    - an off message carries mode auto (IRac passes mode "off", which
      convertMode maps to its default, kSharpAcAuto); auto/fan and dry send
      byte 4 as 0 (no setpoint), cool and heat the setpoint;
    - the fan is sent in every mode: IRac's setClean(false) restores the
      requested speed after setMode forced auto (except in the first
      message of a cleaning request, below);
    - swing positions are sent, "off" sends kSharpAcSwingVIgnore; purifier
      sets Ion.

    Extra messages, as IRac::sharp sends them:
    - cleaning: an off message first, with fan auto in the modes without a
      setpoint (it is sent before setClean(false) restores the fan). When the target is on, the port then
      sends the documented clean message (setClean(true): dry, fan auto, no
      setpoint, Clean, PowerSpecial OnFromOff). C never sends it: IRac calls
      setPower after setClean, and setPower clears Clean and restores the
      mode (declared as a Defect). When the target is off, both messages are
      off messages, as in C;
    - powerful: the state message, then the same with setTurbo(true)
      (PowerSpecial SpecialOn, Special Turbo, fan kSharpAcFanMax), off or on.

    Economy (A907) and light (A903/A705) are not offered: IRac::sharp never
    calls setEconoToggle, and the PowerSpecial/Special values
    setLightToggle writes are overwritten by the setMode and setPower calls
    that follow it, so C sent nothing for them. Sending them needs their
    own special message (deferred).

    ``previous`` only sets PowerSpecial (above). IRac::handleToggles turns
    SHARP_AC swing changes into kAuto (swing toggle) or kOff, which with the
    entity's positions makes a persistent C object send SwingVToggle or
    SwingVOff instead of the requested position. The port sends the
    position, as a fresh C object does (declared as a Defect in the
    sequence test).
    """

    PROTOCOL = SHARP_AC
    LAYOUTS = (SHARP_AC_LAYOUT,)
    NAME = "Sharp A/C"

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        # The registry always passes the variant; the table maps the 0.1.x
        # model names (oracle records, direct use) to theirs.
        self.variant = variant or SHARP_AC_MODEL_VARIANT.get(model)
        if self.variant is None:
            raise ValueError(
                f"unknown model {model!r}: pass variant= (see pyhvac.brands)"
            )
        if self.variant not in SHARP_AC_CAPABILITIES:
            raise ValueError(f"unknown {self.NAME} variant {self.variant!r}")
        self.capabilities = SHARP_AC_CAPABILITIES[self.variant]

    @staticmethod
    def layouts(frames):
        """One layout per frame: every message is a state message."""
        return (SHARP_AC_LAYOUT,) * len(frames)

    def _values(self, mode, temperature, fan, target):
        code = SHARP_AC_MODE[mode]
        setpoint = code not in (SHARP_AC_MODE["auto"], SHARP_AC_MODE["dry"])
        degrees = min(max(int(temperature), SHARP_AC_MIN), SHARP_AC_MAX)
        return dict(
            temperature=degrees - SHARP_AC_MIN if setpoint else 0,
            model=int(setpoint and self.variant == "A705"),
            temp_flags=SHARP_AC_TEMP_FLAGS if setpoint else 0,
            mode=code,
            fan=fan,
            swing=SHARP_AC_SWING_V[target.swing_v],
            special="power",
            ion=target.features["purifier"],
            model2=int(self.variant != "A907"),
        )

    def frames(self, previous, target, actions):
        fan = SHARP_AC_FAN[self.variant][target.fan]
        mode = target.mode if target.power else "auto"
        state = self._values(mode, target.temperature, fan, target)
        if not target.power:
            power = "off"
        elif previous is not None and previous.power:
            power = "on"
        else:
            power = "on_from_off"
        messages = []
        plain = state  # what IRac::sharp's setPower restores
        if target.features["cleaning"]:
            # Sent before IRac's setClean restores the fan: setMode left it
            # at auto in the modes without a setpoint.
            first = dict(state, power_special="off")
            if not state["temp_flags"]:
                first.update(fan=SHARP_AC_FAN_AUTO)
            messages.append(first)
            if target.power:
                # setClean(true): dry (fan auto, no setpoint), Clean, and
                # setPower(true, false).
                state = self._values(
                    "dry", target.temperature, SHARP_AC_FAN_AUTO, target
                )
                state.update(clean=1)
                power = "on_from_off"
        messages.append(dict(state, power_special=power))
        if target.features["powerful"]:
            # setTurbo after setPower: built from the plain state, never
            # from the clean message (setPower cleared Clean in C).
            messages.append(
                dict(
                    plain,
                    fan=SHARP_AC_FAN_MAX,
                    power_special="special_on",
                    special="turbo",
                )
            )
        return [Frame("main", bytes(SHARP_AC_LAYOUT.build(**m))) for m in messages]


SHARP_AC_MODELS = tuple(SHARP_AC_MODEL_VARIANT)
