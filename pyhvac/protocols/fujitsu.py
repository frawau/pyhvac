#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Fujitsu AC IR commands.
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
from ..fields import Copy, Field, Layout, Sum8
from ..ir.model import Frame, Protocol, PulseDistance, Section
from ..choices import FAN_4, ON_OFF, SWING
from ..state import Capabilities, TemperatureRange

# ----------------------------------------------------------------- FujitsuAc
# Layout from IRremoteESP8266's FujitsuProtocol (ir_Fujitsu.h). sendFujitsuAC
# is sendGeneric with kFujitsuAcHdrMark/HdrSpace, kFujitsuAcBitMark,
# kFujitsuAcOneSpace/ZeroSpace, a kFujitsuAcBitMark footer and
# kFujitsuAcMinGap, LSB first, 38 kHz, no repeat (kFujitsuAcMinRepeat is
# kNoRepeat).
#
# A message is a long code (the full state: kFujitsuAcStateLength bytes, one
# less for the ARDB1 and ARJW2 remotes) or a short code (a command in byte 5,
# Cmd: kFujitsuAcStateLengthShort bytes, one less for ARDB1 and ARJW2).
# IRFujitsuAC::stateReset zeroes the whole long code and IRFujitsuAC::checkSum
# writes every byte of a short one, so no bit comes from stale memory.

FUJITSU_AC = Protocol(
    "fujitsu_ac",
    {
        "main": Section(
            PulseDistance(448, 390, 1182),  # kFujitsuAcBitMark/ZeroSpace/OneSpace
            header=(3324, 1574),  # kFujitsuAcHdrMark / HdrSpace
            footer=(448,),  # kFujitsuAcBitMark
            gap=8100,  # kFujitsuAcMinGap
        )
    },
    carrier=38000,
    # decodeFujitsuAC: header and bits with _tolerance +
    # kFujitsuAcExtraTolerance (30 %) and mark excess 0 (the footer mark with
    # the defaults).
    tolerance=0.30,
    mark_excess=0,
)

# kFujitsuAcMode{Auto,Cool,Dry,Fan,Heat}
FUJITSU_AC_MODE = {"auto": 0, "cool": 1, "dry": 2, "fan": 3, "heat": 4}
# kFujitsuAcFan{Auto,High,Med,Low,Quiet}
FUJITSU_AC_FAN = {"auto": 0, "high": 1, "medium": 2, "low": 3, "quiet": 4}
# IRFujitsuAC::convertFan: kMin (the legacy "lowest") is kFujitsuAcFanQuiet.
FUJITSU_AC_FAN_BY_LEVEL = {
    "auto": "auto",
    "1": "quiet",
    "2": "low",
    "3": "medium",
    "4": "high",
}
# kFujitsuAcSwing{Off,Vert,Horiz,Both}
FUJITSU_AC_SWING = {"off": 0, "vert": 1, "horiz": 2, "both": 3}
FUJITSU_AC_CMD = {
    "turn_off": 0x02,  # kFujitsuAcCmdTurnOff
    "econo": 0x09,  # kFujitsuAcCmdEcono
    "powerful": 0x39,  # kFujitsuAcCmdPowerful
    "step_vert": 0x6C,  # kFujitsuAcCmdStepVert
    "toggle_swing_vert": 0x6D,  # kFujitsuAcCmdToggleSwingVert
    "step_horiz": 0x79,  # kFujitsuAcCmdStepHoriz
    "toggle_swing_horiz": 0x7A,  # kFujitsuAcCmdToggleSwingHoriz
    # IRFujitsuAC::updateUseLongOrShort: a long code's Cmd byte.
    "long": 0xFE,  # ARRAH2E, ARREB1E, ARRY4, ARREW4E
    "long_ardb1": 0xFC,  # ARDB1, ARJW2
}
FUJITSU_AC_MIN_TEMP, FUJITSU_AC_MAX_TEMP = 16, 30  # kFujitsuAcMinTemp / MaxTemp


def _fujitsu_ac_header_fields():
    return {
        "id": Field.at(2, 4, 2),  # Id (IRac never sets it)
        "cmd": Field.at(5, 0, 8, values=FUJITSU_AC_CMD),
    }


def _fujitsu_ac_state_fields():
    return {
        **_fujitsu_ac_header_fields(),
        "rest_length": Field.at(6, 0, 8),  # RestLength: byte count - 7
        "protocol": Field.at(7, 0, 8),  # Protocol: 0x31 for ARREW4E, else 0x30
        "power": Field.at(8, 0, 1),
        "fahrenheit": Field.at(8, 1, 1),
        # Temp: (C - kFujitsuAcTempOffsetC) * 4, or for ARREW4E
        # (C - kFujitsuAcTempOffsetC / 2) * 2 (IRFujitsuAC::setTemp).
        "temp": Field.at(8, 2, 6),
        "mode": Field.at(9, 0, 3, values=FUJITSU_AC_MODE),
        "clean": Field.at(9, 3, 1),  # Clean (10C Heat on ARREW4E)
        "timer_type": Field.at(9, 4, 2),
        "fan": Field.at(10, 0, 3, values=FUJITSU_AC_FAN),
        "swing": Field.at(10, 4, 2, values=FUJITSU_AC_SWING),
        "off_timer": Field.at(11, 0, 11),  # also the sleep timer
        "off_timer_enable": Field.at(12, 3, 1),
        "on_timer": Field.at(12, 4, 11),
        "on_timer_enable": Field.at(13, 7, 1),
    }


# The long code, 16 bytes (ARRAH2E, ARREB1E, ARRY4, ARREW4E). Skeleton:
# stateReset's fixed bytes 0x14 0x63 _ 0x10 0x10, the long Cmd, RestLength 9
# and Protocol 0x30, everything else clear. The checksum (byte 15) is minus
# the sum of bytes 7-14 (kFujitsuAcStateLengthShort onwards).
FUJITSU_AC_LONG_LAYOUT = Layout(
    bytes.fromhex("14630010 10fe0930 00000000 00000000"),
    {
        **_fujitsu_ac_state_fields(),
        "filter": Field.at(14, 3, 1),
        "unknown": Field.at(14, 5, 1),
        "outside_quiet": Field.at(14, 7, 1),
    },
    checksum=Sum8(7, 15, 15, base=0),  # IRFujitsuAC::checkSum: 0 - sum
)

# The long code of the ARDB1 and ARJW2 remotes, 15 bytes (RestLength 8, Cmd
# 0xFC): byte 14 is the checksum, 0x9B minus the sum of bytes 0-13, so the
# struct's byte 14 fields are never sent.
FUJITSU_AC_LONG15_LAYOUT = Layout(
    bytes.fromhex("14630010 10fc0830 00000000 000000"),
    _fujitsu_ac_state_fields(),
    checksum=Sum8(0, 14, 14, base=0x9B),  # IRFujitsuAC::checkSum: 0x9B - sum
)

# The short code, 7 bytes: the long code's bytes 0-5 (Cmd a command), then
# the complement of byte 5.
FUJITSU_AC_SHORT_LAYOUT = Layout(
    bytes.fromhex("14630010 1002fd"),
    _fujitsu_ac_header_fields(),
    checksum=Copy(5, 6, 6, invert=True),
)

# The short code of the ARDB1 and ARJW2 remotes, 6 bytes, with no check byte.
FUJITSU_AC_SHORT6_LAYOUT = Layout(
    bytes.fromhex("14630010 1002"), _fujitsu_ac_header_fields()
)


def _fujitsu_ac_capabilities(swing_v=SWING, swing_h=None, temperature=(0,), **features):
    """The remotes differ in swing, setpoint steps and features."""
    return Capabilities(
        modes=("auto", "cool", "dry", "fan", "heat"),
        # kFujitsuAcMinTemp / kFujitsuAcMaxTemp.
        temperature=TemperatureRange(
            float(FUJITSU_AC_MIN_TEMP), float(FUJITSU_AC_MAX_TEMP), temperature
        ),
        fan=FAN_4,
        swing_v=swing_v,
        swing_h=swing_h,
        features=features,
    )


# variant (fujitsu_ac_remote_model_t) -> what its messages carry.
# - ARDB1 and ARJW2 have no swing: IRFujitsuAC::checkSum forces Swing off in
#   their long code, and the swing commands (kFujitsuAcCmdToggleSwingVert /
#   Horiz) are short codes the port does not send (deferred);
# - ARREW4E's Temp counts half degrees ((C - kFujitsuAcTempOffsetC / 2) * 2,
#   getTemp returns 25.5 for the arrew4e_25_5c capture);
# - OutsideQuiet (ARREB1E, ARREW4E) and 10C Heat (ARRAH2E, ARREW4E) have no
#   feature name; the sleep timer is a timer.
FUJITSU_AC_CAPABILITIES = {
    "ARRAH2E": _fujitsu_ac_capabilities(swing_h=SWING, quiet=ON_OFF),
    "ARDB1": _fujitsu_ac_capabilities(swing_v=None, quiet=ON_OFF),
    "ARREB1E": _fujitsu_ac_capabilities(powerful=ON_OFF, quiet=ON_OFF, economy=ON_OFF),
    "ARJW2": _fujitsu_ac_capabilities(swing_v=None, quiet=ON_OFF),
    "ARRY4": _fujitsu_ac_capabilities(purifier=ON_OFF, quiet=ON_OFF, cleaning=ON_OFF),
    "ARREW4E": _fujitsu_ac_capabilities(
        swing_h=SWING,
        temperature=(0, 5),
        powerful=ON_OFF,
        quiet=ON_OFF,
        economy=ON_OFF,
    ),
}


class FujitsuAcDevice(Device):
    """Fujitsu A/C (IRFujitsuAC, protocol FUJITSU_AC), for the six remote
    variants (fujitsu_ac_remote_model_t: ARRAH2E, ARDB1, ARREB1E, ARJW2,
    ARRY4, ARREW4E). The variant comes from the model (FUJITSU_AC_VARIANT)
    unless given, and picks the capabilities; unknown models get ARRAH2E,
    IRFujitsuAC's default.

    As IRac::fujitsu sends it from a fresh IRFujitsuAC object:
    - power off sends only the short kFujitsuAcCmdTurnOff code, whatever the
      other settings;
    - power on sends the long code, with Power set (IRac calls on() last),
      the documented mode, the setpoint, the fan (quiet makes it
      kFujitsuAcFanQuiet), Swing, and for ARRY4 Filter (purifier) and Clean
      (cleaning); timers, Id, OutsideQuiet and Fahrenheit stay 0;
    - IRFujitsuAC::checkSum sets the "unknown" bit for ARRAH2E, ARREB1E and
      ARRY4, and forces Swing off for ARDB1 and ARJW2, which therefore
      offer no swing (the toggle-swing commands are never sent);
      IRFujitsuAC::setSwing keeps ARREB1E and ARRY4 to vertical swing;
    - powerful and economy are separate short commands (kFujitsuAcCmdPowerful,
      then kFujitsuAcCmdEcono) sent before the long code, for ARREB1E and
      ARREW4E only (IRFujitsuAC::setCmd).

    They are buttons: IRac::handleToggles sends turbo/econo only when they
    change (either way) from the previous message IRac sent. The port does
    the same with ``previous``; with ``previous=None`` it sends each one
    that is on, as a fresh IRac object does.

    Where the C path contradicts the header, the port sends the documented
    value (see the Defects in tests/test_fujitsu_ac_device.py): swing and
    swing_h "swing" set Swing (the old glue never passed swing "on" to C),
    and ARREW4E sends its powerful and economy commands, which
    IRac::fujitsu only sends for ARREB1E.
    """

    PROTOCOL = FUJITSU_AC
    capabilities = FUJITSU_AC_CAPABILITIES["ARRAH2E"]

    def __init__(self, brand, model, variant=None):
        super().__init__(brand, model)
        self.variant = variant or FUJITSU_AC_VARIANT.get(model, "ARRAH2E")
        if self.variant not in FUJITSU_AC_CAPABILITIES:
            raise ValueError(f"unknown Fujitsu A/C variant {self.variant!r}")
        self.capabilities = FUJITSU_AC_CAPABILITIES[self.variant]

    @property
    def short15(self):
        """Whether the variant sends the one-byte-shorter codes."""
        return self.variant in ("ARDB1", "ARJW2")

    def long_layout(self):
        return FUJITSU_AC_LONG15_LAYOUT if self.short15 else FUJITSU_AC_LONG_LAYOUT

    def short_layout(self):
        return FUJITSU_AC_SHORT6_LAYOUT if self.short15 else FUJITSU_AC_SHORT_LAYOUT

    def layouts(self, frames):
        """The layout of each frame of a message: short codes, then the long
        code last when the message has one."""
        long_size = len(self.long_layout().skeleton)
        return tuple(
            self.long_layout() if len(f.data) == long_size else self.short_layout()
            for f in frames
        )

    def command(self, name):
        return Frame("main", bytes(self.short_layout().build(cmd=name)))

    def commands(self, previous, target):
        """The powerful and economy button presses before the long code."""
        if self.variant not in ("ARREB1E", "ARREW4E"):
            return []
        out = []
        for feature, cmd in (("powerful", "powerful"), ("economy", "econo")):
            on = target.features[feature]
            if on if previous is None else on != previous.features[feature]:
                out.append(self.command(cmd))
        return out

    def swing(self, target):
        if self.short15:
            return "off"  # IRFujitsuAC::checkSum
        vert = target.swing_v not in (None, "off")
        # setSwing: ARREB1E and ARRY4 clamp to Vert (and have no swing_h).
        horiz = target.swing_h not in (None, "off")
        return {
            (False, False): "off",
            (True, False): "vert",
            (False, True): "horiz",
            (True, True): "both",
        }[vert, horiz]

    def long_code(self, target):
        features = target.features
        if self.variant == "ARREW4E":
            # Half degrees: the setpoint is a whole or .5 value (normalise).
            temp = round((target.temperature - FUJITSU_AC_MIN_TEMP / 2) * 2)
        else:
            temp = (int(target.temperature) - FUJITSU_AC_MIN_TEMP) * 4
        values = dict(
            power=1,
            temp=temp,
            mode=target.mode,
            fan="quiet" if features["quiet"] else FUJITSU_AC_FAN_BY_LEVEL[target.fan],
            swing=self.swing(target),
        )
        if self.variant == "ARREW4E":
            values["protocol"] = 0x31
        if self.variant in ("ARRAH2E", "ARREB1E", "ARRY4"):
            values["unknown"] = 1
        if self.variant == "ARRY4":
            values["filter"] = features["purifier"]
            values["clean"] = features["cleaning"]
        return Frame("main", bytes(self.long_layout().build(**values)))

    def frames(self, previous, target, actions):
        if not target.power:
            return [self.command("turn_off")]
        return self.commands(previous, target) + [self.long_code(target)]


# model -> remote variant (fujitsu_ac_remote_model_t), from the legacy
# classes: Fujitsuv1 ARRAH2E, v2 ARDB1, v3 ARREB1E, v4 ARJW2, v5 ARRY4,
# v6 ARREW4E.
FUJITSU_AC_VARIANT = {
    "AR-RAH2E remote": "ARRAH2E",
    "ASYG30LFCA": "ARRAH2E",
    "General AR-RCE1E remote": "ARRAH2E",
    "General ASHG09LLCA": "ARRAH2E",
    "General AOHG09LLC": "ARRAH2E",
    "AR-RAE1E remote": "ARRAH2E",
    "AGTV14LAC": "ARRAH2E",
    "AR-RAC1E remote": "ARRAH2E",
    "AR-RAH2U remote": "ARRAH2E",
    "AR-REG1U remote": "ARRAH2E",
    "General AR-RCL1E remote": "ARRAH2E",
    "generic": "ARRAH2E",
    "AR-DB1 remote": "ARDB1",
    "AST9RSGCW": "ARDB1",
    "AR-DL10 remote": "ARDB1",
    "ASU30C1": "ARDB1",
    "General AR-JW17 remote": "ARDB1",
    "generic 2": "ARDB1",
    "AR-REB1E remote": "ARREB1E",
    "ASYG7LMCA": "ARREB1E",
    "AR-RAH1U remote": "ARREB1E",
    "ASU12RLF": "ARREB1E",
    "AR-REB4E remote": "ARREB1E",
    "generic 3": "ARREB1E",
    "General AR-JW2 remote": "ARJW2",
    "generic 4": "ARJW2",
    "ASTB09LBC": "ARRY4",
    "AR-RY4 remote": "ARRY4",
    "generic 5": "ARRY4",
    "AR-REW4E remote": "ARREW4E",
    "ASYG09KETA-B": "ARREW4E",
    "ASTG09K": "ARREW4E",
    "ASTG18K": "ARREW4E",
    "AR-REW1E remote": "ARREW4E",
    "generic 6": "ARREW4E",
}
FUJITSU_AC_MODELS = tuple(FUJITSU_AC_VARIANT)


# Now the match between models and objects
