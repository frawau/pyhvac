import pytest

from oracle import load_oracle
from port_oracle import (
    Defect,
    assert_matches_oracle,
    assert_sequence_matches_c,
    oracle_params,
    sequence_params,
    state_from_record,
)
from pyhvac import registry
from pyhvac.ir.codec import decode
from pyhvac.plugins.goodweather import (
    GOODWEATHER,
    GOODWEATHER_LAYOUT,
    GOODWEATHER_MODELS,
    GoodweatherDevice,
)
from pyhvac.state import HvacState

# The C path deviates from the documented values here:
# - IRac::goodweather sends kGoodweatherSwingSlow for any swing but off (it
#   does not use convertSwingV), so swing "auto high" (the port's "2") never
#   reached C as kGoodweatherSwingFast.
DEFECTS = (
    Defect("swing_v", "fast", "slow", "IRac::goodweather sends Slow for any swing"),
)


def wire(raw):
    """The frame sendGoodweather puts on the wire for the 48-bit ``raw``
    state: each byte, LSB first, followed by its complement."""
    out = bytearray()
    for b in raw.to_bytes(6, "little"):
        out += bytes((b, ~b & 0xFF))
    return bytes(out)


# Real captures from ir_Goodweather_test.cpp (issue #697).
ON_COOL_20_SWING_FAST = wire(0xD52462000000)  # Command Power
OFF_COOL_22 = wire(0xD52668000000)  # Command Power
ON_COOL_22 = wire(0xD5266A000000)  # Command Power
TEMP_UP_24 = wire(0xD5286A020000)
TEMP_DOWN_23 = wire(0xD5276A030000)
SWING_SLOW_22 = wire(0xD52666040000)


def device(model="ZH/JT-03 remote"):
    return GoodweatherDevice("goodweather", model)


def data(state, previous=None):
    dev = device()
    if previous is not None:
        previous = dev.normalise(previous)
    (main,) = dev.frames(previous, dev.normalise(state), ())
    return main.data


def read(state):
    return GOODWEATHER_LAYOUT.read(data(state))


@pytest.mark.parametrize("record", oracle_params("GOODWEATHER"))
def test_matches_c_library(record):
    dev = device()
    assert_matches_oracle(dev, record, dev.LAYOUTS, DEFECTS)


@pytest.mark.parametrize("record, states", sequence_params("GOODWEATHER"))
def test_sequence_matches_a_persistent_c_object(record, states):
    # The Light/Turbo "toggles" and the Command button could depend on the
    # message before; a persistent C object shows they do not.
    dev = device()
    assert_sequence_matches_c(dev, record, states, dev.LAYOUTS, DEFECTS)


def test_layout_round_trips_every_oracle_state():
    dev = device()
    for record in load_oracle("GOODWEATHER"):
        state = state_from_record(dev, record["state"])
        (main,) = dev.frames(None, state, ())
        values = GOODWEATHER_LAYOUT.read(main.data)
        assert GOODWEATHER_LAYOUT.build(**values) == bytearray(main.data)
        assert GOODWEATHER_LAYOUT.checksum.check(main.data)


def test_every_oracle_message_is_one_frame():
    for record in load_oracle("GOODWEATHER"):
        (main,) = decode(GOODWEATHER, record["pulses"], ["main"])
        assert main.data[10:] == b"\xd5\x2a"  # kGoodweatherStateInit's top byte


def test_the_port_reproduces_the_on_cool_22_capture():
    # "Power: On, Mode: 1 (Cool), Temp: 22C, Fan: 3 (Low), Swing: 2 (Off),
    # Command: 0 (Power)": the remote's own frame.
    assert data(HvacState(True, "cool", 22.0, fan="1")) == ON_COOL_22


@pytest.mark.parametrize(
    "capture, expected",
    [
        (
            ON_COOL_20_SWING_FAST,
            {"command": "power", "power": 1, "temperature": 20, "swing_v": "fast"},
        ),
        (
            OFF_COOL_22,
            {"command": "power", "power": 0, "mode": "cool", "temperature": 22},
        ),
        (
            TEMP_UP_24,
            {"command": "temp_up", "power": 1, "temperature": 24, "swing_v": "off"},
        ),
        (
            TEMP_DOWN_23,
            {"command": "temp_down", "power": 1, "temperature": 23, "fan": "1"},
        ),
        (
            SWING_SLOW_22,
            {"command": "swing", "power": 1, "temperature": 22, "swing_v": "slow"},
        ),
    ],
)
def test_real_captures_read_back(capture, expected):
    # These carry the key actually pressed or an off message in cool, which
    # the C path (and so the port) never sends; they read back through the
    # layout. (The port does send swing fast: see the capture test below.)
    values = GOODWEATHER_LAYOUT.read(capture)
    assert GOODWEATHER_LAYOUT.checksum.check(capture)
    assert {k: values[k] for k in expected} == expected
    assert GOODWEATHER_LAYOUT.build(**values) == bytearray(capture)


def test_complements_follow_every_byte():
    raw = data(HvacState(True, "heat", 27.0, fan="2", swing_v="2"))
    assert all(raw[i + 1] == ~raw[i] & 0xFF for i in range(0, 12, 2))


@pytest.mark.parametrize("mode", ["auto", "cool", "fan", "dry", "heat"])
@pytest.mark.parametrize("t", [16.0, 23.0, 31.0])
def test_off_carries_mode_auto_and_the_power_button(mode, t):
    # IRac passes mode "off"; convertMode maps it to kGoodweatherAuto. The
    # other settings are sent as given.
    values = read(HvacState(False, mode, t, fan="3", swing_v="1"))
    assert (values["power"], values["command"], values["mode"]) == (0, "power", "auto")
    assert (values["temperature"], values["fan"], values["swing_v"]) == (
        int(t),
        "3",
        "slow",
    )


@pytest.mark.parametrize("mode", ["auto", "cool", "fan", "dry", "heat"])
def test_on_always_names_the_power_button(mode):
    # IRac::goodweather ends with setPower, overwriting the Mode, UpTemp/
    # DownTemp, Fan, Swing, Turbo, Light and Sleep commands the setters wrote.
    values = read(
        HvacState(
            True,
            mode,
            31.0,
            fan="2",
            swing_v="2",
            features={"powerful": True, "light": True},
        )
    )
    assert (values["power"], values["command"], values["mode"]) == (1, "power", mode)


def test_setpoint_is_clamped_to_16_31():
    assert read(HvacState(True, "cool", 10.0))["temperature"] == 16
    assert read(HvacState(True, "heat", 35.0))["temperature"] == 31


@pytest.mark.parametrize("fan, raw", [("auto", 0), ("1", 3), ("2", 2), ("3", 1)])
def test_every_fan_level_uses_the_documented_codes(fan, raw):
    # convertFan: kLow -> kGoodweatherFanLow (3), kMedium -> Med (2),
    # kHigh -> High (1), auto -> Auto (0).
    raw_read = GOODWEATHER_LAYOUT.read_raw(
        data(HvacState(True, "cool", 22.0, fan=fan)), "fan"
    )
    assert raw_read == raw


@pytest.mark.parametrize("swing, raw", [("off", 0b10), ("1", 0b01), ("2", 0b00)])
def test_every_swing_value(swing, raw):
    # kGoodweatherSwingOff = 0b10, kGoodweatherSwingSlow = 0b01,
    # kGoodweatherSwingFast = 0b00.
    raw_read = GOODWEATHER_LAYOUT.read_raw(
        data(HvacState(True, "cool", 22.0, swing_v=swing)), "swing_v"
    )
    assert raw_read == raw


def test_powerful_is_the_turbo_bit_and_light_the_light_bit():
    turbo = read(HvacState(True, "cool", 22.0, features={"powerful": True}))
    assert turbo["turbo"] == 1
    assert read(HvacState(True, "cool", 22.0, features={"light": True}))["light"] == 1
    plain = read(HvacState(True, "cool", 22.0))
    assert (plain["turbo"], plain["light"]) == (0, 0)


def test_quiet_is_not_offered():
    # ir_Goodweather.h has no quiet bit (IRac: "No Quiet setting available").
    assert "quiet" not in device().capabilities.features
    assert data(HvacState(True, "cool", 22.0, features={"quiet": True})) == data(
        HvacState(True, "cool", 22.0)
    )


def test_swing_offers_the_two_speeds_and_off():
    # kGoodweatherSwingSlow / kGoodweatherSwingFast / kGoodweatherSwingOff.
    assert device().capabilities.swing_v.values == ("off", "1", "2")


def test_the_port_reproduces_the_swing_fast_capture():
    # ir_Goodweather_test.cpp (issue #697): "Power: On, Mode: 1 (Cool),
    # Temp: 20C, Fan: 3 (Low), Swing: 0 (Fast), Command: 0 (Power)".
    target = HvacState(True, "cool", 20.0, fan="1", swing_v="2")
    assert data(target) == ON_COOL_20_SWING_FAST


@pytest.mark.parametrize("power", [True, False])
def test_sleep_sets_the_sleep_bit(power):
    # IRGoodweatherAc::setSleep; IRac::goodweather: setSleep(sleep >= 0). Its
    # command is overwritten by setPower, as for light and turbo.
    values = read(HvacState(power, "cool", 22.0, features={"sleep": True}))
    assert (values["sleep"], values["command"]) == (1, "power")
    assert read(HvacState(power, "cool", 22.0))["sleep"] == 0


def test_undeclared_swing_fast_deviation_is_reported():
    dev = device()
    record = next(
        r
        for r in load_oracle("GOODWEATHER")
        if r["state"].get("swing") == "auto high" and r["state"]["mode"] != "off"
    )
    with pytest.raises(AssertionError, match="swing_v"):
        assert_matches_oracle(dev, record, dev.LAYOUTS, defects=())


def test_air_flow_is_never_set():
    # IRac has no air flow setting.
    values = read(
        HvacState(True, "heat", 18.0, fan="2", swing_v="1", features={"light": True})
    )
    assert values["air_flow"] == 0


@pytest.mark.parametrize(
    "previous",
    [
        None,
        HvacState(False, "heat", 18.0),
        HvacState(True, "cool", 26.0, fan="1", swing_v="off"),
        HvacState(True, "cool", 22.0, fan="3", features={"light": True}),
        HvacState(True, "cool", 22.0, features={"powerful": True, "light": True}),
    ],
)
def test_previous_is_ignored(previous):
    # IRac::goodweather writes Light and Turbo from the desired state and
    # Command from setPower on every message; IRac::handleToggles has no
    # GOODWEATHER case (see the sequence test).
    dev = device()
    target = HvacState(True, "cool", 22.0, fan="3", features={"light": True})
    assert dev.encode(previous, target).signal == dev.encode(None, target).signal


def test_message_shape():
    pulses = device().encode(None, HvacState(True, "cool", 22.0)).signal.pulses
    assert pulses[:2] == (6820, 6820)
    # A closing bit mark, kGoodweatherHdrSpace, a bit mark, kDefaultMessageGap.
    assert pulses[-4:] == (580, 6820, 580, 100000)
    assert len(pulses) == 2 + 2 * 96 + 4


@pytest.mark.parametrize("model", GOODWEATHER_MODELS)
def test_registry_serves_the_port(model):
    assert isinstance(registry.get_device("goodweather", model), GoodweatherDevice)


def test_layouts_must_cover_every_frame():
    dev = device()
    record = load_oracle("GOODWEATHER")[0]
    with pytest.raises(AssertionError, match="layout"):
        assert_matches_oracle(dev, record, (), DEFECTS)


# decodeGoodweather matches the bits with _tolerance +
# kGoodweatherExtraTolerance (37 %) and kMarkExcess.
def test_decode_tolerance_is_the_c_decoders():
    assert (GOODWEATHER.tolerance, GOODWEATHER.mark_excess) == (0.37, 50)


# RealExampleDecode's rawData_71DD9105: an 858 µs bit mark (580 nominal) that
# matchMark takes, within 37 % of 580 + kMarkExcess.
RAW_71DD9105 = [
    6190,
    7296,
    696,
    1496,
    634,
    1562,
    642,
    1582,
    640,
    1564,
    564,
    1598,
    638,
    1558,
    646,
    1560,
    588,
    1616,
    618,
    520,
    620,
    494,
    622,
    494,
    646,
    494,
    620,
    496,
    644,
    494,
    590,
    528,
    642,
    494,
    642,
    1544,
    638,
    1584,
    618,
    1564,
    804,
    1394,
    620,
    1564,
    640,
    1558,
    644,
    1586,
    562,
    1616,
    620,
    492,
    672,
    470,
    622,
    494,
    646,
    494,
    622,
    494,
    646,
    494,
    620,
    498,
    644,
    492,
    596,
    520,
    644,
    494,
    592,
    1596,
    612,
    1584,
    642,
    1560,
    614,
    1612,
    594,
    1584,
    620,
    1558,
    646,
    1556,
    644,
    1562,
    618,
    520,
    620,
    494,
    620,
    494,
    646,
    494,
    568,
    548,
    644,
    494,
    616,
    1570,
    638,
    494,
    670,
    1534,
    568,
    550,
    646,
    1556,
    616,
    526,
    618,
    492,
    672,
    1532,
    568,
    550,
    646,
    1558,
    640,
    500,
    618,
    1560,
    668,
    470,
    642,
    1548,
    658,
    1536,
    642,
    520,
    588,
    504,
    644,
    492,
    644,
    478,
    642,
    1582,
    618,
    1586,
    590,
    506,
    640,
    1556,
    646,
    1584,
    562,
    1616,
    620,
    1558,
    646,
    1556,
    670,
    454,
    638,
    492,
    648,
    1558,
    642,
    478,
    644,
    492,
    590,
    530,
    858,
    1342,
    642,
    496,
    618,
    1564,
    642,
    492,
    642,
    1548,
    636,
    492,
    648,
    494,
    622,
    1562,
    642,
    492,
    644,
    1562,
    618,
    520,
    620,
    1558,
    644,
    476,
    640,
    1558,
    646,
    1558,
    612,
    7382,
    594,
]


def test_real_capture_with_a_long_mark_decodes():
    (frame,) = decode(GOODWEATHER, RAW_71DD9105, expected=["main"])
    assert bytes(frame.data[0::2]) == (0xD5276A030000).to_bytes(6, "little")
