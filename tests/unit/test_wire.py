"""Unit tests for the Arduino Wire-style I2C layer.

Exercise the stateful ``Wire`` API (begin, beginTransmission/write/
endTransmission, requestFrom/available/read) over a mock protocol.
"""

from __future__ import annotations

import pytest

from liveduino.boards.board import Board
from liveduino.boards.catalog.arduino_uno import ArduinoUno
from liveduino.exceptions import LiveduinoError
from tests.shared.fake_driver import FakeDriver
from tests.shared.mock_protocol import MockProtocol


@pytest.fixture
def board() -> Board:
    protocol = MockProtocol()
    return ArduinoUno(protocol=lambda _driver: protocol).connect(driver=FakeDriver())


def _protocol(board: Board) -> MockProtocol:
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    return protocol


@pytest.mark.unit
def test_begin_enables_bus(board: Board) -> None:
    board.wire.begin()
    assert ("i2c_config", (0,)) in _protocol(board).calls


@pytest.mark.unit
def test_write_and_end_transmission(board: Board) -> None:
    board.wire.beginTransmission(0x68)
    board.wire.write(0x6B)
    board.wire.write([0x00, 0x01])
    assert board.wire.endTransmission() == 0
    assert ("i2c_write", (0x68, (0x6B, 0x00, 0x01))) in _protocol(board).calls


@pytest.mark.unit
def test_end_transmission_honours_stop_flag(board: Board) -> None:
    board.wire.beginTransmission(0x10)
    board.wire.write(0x01)
    assert board.wire.endTransmission(stop=False) == 0


@pytest.mark.unit
def test_end_transmission_without_begin_raises(board: Board) -> None:
    with pytest.raises(LiveduinoError):
        board.wire.endTransmission()


@pytest.mark.unit
def test_request_from_and_read(board: Board) -> None:
    _protocol(board).i2c_reply = bytes([0xDE, 0xAD])
    assert board.wire.requestFrom(0x68, 2) == 2
    assert board.wire.available() == 2
    assert board.wire.read() == 0xDE
    assert board.wire.read() == 0xAD
    assert board.wire.available() == 0
    assert board.wire.read() == -1


@pytest.mark.unit
def test_request_from_repeated_start(board: Board) -> None:
    _protocol(board).i2c_reply = bytes([0x01])
    board.wire.requestFrom(0x68, 1, stop=False)
    assert ("i2c_read", (0x68, 1, None, True)) in _protocol(board).calls


@pytest.mark.unit
def test_wire_is_cached(board: Board) -> None:
    assert board.wire is board.wire
