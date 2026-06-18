"""In-memory ProtocolClient stand-in for unit tests.

Provides a ``ProtocolClient`` implementation that records calls and stores pin
state in memory, letting board-level unit tests run without a real protocol or
driver.
"""

from __future__ import annotations

from typing import Any

from liveduino.types import BitOrder, DigitalValue, PinMode


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
