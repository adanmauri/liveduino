"""Arduino UNO board.

Board definition for the Arduino UNO (ATmega328P), the reference MVP target
controlled over USB serial with StandardFirmata.
"""

from liveduino.boards.board import Board


class ArduinoUno(Board):
    """Arduino UNO over USB serial running StandardFirmata.

    ATmega328P board with 14 digital pins, 6 analog inputs, and PWM available on
    pins 3, 5, 6, 9, 10, and 11.
    """
    id = "arduino:uno"
    fqbn = "arduino:avr:uno"
    name = "Arduino UNO"
    digital_pins = range(14)
    analog_pins = range(6)
    pwm_pins = frozenset({3, 5, 6, 9, 10, 11})
    default_baud = 57600
