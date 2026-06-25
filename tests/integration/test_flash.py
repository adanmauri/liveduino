"""Opt-in integration test for the STK500v1 flashing pipeline.

Flashes the bundled StandardFirmata image to a real ATmega328 board over the
serial port given by ``LIVEDUINO_FLASH_PORT`` (board id from
``LIVEDUINO_FLASH_BOARD``, default ``arduino:uno``), then opens a Firmata
connection to confirm the freshly flashed firmware responds. Skipped when
``LIVEDUINO_FLASH_PORT`` is unset.

This is a destructive test: it overwrites the firmware on the connected board.
It uses a dedicated environment variable (not ``LIVEDUINO_PORT``) so the runtime
integration tests never reflash the board by accident.
"""

import os
import time

import pytest

from liveduino import HIGH, LOW, OUTPUT
from liveduino.boards.registry import get_board
from liveduino.programmers import Stk500v1Programmer, load_bundled_firmware, parse_intel_hex


@pytest.mark.integration
def test_flash_bundled_firmware_and_connect() -> None:
    port = os.environ.get("LIVEDUINO_FLASH_PORT")
    if not port:
        pytest.skip("LIVEDUINO_FLASH_PORT is not set")
    board_id = os.environ.get("LIVEDUINO_FLASH_BOARD", "arduino:uno")
    board_cls = get_board(board_id)

    firmware = parse_intel_hex(load_bundled_firmware(board_id))
    programmer = Stk500v1Programmer(
        port, baud=board_cls.flash_baud, page_size=board_cls.flash_page_size
    )
    programmer.flash(firmware, verify=True)

    # Let the board leave the bootloader and start StandardFirmata.
    time.sleep(2.0)

    board = board_cls().connect(port)
    try:
        board.pinMode(13, OUTPUT)
        board.digitalWrite(13, HIGH)
        board.digitalWrite(13, LOW)
        assert 0 <= board.analogRead(0) <= 1023
    finally:
        board.close()
