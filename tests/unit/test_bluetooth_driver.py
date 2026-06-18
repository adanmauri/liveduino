"""Unit tests for BluetoothDriver."""

from unittest.mock import MagicMock, patch

import pytest

from liveduino.drivers.bluetooth import BluetoothDriver
from liveduino.exceptions import BoardConnectionError

_ADDRESS = "AA:BB:CC:DD:EE:FF"


@pytest.mark.unit
@patch("liveduino.drivers.bluetooth.socket")
def test_bluetooth_open_read_write(mock_socket: MagicMock) -> None:
    sock = MagicMock()
    mock_socket.socket.return_value = sock
    sock.recv.side_effect = [b"\xe0\x10\x00", BlockingIOError()]
    driver = BluetoothDriver(_ADDRESS, channel=1)
    driver.open()
    mock_socket.socket.assert_called_once_with(
        mock_socket.AF_BLUETOOTH, mock_socket.SOCK_STREAM, mock_socket.BTPROTO_RFCOMM
    )
    sock.connect.assert_called_once_with((_ADDRESS, 1))
    sock.setblocking.assert_called_once_with(False)
    driver.write(b"\x01")
    sock.sendall.assert_called_once_with(b"\x01")
    assert driver.in_waiting == 3
    assert driver.read(3) == b"\xe0\x10\x00"
    assert driver.address == _ADDRESS
    assert driver.channel == 1


@pytest.mark.unit
@patch("liveduino.drivers.bluetooth.socket")
def test_bluetooth_open_with_timeout(mock_socket: MagicMock) -> None:
    sock = MagicMock()
    mock_socket.socket.return_value = sock
    driver = BluetoothDriver(_ADDRESS, timeout=5.0)
    driver.open()
    sock.settimeout.assert_called_once_with(5.0)


@pytest.mark.unit
@patch("liveduino.drivers.bluetooth.socket")
def test_bluetooth_unsupported_platform(mock_socket: MagicMock) -> None:
    del mock_socket.AF_BLUETOOTH
    driver = BluetoothDriver(_ADDRESS)
    with pytest.raises(BoardConnectionError):
        driver.open()


@pytest.mark.unit
@patch("liveduino.drivers.bluetooth.socket")
def test_bluetooth_connect_failure(mock_socket: MagicMock) -> None:
    sock = MagicMock()
    mock_socket.socket.return_value = sock
    sock.connect.side_effect = OSError("no route to host")
    driver = BluetoothDriver(_ADDRESS)
    with pytest.raises(BoardConnectionError):
        driver.open()
