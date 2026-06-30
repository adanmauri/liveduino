"""In-memory ProtocolClient stand-in for unit tests.

Provides a ``ProtocolClient`` implementation that records calls and stores pin
state in memory, letting board-level unit tests run without a real protocol or
driver.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from liveduino.types import BitOrder, DigitalValue, PinMode

if TYPE_CHECKING:
    from collections.abc import Iterable


class MockProtocol:
    """In-memory ProtocolClient stand-in for unit tests.

    Records every protocol call and keeps the latest pin modes and values in
    memory so board-level tests can assert on the commands the board issued.
    """
    def __init__(self) -> None:
        self.connected = False
        self.modes: dict[int, int] = {}
        self.digital: dict[int, DigitalValue] = {}
        self.analog: dict[int, int] = {}
        self.pwm: dict[int, int] = {}
        self.servo: dict[int, int] = {}
        self.i2c_reply: bytes = b""
        self.firmware: tuple[int, int, str] = (2, 5, "StandardFirmata")
        self.capabilities: dict[int, list[int]] = {}
        self.analog_mapping: dict[int, int] = {}
        self.pin_states: dict[int, tuple[int, int]] = {}
        self.pulse: int = 0
        self.shifted: int = 0
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    def connect(self) -> None:
        self.connected = True

    def disconnect(self) -> None:
        self.connected = False

    def pin_mode(self, pin: int, mode: PinMode) -> None:
        self.calls.append(("pin_mode", (pin, mode)))
        self.modes[pin] = mode

    def digital_write(self, pin: int, value: DigitalValue) -> None:
        self.calls.append(("digital_write", (pin, value)))
        self.digital[pin] = value

    def digital_read(self, pin: int) -> DigitalValue:
        self.calls.append(("digital_read", (pin,)))
        return self.digital.get(pin, 0)

    def analog_read(self, pin: int) -> int:
        self.calls.append(("analog_read", (pin,)))
        return self.analog.get(pin, 0)

    def analog_write(self, pin: int, value: int) -> None:
        self.calls.append(("analog_write", (pin, value)))
        self.pwm[pin] = value

    def servo_config(self, pin: int, min_pulse: int, max_pulse: int) -> None:
        self.calls.append(("servo_config", (pin, min_pulse, max_pulse)))

    def servo_write(self, pin: int, angle: int) -> None:
        self.calls.append(("servo_write", (pin, angle)))
        self.servo[pin] = angle

    def i2c_config(self, delay: int = 0) -> None:
        self.calls.append(("i2c_config", (delay,)))

    def i2c_write(self, address: int, data: Iterable[int]) -> None:
        self.calls.append(("i2c_write", (address, tuple(data))))

    def i2c_read(
        self, address: int, count: int, register: int | None = None, *, restart: bool = False
    ) -> bytes:
        self.calls.append(("i2c_read", (address, count, register, restart)))
        return self.i2c_reply

    def report_firmware(self) -> tuple[int, int, str]:
        self.calls.append(("report_firmware", ()))
        return self.firmware

    def capability_query(self) -> dict[int, list[int]]:
        self.calls.append(("capability_query", ()))
        return self.capabilities

    def analog_mapping_query(self) -> dict[int, int]:
        self.calls.append(("analog_mapping_query", ()))
        return self.analog_mapping

    def pin_state_query(self, pin: int) -> tuple[int, int]:
        self.calls.append(("pin_state_query", (pin,)))
        return self.pin_states.get(pin, (0, 0))

    def tone(self, pin: int, frequency: int, duration: int | None) -> None:
        self.calls.append(("tone", (pin, frequency, duration)))

    def no_tone(self, pin: int) -> None:
        self.calls.append(("no_tone", (pin,)))

    def pulse_in(self, pin: int, value: DigitalValue, timeout: int) -> int:
        self.calls.append(("pulse_in", (pin, value, timeout)))
        return self.pulse

    def shift_out(self, data_pin: int, clock_pin: int, bit_order: BitOrder, value: int) -> None:
        self.calls.append(("shift_out", (data_pin, clock_pin, bit_order, value)))

    def shift_in(self, data_pin: int, clock_pin: int, bit_order: BitOrder) -> int:
        self.calls.append(("shift_in", (data_pin, clock_pin, bit_order)))
        return self.shifted
