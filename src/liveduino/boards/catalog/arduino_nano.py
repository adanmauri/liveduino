"""Arduino Nano board.

Board definition for the Arduino Nano (ATmega328), controlled over USB serial
running StandardFirmata.
"""

from liveduino.boards.board import Board


class ArduinoNano(Board):
    """Arduino Nano (ATmega328) over USB serial running StandardFirmata.

    ATmega328 board with 14 digital pins and 8 analog inputs (A6 and A7 are
    analog-only); PWM is available on pins 3, 5, 6, 9, 10, and 11.
    """
    id = "arduino:nano"
    fqbn = "arduino:avr:nano"
    name = "Arduino Nano"
    digital_pins = range(14)
    analog_pins = range(8)
    analog_only_pins = frozenset({6, 7})
    pwm_pins = frozenset({3, 5, 6, 9, 10, 11})
    default_baud = 57600
