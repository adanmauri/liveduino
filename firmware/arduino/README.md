# Arduino UNO firmware setup

Liveduino v0.1 uses **StandardFirmata** on the microcontroller. You do not need to flash custom liveduino firmware for Arduino boards in this release.

## Steps

1. Install the [Arduino IDE](https://www.arduino.cc/en/software).
2. Connect your Arduino UNO via USB.
3. Open **File → Examples → Firmata → StandardFirmata**.
4. Select the correct board and port under the **Tools** menu.
5. Click **Upload**.
6. Note the serial port:
   - Linux: usually `/dev/ttyACM0` or `/dev/ttyUSB0`
   - macOS: `/dev/cu.usbmodem*` or `/dev/tty.usbmodem*`
   - Windows: `COM3`, etc.

## Serial settings

- Default baud rate: **57600** (StandardFirmata default)
- Override in Python: `ArduinoUno().connect(port, baud=115200)` only if your sketch uses a different rate

## Verify

After upload, the board should accept Firmata commands immediately. Run a liveduino script or the integration test:

```bash
LIVEDUINO_PORT=/dev/ttyACM0 make test-integration
```

## Troubleshooting

- **Port busy**: close the Arduino IDE serial monitor before connecting from Python.
- **Permission denied (Linux)**: add your user to the `dialout` group or adjust udev rules.
- **Wrong port**: list ports with `python -m serial.tools.list_ports`.
