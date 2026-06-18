"""Driver abstractions: byte channels from the host to the board."""

from typing import Protocol


class Driver(Protocol):
    """Byte channel to the microcontroller (serial, Bluetooth, WiFi, etc.)."""
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
