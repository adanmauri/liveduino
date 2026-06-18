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
    ANALOG_MESSAGE,
    DIGITAL_MESSAGE,
    REPORT_ANALOG,
    REPORT_DIGITAL,
    SET_DIGITAL_PIN_VALUE,
    SET_PIN_MODE,
    FirmataProtocol,
)
from tests.shared.fake_driver import FakeDriver


def _connected() -> tuple[FirmataProtocol, FakeDriver]:
    driver = FakeDriver()
    protocol = FirmataProtocol(driver)
    protocol.connect()
    return protocol, driver


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
