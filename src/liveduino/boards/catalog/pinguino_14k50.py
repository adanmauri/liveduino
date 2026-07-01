"""Pinguino 14K50 board (PIC18F14K50, 20-pin).

8-bit Pinguino over USB serial running PinguinoFirmata (Firmata protocol, driven
by liveduino's FirmataProtocol). ``fqbn`` is ``None`` (flash with Pinguino's
tools); the pin map is a fallback refined by the firmware's capability query.
"""

from liveduino.boards.board import Board
from liveduino.boards.pinguino import ANALOG_20, DIGITAL_20, PINGUINO_BAUD, PWM_ONE


class Pinguino14K50(Board):
    """Pinguino 14K50 (PIC18F14K50) over USB serial running PinguinoFirmata."""

    id = "pinguino:14k50"
    name = "Pinguino 14K50"
    firmware_sketch = "PinguinoFirmata"
    digital_pins = DIGITAL_20
    analog_pins = ANALOG_20
    pwm_pins = PWM_ONE
    default_baud = PINGUINO_BAUD
