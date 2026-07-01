"""Pinguino 46J50 board (PIC18F46J50, 44-pin).

8-bit Pinguino over USB serial running PinguinoFirmata (Firmata protocol, driven
by liveduino's FirmataProtocol). ``fqbn`` is ``None`` (flash with Pinguino's
tools); the pin map is a fallback refined by the firmware's capability query.
"""

from liveduino.boards.board import Board
from liveduino.boards.pinguino import ANALOG_40, DIGITAL_40, PINGUINO_BAUD, PWM_TWO


class Pinguino46J50(Board):
    """Pinguino 46J50 (PIC18F46J50) over USB serial running PinguinoFirmata."""

    id = "pinguino:46j50"
    name = "Pinguino 46J50"
    firmware_sketch = "PinguinoFirmata"
    digital_pins = DIGITAL_40
    analog_pins = ANALOG_40
    pwm_pins = PWM_TWO
    default_baud = PINGUINO_BAUD
