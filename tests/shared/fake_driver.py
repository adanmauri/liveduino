"""In-memory Driver stand-in for unit tests."""

from __future__ import annotations


class FakeDriver:
    """Driver backed by in-memory buffers for write capture and read injection."""
    def __init__(self) -> None:
        self.opened = False
        self.written = bytearray()
        self._rx = bytearray()

    def feed(self, data: bytes) -> None:
        """Queue bytes to be returned by subsequent reads."""
        self._rx.extend(data)

    def open(self) -> None:
        self.opened = True

    def close(self) -> None:
        self.opened = False

    def write(self, data: bytes) -> None:
        self.written.extend(data)

    def read(self, size: int = 1) -> bytes:
        chunk = bytes(self._rx[:size])
        del self._rx[:size]
        return chunk

    @property
    def in_waiting(self) -> int:
        return len(self._rx)
