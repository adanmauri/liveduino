"""Unit tests for package exports and ArduinoUno.connect.

Verify the public ``liveduino`` namespace (constants, helpers, and drivers) and
that ``ArduinoUno.connect`` wires up the serial driver and protocol correctly.
"""

from unittest.mock import MagicMock, patch

import pytest

import liveduino
from liveduino import ArduinoUno, connect
from liveduino.boards.board import Board
from liveduino.drivers.serial import SerialDriver


@pytest.mark.unit
def test_package_exports() -> None:
    assert liveduino.HIGH == 1
    assert liveduino.LOW == 0
    assert liveduino.INPUT == 0
    assert liveduino.OUTPUT == 1
    assert liveduino.INPUT_PULLUP == 2
    assert callable(liveduino.map_range)
    assert callable(liveduino.connect)
    assert liveduino.SerialDriver is SerialDriver


@pytest.mark.unit
def test_analog_pin_constants_exported() -> None:
    assert liveduino.A0.channel == 0
    assert liveduino.A5.channel == 5
    assert liveduino.A7.channel == 7


@pytest.mark.unit
@patch.object(ArduinoUno, "protocol_factory")
def test_arduino_uno_connect(mock_factory: MagicMock) -> None:
    mock_protocol = MagicMock()
    mock_factory.return_value = mock_protocol
    board = ArduinoUno().connect("/dev/ttyACM0")
    assert isinstance(board, Board)
    assert type(board) is ArduinoUno
    driver = mock_factory.call_args.args[0]
    assert isinstance(driver, SerialDriver)
    assert driver.port == "/dev/ttyACM0"
    assert driver.baud == 57600
    mock_protocol.connect.assert_called_once()


@pytest.mark.unit
@patch.object(ArduinoUno, "protocol_factory")
def test_connect_factory(mock_factory: MagicMock) -> None:
    mock_protocol = MagicMock()
    mock_factory.return_value = mock_protocol
    board = connect("arduino:uno", "/dev/ttyACM0", baud=115200)
    assert isinstance(board, Board)
    driver = mock_factory.call_args.args[0]
    assert isinstance(driver, SerialDriver)
    assert driver.baud == 115200
