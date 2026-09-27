#! /usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Unit tests for the Airspool plugin.
#
# The expected frames are the captured references documented at:
#   https://twosortoftechguys.wordpress.com/2026/06/14/sending-ir-codes-to-an-airspool-mini-split-using-a-raspberry-pi-ai-failed-us-2/

import pytest

from pyhvac.plugins.airspool import Airspool


def frame(hexstr):
    return bytearray.fromhex(hexstr.replace(" ", ""))


def build(**settings):
    """Build a single logical frame after applying the given settings."""
    dev = Airspool()
    for name, value in settings.items():
        getattr(dev, "set_" + name)(value)
    frames = dev._build_ircode()
    assert len(frames) == 1
    return frames[0]


# Each entry: (expected hex frame, settings to apply on a fresh device).
# Temperatures are given in degC (the library convention) and converted to the
# nearest degF internally: 16->61, 18->64, 24->75, 26->79 degF.
REFERENCES = [
    ("23 CB 26 01 61 04 23 00 00 00 00 E0 00 7D", dict(mode="cool", temperature=16)),
    ("23 CB 26 01 75 04 23 00 00 00 00 E0 00 91", dict(mode="cool", temperature=24)),
    (
        "23 CB 26 01 75 84 23 00 00 00 00 E0 00 11",
        dict(mode="cool", temperature=24, se="on"),
    ),
    (
        "23 CB 26 01 61 00 23 00 00 00 00 E0 00 79",
        dict(mode="cool", temperature=16, power="off"),
    ),
    (
        # The dehumidify capture was taken with fan1 selected; the mode does
        # not lock the fan, so fan1 is set explicitly here.
        "23 CB 26 01 61 04 22 00 02 00 00 E0 00 7E",
        dict(mode="dehumidify", temperature=16, fan="fan1"),
    ),
    ("23 CB 26 01 64 04 E1 00 00 00 00 E0 00 3E", dict(mode="heat", temperature=18)),
    (
        "23 CB 26 01 79 04 63 00 00 00 00 E0 00 D5",
        dict(mode="cool", temperature=26, se_step="on"),
    ),
    (
        "23 CB 26 01 79 04 03 00 00 00 00 E0 00 75",
        dict(mode="cool", temperature=26, display="off"),
    ),
    (
        "23 CB 26 01 79 04 23 00 02 00 00 E0 00 97",
        dict(mode="cool", temperature=26, fan="fan1"),
    ),
    (
        "23 CB 26 01 79 04 23 00 04 00 00 E0 00 99",
        dict(mode="cool", temperature=26, fan="fan2"),
    ),
    (
        "23 CB 26 01 79 04 23 00 06 00 00 E0 00 9B",
        dict(mode="cool", temperature=26, fan="fan4"),
    ),
    (
        "23 CB 26 01 79 04 23 00 05 00 00 E0 00 9A",
        dict(mode="cool", temperature=26, fan="fan5"),
    ),
    (
        # The panel's "fan6" is the auto setting (enum 0).
        "23 CB 26 01 79 04 23 00 00 00 00 E0 00 95",
        dict(mode="cool", temperature=26, fan="auto"),
    ),
    (
        "23 CB 26 01 79 04 23 00 01 00 00 E0 00 96",
        dict(mode="cool", temperature=26, sleep="on"),
    ),
    (
        "23 CB 26 01 79 04 23 00 38 00 00 E0 00 CD",
        dict(mode="cool", temperature=26, swing="on"),
    ),
    (
        "23 CB 26 01 79 04 23 00 00 00 00 00 00 B5",
        dict(mode="cool", temperature=26, hswing="on"),
    ),
    (
        "23 CB 26 01 79 44 23 00 40 00 00 E0 00 15",
        dict(mode="cool", temperature=26, turbo="on"),
    ),
]


@pytest.mark.parametrize("expected,settings", REFERENCES)
def test_frame_matches_reference(expected, settings):
    assert build(**settings) == frame(expected)


@pytest.mark.parametrize("expected,settings", REFERENCES)
def test_checksum_is_recomputed(expected, settings):
    built = build(**settings)
    # The checksum must equal the sum of bytes 0..12, not a hard-coded value.
    assert built[13] == sum(built[0:13]) & 0xFF
    # And it must match the captured reference's checksum.
    assert built[13] == frame(expected)[13]


def test_checksum_changes_with_payload():
    # Changing the temperature must change the recomputed checksum.
    a = build(mode="cool", temperature=24)  # -> 75 degF
    b = build(mode="cool", temperature=25)  # -> 77 degF
    assert a[13] != b[13]
    assert b[13] == sum(b[0:13]) & 0xFF


def test_frame_is_fourteen_bytes():
    assert len(build(mode="cool", temperature=24)) == 14


@pytest.mark.parametrize(
    "celsius,expected_bcd",
    [
        (16, 0x61),
        (18, 0x64),
        (24, 0x75),
        (25, 0x77),
        (26, 0x79),
        # Half-degree steps reach degF values that whole degC cannot: 62, 76
        # and 78 degF sit between the integer-degC setpoints.
        (16.5, 0x62),
        (24.5, 0x76),
        (25.5, 0x78),
    ],
)
def test_celsius_converted_to_fahrenheit_bcd(celsius, expected_bcd):
    # The API takes degC and BCD-encodes the nearest degF into byte 4.
    assert build(mode="cool", temperature=celsius)[4] == expected_bcd


def test_half_degree_temperatures_are_advertised():
    # The capability list exposes 0.5 degC resolution across 16-30 degC.
    temps = Airspool().capabilities["temperature"]
    assert 16.0 in temps and 30.0 in temps and 24.5 in temps
    assert all(round(t * 2) == t * 2 for t in temps)  # all on the 0.5 grid


def test_round_trip_pulse_to_bytes():
    # Build -> LSB-first pulse train -> decode back -> logical frame.
    dev = Airspool()
    dev.set_mode("cool")
    dev.set_temperature(26)  # degC -> 79 degF
    dev.set_fan("fan2")
    dev.set_swing("on")

    logical = dev._build_ircode()[0]
    wireframes = dev.build_ircode()  # bit-reversed (LSB-first) frames
    pulses = dev.to_lirc(wireframes)
    decoded = dev.decode_pulse(pulses)

    assert decoded == logical


def test_pulse_timings_use_physical_layer():
    dev = Airspool()
    dev.set_mode("cool")
    dev.set_temperature(24)
    pulses = dev.to_lirc(dev.build_ircode())

    # Header.
    assert pulses[0:2] == [3200, 1400]
    # Every bit mark is the constant 480 us; every space is one of the two
    # known durations.
    body = pulses[2:-2]
    marks = body[0::2]
    spaces = body[1::2]
    assert all(m == 480 for m in marks)
    assert set(spaces) <= {360, 1180}
    # Final stop mark then a long trailing gap.
    assert pulses[-2] == 480
    assert pulses[-1] >= 10000
