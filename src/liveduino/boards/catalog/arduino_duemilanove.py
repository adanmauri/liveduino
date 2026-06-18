"""Arduino Duemilanove / Diecimila board."""

from liveduino.boards.board import Board


class ArduinoDuemilanove(Board):
    """Arduino Duemilanove or Diecimila (ATmega328/168) running StandardFirmata."""
    id = "arduino:diecimila"
    name = "Arduino Duemilanove or Diecimila"
    digital_pins = range(14)
    analog_pins = range(6)
    pwm_pins = frozenset({3, 5, 6, 9, 10, 11})
    default_baud = 57600
