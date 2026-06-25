"""Liveduino exception types.

Defines the exception hierarchy raised across the library. Every error derives
from ``LiveduinoError`` so callers can catch the whole family with a single
``except`` clause while still distinguishing specific failure modes.
"""


class LiveduinoError(Exception):
    """Base exception for liveduino errors.

    All exceptions raised by the library derive from this class, allowing
    callers to catch every liveduino-specific failure with a single handler.
    """


class BoardConnectionError(LiveduinoError):
    """Raised when board connection or communication fails.

    Covers failures opening the underlying driver, broken links, and attempts to
    talk to a board before it has been connected.
    """


class InvalidPinError(LiveduinoError):
    """Raised when a pin number is out of range for the board profile.

    The board validates pin arguments against its digital and analog pin maps
    and raises this error when a pin is unknown, reserved, or used for an
    unsupported function.
    """


class InvalidModeError(LiveduinoError):
    """Raised when pinMode receives an invalid mode constant.

    Only INPUT, OUTPUT, and INPUT_PULLUP are accepted; any other value triggers
    this error before a command is sent to the board.
    """


class InvalidValueError(LiveduinoError):
    """Raised when a digital or PWM value is out of range.

    Digital writes accept only LOW or HIGH, and analog (PWM) writes accept only
    values from 0 to 255; out-of-range values raise this error.
    """


class UnsupportedOperationError(LiveduinoError):
    """Raised when the active protocol does not support an Arduino operation.

    Some Arduino functions (tone, noTone, pulseIn, shiftOut, shiftIn) cannot be
    performed over StandardFirmata; calling them raises this error until a
    protocol implements them.
    """


class FlashError(LiveduinoError):
    """Raised when flashing firmware to the board fails.

    Covers malformed firmware files (bad Intel HEX) and bootloader programming
    failures such as losing sync, a rejected command, or a failed verification.
    """
