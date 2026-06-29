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
    from collections.abc import Iterable

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

# Firmata sysex sub-commands
SERVO_CONFIG = 0x70
I2C_REQUEST = 0x76
I2C_REPLY = 0x77
I2C_CONFIG = 0x78

# Servo pulse-width range, in microseconds (a 14-bit value over two 7-bit bytes).
_MAX_PULSE_WIDTH = 0x3FFF
# Servo angle range, in degrees, accepted by the Arduino Servo library.
_MAX_SERVO_ANGLE = 180

# I2C read/write modes, carried in bits 3-4 of the request's mode byte.
_I2C_WRITE = 0x00
_I2C_READ = 0x08
# Bit 6 of the mode byte requests a restart (1) instead of a stop (0) after the write.
_I2C_RESTART_TX = 0x40
# A 7-bit I2C address and an 8-bit data/register byte.
_I2C_ADDRESS_MAX = 0x7F
_I2C_BYTE_MAX = 0xFF
# Read delay between write and read, a 14-bit value over two 7-bit bytes.
_I2C_DELAY_MAX = 0x3FFF
# Upper bound on bytes pulled while waiting for an I2C reply, so a silent or
# chatty board cannot block the read forever.
_MAX_REPLY_READS = 1024

# Firmata pin modes
_PIN_MODE_INPUT = 0x00
_PIN_MODE_OUTPUT = 0x01
_PIN_MODE_PWM = 0x03
_PIN_MODE_SERVO = 0x04
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
        self.i2c_replies: dict[tuple[int, int], list[int]] = {}
        self._command = 0
        self._channel = 0
        self._expected = 0
        self._data: list[int] = []
        self._in_sysex = False
        self._sysex: list[int] = []

    def reset(self) -> None:
        """Clear cached pin values."""
        self.digital_inputs.clear()
        self.analog_values.clear()
        self.i2c_replies.clear()

    def take_i2c_reply(self, address: int, register: int) -> bytes | None:
        """Pop and return the latest I2C reply for an address/register, if any."""
        data = self.i2c_replies.pop((address, register), None)
        return None if data is None else bytes(data)

    def feed(self, data: bytes) -> None:
        """Process a chunk of inbound bytes."""
        for byte in data:
            self._process_byte(byte)

    def _process_byte(self, byte: int) -> None:
        if self._in_sysex:
            if byte == END_SYSEX:
                self._in_sysex = False
                self._end_sysex()
            else:
                self._sysex.append(byte)
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
            self._sysex = []
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

    def _end_sysex(self) -> None:
        if not self._sysex:
            return
        if self._sysex[0] == I2C_REPLY:
            self._store_i2c_reply(self._sysex[1:])

    def _store_i2c_reply(self, payload: list[int]) -> None:
        # Each original byte is sent as a 7-bit LSB/MSB pair; the first two decode
        # to the address and register, the rest are the data bytes.
        decoded = [payload[i] | (payload[i + 1] << 7) for i in range(0, len(payload) - 1, 2)]
        if len(decoded) >= 2:
            self.i2c_replies[(decoded[0], decoded[1])] = decoded[2:]


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

    def servo_config(self, pin: int, min_pulse: int, max_pulse: int) -> None:
        """Attach a servo on a pin and set its min/max pulse widths (microseconds)."""
        for pulse in (min_pulse, max_pulse):
            if not 0 <= pulse <= _MAX_PULSE_WIDTH:
                raise InvalidValueError(
                    f"Servo pulse width must be 0-{_MAX_PULSE_WIDTH}, got {pulse}"
                )
        self._send(
            bytes(
                [
                    START_SYSEX,
                    SERVO_CONFIG,
                    pin,
                    min_pulse & 0x7F,
                    (min_pulse >> 7) & 0x7F,
                    max_pulse & 0x7F,
                    (max_pulse >> 7) & 0x7F,
                    END_SYSEX,
                ]
            )
        )

    def servo_write(self, pin: int, angle: int) -> None:
        """Move a servo to an angle (0-180 degrees), attaching it if needed."""
        if not 0 <= angle <= _MAX_SERVO_ANGLE:
            raise InvalidValueError(
                f"Servo angle must be 0-{_MAX_SERVO_ANGLE}, got {angle}"
            )
        self._send(bytes([SET_PIN_MODE, pin, _PIN_MODE_SERVO]))
        self._send(bytes([ANALOG_MESSAGE | (pin & 0x0F), angle & 0x7F, (angle >> 7) & 0x7F]))

    def i2c_config(self, delay: int = 0) -> None:
        """Enable the I2C bus, setting the read delay (microseconds) between write and read."""
        if not 0 <= delay <= _I2C_DELAY_MAX:
            raise InvalidValueError(f"I2C delay must be 0-{_I2C_DELAY_MAX}, got {delay}")
        self._send(bytes([START_SYSEX, I2C_CONFIG, delay & 0x7F, (delay >> 7) & 0x7F, END_SYSEX]))

    def i2c_write(self, address: int, data: Iterable[int]) -> None:
        """Write a sequence of bytes to the I2C device at a 7-bit address."""
        self._check_i2c_address(address)
        message = [START_SYSEX, I2C_REQUEST, address, _I2C_WRITE]
        for value in data:
            if not 0 <= value <= _I2C_BYTE_MAX:
                raise InvalidValueError(f"I2C byte must be 0-{_I2C_BYTE_MAX}, got {value}")
            message += [value & 0x7F, (value >> 7) & 0x7F]
        message.append(END_SYSEX)
        self._send(bytes(message))

    def i2c_read(
        self, address: int, count: int, register: int | None = None, *, restart: bool = False
    ) -> bytes:
        """Read ``count`` bytes from an I2C device, optionally from a register."""
        self._check_i2c_address(address)
        if count < 0:
            raise InvalidValueError(f"I2C read count must be non-negative, got {count}")
        mode = _I2C_READ | (_I2C_RESTART_TX if restart else 0)
        message = [START_SYSEX, I2C_REQUEST, address, mode]
        if register is not None:
            if not 0 <= register <= _I2C_BYTE_MAX:
                raise InvalidValueError(f"I2C register must be 0-{_I2C_BYTE_MAX}, got {register}")
            message += [register & 0x7F, (register >> 7) & 0x7F]
        message += [count & 0x7F, (count >> 7) & 0x7F, END_SYSEX]
        self._send(bytes(message))
        return self._await_i2c_reply(address, register if register is not None else 0)

    @staticmethod
    def _check_i2c_address(address: int) -> None:
        if not 0 <= address <= _I2C_ADDRESS_MAX:
            raise InvalidValueError(f"I2C address must be 0-{_I2C_ADDRESS_MAX}, got {address}")

    def _await_i2c_reply(self, address: int, register: int) -> bytes:
        for _ in range(_MAX_REPLY_READS):
            chunk = self._driver.read(1)
            if not chunk:
                break
            self._parser.feed(chunk)
            reply = self._parser.take_i2c_reply(address, register)
            if reply is not None:
                return reply
        raise BoardConnectionError(f"No I2C reply received from address {address}")

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
