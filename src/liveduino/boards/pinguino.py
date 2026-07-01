"""Shared pin profiles for 8-bit Pinguino (PIC18F) boards.

These are provisional per-package fallbacks. The ``PinguinoFirmata`` firmware
answers the Firmata capability query, so ``board.capabilities()`` reads each
board's real pin map from the hardware and uses it over these values — verify
against your board's Pinguino pinout if you rely on the fallback.

This module lives outside ``boards/catalog/`` so the registry does not scan it;
catalog board files import these constants.
"""

# 28-pin PIC18F (2455 / 2550 / 2553 / 25K50 / 26J50 / 27J53).
DIGITAL_28 = range(19)
ANALOG_28 = range(10)

# 40/44-pin PIC18F (4455 / 4550 / 4553 / 45K50 / 46J50 / 47J53).
DIGITAL_40 = range(30)
ANALOG_40 = range(13)

# 20-pin PIC18F (14K50).
DIGITAL_20 = range(15)
ANALOG_20 = range(11)

# CCP (PWM) pins in Pinguino numbering (provisional).
PWM_TWO = frozenset({11, 12})
PWM_ONE = frozenset({11})

# USB CDC ignores the baud rate, but the driver needs one.
PINGUINO_BAUD = 115200
