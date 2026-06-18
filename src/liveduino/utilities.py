"""Host-side Arduino value utilities.

Pure value helpers that mirror Arduino math functions (``map`` and
``constrain``) but run on the Python host instead of the microcontroller. They
have no I/O side effects and operate solely on integers.
"""

from __future__ import annotations


def map_range(value: int, in_min: int, in_max: int, out_min: int, out_max: int) -> int:
    """Map a value from one numeric range to another (Arduino map semantics)."""
    if in_min == in_max:
        return out_min
    return (value - in_min) * (out_max - out_min) // (in_max - in_min) + out_min


def constrain(value: int, low: int, high: int) -> int:
    """Constrain a value to lie between low and high inclusive."""
    if value < low:
        return low
    if value > high:
        return high
    return value
