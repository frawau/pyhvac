#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Interactive probe to map out the Airspool energy-saver / limiter behaviour.
#
# It sends a scripted sequence of IR frames to the air conditioner through a
# LIRC transmit device (default /dev/lirc0, using the `ir-ctl` command that you
# already use) and, after each frame, tells you what we EXPECT and asks you what
# the wall unit's display ACTUALLY shows.
#
# What the remote's manual tells us about the two buttons involved:
#
#   * "SE"  (byte 5, bit 0x80) is one of two on/off limiter toggles.  Its twin,
#     labelled "AC Power limiter", sits opposite it; we do not yet have a
#     capture for that second toggle -- section 6 hunts for it.
#   * The button above SLEEP is "Energy saver / AC limiter speed control"
#     (byte 6, bit 0x40).  The word "speed control" is the key: it is a
#     MOMENTARY button that cycles the level, not a state you leave on.
#
# The big questions:
#
#   Q1 (sections 2-3): Is the limiter LEVEL (.1 / .2 / .3 after the temperature)
#      written into the IR frame, or is it a counter the unit keeps itself and
#      bumps each time the "speed control" frame changes?  The manual calling
#      byte 6 0x40 a "speed control" button points hard at the second answer;
#      these sections prove it.
#   Q2 (section 6): Is there a SECOND limiter toggle ("AC Power limiter") on a
#      bit we currently treat as reserved?
#
# Nothing here changes the pyhvac library.  It only builds frames with it and
# hands the timings to `ir-ctl`.  You can run it with --dry-run to see the whole
# sequence (and the frames) without transmitting anything.
#
# Copyright (c) 2026 François Wautier -- same MIT licence as the rest of pyhvac.

import argparse
import subprocess
import sys
import tempfile

from pyhvac.plugins.airspool import PluginObject
from pyhvac.plugins.hvaclib import bit_reverse


# --------------------------------------------------------------------------- IR
def _make_device(**settings):
    """Return a fresh Airspool device configured from the given settings."""
    dev = PluginObject().get_device("airspool")
    dev.set_power(settings.get("power", "on"))
    dev.set_mode(settings.get("mode", "cool"))
    dev.set_temperature(settings.get("temperature", 23))
    dev.set_fan(settings.get("fan", "auto"))
    dev.set_sleep(settings.get("sleep", "off"))
    dev.set_swing(settings.get("swing", "off"))
    dev.set_hswing(settings.get("hswing", "off"))
    dev.set_display(settings.get("display", "on"))
    dev.set_turbo(settings.get("turbo", "off"))
    dev.set_se_step(settings.get("se_step", "off"))
    dev.set_se(settings.get("se", "off"))
    return dev


def build_lirc(**settings):
    """Build the LIRC timing list for one Airspool frame.

    Every call starts from a fresh device so there is no leftover state; only
    the keys you pass differ from the sensible defaults below.
    """
    dev = _make_device(**settings)
    logical = dev._build_ircode()[0]
    lirc = dev.to_lirc(dev.build_ircode())
    return lirc, logical


def build_lirc_raw(byte_index, bit_mask, **settings):
    """Build a frame from the normal settings, then force raw bits in one byte.

    Used by section 6 to poke bits the ``set_*`` API does not expose: we OR
    ``bit_mask`` into ``logical[byte_index]`` (bytes 0..12 only), recompute the
    checksum, then bit-reverse to the wire order and produce LIRC timings.
    """
    dev = _make_device(**settings)
    logical = bytearray(dev._build_ircode()[0])
    logical[byte_index] |= bit_mask
    logical[13] = sum(logical[0:13]) & 0xFF  # recompute checksum over 0..12
    wire = bytearray(bit_reverse(x) for x in logical)  # is_msb -> LSB-first wire
    lirc = dev.to_lirc([wire])
    return lirc, logical


def send(lirc, device_path):
    """Write the timings to a temp file and hand it to `ir-ctl`."""
    text = " ".join(str(int(x)) for x in lirc)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
        fh.write(text + "\n")
        path = fh.name
    subprocess.run(["ir-ctl", "-d", device_path, "-s", path], check=True)


# ---------------------------------------------------------------------- helpers
def hexframe(logical):
    return " ".join("%02x" % b for b in logical)


def ask(prompt):
    """Ask a free-form question; blank answer allowed; Ctrl-C / q aborts."""
    try:
        answer = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.")
        sys.exit(1)
    if answer.lower() in ("q", "quit", "exit"):
        print("Aborted.")
        sys.exit(1)
    return answer


def wait(prompt="Press Enter to send this frame (or q to quit)... "):
    ask(prompt)


# ------------------------------------------------------------------------- flow
class Probe:
    def __init__(self, device_path, dry_run):
        self.device_path = device_path
        self.dry_run = dry_run
        self.log = []  # list of (label, expectation, observation)

    def step(self, label, expectation, question, **settings):
        lirc, logical = build_lirc(**settings)
        print()
        print("=" * 72)
        print(f"STEP: {label}")
        print(f"Frame (logical hex): {hexframe(logical)}")
        print(f"What we expect     : {expectation}")
        print("-" * 72)
        if self.dry_run:
            print("[dry-run] not transmitting.")
            self.log.append((label, expectation, "(dry-run)"))
            return
        wait()
        send(lirc, self.device_path)
        obs = ask(f"{question} ")
        self.log.append((label, expectation, obs))

    def raw_step(self, label, byte_index, bit_mask, expectation, question, **settings):
        lirc, logical = build_lirc_raw(byte_index, bit_mask, **settings)
        print()
        print("=" * 72)
        print(f"STEP: {label}")
        print(f"Frame (logical hex): {hexframe(logical)}")
        print(f"What we expect     : {expectation}")
        print("-" * 72)
        if self.dry_run:
            print("[dry-run] not transmitting.")
            self.log.append((label, expectation, "(dry-run)"))
            return
        wait()
        send(lirc, self.device_path)
        obs = ask(f"{question} ")
        self.log.append((label, expectation, obs))

    def banner(self, text):
        print()
        print("#" * 72)
        print(f"# {text}")
        print("#" * 72)
        if not self.dry_run:
            ask("Press Enter when you are ready and watching the unit's display... ")

    def summary(self):
        print()
        print("=" * 72)
        print("SUMMARY OF WHAT YOU OBSERVED")
        print("=" * 72)
        for label, expectation, obs in self.log:
            print(f"\n- {label}")
            print(f"    expected : {expectation}")
            print(f"    observed : {obs}")
        print()
        print(
            "Q1 - section 2 is decisive: if the level at 'X again (identical to\n"
            "the first X)' is the SAME as the first X, the level is written into\n"
            "the frame (absolute) and we can set it directly.  If it kept\n"
            "climbing, the unit counts presses itself and the frame cannot\n"
            "address a level directly.\n\n"
            "Q2 - section 6: if any probe produced a NEW indicator/icon, note\n"
            "which byte and mask -- that is a candidate for the second\n"
            "'AC Power limiter' toggle we currently treat as reserved."
        )


def run(probe):
    # ------------------------------------------------------------- 1. baseline
    probe.banner(
        "Section 1 - baseline.  We put the unit in a known state.\n"
        "# Watch the number after the decimal point on the WALL unit (not the\n"
        "# remote): .0 means the energy saver is OFF, .1/.2/.3 means it is on."
    )
    probe.step(
        "Power OFF (clean slate)",
        "The unit turns OFF.",
        "Did the unit turn OFF?  (y/n)",
        power="off",
    )
    probe.step(
        "Power ON, cool 23 C, SE OFF",
        "Unit ON, cool, display 73 F, energy saver OFF (should read 73 or 73.0).",
        "What does the display show?  (e.g. 73 or 73.0)",
        power="on",
        mode="cool",
        temperature=23,
        se="off",
    )

    # ------------------------------ 2. absolute vs counter (the decisive test)
    probe.banner(
        "Section 2 - the decisive test: is the LEVEL in the frame, or counted\n"
        "# by the unit?  'SE' (byte 5 0x80) turns the limiter on; the byte 6 0x40\n"
        "# bit is the 'speed control' button.  We send frame X, then a DIFFERENT\n"
        "# frame Y, then X again.  Absolute -> X shows the same level both times.\n"
        "# Counter -> it climbs."
    )
    probe.step(
        "X: SE ON (byte5 0x80), speed-control bit OFF",
        "Limiter turns ON.  Note the level after the dot (.1/.2/.3).",
        "Level after the dot?  (0/1/2/3)",
        se="on",
        se_step="off",
    )
    probe.step(
        "Y: SE ON + speed-control bit ON (byte6 0x40, one extra bit flipped)",
        "If this level DIFFERS from X, the unit is counting, not reading a level.",
        "Level after the dot?  (0/1/2/3)",
        se="on",
        se_step="on",
    )
    probe.step(
        "X again (identical frame to the first X)",
        "ABSOLUTE -> same level as the first X.  COUNTER -> a new/higher level.",
        "Level after the dot?  (0/1/2/3)",
        se="on",
        se_step="off",
    )

    # ------------------------------------------------- 3. step through levels
    probe.banner(
        "Section 3 - step through the levels by pulsing the 'speed control'\n"
        "# button (byte 6 0x40) on and off.  Each change of that bit should move\n"
        "# the level up and wrap .1 -> .2 -> .3 -> .1, just like pressing the\n"
        "# physical button repeatedly."
    )
    for n, es in enumerate(["on", "off", "on", "off"], start=1):
        probe.step(
            f"Speed-control press #{n} (byte6 0x40 {'ON' if es == 'on' else 'OFF'})",
            "Level should move up by one (wrapping .3 -> .1).",
            "Level after the dot?  (0/1/2/3)",
            se="on",
            se_step=es,
        )

    # ------------------------------------------ 4. persistence over power cycle
    probe.banner(
        "Section 4 - does the unit remember the level across a power cycle?\n"
        "# We turn it OFF, back ON withOUT the SE bit, then turn SE back on."
    )
    probe.step(
        "Power OFF",
        "Unit turns OFF (remember the level it last showed).",
        "Did it turn OFF, and what level was showing just before?  (0/1/2/3)",
        power="off",
        se="on",
        se_step="off",
    )
    probe.step(
        "Power ON, SE OFF",
        "Unit ON, energy saver OFF (should read 73 / 73.0).",
        "What does the display show?  (e.g. 73 or 73.0)",
        power="on",
        se="off",
    )
    probe.step(
        "SE ON again (no speed-control bit)",
        "Does it resume the level from before the power cycle, or start fresh?",
        "Level after the dot?  (0/1/2/3)",
        se="on",
        se_step="off",
    )

    # ---------------------------------------------------- 5. mode dependence
    probe.banner(
        "Section 5 - does the starting level depend on the MODE?\n"
        "# You reported dehumidify once started at .2 instead of .1.  We reset\n"
        "# with a power cycle before each mode so the comparison is fair."
    )
    for mode, temp in [("cool", 23), ("dry", 23), ("heat", 20)]:
        probe.step(
            f"Reset: power OFF before {mode}",
            "Unit turns OFF.",
            "Did it turn OFF?  (y/n)",
            power="off",
        )
        probe.step(
            f"{mode} + SE ON (speed-control bit OFF)",
            f"Limiter turns on in {mode}.  Note the STARTING level.",
            "Starting level after the dot?  (0/1/2/3)",
            power="on",
            mode=mode,
            temperature=temp,
            se="on",
            se_step="off",
        )

    # -------------------------------------- 6. hunt for a second limiter toggle
    probe.banner(
        "Section 6 - the manual mentions TWO limiters: 'SE' (which we know is\n"
        "# byte 5 0x80) and a separate 'AC Power limiter'.  We have no capture\n"
        "# for the second one, so here we poke bits we currently treat as unused\n"
        "# and watch for ANY new indicator (a limiter dot, an eco/plug icon, or\n"
        "# a change in behaviour).  Base frame is cool 23 C with SE OFF, so a\n"
        "# clean unit should just read 73 with nothing after the dot.  We reset\n"
        "# with a power cycle first so nothing lingers from earlier sections."
    )
    probe.step(
        "Reset: power OFF",
        "Unit turns OFF.",
        "Did it turn OFF?  (y/n)",
        power="off",
    )
    probe.step(
        "Power ON, cool 23 C, SE OFF (reference)",
        "Plain 73, no dot / no extra icon.  This is what 'nothing happened' looks like.",
        "What does the display show?  (e.g. 73)",
        power="on",
        se="off",
    )
    # (byte, mask, human description).  Bytes 7/9/10/12 are fully reserved, so a
    # coarse 0xFF sweep is safe there; bytes 5/6 get only their spare bits.
    candidates = [
        ("byte 5 spare bits (0x3B)", 5, 0x3B),
        ("byte 6 spare high bits (0x90)", 6, 0x90),
        ("byte 7 reserved (0xFF)", 7, 0xFF),
        ("byte 9 reserved (0xFF)", 9, 0xFF),
        ("byte 10 reserved (0xFF)", 10, 0xFF),
        ("byte 12 reserved (0xFF)", 12, 0xFF),
    ]
    for desc, byte_index, mask in candidates:
        probe.raw_step(
            f"Probe {desc}",
            byte_index,
            mask,
            "If this is a hidden limiter toggle, a NEW indicator/icon appears.",
            "Anything new vs the reference 73?  (describe, or 'no')",
            se="off",
        )

    probe.summary()


def main():
    parser = argparse.ArgumentParser(
        description="Interactive probe for the Airspool energy-saver (SE) behaviour."
    )
    parser.add_argument(
        "-d",
        "--device",
        default="/dev/lirc0",
        help="LIRC transmit device passed to ir-ctl (default /dev/lirc0).",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Print the whole sequence and each frame without transmitting.",
    )
    opts = parser.parse_args()

    print(
        "Airspool SE probe.\n"
        "  - Watch the WALL unit's display, especially the digit after the dot.\n"
        "  - After each frame, type what you actually see.\n"
        "  - Press q at any prompt to stop.\n"
    )
    probe = Probe(opts.device, opts.dry_run)
    run(probe)


if __name__ == "__main__":
    main()
