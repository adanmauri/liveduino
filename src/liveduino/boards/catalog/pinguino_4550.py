"""Pinguino 4550 board (PIC18F4550, 40-pin).

8-bit Pinguino controlled over USB serial, running the ``PinguinoFirmata``
firmware (``firmware/pinguino/firmata/``), which speaks the same Firmata wire
protocol as StandardFirmata. liveduino drives it with the native
``FirmataProtocol``. ``fqbn`` is ``None``: flash the firmware with Pinguino's own
tools. The pin map is a fallback, refined at runtime by the firmware's capability
query.
"""

from liveduino.boards.board import Board
from liveduino.boards.pinguino import ANALOG_40, DIGITAL_40, PINGUINO_BAUD, PWM_TWO


class Pinguino4550(Board):
    """Pinguino 4550 (PIC18F4550) over USB serial running PinguinoFirmata."""

    id = "pinguino:4550"
    name = "Pinguino 4550"
    firmware_sketch = "PinguinoFirmata"
    digital_pins = DIGITAL_40
    analog_pins = ANALOG_40
    pwm_pins = PWM_TWO
    default_baud = PINGUINO_BAUD
