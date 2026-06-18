"""Arduino UNO Mini board.

Board definition for the Arduino UNO Mini (ATmega328P), controlled over USB
serial running StandardFirmata.
"""

from liveduino.boards.board import Board


class ArduinoUnoMini(Board):
    """Arduino UNO Mini (ATmega328P) over USB serial running StandardFirmata.

    ATmega328P board with 14 digital pins, 6 analog inputs, and PWM available on
    pins 3, 5, 6, 9, 10, and 11.
    """
    id = "arduino:unomini"
    name = "Arduino UNO Mini"
    digital_pins = range(14)
    analog_pins = range(6)
    pwm_pins = frozenset({3, 5, 6, 9, 10, 11})
    default_baud = 57600
