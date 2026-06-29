"""Arduino ``Wire`` (I2C) compatibility layer.

Mirrors the Arduino ``Wire`` library's stateful API (``begin``,
``beginTransmission`` / ``write`` / ``endTransmission``, and ``requestFrom`` /
``available`` / ``read``) on top of liveduino's batched I2C calls, so an Arduino
sketch translates line for line. Reach it through ``board.wire``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from liveduino.exceptions import LiveduinoError

if TYPE_CHECKING:
    from collections.abc import Iterable

    from liveduino.boards.board import Board


class Wire:
    """Arduino ``Wire``-style I2C interface bound to a board.

    Buffers a transmission across ``beginTransmission`` / ``write`` /
    ``endTransmission`` and a reply across ``requestFrom`` / ``available`` /
    ``read``, delegating the actual transfers to the board's I2C methods.
    """

    def __init__(self, board: Board) -> None:
        self._board = board
        self._tx_address: int | None = None
        self._tx_buffer = bytearray()
        self._rx_buffer: bytes = b""
        self._rx_index = 0

    def begin(self) -> None:
        """Enable the I2C bus, like ``Wire.begin()``."""
        self._board.i2cConfig()

    def beginTransmission(self, address: int) -> None:
        """Start queueing a write to a 7-bit address."""
        self._tx_address = address
        self._tx_buffer = bytearray()

    def write(self, data: int | Iterable[int]) -> None:
        """Queue one byte, or a sequence of bytes, for the pending transmission."""
        if isinstance(data, int):
            self._tx_buffer.append(data)
        else:
            self._tx_buffer.extend(data)

    def endTransmission(self, stop: bool = True) -> int:
        """Send the queued bytes and return 0 (success), like Arduino.

        ``stop`` is accepted for API compatibility, but StandardFirmata always
        ends a write with a stop condition, so the flag has no effect here.
        """
        _ = stop
        if self._tx_address is None:
            raise LiveduinoError("endTransmission called without beginTransmission")
        self._board.i2cWrite(self._tx_address, bytes(self._tx_buffer))
        self._tx_address = None
        self._tx_buffer = bytearray()
        return 0

    def requestFrom(self, address: int, count: int, stop: bool = True) -> int:
        """Read ``count`` bytes from a device; returns how many were received."""
        self._rx_buffer = self._board.i2cRead(address, count, restart=not stop)
        self._rx_index = 0
        return len(self._rx_buffer)

    def available(self) -> int:
        """Number of bytes still unread from the last ``requestFrom``."""
        return len(self._rx_buffer) - self._rx_index

    def read(self) -> int:
        """Return the next received byte, or -1 if none remain."""
        if self._rx_index >= len(self._rx_buffer):
            return -1
        value = self._rx_buffer[self._rx_index]
        self._rx_index += 1
        return value
