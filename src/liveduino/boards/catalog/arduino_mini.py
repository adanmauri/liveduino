"""Arduino Mini board.

Board definition for the Arduino Mini (ATmega328), controlled over a serial link
running StandardFirmata.
"""

from liveduino.boards.board import Board


class ArduinoMini(Board):
    """Arduino Mini (ATmega328) over serial running StandardFirmata.

    ATmega328 board with 14 digital pins and 8 analog inputs (A6 and A7 are
    analog-only); PWM is available on pins 3, 5, 6, 9, 10, and 11.
    """
    id = "arduino:mini"
    fqbn = "arduino:avr:mini"
    name = "Arduino Mini"
    digital_pins = range(14)
    analog_pins = range(8)
    analog_only_pins = frozenset({6, 7})
    pwm_pins = frozenset({3, 5, 6, 9, 10, 11})
    default_baud = 57600
