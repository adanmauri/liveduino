"""Pinguino 26J50 board (PIC18F26J50, 28-pin).

8-bit Pinguino over USB serial running PinguinoFirmata (Firmata protocol, driven
by liveduino's FirmataProtocol). ``fqbn`` is ``None`` (flash with Pinguino's
tools); the pin map is a fallback refined by the firmware's capability query.
"""

from liveduino.boards.board import Board
from liveduino.boards.pinguino import ANALOG_28, DIGITAL_28, PINGUINO_BAUD, PWM_TWO


class Pinguino26J50(Board):
    """Pinguino 26J50 (PIC18F26J50) over USB serial running PinguinoFirmata."""

    id = "pinguino:26j50"
    name = "Pinguino 26J50"
    firmware_sketch = "PinguinoFirmata"
    digital_pins = DIGITAL_28
    analog_pins = ANALOG_28
    pwm_pins = PWM_TWO
    default_baud = PINGUINO_BAUD
