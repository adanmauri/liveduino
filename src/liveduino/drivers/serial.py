"""Serial byte channel driver."""

from __future__ import annotations

import serial

from liveduino.drivers.base import Driver
from liveduino.exceptions import BoardConnectionError


class SerialDriver(Driver):
    """USB/serial driver backed by pyserial."""
    def __init__(self, port: str, *, baud: int = 57600, timeout: float | None = None) -> None:
        self._port = port
        self._baud = baud
        self._timeout = timeout
        self._serial: serial.Serial | None = None

    @property
    def port(self) -> str:
        """Return the configured serial port path."""
        return self._port

    @property
    def baud(self) -> int:
        """Return the configured baud rate."""
        return self._baud

    def open(self) -> None:
        """Open the serial port."""
        if self._serial is not None and self._serial.is_open:
            return
        try:
            self._serial = serial.Serial(self._port, self._baud, timeout=self._timeout)
        except serial.SerialException as exc:
            raise BoardConnectionError(f"Failed to open serial port {self._port!r}") from exc

    def close(self) -> None:
        """Close the serial port."""
        if self._serial is not None and self._serial.is_open:
            self._serial.close()
        self._serial = None

    def write(self, data: bytes) -> None:
        """Write bytes to the serial port."""
        if self._serial is None or not self._serial.is_open:
            raise BoardConnectionError("Serial port is not open")
        self._serial.write(data)

    def read(self, size: int = 1) -> bytes:
        """Read up to size bytes from the serial port."""
        if self._serial is None or not self._serial.is_open:
            raise BoardConnectionError("Serial port is not open")
        data = self._serial.read(size)
        return bytes(data)

    @property
    def in_waiting(self) -> int:
        """Return the number of bytes waiting in the input buffer."""
        if self._serial is None or not self._serial.is_open:
            return 0
        return int(self._serial.in_waiting)
