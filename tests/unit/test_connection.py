"""Unit tests for connection helpers.

Exercise the ``connect`` entry point and the board ``connect`` method, covering
board lookup, driver selection, and the mutually exclusive port/driver options.
"""

from unittest.mock import MagicMock, patch

import pytest

from liveduino.boards.board import Board
from liveduino.boards.catalog.arduino_uno import ArduinoUno
from liveduino.connection import connect
from liveduino.drivers.serial import SerialDriver
from liveduino.exceptions import LiveduinoError
from tests.shared.fake_driver import FakeDriver
from tests.shared.mock_protocol import MockProtocol


@pytest.mark.unit
@patch.object(ArduinoUno, "protocol_factory")
def test_connect_uses_firmata(mock_factory: MagicMock) -> None:
    mock_protocol = MockProtocol()
    mock_factory.return_value = mock_protocol
    board = connect("arduino:uno", "/dev/ttyACM0")
    assert isinstance(board, Board)
    assert isinstance(board, ArduinoUno)
    driver = mock_factory.call_args.args[0]
    assert isinstance(driver, SerialDriver)
    assert driver.port == "/dev/ttyACM0"
    assert driver.baud == 57600
    assert mock_protocol.connected is True


@pytest.mark.unit
def test_connect_unknown_board_raises() -> None:
    with pytest.raises(LiveduinoError):
        connect("missing:board", "/dev/ttyACM0")


@pytest.mark.unit
def test_connect_with_explicit_driver() -> None:
    driver = FakeDriver()
    board = ArduinoUno().connect(driver=driver)
    assert isinstance(board, ArduinoUno)
    assert driver.opened is True
    board.pinMode(13, 1)
    assert bytes(driver.written) == bytes([0xF4, 13, 0x01])


@pytest.mark.unit
def test_connect_without_port_or_driver_raises() -> None:
    with pytest.raises(LiveduinoError):
        ArduinoUno().connect()


@pytest.mark.unit
def test_connect_with_port_and_driver_raises() -> None:
    with pytest.raises(LiveduinoError):
        ArduinoUno().connect("/dev/ttyACM0", driver=FakeDriver())


@pytest.mark.unit
def test_connect_with_baud_and_driver_raises() -> None:
    with pytest.raises(LiveduinoError):
        ArduinoUno().connect(baud=115200, driver=FakeDriver())
