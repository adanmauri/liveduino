"""Arduino/Wiring value types.

Typed aliases and helpers for the values accepted by the board API: pin modes,
digital levels, and bit orders are expressed as ``Literal`` types, while analog
pin constants are modelled by the board-agnostic ``AnalogPin`` identifier.
"""

from dataclasses import dataclass
from typing import Literal

# INPUT | OUTPUT | INPUT_PULLUP
PinMode = Literal[0, 1, 2]
# LOW | HIGH
DigitalValue = Literal[0, 1]
# LSBFIRST | MSBFIRST
BitOrder = Literal[0, 1]


@dataclass(frozen=True)
class AnalogPin:
    """Board-agnostic analog pin identifier (A0-A20) carrying only its channel.

    The numeric pin of A0 differs per board (14 on the ATmega328 family, 54 on
    the Mega, ...), so the constant stores just the channel and each board maps
    it to a concrete digital pin or analog channel.
    """
    channel: int

    def __repr__(self) -> str:
        return f"A{self.channel}"


# A pin argument accepted by the board API: a raw pin/channel number or an analog constant.
PinArg = int | AnalogPin
