# Arduino UNO firmware setup

Liveduino v0.1 uses **StandardFirmata** on the microcontroller. You do not need to write or
flash custom liveduino firmware for Arduino boards in this release, and **you do not need
the Arduino IDE**: liveduino flashes the firmware for you.

## Flash from the CLI (recommended)

liveduino ships a prebuilt StandardFirmata image for each board and flashes it over the
serial bootloader in pure Python (STK500v1, with DTR/RTS auto-reset). On the ATmega328
family (UNO, Nano, Mini, Pro Mini, ...) the whole setup is one command, **no Arduino IDE,
no avrdude, no `.hex` file, no toolchain**:

1. Connect your board via USB.
2. Find its serial port with `liveduino-cli ports`:
   - Linux: usually `/dev/ttyACM0` or `/dev/ttyUSB0`
   - macOS: `/dev/cu.usbmodem*` or `/dev/tty.usbmodem*`
   - Windows: `COM3`, etc.
3. Flash the bundled StandardFirmata:

```bash
liveduino-cli flash arduino:uno --port /dev/ttyACM0    # bundled StandardFirmata for the UNO
liveduino-cli flash arduino:nano --port /dev/ttyACM0
```

The bundled image works offline. Pass `--hex PATH` to flash your own image instead. See
[`docs/CLI.md`](../../docs/CLI.md) for every option.

## Flash from the Arduino IDE (optional)

Prefer the IDE, or on a board the CLI flasher does not target yet? You can upload
StandardFirmata by hand:

1. Install the [Arduino IDE](https://www.arduino.cc/en/software).
2. Connect your Arduino UNO via USB.
3. Open **File → Examples → Firmata → StandardFirmata**.
4. Select the correct board and port under the **Tools** menu.
5. Click **Upload**.

Either way, liveduino talks to whatever StandardFirmata build ends up on the board.

## Serial settings

- Default baud rate: **57600** (StandardFirmata default)
- Override in Python: `ArduinoUno().connect(port, baud=115200)` only if your sketch uses a different rate

## Other transports

Firmata is not tied to serial. To reach the board over a network instead of USB, upload a
network variant of the sketch and connect from Python with a `TcpDriver` (the protocol stays
the same, only the driver changes).

### Wi-Fi (StandardFirmataWiFi)

1. Open **File → Examples → Firmata → StandardFirmataWiFi**.
2. Edit `wifiConfig.h` with your SSID, security, and (optionally) a static IP and TCP port (default `3030`).
3. Select the board and **Upload**.
4. Connect from Python:

```python
from liveduino import ArduinoUno, TcpDriver

board = ArduinoUno().connect(driver=TcpDriver("192.168.1.50", 3030))
```

### Ethernet (StandardFirmataEthernet)

1. Open **File → Examples → Firmata → StandardFirmataEthernet**.
2. Edit the sketch with the board IP (and MAC if required) and TCP port (default `3030`).
3. Select the board and **Upload**.
4. Connect from Python the same way as Wi-Fi, using the board's Ethernet IP:

```python
board = ArduinoUno().connect(driver=TcpDriver("192.168.1.60", 3030))
```

### Bluetooth (classic / RFCOMM)

Classic Bluetooth modules (e.g. HC-05/HC-06, or the onboard radio of the Arduino BT) are
wired to the UART and act as a transparent serial bridge, so they use the plain
**StandardFirmata** sketch above, no special variant. Connect with a `BluetoothDriver`
instead of the serial port. `StandardFirmataBLE` is for Bluetooth Low Energy and is not
supported yet (no BLE driver).

See [`docs/CONNECTIONS.md`](../../docs/CONNECTIONS.md) for the driver details.

## Verify

After upload, the board should accept Firmata commands immediately. Run a liveduino script or the integration test:

```bash
LIVEDUINO_PORT=/dev/ttyACM0 make test-integration
```

## Troubleshooting

- **Port busy**: close the Arduino IDE serial monitor before connecting from Python.
- **Permission denied (Linux)**: add your user to the `dialout` group or adjust udev rules.
- **Wrong port**: list ports with `python -m serial.tools.list_ports`.
