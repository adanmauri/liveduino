"""Arduino Nano board."""

from liveduino.boards.board import Board


class ArduinoNano(Board):
    """Arduino Nano (ATmega328) over USB serial running StandardFirmata."""
    id = "arduino:nano"
    name = "Arduino Nano"
    digital_pins = range(14)
    analog_pins = range(8)
    analog_only_pins = frozenset({6, 7})
    pwm_pins = frozenset({3, 5, 6, 9, 10, 11})
    default_baud = 57600
