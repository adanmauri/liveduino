"""Serial-relay port over Firmata's SERIAL_MESSAGE.

Turns the board into a bridge to a UART device wired to one of its extra serial
ports (hardware ``Serial1``/``Serial2``/``Serial3`` or a software-serial port),
mirroring the Arduino ``HardwareSerial`` API (``begin`` / ``write`` /
``available`` / ``read`` / ``end``). Reach it through ``board.serial(port)``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from liveduino.protocols.base import ProtocolClient


class SerialRelay:
    """A serial port on the board, driven from the host like an Arduino ``Serial``."""

    def __init__(self, client: ProtocolClient, port: int) -> None:
        self._client = client
        self._port = port
        self._buffer = b""

    def begin(self, baud: int, rx: int | None = None, tx: int | None = None) -> None:
        """Open the port at a baud rate (rx/tx pins are for software serial)."""
        self._client.serial_config(self._port, baud, rx, tx)

    def write(self, data: int | Iterable[int]) -> None:
        """Send one byte or a sequence of bytes out of the port."""
        self._client.serial_write(self._port, [data] if isinstance(data, int) else data)

    def available(self) -> int:
        """Number of bytes received on the port and waiting to be read."""
        self._buffer += self._client.serial_value(self._port)
        return len(self._buffer)

    def read(self) -> int:
        """Return the next received byte, or -1 if none are available."""
        self._buffer += self._client.serial_value(self._port)
        if not self._buffer:
            return -1
        value, self._buffer = self._buffer[0], self._buffer[1:]
        return value

    def end(self) -> None:
        """Close the port on the board."""
        self._client.serial_close(self._port)
