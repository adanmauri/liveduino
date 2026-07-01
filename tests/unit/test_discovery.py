"""Unit tests for the discovery value types."""

from __future__ import annotations

import pytest

from liveduino.discovery import Capabilities, PinState, mode_name


@pytest.mark.unit
def test_mode_name_known_and_unknown() -> None:
    assert mode_name(0x04) == "SERVO"
    assert mode_name(0x03) == "PWM"
    assert mode_name(0xFF) == "0xFF"


@pytest.mark.unit
def test_pin_state_holds_named_mode() -> None:
    assert PinState(pin=13, mode="OUTPUT", value=1).mode == "OUTPUT"


@pytest.mark.unit
def test_capabilities_helpers() -> None:
    caps = Capabilities(
        modes={3: ["INPUT", "OUTPUT", "PWM"], 4: ["INPUT", "OUTPUT"]},
        analogChannels={18: 4},
    )
    assert caps.supports(3, "PWM") is True
    assert caps.supports(4, "PWM") is False
    assert caps.pinsSupporting("PWM") == frozenset({3})
