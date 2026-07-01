"""Board discovery value types.

Structured results for the board discovery queries: ``info`` (firmware and
identity), ``capabilities`` (per-pin supported modes, by name), and ``status`` /
``pinState`` (live pin mode and value). Pin modes are exposed as Arduino-style
names (``"INPUT"``, ``"PWM"``, ``"SERVO"``, ...), never as raw protocol bytes.
"""

from __future__ import annotations

from dataclasses import dataclass

# Firmata pin-mode bytes mapped to their Arduino-style names. The public API
# speaks names; the raw bytes stay inside the protocol layer.
_MODE_NAMES = {
    0x00: "INPUT",
    0x01: "OUTPUT",
    0x02: "ANALOG",
    0x03: "PWM",
    0x04: "SERVO",
    0x05: "SHIFT",
    0x06: "I2C",
    0x07: "ONEWIRE",
    0x08: "STEPPER",
    0x09: "ENCODER",
    0x0A: "SERIAL",
    0x0B: "PULLUP",
}


def mode_name(mode: int) -> str:
    """Translate a Firmata pin-mode byte to its Arduino-style name."""
    return _MODE_NAMES.get(mode, f"0x{mode:02X}")


@dataclass(frozen=True)
class BoardInfo:
    """Static identity of a connected board: its model and flashed firmware."""

    id: str
    name: str
    firmware: str
    firmwareVersion: str


@dataclass(frozen=True)
class PinState:
    """A pin's current mode (by name) and value, as reported by the board."""

    pin: int
    mode: str
    value: int


@dataclass(frozen=True)
class Capabilities:
    """Per-pin modes a board supports, by name, plus the analog channel map."""

    modes: dict[int, list[str]]
    analogChannels: dict[int, int]

    def supports(self, pin: int, mode: str) -> bool:
        """Return True if ``pin`` supports the named mode (e.g. ``"PWM"``)."""
        return mode in self.modes.get(pin, [])

    def pinsSupporting(self, mode: str) -> frozenset[int]:
        """Return the set of pins that support a named mode."""
        return frozenset(pin for pin, modes in self.modes.items() if mode in modes)


@dataclass(frozen=True)
class BoardStatus:
    """Live snapshot of a board: its identity plus every queried pin's state."""

    connected: bool
    info: BoardInfo
    pins: dict[int, PinState]
