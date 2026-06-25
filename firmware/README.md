# Firmware

liveduino drives the board over **StandardFirmata**, the firmware that already ships with
the Arduino IDE. You do not need to write or compile any custom firmware, and in most cases
you do not need to flash it by hand either: liveduino bundles a prebuilt StandardFirmata
image per board and flashes it for you in pure Python.

```bash
liveduino-cli flash arduino:uno --port /dev/ttyACM0   # bundled StandardFirmata, no Arduino IDE
```

This folder holds the per-board setup guides. The bundled `.hex` images themselves live in
the [`liveduino.firmware`](../src/liveduino/firmware) package and are built by `make
firmware` (see [`docs/DEVELOPMENT.md`](../docs/DEVELOPMENT.md)).

## Guides

| Guide | Contents |
| --- | --- |
| [`arduino/README.md`](arduino/README.md) | Arduino UNO and compatibles: flash from the CLI or the Arduino IDE, serial settings, Wi-Fi / Ethernet / Bluetooth variants, troubleshooting |

## See also

- [`docs/CLI.md`](../docs/CLI.md) for the full `liveduino-cli flash` reference (variants, custom `.hex`, options).
- [`docs/CONNECTIONS.md`](../docs/CONNECTIONS.md) for reaching the board over serial, TCP, or Bluetooth.
- [`docs/BOARDS.md`](../docs/BOARDS.md) for the supported boards and how to add one.
