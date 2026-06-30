"""Board discovery value types.

Structured results for the Firmata discovery queries exposed by ``Board``:
``info`` (firmware and identity), ``capabilities`` (per-pin supported modes),
and ``status`` / ``pinState`` (live pin mode and value).
"""

from __future__ import annotations

from dataclasses import dataclass

# Firmata pin-mode bytes.
MODE_INPUT = 0x00
MODE_OUTPUT = 0x01
MODE_ANALOG = 0x02
MODE_PWM = 0x03
MODE_SERVO = 0x04
MODE_I2C = 0x06
MODE_PULLUP = 0x0B

# Human-readable names for the Firmata pin modes, for readable output.
MODE_NAMES = {
    MODE_INPUT: "INPUT",
    MODE_OUTPUT: "OUTPUT",
    MODE_ANALOG: "ANALOG",
    MODE_PWM: "PWM",
    MODE_SERVO: "SERVO",
    0x05: "SHIFT",
    MODE_I2C: "I2C",
    0x07: "ONEWIRE",
    0x08: "STEPPER",
    0x09: "ENCODER",
    0x0A: "SERIAL",
    MODE_PULLUP: "PULLUP",
}


def mode_name(mode: int) -> str:
    """Return the human-readable name for a Firmata pin-mode byte."""
    return MODE_NAMES.get(mode, f"0x{mode:02X}")


@dataclass(frozen=True)
class BoardInfo:
    """Static identity of a connected board: its model and flashed firmware."""

    id: str
    name: str
    firmware: str
    firmware_version: str


@dataclass(frozen=True)
class PinState:
    """A pin's current mode and value, as reported by the board."""

    pin: int
    mode: int
    value: int

    @property
    def mode_name(self) -> str:
        """Human-readable name of this pin's current mode."""
        return mode_name(self.mode)


@dataclass(frozen=True)
class Capabilities:
    """Per-pin modes the board reports it supports, plus the analog channel map."""

    modes: dict[int, list[int]]
    analog_channels: dict[int, int]

    def supports(self, pin: int, mode: int) -> bool:
        """Return True if ``pin`` supports the given Firmata mode byte."""
        return mode in self.modes.get(pin, [])

    def pins_supporting(self, mode: int) -> frozenset[int]:
        """Return the set of pins that support a given Firmata mode byte."""
        return frozenset(pin for pin, modes in self.modes.items() if mode in modes)

    def mode_names(self, pin: int) -> list[str]:
        """Return the human-readable mode names a pin supports."""
        return [mode_name(mode) for mode in self.modes.get(pin, [])]


@dataclass(frozen=True)
class BoardStatus:
    """Live snapshot of a board: its identity plus every queried pin's state."""

    connected: bool
    info: BoardInfo
    pins: dict[int, PinState]
