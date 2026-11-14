import json

import pytest

from pyhvac.state import BOOL, Capabilities, Choice, HvacState, TemperatureRange


def state(**kw):
    base = dict(power=True, mode="cool", temperature=24.0)
    base.update(kw)
    return HvacState(**base)


def test_temperature_rounds_to_one_decimal():
    assert state(temperature=23.46).temperature == 23.5
    assert state(temperature=23.44).temperature == 23.4
    assert state(temperature=24).temperature == 24.0


@pytest.mark.parametrize(
    "kw",
    [
        dict(power=1),
        dict(mode="fan_only"),
        dict(temperature="24"),
        dict(temperature=True),
        dict(fan="high"),
        dict(fan="0"),
        dict(swing_v="on"),
        dict(swing_h="-1"),
        dict(features={"quiet": 1}),
        dict(features={"": True}),
    ],
)
def test_state_validation(kw):
    with pytest.raises(ValueError):
        state(**kw)


def test_levels_and_keywords_accepted():
    s = state(fan="3", swing_v="swing", swing_h="auto")
    assert (s.fan, s.swing_v, s.swing_h) == ("3", "swing", "auto")


def test_features_are_read_only():
    s = state(features={"quiet": True})
    with pytest.raises(TypeError):
        s.features["quiet"] = False


def test_to_dict_round_trip_through_json():
    s = state(fan="2", swing_v="1", features={"quiet": True, "economy": "80"})
    data = json.loads(json.dumps(s.to_dict()))
    assert HvacState.from_dict(data) == s


def test_from_dict_ignores_unknown_keys():
    data = state().to_dict()
    data["humidity_target"] = 50
    assert HvacState.from_dict(data) == state()


def test_states_are_hashable():
    assert len({state(features={"quiet": True}), state(features={"quiet": True})}) == 1


@pytest.mark.parametrize(
    "decimals, value, expected",
    [
        ((0,), 23.4, 23.0),
        ((0,), 23.5, 23.0),  # tie goes to the lower value
        ((0,), 23.6, 24.0),
        ((0, 5), 23.2, 23.0),
        ((0, 5), 23.3, 23.5),
        ((0, 5), 23.8, 24.0),
        ((0, 2, 5, 8), 23.1, 23.0),
        ((0, 2, 5, 8), 23.4, 23.5),
        ((0, 2, 5, 8), 23.9, 23.8),
        ((0, 2, 5, 8), 23.95, 24.0),  # 23.95 rounds to 24.0 first
        ((0,), 10.0, 16.0),  # clamped to min
        ((0,), 40.0, 30.0),  # clamped to max
    ],
)
def test_snap(decimals, value, expected):
    assert TemperatureRange(16.0, 30.0, decimals).snap(value) == expected


@pytest.mark.parametrize(
    "args",
    [
        (16.0, 30.0, ()),
        (16.0, 30.0, (0, 0)),
        (16.0, 30.0, (10,)),
        (16.5, 30.0, (0,)),  # min not an allowed value
        (30.0, 16.0, (0,)),
    ],
)
def test_temperature_range_validation(args):
    with pytest.raises(ValueError):
        TemperatureRange(*args)


def test_choice_validation_and_labels():
    c = Choice(("auto", "1"), {"1": "low"})
    assert c.label("1") == "low"
    assert c.label("auto") == "auto"
    with pytest.raises(ValueError):
        Choice(())
    with pytest.raises(ValueError):
        Choice(("1", "1"))
    with pytest.raises(ValueError):
        Choice(("1",), {"2": "x"})


def test_capabilities_validation():
    rng = TemperatureRange(16.0, 30.0)
    Capabilities(modes=("cool", "heat"), temperature=rng, features={"quiet": BOOL})
    with pytest.raises(ValueError):
        Capabilities(modes=(), temperature=rng)
    with pytest.raises(ValueError):
        Capabilities(modes=("cool", "fanheat"), temperature=rng)


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"power": True, "mode": "cool"},
        {"power": True, "mode": "cool", "temperature": 24.0, "features": None},
        {"power": True, "mode": "cool", "temperature": 24.0, "features": [1]},
        {"power": True, "mode": "cool", "temperature": float("inf")},
        {"power": True, "mode": "cool", "temperature": 1e308},
        {"power": True, "mode": "cool", "temperature": float("nan")},
        {"power": True, "mode": "cool", "temperature": "24"},
        {"power": True, "mode": "heat_cool", "temperature": 24.0},
        {"power": True, "mode": "cool", "temperature": 24.0, "swing_v": "wide"},
        [],
        None,
        "state",
    ],
)
def test_from_dict_rejects_malformed_data_with_value_error(data):
    # Callers restoring persisted state catch ValueError and fall back to
    # previous=None ("unknown").
    with pytest.raises(ValueError):
        HvacState.from_dict(data)
