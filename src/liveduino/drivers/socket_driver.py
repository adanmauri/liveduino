"""Socket-based driver base class."""

from __future__ import annotations

import socket

from liveduino.exceptions import BoardConnectionError

_READ_CHUNK = 1024


class SocketDriver:
    """Base driver over a stream socket with buffered non-blocking reads."""
    def __init__(self) -> None:
        self._socket: socket.socket | None = None
        self._buffer = bytearray()

    def open(self) -> None:
        """Open and connect the underlying socket."""
        if self._socket is not None:
            return
        try:
            sock = self._open_socket()
        except OSError as exc:
            raise BoardConnectionError(f"Failed to open {self._describe()}") from exc
        sock.setblocking(False)
        self._socket = sock

    def close(self) -> None:
        """Close the socket connection."""
        if self._socket is not None:
            self._socket.close()
        self._socket = None
        self._buffer.clear()

    def write(self, data: bytes) -> None:
        """Send bytes over the socket."""
        self._require_socket().sendall(data)

    def read(self, size: int = 1) -> bytes:
        """Read up to size buffered bytes, refilling from the socket first."""
        self._fill(self._require_socket())
        data = bytes(self._buffer[:size])
        del self._buffer[:size]
        return data

    @property
    def in_waiting(self) -> int:
        """Return the number of buffered bytes available to read."""
        if self._socket is None:
            return 0
        self._fill(self._socket)
        return len(self._buffer)

    def _fill(self, sock: socket.socket) -> None:
        try:
            chunk = sock.recv(_READ_CHUNK)
        except BlockingIOError:
            return
        if chunk:
            self._buffer.extend(chunk)

    def _require_socket(self) -> socket.socket:
        if self._socket is None:
            raise BoardConnectionError(f"{self._describe()} is not open")
        return self._socket

    def _open_socket(self) -> socket.socket:
        """Create and connect the socket (implemented by subclasses)."""
        raise NotImplementedError

    def _describe(self) -> str:
        """Return a human-readable description of the endpoint."""
        raise NotImplementedError
