"""Unit tests for the Intel HEX parser.

Cover decoding of data records, gap padding, extended addressing, EOF handling,
and the malformed-input error paths.
"""

import pytest

from liveduino.exceptions import FlashError
from liveduino.programmers.intel_hex import parse_intel_hex


@pytest.mark.unit
def test_parse_single_data_record() -> None:
    assert parse_intel_hex(":01000000AA55\n:00000001FF\n") == bytes([0xAA])


@pytest.mark.unit
def test_blank_lines_are_ignored() -> None:
    assert parse_intel_hex("\n  \n:01000000AA55\n") == bytes([0xAA])


@pytest.mark.unit
def test_gaps_are_padded_with_ff() -> None:
    text = ":0100000011EE\n:0100030022DA\n:00000001FF\n"
    assert parse_intel_hex(text) == bytes([0x11, 0xFF, 0xFF, 0x22])


@pytest.mark.unit
def test_extended_segment_address_offsets_data() -> None:
    text = ":020000020001FB\n:0100000033CC\n:00000001FF\n"
    image = parse_intel_hex(text)
    assert len(image) == 17
    assert image[16] == 0x33
    assert image[:16] == bytes([0xFF] * 16)


@pytest.mark.unit
def test_extended_linear_address_is_supported() -> None:
    text = ":020000040000FA\n:01000000AB54\n:00000001FF\n"
    assert parse_intel_hex(text) == bytes([0xAB])


@pytest.mark.unit
def test_missing_start_code_raises() -> None:
    with pytest.raises(FlashError, match="missing ':'"):
        parse_intel_hex("01000000AA55\n")


@pytest.mark.unit
def test_non_hex_characters_raise() -> None:
    with pytest.raises(FlashError, match="non-hex"):
        parse_intel_hex(":zzzz\n")


@pytest.mark.unit
def test_record_too_short_raises() -> None:
    with pytest.raises(FlashError, match="too short"):
        parse_intel_hex(":0102\n")


@pytest.mark.unit
def test_byte_count_mismatch_raises() -> None:
    with pytest.raises(FlashError, match="byte count"):
        parse_intel_hex(":02000000AA\n")


@pytest.mark.unit
def test_checksum_error_raises() -> None:
    with pytest.raises(FlashError, match="checksum"):
        parse_intel_hex(":01000000AA00\n")
