# Supported boards

| Board | Status | Protocol | Firmware |
| --- | --- | --- | --- |
| Arduino UNO | Supported | Firmata | StandardFirmata |
| Nano | Supported | Firmata | StandardFirmata |
| Mini | Supported | Firmata | StandardFirmata |
| Pro Mini | Supported | Firmata | StandardFirmata |
| Fio | Supported | Firmata | StandardFirmata |
| Duemilanove | Supported | Firmata | StandardFirmata |
| Diecimila | Supported | Firmata | StandardFirmata |
| Ethernet | Supported | Firmata | StandardFirmata |
| BT | Supported | Firmata | StandardFirmata |
| LilyPad | Supported | Firmata | StandardFirmata |
| UNO Mini | Supported | Firmata | StandardFirmata |
| Mega | Planned | Firmata | StandardFirmata |
| Mega ADK | Planned | Firmata | StandardFirmata |
| Leonardo | Planned | Firmata | StandardFirmata |
| Micro | Planned | Firmata | StandardFirmata |
| UNO WiFi Rev2 | Planned | Firmata | StandardFirmataWiFi |
| MKR1000 | Planned | Firmata | StandardFirmataWiFi |
| MKR WiFi 1010 | Planned | Firmata | StandardFirmataWiFi |
| Nano 33 IoT | Planned | Firmata | StandardFirmataWiFi |
| Pinguino | Planned | LiveProtocol | Live interpreter (Frameduino-style) |

All ids use the `arduino:<model>` form (e.g. `arduino:nano`, `arduino:pro`,
`arduino:diecimila`). Each board profile only declares its pin map and
capabilities; the protocol (Firmata) and driver (serial/TCP/Bluetooth) are shared.

The Firmware column lists the sketch `liveduino-cli flash` bundles and writes over the serial
bootloader, so it is the serial StandardFirmata image. A board may also ship extra firmware
variants: the Ethernet board additionally bundles a `StandardFirmataEthernet` image (built by
`make firmware`) for the network transport. To use it, reflash that image (its baked-in IP
may need editing) and connect with a `TcpDriver`; see
[`firmware/arduino/README.md`](../firmware/arduino/README.md).

```python
from liveduino import connect

board = connect("arduino:uno", "/dev/ttyACM0")
```

## Adding a board

Board profiles are auto-discovered: drop a `Board` subclass file under
`src/liveduino/boards/catalog/` and it is registered for `connect("<id>", port)` and
`available_boards()` without editing the registry. Subclasses just set class attributes:
pin map and capabilities (`id`, `name`, `digital_pins`, `analog_pins`, `pwm_pins`, ...) and,
for bundled firmware, the build metadata (`fqbn`, `firmware_sketch`, and optional
`firmware_sketches` for extra variants). See
[`docs/ARCHITECTURE.md`](ARCHITECTURE.md) for the analog pin model and board catalog
details.
