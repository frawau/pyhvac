import pytest

from pyhvac.state import TemperatureRange, fahrenheit


def test_fahrenheit_range_offers_one_celsius_setpoint_per_whole_fahrenheit():
    r = TemperatureRange.fahrenheit(60, 86)
    assert r.values[:3] == (15.6, 16.1, 16.7)
    assert (r.min, r.max) == (15.6, 30.0)
    assert len(r.values) == 27


def test_round_trip_is_exact_for_0_to_120_f():
    r = TemperatureRange.fahrenheit(0, 120)
    assert [fahrenheit(c) for c in r.values] == list(range(0, 121))


@pytest.mark.parametrize(
    "celsius, snapped", [(24.0, 23.9), (24.2, 24.4), (10.0, 15.6), (40.0, 30.0)]
)
def test_snap_picks_the_nearest_offered_setpoint(celsius, snapped):
    assert TemperatureRange.fahrenheit(60, 86).snap(celsius) == snapped


def test_explicit_values_must_be_sorted_unique_tenths():
    with pytest.raises(ValueError):
        TemperatureRange(16.0, 17.0, values=(17.0, 16.0))
    with pytest.raises(ValueError):
        TemperatureRange(16.0, 17.0, values=(16.0, 16.05))


def test_values_must_lie_within_min_and_max():
    with pytest.raises(ValueError):
        TemperatureRange(16.0, 20.0, (0,), (16.0, 21.0))
