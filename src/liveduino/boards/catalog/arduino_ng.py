"""Arduino NG or older board."""

from liveduino.boards.board import Board


class ArduinoNG(Board):
    """Arduino NG or older (ATmega168) running StandardFirmata over serial."""
    id = "arduino:atmegang"
    name = "Arduino NG or older"
    digital_pins = range(14)
    analog_pins = range(6)
    pwm_pins = frozenset({3, 5, 6, 9, 10, 11})
    default_baud = 57600
