"""Unit tests for the STK500v1 programmer.

Drive the bootloader programmer against a fake serial port that scripts the
INSYNC/OK handshake, covering a successful flash, verification, and the error
paths (open failure, lost sync, rejected command, short read, bad verify).
"""

from collections import deque
from unittest.mock import MagicMock, patch

import pytest
import serial

from liveduino.exceptions import FlashError
from liveduino.programmers.stk500v1 import Stk500v1Programmer

_INSYNC = 0x14
_OK = 0x10


class FakeSerial:
    """Serial stand-in that returns scripted responses for each read call."""

    def __init__(self, responses: list[bytes]) -> None:
        self.responses: deque[bytes] = deque(responses)
        self.written = bytearray()
        self.dtr = False
        self.rts = False
        self.closed = False

    def reset_input_buffer(self) -> None:
        return None

    def write(self, data: bytes) -> None:
        self.written.extend(data)

    def read(self, size: int = 1) -> bytes:
        if not self.responses:
            return b""
        return self.responses.popleft()

    def close(self) -> None:
        self.closed = True


def _ok() -> list[bytes]:
    """Response pair for a plain command with no payload."""
    return [bytes([_INSYNC]), bytes([_OK])]


@pytest.mark.unit
@patch("liveduino.programmers.stk500v1.time.sleep")
@patch("liveduino.programmers.stk500v1.serial.Serial")
def test_flash_with_verify(mock_serial_cls: MagicMock, _sleep: MagicMock) -> None:
    responses = [
        bytes([_INSYNC, _OK]),  # sync
        *_ok(),  # enter progmode
        *_ok(),  # load address
        *_ok(),  # prog page
        *_ok(),  # verify load address
        bytes([_INSYNC]),  # read page insync
        bytes([1, 2, 3, 4]),  # read page payload
        bytes([_OK]),  # read page ok
        *_ok(),  # leave progmode
    ]
    fake = FakeSerial(responses)
    mock_serial_cls.return_value = fake
    programmer = Stk500v1Programmer("/dev/ttyACM0", baud=115200, page_size=4)
    programmer.flash(bytes([1, 2, 3, 4]))
    mock_serial_cls.assert_called_once_with("/dev/ttyACM0", 115200, timeout=1.0)
    assert fake.closed is True
    assert programmer.port == "/dev/ttyACM0"
    assert programmer.baud == 115200
    assert programmer.page_size == 4


@pytest.mark.unit
@patch("liveduino.programmers.stk500v1.time.sleep")
@patch("liveduino.programmers.stk500v1.serial.Serial")
def test_flash_without_verify_skips_readback(mock_serial_cls: MagicMock, _sleep: MagicMock) -> None:
    responses = [
        bytes([_INSYNC, _OK]),  # sync
        *_ok(),  # enter progmode
        *_ok(),  # load address
        *_ok(),  # prog page
        *_ok(),  # leave progmode
    ]
    fake = FakeSerial(responses)
    mock_serial_cls.return_value = fake
    programmer = Stk500v1Programmer("/dev/ttyACM0", page_size=4)
    programmer.flash(bytes([1, 2, 3, 4]), verify=False)
    assert fake.closed is True


@pytest.mark.unit
@patch(
    "liveduino.programmers.stk500v1.serial.Serial",
    side_effect=serial.SerialException("nope"),
)
def test_flash_open_failure(_mock_serial_cls: MagicMock) -> None:
    programmer = Stk500v1Programmer("/dev/ttyACM0")
    with pytest.raises(FlashError, match="Failed to open"):
        programmer.flash(b"")


@pytest.mark.unit
@patch("liveduino.programmers.stk500v1.time.sleep")
@patch("liveduino.programmers.stk500v1.serial.Serial")
def test_flash_sync_failure(mock_serial_cls: MagicMock, _sleep: MagicMock) -> None:
    fake = FakeSerial([bytes([0x00, 0x00])] * 5)
    mock_serial_cls.return_value = fake
    programmer = Stk500v1Programmer("/dev/ttyACM0")
    with pytest.raises(FlashError, match="synchronize"):
        programmer.flash(b"")
    assert fake.closed is True


@pytest.mark.unit
@patch("liveduino.programmers.stk500v1.time.sleep")
@patch("liveduino.programmers.stk500v1.serial.Serial")
def test_flash_lost_sync_on_command(mock_serial_cls: MagicMock, _sleep: MagicMock) -> None:
    responses = [
        bytes([_INSYNC, _OK]),  # sync
        bytes([0x00]),  # enter progmode: not INSYNC
    ]
    mock_serial_cls.return_value = FakeSerial(responses)
    programmer = Stk500v1Programmer("/dev/ttyACM0")
    with pytest.raises(FlashError, match="Lost sync"):
        programmer.flash(b"")


@pytest.mark.unit
@patch("liveduino.programmers.stk500v1.time.sleep")
@patch("liveduino.programmers.stk500v1.serial.Serial")
def test_flash_rejected_command(mock_serial_cls: MagicMock, _sleep: MagicMock) -> None:
    responses = [
        bytes([_INSYNC, _OK]),  # sync
        bytes([_INSYNC]),  # enter progmode insync
        bytes([0x00]),  # enter progmode: not OK
    ]
    mock_serial_cls.return_value = FakeSerial(responses)
    programmer = Stk500v1Programmer("/dev/ttyACM0")
    with pytest.raises(FlashError, match="rejected"):
        programmer.flash(b"")


@pytest.mark.unit
@patch("liveduino.programmers.stk500v1.time.sleep")
@patch("liveduino.programmers.stk500v1.serial.Serial")
def test_flash_short_read(mock_serial_cls: MagicMock, _sleep: MagicMock) -> None:
    responses = [
        bytes([_INSYNC, _OK]),  # sync
        b"",  # enter progmode: short read
    ]
    mock_serial_cls.return_value = FakeSerial(responses)
    programmer = Stk500v1Programmer("/dev/ttyACM0")
    with pytest.raises(FlashError, match="Timed out"):
        programmer.flash(b"")


@pytest.mark.unit
@patch("liveduino.programmers.stk500v1.time.sleep")
@patch("liveduino.programmers.stk500v1.serial.Serial")
def test_flash_verification_mismatch(mock_serial_cls: MagicMock, _sleep: MagicMock) -> None:
    responses = [
        bytes([_INSYNC, _OK]),  # sync
        *_ok(),  # enter progmode
        *_ok(),  # load address
        *_ok(),  # prog page
        *_ok(),  # verify load address
        bytes([_INSYNC]),  # read page insync
        bytes([9, 9, 9, 9]),  # read page payload (wrong)
        bytes([_OK]),  # read page ok
    ]
    mock_serial_cls.return_value = FakeSerial(responses)
    programmer = Stk500v1Programmer("/dev/ttyACM0", page_size=4)
    with pytest.raises(FlashError, match="Verification failed"):
        programmer.flash(bytes([1, 2, 3, 4]))
