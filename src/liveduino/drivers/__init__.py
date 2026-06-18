"""Driver layer: byte channels to the board (serial, TCP, Bluetooth).

Public entry point for the driver layer: re-exports the ``Driver`` protocol and
the concrete drivers used to connect a board over different transports.
"""

from liveduino.drivers.base import Driver
from liveduino.drivers.bluetooth import BluetoothDriver
from liveduino.drivers.serial import SerialDriver
from liveduino.drivers.socket_driver import SocketDriver
from liveduino.drivers.tcp import TcpDriver

__all__ = [
    "BluetoothDriver",
    "Driver",
    "SerialDriver",
    "SocketDriver",
    "TcpDriver",
]
