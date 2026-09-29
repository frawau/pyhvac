#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate TCL AC IR commands.
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
from ..fields import Field, Layout, Sum8
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_4, ON_OFF, SWING, SWING_V_ANGLES
from ..state import Capabilities, TemperatureRange

# ---------------------------------------------------------------- Tcl112Ac
# Layout from IRremoteESP8266's Tcl112Protocol (ir_Tcl.h): one 14-byte state
# (kTcl112AcStateLength), sent LSB first by IRsend::sendTcl112Ac (sendGeneric
# with kTcl112AcHdrMark/HdrSpace, kTcl112AcBitMark, kTcl112AcOneSpace/
# ZeroSpace, a kTcl112AcBitMark footer and a kTcl112AcGap gap), 38 kHz, no
# repeat (kTcl112AcDefaultRepeat = kNoRepeat). MsgType (byte 3) tells the
# normal state message (kTcl112AcNormal) from the special one
# (kTcl112AcSpecial) that carries Quiet: IRTcl112Ac::send sends a special
# message before the normal one when quiet changes.

TCL112AC_SECTION = Section(
    PulseDistance(500, 325, 1050),  # kTcl112AcBitMark/ZeroSpace/OneSpace
    header=(3000, 1650),  # kTcl112AcHdrMark/HdrSpace
    footer=(500,),  # kTcl112AcBitMark
    gap=100000,  # kTcl112AcGap (kDefaultMessageGap)
)
TCL112AC = Protocol(
    "tcl112ac",
    {"quiet": TCL112AC_SECTION, "main": TCL112AC_SECTION},
    carrier=38000,
    # decodeMitsubishi112 (shared with TCL112AC): _tolerance +
    # kTcl112AcTolerance (30 %), mark excess 0.
    tolerance=0.30,
    mark_excess=0,
)


TCL112AC_MSG_TYPE = {"normal": 0b01, "special": 0b10}  # kTcl112AcNormal/Special
# tcl_ac_remote_model_t -> isTcl, as IRTcl112Ac::setModel writes it.
TCL112AC_MODEL = {"TAC09CHSD": 1, "GZ055BE1": 0}

# Skeleton: IRTcl112Ac::stateReset's known good state (on, cool, 24 C), with
# the fields the device always writes cleared and the sum cleared; stateReset
# writes every byte, so nothing comes from stale memory. Byte 5 bit 5 (Quiet,
# only written in a special message) and TimerIndicator (byte 8 bit 6, only
# written by the timer setters) keep the reset value 1.
TCL112AC_LAYOUT = Layout(
    bytes([0x23, 0xCB, 0x26, 0x01, 0x00, 0x20, 0x00])
    + bytes([0x00, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00]),
    {
        "msg_type": Field.at(3, 0, 2, values=TCL112AC_MSG_TYPE),
        "power": Field.at(5, 2, 1),
        "off_timer_enabled": Field.at(5, 3, 1),
        "on_timer_enabled": Field.at(5, 4, 1),
        "quiet": Field.at(5, 5, 1),
        # The Light bit is cleared when the light is on (setLight).
        "light": Field.at(5, 6, 1, values={True: 0, False: 1}),
        "econo": Field.at(5, 7, 1),
        "mode": Field.at(  # kTcl112Ac{Heat,Dry,Cool,Fan,Auto}
            6, 0, 4, values={"heat": 1, "dry": 2, "cool": 3, "fan": 7, "auto": 8}
        ),
        "health": Field.at(6, 4, 1),
        "turbo": Field.at(6, 5, 1),
        # kTcl112AcTempMax - whole degrees (setTemp); HalfDegree adds 0.5.
        "temperature": Field.at(7, 0, 4, values={t: 31 - t for t in range(16, 32)}),
        "fan": Field.at(  # kTcl112AcFan{Auto,Min,Low,Med,High}
            8, 0, 3, values={"auto": 0, "1": 1, "2": 2, "3": 3, "4": 5}
        ),
        "swing_v": Field.at(  # kTcl112AcSwingV{Off,Highest,...,Lowest,On}
            8,
            3,
            3,
            values={"off": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "auto": 7},
        ),
        "timer_indicator": Field.at(8, 6, 1),
        "off_timer": Field.at(9, 1, 6),
        "on_timer": Field.at(10, 1, 6),
        "swing_h": Field.at(12, 3, 1, values={"off": 0, "swing": 1}),
        "half_degree": Field.at(12, 5, 1),
        "model": Field.at(12, 7, 1, values=TCL112AC_MODEL),  # isTcl
    },
    Sum8(0, 13, 13),  # IRTcl112Ac::calcChecksum, normal message
)

# The special message: IRTcl112Ac::send's quiet_off state (issue 1528) with
# setQuiet's Quiet bit. It is the same for both remote models.
TCL112AC_QUIET_LAYOUT = Layout(
    bytes([0x23, 0xCB, 0x26, 0x02, 0x00, 0x40]) + bytes(8),
    {
        "msg_type": Field.at(3, 0, 2, values=TCL112AC_MSG_TYPE),
        "quiet": Field.at(5, 5, 1),
    },
    Sum8(0, 13, 13, init=0xF),  # IRTcl112Ac::calcChecksum, special: sum + 0xF
)

TCL112AC_MIN = 16  # kTcl112AcTempMin
TCL112AC_MAX = 31  # kTcl112AcTempMax


class Tcl112AcDevice(Device):
    """TCL 112-bit (TCL112AC), both remote models of tcl_ac_remote_model_t:
    TAC09CHSD (isTcl set) and GZ055BE1 (isTcl clear). The variant comes from
    the model (MODELS) unless given, so the registry's ``cls(brand, model)``
    call picks it; unknown models get TAC09CHSD, as IRTcl112Ac::setModel
    does for any model but GZ055BE1.

    As IRac::tcl112 sends it, every setting goes in full in the normal
    message:
    - an off message carries mode auto (IRac passes mode "off", which
      convertMode maps to its default, kTcl112AcAuto);
    - the setpoint is kTcl112AcTempMin..kTcl112AcTempMax in half degrees:
      Temp holds the whole degrees, HalfDegree the half (setTemp);
    - powerful sets Turbo, and setTurbo (called after setFan and
      setSwingVertical) forces kTcl112AcFanHigh and kTcl112AcSwingVOn;
    - purifier sets Health; the Light bit is cleared when the light is on.

    Quiet only travels in the special message, which IRTcl112Ac::send sends
    before the normal one when quiet differs from the last quiet it sent.
    IRac builds a fresh object for every message, so C sends it (quiet on)
    whenever quiet is on and never sends quiet off. With ``previous=None``
    the port does the same. With ``previous``, it sends the special message
    only when quiet changes, both ways, as IRTcl112Ac::send's own rule does:
    a deliberate deviation from the C path, which can never turn quiet off.

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_tcl112ac_device.py):
    - swing_v "1"/"2" (90°/60°): the old glue maps them to kHigh and
      kUpperMiddle, which convertSwingV turns into kTcl112AcSwingVHigh and
      (no case) kTcl112AcSwingVOn; the port sends Highest and High;
    - swing_h "swing": the old glue has no swing "on", so IRac's swingh
      stays kOff; the port sets SwingH;
    - GZ055BE1 after a quiet message: IRTcl112Ac::send sets isTcl in the
      normal message that follows the special one, whatever the model; the
      port keeps isTcl clear, as setModel(GZ055BE1) writes it.
    """

    PROTOCOL = TCL112AC
    LAYOUTS = (TCL112AC_LAYOUT,)
    capabilities = Capabilities(
        modes=("auto", "cool", "dry", "fan", "heat"),  # kTcl112Ac{Auto,...}
        # kTcl112AcTempMin..kTcl112AcTempMax, 0.5 steps (HalfDegree)
        temperature=TemperatureRange(TCL112AC_MIN, TCL112AC_MAX, (0, 5)),
        fan=FAN_4,
        swing_v=SWING_V_ANGLES,
        swing_h=SWING,
        features={
            "quiet": ON_OFF,
            "purifier": ON_OFF,
            "light": ON_OFF,
            "powerful": ON_OFF,
            "economy": ON_OFF,
        },
    )
    MODELS = {}  # model -> remote variant, filled below

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        self.variant = variant or self.MODELS.get(model, "TAC09CHSD")
        if self.variant not in TCL112AC_MODEL:
            raise ValueError(f"unknown Tcl112Ac variant {self.variant!r}")

    def sends_quiet(self, previous, target):
        """Whether the special (quiet) message goes before the normal one."""
        quiet = target.features["quiet"]
        if previous is None:
            return quiet  # a fresh IRTcl112Ac: its last quiet sent is off
        return quiet != previous.features["quiet"]

    def frames(self, previous, target, actions):
        features = target.features
        powerful = features["powerful"]
        main = TCL112AC_LAYOUT.build(
            power=target.power,
            light=features["light"],
            econo=features["economy"],
            mode=target.mode if target.power else "auto",
            health=features["purifier"],
            turbo=powerful,
            temperature=min(max(int(target.temperature), TCL112AC_MIN), TCL112AC_MAX),
            half_degree=target.temperature % 1 == 0.5,
            # setTurbo(true) forces kTcl112AcFanHigh and kTcl112AcSwingVOn.
            fan="4" if powerful else target.fan,
            swing_v="auto" if powerful else target.swing_v,
            swing_h=target.swing_h,
            model=self.variant,
        )
        out = [Frame("main", bytes(main))]
        if self.sends_quiet(previous, target):
            quiet = TCL112AC_QUIET_LAYOUT.build(quiet=features["quiet"])
            out.insert(0, Frame("quiet", bytes(quiet)))
        return out


TCL112AC_MODELS = {  # model -> remote variant (tcl_ac_remote_model_t)
    "TAC-09CHSD/XA31I": "TAC09CHSD",
    "generic": "TAC09CHSD",
    "generic v1": "TAC09CHSD",
    "generic v2": "GZ055BE1",
}
TCL112AC_DAEWOO_MODELS = {  # daewoo plugin
    "DSB-F0934ELH-V": "GZ055BE1",
    "GYKQ-52E remote": "GZ055BE1",
}
TCL112AC_TECHNOPOINT_MODELS = {  # technopoint plugin
    "Allegro SSA-09H": "GZ055BE1",
    "GZ-055B-E1 remote": "GZ055BE1",
}
TCL112AC_LEBERG_MODELS = {"LBS-TOR07": "TAC09CHSD"}  # leberg plugin
Tcl112AcDevice.MODELS = {
    **TCL112AC_MODELS,
    **TCL112AC_DAEWOO_MODELS,
    **TCL112AC_TECHNOPOINT_MODELS,
    **TCL112AC_LEBERG_MODELS,
}


# Now the match between models and objects
