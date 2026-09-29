import pytest

from oracle import load_oracle
from port_oracle import Defect, assert_matches_oracle, oracle_params, state_from_record
from pyhvac import registry
from pyhvac.plugins.sanyo import (
    SANYO_AC88,
    SANYO_AC88_LAYOUT,
    SANYO_AC88_MODELS,
    SanyoAc88Device,
)
from pyhvac.state import HvacState
from pyhvac.ir.codec import decode

# The C path deviates from the documented SanyoAc88 values here (pyhvac's
# glue, not IRremoteESP8266):
# - IRGHVAC.trans_swing has no "on" key, so IRac keeps swingv at kOff and
#   IRac::sanyo88 calls setSwingV(false). The port sends SwingV = 1.
# - IRGHVAC.build_ircode's key map has no "sleep", so IRac keeps sleep at -1
#   and IRac::sanyo88 calls setSleep(false). The port sends Sleep = 1.
SWING = Defect("swing_v", "swing", "off", "C path drops swing 'on' (SwingV)")
SLEEP = Defect("sleep", 1, 0, "C path drops sleep (IRSanyoAc88::setSleep)")
DEFECTS = (SWING, SLEEP)

# ir_Sanyo_test.cpp, DecodeRealExamples ("On", issue 1503): cool, 24 C, fan
# auto, clock 18:42:06. Bytes 1, 7 and 10 are 0x59, 0x00 and 0x80 in the
# capture, where stateReset (and so the C path) has 0x55, 0x01 and 0x10.
REAL_CAPTURE = bytes.fromhex("aa59a018062a1200000080")


def wire(record):
    """``record`` with the pulses the C library puts on the wire.

    sendSanyoAc88 ends with space(kSanyoAc88Gap) then space(kDefaultMessageGap).
    IRac's timing log keeps them as two entries, so the fixture's last entry
    (100 000 µs) sits at a mark position; IRremoteESP8266's own
    SyntheticSelfDecode test shows them merged ("m500s103675").
    """
    pulses = record["pulses"]
    assert len(pulses) % 2 and pulses[-2:] == [3675, 100000]
    return {**record, "pulses": pulses[:-2] + [3675 + 100000]}


# The legacy fan "lowest" (kMin) and "highest" (kMax) are no longer offered:
# convertFan sent them as FanLow and FanHigh, "low" and "high" here.
FAN_AS_SENT = {"lowest": "low", "highest": "high"}


def as_sent(record):
    fan = record["state"].get("fan")
    if fan not in FAN_AS_SENT:
        return record
    return {**record, "state": {**record["state"], "fan": FAN_AS_SENT[fan]}}


def device(model="generic 88"):
    return SanyoAc88Device("sanyo", model)


def frames(state):
    dev = device()
    return dev.frames(None, dev.normalise(state), ())


def read(state):
    return SANYO_AC88_LAYOUT.read(frames(state)[0].data)


def raw(state, field):
    return SANYO_AC88_LAYOUT.read_raw(frames(state)[0].data, field)


@pytest.mark.parametrize("record", oracle_params("SANYO_AC88"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, as_sent(wire(record)), dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("SANYO_AC88"):
        state = state_from_record(dev, as_sent(record)["state"])
        *mains, end = dev.frames(None, state, ())
        assert (end.section, end.data, end.nbits) == ("end", b"", 0)
        assert len(mains) == 3 and len({f.data for f in mains}) == 1
        values = SANYO_AC88_LAYOUT.read(mains[0].data)
        assert SANYO_AC88_LAYOUT.build(**values) == bytearray(mains[0].data)


def test_the_real_capture_reads_as_documented():
    assert SANYO_AC88_LAYOUT.read(REAL_CAPTURE) == {
        "fan": "auto",
        "mode": "cool",
        "power": 1,
        "temperature": 24,
        "filter": 0,
        "swing_v": "off",
        "clock_secs": 6,
        "clock_mins": 42,
        "clock_hours": 18,
        "turbo": 0,
        "start_timer": 0,
        "stop_timer": 0,
        "sleep": 0,
    }


def test_the_real_capture_differs_only_where_the_c_path_does():
    # The clock (never set by IRac) and bytes 1, 7 and 10 (stateReset's 0x55,
    # 0x01 and 0x10) are the only differences.
    frame, *_ = frames(HvacState(True, "cool", 24.0))
    capture = bytearray(REAL_CAPTURE)
    for name in ("clock_secs", "clock_mins", "clock_hours"):
        SANYO_AC88_LAYOUT.write_raw(capture, name, 0)
    capture[1], capture[7], capture[10] = 0x55, 0x01, 0x10
    assert frame.data == bytes(capture)


@pytest.mark.parametrize("mode", ["auto", "cool", "heat", "fan"])
@pytest.mark.parametrize("temperature", [10.0, 20.0, 30.0])
def test_off_carries_mode_auto(mode, temperature):
    # IRac passes mode "off"; convertMode maps it to kSanyoAc88Auto.
    values = read(HvacState(False, mode, temperature))
    assert (values["power"], values["mode"], values["temperature"]) == (
        0,
        "auto",
        int(temperature),
    )


def test_mode_codes():
    for mode, code in (("auto", 0), ("cool", 2), ("heat", 4), ("fan", 5)):
        assert raw(HvacState(True, mode, 22.0), "mode") == code


@pytest.mark.parametrize("mode", ["auto", "cool", "heat", "fan"])
def test_setpoint_is_whole_degrees_clamped_to_10_30(mode):
    assert read(HvacState(True, mode, 5.0))["temperature"] == 10
    assert read(HvacState(True, mode, 21.0))["temperature"] == 21
    assert read(HvacState(True, mode, 21.5))["temperature"] == 21
    assert read(HvacState(True, mode, 40.0))["temperature"] == 30


@pytest.mark.parametrize("fan, code", [("auto", 0), ("1", 1), ("2", 2), ("3", 3)])
def test_fan_codes(fan, code):
    # kSanyoAc88FanAuto, FanLow, FanMedium, FanHigh.
    assert raw(HvacState(True, "cool", 22.0, fan=fan), "fan") == code


def test_capabilities_are_the_documented_values():
    caps = device().capabilities
    # kSanyoAc88TempMin / kSanyoAc88TempMax, whole degrees.
    assert (caps.temperature.min, caps.temperature.max) == (10.0, 30.0)
    # kSanyoAc88{Auto,Cool,Heat,Fan}; FeelCool/FeelHeat have no HvacState mode.
    assert caps.modes == ("auto", "cool", "heat", "fan")
    assert caps.fan.values == ("auto", "1", "2", "3")
    assert caps.fan.labels == {
        "auto": "auto",
        "1": "low",
        "2": "medium",
        "3": "high",
    }
    assert caps.swing_v.values == ("off", "swing")
    assert set(caps.features) == {"powerful", "purifier", "sleep"}


@pytest.mark.parametrize("old", ["lowest", "highest"])
def test_legacy_extra_fans_are_read_as_what_c_sent(old):
    # Removed: "lowest" and "highest" duplicated FanLow and FanHigh.
    dev = device()
    record = wire(_record(mode="cool", fan=old))
    with pytest.raises(ValueError, match=old):
        state_from_record(dev, record["state"])
    assert_matches_oracle(dev, as_sent(record), dev.LAYOUTS, DEFECTS)


@pytest.mark.parametrize(
    "feature, field",
    [("powerful", "turbo"), ("purifier", "filter"), ("sleep", "sleep")],
)
def test_each_feature_sets_its_bit_only(feature, field):
    base = read(HvacState(True, "cool", 22.0))
    on = read(HvacState(True, "cool", 22.0, features={feature: True}))
    assert (base[field], on[field]) == (0, 1)
    assert {k: v for k, v in on.items() if k != field} == {
        k: v for k, v in base.items() if k != field
    }


def test_features_combine():
    feats = {"powerful": True, "purifier": True, "sleep": True}
    values = read(
        HvacState(True, "heat", 26.0, fan="2", swing_v="swing", features=feats)
    )
    assert (values["turbo"], values["filter"], values["sleep"]) == (1, 1, 1)
    assert (values["swing_v"], values["fan"], values["mode"]) == ("swing", "2", "heat")


def test_swing_sends_the_documented_bit():
    assert raw(HvacState(True, "cool", 22.0, swing_v="swing"), "swing_v") == 1
    assert raw(HvacState(True, "cool", 22.0, swing_v="off"), "swing_v") == 0


def test_start_timer_bit_stays_set_as_state_reset():
    assert read(HvacState(True, "cool", 22.0))["start_timer"] == 1


def test_previous_is_ignored():
    dev = device()
    on = HvacState(True, "cool", 22.0, swing_v="swing")
    off = HvacState(False, "heat", 30.0)
    assert dev.encode(off, on).signal == dev.encode(None, on).signal
    assert dev.encode(on, on).signal == dev.encode(None, on).signal


def test_message_shape():
    signal = device().encode(None, HvacState(True, "cool", 22.0)).signal
    assert signal.carrier == 38000
    pulses = signal.pulses
    per_frame = 2 + 2 * 88 + 2
    assert len(pulses) == 3 * per_frame
    for n in range(3):
        start = n * per_frame
        assert pulses[start : start + 2] == (5400, 2000)
        assert pulses[start + 2 : start + 4] == (500, 750)  # 0xAA LSB first
        assert pulses[start + 4 : start + 6] == (500, 1500)
    assert pulses[per_frame - 2 : per_frame] == (500, 3675)
    assert pulses[-2:] == (500, 103675)


def test_the_fixture_ends_on_unmerged_spaces():
    for record in load_oracle("SANYO_AC88"):
        assert len(record["pulses"]) == 3 * (2 + 2 * 88 + 2) + 1
        assert record["pulses"][-2:] == [3675, 100000]


def test_registry_serves_the_port():
    for model in SANYO_AC88_MODELS:
        assert isinstance(registry.get_device("sanyo", model), SanyoAc88Device)


def _record(**state):
    return next(
        r
        for r in load_oracle("SANYO_AC88")
        if all(r["state"].get(k) == v for k, v in state.items())
    )


@pytest.mark.parametrize(
    "state, defect",
    [
        ({"mode": "cool", "fan": "medium", "swing": "on"}, SWING),
        ({"mode": "auto", "sleep": "on"}, SLEEP),
    ],
)
def test_undeclared_deviation_is_reported(state, defect):
    dev = device()
    record = as_sent(wire(_record(**state)))
    assert_matches_oracle(dev, record, dev.LAYOUTS, (defect,))
    others = tuple(d for d in DEFECTS if d is not defect)
    with pytest.raises(AssertionError, match=f"'{defect.field}'"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=others)


def test_layouts_must_cover_every_frame():
    dev = device()
    record = wire(_record(mode="cool", fan="medium", swing="on"))
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, dev.LAYOUTS[:3], DEFECTS)


# ir_Sanyo_test.cpp DecodeSanyoAc88.DecodeRealExamples: decodeSanyoAc88
# matches with _tolerance + kSanyoAc88ExtraTolerance (30 %) and kMarkExcess;
# this capture has spaces as long as 944 µs for 750. C keeps the last of its
# three frames.
REAL_RAW = (
    "5374 1972 512 762 522 1510 498 780 578 1486 462 790 462 1550 544 708 "
    "510 1500 544 1470 516 762 482 770 516 1496 518 1510 498 780 468 1544 "
    "466 786 466 786 466 786 466 786 486 748 526 756 506 1520 516 764 516 "
    "1492 518 762 544 708 548 704 602 1434 556 1456 524 726 552 700 554 698 "
    "648 1438 548 684 536 1478 568 682 568 682 578 702 568 684 570 712 624 "
    "724 528 1482 528 726 528 1482 526 724 546 1524 568 682 540 710 544 734 "
    "542 1516 492 762 488 744 546 1482 492 788 544 734 494 758 492 760 490 "
    "744 548 828 494 760 494 758 494 758 494 786 492 760 494 758 494 742 "
    "508 746 508 788 492 760 494 786 494 786 494 742 508 744 508 788 570 "
    "760 494 784 494 788 568 786 492 744 508 772 608 768 538 714 490 786 "
    "628 728 494 786 494 758 494 742 508 1390 494 3692 5394 1960 494 784 "
    "494 1516 494 760 494 1516 494 760 492 1516 494 760 492 1518 524 1486 "
    "494 790 486 764 492 1524 538 1472 540 740 538 1546 546 728 524 726 526 "
    "728 524 728 526 728 524 728 524 1486 526 726 546 1464 550 702 550 728 "
    "552 702 550 1460 550 1460 550 702 552 728 550 702 550 1460 550 728 550 "
    "1464 548 704 546 704 548 732 546 704 548 704 548 730 548 1462 548 706 "
    "518 1492 546 706 518 1490 546 706 520 732 520 732 522 1492 518 760 518 "
    "732 546 1468 516 736 516 732 520 732 520 758 520 818 478 772 480 802 "
    "454 894 520 734 518 734 518 760 518 734 518 734 518 718 506 746 480 "
    "818 488 790 490 744 508 790 490 744 510 770 508 788 490 762 544 788 "
    "490 788 462 818 566 788 490 744 480 770 456 794 458 894 492 762 492 "
    "760 490 744 508 1390 492 3664 5398 1960 490 746 476 1552 492 742 508 "
    "1504 508 746 504 1522 494 786 492 1516 494 1516 494 760 492 786 494 "
    "1520 490 1520 458 822 458 1554 510 788 494 784 494 760 492 742 508 770 "
    "512 786 492 1516 520 760 520 1488 520 734 520 760 518 734 520 1490 520 "
    "1494 516 734 518 732 520 762 516 762 488 1522 458 1554 506 774 506 744 "
    "508 774 508 770 510 742 506 746 540 1472 506 744 508 1522 488 764 488 "
    "1504 538 758 520 734 520 760 520 1490 518 734 520 734 520 1490 520 760 "
    "518 760 538 770 488 764 516 734 518 734 518 818 476 802 476 774 478 "
    "904 538 734 520 762 516 818 510 748 476 772 458 794 458 792 516 736 "
    "516 736 516 736 516 738 514 762 516 764 514 738 516 738 538 766 516 "
    "738 514 738 514 766 512 794 486 768 486 794 486 766 512 738 488 1398 "
    "504"
)


def test_real_raw_capture_decodes():
    pulses = [int(x) for x in REAL_RAW.split()]
    frames = decode(SANYO_AC88, pulses, expected=["main", "main", "main"])
    assert frames[-1].data == bytes.fromhex("aa59a018062a1200000080")
