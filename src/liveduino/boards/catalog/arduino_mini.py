"""Arduino Mini board."""

from liveduino.boards.board import Board


class ArduinoMini(Board):
    """Arduino Mini (ATmega328) over serial running StandardFirmata."""
    id = "arduino:mini"
    name = "Arduino Mini"
    digital_pins = range(14)
    analog_pins = range(8)
    analog_only_pins = frozenset({6, 7})
    pwm_pins = frozenset({3, 5, 6, 9, 10, 11})
    default_baud = 57600
