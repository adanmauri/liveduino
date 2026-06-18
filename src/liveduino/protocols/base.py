"""Protocol layer abstractions.

Defines the ``ProtocolClient`` protocol implemented by every host-to-board
protocol. A protocol client encodes the board API into wire commands and decodes
incoming reports, sitting between the board and the driver.
"""

from typing import Protocol

from liveduino.types import BitOrder, DigitalValue, PinMode


class ProtocolClient(Protocol):
    """Command encoder/decoder for a host-to-board protocol.

    Structural protocol that translates the board API (pin modes, reads, and
    writes) into the wire format understood by the firmware, and parses the
    responses returned over the driver.
    """
    def connect(self) -> None:
        """Establish the protocol session with the board."""
        ...

    def disconnect(self) -> None:
        """Close the protocol session."""
        ...

    def pin_mode(self, pin: int, mode: PinMode) -> None:
        """Configure a digital pin mode."""
        ...

    def digital_write(self, pin: int, value: DigitalValue) -> None:
        """Write a digital pin HIGH or LOW."""
        ...

    def digital_read(self, pin: int) -> DigitalValue:
        """Read a digital pin value."""
        ...

    def analog_read(self, pin: int) -> int:
        """Read an analog channel (0-1023 on AVR boards)."""
        ...

    def analog_write(self, pin: int, value: int) -> None:
        """Write a PWM value (0-255) to a PWM-capable pin."""
        ...

    def tone(self, pin: int, frequency: int, duration: int | None) -> None:
        """Generate a square wave of the given frequency on a pin."""
        ...

    def no_tone(self, pin: int) -> None:
        """Stop a tone started on a pin."""
        ...

    def pulse_in(self, pin: int, value: DigitalValue, timeout: int) -> int:
        """Measure a pulse of the given level on a pin, in microseconds."""
        ...

    def shift_out(self, data_pin: int, clock_pin: int, bit_order: BitOrder, value: int) -> None:
        """Shift a byte out one bit at a time on a data pin."""
        ...

    def shift_in(self, data_pin: int, clock_pin: int, bit_order: BitOrder) -> int:
        """Shift in a byte of data one bit at a time from a data pin."""
        ...
