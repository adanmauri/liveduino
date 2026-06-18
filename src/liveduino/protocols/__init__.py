"""Protocol adapters.

Public entry point for the protocol layer: re-exports the ``ProtocolClient``
protocol and the concrete protocol implementations available to boards.
"""

from liveduino.protocols.base import ProtocolClient
from liveduino.protocols.firmata import FirmataProtocol

__all__ = ["FirmataProtocol", "ProtocolClient"]
