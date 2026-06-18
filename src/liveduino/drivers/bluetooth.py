"""Bluetooth RFCOMM driver.

Driver implementation that carries Firmata bytes over a Bluetooth RFCOMM serial
link, used with modules such as HC-05/HC-06 on platforms that expose RFCOMM
sockets.
"""

from __future__ import annotations

import socket

from liveduino.drivers.socket_driver import SocketDriver
from liveduino.exceptions import BoardConnectionError


class BluetoothDriver(SocketDriver):
    """Firmata driver over Bluetooth RFCOMM (e.g. HC-05/HC-06 modules).

    Uses the standard library's ``AF_BLUETOOTH`` RFCOMM sockets, available on
    Linux. No third-party Bluetooth dependency is required.
    """
    def __init__(self, address: str, channel: int = 1, *, timeout: float | None = None) -> None:
        super().__init__()
        self._address = address
        self._channel = channel
        self._timeout = timeout

    @property
    def address(self) -> str:
        """Return the configured Bluetooth device address."""
        return self._address

    @property
    def channel(self) -> int:
        """Return the configured RFCOMM channel."""
        return self._channel

    def _open_socket(self) -> socket.socket:
        family = getattr(socket, "AF_BLUETOOTH", None)
        proto = getattr(socket, "BTPROTO_RFCOMM", None)
        if family is None or proto is None:
            raise BoardConnectionError("Bluetooth RFCOMM is not available on this platform")
        sock = socket.socket(family, socket.SOCK_STREAM, proto)
        if self._timeout is not None:
            sock.settimeout(self._timeout)
        sock.connect((self._address, self._channel))
        return sock

    def _describe(self) -> str:
        return f"Bluetooth {self._address} channel {self._channel}"
