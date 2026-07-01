"""Pinguino 4455 board (PIC18F4455, 40-pin).

8-bit Pinguino over USB serial running PinguinoFirmata (Firmata protocol, driven
by liveduino's FirmataProtocol). ``fqbn`` is ``None`` (flash with Pinguino's
tools); the pin map is a fallback refined by the firmware's capability query.
"""

from liveduino.boards.board import Board
from liveduino.boards.pinguino import ANALOG_40, DIGITAL_40, PINGUINO_BAUD, PWM_TWO


class Pinguino4455(Board):
    """Pinguino 4455 (PIC18F4455) over USB serial running PinguinoFirmata."""

    id = "pinguino:4455"
    name = "Pinguino 4455"
    firmware_sketch = "PinguinoFirmata"
    digital_pins = DIGITAL_40
    analog_pins = ANALOG_40
    pwm_pins = PWM_TWO
    default_baud = PINGUINO_BAUD
