"""Arduino Fio board."""

from liveduino.boards.board import Board


class ArduinoFio(Board):
    """Arduino Fio (ATmega328P, 3.3V) running StandardFirmata."""
    id = "arduino:fio"
    name = "Arduino Fio"
    digital_pins = range(14)
    analog_pins = range(8)
    analog_only_pins = frozenset({6, 7})
    pwm_pins = frozenset({3, 5, 6, 9, 10, 11})
    default_baud = 57600
