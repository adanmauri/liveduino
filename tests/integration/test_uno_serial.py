"""Opt-in integration tests requiring a connected Arduino UNO."""

import os

import pytest

from liveduino import HIGH, LOW, OUTPUT, ArduinoUno


@pytest.mark.integration
def test_blink_and_analog_read() -> None:
    port = os.environ.get("LIVEDUINO_PORT")
    if not port:
        pytest.skip("LIVEDUINO_PORT is not set")
    board = ArduinoUno().connect(port)
    try:
        board.pinMode(13, OUTPUT)
        board.digitalWrite(13, HIGH)
        board.digitalWrite(13, LOW)
        value = board.analogRead(0)
        assert 0 <= value <= 1023
    finally:
        board.close()
