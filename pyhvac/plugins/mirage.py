#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Mirage AC IR commands.
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

from .hvaclib import PulseBased, GenPluginObject
from ..device import Device
from ..fields import Field, Layout, NibbleSum
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_3, ON_OFF, SWING, SWING_V_ANGLES
from ..state import Capabilities, Choice, TemperatureRange

try:
    from ..irhvac import KKG9AC1, KKG29AC1
except ImportError:
    # Only the C-backed classes use these; keep the ported ones importable.
    KKG9AC1 = KKG29AC1 = None


class Miragev1(PulseBased):

    STARTFRAME = [8360, 4248]
    ENDFRAME = [554, 20000]
    MARK = [554]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [545, 1592]  # ditto

    def __init__(self):
        super().__init__("MIRAGE", variant=KKG9AC1)
        self.capabilities = {
            "mode": ["off", "cool", "fan", "dry", "heat"],
            "temperature": [16, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto", "90°", "60°", "45°", "30°", "0°"],
            "powerful": ["off", "on"],
            "sleep": ["off", "on"],
            "light": ["off", "on"],
        }


class Miragev2(PulseBased):

    STARTFRAME = [8360, 4248]
    ENDFRAME = [554, 20000]
    MARK = [554]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [545, 1592]  # ditto

    def __init__(self):
        super().__init__("MIRAGE", variant=KKG29AC1)
        self.capabilities = {
            "mode": ["off", "cool", "fan", "dry", "heat"],
            "temperature": [16, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "auto", "90°", "60°", "45°", "30°", "0°"],
            "hswing": ["off", "on"],
            "powerful": ["off", "on"],
            "sleep": ["off", "on"],
            "light": ["off", "on"],
            "quiet": ["off", "on"],
            "cleaning": ["off", "on"],
            "purifier": ["off", "on"],
        }


DEVICES = {}


# ------------------------------------------------------------------- Mirage
# Layout from IRremoteESP8266's Mirage120Protocol (ir_Mirage.h): one 15-byte
# state (kMirageStateLength), sent LSB first by IRsend::sendMirage
# (sendGeneric with kMirageHdrMark/HdrSpace, kMirageBitMark,
# kMirageOneSpace/ZeroSpace, a kMirageBitMark footer and kMirageGap, i.e.
# kDefaultMessageGap), closed by Sum, the sum of the nibbles of bytes 0-13
# (IRMirageAc::calculateChecksum). No repeat (kMirageMinRepeat is
# kNoRepeat). Carrier kMirageFreq, 38 kHz.
# The union has one view per remote (mirage_ac_remote_model_t): the common
# fields (Header, Temp, Fan, Mode, Sum) plus the KKG9AC1 fields or the
# KKG29AC1 fields, which overlap. Each remote gets its own layout.

MIRAGE = Protocol(
    "mirage",
    {
        "main": Section(
            PulseDistance(554, 545, 1592),  # kMirageBitMark/ZeroSpace/OneSpace
            header=(8360, 4248),  # kMirageHdrMark/HdrSpace
            footer=(554,),  # kMirageBitMark
            gap=100000,  # kMirageGap (kDefaultMessageGap)
        )
    },
    carrier=38000,  # kMirageFreq
)

MIRAGE_CHECKSUM = NibbleSum(0, 14, 14)  # IRMirageAc::calculateChecksum

MIRAGE_MODE = {  # kMirageAc{Heat,Cool,Dry,Recycle,Fan}
    "heat": 0b001,
    "cool": 0b010,
    "dry": 0b011,
    "recycle": 0b100,
    "fan": 0b101,
}
MIRAGE_MIN_TEMP = 16  # kMirageAcMinTemp
MIRAGE_MAX_TEMP = 32  # kMirageAcMaxTemp
MIRAGE_TEMP = {  # degrees + kMirageAcTempOffset
    t: t + 0x5C for t in range(MIRAGE_MIN_TEMP, MIRAGE_MAX_TEMP + 1)
}


def _mirage_common_fields(fan):
    """Mirage120Protocol's common struct: Temp (byte 1), Fan and Mode
    (byte 4). Header (0x56) is fixed in the skeletons; Sum is the
    checksum."""
    return {
        "temperature": Field.at(1, 0, 8, values=MIRAGE_TEMP),
        "fan": Field.at(4, 0, 2, values=fan),
        "mode": Field.at(4, 4, 4, values=MIRAGE_MODE),
    }


# KKG9AC1 -------------------------------------------------------------------
# SwingAndPower (byte 5, bits 1-7) holds the vane position (kMirageAcSwingV*),
# plus kMirageAcPowerOff when the power is off (IRMirageAc::setPower and
# setSwingV); the field's values are (position, power) pairs.
MIRAGE_SWING_V = {  # documented position -> kMirageAcSwingV*
    "off": 0b0000,
    "lowest": 0b0011,
    "low": 0b0101,
    "middle": 0b0111,
    "high": 0b1001,
    "highest": 0b1011,
    "auto": 0b1101,
}
MIRAGE_POWER_OFF = 0x5F  # kMirageAcPowerOff
MIRAGE_SWING_POWER = {
    (position, power): code + (0 if power else MIRAGE_POWER_OFF)
    for position, code in MIRAGE_SWING_V.items()
    for power in (True, False)
}
# Canonical swing_v -> documented position: "1" (90°) is the topmost,
# kMirageAcSwingVHighest, counting down to "5" (0°), kMirageAcSwingVLowest.
MIRAGE_SWING_V_POSITION = {
    "off": "off",
    "auto": "auto",
    "1": "highest",
    "2": "high",
    "3": "middle",
    "4": "low",
    "5": "lowest",
}

# Skeleton: IRMirageAc::stateReset's kReset with the fields IRac writes
# cleared. Bytes 8 and 10 (unnamed for this remote) keep kReset's 0x0C:
# setOnTimer/setOffTimer only write them for KKG29AC1. The clock is 00:00:00
# (IRac passes clock -1, so fromCommon calls setClock(0)).
MIRAGE_KKG9AC1_LAYOUT = Layout(
    bytes.fromhex("56000000000000000c000c00000000"),
    {
        **_mirage_common_fields(
            # kMirageAcFan{Auto,Low,Med,High}, as convertFan maps them
            {"auto": 0b00, "1": 0b11, "2": 0b10, "3": 0b01}
        ),
        "light": Field.at(3, 3, 1),  # Light_Kkg9ac1
        # Unnamed bits: C leaves them as the skeleton has them, real
        # captures show other values (see the tests).
        "pad5": Field.at(5, 0, 1),
        "pad8": Field.at(8, 0, 8),
        "pad9": Field.at(9, 0, 8),
        "pad10": Field.at(10, 0, 8),
        "swing_power": Field.at(5, 1, 7, values=MIRAGE_SWING_POWER),
        "sleep": Field.at(6, 7, 1),  # Sleep_Kkg9ac1
        "turbo": Field.at(7, 3, 1),  # Turbo_Kkg9ac1
        "seconds": Field.at(11, 0, 8),  # BCD
        "minutes": Field.at(12, 0, 8),  # BCD
        "hours": Field.at(13, 0, 8),  # BCD
    },
    MIRAGE_CHECKSUM,
)

# KKG29AC1 ------------------------------------------------------------------
# Skeleton: kReset with the fields IRac writes cleared (setOnTimer(0) and
# setOffTimer(0) clear kReset's 12-hour timers). The three unnamed bits of
# byte 5 (pad5) keep kReset's 0b011: kReset's byte 5 (0x1A) is a KKG9AC1
# SwingAndPower, and no KKG29AC1 setter writes these bits.
MIRAGE_KKG29AC1_LAYOUT = Layout(
    bytes.fromhex("560000000018000000000000000000"),
    {
        **_mirage_common_fields(
            # kMirageAcKKG29AC1Fan{Auto,Low,Med,High}, as convertFan maps them
            {"auto": 0b00, "1": 0b10, "2": 0b11, "3": 0b01}
        ),
        "quiet": Field.at(3, 0, 1),
        "off_timer_enable": Field.at(4, 2, 1),
        "on_timer_enable": Field.at(4, 3, 1),
        "swing_h": Field.at(5, 0, 1, values={"off": 0, "swing": 1}),
        "swing_v": Field.at(5, 1, 1),
        "light_toggle": Field.at(5, 2, 1),  # LightToggle_Kkg29ac1
        "pad5": Field.at(5, 3, 3),
        # kMirageAcKKG29AC1PowerOn / kMirageAcKKG29AC1PowerOff
        "power": Field.at(5, 6, 2, values={True: 0b00, False: 0b11}),
        "filter": Field.at(6, 1, 1),
        "sleep": Field.at(6, 3, 1),  # Sleep_Kkg29ac1
        "recycle_heat": Field.at(6, 6, 1),
        "sensor_temp": Field.at(7, 0, 6),
        "clean_toggle": Field.at(7, 6, 1),
        "ifeel": Field.at(7, 7, 1),
        "on_timer_hours": Field.at(8, 0, 5),
        "turbo": Field.at(8, 7, 1),  # Turbo_Kkg29ac1
        "on_timer_mins": Field.at(9, 0, 6),
        "off_timer_hours": Field.at(10, 0, 5),
        "off_timer_mins": Field.at(11, 0, 6),
    },
    MIRAGE_CHECKSUM,
)

# KKG29AC1's SwingV is one bit: setSwingV sets it for every position but
# kMirageAcSwingVOff, and getSwingV reads it back as kMirageAcSwingVAuto. The
# fixed positions do nothing there, so the remote offers off and auto only
# (auto, as KKG9AC1 names kMirageAcSwingVAuto).
MIRAGE_KKG29AC1_SWING_V = Choice(("off", "auto"), {"off": "off", "auto": "auto"})

_MIRAGE_FEATURES = {"powerful": ON_OFF, "sleep": ON_OFF, "light": ON_OFF}
MIRAGE_CAPABILITIES = {  # remote variant -> what its layout can encode
    "KKG9AC1": Capabilities(
        modes=("cool", "fan", "dry", "heat"),
        temperature=TemperatureRange(float(MIRAGE_MIN_TEMP), float(MIRAGE_MAX_TEMP)),
        fan=FAN_3,
        swing_v=SWING_V_ANGLES,
        features=_MIRAGE_FEATURES,
    ),
    "KKG29AC1": Capabilities(
        modes=("cool", "fan", "dry", "heat"),
        temperature=TemperatureRange(float(MIRAGE_MIN_TEMP), float(MIRAGE_MAX_TEMP)),
        fan=FAN_3,
        swing_v=MIRAGE_KKG29AC1_SWING_V,
        swing_h=SWING,
        features={
            **_MIRAGE_FEATURES,
            "quiet": ON_OFF,
            "cleaning": ON_OFF,
            "purifier": ON_OFF,
        },
    ),
}
MIRAGE_LAYOUTS = {
    "KKG9AC1": MIRAGE_KKG9AC1_LAYOUT,
    "KKG29AC1": MIRAGE_KKG29AC1_LAYOUT,
}


class MirageDevice(Device):
    """Mirage 120-bit A/C (IRMirageAc): one full-state frame.

    The variant (a mirage_ac_remote_model_t name: KKG9AC1 or KKG29AC1)
    comes from the model (MIRAGE_MODEL_VARIANT) unless given; unknown models
    get KKG9AC1, IRMirageAc's default. It picks the capabilities and the
    layout.

    As IRac::mirage (fromCommon on a fresh object) sends it:
    - an off message carries mode cool (convertMode's default, which IRac's
      kOff mode falls to) with the rest of the target state;
    - powerful sets Turbo in cool only (setTurbo);
    - KKG9AC1: the vane position and the power share SwingAndPower (the
      position, plus kMirageAcPowerOff when off);
    - KKG29AC1: SwingV is one bit (swing_v off or auto); purifier sets
      Filter.

    ``previous`` matters for KKG29AC1 only, whose light and clean bits are
    toggles (LightToggle_Kkg29ac1, CleanToggle). IRac::handleToggles sends
    ``light ^ prev->light`` (KKG29AC1) and ``clean ^ prev->clean``, and so
    does the port: with ``previous`` it toggles only when the setting
    changes. Without ``previous`` it sends what a fresh IRac does: its _prev
    has protocol UNKNOWN, so handleToggles does nothing and each bit is the
    target setting. KKG9AC1's Light is a state, and it has no clean bit.

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_mirage_device.py):
    - sleep: the old glue never passes sleep, so setSleep(sleep >= 0) clears
      the Sleep bit; the port sends it;
    - swing_h "swing" (KKG29AC1): the old glue has no swing_h "on", so
      setSwingH(false); the port sets SwingH;
    - swing_v "1"/"2" (KKG9AC1): the old glue sends kHigh for 90° and
      kUpperMiddle (which convertSwingV maps to auto) for 60°; the port
      sends kMirageAcSwingVHighest and kMirageAcSwingVHigh.
    """

    PROTOCOL = MIRAGE

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        self.variant = variant or MIRAGE_MODEL_VARIANT.get(model, "KKG9AC1")
        if self.variant not in MIRAGE_CAPABILITIES:
            raise ValueError(f"unknown Mirage variant {self.variant!r}")
        self.capabilities = MIRAGE_CAPABILITIES[self.variant]
        self.LAYOUTS = (MIRAGE_LAYOUTS[self.variant],)

    def frames(self, previous, target, actions):
        features = target.features
        mode = target.mode if target.power else "cool"
        values = dict(
            temperature=int(target.temperature),
            fan=target.fan,
            mode=mode,
            turbo=features["powerful"] and mode == "cool",
            # The documented Sleep bit (the C path never sets it).
            sleep=features["sleep"],
        )
        if self.variant == "KKG9AC1":
            position = MIRAGE_SWING_V_POSITION[target.swing_v]
            values.update(
                light=features["light"],
                swing_power=(position, target.power),
            )
        else:
            light, clean = features["light"], features["cleaning"]
            if previous is not None:
                light = light != previous.features["light"]
                clean = clean != previous.features["cleaning"]
            values.update(
                quiet=features["quiet"],
                swing_h=target.swing_h,
                swing_v=target.swing_v != "off",
                light_toggle=light,
                power=target.power,
                filter=features["purifier"],
                clean_toggle=clean,
            )
        return [Frame("main", bytes(self.LAYOUTS[0].build(**values)))]


MIRAGE_MODEL_VARIANT = {  # model -> remote variant (mirage_ac_remote_model_t)
    "VLU series": "KKG9AC1",
    "generic": "KKG9AC1",
    "generic 2": "KKG29AC1",
    "Maxell MX-CH18CF": "KKG9AC1",  # maxell plugin
    "Maxell KKG9A-C1 remote": "KKG9AC1",  # maxell plugin
    "Reykir 9000": "KKG29AC1",  # tronitechnik plugin
    "KKG29A-C1 remote": "KKG29AC1",  # tronitechnik plugin
}
MIRAGE_MODELS = ("VLU series", "generic", "generic 2")  # mirage plugin
MIRAGE_MAXELL_MODELS = ("Maxell MX-CH18CF", "Maxell KKG9A-C1 remote")
MIRAGE_TRONITECHNIK_MODELS = ("Reykir 9000", "KKG29A-C1 remote")


DEVICES.update({m: MirageDevice for m in MIRAGE_MODELS})


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "VLU series": Miragev1,
        "generic": Miragev1,
        "generic 2": Miragev2,
    }

    def __init__(self):
        self.brand = "mirage"
