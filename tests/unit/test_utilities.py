"""Unit tests for Arduino value utilities."""

import pytest

from liveduino.utilities import constrain, map_range


@pytest.mark.unit
def test_map_range_scales_value() -> None:
    assert map_range(512, 0, 1023, 0, 255) == 127


@pytest.mark.unit
def test_map_range_equal_input_range_returns_out_min() -> None:
    assert map_range(10, 5, 5, 0, 255) == 0


@pytest.mark.unit
def test_constrain_clamps_value() -> None:
    assert constrain(1500, 0, 1023) == 1023
    assert constrain(-1, 0, 1023) == 0
    assert constrain(500, 0, 1023) == 500
