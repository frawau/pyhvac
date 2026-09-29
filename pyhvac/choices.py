"""Capability choices several devices share.

The labels are the legacy entity's vocabulary (what pyhvac 0.1 offered for
each value), which the ports keep so that capabilities stay equal to it.
"""

from .state import Choice

# A feature switched on or off.
ON_OFF = Choice((False, True), {False: "off", True: "on"})

# A swing that is either off or swinging (the legacy "on").
SWING = Choice(("off", "swing"), {"off": "off", "swing": "on"})

# Fan ladders: "auto", then the speeds, slowest first.
FAN_3 = Choice(
    ("auto", "1", "2", "3"),
    {"auto": "auto", "1": "low", "2": "medium", "3": "high"},
)
FAN_4 = Choice(
    ("auto", "1", "2", "3", "4"),
    {"auto": "auto", "1": "lowest", "2": "low", "3": "medium", "4": "high"},
)
FAN_5 = Choice(
    ("auto", "1", "2", "3", "4", "5"),
    {
        "auto": "auto",
        "1": "lowest",
        "2": "low",
        "3": "medium",
        "4": "high",
        "5": "highest",
    },
)

# Vertical vane positions, highest ("1", 90°) to lowest ("5", 0°).
SWING_V_ANGLES = Choice(
    ("off", "auto", "1", "2", "3", "4", "5"),
    {
        "off": "off",
        "auto": "auto",
        "1": "90°",
        "2": "60°",
        "3": "45°",
        "4": "30°",
        "5": "0°",
    },
)

# Horizontal vane positions, far left ("1") to far right ("5"), and wide.
SWING_H_5 = Choice(
    ("auto", "1", "2", "3", "4", "5"),
    {
        "auto": "auto",
        "1": "far left",
        "2": "left",
        "3": "middle",
        "4": "right",
        "5": "far right",
    },
)
SWING_H_6 = Choice(
    SWING_H_5.values + ("6",),
    {**SWING_H_5.labels, "6": "wide"},
)
