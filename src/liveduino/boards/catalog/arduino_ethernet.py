"""Arduino Ethernet board."""

from liveduino.boards.board import Board


class ArduinoEthernet(Board):
    """Arduino Ethernet (ATmega328) running StandardFirmata over serial."""
    id = "arduino:ethernet"
    name = "Arduino Ethernet"
    digital_pins = range(14)
    analog_pins = range(6)
    pwm_pins = frozenset({3, 5, 6, 9, 10, 11})
    # Pins 10-13 drive the onboard W5100 over SPI; they cannot be used as I/O.
    reserved_pins = frozenset({10, 11, 12, 13})
    default_baud = 57600
