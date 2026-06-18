"""Arduino/Wiring constants."""

from typing import Final

from liveduino.types import AnalogPin

INPUT: Final = 0
OUTPUT: Final = 1
INPUT_PULLUP: Final = 2
LOW: Final = 0
HIGH: Final = 1
LSBFIRST: Final = 0
MSBFIRST: Final = 1

# Analog input pin constants. These are board-agnostic: each carries only its
# analog channel, and the board maps it to the right digital pin / channel
# (e.g. A0 is digital pin 14 on the ATmega328 family, 54 on the Mega).
A0: Final = AnalogPin(0)
A1: Final = AnalogPin(1)
A2: Final = AnalogPin(2)
A3: Final = AnalogPin(3)
A4: Final = AnalogPin(4)
A5: Final = AnalogPin(5)
A6: Final = AnalogPin(6)
A7: Final = AnalogPin(7)
A8: Final = AnalogPin(8)
A9: Final = AnalogPin(9)
A10: Final = AnalogPin(10)
A11: Final = AnalogPin(11)
A12: Final = AnalogPin(12)
A13: Final = AnalogPin(13)
A14: Final = AnalogPin(14)
A15: Final = AnalogPin(15)
A16: Final = AnalogPin(16)
A17: Final = AnalogPin(17)
A18: Final = AnalogPin(18)
A19: Final = AnalogPin(19)
A20: Final = AnalogPin(20)
