"""Pinguino 4550 board.

8-bit Pinguino board (PIC18F4550) controlled over USB serial. It runs the
``PinguinoFirmata`` firmware (``firmware/pinguino/firmata/``), which speaks the
same Firmata wire protocol as StandardFirmata, so liveduino drives it with the
native ``FirmataProtocol`` — no client changes.

``fqbn`` is ``None``: the firmware is built with the Pinguino IDE, not
arduino-cli, so there is no bundled hex to flash. Flash ``PinguinoFirmata`` with
Pinguino's own tools; liveduino then just talks Firmata over the serial port.

The pin map below is a **fallback**. The firmware answers the Firmata capability
query, so ``board.capabilities()`` reads the board's real per-pin modes from the
hardware and uses them over this catalog definition.
"""

from liveduino.boards.board import Board


class Pinguino4550(Board):
    """Pinguino 4550 (PIC18F4550) over USB serial running PinguinoFirmata."""

    id = "pinguino:4550"
    name = "Pinguino 4550"
    firmware_sketch = "PinguinoFirmata"
    # Provisional map; refined at runtime by the firmware's capability query.
    digital_pins = range(30)
    analog_pins = range(13)
    pwm_pins = frozenset({11, 12})  # CCP1 / CCP2
    default_baud = 115200  # USB CDC ignores the rate, but the driver needs one
