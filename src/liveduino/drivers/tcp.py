"""TCP socket driver (Firmata over WiFi/Ethernet)."""

from __future__ import annotations

import socket

from liveduino.drivers.socket_driver import SocketDriver


class TcpDriver(SocketDriver):
    """Firmata driver over a TCP socket (StandardFirmataWiFi/Ethernet)."""
    def __init__(self, host: str, port: int = 3030, *, timeout: float | None = None) -> None:
        super().__init__()
        self._host = host
        self._port = port
        self._timeout = timeout

    @property
    def host(self) -> str:
        """Return the configured TCP host."""
        return self._host

    @property
    def port(self) -> int:
        """Return the configured TCP port."""
        return self._port

    def _open_socket(self) -> socket.socket:
        return socket.create_connection((self._host, self._port), timeout=self._timeout)

    def _describe(self) -> str:
        return f"TCP {self._host}:{self._port}"
