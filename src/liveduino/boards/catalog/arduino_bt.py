"""Arduino BT board.

Board definition for the Arduino BT (ATmega328), controlled over a Bluetooth
serial link running StandardFirmata.
"""

from liveduino.boards.board import Board


class ArduinoBt(Board):
    """Arduino BT (ATmega328) running StandardFirmata over Bluetooth.

    ATmega328 board with 14 digital pins, 6 analog inputs, and PWM available on
    pins 3, 5, 6, 9, 10, and 11.
    """
    id = "arduino:bt"
    name = "Arduino BT"
    digital_pins = range(14)
    analog_pins = range(6)
    pwm_pins = frozenset({3, 5, 6, 9, 10, 11})
    default_baud = 57600
