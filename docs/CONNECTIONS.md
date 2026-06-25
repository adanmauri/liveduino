# Connections

Liveduino implements the StandardFirmata protocol natively over a pluggable **driver** (the
channel), so the same board API works over any medium. The **protocol** is chosen when you
create the board (default: Firmata); the **driver** is how you connect it. Serial is the
default.

```python
from liveduino import ArduinoUno, TcpDriver, BluetoothDriver

# USB serial (default)
board = ArduinoUno().connect("/dev/ttyACM0")

# Wi-Fi / Ethernet (StandardFirmataWiFi/Ethernet)
board = ArduinoUno().connect(driver=TcpDriver("192.168.1.50", 3030))

# Bluetooth RFCOMM (e.g. HC-05/HC-06; Linux AF_BLUETOOTH sockets)
board = ArduinoUno().connect(driver=BluetoothDriver("AA:BB:CC:DD:EE:FF"))
```

Override the protocol at instantiation for a board flashed with different firmware:
`ArduinoUno(protocol=MyProtocol).connect("/dev/ttyACM0")`.

## Drivers

| Driver | Channel | Notes |
| --- | --- | --- |
| `SerialDriver` | USB/UART serial | Default; built by `connect(port)` (pyserial) |
| `TcpDriver` | TCP (Wi-Fi/Ethernet) | For StandardFirmataWiFi/Ethernet; `TcpDriver(host, port)` |
| `BluetoothDriver` | Bluetooth RFCOMM | Linux `AF_BLUETOOTH` sockets (stdlib), e.g. HC-05/HC-06 |

`TcpDriver` and `BluetoothDriver` share a `SocketDriver` base that buffers non-blocking
socket reads so the synchronous Firmata pump works the same as over serial. See
[`docs/ARCHITECTURE.md`](ARCHITECTURE.md) for the full driver design.
