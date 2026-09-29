import pytest

from pyhvac.fields import (
    Checksums,
    Copy,
    Crc8,
    Field,
    HighNibbleSum,
    InvertedPairs,
    Layout,
    NibbleSum,
    Sum8,
    Xor8,
    bit_reverse,
)

MODE = {"auto": 0, "dry": 2, "cool": 3, "heat": 4, "fan": 6}


def layout(**kw):
    fields = {
        "power": Field.at(1, 0, 1),
        "mode": Field.at(1, 4, 3, values=MODE),
        "temperature": Field.at(2, 1, 6, encode=lambda c: round(c * 2) - 20),
        "span": Field.at(3, 6, 4),  # bits 6-7 of byte 3 and 0-1 of byte 4
    }
    return Layout(b"\x11\x00\x00\x00\x00\x00", fields, **kw)


def test_build_writes_fields_over_the_skeleton():
    data = layout().build(power=True, mode="cool", temperature=24.0, span=0b1011)
    assert data[0] == 0x11
    assert data[1] == 0x01 | 3 << 4
    assert data[2] == (24 * 2 - 20) << 1
    assert data[3] == 0b11 << 6 and data[4] == 0b10


def test_fields_not_given_keep_skeleton_bits():
    lay = Layout(b"\xff", {"x": Field.at(0, 0, 2)})
    assert lay.build(x=0) == bytearray(b"\xfc")
    assert lay.build() == bytearray(b"\xff")


def test_read_reverses_build():
    lay = layout()
    data = lay.build(power=True, mode="dry", temperature=18.5, span=9)
    assert lay.read(data) == {"power": 1, "mode": "dry", "temperature": 17, "span": 9}


def test_read_returns_raw_int_for_unknown_table_value():
    lay = Layout(b"\x00", {"mode": Field.at(0, 0, 3, values=MODE)})
    assert lay.read(b"\x07") == {"mode": 7}


@pytest.mark.parametrize(
    "fields",
    [
        {"a": Field.at(0, 0, 4), "b": Field.at(0, 3, 2)},  # overlap
        {"a": Field.at(1, 4, 8)},  # past the skeleton
    ],
)
def test_layout_validation(fields):
    with pytest.raises(ValueError):
        Layout(b"\x00\x00", fields)


def test_checksum_may_not_overlap_a_field():
    with pytest.raises(ValueError, match="checksum"):
        Layout(b"\x00\x00", {"a": Field.at(1, 0, 1)}, checksum=Sum8(0, 1, 1))


@pytest.mark.parametrize(
    "values",
    [dict(nope=1), dict(mode="heat_cool"), dict(power=2), dict(temperature=60.0)],
)
def test_build_validation(values):
    with pytest.raises(ValueError):
        layout().build(**values)


def test_field_takes_table_or_encoder_not_both():
    with pytest.raises(ValueError):
        Field(0, 3, values=MODE, encode=int)


def test_checksum_applied_last_unless_disabled():
    lay = Layout(b"\x01\x02\x00", {"x": Field.at(1, 4, 4)}, checksum=Sum8(0, 2, 2))
    assert lay.build(x=1)[2] == 0x01 + 0x12
    assert lay.build(checksum=False, x=1)[2] == 0


def test_sum8_matches_airspool_reference():
    data = bytearray.fromhex("23CB260175042300000000E00091")
    assert Sum8(0, 13, 13).check(data)


def test_nibble_sum():
    assert NibbleSum(0, 2, 2).compute(b"\x12\x34\x00") == 1 + 2 + 3 + 4


def test_xor8():
    assert Xor8(0, 3, 3).compute(b"\x0f\xf0\x11\x00") == 0x0F ^ 0xF0 ^ 0x11


def test_reverse_bit_reverses_input_bytes():
    assert Sum8(0, 2, 2, reverse=True).compute(b"\x01\x02\x00") == 0x80 + 0x40


def test_crc8_standard_check_values():
    msg = bytearray(b"123456789\x00")
    assert Crc8(0, 9, 9, poly=0x07).compute(msg) == 0xF4  # CRC-8/SMBUS
    assert Crc8(0, 9, 9, poly=0x31, reflect=True).compute(msg) == 0xA1  # MAXIM


def test_inverted_pairs():
    data = bytearray(b"\x12\x00\x34\x00")
    InvertedPairs(0, 4).apply(data)
    assert data == bytearray(b"\x12\xed\x34\xcb")
    assert InvertedPairs(0, 4).check(data)
    assert InvertedPairs(0, 4).positions() == {1, 3}


def test_bit_reverse():
    assert bit_reverse(0x01) == 0x80 and bit_reverse(0xA0) == 0x05


def test_split_field_reads_and_writes_scattered_bits():
    # raw bit 0 -> byte 0 bit 5, raw bit 1 -> byte 1 bit 7, raw bit 2 -> byte 0 bit 0
    f = Field.over((0, 5), (1, 7), (0, 0))
    assert tuple(f.bits) == (5, 15, 0) and f.width == 3
    lay = Layout(b"\x00\x00", {"s": f, "rest": Field.at(0, 1, 4)})
    data = lay.build(s=0b101)
    assert data == bytearray(b"\x21\x00")
    assert lay.read(lay.build(s=0b010))["s"] == 0b010


@pytest.mark.parametrize(
    "kw",
    [
        dict(offset=3, width=2, spread=(3, 3)),  # a bit twice
        dict(offset=3, width=3, spread=(3, 4)),  # width disagrees
        dict(offset=4, width=2, spread=(3, 9)),  # offset is not the first bit
        dict(offset=0, width=2, spread=(0, -1)),  # negative bit
    ],
)
def test_split_field_validation(kw):
    with pytest.raises(ValueError):
        Field(**kw)


def test_split_field_overlap_is_checked_per_bit():
    with pytest.raises(ValueError, match="overlap"):
        Layout(b"\x00\x00", {"a": Field.over((0, 1), (1, 2)), "b": Field.at(1, 2, 1)})


def test_checksum_bits_default_to_whole_bytes():
    assert Sum8(0, 1, 1).bits() == set(range(8, 16))


def test_high_nibble_sum_shares_its_byte_with_fields():
    lay = Layout(
        b"\x00\x00\x00",
        {"a": Field.at(0, 0, 8), "low": Field.at(2, 0, 4)},
        checksum=HighNibbleSum(0, 2, 2),
    )
    data = lay.build(a=0x12, low=0xF)
    assert data[2] == 0x3F  # 1 + 2 in the high nibble, the field below it
    assert lay.checksum.check(data)
    assert lay.checksum.positions() == {2}
    assert lay.checksum.bits() == set(range(20, 24))
    with pytest.raises(ValueError, match="checksum"):
        Layout(b"\x00\x00\x00", {"a": Field.at(2, 3, 2)}, HighNibbleSum(0, 2, 2))


def test_high_nibble_sum_may_count_the_low_nibble_of_its_byte():
    data = bytearray(b"\x12\x05")
    HighNibbleSum(0, 1, 1, with_low=True).apply(data)
    assert data[1] == (1 + 2 + 5) << 4 | 5
    assert HighNibbleSum(0, 1, 1, with_low=True).check(data)
    data = bytearray(b"\xff\xff\x00")
    HighNibbleSum(0, 2, 2).apply(data)
    assert data[2] == (60 & 0x0F) << 4  # mod 16


def test_copy_and_complement_blocks():
    data = bytearray(b"\x12\x34\x00\x00")
    Copy(0, 2, 2).apply(data)
    assert data == bytearray(b"\x12\x34\x12\x34") and Copy(0, 2, 2).check(data)
    Copy(0, 2, 2, invert=True).apply(data)
    assert data == bytearray(b"\x12\x34\xed\xcb")
    assert Copy(0, 2, 2, invert=True).check(data) and not Copy(0, 2, 2).check(data)
    assert Copy(0, 2, 2).positions() == {2, 3}


def test_checksums_apply_every_part():
    both = Checksums(Sum8(0, 2, 2), Sum8(3, 5, 5))
    data = bytearray(b"\x01\x02\x00\x03\x04\x00")
    both.apply(data)
    assert data == bytearray(b"\x01\x02\x03\x03\x04\x07")
    assert both.check(data) and both.positions() == {2, 5}
    data[5] = 0
    assert not both.check(data)
    assert both.bits() == set(range(16, 24)) | set(range(40, 48))
    assert both == Checksums(Sum8(0, 2, 2), Sum8(3, 5, 5))


def test_checksum_past_the_skeleton_is_refused():
    with pytest.raises(ValueError, match="past"):
        Layout(b"\x00", {}, checksum=HighNibbleSum(0, 1, 1))
