"""Arduino BT board."""

from liveduino.boards.board import Board


class ArduinoBt(Board):
    """Arduino BT (ATmega328) running StandardFirmata over Bluetooth."""
    id = "arduino:bt"
    name = "Arduino BT"
    digital_pins = range(14)
    analog_pins = range(6)
    pwm_pins = frozenset({3, 5, 6, 9, 10, 11})
    default_baud = 57600
