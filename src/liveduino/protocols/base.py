"""Protocol layer abstractions.

Defines the ``ProtocolClient`` protocol implemented by every host-to-board
protocol. A protocol client encodes the board API into wire commands and decodes
incoming reports, sitting between the board and the driver.
"""

from collections.abc import Iterable
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

    def servo_config(self, pin: int, min_pulse: int, max_pulse: int) -> None:
        """Attach a servo on a pin and set its min/max pulse widths (microseconds)."""
        ...

    def servo_write(self, pin: int, angle: int) -> None:
        """Move a servo to an angle (0-180 degrees)."""
        ...

    def i2c_config(self, delay: int = 0) -> None:
        """Enable the I2C bus, setting the read delay in microseconds."""
        ...

    def i2c_write(self, address: int, data: Iterable[int]) -> None:
        """Write a sequence of bytes to an I2C device at a 7-bit address."""
        ...

    def i2c_read(
        self, address: int, count: int, register: int | None = None, *, restart: bool = False
    ) -> bytes:
        """Read count bytes from an I2C device, optionally from a register."""
        ...

    def i2c_read_continuous(self, address: int, count: int, register: int | None = None) -> None:
        """Ask an I2C device to keep reporting count bytes until stopped."""
        ...

    def i2c_value(self, address: int, register: int | None = None) -> bytes | None:
        """Return the latest continuously-reported I2C reply, or None."""
        ...

    def i2c_stop_reading(self, address: int) -> None:
        """Stop a continuous I2C read for a device."""
        ...

    def sampling_interval(self, milliseconds: int) -> None:
        """Set how often the board auto-reports analog and continuous I2C reads."""
        ...

    def read_string(self) -> str | None:
        """Return the latest text message the board has sent, or None."""
        ...

    def serial_config(
        self, port: int, baud: int, rx: int | None = None, tx: int | None = None
    ) -> None:
        """Open a serial-relay port at a baud rate."""
        ...

    def serial_write(self, port: int, data: Iterable[int]) -> None:
        """Write bytes out of a serial-relay port."""
        ...

    def serial_value(self, port: int) -> bytes:
        """Return and clear bytes received on a serial-relay port."""
        ...

    def serial_close(self, port: int) -> None:
        """Close a serial-relay port."""
        ...

    def report_firmware(self) -> tuple[int, int, str]:
        """Query the firmware (major, minor, name)."""
        ...

    def capability_query(self) -> dict[int, list[int]]:
        """Query the modes each pin supports."""
        ...

    def analog_mapping_query(self) -> dict[int, int]:
        """Query the pin-to-analog-channel mapping."""
        ...

    def pin_state_query(self, pin: int) -> tuple[int, int]:
        """Query a pin's current (mode, value)."""
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
