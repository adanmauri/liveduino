"""Arduino UNO Mini board."""

from liveduino.boards.board import Board


class ArduinoUnoMini(Board):
    """Arduino UNO Mini (ATmega328P) over USB serial running StandardFirmata."""
    id = "arduino:unomini"
    name = "Arduino UNO Mini"
    digital_pins = range(14)
    analog_pins = range(6)
    pwm_pins = frozenset({3, 5, 6, 9, 10, 11})
    default_baud = 57600
