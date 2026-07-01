"""Arduino ``Wire`` (I2C) API over Firmata.

Mirrors the Arduino ``Wire`` library — ``begin``, ``beginTransmission`` /
``write`` / ``endTransmission``, and ``requestFrom`` / ``available`` / ``read``
(including the register overload ``requestFrom(addr, n, register)``) — so an
Arduino sketch ports almost verbatim. Reach it through ``board.wire``.

Continuous reads (``readContinuous`` / ``value`` / ``stopReading``) are a Firmata
extension with no Arduino ``Wire`` equivalent: the board keeps reporting a
register on its own and the host polls the latest value.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from liveduino.exceptions import LiveduinoError

if TYPE_CHECKING:
    from collections.abc import Iterable

    from liveduino.protocols.base import ProtocolClient


class Wire:
    """Arduino ``Wire``-style I2C master over a protocol client."""

    def __init__(self, client: ProtocolClient) -> None:
        self._client = client
        self._tx_address: int | None = None
        self._tx_buffer = bytearray()
        self._rx_buffer = b""
        self._rx_index = 0

    def begin(self) -> None:
        """Enable the I2C bus, like ``Wire.begin()``."""
        self._client.i2c_config()

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
        self._client.i2c_write(self._tx_address, bytes(self._tx_buffer))
        self._tx_address = None
        self._tx_buffer = bytearray()
        return 0

    def requestFrom(
        self, address: int, quantity: int, register: int | None = None, sendStop: bool = True
    ) -> int:
        """Read ``quantity`` bytes from a device; returns how many were received.

        Pass ``register`` to read from a register in one transaction (Arduino's
        ``requestFrom(address, quantity, iaddress, ...)`` overload).
        """
        self._rx_buffer = self._client.i2c_read(address, quantity, register, restart=not sendStop)
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

    def readContinuous(self, address: int, quantity: int, register: int | None = None) -> None:
        """Firmata extension: ask the device to keep reporting until stopped."""
        self._client.i2c_read_continuous(address, quantity, register)

    def value(self, address: int, register: int | None = None) -> bytes | None:
        """Firmata extension: latest continuously-reported reply, or None."""
        return self._client.i2c_value(address, register)

    def stopReading(self, address: int) -> None:
        """Firmata extension: stop a continuous read for a device."""
        self._client.i2c_stop_reading(address)
