"""Unit tests for the discovery value types."""

from __future__ import annotations

import pytest

from liveduino.discovery import Capabilities, PinState, mode_name


@pytest.mark.unit
def test_mode_name_known_and_unknown() -> None:
    assert mode_name(0x00) == "INPUT"
    assert mode_name(0x03) == "PWM"
    assert mode_name(0xFF) == "0xFF"


@pytest.mark.unit
def test_pin_state_mode_name() -> None:
    assert PinState(pin=13, mode=0x01, value=1).mode_name == "OUTPUT"


@pytest.mark.unit
def test_capabilities_helpers() -> None:
    caps = Capabilities(modes={3: [0x00, 0x01, 0x03], 4: [0x00, 0x01]}, analog_channels={18: 4})
    assert caps.supports(3, 0x03) is True
    assert caps.supports(4, 0x03) is False
    assert caps.pins_supporting(0x03) == frozenset({3})
    assert caps.mode_names(3) == ["INPUT", "OUTPUT", "PWM"]
    assert caps.mode_names(99) == []
