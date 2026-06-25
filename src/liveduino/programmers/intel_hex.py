"""Intel HEX parsing for firmware images.

Minimal Intel HEX decoder used by the programmers to turn a ``.hex`` firmware
file into a flat binary image ready to be written to flash. Only the record
types needed for AVR firmware are handled; gaps between data records are padded
with ``0xFF`` (erased flash).
"""

from __future__ import annotations

from liveduino.exceptions import FlashError

_RECORD_DATA = 0x00
_RECORD_EOF = 0x01
_RECORD_EXT_SEGMENT = 0x02
_RECORD_EXT_LINEAR = 0x04
_PAD_BYTE = 0xFF


def parse_intel_hex(text: str) -> bytes:
    """Parse Intel HEX text into a flat binary image, padding gaps with 0xFF."""
    image = bytearray()
    base_address = 0
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        record = _parse_record(line, line_number)
        record_type = record[3]
        if record_type == _RECORD_EOF:
            break
        if record_type == _RECORD_DATA:
            base_address = _apply_data(image, base_address, record)
        elif record_type in (_RECORD_EXT_SEGMENT, _RECORD_EXT_LINEAR):
            base_address = _extended_base(record_type, record)
    return bytes(image)


def _parse_record(line: str, line_number: int) -> bytes:
    """Decode and checksum-validate a single Intel HEX record line."""
    if not line.startswith(":"):
        raise FlashError(f"Invalid Intel HEX line {line_number}: missing ':' start code")
    try:
        record = bytes.fromhex(line[1:])
    except ValueError as exc:
        raise FlashError(f"Invalid Intel HEX line {line_number}: non-hex characters") from exc
    if len(record) < 5:
        raise FlashError(f"Invalid Intel HEX line {line_number}: record too short")
    length = record[0]
    if len(record) != length + 5:
        raise FlashError(f"Invalid Intel HEX line {line_number}: byte count mismatch")
    if sum(record) & 0xFF != 0:
        raise FlashError(f"Invalid Intel HEX line {line_number}: checksum error")
    return record


def _apply_data(image: bytearray, base_address: int, record: bytes) -> int:
    """Write a data record's payload into the image at its absolute address."""
    length = record[0]
    offset = base_address + (record[1] << 8 | record[2])
    payload = record[4 : 4 + length]
    end = offset + length
    if end > len(image):
        image.extend([_PAD_BYTE] * (end - len(image)))
    image[offset:end] = payload
    return base_address


def _extended_base(record_type: int, record: bytes) -> int:
    """Return the new base address from an extended segment/linear record."""
    value = record[4] << 8 | record[5]
    if record_type == _RECORD_EXT_SEGMENT:
        return value << 4
    return value << 16
