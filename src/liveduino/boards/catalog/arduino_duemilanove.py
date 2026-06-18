"""Arduino Duemilanove / Diecimila board.

Board definition for the Arduino Duemilanove or Diecimila (ATmega328/168),
controlled over USB serial running StandardFirmata.
"""

from liveduino.boards.board import Board


class ArduinoDuemilanove(Board):
    """Arduino Duemilanove or Diecimila (ATmega328/168) running StandardFirmata.

    ATmega328/168 board with 14 digital pins, 6 analog inputs, and PWM available
    on pins 3, 5, 6, 9, 10, and 11.
    """
    id = "arduino:diecimila"
    name = "Arduino Duemilanove or Diecimila"
    digital_pins = range(14)
    analog_pins = range(6)
    pwm_pins = frozenset({3, 5, 6, 9, 10, 11})
    default_baud = 57600
