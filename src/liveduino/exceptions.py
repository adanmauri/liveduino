"""Liveduino exception types."""


class LiveduinoError(Exception):
    """Base exception for liveduino errors."""


class BoardConnectionError(LiveduinoError):
    """Raised when board connection or communication fails."""


class InvalidPinError(LiveduinoError):
    """Raised when a pin number is out of range for the board profile."""


class InvalidModeError(LiveduinoError):
    """Raised when pinMode receives an invalid mode constant."""


class InvalidValueError(LiveduinoError):
    """Raised when a digital or PWM value is out of range."""


class UnsupportedOperationError(LiveduinoError):
    """Raised when the active protocol does not support an Arduino operation."""
