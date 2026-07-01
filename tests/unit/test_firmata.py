"""Unit tests for the native FirmataProtocol.

Exercise the Firmata 2.x command encoding and the inbound report parser over a
fake driver, including reporting setup and unsupported operations.
"""

from __future__ import annotations

import pytest

from liveduino.constants import INPUT, INPUT_PULLUP, OUTPUT
from liveduino.exceptions import (
    BoardConnectionError,
    InvalidModeError,
    InvalidValueError,
    UnsupportedOperationError,
)
from liveduino.protocols.firmata import (
    ANALOG_MAPPING_QUERY,
    ANALOG_MAPPING_RESPONSE,
    ANALOG_MESSAGE,
    CAPABILITY_QUERY,
    CAPABILITY_RESPONSE,
    DIGITAL_MESSAGE,
    END_SYSEX,
    EXTENDED_ANALOG,
    I2C_CONFIG,
    I2C_REPLY,
    I2C_REQUEST,
    PIN_STATE_QUERY,
    PIN_STATE_RESPONSE,
    REPORT_ANALOG,
    REPORT_DIGITAL,
    REPORT_FIRMWARE,
    SERVO_CONFIG,
    SET_DIGITAL_PIN_VALUE,
    SET_PIN_MODE,
    START_SYSEX,
    FirmataProtocol,
)
from tests.shared.fake_driver import FakeDriver


def _connected() -> tuple[FirmataProtocol, FakeDriver]:
    driver = FakeDriver()
    protocol = FirmataProtocol(driver)
    protocol.connect()
    return protocol, driver


def _i2c_reply_bytes(address: int, register: int, data: list[int]) -> bytes:
    """Encode an inbound I2C_REPLY sysex (each byte as a 7-bit LSB/MSB pair)."""
    encoded: list[int] = []
    for value in (address, register, *data):
        encoded += [value & 0x7F, (value >> 7) & 0x7F]
    return bytes([START_SYSEX, I2C_REPLY, *encoded, END_SYSEX])


@pytest.mark.unit
def test_connect_opens_driver() -> None:
    protocol, driver = _connected()
    assert driver.opened is True


@pytest.mark.unit
def test_disconnect_closes_driver_and_clears_state() -> None:
    protocol, driver = _connected()
    protocol.disconnect()
    assert driver.opened is False
    protocol.disconnect()  # idempotent when already disconnected


@pytest.mark.unit
def test_pin_mode_encodes_command() -> None:
    protocol, driver = _connected()
    protocol.pin_mode(13, OUTPUT)
    assert bytes(driver.written) == bytes([SET_PIN_MODE, 13, 0x01])


@pytest.mark.unit
def test_pin_mode_input_and_pullup() -> None:
    protocol, driver = _connected()
    protocol.pin_mode(2, INPUT)
    protocol.pin_mode(3, INPUT_PULLUP)
    assert bytes(driver.written) == bytes([SET_PIN_MODE, 2, 0x00, SET_PIN_MODE, 3, 0x0B])


@pytest.mark.unit
def test_pin_mode_invalid_raises() -> None:
    protocol, _ = _connected()
    with pytest.raises(InvalidModeError):
        protocol.pin_mode(13, 99)  # type: ignore[arg-type]


@pytest.mark.unit
def test_digital_write_encodes_command() -> None:
    protocol, driver = _connected()
    protocol.digital_write(13, 1)
    assert bytes(driver.written) == bytes([SET_DIGITAL_PIN_VALUE, 13, 1])


@pytest.mark.unit
def test_digital_write_invalid_value_raises() -> None:
    protocol, _ = _connected()
    with pytest.raises(InvalidValueError):
        protocol.digital_write(13, 5)  # type: ignore[arg-type]


@pytest.mark.unit
def test_digital_read_enables_reporting_and_parses_message() -> None:
    protocol, driver = _connected()
    # Digital port 0, pin 2 high (bit 2 set -> 0x04).
    driver.feed(bytes([DIGITAL_MESSAGE | 0, 0x04, 0x00]))
    assert protocol.digital_read(2) == 1
    assert protocol.digital_read(3) == 0
    assert bytes(driver.written[:2]) == bytes([REPORT_DIGITAL | 0, 1])
    # Reporting is only requested once per port.
    assert bytes(driver.written) == bytes([REPORT_DIGITAL | 0, 1])


@pytest.mark.unit
def test_analog_read_enables_reporting_and_parses_message() -> None:
    protocol, driver = _connected()
    # Analog channel 5, value 515 -> lsb 0x03, msb 0x04.
    driver.feed(bytes([ANALOG_MESSAGE | 5, 0x03, 0x04]))
    assert protocol.analog_read(5) == 515
    assert bytes(driver.written) == bytes([REPORT_ANALOG | 5, 1])


@pytest.mark.unit
def test_analog_read_defaults_to_zero_without_data() -> None:
    protocol, _ = _connected()
    assert protocol.analog_read(0) == 0


@pytest.mark.unit
def test_analog_write_encodes_mode_and_value() -> None:
    protocol, driver = _connected()
    protocol.analog_write(6, 200)
    assert bytes(driver.written) == bytes(
        [SET_PIN_MODE, 6, 0x03, ANALOG_MESSAGE | 6, 200 & 0x7F, (200 >> 7) & 0x7F]
    )


@pytest.mark.unit
def test_analog_write_invalid_value_raises() -> None:
    protocol, _ = _connected()
    with pytest.raises(InvalidValueError):
        protocol.analog_write(6, 999)


@pytest.mark.unit
def test_analog_write_uses_extended_analog_for_high_pins() -> None:
    protocol, driver = _connected()
    protocol.analog_write(16, 200)
    assert bytes(driver.written) == bytes(
        [
            SET_PIN_MODE, 16, 0x03,
            START_SYSEX, EXTENDED_ANALOG, 16, 200 & 0x7F, (200 >> 7) & 0x7F, END_SYSEX,
        ]
    )


@pytest.mark.unit
def test_servo_write_sets_mode_and_angle() -> None:
    protocol, driver = _connected()
    protocol.servo_write(9, 90)
    assert bytes(driver.written) == bytes(
        [SET_PIN_MODE, 9, 0x04, ANALOG_MESSAGE | 9, 90 & 0x7F, (90 >> 7) & 0x7F]
    )


@pytest.mark.unit
def test_servo_write_invalid_angle_raises() -> None:
    protocol, _ = _connected()
    with pytest.raises(InvalidValueError):
        protocol.servo_write(9, 181)


@pytest.mark.unit
def test_servo_write_uses_extended_analog_for_high_pins() -> None:
    protocol, driver = _connected()
    protocol.servo_write(16, 90)
    assert bytes(driver.written) == bytes(
        [
            SET_PIN_MODE, 16, 0x04,
            START_SYSEX, EXTENDED_ANALOG, 16, 90 & 0x7F, (90 >> 7) & 0x7F, END_SYSEX,
        ]
    )


@pytest.mark.unit
def test_servo_config_encodes_sysex() -> None:
    protocol, driver = _connected()
    protocol.servo_config(9, 600, 2400)
    assert bytes(driver.written) == bytes(
        [
            START_SYSEX,
            SERVO_CONFIG,
            9,
            600 & 0x7F,
            (600 >> 7) & 0x7F,
            2400 & 0x7F,
            (2400 >> 7) & 0x7F,
            END_SYSEX,
        ]
    )


@pytest.mark.unit
def test_servo_config_invalid_pulse_raises() -> None:
    protocol, _ = _connected()
    with pytest.raises(InvalidValueError):
        protocol.servo_config(9, 0, 0x4000)


@pytest.mark.unit
def test_i2c_config_encodes_sysex() -> None:
    protocol, driver = _connected()
    protocol.i2c_config()
    assert bytes(driver.written) == bytes([START_SYSEX, I2C_CONFIG, 0, 0, END_SYSEX])


@pytest.mark.unit
def test_i2c_config_invalid_delay_raises() -> None:
    protocol, _ = _connected()
    with pytest.raises(InvalidValueError):
        protocol.i2c_config(0x4000)


@pytest.mark.unit
def test_i2c_write_encodes_request() -> None:
    protocol, driver = _connected()
    protocol.i2c_write(0x68, [0x01, 0x02])
    assert bytes(driver.written) == bytes(
        [START_SYSEX, I2C_REQUEST, 0x68, 0x00, 0x01, 0x00, 0x02, 0x00, END_SYSEX]
    )


@pytest.mark.unit
def test_i2c_write_invalid_address_raises() -> None:
    protocol, _ = _connected()
    with pytest.raises(InvalidValueError):
        protocol.i2c_write(0x80, [0x00])


@pytest.mark.unit
def test_i2c_write_invalid_byte_raises() -> None:
    protocol, _ = _connected()
    with pytest.raises(InvalidValueError):
        protocol.i2c_write(0x10, [0x100])


@pytest.mark.unit
def test_i2c_read_without_register() -> None:
    protocol, driver = _connected()
    driver.feed(_i2c_reply_bytes(0x68, 0, [0x12, 0x34]))
    assert protocol.i2c_read(0x68, 2) == bytes([0x12, 0x34])
    assert bytes(driver.written) == bytes([START_SYSEX, I2C_REQUEST, 0x68, 0x08, 2, 0, END_SYSEX])


@pytest.mark.unit
def test_i2c_read_with_register() -> None:
    protocol, driver = _connected()
    driver.feed(_i2c_reply_bytes(0x68, 0x05, [0xAB]))
    assert protocol.i2c_read(0x68, 1, register=0x05) == bytes([0xAB])
    assert bytes(driver.written) == bytes(
        [START_SYSEX, I2C_REQUEST, 0x68, 0x08, 0x05, 0x00, 1, 0, END_SYSEX]
    )


@pytest.mark.unit
def test_i2c_read_restart_sets_mode_bit() -> None:
    protocol, driver = _connected()
    driver.feed(_i2c_reply_bytes(0x10, 0, [0x01]))
    protocol.i2c_read(0x10, 1, restart=True)
    assert bytes(driver.written) == bytes([START_SYSEX, I2C_REQUEST, 0x10, 0x48, 1, 0, END_SYSEX])


@pytest.mark.unit
def test_i2c_read_invalid_count_raises() -> None:
    protocol, _ = _connected()
    with pytest.raises(InvalidValueError):
        protocol.i2c_read(0x10, -1)


@pytest.mark.unit
def test_i2c_read_invalid_register_raises() -> None:
    protocol, _ = _connected()
    with pytest.raises(InvalidValueError):
        protocol.i2c_read(0x10, 1, register=0x100)


@pytest.mark.unit
def test_i2c_read_without_reply_raises() -> None:
    protocol, _ = _connected()
    with pytest.raises(BoardConnectionError):
        protocol.i2c_read(0x68, 2)


@pytest.mark.unit
def test_parser_ignores_empty_sysex() -> None:
    protocol, driver = _connected()
    driver.feed(bytes([START_SYSEX, END_SYSEX, DIGITAL_MESSAGE | 0, 0x04, 0x00]))
    assert protocol.digital_read(2) == 1


def _firmware_bytes(major: int, minor: int, name: str) -> bytes:
    """Encode an inbound REPORT_FIRMWARE sysex (name chars as 7-bit pairs)."""
    chars: list[int] = []
    for char in name:
        code = ord(char)
        chars += [code & 0x7F, (code >> 7) & 0x7F]
    return bytes([START_SYSEX, REPORT_FIRMWARE, major, minor, *chars, END_SYSEX])


@pytest.mark.unit
def test_report_firmware_parses_name_and_version() -> None:
    protocol, driver = _connected()
    driver.feed(_firmware_bytes(2, 5, "StandardFirmata"))
    assert protocol.report_firmware() == (2, 5, "StandardFirmata")
    assert bytes(driver.written) == bytes([START_SYSEX, REPORT_FIRMWARE, END_SYSEX])


@pytest.mark.unit
def test_report_firmware_without_reply_raises() -> None:
    protocol, _ = _connected()
    with pytest.raises(BoardConnectionError):
        protocol.report_firmware()


@pytest.mark.unit
def test_capability_query_parses_per_pin_modes() -> None:
    protocol, driver = _connected()
    # pin 0: INPUT/OUTPUT, pin 1: PWM. Each mode is followed by a resolution byte.
    driver.feed(
        bytes(
            [
                START_SYSEX, CAPABILITY_RESPONSE,
                0x00, 0x01, 0x01, 0x01, 0x7F,
                0x03, 0x08, 0x7F,
                END_SYSEX,
            ]
        )
    )
    assert protocol.capability_query() == {0: [0x00, 0x01], 1: [0x03]}
    assert bytes(driver.written) == bytes([START_SYSEX, CAPABILITY_QUERY, END_SYSEX])


@pytest.mark.unit
def test_analog_mapping_query_skips_non_analog_pins() -> None:
    protocol, driver = _connected()
    # pins 0,1 are not analog (0x7F); pin 2 -> channel 0, pin 3 -> channel 1.
    driver.feed(
        bytes([START_SYSEX, ANALOG_MAPPING_RESPONSE, 0x7F, 0x7F, 0x00, 0x01, END_SYSEX])
    )
    assert protocol.analog_mapping_query() == {2: 0, 3: 1}
    assert bytes(driver.written) == bytes([START_SYSEX, ANALOG_MAPPING_QUERY, END_SYSEX])


@pytest.mark.unit
def test_pin_state_query_parses_mode_and_value() -> None:
    protocol, driver = _connected()
    driver.feed(bytes([START_SYSEX, PIN_STATE_RESPONSE, 13, 0x01, 0x01, END_SYSEX]))
    assert protocol.pin_state_query(13) == (0x01, 1)
    assert bytes(driver.written) == bytes([START_SYSEX, PIN_STATE_QUERY, 13, END_SYSEX])


@pytest.mark.unit
def test_pin_state_query_combines_multibyte_value() -> None:
    protocol, driver = _connected()
    # value 200 = 0x48 | (0x01 << 7).
    driver.feed(bytes([START_SYSEX, PIN_STATE_RESPONSE, 9, 0x03, 0x48, 0x01, END_SYSEX]))
    assert protocol.pin_state_query(9) == (0x03, 200)


@pytest.mark.unit
def test_send_requires_connection() -> None:
    driver = FakeDriver()
    protocol = FirmataProtocol(driver)
    with pytest.raises(BoardConnectionError):
        protocol.pin_mode(13, OUTPUT)


@pytest.mark.unit
def test_parser_ignores_sysex_version_and_stray_bytes() -> None:
    protocol, driver = _connected()
    driver.feed(
        bytes(
            [
                0x00,  # stray data byte with no active command
                0xFF,  # unsupported command byte (resets parser)
                0xF9, 0x02, 0x05,  # REPORT_VERSION 2.5 (ignored)
                0xF0, 0x79, 0x41, 0xF7,  # sysex payload (ignored)
                DIGITAL_MESSAGE | 1, 0x01, 0x00,  # port 1, pin 8 high
            ]
        )
    )
    assert protocol.digital_read(8) == 1


@pytest.mark.unit
def test_unsupported_device_functions_raise() -> None:
    protocol, _ = _connected()
    with pytest.raises(UnsupportedOperationError):
        protocol.tone(8, 440, None)
    with pytest.raises(UnsupportedOperationError):
        protocol.no_tone(8)
    with pytest.raises(UnsupportedOperationError):
        protocol.pulse_in(8, 1, 1000)
    with pytest.raises(UnsupportedOperationError):
        protocol.shift_out(8, 9, 1, 0xFF)
    with pytest.raises(UnsupportedOperationError):
        protocol.shift_in(8, 9, 1)
