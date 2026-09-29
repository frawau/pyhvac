#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Whirlpool AC IR commands.
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
from ..fields import Checksums, Field, Joined, Layout, Xor8
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_3, ON_OFF, SWING
from ..state import Capabilities, TemperatureRange

try:
    from ..irhvac import DG11J13A, DG11J191
except ImportError:
    # Only the C-backed classes use these; keep the ported one importable.
    DG11J13A = DG11J191 = None


class Whirlpool(PulseBased):
    STARTFRAME = [3110, 9066]
    MARK = [520]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [480, 1535]  # ditto

    def __init__(self):
        super().__init__("WHIRLPOOL_AC", variant=DG11J13A)
        self.capabilities = {
            "mode": ["auto", "cool", "dry", "fan", "heat"],
            "temperature": [18, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "light": ["off", "on"],
            "sleep": ["off", "on"],
            "powerful": ["off", "on"],
        }


class Whirlpoolv2(PulseBased):
    STARTFRAME = [3110, 9066]
    MARK = [520]  # MARK0 is MARK[0], MARK1 is MARK[-1]
    SPACE = [480, 1535]  # ditto

    def __init__(self):
        super().__init__("WHIRLPOOL_AC", variant=DG11J191)
        self.capabilities = {
            "mode": ["auto", "cool", "dry", "fan", "heat"],
            "temperature": [18, 32],
            "fan": ["auto", "high", "medium", "low"],
            "swing": ["off", "on"],
            "light": ["off", "on"],
            "sleep": ["off", "on"],
            "powerful": ["off", "on"],
        }


DEVICES = {}


# --------------------------------------------------------------- WhirlpoolAc
# Layout from IRremoteESP8266's WhirlpoolProtocol (ir_Whirlpool.h): the
# 21-byte state (kWhirlpoolAcStateLength), sent LSB first by sendWhirlpoolAC
# in three sections of 6, 8 and 7 bytes. Only the first has a header
# (kWhirlpoolAcHdrMark/HdrSpace); each ends with a kWhirlpoolAcBitMark
# footer and a kWhirlpoolAcGap space, the last with kDefaultMessageGap. No
# repeat (kWhirlpoolAcDefaultRepeat = kNoRepeat). Carrier 38 kHz.
# The checksums span the sections (Sum1, in the second, covers bytes 2-11),
# so one Layout covers the whole state and frames() splits it.

WHIRLPOOL_AC_BITS = PulseDistance(597, 533, 1649)  # kWhirlpoolAcBitMark/Zero/One

WHIRLPOOL_AC = Protocol(
    "whirlpool_ac",
    {
        "first": Section(
            WHIRLPOOL_AC_BITS,
            header=(8950, 4484),  # kWhirlpoolAcHdrMark/HdrSpace
            footer=(597,),  # kWhirlpoolAcBitMark
            gap=7920,  # kWhirlpoolAcGap
        ),
        "second": Section(WHIRLPOOL_AC_BITS, footer=(597,), gap=7920),
        "third": Section(WHIRLPOOL_AC_BITS, footer=(597,), gap=100000),
    },
    carrier=38000,
)
WHIRLPOOL_AC_SECTIONS = (("first", 0, 6), ("second", 6, 14), ("third", 14, 21))

# kWhirlpoolAcCommand*: the button a message reports (Cmd, byte 15).
WHIRLPOOL_AC_COMMAND = {
    "light": 0x00,
    "power": 0x01,
    "temp": 0x02,
    "sleep": 0x03,
    "super": 0x04,
    "on_timer": 0x05,
    "mode": 0x06,
    "swing": 0x07,
    "ifeel": 0x0D,
    "fan": 0x11,
    "6th_sense": 0x17,
    "off_timer": 0x1D,
}

# Skeleton: IRWhirlpoolAc::stateReset, 0x83 0x06 in bytes 0-1, bit 7 of
# byte 6 set, every other byte 0, so no bit comes from stale memory. The
# real captures in ir_Whirlpool_test.cpp all have byte 6 bit 7 set.
WHIRLPOOL_AC_LAYOUT = Layout(
    bytes.fromhex("830600000000" "8000000000000000" "00000000000000"),
    {
        # kWhirlpoolAcFanAuto/High/Medium/Low
        "fan": Field.at(2, 0, 2, values={"auto": 0, "3": 1, "2": 2, "1": 3}),
        "power": Field.at(2, 2, 1),  # a toggle
        "sleep": Field.at(2, 3, 1),
        # Unnamed in the struct: 0 from stateReset, as C sends it. The real
        # capture RealExampleDecode has bit 4 set.
        "pad2": Field.at(2, 4, 3),
        # Swing1 and Swing2, always set together (setSwing).
        "swing": Field.over((2, 7), (8, 6), values={"off": 0, "swing": 0b11}),
        # kWhirlpoolAcHeat/Auto/Cool/Dry/Fan
        "mode": Field.at(
            3, 0, 3, values={"heat": 0, "auto": 1, "cool": 2, "dry": 3, "fan": 4}
        ),
        # degrees - (kWhirlpoolAcMinTemp + the model's offset)
        "temperature": Field.at(3, 4, 4),
        # Super1 and Super2, always set together (setSuper).
        "super": Field.over((5, 4), (5, 7), values={False: 0, True: 0b11}),
        "clock_hours": Field.at(6, 0, 5),
        "light_off": Field.at(6, 5, 1),
        "clock_mins": Field.at(7, 0, 6),
        "off_timer": Field.at(7, 7, 1),  # OffTimerEnabled
        "off_hours": Field.at(8, 0, 5),
        "off_mins": Field.at(9, 0, 6),
        "on_timer": Field.at(9, 7, 1),  # OnTimerEnabled
        "on_hours": Field.at(10, 0, 5),
        "on_mins": Field.at(11, 0, 6),
        "command": Field.at(15, 0, 8, values=WHIRLPOOL_AC_COMMAND),
        # J191: whirlpool_ac_remote_model_t DG11J13A (clear) / DG11J191 (set)
        "model": Field.at(18, 3, 1, values={"DG11J13A": 0, "DG11J191": 1}),
    },
    # IRWhirlpoolAc::checksum: Sum1 (byte 13) is the XOR of bytes 2-11,
    # Sum2 (byte 20) the XOR of bytes 14-19.
    Checksums(Xor8(2, 12, 13), Xor8(14, 20, 20)),
)

# The setpoint range per model: kWhirlpoolAcMinTemp/MaxTemp plus the
# model's offset (IRWhirlpoolAc::getTempOffset: -2 for DG11J191).
WHIRLPOOL_AC_RANGE = {"DG11J13A": (18, 32), "DG11J191": (16, 30)}


def _whirlpool_ac_capabilities(low, high):
    return Capabilities(
        modes=("auto", "cool", "dry", "fan", "heat"),  # kWhirlpoolAc*
        temperature=TemperatureRange(float(low), float(high)),
        fan=FAN_3,  # kWhirlpoolAcFan{Auto,Low,Medium,High}
        swing_v=SWING,  # Swing1/Swing2
        features={"light": ON_OFF, "sleep": ON_OFF, "powerful": ON_OFF},
    )


# Remote variant -> capabilities: the same but for the setpoint range.
WHIRLPOOL_AC_CAPABILITIES = {
    variant: _whirlpool_ac_capabilities(low, high)
    for variant, (low, high) in WHIRLPOOL_AC_RANGE.items()
}


WHIRLPOOL_AC_MODELS = {  # model -> remote variant (whirlpool_ac_remote_model_t)
    "DG11J1-3A remote": "DG11J13A",
    "DG11J1-04 remote": "DG11J13A",
    "DG11J1-91 remote": "DG11J191",
    "SPIS409L": "DG11J13A",
    "SPIS412L": "DG11J13A",
    "SPIW409L": "DG11J13A",
    "SPIW412L": "DG11J13A",
    "SPIW418L": "DG11J13A",
    "generic": "DG11J13A",
    "generic 2": "DG11J191",
}


class WhirlpoolAcDevice(Device):
    """Whirlpool DG11J1 remotes: full state, except that the power bit is a
    toggle. The model picks the remote variant (MODELS: DG11J13A or
    DG11J191, whirlpool_ac_remote_model_t), which sets J191 and the
    setpoint range the capabilities offer: kWhirlpoolAcMinTemp..MaxTemp
    (18-32 °C), or the same minus DG11J191's offset of 2 (16-30 °C).

    Power: with ``previous`` the toggle bit is set only when the power
    changes, as C does with a persistent IRac (IRac::handleToggles toggles
    WHIRLPOOL_AC's power on change). Without ``previous`` the bit is
    ``target.power``, as a fresh IRac sends: an "on" toggles, an "off"
    toggles nothing.

    As IRac::whirlpool sends it (setModel, setMode, setTemp, setFan,
    setSwing, setSuper, setLight, setSleep, setPowerToggle, in that order):
    - an off message carries mode cool (IRac passes mode "off", which
      convertMode maps to its default, cool) with the rest of the state;
    - Cmd is always kWhirlpoolAcCommandPower (setPowerToggle runs last);
    - light clears LightOff;
    - powerful (setSuper(true)) sets fan high and, in heat, the highest
      setpoint, else mode cool and the lowest setpoint (the variant's range);
    - sleep sets fan low (setSleep), which also cancels Super.

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_whirlpool_ac_device.py):
    - swing "swing": the old glue has no swing "on", so Swing1/Swing2 stay
      clear; the port sets them;
    - sleep: the old glue never passes sleep; the port sets Sleep (and fan
      low, as setSleep does);
    - powerful: setPowerToggle calls setSuper(false) after setSuper(turbo),
      so C never sends Super1/Super2; the port sets them.
    """

    PROTOCOL = WHIRLPOOL_AC
    LAYOUT = WHIRLPOOL_AC_LAYOUT
    # The Sum1 checksum spans the first two sections: one layout, 3 frames.
    LAYOUTS = (Joined(WHIRLPOOL_AC_LAYOUT, 3),)
    MODELS = WHIRLPOOL_AC_MODELS
    VARIANT_CAPABILITIES = WHIRLPOOL_AC_CAPABILITIES
    capabilities = WHIRLPOOL_AC_CAPABILITIES["DG11J13A"]

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        self.variant = variant or self.MODELS.get(model, "DG11J13A")
        if self.variant not in WHIRLPOOL_AC_RANGE:
            raise ValueError(f"unknown Whirlpool variant {self.variant!r}")
        self.capabilities = self.VARIANT_CAPABILITIES[self.variant]

    def frames(self, previous, target, actions):
        low, high = WHIRLPOOL_AC_RANGE[self.variant]
        if previous is None:
            toggle = target.power
        else:
            toggle = target.power != previous.power
        mode = target.mode if target.power else "cool"
        temperature = min(max(int(target.temperature), low), high)
        fan = target.fan
        features = target.features
        powerful = features["powerful"]
        if powerful:  # setSuper(true)
            fan = "3"
            if mode == "heat":
                temperature = high
            else:
                temperature, mode = low, "cool"
        if features["sleep"]:  # setSleep(true): fan low, Super cancelled
            fan, powerful = "1", False
        data = WHIRLPOOL_AC_LAYOUT.build(
            fan=fan,
            power=toggle,
            sleep=features["sleep"],
            swing=target.swing_v,
            mode=mode,
            temperature=temperature - low,
            super=powerful,
            light_off=not features["light"],
            command="power",
            model=self.variant,
        )
        return [Frame(name, bytes(data[a:b])) for name, a, b in WHIRLPOOL_AC_SECTIONS]


DEVICES.update({m: WhirlpoolAcDevice for m in WHIRLPOOL_AC_MODELS})


# Now the match between models and objects
class PluginObject(GenPluginObject):
    MODELS = {
        "DG11J1-3A remote": Whirlpool,
        "DG11J1-04 remote": Whirlpool,
        "DG11J1-91 remote": Whirlpoolv2,
        "SPIS409L": Whirlpool,
        "SPIS412L": Whirlpool,
        "SPIW409L": Whirlpool,
        "SPIW412L": Whirlpool,
        "SPIW418L": Whirlpool,
        "generic": Whirlpool,
        "generic 2": Whirlpoolv2,
    }

    def __init__(self):
        self.brand = "whirlpool"
