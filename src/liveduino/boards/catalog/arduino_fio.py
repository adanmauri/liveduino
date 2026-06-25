"""Arduino Fio board.

Board definition for the Arduino Fio (ATmega328P, 3.3V), controlled over a
serial link running StandardFirmata.
"""

from liveduino.boards.board import Board


class ArduinoFio(Board):
    """Arduino Fio (ATmega328P, 3.3V) running StandardFirmata.

    ATmega328P board with 14 digital pins and 8 analog inputs (A6 and A7 are
    analog-only); PWM is available on pins 3, 5, 6, 9, 10, and 11.
    """
    id = "arduino:fio"
    fqbn = "arduino:avr:fio"
    name = "Arduino Fio"
    digital_pins = range(14)
    analog_pins = range(8)
    analog_only_pins = frozenset({6, 7})
    pwm_pins = frozenset({3, 5, 6, 9, 10, 11})
    default_baud = 57600
