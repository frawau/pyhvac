#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Plugin to generate Airspool (Tuya-style mini-split) AC IR commands.
#
# Protocol reverse-engineered and documented at:
#   https://twosortoftechguys.wordpress.com/2026/06/14/sending-ir-codes-to-an-airspool-mini-split-using-a-raspberry-pi-ai-failed-us-2/
#
# Several fields are only partially understood; they are flagged UNVERIFIED /
# UNKNOWN in the code below and should not be trusted blindly.
#
# Copyright (c) 2026 François Wautier
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

from .hvaclib import HVAC, GenPluginObject, bit_reverse


class Airspool(HVAC):
    """Airspool mini-split (Tuya-style) HVAC object.

    Physical layer: 38 kHz carrier, pulse-distance encoding, LSB-first within
    each byte (handled by ``is_msb`` which swaps the bit order at build time so
    the MSB-first emitter in :class:`HVAC` produces an LSB-first wire stream).

      Header   : ~3200 us mark, ~1400 us space
      Bit mark : ~480 us (constant)
      Bit 0    : ~360 us space
      Bit 1    : ~1180 us space
      Trailer  : one final ~480 us stop mark, then a long trailing gap

    Frame: 14 bytes (112 bits) + stop mark.

      byte 0-3 : 23 CB 26 01   fixed header / address
      byte 4   : setpoint temperature, BCD of the value in degF (75 -> 0x75).
                 The device is degF-native; the public API takes degC (the
                 library convention) and converts to the nearest degF.
      byte 5   : flags  (0x04 power on, 0x40 turbo, 0x80 "SE" = Save Energy)
      byte 6   : low nibble = mode (1=heat, 2=dehumidify, 3=cool); 0x20 display,
                 0x40 energy-saver (the "energy saver speed control"); heat
                 carries the fixed 0xE0 high-bit signature
      byte 7   : reserved (00)
      byte 8   : airflow bitfield (fan/sleep enum, vertical louver, turbo)
      byte 9-10: reserved (00)
      byte 11  : horizontal swing (0xE0 = off, 0x00 = on)
      byte 12  : reserved (00)
      byte 13  : checksum = sum(byte 0..12) & 0xFF
    """

    # Physical-layer timings (microseconds).
    STARTFRAME = [3200, 1400]
    # Final stop mark, then a long trailing gap before any repeat.  The exact
    # gap length is not part of the documented capture; 100 ms is a safe value.
    ENDFRAME = [480, 100000]
    MARK = [480]  # constant bit mark
    SPACE = [360, 1180]  # SPACE[0] -> bit 0, SPACE[-1] -> bit 1

    # Fixed skeleton, bytes 0..12 (the checksum, byte 13, is appended later).
    FBODY = b"\x23\xcb\x26\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00"

    # Airflow enum (byte 8, bits 0-2).  Non-monotonic lookup table, NOT a
    # "speed = N" scale.  Decoded from the fan1..fan6 panel captures; the
    # panel's "fan6" is the auto setting (enum 0, also the power-on default):
    #   0 = auto, 1 = sleep, 2 = fan1, 3 = fan3, 4 = fan2, 5 = fan5, 6 = fan4
    # (value 7 is unused / unobserved.)
    FAN_ENUM = {"auto": 0, "fan1": 2, "fan2": 4, "fan3": 3, "fan4": 6, "fan5": 5}
    SLEEP_ENUM = 1

    # Mode low nibble (byte 6, bits 0-3).
    #   1 = heat, 2 = dehumidify, 3 = cool
    # (4 = fan-only / 0 = auto are UNVERIFIED and therefore not exposed.)
    MODE_NIBBLE = {"heat": 0x01, "dry": 0x02, "cool": 0x03}

    def __init__(self):
        super().__init__()
        self.brand = "Airspool"
        self.model = "Generic"
        self.capabilities = {
            "mode": ["cool", "dry", "heat"],
            # The public API works in degC (library convention); values are
            # converted to the nearest degF and BCD-encoded into byte 4.  The
            # device is degF-native (61-86 degF), so degC is exposed at 0.5 degC
            # resolution: that is fine enough to reach every distinct degF
            # setpoint exactly.  A few adjacent 0.5-degC steps round to the same
            # degF (e.g. 17.5 and 18.0 both -> 64 degF), which is harmless.
            "temperature": [x / 2 for x in range(32, 61)],
            "fan": ["auto", "fan1", "fan2", "fan3", "fan4", "fan5"],
            "sleep": ["off", "on"],
            "swing": ["off", "on"],  # vertical louver (0x38 = full swing)
            "hswing": ["off", "on"],  # horizontal swing
            # byte 6, 0x40: the "energy saver speed control" (formerly guessed
            # to be a generic eco flag).
            "energy_saver": ["off", "on"],
            "display": ["off", "on"],
            "turbo": ["off", "on"],
            "power": ["off", "on"],
            # byte 5, 0x80: "SE" = Save Energy.  The remote only toggles it on/
            # off; the 25/50/75% panel steps are not individually IR-addressable.
            "se": ["off", "on"],
        }
        self.xtra_capabilities = {}
        self.status = {
            "mode": "cool",
            "temperature": 24,  # degC (~75 degF)
            "fan": "auto",
            "sleep": "off",
            "swing": "off",
            "hswing": "off",
            "energy_saver": "off",
            "display": "on",
            "turbo": "off",
            "power": "on",
            "se": "off",
        }
        self.to_set = {}
        # LSB-first on the wire: swap the bit order of every byte at build time.
        self.is_msb = True

    # ------------------------------------------------------------------ helpers
    def _val(self, key):
        """Return the pending (to_set) value for ``key`` else the current one."""
        if key in self.to_set:
            return self.to_set[key]
        return self.status.get(key)

    def _on(self, key):
        return self._val(key) == "on"

    def _empty_mask(self):
        return bytearray(len(self.FBODY))

    # ------------------------------------------------------------------ setters
    def _set_choice(self, name, value):
        if name not in self.capabilities:
            return
        if value not in self.capabilities[name]:
            return
        self.to_set[name] = value

    def set_mode(self, mode):
        if mode == "dehumidify":
            mode = "dry"
        self._set_choice("mode", mode)

    def set_temperature(self, temp):
        # Input is degC (library convention); kept in degC and converted to
        # degF at encoding time (see code_temperature).
        lo, hi = (
            self.capabilities["temperature"][0],
            self.capabilities["temperature"][-1],
        )
        temp = max(lo, min(hi, temp))
        self.to_set["temperature"] = temp

    @staticmethod
    def c_to_f(temp_c):
        # Device is degF-native; round to the nearest whole degF.
        return round(temp_c * 9 / 5 + 32)

    def set_fan(self, mode):
        self._set_choice("fan", mode)

    def set_sleep(self, mode):
        self._set_choice("sleep", mode)

    def set_swing(self, mode):
        self._set_choice("swing", mode)

    def set_hswing(self, mode):
        self._set_choice("hswing", mode)

    def set_energy_saver(self, mode):
        self._set_choice("energy_saver", mode)

    def set_display(self, mode):
        self._set_choice("display", mode)

    def set_turbo(self, mode):
        self._set_choice("turbo", mode)

    def set_power(self, mode):
        self._set_choice("power", mode)

    def set_se(self, mode):
        # "SE" = Save Energy (byte 5, 0x80); on/off only.
        self._set_choice("se", mode)

    # ------------------------------------------------------------------ coders
    def code_temperature(self):
        # byte 4: BCD of the degF value (e.g. 75 -> 0x75).  The stored setpoint
        # is degC; convert to degF first.  Only two-digit Fahrenheit setpoints
        # are representable.
        temp_f = self.c_to_f(self._val("temperature"))
        mask = self._empty_mask()
        mask[4] = ((temp_f // 10) << 4) | (temp_f % 10)
        return mask

    def code_power(self):
        # byte 5, 0x04 = power on.
        mask = self._empty_mask()
        if self._on("power"):
            mask[5] |= 0x04
        return mask

    def code_se(self):
        # byte 5, 0x80 = "SE" (Save Energy).  On/off toggle only.
        mask = self._empty_mask()
        if self._on("se"):
            mask[5] |= 0x80
        return mask

    def code_turbo(self):
        # Turbo sets byte 5 bit 0x40 *and* byte 8 bit 0x40.
        mask = self._empty_mask()
        if self._on("turbo"):
            mask[5] |= 0x40
            mask[8] |= 0x40
        return mask

    def code_mode(self):
        # byte 6 low nibble = mode.  Heat additionally carries the fixed 0xE0
        # high-bit signature (so heat always reads 0xE1).  We treat those high
        # bits as part of the heat mode signature rather than user-controllable
        # energy-saver/display flags.
        mode = self._val("mode")
        mask = self._empty_mask()
        mask[6] |= self.MODE_NIBBLE.get(mode, self.MODE_NIBBLE["cool"])
        if mode == "heat":
            # UNVERIFIED: heat also asserts 0x40+0x80; bundled as a signature.
            mask[6] |= 0xE0
        return mask

    def code_display(self):
        # byte 6, 0x20 = display/light on.  Only treated as a togglable bit in
        # cool/dehumidify; in heat the bit is already part of the 0xE0
        # signature (see code_mode), so OR-ing it here is harmless.
        mask = self._empty_mask()
        if self._on("display"):
            mask[6] |= 0x20
        return mask

    def code_energy_saver(self):
        # byte 6, 0x40 = energy-saver ("energy saver speed control").  Togglable
        # only in cool/dehumidify; in heat it is part of the 0xE0 signature.
        mask = self._empty_mask()
        if self._on("energy_saver"):
            mask[6] |= 0x40
        return mask

    def code_airflow(self):
        # byte 8 bits 0-2: fan/sleep enum (mutually exclusive - the field holds
        # exactly one value).  Sleep wins over an explicit fan speed.  The fan
        # is independent of the mode (the dehumidify capture happens to use
        # fan1, but there is no evidence the mode locks the fan).
        mask = self._empty_mask()
        if self._on("sleep"):
            mask[8] |= self.SLEEP_ENUM
        else:
            mask[8] |= self.FAN_ENUM.get(self._val("fan"), 0)
        return mask

    def code_swing(self):
        # byte 8 bits 3-5: vertical louver.  0x38 = full swing.  Fixed louver
        # positions are UNVERIFIED, so only off/full-swing is exposed.
        mask = self._empty_mask()
        if self._on("swing"):
            mask[8] |= 0x38
        return mask

    def code_hswing(self):
        # byte 11: horizontal swing.  0xE0 = off, 0x00 = on.
        mask = self._empty_mask()
        if not self._on("hswing"):
            mask[11] |= 0xE0
        return mask

    # ------------------------------------------------------------------ assembly
    def checksum(self, body):
        # byte 13 = sum of bytes 0..12, truncated to 8 bits.  Computed on the
        # logical (pre bit-reversal) frame.
        return (sum(body) & 0xFF).to_bytes(1, "big")

    def _build_ircode(self):
        coders = [
            self.code_temperature,
            self.code_power,
            self.code_se,
            self.code_turbo,
            self.code_mode,
            self.code_display,
            self.code_energy_saver,
            self.code_airflow,
            self.code_swing,
            self.code_hswing,
        ]
        body = bytearray(self.FBODY)
        for coder in coders:
            mask = coder()
            body = bytearray(x | y for x, y in zip(body, mask))
        body += self.checksum(body)
        return [body]

    # ------------------------------------------------------------------ decoding
    def decode_pulse(self, pulse, endian="msb"):
        """Decode an Airspool LIRC pulse train back into the logical byte frame.

        ``pulse`` is a flat list of timings as produced by ``to_lirc`` (header,
        then a (mark, space) pair per bit).  Returns the 14-byte logical frame,
        i.e. what ``_build_ircode`` produced before the LSB-first bit swap.
        """
        p = list(pulse)
        i = len(self.STARTFRAME)  # skip the header
        nbits = len(self.FBODY + b"\x00") * 8  # 14 bytes
        bits = []
        for _ in range(nbits):
            space = p[i + 1]
            # classify the space against the two known durations
            bit = 1 if abs(space - self.SPACE[-1]) < abs(space - self.SPACE[0]) else 0
            bits.append(bit)
            i += 2
        # bits were emitted MSB-first per wire byte
        wire = bytearray()
        for b in range(nbits // 8):
            val = 0
            for k in range(8):
                val = (val << 1) | bits[b * 8 + k]
            wire.append(val)
        if self.is_msb:
            # undo the LSB-first wire encoding to recover the logical frame
            wire = bytearray(bit_reverse(x) for x in wire)
        return wire


class PluginObject(GenPluginObject):
    MODELS = {
        "generic": Airspool,
        "airspool": Airspool,
        "airspool mini-split": Airspool,
    }

    def __init__(self):
        self.brand = "airspool"


def main():
    import argparse
    import base64

    parser = argparse.ArgumentParser(description="Generate Airspool A/C codes.")
    parser.add_argument(
        "-M",
        "--model",
        type=str,
        default="generic",
        help="Set the A/C model. (default generic).",
    )
    parser.add_argument(
        "-L",
        "--list",
        action="store_true",
        default=False,
        help="List known models and return.",
    )
    parser.add_argument(
        "-t",
        "--temp",
        type=float,
        default=24,
        help="Temperature (degC at 0.5 resolution, converted to nearest degF). "
        "(default 24).",
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=["cool", "dry", "dehumidify", "heat"],
        default="cool",
        help="Mode, one of 'cool', 'dry'/'dehumidify' or 'heat'. (default 'cool').",
    )
    parser.add_argument(
        "-f",
        "--fan",
        choices=["auto", "fan1", "fan2", "fan3", "fan4", "fan5"],
        default="auto",
        help="Fan speed. (default 'auto').",
    )
    parser.add_argument(
        "-S", "--sleep", action="store_true", default=False, help="Sleep mode"
    )
    parser.add_argument(
        "-s", "--swing", action="store_true", default=False, help="Vertical swing"
    )
    parser.add_argument(
        "-z",
        "--hswing",
        action="store_true",
        default=False,
        help="Horizontal swing",
    )
    parser.add_argument(
        "-e",
        "--energy-saver",
        dest="energy_saver",
        action="store_true",
        default=False,
        help="Energy-saver speed control",
    )
    parser.add_argument(
        "-d",
        "--no-display",
        dest="display",
        action="store_false",
        default=True,
        help="Turn the display/light off",
    )
    parser.add_argument(
        "-p", "--turbo", action="store_true", default=False, help="Turbo mode"
    )
    parser.add_argument(
        "-x",
        "--se",
        action="store_true",
        default=False,
        help="Enable SE (Save Energy)",
    )
    parser.add_argument(
        "-O",
        "--off",
        action="store_true",
        default=False,
        help="Power the unit off",
    )
    parser.add_argument(
        "-l",
        "--lirc",
        action="store_true",
        default=False,
        help="Output LIRC compatible timing",
    )
    parser.add_argument(
        "-b",
        "--broadlink",
        action="store_true",
        default=False,
        help="Output Broadlink timing",
    )
    parser.add_argument(
        "-B",
        "--base64",
        action="store_true",
        default=False,
        help="Output Broadlink timing base64 encoded",
    )

    try:
        opts = parser.parse_args()
    except Exception as e:
        parser.error("Error: " + str(e))

    if opts.list:
        print(f"Available models are: {[x for x in PluginObject().MODELS.keys()]}")
        return

    device = PluginObject().get_device(opts.model)
    device.set_power((not opts.off and "on") or "off")
    device.set_mode(opts.mode)
    device.set_temperature(opts.temp)
    device.set_fan(opts.fan)
    device.set_sleep((opts.sleep and "on") or "off")
    device.set_swing((opts.swing and "on") or "off")
    device.set_hswing((opts.hswing and "on") or "off")
    device.set_energy_saver((opts.energy_saver and "on") or "off")
    device.set_display((opts.display and "on") or "off")
    device.set_turbo((opts.turbo and "on") or "off")
    device.set_se((opts.se and "on") or "off")

    frames = device.build_ircode()

    if opts.lirc:
        lircf = device.to_lirc(frames)
        while lircf:
            print("\t".join(["%d" % x for x in lircf[:6]]))
            lircf = lircf[6:]
    elif opts.broadlink or opts.base64:
        bframe = device.to_broadlink(frames)
        if opts.base64:
            print("{}".format(str(base64.b64encode(bframe), "ascii")))
        else:
            print("{}".format(bframe.hex()))
    else:
        for f in frames:
            print(" ".join(["%02x" % x for x in f]))


if __name__ == "__main__":
    main()
