"""Unit tests for TcpDriver.

Exercise the TCP socket driver with a mocked socket, covering open, close,
buffered reads and writes, error handling, and idempotent reopen.
"""

from unittest.mock import MagicMock, patch

import pytest

from liveduino.drivers.tcp import TcpDriver
from liveduino.exceptions import BoardConnectionError


@pytest.mark.unit
@patch("liveduino.drivers.tcp.socket")
def test_tcp_open_read_write(mock_socket: MagicMock) -> None:
    sock = MagicMock()
    mock_socket.create_connection.return_value = sock
    sock.recv.side_effect = [b"\x90\x04", BlockingIOError()]
    driver = TcpDriver("192.168.0.5", 3030, timeout=2.0)
    driver.open()
    mock_socket.create_connection.assert_called_once_with(("192.168.0.5", 3030), timeout=2.0)
    sock.setblocking.assert_called_once_with(False)
    driver.write(b"\xff")
    sock.sendall.assert_called_once_with(b"\xff")
    assert driver.in_waiting == 2
    assert driver.read(2) == b"\x90\x04"
    assert driver.host == "192.168.0.5"
    assert driver.port == 3030


@pytest.mark.unit
@patch("liveduino.drivers.tcp.socket")
def test_tcp_open_failure(mock_socket: MagicMock) -> None:
    mock_socket.create_connection.side_effect = OSError("unreachable")
    driver = TcpDriver("192.168.0.5", 3030)
    with pytest.raises(BoardConnectionError):
        driver.open()


@pytest.mark.unit
@patch("liveduino.drivers.tcp.socket")
def test_tcp_reopen_is_idempotent(mock_socket: MagicMock) -> None:
    mock_socket.create_connection.return_value = MagicMock()
    driver = TcpDriver("192.168.0.5", 3030)
    driver.open()
    driver.open()
    mock_socket.create_connection.assert_called_once()


@pytest.mark.unit
@patch("liveduino.drivers.tcp.socket")
def test_tcp_close(mock_socket: MagicMock) -> None:
    sock = MagicMock()
    mock_socket.create_connection.return_value = sock
    driver = TcpDriver("192.168.0.5", 3030)
    driver.open()
    driver.close()
    sock.close.assert_called_once()
    assert driver.in_waiting == 0


@pytest.mark.unit
def test_tcp_requires_open_for_io() -> None:
    driver = TcpDriver("192.168.0.5", 3030)
    with pytest.raises(BoardConnectionError):
        driver.write(b"\x00")
    with pytest.raises(BoardConnectionError):
        driver.read()
    assert driver.in_waiting == 0
