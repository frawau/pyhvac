#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate LG AC IR commands as done by the AXB74515402 and others
#
# Found the info about 4 bits somewhere on the  Internet...Can't find
# it again. Apologies for not being able to thanks that person.
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

from dataclasses import replace

from ..device import Device
from ..fields import Field, HighNibbleSum, Layout
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_4, FAN_5, ON_OFF, SWING
from ..state import Capabilities, Choice, TemperatureRange

# Frames are 4 bytes (32 bits) on the wire, as the legacy emitter sent them.
LG_NATIVE = Protocol(
    "lg-native",
    {
        "main": Section(
            PulseDistance(520, 520, 1530),
            header=(3100, 9850),
            footer=(520,),
            gap=12000,
            lsb_first=False,
        )
    },
)


# ------------------------------------------------------------- LGProtocol
# LG (IRLgAc, decode_type LG) and LG2 (IRLgAc, decode_type LG2) share one
# word, IRremoteESP8266's LGProtocol (ir_LG.h): 28 bits, sent MSB first. As
# logical bytes the word is (raw << 4) big-endian, the last nibble unsent:
#   byte 0: Sign (kLgAcSignature 0x88), raw bits 20-27
#   byte 1: Power (bits 6-7), unnamed (bits 3-5), Mode (bits 0-2)
#   byte 2: Temp (bits 4-7), Fan (bits 0-3)
#   byte 3: Sum (bits 4-7)
# Settings the state word cannot carry are separate "special" words (the
# kLgAc*Command/Toggle, kLgAcSwing*, kLgAcVaneSwingV* constants), each a
# burst of its own with the same Sign and Sum. The two protocols differ only
# in their header and bit mark (sendLG vs sendLG2).
#
# The gap closing each word is kLgMinMessageLength (108 050 µs): sendGeneric
# spaces max(kLgMinGap, kLgMinMessageLength - elapsed), and the C library's
# timing recorder (the oracle) elapses no time, so every word is followed by
# the full message length. No repeat (kLgDefaultRepeat is kNoRepeat).


def _lg_protocol(name, bit_mark, header):
    return Protocol(
        name,
        {
            "main": Section(
                PulseDistance(bit_mark, 550, 1600),  # kLgZeroSpace/kLgOneSpace
                header=header,
                footer=(bit_mark,),
                gap=108050,  # kLgMinMessageLength, as recorded
                lsb_first=False,
            )
        },
        carrier=38000,  # sendGeneric's 38 kHz
        # decodeLG: header, bits and footer with kUseDefTol (25 %) and mark
        # excess 0 (the header mark alone with the defaults).
        mark_excess=0,
    )


# IRsend::sendLG: kLgHdrMark/kLgHdrSpace, kLgBitMark.
LG_AC = _lg_protocol("lg-ac", 550, (8500, 4250))
# IRsend::sendLG2: kLg2HdrMark/kLg2HdrSpace, kLg2BitMark.
LG2 = _lg_protocol("lg2", 480, (3200, 9900))

LG_BITS = 28  # kLgBits
LG_AC_SIGNATURE = 0x88  # kLgAcSignature
LG_AC_TEMP_ADJUST = 15  # kLgAcTempAdjust: Temp = celsius - 15
LG_AC_MIN_TEMP, LG_AC_MAX_TEMP = 16, 30  # kLgAcMinTemp, kLgAcMaxTemp
LG_AC_MODE = {  # kLgAc{Cool,Dry,Fan,Auto,Heat}
    "cool": 0b000,
    "dry": 0b001,
    "fan": 0b010,
    "auto": 0b011,
    "heat": 0b100,
}
LG_AC_FAN_CODE = {  # kLgAcFan*
    "lowest": 0,
    "low": 1,
    "medium": 2,
    "max": 4,
    "auto": 5,
    "low_alt": 9,
    "high": 10,
}
# canonical fan -> kLgAcFan*, as IRLgAc::setFan stores it on every model but
# AKB74955603: convertFan(kHigh) gives kLgAcFanHigh, which setFan turns into
# kLgAcFanMax (a designed mapping).
LG_AC_FAN_BY_LEVEL = {
    "auto": "auto",  # kAuto
    "1": "lowest",  # kMin
    "2": "low",  # kLow
    "3": "medium",  # kMedium
    "4": "max",  # kHigh
}
LG_AC_POWER = {"on": 0b00, "off": 0b11}  # kLgAcPowerOn, kLgAcPowerOff
LG_AC_OFF_COMMAND = 0x88C0051  # kLgAcOffCommand
LG_AC_LIGHT_TOGGLE = 0x88C00A6  # kLgAcLightToggle
LG_AC_SWINGV_TOGGLE = 0x8810001  # kLgAcSwingVToggle
LG_AC_CHECKSUM = HighNibbleSum(1, 3, 3)  # IRLgAc::calcChecksum
# Skeleton: Sign kLgAcSignature, everything else (and Sum) clear. The C
# object never carries stale bits: IRLgAc::stateReset loads kLgAcOffCommand
# (unnamed bits 0) and every message is either a constant or setRaw'd state
# plus setters, none of which write the unnamed bits.
LG_AC_SKELETON = bytes([LG_AC_SIGNATURE, 0, 0, 0])


def lg_ac_word(raw):
    """The logical bytes of a 28-bit LG word (sent MSB first)."""
    return (raw << 4).to_bytes(4, "big")


def lg_ac_frame(raw):
    """A 28-bit ir_LG.h word (a constant, its Sum included) as a frame."""
    return Frame("main", lg_ac_word(raw), LG_BITS)


def _lg_layout(sign=None, *, power, unnamed, mode, temp, fan):
    """A Layout of LGProtocol's state word. Each keyword is a struct member,
    given as (field name, value table or None); Sign is a field only when
    named, else it stays the skeleton's kLgAcSignature."""
    at = {  # struct member -> (byte, bit, width)
        "sign": (0, 0, 8),  # raw bits 20-27
        "power": (1, 6, 2),  # raw bits 18-19
        "unnamed": (1, 3, 3),  # raw bits 15-17
        "mode": (1, 0, 3),  # raw bits 12-14
        "temp": (2, 4, 4),  # raw bits 8-11: celsius - kLgAcTempAdjust
        "fan": (2, 0, 4),  # raw bits 4-7
    }
    members = dict(power=power, unnamed=unnamed, mode=mode, temp=temp, fan=fan)
    if sign is not None:
        members = {"sign": sign, **members}
    return Layout(
        LG_AC_SKELETON,
        {
            name: Field.at(*at[member], values=values)
            for member, (name, values) in members.items()
        },
        checksum=LG_AC_CHECKSUM,
    )


def _lg_capabilities(fan, swing_v=None, swing_h=None, light=False):
    """A remote variant's capabilities: the state word's modes, setpoint
    (kLgAcMinTemp-kLgAcMaxTemp, whole degrees) and fan levels, plus swing
    and light only where IRLgAc::send sends a word for them."""
    return Capabilities(
        modes=("auto", "cool", "fan", "dry", "heat"),
        temperature=TemperatureRange(LG_AC_MIN_TEMP, LG_AC_MAX_TEMP),
        fan=fan,
        swing_v=swing_v,
        swing_h=swing_h,
        features={"light": ON_OFF} if light else {},
    )


class _LgWordDevice(Device):
    """IRLgAc: a state word, preceded by nothing and followed by the special
    words the remote variant (lg_ac_remote_model_t) sends. Power off sends
    only kLgAcOffCommand, whatever the other settings or the variant
    (IRLgAc::send: "Always send the special Off command").

    Subclasses give MODEL_VARIANT (model -> variant), DEFAULT_VARIANT,
    VARIANT_CAPABILITIES, state_word() and special_words()."""

    NAME = "LG"

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        # The registry always passes the variant; the table maps the 0.1.x
        # model names (oracle records, direct use) to theirs.
        self.variant = variant or self.MODEL_VARIANT.get(model)
        if self.variant is None:
            raise ValueError(
                f"unknown model {model!r}: pass variant= (see pyhvac.brands)"
            )
        if self.variant not in self.VARIANT_CAPABILITIES:
            raise ValueError(f"unknown {self.NAME} variant {self.variant!r}")
        self.capabilities = self.VARIANT_CAPABILITIES[self.variant]

    def frames(self, previous, target, actions):
        if not target.power:
            return [lg_ac_frame(LG_AC_OFF_COMMAND)]
        state = Frame("main", bytes(self.state_word(target)), LG_BITS)
        return [state] + self.special_words(previous, target)


# ------------------------------------------------------------------ LgAc
# IRLgAc::send sends the state word, then, for LG6711A20083V only, the swing
# word when it changed.

LG_AC_FAN = {  # canonical fan -> the Fan value IRLgAc::setFan stores
    level: LG_AC_FAN_CODE[name] for level, name in LG_AC_FAN_BY_LEVEL.items()
}

LG_AC_LAYOUT = _lg_layout(
    ("sign", None),
    power=("power", LG_AC_POWER),
    # The struct's unnamed 3 bits. C never sets them in a state word;
    # special words use them (kLgAcSwingVToggle has bit 16), and real LG
    # remotes set bit 15 (see the tests).
    unnamed=("unused", None),
    mode=("mode", LG_AC_MODE),
    temp=("temp", None),
    fan=("fan", LG_AC_FAN),
)


LG_AC_CAPABILITIES = {  # variant -> capabilities
    # IRLgAc::send sends no light or SwingH word for either variant, so
    # neither is offered (the legacy LGv2 / LGv1 entities offered both).
    "LG6711A20083V": _lg_capabilities(FAN_4, SWING),
    # The legacy LGv1 entity offered swing positions, but IRLgAc::send sends
    # no swing word for GE6711AR2853M (its default case): none is offered.
    "GE6711AR2853M": _lg_capabilities(FAN_4),
}

LG_AC_MODEL_VARIANT = {  # model -> remote variant (lg_ac_remote_model_t)
    "6711A20083V  remote": "LG6711A20083V",
    "TS-H122ERM1  remote": "LG6711A20083V",
    "AG1BH09AW101": "GE6711AR2853M",  # ge plugin
    "6711AR2853M Remote": "GE6711AR2853M",  # ge plugin
}
LG_AC_MODELS = ("6711A20083V  remote", "TS-H122ERM1  remote")  # lg plugin
LG_AC_GE_MODELS = ("AG1BH09AW101", "6711AR2853M Remote")  # ge plugin


class LgAcDevice(_LgWordDevice):
    """LG 28-bit A/C (IRLgAc, protocol LG): a full-state word, plus a swing
    toggle word for the LG6711A20083V remote.

    The variant (an lg_ac_remote_model_t name: LG6711A20083V, or
    GE6711AR2853M for the "ge" plugin's models) comes from the model
    (LG_AC_MODEL_VARIANT) unless given, and picks the capabilities (the
    legacy LGv2 / LGv1 entities). The variants share the state word.

    Power off sends only kLgAcOffCommand, whatever the other settings
    (IRLgAc::send). Light and horizontal swing are not offered: IRLgAc::send
    sends the light toggle for AKB74955603 and the SwingH words for
    AKB73757604 only.

    Swing: GE6711AR2853M sends no swing word at all, so it offers no swing.
    LG6711A20083V has one
    vertical swing button: IRac::lg sends kLgAcSwingVToggle when the swing
    changes between off and not-off, comparing with the previous state
    IRac::sendAc passes (prev->swingv, kOff without one);
    IRac::handleToggles has no LG case, the rule lives in IRac::lg. The port
    does the same: with ``previous`` the toggle word follows the state word
    when the swing changes, without it when the target swing is on. No
    toggle word goes with an off message.
    """

    PROTOCOL = LG_AC
    # One layout per word: the toggle word, when sent, reads with it too.
    LAYOUTS = (LG_AC_LAYOUT,)
    NAME = "LG A/C"
    MODEL_VARIANT = LG_AC_MODEL_VARIANT
    DEFAULT_VARIANT = "LG6711A20083V"
    VARIANT_CAPABILITIES = LG_AC_CAPABILITIES
    capabilities = LG_AC_CAPABILITIES["LG6711A20083V"]

    def state_word(self, target):
        temperature = min(max(int(target.temperature), LG_AC_MIN_TEMP), LG_AC_MAX_TEMP)
        return LG_AC_LAYOUT.build(
            sign=LG_AC_SIGNATURE,
            power="on",
            mode=target.mode,
            temp=temperature - LG_AC_TEMP_ADJUST,
            fan=target.fan,
        )

    def special_words(self, previous, target):
        if self.variant != "LG6711A20083V":
            return []
        was_swinging = previous is not None and previous.swing_v != "off"
        if (target.swing_v != "off") != was_swinging:
            # The documented toggle word. The old glue never passed swing
            # "on" to C (declared as a Defect in the tests).
            return [lg_ac_frame(LG_AC_SWINGV_TOGGLE)]
        return []


# ------------------------------------------------------------------- Lg2
# The special words (swing, light) go through LG2_COMMAND_LAYOUT: Sign, a
# 16-bit command over bytes 1-2, Sum.


def _lg2_command(code):
    """A 28-bit special word (ir_LG.h constant) -> the 16 bits of bytes 1-2,
    as the "command" field stores them (byte 1 low, byte 2 high)."""
    return int.from_bytes(lg_ac_word(code)[1:3], "little")


LG2_VANE_POSITION = {  # kLgAcVaneSwingV*
    "highest": 1,
    "high": 2,
    "upper_middle": 3,
    "middle": 4,
    "low": 5,
    "lowest": 6,
}
LG2_COMMANDS = {
    "off": _lg2_command(LG_AC_OFF_COMMAND),
    "light_toggle": _lg2_command(LG_AC_LIGHT_TOGGLE),
    "swing_v_toggle": _lg2_command(LG_AC_SWINGV_TOGGLE),
    "swing_v_lowest": _lg2_command(0x8813048),  # kLgAcSwingVLowest
    "swing_v_low": _lg2_command(0x8813059),  # kLgAcSwingVLow
    "swing_v_middle": _lg2_command(0x881306A),  # kLgAcSwingVMiddle
    "swing_v_upper_middle": _lg2_command(0x881307B),  # kLgAcSwingVUpperMiddle
    "swing_v_high": _lg2_command(0x881308C),  # kLgAcSwingVHigh
    "swing_v_highest": _lg2_command(0x881309D),  # kLgAcSwingVHighest
    "swing_v_swing": _lg2_command(0x8813149),  # kLgAcSwingVSwing (= Auto)
    "swing_v_off": _lg2_command(0x881315A),  # kLgAcSwingVOff
    "swing_h_auto": _lg2_command(0x881316B),  # kLgAcSwingHAuto
    "swing_h_off": _lg2_command(0x881317C),  # kLgAcSwingHOff
    # IRLgAc::calcVaneSwingV: kLgAcVaneSwingVBase (0x8813200) +
    # ((vane * kLgAcVaneSwingVSize + position) << 4), for the
    # kLgAcSwingVMaxVanes (4) vanes.
    **{
        f"vane{vane}_{name}": _lg2_command(0x8813200 + ((vane * 8 + pos) << 4))
        for vane in range(4)
        for name, pos in LG2_VANE_POSITION.items()
    },
}

LG2_LAYOUT = _lg_layout(
    power=("power", {True: 0, False: 3}),  # kLgAcPowerOn/Off
    # LGProtocol's unnamed bits. Real AKB74955603 words set bit 3; C never
    # writes them, so they keep kLgAcOffCommand's 0. The device never sets
    # "unnamed" (C sends 0).
    unnamed=("unnamed", None),
    mode=("mode", LG_AC_MODE),
    temp=(  # Temp: degrees - kLgAcTempAdjust
        "temperature",
        {t: t - LG_AC_TEMP_ADJUST for t in range(LG_AC_MIN_TEMP, LG_AC_MAX_TEMP + 1)},
    ),
    fan=("fan", LG_AC_FAN_CODE),
)
# The special words: Sign, a 16-bit command, Sum.
LG2_COMMAND_LAYOUT = Layout(
    LG_AC_SKELETON,
    {"command": Field.at(1, 0, 16, values=LG2_COMMANDS)},
    checksum=LG_AC_CHECKSUM,
)

LG2_FAN_BY_VARIANT = {  # canonical fan -> kLgAcFan*, as IRLgAc::setFan stores it
    # AKB75215403: convertFan(kHigh) = kLgAcFanHigh, which setFan turns into
    # kLgAcFanMax on any model but AKB74955603, so "4" is kLgAcFanMax. "5"
    # (kMax, kLgAcFanMax too) is not offered: it would repeat "4".
    "AKB75215403": {**LG_AC_FAN_BY_LEVEL, "5": "max"},
    # AKB74955603: setFan keeps kLgAcFanHigh and kLgAcFanMax apart and turns
    # low into kLgAcFanLowAlt: five speeds.
    "AKB74955603": {**LG_AC_FAN_BY_LEVEL, "2": "low_alt", "4": "high", "5": "max"},
    "AKB73757604": LG_AC_FAN_BY_LEVEL,
}
LG2_SWING_V = {  # canonical swing -> kLgAcSwingV* (AKB74955603), top to bottom
    "off": "swing_v_off",
    "auto": "swing_v_swing",  # convertSwingV(kAuto): kLgAcSwingVSwing
    "1": "swing_v_highest",
    "2": "swing_v_high",
    "3": "swing_v_upper_middle",
    "4": "swing_v_middle",
    "5": "swing_v_low",
    "6": "swing_v_lowest",
}
LG2_VANE = {  # canonical swing -> kLgAcVaneSwingV* (AKB73757604), top to bottom
    # Not offered: convertVaneSwingV has no off or auto (its default is
    # Highest, as "1").
    "off": "highest",
    "auto": "highest",
    "1": "highest",
    "2": "high",
    "3": "upper_middle",
    "4": "middle",
    "5": "low",
    "6": "lowest",
}
# The six documented positions (kLgAcSwingV* / kLgAcVaneSwingV*), highest
# first. The angle labels of the five-position choices do not fit six
# positions, so the labels are the header's names.
LG2_POSITIONS = Choice(
    ("1", "2", "3", "4", "5", "6"),
    {
        "1": "highest",
        "2": "high",
        "3": "upper middle",
        "4": "middle",
        "5": "low",
        "6": "lowest",
    },
)

LG2_CAPABILITIES = {
    # IRLgAc::send sends nothing but the state word for AKB75215403: no
    # swing or light (the legacy LG2v1 entity offered them).
    "AKB75215403": _lg_capabilities(FAN_4),
    # kLgAcSwingV* words (off, swing, six positions) and the light toggle;
    # no SwingH word.
    "AKB74955603": _lg_capabilities(
        FAN_5,
        Choice(
            ("off", "auto") + LG2_POSITIONS.values,
            {"off": "off", "auto": "auto", **LG2_POSITIONS.labels},
        ),
        light=True,
    ),
    # The kLgAcVaneSwingV* positions (no off or auto) and the SwingH words;
    # no light toggle.
    "AKB73757604": _lg_capabilities(FAN_4, LG2_POSITIONS, SWING),
}

LG2_MODELS = {  # model -> remote (lg_ac_remote_model_t), as the old LG2v1-3
    "AKB74395308  remote": "AKB75215403",
    "S4-W12JA3AA": "AKB75215403",
    "AKB75215403  remote": "AKB75215403",
    "AKB74955603  remote": "AKB74955603",
    "A4UW30GFA2": "AKB74955603",
    "AMNW09GSJA0": "AKB74955603",
    "AKB73315611  remote": "AKB74955603",
    "MS05SQ NW0": "AKB74955603",
    "AMNW24GTPA1": "AKB73757604",
    "AKB73757604  remote": "AKB73757604",
}


class Lg2Device(_LgWordDevice):
    """LG2 (28-bit LG protocol, remotes AKB75215403, AKB74955603 and
    AKB73757604, lg_ac_remote_model_t): a state word plus, depending on the
    remote, special words for swing and light, as IRac::lg / IRLgAc::send
    send them.

    The variant comes from the model (LG2_MODELS) unless given, so the
    registry's ``cls(brand, model)`` call picks it; unknown models get
    AKB75215403, the model IRLgAc::setRaw assumes for LG2.

    Power off is always the single kLgAcOffCommand word, whatever the mode,
    setpoint or variant. Power on sends the state word (Power on, Mode,
    Temp, Fan), then:
    - AKB75215403: nothing else. IRLgAc::send has no swing or light for it,
      so it offers none (the legacy entity's had no effect).
    - AKB74955603: the swing_v word when the swing differs from the previous
      one, then kLgAcLightToggle when light is off (every state word turns
      the light on, ir_LG.cpp). swing_h is not sent (as C), so not offered.
    - AKB73757604: one kLgAcVaneSwingV word per vane (4) for swing_v, then
      kLgAcSwingHAuto/Off. light is not sent (as C), so not offered.

    ``previous``, as the C path:
    - The swing_v word (AKB74955603) goes only when its code differs from
      the previous swing's: IRac::sendAc passes prev->swingv and IRac::lg
      seeds IRLgAc's previous swing with it, and IRLgAc::send compares. A
      fresh IRac's previous state has swing off, so without ``previous`` the
      word goes when swing_v is not "off". The port matches C in both cases.
      (IRac::handleToggles has no LG case: this rule is in IRac::lg/send.)
    - The vane words are sent every time: IRLgAc::send only sends vanes that
      changed, but IRac::lg never seeds the previous vanes (they stay 0, an
      unused position), so every vane always counts as changed.
    - The swing_h word (AKB73757604) goes without ``previous`` (as every
      fresh C message recorded, and as the vane words), and with
      ``previous`` only when swing_h changed. IRLgAc::send means that rule
      (it compares _swingh with _swingh_prev) but nothing ever writes
      _swingh_prev, so C compares with stale memory and in practice sends
      the word every time; stale memory is not a reference (house rule 3a),
      so the port deliberately applies the documented change rule.
    - light: no previous state is used, as C: the toggle goes whenever light
      is off. It is a real toggle, but IRLgAc::send only sends it right after
      a state word, which always turns the light on (ir_LG.cpp, issue 1513),
      so each message leaves the light as asked; toggling only on change
      would leave it on.

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_lg2_device.py):
    - swing_v "1"/"2" (the legacy 90°/60°): the glue maps them to
      kHigh/kUpperMiddle; convertSwingV sends kLgAcSwingVHigh for kHigh and
      has no kUpperMiddle case (kLgAcSwingVOff, so no swing word at all),
      and convertVaneSwingV sends High for kHigh and Highest for
      kUpperMiddle. The port sends Highest/High (canonical "1" is the
      topmost documented position).
    - swing_h "swing" (the legacy "on"): IRGHVAC.trans_hswing has no "on",
      so C sends kLgAcSwingHOff; the port sends kLgAcSwingHAuto.
    """

    PROTOCOL = LG2
    LAYOUTS = (LG2_LAYOUT, LG2_COMMAND_LAYOUT)
    NAME = "LG2"
    MODEL_VARIANT = LG2_MODELS
    DEFAULT_VARIANT = "AKB75215403"
    VARIANT_CAPABILITIES = LG2_CAPABILITIES

    @staticmethod
    def _command(name):
        return Frame("main", bytes(LG2_COMMAND_LAYOUT.build(command=name)), LG_BITS)

    def state_word(self, target):
        return LG2_LAYOUT.build(
            power=True,
            mode=target.mode,
            temperature=int(target.temperature),
            fan=LG2_FAN_BY_VARIANT[self.variant][target.fan],
        )

    def special_words(self, previous, target):
        words = []
        if self.variant == "AKB74955603":
            before = "off" if previous is None else previous.swing_v
            if LG2_SWING_V[target.swing_v] != LG2_SWING_V[before]:
                words.append(self._command(LG2_SWING_V[target.swing_v]))
            if not target.features["light"]:  # must be sent last
                words.append(self._command("light_toggle"))
        elif self.variant == "AKB73757604":
            position = LG2_VANE[target.swing_v]
            words += [self._command(f"vane{v}_{position}") for v in range(4)]
            if previous is None or previous.swing_h != target.swing_h:
                words.append(
                    self._command(
                        "swing_h_auto" if target.swing_h == "swing" else "swing_h_off"
                    )
                )
        return words


# ------------------------------------------------------------- LG native
# The 0.1.x pure-Python LG classes (LG, InverterV, DualInverter) on
# LG_NATIVE. Their code is the spec: every frame is 3 bytes plus the
# checksum byte LG.crc appends (the nibble sum of the 3 bytes, mod 16, in
# its high nibble), sent MSB first as 32 bits. The first 28 bits are
# IRremoteESP8266's LGProtocol word (the off frame is kLgAcOffCommand):
#   byte 0: 0x88 (LG.FBODY)
#   byte 1: power (bits 6-7, 3 = off: code_mode's 0xc0), "change" (bit 3:
#           code_mode's addit, set when the unit was already on), mode
#           (bits 0-2)
#   byte 2: temperature - 15 (bits 4-7), fan (bits 0-3)
# Settings the state frame cannot carry are "special" frames of their own:
# 0x88 and a 16-bit command (code_swing, code_hswing, code_powerful,
# code_purifier, code_cleaning, code_economy, code_diagnostic).

LG_NATIVE_MODE = {"cool": 0, "dry": 1, "fan": 2, "auto": 3}  # LG.code_mode
LG_NATIVE_FAN = {  # LG.code_fan's rank
    "lowest": 0x0,
    "low": 0x09,
    "medium": 0x02,
    "high": 0x0A,
    "highest": 0x04,
    "auto": 0x05,
}
LG_NATIVE_CHECKSUM = HighNibbleSum(0, 3, 3)  # LG.crc

LG_NATIVE_LAYOUT = Layout(
    b"\x88\x00\x00\x00",
    {
        "power": Field.at(1, 6, 2, values={True: 0, False: 3}),
        "change": Field.at(1, 3, 1),
        "mode": Field.at(1, 0, 3, values=LG_NATIVE_MODE),
        "temp": Field.at(2, 4, 4),  # celsius - 15
        "fan": Field.at(2, 0, 4, values=LG_NATIVE_FAN),
    },
    checksum=LG_NATIVE_CHECKSUM,
)


def _lg_native_commands(prefix, byte1, codes):
    return {f"{prefix}{name}": byte1 | code << 8 for name, code in codes.items()}


LG_NATIVE_COMMANDS = {  # command -> bytes 1-2 (byte 1 low, byte 2 high)
    # LG.code_swing: 0x88 0x13 xx
    **_lg_native_commands(
        "swing_v ",
        0x13,
        {
            "swing": 0x14,
            "off": 0x15,
            "0°": 0x04,
            "30°": 0x05,
            "45°": 0x06,
            "60°": 0x07,
            "90°": 0x08,
            "ceiling": 0x09,
        },
    ),
    # LG.code_hswing: 0x88 0x13 xx
    **_lg_native_commands(
        "swing_h ",
        0x13,
        {
            "swing": 0x16,
            "off": 0x17,
            "left": 0x0B,
            "centre left": 0x0C,
            "centre": 0x0D,
            "centre right": 0x0E,
            "right": 0x0F,
            "swing left": 0x10,
            "swing right": 0x11,
        },
    ),
    "powerful on": 0x10 | 0x08 << 8,  # LG.code_powerful: 0x88 0x10 0x08
    # LG.code_purifier, code_cleaning, code_economy, code_diagnostic: 0x88 0xc0 xx
    **_lg_native_commands("purifier ", 0xC0, {"on": 0x00, "off": 0x08}),
    **_lg_native_commands("cleaning ", 0xC0, {"off": 0x0B, "on": 0x0C}),
    **_lg_native_commands(
        "economy ", 0xC0, {"off": 0x7F, "80": 0x7D, "60": 0x7E, "40": 0x80}
    ),
    "diagnostic": 0xC0 | 0xCE << 8,
}
LG_NATIVE_COMMAND_LAYOUT = Layout(
    b"\x88\x00\x00\x00",
    {"command": Field.at(1, 0, 16, values=LG_NATIVE_COMMANDS)},
    checksum=LG_NATIVE_CHECKSUM,
)

# canonical fan -> the legacy name LG.code_fan ranks
LG_NATIVE_FAN_NAME = dict(FAN_5.labels)
# The auto_bias ladder: code_temperature sends 15 + its index in auto mode.
LG_NATIVE_AUTO_BIAS_LADDER = ("-2", "-1", "default", "+1", "+2")
# The same values, default first (a feature's first value is its default).
LG_NATIVE_AUTO_BIAS = Choice(("default", "-2", "-1", "+1", "+2"))
LG_NATIVE_ECONOMY = Choice(("off", "80", "60", "40"))


def _lg_native_positions(*labels):
    """A swing Choice: off, swing, then "1".."n" labelled with the legacy
    positions, top (or left) first."""
    levels = {str(n): label for n, label in enumerate(labels, 1)}
    return Choice(("off", "swing") + tuple(levels), {"swing": "swing", **levels})


LG_NATIVE_VARIANTS = {
    # LG: modes off/cool/fan/dry, 18-29 °C, nothing else (LG.__init__).
    "generic": Capabilities(
        modes=("cool", "fan", "dry"),
        temperature=TemperatureRange(18.0, 29.0),
    ),
    # InverterV.__init__
    "inverter v": Capabilities(
        modes=("auto", "cool", "fan", "dry"),
        temperature=TemperatureRange(16.0, 29.0),
        fan=FAN_5,  # auto, lowest..highest
        swing_v=_lg_native_positions("90°", "0°"),
        features={
            "auto_bias": LG_NATIVE_AUTO_BIAS,
            "powerful": ON_OFF,
            "cleaning": ON_OFF,
            "economy": LG_NATIVE_ECONOMY,
        },
    ),
    # DualInverter.__init__
    "dual inverter": Capabilities(
        modes=("auto", "cool", "fan", "dry"),
        temperature=TemperatureRange(16.0, 29.0),
        fan=FAN_5,  # auto, lowest..highest
        swing_v=_lg_native_positions("ceiling", "90°", "60°", "45°", "30°", "0°"),
        swing_h=_lg_native_positions(
            "left",
            "centre left",
            "centre",
            "centre right",
            "right",
            "swing left",
            "swing right",
        ),
        features={
            "auto_bias": LG_NATIVE_AUTO_BIAS,
            "powerful": ON_OFF,
            "purifier": ON_OFF,
            "cleaning": ON_OFF,
            "economy": LG_NATIVE_ECONOMY,
        },
        actions={"diagnostic": "diagnostic"},
    ),
}
LG_NATIVE_MODELS = {  # model -> variant, as PluginObject.MODELS
    "generic": "generic",
    "inverter v": "inverter v",
    "dual inverter": "dual inverter",
}


class LgNativeDevice(Device):
    """The 0.1.x pure-Python LG classes: LG ("generic"), InverterV
    ("inverter v") and DualInverter ("dual inverter"). They share LG's code
    and differ only by their tables (the variant's capabilities).

    A message is a state frame and/or special frames, as LG.build_code:
    - Power off: the off frame (kLgAcOffCommand) alone.
    - Power on: the state frame, then one special frame per setting that
      changed, in LG's order (swing_v, swing_h, powerful, purifier,
      cleaning, economy), then the diagnostic request when asked.

    The state frame carries the mode, the fan (auto in auto mode,
    code_fan) and a temperature that depends on the mode (code_temperature):
    the setpoint in cool, 18 in fan, 24 in dry, and 15 plus the auto_bias
    index (17 by default) in auto.

    ``previous``, as the legacy object's status (what it sent last):
    - The "change" bit (code_mode's addit) is set when the unit was on.
      Without ``previous`` it is clear: a power-on frame, as a fresh object.
    - The state frame goes when power, mode, setpoint, fan or auto_bias
      changed, when powerful was switched off (code_powerful resends the
      normal code to leave jet mode), and whenever nothing else would be
      sent. LG.build_code tests mode, temperature and fan only, so an
      auto_bias change alone sent nothing (an evident omission: auto_bias
      only lives in that frame); the port sends it.
    - A special frame goes when its setting differs from ``previous``.
      Without ``previous`` every offered setting's frame goes (each is an
      absolute code, not a toggle), powerful only when on.
    """

    PROTOCOL = LG_NATIVE
    # The state frame, then any number of special frames.
    LAYOUTS = (LG_NATIVE_LAYOUT, LG_NATIVE_COMMAND_LAYOUT)
    capabilities = LG_NATIVE_VARIANTS["generic"]

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        # The registry always passes the variant; the table maps the 0.1.x
        # model names (oracle records, direct use) to theirs.
        self.variant = variant or LG_NATIVE_MODELS.get(model)
        if self.variant is None:
            raise ValueError(
                f"unknown model {model!r}: pass variant= (see pyhvac.brands)"
            )
        if self.variant not in LG_NATIVE_VARIANTS:
            raise ValueError(f"unknown LG native variant {self.variant!r}")
        self.capabilities = LG_NATIVE_VARIANTS[self.variant]

    def normalise(self, state):
        state = super().normalise(state)
        if state.mode == "auto" and state.fan != "auto":
            state = replace(state, fan="auto")  # code_fan: auto mode, auto fan
        return state

    @staticmethod
    def _frame(data):
        return Frame("main", bytes(data))

    def _command(self, name):
        return self._frame(LG_NATIVE_COMMAND_LAYOUT.build(command=name))

    def _temperature(self, target):
        """LG.code_temperature."""
        if target.mode == "fan":
            return 18
        if target.mode == "dry":
            return 24
        if target.mode == "auto":
            bias = target.features.get("auto_bias")
            if bias is None:  # no auto_bias capability
                return 17
            return 15 + LG_NATIVE_AUTO_BIAS_LADDER.index(bias)
        return int(target.temperature)

    def _state_frame(self, previous, target):
        if not target.power:
            return LG_NATIVE_LAYOUT.build(
                power=False, change=0, mode="cool", temp=0, fan="auto"
            )
        return LG_NATIVE_LAYOUT.build(
            power=True,
            change=int(previous is not None and previous.power),
            mode=target.mode,
            temp=self._temperature(target) - 15,
            fan=LG_NATIVE_FAN_NAME[target.fan],
        )

    def _specials(self, previous, target):
        caps = self.capabilities

        def changed(get):
            return previous is None or get(previous) != get(target)

        names = []
        if caps.swing_v is not None and changed(lambda s: s.swing_v):
            names.append(f"swing_v {caps.swing_v.label(target.swing_v)}")
        if caps.swing_h is not None and changed(lambda s: s.swing_h):
            names.append(f"swing_h {caps.swing_h.label(target.swing_h)}")
        for feature in ("powerful", "purifier", "cleaning", "economy"):
            if feature not in caps.features:
                continue
            value = target.features[feature]
            if not changed(lambda s: s.features[feature]):
                continue
            if feature == "powerful" and not value:
                continue  # leaving jet mode is the state frame (see frames)
            if isinstance(value, bool):
                value = caps.features[feature].label(value)
            names.append(f"{feature} {value}")
        return names

    def frames(self, previous, target, actions):
        if not target.power:
            return [self._frame(self._state_frame(previous, target))]
        names = self._specials(previous, target)
        if "diagnostic" in actions:
            names.append("diagnostic")
        keys = ("power", "mode", "temperature", "fan")
        send_state = (
            previous is None
            or not names
            or any(getattr(previous, k) != getattr(target, k) for k in keys)
            or previous.features.get("auto_bias") != target.features.get("auto_bias")
            or (
                previous.features.get("powerful")
                and not target.features.get("powerful")
            )
        )
        frames = (
            [self._frame(self._state_frame(previous, target))] if send_state else []
        )
        return frames + [self._command(name) for name in names]
