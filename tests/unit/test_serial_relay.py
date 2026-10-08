"""Unit tests for the Arduino-style serial-relay port."""

from __future__ import annotations

import pytest

from liveduino.boards.board import Board
from tests.shared.boards import connected_uno, mock_protocol_of


@pytest.fixture
def board() -> Board:
    return connected_uno()


@pytest.mark.unit
def test_begin_and_write(board: Board) -> None:
    port = board.serial(1)
    port.begin(9600)
    port.write(0x41)
    port.write([0x42, 0x43])
    calls = mock_protocol_of(board).calls
    assert ("serial_config", (1, 9600, None, None)) in calls
    assert ("serial_write", (1, (0x41,))) in calls
    assert ("serial_write", (1, (0x42, 0x43))) in calls


@pytest.mark.unit
def test_begin_with_software_serial_pins(board: Board) -> None:
    board.serial(8).begin(4800, rx=10, tx=11)
    assert ("serial_config", (8, 4800, 10, 11)) in mock_protocol_of(board).calls


@pytest.mark.unit
def test_available_and_read(board: Board) -> None:
    mock_protocol_of(board).serial_reply = bytes([0x48, 0x49])
    port = board.serial(1)
    assert port.available() == 2
    assert port.read() == 0x48
    assert port.read() == 0x49
    assert port.read() == -1


@pytest.mark.unit
def test_end_closes_port(board: Board) -> None:
    board.serial(1).end()
    assert ("serial_close", (1,)) in mock_protocol_of(board).calls


@pytest.mark.unit
def test_serial_port_is_cached(board: Board) -> None:
    assert board.serial(1) is board.serial(1)
