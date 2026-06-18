"""Driver abstractions: byte channels from the host to the board.

Defines the ``Driver`` protocol that every transport implements (serial, TCP,
Bluetooth). Drivers move raw bytes between the host and the board and know
nothing about the higher-level protocol framing.
"""

from typing import Protocol


class Driver(Protocol):
    """Byte channel to the microcontroller (serial, Bluetooth, WiFi, etc.).

    Structural protocol implemented by every transport. It exposes a minimal
    open/close/read/write interface plus ``in_waiting`` so protocol clients can
    exchange bytes without depending on a concrete transport.
    """
    def open(self) -> None:
        """Open the channel."""
        ...

    def close(self) -> None:
        """Close the channel."""
        ...

    def write(self, data: bytes) -> None:
        """Write raw bytes to the board."""
        ...

    def read(self, size: int = 1) -> bytes:
        """Read up to size bytes from the board."""
        ...

    @property
    def in_waiting(self) -> int:
        """Return the number of bytes available to read."""
        ...
