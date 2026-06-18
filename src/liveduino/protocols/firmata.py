"""Native StandardFirmata protocol client over a byte Driver.

Implements the Firmata 2.x wire protocol directly (no third-party Firmata
library). Outgoing commands are encoded to bytes and written to the driver;
incoming digital/analog reports are parsed by a small synchronous state machine
that is pumped on each read.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from liveduino.constants import INPUT as LD_INPUT
from liveduino.constants import INPUT_PULLUP as LD_INPUT_PULLUP
from liveduino.constants import OUTPUT as LD_OUTPUT
from liveduino.exceptions import (
    BoardConnectionError,
    InvalidModeError,
    InvalidValueError,
    UnsupportedOperationError,
)
from liveduino.types import BitOrder, DigitalValue, PinMode

if TYPE_CHECKING:
    from liveduino.drivers.base import Driver

# Firmata command bytes
DIGITAL_MESSAGE = 0x90
ANALOG_MESSAGE = 0xE0
REPORT_ANALOG = 0xC0
REPORT_DIGITAL = 0xD0
SET_PIN_MODE = 0xF4
SET_DIGITAL_PIN_VALUE = 0xF5
REPORT_VERSION = 0xF9
START_SYSEX = 0xF0
END_SYSEX = 0xF7

# Firmata pin modes
_PIN_MODE_INPUT = 0x00
_PIN_MODE_OUTPUT = 0x01
_PIN_MODE_PWM = 0x03
_PIN_MODE_PULLUP = 0x0B

_FIRMATA_PIN_MODES = {
    LD_INPUT: _PIN_MODE_INPUT,
    LD_OUTPUT: _PIN_MODE_OUTPUT,
    LD_INPUT_PULLUP: _PIN_MODE_PULLUP,
}


class _FirmataParser:
    """Incremental decoder for inbound Firmata digital and analog reports.

    Fed raw bytes as they arrive, it runs a small synchronous state machine that
    tracks the current command and caches the latest digital and analog values
    for later reads.
    """
    def __init__(self) -> None:
        self.digital_inputs: dict[int, int] = {}
        self.analog_values: dict[int, int] = {}
        self._command = 0
        self._channel = 0
        self._expected = 0
        self._data: list[int] = []
        self._in_sysex = False

    def reset(self) -> None:
        """Clear cached pin values."""
        self.digital_inputs.clear()
        self.analog_values.clear()

    def feed(self, data: bytes) -> None:
        """Process a chunk of inbound bytes."""
        for byte in data:
            self._process_byte(byte)

    def _process_byte(self, byte: int) -> None:
        if self._in_sysex:
            if byte == END_SYSEX:
                self._in_sysex = False
            return
        if byte >= 0x80:
            self._begin_command(byte)
            return
        if self._expected:
            self._data.append(byte)
            if len(self._data) == self._expected:
                self._dispatch()
                self._expected = 0

    def _begin_command(self, byte: int) -> None:
        if byte == START_SYSEX:
            self._in_sysex = True
            return
        command = byte & 0xF0
        if command in (DIGITAL_MESSAGE, ANALOG_MESSAGE):
            self._command = command
            self._channel = byte & 0x0F
            self._expected = 2
            self._data = []
        elif byte == REPORT_VERSION:
            self._command = REPORT_VERSION
            self._expected = 2
            self._data = []
        else:
            self._expected = 0

    def _dispatch(self) -> None:
        value = self._data[0] | (self._data[1] << 7)
        if self._command == DIGITAL_MESSAGE:
            base = self._channel * 8
            for offset in range(8):
                self.digital_inputs[base + offset] = (value >> offset) & 0x01
        elif self._command == ANALOG_MESSAGE:
            self.analog_values[self._channel] = value


class FirmataProtocol:
    """StandardFirmata client implemented natively over a byte driver.

    Encodes the board API into Firmata 2.x wire commands and parses incoming
    reports, without relying on any third-party Firmata library. Operations that
    StandardFirmata cannot perform raise ``UnsupportedOperationError``.
    """
    def __init__(self, driver: Driver) -> None:
        self._driver = driver
        self._connected = False
        self._digital_reporting: set[int] = set()
        self._analog_reporting: set[int] = set()
        self._parser = _FirmataParser()

    def connect(self) -> None:
        """Open the driver for Firmata communication."""
        self._driver.open()
        self._connected = True

    def disconnect(self) -> None:
        """Close the driver and reset cached state."""
        if self._connected:
            self._driver.close()
        self._connected = False
        self._digital_reporting.clear()
        self._analog_reporting.clear()
        self._parser.reset()

    def pin_mode(self, pin: int, mode: PinMode) -> None:
        """Set a digital pin to INPUT, OUTPUT, or INPUT_PULLUP."""
        try:
            firmata_mode = _FIRMATA_PIN_MODES[mode]
        except KeyError as exc:
            raise InvalidModeError(f"Unsupported pin mode: {mode}") from exc
        self._send(bytes([SET_PIN_MODE, pin, firmata_mode]))

    def digital_write(self, pin: int, value: DigitalValue) -> None:
        """Write HIGH or LOW to a digital output pin."""
        if value not in (0, 1):
            raise InvalidValueError(f"Digital value must be 0 or 1, got {value}")
        self._send(bytes([SET_DIGITAL_PIN_VALUE, pin, value]))

    def digital_read(self, pin: int) -> DigitalValue:
        """Read the latest reported state of a digital input pin."""
        port = pin // 8
        if port not in self._digital_reporting:
            self._send(bytes([REPORT_DIGITAL | port, 1]))
            self._digital_reporting.add(port)
        self._pump()
        return cast(DigitalValue, self._parser.digital_inputs.get(pin, 0))

    def analog_read(self, pin: int) -> int:
        """Read the latest reported value of an analog input channel (0-1023)."""
        if pin not in self._analog_reporting:
            self._send(bytes([REPORT_ANALOG | pin, 1]))
            self._analog_reporting.add(pin)
        self._pump()
        return self._parser.analog_values.get(pin, 0)

    def analog_write(self, pin: int, value: int) -> None:
        """Write a PWM duty cycle (0-255) on a PWM-capable pin."""
        if not 0 <= value <= 255:
            raise InvalidValueError(f"PWM value must be 0-255, got {value}")
        self._send(bytes([SET_PIN_MODE, pin, _PIN_MODE_PWM]))
        self._send(bytes([ANALOG_MESSAGE | (pin & 0x0F), value & 0x7F, (value >> 7) & 0x7F]))

    def tone(self, pin: int, frequency: int, duration: int | None) -> None:
        """StandardFirmata cannot generate tones; raises UnsupportedOperationError."""
        raise UnsupportedOperationError("tone is not supported by StandardFirmata")

    def no_tone(self, pin: int) -> None:
        """StandardFirmata cannot generate tones; raises UnsupportedOperationError."""
        raise UnsupportedOperationError("noTone is not supported by StandardFirmata")

    def pulse_in(self, pin: int, value: DigitalValue, timeout: int) -> int:
        """StandardFirmata cannot measure pulses; raises UnsupportedOperationError."""
        raise UnsupportedOperationError("pulseIn is not supported by StandardFirmata")

    def shift_out(self, data_pin: int, clock_pin: int, bit_order: BitOrder, value: int) -> None:
        """StandardFirmata has no shift support; raises UnsupportedOperationError."""
        raise UnsupportedOperationError("shiftOut is not supported by StandardFirmata")

    def shift_in(self, data_pin: int, clock_pin: int, bit_order: BitOrder) -> int:
        """StandardFirmata has no shift support; raises UnsupportedOperationError."""
        raise UnsupportedOperationError("shiftIn is not supported by StandardFirmata")

    def _send(self, data: bytes) -> None:
        if not self._connected:
            raise BoardConnectionError("Firmata session is not connected")
        self._driver.write(data)

    def _pump(self) -> None:
        waiting = self._driver.in_waiting
        if waiting:
            self._parser.feed(self._driver.read(waiting))
