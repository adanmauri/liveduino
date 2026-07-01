# PinguinoFirmata (8-bit / PIC18F)

A StandardFirmata-compatible firmware for 8-bit Pinguino (PIC18F) boards. It
implements the **Firmata 2.x wire protocol** on top of the Pinguino API, so
liveduino's native `FirmataProtocol` talks to a Pinguino exactly as it does to an
Arduino UNO — **no client changes**, just a Pinguino board entry in the catalog.

Firmata is a protocol, not an Arduino-only thing: it is a small set of bytes over
serial. This sketch reimplements that protocol using Pinguino's own
`pinMode` / `digitalWrite` / `analogRead` / `analogWrite`, so the same host code
drives a PIC.

## What it supports

Aims for the full StandardFirmata surface, so liveduino's whole Arduino API works:

- Digital I/O with per-port reporting; analog input with per-channel reporting
- PWM and **servo** (`servoWrite` / `servoConfig`), including **extended analog** (pins > 15)
- **I2C** master (config, write, one-shot read)
- **Discovery**: `REPORT_FIRMWARE`, `CAPABILITY_QUERY`, `ANALOG_MAPPING_QUERY`,
  `PIN_STATE_QUERY` — so `board.capabilities()` reads the real pin map from the hardware
- `SAMPLING_INTERVAL`, `STRING_DATA`, `SYSTEM_RESET`

Not yet implemented: **continuous I2C** and the **serial relay** (needs a 2nd UART, which
most 8-bit Pinguinos lack). liveduino degrades gracefully without them.

## Works on any 8-bit PIC18F

This firmware is **not 4550-specific** — it is parameterized. To target another PIC18F
(e.g. 2550, 25K50, 4455), adjust the `TOTAL_PINS` / `TOTAL_PORTS` / `TOTAL_ANALOG` /
`ANALOG_BASE` defines and the `isPwmPin()` helper for that chip's CCP pins, and pick the
serial backend (USB CDC vs UART). Then add a matching `Board` subclass in the catalog
(the `Pinguino4550` file is the template). The firmware's capability query means the exact
pin map in the catalog is only a fallback.

## Flash it

Open `PinguinoFirmata.pde` in the **Pinguino IDE** (8-bit / PIC18F), pick your board,
and upload with the Pinguino bootloader (liveduino's pure-Python flasher is STK500v1
and does **not** flash PIC — use Pinguino's own tools). Once flashed, the board shows
up as a USB CDC (or UART) serial port and speaks Firmata.

## Adapt before flashing

Two things depend on your board:

1. **Serial backend.** The `fm_available` / `fm_read` / `fm_write` helpers default to
   USB CDC (`CDC.*`, for PIC18F2550/4550). For a UART board, switch them to `Serial.*`.
2. **Pin counts.** Set `TOTAL_PINS`, `TOTAL_PORTS`, and `TOTAL_ANALOG` for your PIC18F
   model (defaults are sized for a 2550/4550-class board).

## Talk to it from liveduino

`FirmataProtocol` already speaks this. You still need a Pinguino `Board` subclass in
`src/liveduino/boards/catalog/` declaring the board's pin map (`digital_pins`,
`analog_pins`, `pwm_pins`, `first_analog_pin`) and `default_baud`; then:

```python
board = PinguinoNN().connect("/dev/ttyACM0")   # USB CDC serial port
board.pinMode(13, OUTPUT)
board.digitalWrite(13, HIGH)
```

> **Untested on hardware.** This firmware is written against the Pinguino API but has
> not been compiled or run on a board here; verify on a real PIC18F Pinguino and
> adjust the serial backend / pin counts as needed.
