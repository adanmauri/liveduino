# Live Wiring commands from Python

**Liveduino** lets you control microcontroller boards from Python using the exact same API as the Arduino/Wiring language. It's interactive, like a REPL or shell for your board: every `pinMode`, `digitalWrite`, or `analogRead` you call is sent and executed on the hardware right away — no compile, no upload, no flashing. Type a command in a Python shell and the LED blinks; read a pin and you get the live value back. This realtime, line-by-line control is the original [Frameduino](legacy/) vision, now for Python 3.13 and multiple boards.

This is **not** MicroPython (Python on the chip), **not** a sketch compiler, and **not** a new API like pyFirmata's pin objects. If you know Arduino, you already know liveduino.

## Quick start

### 1. Firmware (Arduino UNO)

Upload **StandardFirmata** from the Arduino IDE: File → Examples → Firmata → StandardFirmata. See [firmware/arduino/README.md](firmware/arduino/README.md).

### 2. Install

```bash
pip install liveduino
# or
uv add liveduino
```

### 3. Blink from Python

```python
from liveduino import ArduinoUno, OUTPUT, HIGH, LOW

board = ArduinoUno().connect("/dev/ttyACM0")  # or COM3 on Windows
board.pinMode(13, OUTPUT)

while True:
    board.digitalWrite(13, HIGH)
    board.delay(1000)
    board.digitalWrite(13, LOW)
    board.delay(1000)
```

Timing functions (`delay`, `delayMicroseconds`, `millis`, `micros`) are board
methods that run on the host, mirroring the Arduino sketch API.

```python
from liveduino import A0

val = board.analogRead(A0)  # same as analogRead(0); returns 0-1023
board.close()
```

Analog pins use the Arduino `A0`-`A20` constants. They are board-agnostic
(each carries only its analog channel), so the same `A0` works on any board and
the board maps it to the right pin. `analogRead(A0)` equals `analogRead(0)`, and
where the hardware allows it `A0`-`A5` double as digital pins
(`pinMode(A0, OUTPUT)`); analog-only channels like `A6`-`A7` reject digital use.

## What it is / what it is not

| | Liveduino | pyFirmata / Telemetrix | MicroPython |
|---|-----------|------------------------|-------------|
| API style | Arduino/Wiring (`pinMode`, `digitalWrite`) | Library-specific | Python on device |
| Code runs on | Host Python | Host Python | Microcontroller |
| Firmware | StandardFirmata (UNO MVP) | Firmata / custom | MicroPython |
| Learning curve for Arduino users | Zero | New API | New language |

## Supported boards

| Board | Status | Protocol |
|-------|--------|----------|
| Arduino UNO | MVP | StandardFirmata over USB serial |
| Nano, Mini, Pro/Pro Mini, Fio | Supported | StandardFirmata (8 analog channels) |
| Duemilanove/Diecimila, Ethernet, BT, LilyPad, NG, UNO Mini | Supported | StandardFirmata (6 analog channels) |
| Mega/Mega ADK, Leonardo, Micro | Planned | Firmata |
| Pinguino | Planned | LiveProtocol (Frameduino-style) |

All `id`s use the `arduino:<model>` form (e.g. `arduino:nano`, `arduino:pro`,
`arduino:diecimila`, `arduino:atmegang`). Each board profile only declares its
pin map and capabilities; the protocol (Firmata) and driver (serial/TCP/Bluetooth)
are shared.

Generic connection:

```python
from liveduino import connect

board = connect("arduino:uno", "/dev/ttyACM0")
```

## Connections (serial, WiFi, Bluetooth)

Liveduino implements the StandardFirmata protocol natively over a pluggable
**driver** (the channel), so the same board API works over any medium. The
**protocol** is chosen when you create the board (default: Firmata); the
**driver** is how you connect it. Serial is the default driver.

```python
from liveduino import ArduinoUno, TcpDriver, BluetoothDriver

# USB serial (default)
board = ArduinoUno().connect("/dev/ttyACM0")

# Wi-Fi / Ethernet (StandardFirmataWiFi/Ethernet)
board = ArduinoUno().connect(driver=TcpDriver("192.168.1.50", 3030))

# Bluetooth RFCOMM (e.g. HC-05/HC-06; Linux AF_BLUETOOTH sockets)
board = ArduinoUno().connect(driver=BluetoothDriver("AA:BB:CC:DD:EE:FF"))
```

The protocol defaults per board (Firmata), but you can override it at
instantiation for a board flashed with different firmware:
`ArduinoUno(protocol=MyProtocol).connect("/dev/ttyACM0")`.

## Development

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

```bash
uv python pin 3.13
uv sync --all-groups
make install-dev
make test-coverage
```

Integration tests (real hardware):

```bash
LIVEDUINO_PORT=/dev/ttyACM0 make test-integration
```

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Legacy

Frameduino 0.x (Python 2, Pinguino-only) is preserved under [legacy/](legacy/).

## License

MIT — see [LICENSE](LICENSE).
