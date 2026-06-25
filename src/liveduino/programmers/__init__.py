"""Programmer layer: flash firmware to the board over its bootloader.

Public entry point for the programmer layer: re-exports the Intel HEX parser and
the concrete programmers used to write firmware to a board without an external
toolchain. Programmers talk to the bootloader, independently of the runtime
protocol (Firmata) used once the firmware is running.
"""

from liveduino.programmers.firmware import available_firmwares, load_bundled_firmware
from liveduino.programmers.intel_hex import parse_intel_hex
from liveduino.programmers.stk500v1 import Stk500v1Programmer

__all__ = [
    "Stk500v1Programmer",
    "available_firmwares",
    "load_bundled_firmware",
    "parse_intel_hex",
]
