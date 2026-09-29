from pyhvac import choices
from pyhvac.state import Choice


def test_on_off_labels_the_booleans():
    assert choices.ON_OFF == Choice((False, True), {False: "off", True: "on"})


def test_swing_is_the_legacy_on_off_swing():
    assert choices.SWING == Choice(("off", "swing"), {"off": "off", "swing": "on"})


def test_fan_ladders():
    assert choices.FAN_3.values == ("auto", "1", "2", "3")
    assert [choices.FAN_3.label(v) for v in choices.FAN_3.values] == [
        "auto",
        "low",
        "medium",
        "high",
    ]
    assert [choices.FAN_4.label(v) for v in choices.FAN_4.values] == [
        "auto",
        "lowest",
        "low",
        "medium",
        "high",
    ]
    assert [choices.FAN_5.label(v) for v in choices.FAN_5.values] == [
        "auto",
        "lowest",
        "low",
        "medium",
        "high",
        "highest",
    ]


def test_swing_positions():
    assert choices.SWING_V_ANGLES.values == ("off", "auto", "1", "2", "3", "4", "5")
    assert choices.SWING_V_ANGLES.label("1") == "90°"
    assert choices.SWING_V_ANGLES.label("5") == "0°"
    assert choices.SWING_H_5.values == ("auto", "1", "2", "3", "4", "5")
    assert choices.SWING_H_5.label("1") == "far left"
    assert choices.SWING_H_6.values == choices.SWING_H_5.values + ("6",)
    assert choices.SWING_H_6.label("6") == "wide"
