"""Pure-Python STK500v1 bootloader programmer.

Flashes firmware to ATmega328-family boards (Arduino UNO, Nano, ...) by speaking
the STK500v1 protocol used by the Optiboot/Arduino serial bootloader directly
over pyserial. No avrdude or external toolchain is required.

The board is reset into its bootloader by toggling the DTR/RTS lines (the
auto-reset circuit on Arduino boards), then the firmware is written page by page
and optionally verified.
"""

from __future__ import annotations

import time

import serial

from liveduino.exceptions import FlashError

# STK500v1 response/command bytes (see the STK500 communication protocol).
_RESP_OK = 0x10
_RESP_INSYNC = 0x14
_SYNC_CRC_EOP = 0x20
_CMD_GET_SYNC = 0x30
_CMD_ENTER_PROGMODE = 0x50
_CMD_LEAVE_PROGMODE = 0x51
_CMD_LOAD_ADDRESS = 0x55
_CMD_PROG_PAGE = 0x64
_CMD_READ_PAGE = 0x74
_FLASH_MEMORY = ord("F")

_SYNC_ATTEMPTS = 5


class Stk500v1Programmer:
    """STK500v1 serial bootloader programmer for AVR Arduino boards.

    Opens the serial port, resets the board into its bootloader, and programs a
    flat firmware image in flash pages. Errors from pyserial or the bootloader
    are surfaced as ``FlashError``.
    """

    def __init__(
        self,
        port: str,
        *,
        baud: int = 115200,
        page_size: int = 128,
        timeout: float = 1.0,
    ) -> None:
        """Create a programmer for the given serial port and bootloader settings."""
        self._port = port
        self._baud = baud
        self._page_size = page_size
        self._timeout = timeout

    @property
    def port(self) -> str:
        """Return the configured serial port path."""
        return self._port

    @property
    def baud(self) -> int:
        """Return the configured bootloader baud rate."""
        return self._baud

    @property
    def page_size(self) -> int:
        """Return the flash page size in bytes."""
        return self._page_size

    def flash(self, firmware: bytes, *, verify: bool = True) -> None:
        """Reset the board into its bootloader and write the firmware image to flash."""
        try:
            port = serial.Serial(self._port, self._baud, timeout=self._timeout)
        except serial.SerialException as exc:
            raise FlashError(f"Failed to open serial port {self._port!r}") from exc
        try:
            self._reset(port)
            self._sync(port)
            self._command(port, bytes([_CMD_ENTER_PROGMODE]))
            self._write_pages(port, firmware)
            if verify:
                self._verify_pages(port, firmware)
            self._command(port, bytes([_CMD_LEAVE_PROGMODE]))
        finally:
            port.close()

    def _reset(self, port: serial.Serial) -> None:
        """Pulse DTR/RTS to drive the auto-reset line and enter the bootloader."""
        port.dtr = True
        port.rts = True
        time.sleep(0.1)
        port.dtr = False
        port.rts = False
        time.sleep(0.1)
        port.reset_input_buffer()

    def _sync(self, port: serial.Serial) -> None:
        """Send GET_SYNC until the bootloader answers, or fail after a few tries."""
        for _ in range(_SYNC_ATTEMPTS):
            port.reset_input_buffer()
            port.write(bytes([_CMD_GET_SYNC, _SYNC_CRC_EOP]))
            if port.read(2) == bytes([_RESP_INSYNC, _RESP_OK]):
                return
            time.sleep(0.05)
        raise FlashError("Could not synchronize with the bootloader; is the board in reset?")

    def _write_pages(self, port: serial.Serial, firmware: bytes) -> None:
        """Program the firmware image one flash page at a time."""
        for offset in range(0, len(firmware), self._page_size):
            chunk = firmware[offset : offset + self._page_size]
            self._load_address(port, offset // 2)
            header = bytes(
                [_CMD_PROG_PAGE, (len(chunk) >> 8) & 0xFF, len(chunk) & 0xFF, _FLASH_MEMORY]
            )
            self._command(port, header + chunk)

    def _verify_pages(self, port: serial.Serial, firmware: bytes) -> None:
        """Read back each flash page and compare it with the written image."""
        for offset in range(0, len(firmware), self._page_size):
            chunk = firmware[offset : offset + self._page_size]
            self._load_address(port, offset // 2)
            header = bytes(
                [_CMD_READ_PAGE, (len(chunk) >> 8) & 0xFF, len(chunk) & 0xFF, _FLASH_MEMORY]
            )
            read_back = self._command(port, header, response_len=len(chunk))
            if read_back != chunk:
                raise FlashError(f"Verification failed at byte {offset}")

    def _load_address(self, port: serial.Serial, word_address: int) -> None:
        """Set the bootloader's word address pointer for the next page operation."""
        body = bytes([_CMD_LOAD_ADDRESS, word_address & 0xFF, (word_address >> 8) & 0xFF])
        self._command(port, body)

    def _command(self, port: serial.Serial, body: bytes, *, response_len: int = 0) -> bytes:
        """Send a command framed with CRC_EOP and check the INSYNC/OK response."""
        port.write(body + bytes([_SYNC_CRC_EOP]))
        if self._read_exact(port, 1)[0] != _RESP_INSYNC:
            raise FlashError("Lost sync with the bootloader")
        payload = self._read_exact(port, response_len) if response_len else b""
        if self._read_exact(port, 1)[0] != _RESP_OK:
            raise FlashError("Bootloader rejected a command")
        return payload

    def _read_exact(self, port: serial.Serial, size: int) -> bytes:
        """Read exactly size bytes from the port, failing on a short read."""
        data = port.read(size)
        if len(data) != size:
            raise FlashError("Timed out reading from the bootloader")
        return bytes(data)
