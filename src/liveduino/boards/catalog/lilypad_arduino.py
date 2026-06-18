"""LilyPad Arduino board."""

from liveduino.boards.board import Board


class LilyPadArduino(Board):
    """LilyPad Arduino (ATmega328) running StandardFirmata over serial."""
    id = "arduino:lilypad"
    name = "LilyPad Arduino"
    digital_pins = range(14)
    analog_pins = range(6)
    pwm_pins = frozenset({3, 5, 6, 9, 10, 11})
    default_baud = 57600
