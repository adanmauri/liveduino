# Command-line interface

Installing liveduino adds a `liveduino-cli` console command with a few helpers. It
is pure Python (no avrdude or Arduino toolchain) and uses the same `pyserial`
stack as the library.

```bash
liveduino-cli --help
liveduino-cli --version
```

## Flash firmware

`liveduino-cli flash` writes a firmware image to a board over its serial bootloader,
so you can upload StandardFirmata without the Arduino IDE. It speaks the STK500v1
protocol used by the Optiboot/Arduino bootloader, resetting the board through the
DTR/RTS auto-reset line.

The `board` is required and the `firmware` is optional (it defaults to the board's
primary firmware, i.e. serial StandardFirmata). By default the bundled image is
used, so it works offline with no extra files.

```bash
# flash the board's default firmware
liveduino-cli flash arduino:uno --port /dev/ttyACM0

# flash a specific bundled firmware variant
liveduino-cli flash arduino:ethernet StandardFirmataEthernet --port /dev/ttyACM0

# flash your own Intel HEX instead of a bundled image
liveduino-cli flash arduino:uno --port /dev/ttyACM0 --hex custom.hex
```

| Argument / option | Default | Description |
| --- | --- | --- |
| `board` | (required) | Board id, e.g. `arduino:uno` |
| `firmware` | board's primary | Bundled firmware name to flash (see `boards <board> firmwares`) |
| `--port PORT` | (required) | Serial port, e.g. `/dev/ttyACM0` or `COM3` |
| `--hex PATH` | bundled firmware | Intel HEX file to flash instead of a bundled image |
| `--baud N` | board default | Override the bootloader baud rate |
| `--no-verify` | off | Skip the read-back verification pass |

The board id selects the bundled firmware image and the bootloader settings (baud
rate and flash page size). Flashing targets the ATmega328 family (UNO, Nano, Mini,
Pro Mini, ...); other bootloaders (Caterina on the Leonardo/Micro, SAM-BA on the
MKR family) are not implemented yet.

The bundled images live in the `liveduino.firmware` package and are built by
`make firmware` (see [`docs/DEVELOPMENT.md`](DEVELOPMENT.md)) and the Firmware
GitHub workflow. If a board has no bundled image, or the requested firmware name
is not bundled, `flash` reports the available firmwares; pass `--hex` with a build
of your own.

## List boards and firmwares

```bash
liveduino-cli boards                            # list the boards in the catalog
liveduino-cli boards arduino:ethernet firmwares # list a board's bundled firmwares
```

`boards` prints every board id with its display name (the same ids used by
`connect("arduino:uno", port)`). Passing a board id lists the firmwares bundled for
it, marking the default; use those names as the `firmware` argument to `flash`.

## List serial ports

```bash
liveduino-cli ports
```

Prints the serial ports detected on the host, to help you find the right `--port`
value for `flash` or for connecting.

## Firmware variants

The Firmata family ships several firmware sketches. liveduino bundles and flashes
**StandardFirmata** by default, plus **StandardFirmataEthernet** for the Ethernet board.
liveduino's client speaks the base Firmata 2.x wire protocol, which all of these share for
core I/O, so it can talk to any StandardFirmata build already on your board.

| Firmware | Transport | Over StandardFirmata it adds | liveduino |
| --- | --- | --- | --- |
| **StandardFirmata** | Serial | digital/analog I/O, PWM, servo, I2C | ✅ default |
| **StandardFirmataPlus** | Serial | serial-device (UART/SoftwareSerial) support | not bundled |
| **StandardFirmataEthernet** | Ethernet (TCP) | network transport | ✅ bundled extra |
| **StandardFirmataWiFi** | Wi-Fi (TCP) | network transport (needs `wifiConfig.h`) | not bundled |
| **StandardFirmataBLE** | Bluetooth LE | BLE transport (needs config) | not bundled |
| **ConfigurableFirmata** | Serial / net | modular features: DHT, stepper, I2C, SPI, encoder | not bundled |

The richer variants (ConfigurableFirmata) add features that would need extra client support
before liveduino can drive them. Note `tone`/`pulseIn`/`shift` are in **none** of these — the
Firmata protocol does not define them (see [`ARCHITECTURE.md`](ARCHITECTURE.md#not-supported-tone--pulsein--shift)).
