#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Gree AC IR commands.
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

from .kelvinator import KelvinatorBlockSum
from ..choices import FAN_3, ON_OFF, SWING_V_ANGLES
from ..device import Device
from ..fields import Field, Joined, Layout
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..state import Capabilities, Choice, TemperatureRange

# ------------------------------------------------------------------ Gree
# Layout from IRremoteESP8266's GreeProtocol (ir_Gree.h): an 8-byte state,
# each byte LSB first. IRsend::sendGree sends it as two blocks of 4 bytes:
# block 1 (kGreeHdrMark / kGreeHdrSpace header, bytes 0-3, then the 3-bit
# kGreeBlockFooter b010, a kGreeBitMark and kGreeMsgSpace) and block 2
# (no header, bytes 4-7, a kGreeBitMark and kGreeMsgSpace). No repeat
# (kGreeDefaultRepeat is kNoRepeat). Carrier 38 kHz (sendGeneric's 38).
#
# The block footer carries no data: it is a fixed burst in "block1"'s
# footer. The checksum (Sum, byte 7's high nibble) covers both blocks, so
# the Layout is over the whole message, the two frames' data joined.

# kGreeBitMark, kGreeZeroSpace, kGreeOneSpace.
_GREE_MARK, _GREE_ZERO, _GREE_ONE = 620, 540, 1600
_GREE_BITS = PulseDistance(_GREE_MARK, _GREE_ZERO, _GREE_ONE)

GREE = Protocol(
    "gree",
    {
        "block1": Section(
            _GREE_BITS,
            header=(9000, 4500),  # kGreeHdrMark, kGreeHdrSpace
            # kGreeBlockFooter (b010, LSB first) and kGreeBitMark.
            footer=(
                _GREE_MARK,
                _GREE_ZERO,
                _GREE_MARK,
                _GREE_ONE,
                _GREE_MARK,
                _GREE_ZERO,
                _GREE_MARK,
            ),
            gap=19980,  # kGreeMsgSpace
        ),
        "block2": Section(
            _GREE_BITS,
            footer=(_GREE_MARK,),  # kGreeBitMark
            gap=19980,  # kGreeMsgSpace
        ),
    },
    carrier=38000,
)

GREE_MIN_TEMP, GREE_MAX_TEMP = 16, 30  # kGreeMinTempC, kGreeMaxTempC
GREE_AUTO_TEMP = 25  # setTemp: "An operating mode of Auto locks the temp"
GREE_MODE = {  # kGree{Auto,Cool,Dry,Fan,Heat,Econo}
    "auto": 0,
    "cool": 1,
    "dry": 2,
    "fan": 3,
    "heat": 4,
    "econo": 5,  # the YX1FSF remote's energy saver, as a mode
}
GREE_FAN = {"auto": 0, "1": 1, "2": 2, "3": 3}  # kGreeFan{Auto,Min,Med,Max}
GREE_SWING_V = {  # kGreeSwing*: canonical "1" highest (Up) .. "5" lowest (Down)
    "off": 0b0000,  # LastPos: convertSwingV's kOff (the vane stays put)
    "auto": 0b0001,
    "1": 0b0010,  # Up
    "2": 0b0011,  # MiddleUp
    "3": 0b0100,  # Middle
    "4": 0b0101,  # MiddleDown
    "5": 0b0110,  # Down
    "down_auto": 0b0111,
    "middle_auto": 0b1001,
    "up_auto": 0b1011,
}
GREE_SWING_H = {  # kGreeSwingH*: canonical "1" far left .. "5" far right
    "off": 0b000,
    "auto": 0b001,
    "1": 0b010,  # MaxLeft
    "2": 0b011,  # Left
    "3": 0b100,  # Middle
    "4": 0b101,  # Right
    "5": 0b110,  # MaxRight
}

# Skeleton: IRGreeAC::stateReset (all zero, Temp 9, Light on, unknown1
# 0b0101, unknown2 0b100) with its checksum, as getRaw returns it.
# stateReset clears every byte, so no bit is stale; the unnamed bits are
# never written after it.
GREE_LAYOUT = Layout(
    bytes.fromhex("00092050" "00200050"),
    {
        # Byte 0.
        "mode": Field.at(0, 0, 3, values=GREE_MODE),
        "power": Field.at(0, 3, 1),
        "fan": Field.at(0, 4, 2, values=GREE_FAN),
        "swing_auto": Field.at(0, 6, 1),  # SwingAuto
        "sleep": Field.at(0, 7, 1),
        # Byte 1: degrees - kGreeMinTempC.
        "temp": Field.at(
            1,
            0,
            4,
            values={
                t: t - GREE_MIN_TEMP for t in range(GREE_MIN_TEMP, GREE_MAX_TEMP + 1)
            },
        ),
        "timer_half_hr": Field.at(1, 4, 1),
        "timer_tens_hr": Field.at(1, 5, 2),
        "timer_enabled": Field.at(1, 7, 1),
        # Byte 2.
        "timer_hours": Field.at(2, 0, 4),
        "turbo": Field.at(2, 4, 1),
        "light": Field.at(2, 5, 1),
        "model_a": Field.at(2, 6, 1),  # ModelA: power on and model YAW1F
        "xfan": Field.at(2, 7, 1),
        # Byte 3 (bits 4-7: unknown1, 0b0101 from stateReset).
        "temp_extra_degree_f": Field.at(3, 2, 1),
        "use_fahrenheit": Field.at(3, 3, 1),
        # Byte 4.
        "swing_v": Field.at(4, 0, 4, values=GREE_SWING_V),
        "swing_h": Field.at(4, 4, 3, values=GREE_SWING_H),
        # Byte 5 (bits 3-5: unknown2, 0b100 from stateReset).
        "display_temp": Field.at(5, 0, 2),
        "ifeel": Field.at(5, 2, 1),
        "wifi": Field.at(5, 6, 1),
        # Byte 7.
        "econo": Field.at(7, 2, 1),
    },
    # IRGreeAC::checksum: Kelvinator's block checksum over the 8 bytes.
    checksum=KelvinatorBlockSum(0),
)

# The remotes differ in economy only. Swing "off" is kGreeSwingLastPos
# (convertSwingV's kOff); the auto ranges (kGreeSwing{Down,Middle,Up}Auto)
# have no canonical name.
_GREE_SWING_V = SWING_V_ANGLES
_GREE_SWING_H = Choice(
    ("off", "auto", "1", "2", "3", "4", "5"),
    {
        "off": "off",
        "auto": "auto",
        "1": "far left",
        "2": "close left",
        "3": "middle",
        "4": "close right",
        "5": "far right",
    },
)


def _gree_capabilities(*features):
    return Capabilities(
        modes=("auto", "cool", "dry", "fan", "heat"),
        temperature=TemperatureRange(16.0, 30.0),
        fan=FAN_3,
        swing_v=_GREE_SWING_V,
        swing_h=_GREE_SWING_H,
        features={f: ON_OFF for f in features},
    )


GREE_CAPABILITIES = {  # variant (gree_ac_remote_model_t)
    "YAW1F": _gree_capabilities("powerful", "light", "cleaning", "sleep"),
    # YAW1F with byte 5's high bits 0b110 (WiFi and bit 7 set, bit 5 clear),
    # from SmartIR captures: climate 1402 (Samsung), 3040 (Viessmann), 3120
    # (Cooper & Hunter) send it on every message.
    "YAW1F-wifi": _gree_capabilities("powerful", "light", "cleaning", "sleep"),
    # YAW1F with byte 5's high bits 0b000: SmartIR climate 1183 (Gree), 1763
    # (Daitsu), 1780 (Trotec).
    "YAW1F-0": _gree_capabilities("powerful", "light", "cleaning", "sleep"),
    "YBOFB": _gree_capabilities("economy", "powerful", "light", "cleaning", "sleep"),
    "YX1FSF": _gree_capabilities("powerful", "light", "economy", "cleaning", "sleep"),
    # YX1FSF with byte 7 bit 3 set in heat mode: SmartIR climate 1184, 1185
    # (Gree), 2360 (Flouu).
    "YX1FSF-H": _gree_capabilities("powerful", "light", "economy", "cleaning", "sleep"),
}


# Byte 5 bits 5-7 of the YAW1F remotes SmartIR captured (stateReset: 0b001).
GREE_BYTE5_HIGH = {"YAW1F-wifi": 0b110, "YAW1F-0": 0b000}
GREE_HEAT_BIT = 0b1000  # byte 7 bit 3, set in heat by the YX1FSF-H remotes


class GreeDevice(Device):
    """Gree (IRGreeAC), for the YAW1F, YBOFB and YX1FSF remotes (the old
    Greev1, Greev2 and Greev3): a full-state protocol with no toggles, so
    ``previous`` is ignored.

    The variant (a gree_ac_remote_model_t name) comes from the model
    (GREE_MODEL_VARIANT) unless given; unknown models get YAW1F, as
    IRGreeAC::setModel does. It sets the capabilities (YBOFB and YX1FSF
    have economy) and two bits of the message: ModelA (YAW1F, power on)
    and the YX1FSF economy mode.

    As IRac::gree sends it (setModel, setPower, setMode, setTemp, setFan,
    setSwingVertical, setSwingHorizontal, then the features, on a fresh
    IRGreeAC):
    - an off message carries mode auto (convertMode's default for IRac's
      "off"), so the auto setpoint, with the requested fan and settings;
    - auto sends 25 C whatever the setpoint (setTemp's auto lock);
    - dry sends fan 1 whatever the fan (setFan's dry lock);
    - swing_v auto sets SwingAuto and kGreeSwingAuto; a position, or off
      (kGreeSwingLastPos), clears SwingAuto;
    - ModelA is set when the power is on and the variant is YAW1F
      (setPower);
    - economy sets Econo, and on YX1FSF also mode kGreeEcono (setEcono),
      in every mode and in off messages;
    - powerful is Turbo, cleaning is XFan, sleep is Sleep (IRac's
      setSleep(sleep >= 0)); iFeel, WiFi, the timer, the display and
      Fahrenheit bits stay clear.

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_gree_device.py; sleep is not one:
    the old glue has no sleep to pass):
    - fan "1" (low): convertFan maps kLow, like kMedium, to kGreeFanMax - 1
      (kGreeFanMed). The port sends kGreeFanMin;
    - swing_v "1" and "2" (90°, 60°): the old glue passes kHigh and
      kUpperMiddle; convertSwingV gives kGreeSwingMiddleUp and its default
      kGreeSwingAuto, which setSwingVertical(false, ...) replaces with
      kGreeSwingLastPos. The port sends the documented positions, highest
      to lowest: Up, MiddleUp, Middle, MiddleDown, Down ("3" to "5" are
      what C sends).
    """

    PROTOCOL = GREE
    LAYOUTS = (Joined(GREE_LAYOUT, 2),)  # the two blocks, joined
    VARIANTS = (
        "YAW1F-wifi",
        "YAW1F-0",
        "YX1FSF-H",
    )  # beyond the 0.1.x models' (see GREE_CAPABILITIES)
    capabilities = GREE_CAPABILITIES["YAW1F"]

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        # The registry always passes the variant; the table maps the 0.1.x
        # model names (oracle records, direct use) to theirs.
        self.variant = variant or GREE_MODEL_VARIANT.get(model)
        if self.variant is None:
            raise ValueError(
                f"unknown model {model!r}: pass variant= (see pyhvac.brands)"
            )
        if self.variant not in GREE_CAPABILITIES:
            raise ValueError(f"unknown Gree variant {self.variant!r}")
        self.capabilities = GREE_CAPABILITIES[self.variant]

    def frames(self, previous, target, actions):
        mode = target.mode if target.power else "auto"
        econo = target.features.get("economy", False)
        if econo and self.variant.startswith("YX1FSF"):
            mode_code = "econo"
        else:
            mode_code = mode
        features = target.features
        data = GREE_LAYOUT.build(
            power=target.power,
            mode=mode_code,
            temp=GREE_AUTO_TEMP if mode == "auto" else int(target.temperature),
            fan="1" if mode == "dry" else target.fan,
            swing_auto=target.swing_v == "auto",
            swing_v=target.swing_v,
            swing_h=target.swing_h,
            model_a=target.power and self.variant.startswith("YAW1F"),
            turbo=features["powerful"],
            light=features["light"],
            xfan=features["cleaning"],
            sleep=features.get("sleep", False),
            econo=econo,
        )
        if self.variant == "YX1FSF-H" and target.power and mode == "heat":
            data[7] |= GREE_HEAT_BIT
            GREE_LAYOUT.checksum.apply(data)
        high = GREE_BYTE5_HIGH.get(self.variant)
        if high is not None:  # byte 5 bits 5-7
            data[5] = data[5] & 0b00011111 | high << 5
            GREE_LAYOUT.checksum.apply(data)
        return [Frame("block1", bytes(data[:4])), Frame("block2", bytes(data[4:]))]


GREE_MODELS = (  # gree plugin
    "YAA1FBF remote",
    "YB1F2F remote",
    "YAN1F1 remote",
    "YX1F2F remote",
    "VIR09HP115V1AH",
    "VIR12HP230V1AH",
    "gemeric",
)
GREE_AMANA_MODELS = ("PBC093G00CC", "YX1FF remote")  # amana plugin
GREE_COOPER_HUNTER_MODELS = ("YB1F2 remote", "CH-S09FTXG")  # cooper_hunter plugin
GREE_EKOKAI_MODELS = ("generic",)  # ekokai plugin
GREE_GREEN_MODELS = ("YBOFB remote", "YBOFB2 remote")  # green plugin
GREE_RUSCLIMATE_MODELS = ("EACS/I-09HAR_X/N3", "YAW1F remote")  # rusclimate plugin
GREE_SOLEUS_MODELS = ("Air window",)  # soleus plugin
GREE_ULTIMATE_MODELS = ("Heat Pump",)  # ultimate plugin
GREE_VAILLAND_MODELS = ("YACIFB remote", "VAI5-035WNI")  # vailland plugin
GREE_MODEL_VARIANT = {  # model -> remote (gree_ac_remote_model_t), as Greev1-3
    **{
        m: "YAW1F"
        for m in GREE_MODELS
        + GREE_AMANA_MODELS
        + GREE_COOPER_HUNTER_MODELS
        + GREE_EKOKAI_MODELS
        + GREE_RUSCLIMATE_MODELS
        + GREE_ULTIMATE_MODELS
        + GREE_VAILLAND_MODELS
    },
    **{m: "YBOFB" for m in GREE_GREEN_MODELS},
    "YX1F2F remote": "YX1FSF",
    "Air window": "YX1FSF",  # soleus plugin
}


# Now the match between models and objects
