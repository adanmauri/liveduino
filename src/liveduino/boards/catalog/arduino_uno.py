"""Arduino UNO board."""

from liveduino.boards.board import Board


class ArduinoUno(Board):
    """Arduino UNO over USB serial running StandardFirmata."""
    id = "arduino:uno"
    name = "Arduino UNO"
    digital_pins = range(14)
    analog_pins = range(6)
    pwm_pins = frozenset({3, 5, 6, 9, 10, 11})
    default_baud = 57600
