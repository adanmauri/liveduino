"""Native StandardFirmata protocol client over a byte Driver.

Implements the Firmata 2.x wire protocol directly (no third-party Firmata
library). Outgoing commands are encoded to bytes and written to the driver;
incoming digital/analog reports are parsed by a small synchronous state machine
that is pumped on each read.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, cast

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
    from collections.abc import Callable, Iterable

    from liveduino.drivers.base import Driver

_T = TypeVar("_T")

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
SERIAL_MESSAGE = 0x60
ANALOG_MAPPING_QUERY = 0x69
ANALOG_MAPPING_RESPONSE = 0x6A
CAPABILITY_QUERY = 0x6B
CAPABILITY_RESPONSE = 0x6C
PIN_STATE_QUERY = 0x6D
PIN_STATE_RESPONSE = 0x6E
EXTENDED_ANALOG = 0x6F
SERVO_CONFIG = 0x70
STRING_DATA = 0x71
I2C_REQUEST = 0x76
I2C_REPLY = 0x77
I2C_CONFIG = 0x78
REPORT_FIRMWARE = 0x79
SAMPLING_INTERVAL = 0x7A

# Per-pin terminator in a capability response, and the "no analog channel" marker
# in an analog-mapping response.
_CAPABILITY_END = 0x7F
_NO_ANALOG_CHANNEL = 0x7F

# Highest pin addressable by the short analog message (its channel is 4-bit);
# higher pins use the EXTENDED_ANALOG sysex instead.
_MAX_ANALOG_CHANNEL = 0x0F

# Servo pulse-width range, in microseconds (a 14-bit value over two 7-bit bytes).
_MAX_PULSE_WIDTH = 0x3FFF
# Servo angle range, in degrees, accepted by the Arduino Servo library.
_MAX_SERVO_ANGLE = 180

# I2C read/write modes, carried in bits 3-4 of the request's mode byte.
_I2C_WRITE = 0x00
_I2C_READ = 0x08
_I2C_READ_CONTINUOUSLY = 0x10
_I2C_STOP_READING = 0x18
# Bit 6 of the mode byte requests a restart (1) instead of a stop (0) after the write.
_I2C_RESTART_TX = 0x40

# Sampling interval, in milliseconds (a 14-bit value; the firmware floors it at 1).
_MIN_SAMPLING_INTERVAL = 1
_MAX_SAMPLING_INTERVAL = 0x3FFF

# Serial relay: the message byte packs an action (high nibble) with a port (low nibble).
_SERIAL_CONFIG = 0x10
_SERIAL_WRITE = 0x20
_SERIAL_READ = 0x30
_SERIAL_REPLY = 0x40
_SERIAL_CLOSE = 0x50
_SERIAL_READ_CONTINUOUS = 0x00
_SERIAL_STOP_READING = 0x01
_SERIAL_PORT_MASK = 0x0F
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
        self.firmware: tuple[int, int, str] | None = None
        self.capabilities: dict[int, list[int]] | None = None
        self.analog_mapping: dict[int, int] | None = None
        self.pin_states: dict[int, tuple[int, int]] = {}
        self.string: str | None = None
        self.serial_data: dict[int, list[int]] = {}
        self._command = 0
        self._channel = 0
        self._expected = 0
        self._data: list[int] = []
        self._in_sysex = False
        self._sysex: list[int] = []

    def reset(self) -> None:
        """Clear cached pin values and discovery results."""
        self.digital_inputs.clear()
        self.analog_values.clear()
        self.i2c_replies.clear()
        self.firmware = None
        self.capabilities = None
        self.analog_mapping = None
        self.pin_states.clear()
        self.string = None
        self.serial_data.clear()

    def take_i2c_reply(self, address: int, register: int) -> bytes | None:
        """Pop and return the latest I2C reply for an address/register, if any."""
        data = self.i2c_replies.pop((address, register), None)
        return None if data is None else bytes(data)

    def peek_i2c_reply(self, address: int, register: int) -> bytes | None:
        """Return the latest I2C reply for an address/register without consuming it."""
        data = self.i2c_replies.get((address, register))
        return None if data is None else bytes(data)

    def take_string(self) -> str | None:
        """Pop the latest string message from the board, if any."""
        message, self.string = self.string, None
        return message

    def drain_serial(self, port: int) -> bytes:
        """Return and clear the bytes buffered from a serial-relay port."""
        return bytes(self.serial_data.pop(port, []))

    def take_firmware(self) -> tuple[int, int, str] | None:
        """Pop the reported firmware (major, minor, name), if received."""
        firmware, self.firmware = self.firmware, None
        return firmware

    def take_capabilities(self) -> dict[int, list[int]] | None:
        """Pop the per-pin supported modes, if received."""
        capabilities, self.capabilities = self.capabilities, None
        return capabilities

    def take_analog_mapping(self) -> dict[int, int] | None:
        """Pop the pin-to-analog-channel mapping, if received."""
        mapping, self.analog_mapping = self.analog_mapping, None
        return mapping

    def take_pin_state(self, pin: int) -> tuple[int, int] | None:
        """Pop a pin's reported (mode, value), if received."""
        return self.pin_states.pop(pin, None)

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
        command, payload = self._sysex[0], self._sysex[1:]
        handler = self._SYSEX_HANDLERS.get(command)
        if handler is not None:
            handler(self, payload)

    def _store_i2c_reply(self, payload: list[int]) -> None:
        # Each original byte is sent as a 7-bit LSB/MSB pair; the first two decode
        # to the address and register, the rest are the data bytes.
        decoded = [payload[i] | (payload[i + 1] << 7) for i in range(0, len(payload) - 1, 2)]
        if len(decoded) >= 2:
            self.i2c_replies[(decoded[0], decoded[1])] = decoded[2:]

    def _store_firmware(self, payload: list[int]) -> None:
        if len(payload) >= 2:
            chars = payload[2:]
            name = "".join(
                chr(chars[i] | (chars[i + 1] << 7)) for i in range(0, len(chars) - 1, 2)
            )
            self.firmware = (payload[0], payload[1], name)

    def _store_capabilities(self, payload: list[int]) -> None:
        # Each pin lists (mode, resolution) pairs ending in 0x7F; pins are in order.
        capabilities: dict[int, list[int]] = {}
        modes: list[int] = []
        pin = index = 0
        while index < len(payload):
            if payload[index] == _CAPABILITY_END:
                capabilities[pin] = modes
                pin, modes, index = pin + 1, [], index + 1
            else:
                modes.append(payload[index])
                index += 2
        self.capabilities = capabilities

    def _store_analog_mapping(self, payload: list[int]) -> None:
        self.analog_mapping = {
            pin: channel
            for pin, channel in enumerate(payload)
            if channel != _NO_ANALOG_CHANNEL
        }

    def _store_pin_state(self, payload: list[int]) -> None:
        if len(payload) >= 2:
            value = 0
            for shift, byte in enumerate(payload[2:]):
                value |= byte << (7 * shift)
            self.pin_states[payload[0]] = (payload[1], value)

    def _store_string(self, payload: list[int]) -> None:
        self.string = "".join(
            chr(payload[i] | (payload[i + 1] << 7)) for i in range(0, len(payload) - 1, 2)
        )

    def _store_serial_reply(self, payload: list[int]) -> None:
        # payload[0] packs the reply action with the port; the rest are byte pairs.
        port = payload[0] & _SERIAL_PORT_MASK
        data = [payload[i] | (payload[i + 1] << 7) for i in range(1, len(payload) - 1, 2)]
        self.serial_data.setdefault(port, []).extend(data)

    _SYSEX_HANDLERS = {
        I2C_REPLY: _store_i2c_reply,
        REPORT_FIRMWARE: _store_firmware,
        CAPABILITY_RESPONSE: _store_capabilities,
        ANALOG_MAPPING_RESPONSE: _store_analog_mapping,
        PIN_STATE_RESPONSE: _store_pin_state,
        STRING_DATA: _store_string,
        SERIAL_MESSAGE: _store_serial_reply,
    }


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
        self._send(self._analog_message(pin, value))

    @staticmethod
    def _analog_message(pin: int, value: int) -> bytes:
        """Encode an analog write: the short message for pins 0-15, else EXTENDED_ANALOG."""
        lsb, msb = value & 0x7F, (value >> 7) & 0x7F
        if pin <= _MAX_ANALOG_CHANNEL:
            return bytes([ANALOG_MESSAGE | pin, lsb, msb])
        return bytes([START_SYSEX, EXTENDED_ANALOG, pin, lsb, msb, END_SYSEX])

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
        self._send(self._analog_message(pin, angle))

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
        """Read ``count`` bytes from an I2C device once, optionally from a register."""
        mode = _I2C_READ | (_I2C_RESTART_TX if restart else 0)
        self._send_i2c_read(address, mode, count, register)
        reply_register = register if register is not None else 0
        return self._await_reply(
            lambda: self._parser.take_i2c_reply(address, reply_register), "I2C reply"
        )

    def i2c_read_continuous(self, address: int, count: int, register: int | None = None) -> None:
        """Ask the device to keep reporting ``count`` bytes until stopped."""
        self._send_i2c_read(address, _I2C_READ_CONTINUOUSLY, count, register)

    def i2c_value(self, address: int, register: int | None = None) -> bytes | None:
        """Return the latest continuously-reported reply for a device, or None."""
        self._pump()
        return self._parser.peek_i2c_reply(address, register if register is not None else 0)

    def i2c_stop_reading(self, address: int) -> None:
        """Stop a continuous read previously started for a device."""
        self._check_i2c_address(address)
        self._send(bytes([START_SYSEX, I2C_REQUEST, address, _I2C_STOP_READING, END_SYSEX]))

    def _send_i2c_read(self, address: int, mode: int, count: int, register: int | None) -> None:
        self._check_i2c_address(address)
        if count < 0:
            raise InvalidValueError(f"I2C read count must be non-negative, got {count}")
        message = [START_SYSEX, I2C_REQUEST, address, mode]
        if register is not None:
            if not 0 <= register <= _I2C_BYTE_MAX:
                raise InvalidValueError(f"I2C register must be 0-{_I2C_BYTE_MAX}, got {register}")
            message += [register & 0x7F, (register >> 7) & 0x7F]
        message += [count & 0x7F, (count >> 7) & 0x7F, END_SYSEX]
        self._send(bytes(message))

    @staticmethod
    def _check_i2c_address(address: int) -> None:
        if not 0 <= address <= _I2C_ADDRESS_MAX:
            raise InvalidValueError(f"I2C address must be 0-{_I2C_ADDRESS_MAX}, got {address}")

    def sampling_interval(self, milliseconds: int) -> None:
        """Set how often the board auto-reports analog inputs and continuous I2C reads."""
        if not _MIN_SAMPLING_INTERVAL <= milliseconds <= _MAX_SAMPLING_INTERVAL:
            raise InvalidValueError(
                f"Sampling interval must be {_MIN_SAMPLING_INTERVAL}-{_MAX_SAMPLING_INTERVAL} ms, "
                f"got {milliseconds}"
            )
        self._send(
            bytes(
                [
                    START_SYSEX,
                    SAMPLING_INTERVAL,
                    milliseconds & 0x7F,
                    (milliseconds >> 7) & 0x7F,
                    END_SYSEX,
                ]
            )
        )

    def read_string(self) -> str | None:
        """Return the latest text message the board has sent, or None."""
        self._pump()
        return self._parser.take_string()

    def serial_config(
        self, port: int, baud: int, rx: int | None = None, tx: int | None = None
    ) -> None:
        """Open a serial-relay port at a baud rate (rx/tx pins for software serial)."""
        message = [
            START_SYSEX,
            SERIAL_MESSAGE,
            _SERIAL_CONFIG | (port & _SERIAL_PORT_MASK),
            baud & 0x7F,
            (baud >> 7) & 0x7F,
            (baud >> 14) & 0x7F,
        ]
        if rx is not None and tx is not None:
            message += [rx, tx]
        message.append(END_SYSEX)
        self._send(bytes(message))
        # Start relaying inbound bytes from the port back to the host.
        self._send(
            bytes(
                [
                    START_SYSEX,
                    SERIAL_MESSAGE,
                    _SERIAL_READ | (port & _SERIAL_PORT_MASK),
                    _SERIAL_READ_CONTINUOUS,
                    END_SYSEX,
                ]
            )
        )

    def serial_write(self, port: int, data: Iterable[int]) -> None:
        """Write bytes out of a serial-relay port."""
        message = [START_SYSEX, SERIAL_MESSAGE, _SERIAL_WRITE | (port & _SERIAL_PORT_MASK)]
        for value in data:
            message += [value & 0x7F, (value >> 7) & 0x7F]
        message.append(END_SYSEX)
        self._send(bytes(message))

    def serial_value(self, port: int) -> bytes:
        """Return and clear the bytes received on a serial-relay port."""
        self._pump()
        return self._parser.drain_serial(port & _SERIAL_PORT_MASK)

    def serial_close(self, port: int) -> None:
        """Close a serial-relay port."""
        self._send(
            bytes(
                [START_SYSEX, SERIAL_MESSAGE, _SERIAL_CLOSE | (port & _SERIAL_PORT_MASK), END_SYSEX]
            )
        )

    def report_firmware(self) -> tuple[int, int, str]:
        """Query the board's firmware name and (major, minor) version."""
        self._send(bytes([START_SYSEX, REPORT_FIRMWARE, END_SYSEX]))
        return self._await_reply(self._parser.take_firmware, "firmware report")

    def capability_query(self) -> dict[int, list[int]]:
        """Query the modes each pin supports (pin -> list of Firmata mode bytes)."""
        self._send(bytes([START_SYSEX, CAPABILITY_QUERY, END_SYSEX]))
        return self._await_reply(self._parser.take_capabilities, "capability response")

    def analog_mapping_query(self) -> dict[int, int]:
        """Query the pin-to-analog-channel mapping."""
        self._send(bytes([START_SYSEX, ANALOG_MAPPING_QUERY, END_SYSEX]))
        return self._await_reply(self._parser.take_analog_mapping, "analog mapping")

    def pin_state_query(self, pin: int) -> tuple[int, int]:
        """Query a pin's current (mode, value)."""
        self._send(bytes([START_SYSEX, PIN_STATE_QUERY, pin, END_SYSEX]))
        return self._await_reply(lambda: self._parser.take_pin_state(pin), "pin state")

    def _await_reply(self, getter: Callable[[], _T | None], what: str) -> _T:
        for _ in range(_MAX_REPLY_READS):
            chunk = self._driver.read(1)
            if not chunk:
                break
            self._parser.feed(chunk)
            result = getter()
            if result is not None:
                return result
        raise BoardConnectionError(f"No {what} received from the board")

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
