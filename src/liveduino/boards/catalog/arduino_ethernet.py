"""Arduino Ethernet board.

Board definition for the Arduino Ethernet (ATmega328), controlled over a serial
link running StandardFirmata.
"""

from liveduino.boards.board import Board


class ArduinoEthernet(Board):
    """Arduino Ethernet (ATmega328) running StandardFirmata over serial.

    ATmega328 board with 14 digital pins and 6 analog inputs; PWM is available
    on pins 3, 5, 6, 9, 10, and 11, and pins 10-13 are reserved for the onboard
    Ethernet controller.
    """
    id = "arduino:ethernet"
    name = "Arduino Ethernet"
    digital_pins = range(14)
    analog_pins = range(6)
    pwm_pins = frozenset({3, 5, 6, 9, 10, 11})
    reserved_pins = frozenset({10, 11, 12, 13})
    default_baud = 57600
