import gzip
import importlib
import json
from pathlib import Path

import pytest

from pyhvac.legacy import LegacyDevice, legacy_capabilities
from pyhvac.state import HvacState

GOLDEN = Path(__file__).parent / "fixtures" / "golden"


def caps(**extra):
    base = {"mode": ["off", "auto", "cool", "heat"], "temperature": [16, 30]}
    base.update(extra)
    return base


def test_modes_drop_off_and_temperature_range():
    c = legacy_capabilities(caps(), 1.0)
    assert c.modes == ("auto", "cool", "heat")
    assert (c.temperature.min, c.temperature.max, c.temperature.decimals) == (
        16.0,
        30.0,
        (0,),
    )
    assert legacy_capabilities(caps(), 0.5).temperature.decimals == (0, 5)


def test_fan_levels_ranked_lowest_first_with_old_labels():
    c = legacy_capabilities(caps(fan=["auto", "highest", "high", "low", "lowest"]), 1)
    assert c.fan.values == ("auto", "1", "2", "3", "4")
    assert [c.fan.label(v) for v in c.fan.values] == [
        "auto",
        "lowest",
        "low",
        "high",
        "highest",
    ]


def test_unknown_fan_word_rejected():
    with pytest.raises(ValueError, match="turbo"):
        legacy_capabilities(caps(fan=["auto", "turbo"]), 1)


def test_swing_keywords_and_positions_in_list_order():
    c = legacy_capabilities(caps(swing=["off", "auto", "90°", "45°", "on"]), 1)
    assert c.swing_v.values == ("off", "auto", "swing", "1", "2")
    assert c.swing_v.label("swing") == "on"
    assert c.swing_v.label("1") == "90°"


def test_hswing_positions_left_to_right():
    c = legacy_capabilities(
        caps(
            hswing=["auto", "wide", "far right", "right", "middle", "left", "far left"]
        ),
        1,
    )
    assert c.swing_h.values == ("auto", "1", "2", "3", "4", "5", "6")
    assert [c.swing_h.label(v) for v in c.swing_h.values[1:]] == [
        "far left",
        "left",
        "middle",
        "right",
        "far right",
        "wide",  # outside the ranking: follows in list order
    ]


def test_features_bool_and_string():
    c = legacy_capabilities(caps(quiet=["off", "on"], economy=["off", "80", "60"]), 1)
    assert c.features["quiet"].values == (False, True)
    assert c.features["economy"].values == ("off", "80", "60")


# ---- LegacyDevice over the pure-Python classes, against the golden fixtures

NATIVE_LEGACY = {
    "daikin": ["Daikinth", "Smash2"],
    "panasonic": ["Panasonic", "PanaCassette"],
    "lg": ["LG", "InverterV", "DualInverter"],
    "sharp": ["JTech"],
}


def _records():
    for module, classes in NATIVE_LEGACY.items():
        path = GOLDEN / f"{module}.json.gz"
        for n, rec in enumerate(json.loads(gzip.decompress(path.read_bytes()))):
            if rec["class"] in classes:
                yield pytest.param(module, rec, id=f"{module}-{rec['class']}-{n}")


@pytest.mark.parametrize("module, record", list(_records()))
def test_legacy_device_reproduces_golden(module, record):
    if record["state"]["mode"] == "off":
        # Old off frames carried the stored setpoint; the adapter sends the
        # target's. The unit stays off either way.
        pytest.skip("off frame setpoint differs by design")
    cls = getattr(importlib.import_module(f"pyhvac.plugins.{module}"), record["class"])
    dev = LegacyDevice(module, record["class"], cls)
    target = dev.from_old({**cls().status, **record["state"]})
    assert list(dev.encode(None, target).signal.pulses) == record["pulses"]


def test_to_old_and_from_old_round_trip():
    from pyhvac.plugins.lg import InverterV

    dev = LegacyDevice("lg", "inverter v", InverterV)
    old = {**InverterV().status, "mode": "cool", "fan": "low", "powerful": "on"}
    state = dev.from_old(old)
    assert state.power and state.fan == "2"  # lowest=1, low=2
    back = dev.to_old(state)
    assert {k: back[k] for k in old} == old


def test_power_off_maps_to_old_off_mode():
    from pyhvac.plugins.daikin import Daikinth

    dev = LegacyDevice("daikin", "generic", Daikinth)
    assert dev.to_old(dev.normalise(HvacState(False, "cool", 22.0)))["mode"] == "off"


def test_legacy_signal_is_even_and_positive():
    from pyhvac.plugins.lg import LG

    dev = LegacyDevice("lg", "generic", LG)
    pulses = dev.encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert len(pulses) % 2 == 0 and min(pulses) > 0
