"""Unit tests for SerialDriver.

Exercise the pyserial-backed driver with a mocked serial port, covering open,
close, read, write, error handling, and idempotent reopen.
"""

from unittest.mock import MagicMock, patch

import pytest
import serial

from liveduino.drivers.serial import SerialDriver
from liveduino.exceptions import BoardConnectionError


@pytest.mark.unit
@patch("liveduino.drivers.serial.serial.Serial")
def test_serial_driver_open_and_close(mock_serial_cls: MagicMock) -> None:
    mock_port = MagicMock()
    mock_port.is_open = True
    mock_serial_cls.return_value = mock_port
    driver = SerialDriver("/dev/ttyACM0", baud=57600)
    driver.open()
    mock_serial_cls.assert_called_once_with("/dev/ttyACM0", 57600, timeout=None)
    driver.close()
    mock_port.close.assert_called_once()


@pytest.mark.unit
@patch("liveduino.drivers.serial.serial.Serial", side_effect=serial.SerialException("fail"))
def test_serial_driver_open_failure(mock_serial_cls: MagicMock) -> None:
    driver = SerialDriver("/dev/ttyACM0")
    with pytest.raises(BoardConnectionError):
        driver.open()


@pytest.mark.unit
@patch("liveduino.drivers.serial.serial.Serial")
def test_serial_driver_read_write(mock_serial_cls: MagicMock) -> None:
    mock_port = MagicMock()
    mock_port.is_open = True
    mock_port.read.return_value = b"\x01"
    mock_port.in_waiting = 3
    mock_serial_cls.return_value = mock_port
    driver = SerialDriver("/dev/ttyACM0")
    driver.open()
    driver.write(b"\xff")
    mock_port.write.assert_called_once_with(b"\xff")
    assert driver.read(1) == b"\x01"
    assert driver.in_waiting == 3
    assert driver.port == "/dev/ttyACM0"
    assert driver.baud == 57600


@pytest.mark.unit
def test_serial_driver_requires_open_port_for_io() -> None:
    driver = SerialDriver("/dev/ttyACM0")
    with pytest.raises(BoardConnectionError):
        driver.write(b"\x00")
    with pytest.raises(BoardConnectionError):
        driver.read()
    assert driver.in_waiting == 0


@pytest.mark.unit
@patch("liveduino.drivers.serial.serial.Serial")
def test_serial_driver_reopen_is_idempotent(mock_serial_cls: MagicMock) -> None:
    mock_port = MagicMock()
    mock_port.is_open = True
    mock_serial_cls.return_value = mock_port
    driver = SerialDriver("/dev/ttyACM0")
    driver.open()
    driver.open()
    mock_serial_cls.assert_called_once()
