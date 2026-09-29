import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.ir.codec import decode
from pyhvac.plugins.ecoclim import (
    ECOCLIM,
    ECOCLIM_LAYOUT,
    ECOCLIM_MODELS,
    EcoclimDevice,
)
from pyhvac.state import HvacState

# The C path deviates from the documented EcoClim values here:
# - IRac::sendAc passes send.iFeel (false, 0) as IRac::ecoclim's sleep
#   minutes, and sleep >= 0 selects kEcoclimSleep: every C message is mode
#   sleep (7), whatever the requested mode, off messages included. Oracle off
#   records read as mode auto, so they are covered by the auto entry.
DEFECTS = tuple(
    Defect("mode", mode, "sleep", "IRac::sendAc passes iFeel as sleep")
    for mode in ("auto", "cool", "dry", "fan", "heat")
)


def device():
    return EcoclimDevice("ecoclim", "generic")


def state(power=True, mode="cool", temperature=22.0, **kw):
    return device().normalise(HvacState(power, mode, temperature, **kw))


def frames(target, previous=None):
    return device().frames(previous, target, ())


def read(target, previous=None):
    return ECOCLIM_LAYOUT.read(frames(target, previous)[0].data)


@pytest.mark.parametrize("record", oracle_params("ECOCLIM"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("ECOCLIM"):
        for frame in dev.frames(None, state_from_record(dev, record["state"]), ()):
            values = ECOCLIM_LAYOUT.read(frame.data)
            assert ECOCLIM_LAYOUT.build(**values) == bytearray(frame.data)


def test_the_three_copies_are_identical():
    # sendEcoclim sends the same word in every section.
    first, second, last = frames(state(True, "heat", 27.0, fan="2"))
    assert [f.section for f in (first, second, last)] == ["first", "second", "last"]
    assert first.data == second.data == last.data


# ir_Ecoclim_test.cpp, RealExample: the two 56-bit captures, and
# kEcoclimDefaultState (HumanReadable).
CAPTURES = [
    (
        0x110673AEFFFF72,
        {
            "power": 1,
            "mode": "auto",
            "temperature": 11,
            "sensor_temperature": 22,
            "fan": "auto",
            "clock": 15 * 60 + 42,
            "on_hours": 0x1F,
            "on_ten_minutes": 7,
            "off_hours": 0x1F,
            "off_ten_minutes": 7,
            "dip_config": "slave",
        },
    ),
    (
        0x15594507FFFF0A,
        {
            "power": 1,
            "mode": "dry",
            "temperature": 30,
            "sensor_temperature": 26,
            "fan": "1",
            "clock": 21 * 60 + 27,
            "on_hours": 0x1F,
            "off_hours": 0x1F,
            "dip_config": "master",
        },
    ),
    (
        0x11063000FFFF02,
        {
            "power": 0,
            "mode": "auto",
            "temperature": 11,
            "sensor_temperature": 22,
            "fan": "auto",
            "clock": 0,
            "dip_config": "master",
        },
    ),
]


@pytest.mark.parametrize("raw, fields", CAPTURES)
def test_layout_reads_the_real_captures(raw, fields):
    data = raw.to_bytes(7, "big")
    values = ECOCLIM_LAYOUT.read(data)
    assert {k: values[k] for k in fields} == fields
    assert ECOCLIM_LAYOUT.build(**values) == bytearray(data)


@pytest.mark.parametrize(
    "raw, target, differing",
    [
        # The entity has no sensor reading, clock or DIP setting: the port
        # sends the setpoint, 00:00 and master there.
        (
            0x110673AEFFFF72,
            state(True, "auto", 11.0, fan="auto"),
            {"sensor_temperature", "clock", "dip_config"},
        ),
        # The unknown bit next to DipConfig is set in this capture only.
        (
            0x15594507FFFF0A,
            state(True, "dry", 30.0, fan="1"),
            {"sensor_temperature", "clock", "unknown_type"},
        ),
    ],
)
def test_port_reproduces_the_real_captures_but_what_it_cannot_express(
    raw, target, differing
):
    capture = raw.to_bytes(7, "big")
    ours = frames(target)[0].data
    a, b = ECOCLIM_LAYOUT.read(ours), ECOCLIM_LAYOUT.read(capture)
    assert {k for k in a if a[k] != b[k]} == differing
    patched = bytearray(ours)
    for name in differing:
        ECOCLIM_LAYOUT.write_raw(patched, name, ECOCLIM_LAYOUT.read_raw(capture, name))
    assert bytes(patched) == capture


def test_port_reproduces_the_default_state_but_the_setpoint():
    # kEcoclimDefaultState: off, auto, 11C, sensor 22C, fan auto. The port
    # sends the setpoint as the sensor temperature.
    ours = frames(state(False, "auto", 11.0, fan="auto"))[0].data
    expected = bytearray((0x11063000FFFF02).to_bytes(7, "big"))
    ECOCLIM_LAYOUT.write_raw(expected, "sensor_temperature", 11 - 5)
    assert ours == bytes(expected)


@pytest.mark.parametrize("power", [True, False])
@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan", "heat"])
@pytest.mark.parametrize("t", [float(x) for x in range(5, 32)])
def test_setpoint_and_sensor_temperature_are_the_target(power, mode, t):
    # IRac::ecoclim sets SensorTemp to the setpoint without a sensor reading
    # (the oracle records show it at 5, 18 and 31C in every mode, on and off).
    values = read(state(power, mode, t))
    assert values["temperature"] == int(t)
    assert values["sensor_temperature"] == int(t)


@pytest.mark.parametrize(
    "mode, code", [("auto", 0), ("cool", 1), ("dry", 2), ("fan", 4), ("heat", 5)]
)
def test_mode_uses_its_documented_value(mode, code):
    first, _, _ = frames(state(True, mode))
    assert ECOCLIM_LAYOUT.read_raw(first.data, "mode") == code


@pytest.mark.parametrize("mode", ["auto", "cool", "dry", "fan", "heat"])
def test_off_carries_mode_auto_and_power_off(mode):
    values = read(state(False, mode, 25.0))
    assert (values["power"], values["mode"]) == (0, "auto")


def test_on_sets_the_power_bit():
    assert read(state(True, "cool"))["power"] == 1


@pytest.mark.parametrize("fan, raw", [("1", 0), ("2", 1), ("3", 2), ("auto", 3)])
def test_every_fan_level_uses_its_documented_code(fan, raw):
    # kEcoclimFanMin/Med/Max/Auto; the oracle records show the same codes.
    first, _, _ = frames(state(fan=fan))
    assert ECOCLIM_LAYOUT.read_raw(first.data, "fan") == raw


@pytest.mark.parametrize("power", [True, False])
def test_unset_fields_keep_the_default_state(power):
    # Clock 00:00, both timers disabled, DIP master, as in
    # kEcoclimDefaultState and every oracle record.
    values = read(state(power, "heat", 30.0, fan="3"))
    assert values["clock"] == 0
    assert (values["on_hours"], values["on_ten_minutes"]) == (0x1F, 7)
    assert (values["off_hours"], values["off_ten_minutes"]) == (0x1F, 7)
    assert values["dip_config"] == "master"
    for name in ("unknown_clock", "unknown_type", "clear"):
        assert values[name] == 0, name


def test_previous_is_ignored():
    target = state(True, "cool", 22.0)
    for previous in (None, state(False, "heat", 30.0, fan="1"), target):
        assert frames(target, previous) == frames(target)


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (5730, 1935)
    assert pulses[-2:] == (7820, 100000)
    assert len(pulses) == 3 * (2 + 2 * 56) + 2
    record = load_oracle("ECOCLIM")[0]
    assert len(pulses) == len(record["pulses"])


@pytest.mark.parametrize("model", ECOCLIM_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("ecoclim", model), EcoclimDevice)


@pytest.mark.parametrize("model", ECOCLIM_MODELS)
def test_capabilities_match_the_legacy_entity(model):
    pytest.importorskip("pyhvac.irhvac")
    from pyhvac.legacy import LegacyDevice
    from pyhvac.plugins.ecoclim import Ecoclim

    legacy = LegacyDevice("ecoclim", model, Ecoclim)
    assert EcoclimDevice("ecoclim", model).capabilities == legacy.capabilities


@pytest.mark.parametrize("mode", ["off", "auto", "cool", "dry", "fan", "heat"])
def test_undeclared_mode_deviation_is_reported(mode):
    dev = device()
    record = next(r for r in load_oracle("ECOCLIM") if r["state"]["mode"] == mode)
    with pytest.raises(AssertionError, match="mode"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_every_c_message_is_mode_sleep():
    # The mode defect: C's frames read as sleep in every oracle record.
    dev = device()
    for record in load_oracle("ECOCLIM"):
        names = [f.section for f in dev.frames(None, state(), ())]
        for frame in decode(dev.PROTOCOL, record["pulses"], expected=names):
            assert ECOCLIM_LAYOUT.read(frame.data)["mode"] == "sleep"


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("ECOCLIM")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)


# ir_Ecoclim_test.cpp DecodeEcoclim.RealExample (long_rawData, long_rawData2):
# decodeEcoclim matches with _tolerance + kEcoclimExtraTolerance (30 %);
# their bit marks run as short as 316 µs for 440.
RAW_LONG = (
    "5834 1950 482 580 506 614 480 612 456 1738 482 562 532 582 508 608 430 "
    "1760 456 642 456 608 484 638 458 634 456 634 456 1734 482 1704 402 690 "
    "456 638 404 1786 458 1730 430 1762 454 638 456 636 456 1732 426 1764 "
    "426 1788 400 692 402 1764 452 638 430 1760 424 1786 374 1818 402 690 "
    "374 1786 424 1796 402 1758 426 1790 376 1782 426 1766 400 1810 398 "
    "1796 400 1788 428 1734 398 1814 400 1762 470 1742 400 1786 398 1794 "
    "400 1762 398 718 400 1792 400 1788 400 1788 400 694 400 694 402 1788 "
    "398 664 5720 1944 426 642 450 696 442 650 396 1794 468 602 422 642 448 "
    "696 442 1744 392 702 392 678 420 700 394 700 464 628 466 1720 464 1726 "
    "462 628 464 630 464 1728 438 1752 462 1722 464 636 438 626 464 1722 "
    "490 1698 488 1722 464 628 466 1724 466 626 464 1724 464 1724 462 1732 "
    "462 626 464 1726 464 1724 464 1722 464 1732 464 1690 490 1724 464 1726 "
    "464 1728 464 1728 462 1690 492 1728 462 1724 464 1726 464 1728 464 "
    "1720 462 1736 460 604 490 1718 464 1730 462 1720 462 630 464 628 462 "
    "1734 462 600 5632 2028 490 630 464 632 464 630 462 1724 462 630 462 "
    "636 462 602 488 1728 464 630 462 632 464 630 462 628 462 630 464 1730 "
    "460 1724 464 630 464 630 462 1728 464 1724 462 1728 462 630 464 630 "
    "462 1724 464 1728 460 1730 462 628 460 1732 464 602 492 1722 464 1726 "
    "460 1726 464 632 464 1696 488 1728 460 1732 462 1728 462 1694 488 1728 "
    "462 1724 464 1732 460 1700 490 1728 462 1694 488 1730 462 1720 462 "
    "1728 464 1726 462 1726 460 632 464 1724 462 1726 460 1730 464 630 464 "
    "632 464 1728 462 596 7862"
)
RAW_LONG2 = (
    "5832 1928 482 614 482 610 482 588 506 1704 482 586 508 1714 454 606 "
    "508 1682 508 618 480 1646 534 594 506 1708 454 1708 506 582 508 586 "
    "508 1706 456 612 508 1704 482 614 480 590 508 586 506 1678 508 592 506 "
    "1682 506 590 506 578 508 612 480 590 478 646 454 1676 534 1708 480 "
    "1712 482 1706 480 1710 480 1704 482 1672 430 1744 534 1712 482 1698 "
    "482 1708 482 1702 484 1704 484 1712 484 1704 484 1700 484 1706 484 "
    "1710 484 1698 484 612 484 610 482 612 484 610 482 1732 458 608 484 "
    "1704 482 614 5726 1906 510 610 458 634 484 614 480 1706 484 612 484 "
    "1732 458 610 484 1700 484 616 482 1708 456 608 510 1710 484 1700 482 "
    "612 484 614 480 1696 482 622 482 1704 482 620 484 602 482 610 486 1706 "
    "482 612 484 1706 482 612 482 608 484 610 482 610 482 614 482 1710 482 "
    "1708 482 1700 480 1714 478 1706 482 1706 482 1712 480 1702 482 1710 "
    "478 1710 480 1706 480 1732 456 1716 478 1676 504 1736 456 1708 478 "
    "1708 482 1714 450 1706 504 640 454 616 480 638 454 642 452 1710 480 "
    "612 478 1710 480 602 5726 1950 450 642 482 614 452 642 478 1730 428 "
    "644 450 1746 478 630 456 1710 478 644 452 1734 456 614 452 1738 480 "
    "1706 450 666 428 642 452 1760 456 614 452 1736 454 646 452 662 454 640 "
    "398 1788 426 670 456 1712 446 670 454 638 454 646 430 664 426 662 396 "
    "1774 416 1792 392 1798 464 1696 416 1798 464 1724 392 1800 392 1790 "
    "390 1788 464 1734 392 1798 462 1734 438 1724 490 1724 390 1766 464 "
    "1752 390 1802 390 1792 366 1802 414 702 390 702 390 704 394 700 392 "
    "1792 440 654 390 1800 366 730 7800"
)


@pytest.mark.parametrize(
    "raw, state",
    [(RAW_LONG, "110673aeffff72"), (RAW_LONG2, "15594507ffff0a")],
    ids=["long_rawData", "long_rawData2"],
)
def test_real_raw_captures_decode(raw, state):
    pulses = [int(x) for x in raw.split()]
    frames = decode(ECOCLIM, pulses, expected=["first", "second", "last"])
    assert [f.data.hex() for f in frames] == [state] * 3
