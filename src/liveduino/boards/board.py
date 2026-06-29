"""Arduino/Wiring board base class.

Defines ``Board``, the abstract base shared by every concrete board model. It
exposes the Arduino/Wiring API (pinMode, digitalWrite, analogRead, ...), holds
the board's pin map and capabilities, and manages the driver and protocol used
to talk to the hardware.
"""

from __future__ import annotations

import abc
import time
from collections.abc import Callable, Iterable
from typing import ClassVar, Self

from liveduino.constants import (
    HIGH,
    INPUT,
    INPUT_PULLUP,
    LOW,
    OUTPUT,
)
from liveduino.drivers.base import Driver
from liveduino.drivers.serial import SerialDriver
from liveduino.exceptions import (
    BoardConnectionError,
    InvalidModeError,
    InvalidPinError,
    InvalidValueError,
    LiveduinoError,
)
from liveduino.i2c import Wire
from liveduino.protocols.base import ProtocolClient
from liveduino.protocols.firmata import FirmataProtocol
from liveduino.types import AnalogPin, BitOrder, DigitalValue, PinArg, PinMode


class Board(abc.ABC):
    """Abstract base class for Arduino-compatible boards; subclass it per board model.

    Concrete boards declare their pin map and capabilities as class attributes
    and inherit the full Arduino/Wiring API. The base class validates pins,
    modes, and values before delegating to the active protocol client.
    """
    id: ClassVar[str]
    name: ClassVar[str]
    digital_pins: ClassVar[range]
    analog_pins: ClassVar[range]
    pwm_pins: ClassVar[frozenset[int]]
    default_baud: ClassVar[int] = 57600

    # Bootloader settings used when flashing firmware over serial (STK500v1).
    flash_baud: ClassVar[int] = 115200
    flash_page_size: ClassVar[int] = 128

    # Firmware metadata: the primary sketch the board runs (what 'liveduino-cli flash'
    # writes over serial) and the arduino-cli FQBN used to build it (fqbn is None
    # when the board has no bundled firmware). firmware_sketches lists extra Firmata
    # variants to also build/bundle for the board (e.g. network transports), even if
    # liveduino does not support them yet.
    firmware_sketch: ClassVar[str] = "StandardFirmata"
    firmware_sketches: ClassVar[tuple[str, ...]] = ()
    fqbn: ClassVar[str | None] = None

    # Digital pin number of analog channel A0 (A0=14 on the ATmega328/168 family).
    first_analog_pin: ClassVar[int] = 14
    # Analog channels that are input-only and cannot be used for digital I/O.
    analog_only_pins: ClassVar[frozenset[int]] = frozenset()
    # Digital pins reserved by onboard hardware (e.g. SPI) and unavailable for I/O.
    reserved_pins: ClassVar[frozenset[int]] = frozenset()

    _REQUIRED_ATTRS: ClassVar[tuple[str, ...]] = (
        "id",
        "name",
        "digital_pins",
        "analog_pins",
        "pwm_pins",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Validate that every concrete board defines the required class attributes."""
        super().__init_subclass__(**kwargs)
        missing = [attr for attr in cls._REQUIRED_ATTRS if not hasattr(cls, attr)]
        if missing:
            raise TypeError(
                f"{cls.__name__} must define class attributes: {', '.join(missing)}"
            )

    def __init__(self, protocol: Callable[[Driver], ProtocolClient] | None = None) -> None:
        """Create a board; protocol defaults to the board's protocol, set it to override."""
        if type(self) is Board:  # pylint: disable=unidiomatic-typecheck
            raise TypeError("Board is abstract; instantiate a concrete board subclass instead")
        self._make_protocol: Callable[[Driver], ProtocolClient] = (
            self.protocol_factory if protocol is None else protocol
        )
        self._protocol: ProtocolClient | None = None
        self._origin_s = time.monotonic()
        self._wire: Wire | None = None

    @staticmethod
    def protocol_factory(driver: Driver) -> ProtocolClient:
        """Default protocol client for this board; override per model to change it."""
        return FirmataProtocol(driver)

    def connect(
        self,
        port: str | None = None,
        *,
        baud: int | None = None,
        driver: Driver | None = None,
    ) -> Self:
        """
        Connect this board over serial (default) or a given driver. The driver
        is how the board is connected (serial/TCP/Bluetooth); the protocol is
        the one chosen when the board was instantiated.
        """
        if driver is not None:
            if port is not None or baud is not None:
                raise LiveduinoError(
                    f"{type(self).__name__}.connect accepts either port/baud or driver, not both"
                )
        else:
            if port is None:
                raise LiveduinoError(f"{type(self).__name__}.connect requires a port or a driver")
            rate = self.default_baud if baud is None else baud
            driver = SerialDriver(port, baud=rate)
        protocol = self._make_protocol(driver)
        protocol.connect()
        self._protocol = protocol
        return self

    @property
    def _client(self) -> ProtocolClient:
        if self._protocol is None:
            raise BoardConnectionError(f"{self.name} is not connected; call connect() first")
        return self._protocol

    @classmethod
    def is_valid_digital_pin(cls, pin: int) -> bool:
        """Return True if pin can be used for digital I/O (including A0-A5)."""
        if pin in cls.digital_pins:
            return True
        channel = pin - cls.first_analog_pin
        return channel in cls.analog_pins and channel not in cls.analog_only_pins

    @classmethod
    def is_valid_analog_pin(cls, pin: int) -> bool:
        """Return True if pin is a valid analog channel index."""
        return pin in cls.analog_pins

    @classmethod
    def supports_pwm(cls, pin: int) -> bool:
        """Return True if the digital pin supports PWM output."""
        return pin in cls.pwm_pins

    def pinMode(self, pin: PinArg, mode: PinMode) -> None:
        """Configure a digital pin as INPUT, OUTPUT, or INPUT_PULLUP."""
        pin = self._resolve_digital_pin(pin)
        if mode not in (INPUT, OUTPUT, INPUT_PULLUP):
            raise InvalidModeError(
                f"pinMode mode must be INPUT, OUTPUT, or INPUT_PULLUP, got {mode}"
            )
        self._client.pin_mode(pin, mode)

    def digitalWrite(self, pin: PinArg, value: DigitalValue) -> None:
        """Write HIGH or LOW to a digital output pin."""
        pin = self._resolve_digital_pin(pin)
        if value not in (LOW, HIGH):
            raise InvalidValueError(f"digitalWrite value must be LOW or HIGH, got {value}")
        self._client.digital_write(pin, value)

    def digitalRead(self, pin: PinArg) -> DigitalValue:
        """Read HIGH or LOW from a digital input pin."""
        pin = self._resolve_digital_pin(pin)
        return self._client.digital_read(pin)

    def analogRead(self, pin: PinArg) -> int:
        """Read an analog input channel (0-1023 on AVR boards); accepts A0-A7 or a channel."""
        channel = pin.channel if isinstance(pin, AnalogPin) else pin
        self._validate_analog_pin(channel)
        return self._client.analog_read(channel)

    def analogWrite(self, pin: PinArg, value: int) -> None:
        """Write a PWM value (0-255) to a PWM-capable digital pin."""
        pin = self._resolve_digital_pin(pin)
        if not self.supports_pwm(pin):
            raise InvalidPinError(f"Pin {pin} does not support PWM on {self.name}")
        if not 0 <= value <= 255:
            raise InvalidValueError(f"analogWrite value must be 0-255, got {value}")
        self._client.analog_write(pin, value)

    def servoWrite(self, pin: PinArg, angle: int) -> None:
        """Move a servo attached to a pin to an angle (0-180 degrees)."""
        pin = self._resolve_digital_pin(pin)
        if not 0 <= angle <= 180:
            raise InvalidValueError(f"servoWrite angle must be 0-180, got {angle}")
        self._client.servo_write(pin, angle)

    def servoConfig(self, pin: PinArg, minPulse: int = 544, maxPulse: int = 2400) -> None:
        """Attach a servo on a pin and set its min/max pulse widths in microseconds."""
        pin = self._resolve_digital_pin(pin)
        if not 0 <= minPulse <= maxPulse:
            raise InvalidValueError(
                f"servoConfig requires 0 <= minPulse <= maxPulse, got {minPulse}, {maxPulse}"
            )
        self._client.servo_config(pin, minPulse, maxPulse)

    def i2cConfig(self, delay: int = 0) -> None:
        """Enable the I2C bus, optionally setting the read delay in microseconds."""
        self._client.i2c_config(delay)

    def i2cWrite(self, address: int, data: Iterable[int]) -> None:
        """Write a sequence of bytes to the I2C device at a 7-bit address."""
        self._client.i2c_write(address, data)

    def i2cRead(
        self, address: int, count: int, register: int | None = None, *, restart: bool = False
    ) -> bytes:
        """Read count bytes from an I2C device, optionally starting at a register."""
        return self._client.i2c_read(address, count, register, restart=restart)

    @property
    def wire(self) -> Wire:
        """Arduino ``Wire``-style I2C interface bound to this board."""
        if self._wire is None:
            self._wire = Wire(self)
        return self._wire

    def tone(self, pin: PinArg, frequency: int, duration: int | None = None) -> None:
        """Generate a square wave of the given frequency on a digital pin."""
        pin = self._resolve_digital_pin(pin)
        self._client.tone(pin, frequency, duration)

    def noTone(self, pin: PinArg) -> None:
        """Stop a tone previously started on a digital pin."""
        pin = self._resolve_digital_pin(pin)
        self._client.no_tone(pin)

    def pulseIn(self, pin: PinArg, value: DigitalValue, timeout: int = 1_000_000) -> int:
        """Measure the length of a pulse on a digital pin, in microseconds."""
        pin = self._resolve_digital_pin(pin)
        return self._client.pulse_in(pin, value, timeout)

    def shiftOut(self, dataPin: PinArg, clockPin: PinArg, bitOrder: BitOrder, value: int) -> None:
        """Shift a byte out one bit at a time on a data pin."""
        data_pin = self._resolve_digital_pin(dataPin)
        clock_pin = self._resolve_digital_pin(clockPin)
        self._client.shift_out(data_pin, clock_pin, bitOrder, value)

    def shiftIn(self, dataPin: PinArg, clockPin: PinArg, bitOrder: BitOrder) -> int:
        """Shift in a byte of data one bit at a time from a data pin."""
        data_pin = self._resolve_digital_pin(dataPin)
        clock_pin = self._resolve_digital_pin(clockPin)
        return self._client.shift_in(data_pin, clock_pin, bitOrder)

    def delay(self, ms: int) -> None:
        """Block the host for the given number of milliseconds."""
        time.sleep(ms / 1000.0)

    def delayMicroseconds(self, us: int) -> None:
        """Block the host for the given number of microseconds."""
        time.sleep(us / 1_000_000.0)

    def millis(self) -> int:
        """Return milliseconds elapsed since this board connection started."""
        return int((time.monotonic() - self._origin_s) * 1000.0)

    def micros(self) -> int:
        """Return microseconds elapsed since this board connection started."""
        return int((time.monotonic() - self._origin_s) * 1_000_000.0)

    def close(self) -> None:
        """Disconnect from the board."""
        if self._protocol is not None:
            self._protocol.disconnect()

    def _resolve_digital_pin(self, pin: PinArg) -> int:
        """Resolve a pin argument (raw number or analog constant) to a physical digital pin."""
        if isinstance(pin, AnalogPin):
            if pin.channel not in self.analog_pins or pin.channel in self.analog_only_pins:
                raise InvalidPinError(f"{pin!r} has no digital function on {self.name}")
            resolved = self.first_analog_pin + pin.channel
        elif self.is_valid_digital_pin(pin):
            resolved = pin
        else:
            raise InvalidPinError(f"Invalid digital pin {pin} for {self.name}")
        if resolved in self.reserved_pins:
            raise InvalidPinError(f"Pin {resolved} is reserved on {self.name}")
        return resolved

    def _validate_analog_pin(self, pin: int) -> None:
        if not self.is_valid_analog_pin(pin):
            raise InvalidPinError(f"Invalid analog pin {pin} for {self.name}")
