# Liveduino architecture

Liveduino is a layered Python library that exposes the Arduino/Wiring API while delegating driver (channel) and protocol details to pluggable backends.

## Layers

```
User API (Board subclass: ArduinoUno.pinMode, digitalWrite, …)
    → ProtocolClient (FirmataProtocol, future LiveProtocol)
    → Driver (SerialDriver, TcpDriver, BluetoothDriver, …)
    → Microcontroller firmware
```

Two clearly separated concerns:

- **Protocol** = *what* is spoken (Firmata) → `FirmataProtocol`.
- **Driver** = *where* it connects, i.e. the byte channel (serial, TCP, Bluetooth) → `SerialDriver`, `TcpDriver`, `BluetoothDriver`.

`FirmataProtocol` is a **native** StandardFirmata client: it encodes/decodes the
Firmata 2.x wire protocol itself over a `Driver` byte stream (no third-party
Firmata library). The user **never** sees Firmata bytes; they are an
implementation detail inside `FirmataProtocol`.

Because the protocol only talks to a `Driver`, the same StandardFirmata board
works over USB serial, TCP/WiFi, or Bluetooth RFCOMM just by swapping the
driver.

## Packages

| Path | Role |
|------|------|
| `src/liveduino/constants.py` | Arduino constants (`HIGH`, `LOW`, `INPUT`, …, and analog pins `A0`-`A7`) |
| `src/liveduino/types.py` | Arduino value types (`PinMode`, `DigitalValue`, `BitOrder`) |
| `src/liveduino/utilities.py` | Host value utilities (`map_range`, `constrain`) |
| `src/liveduino/boards/board.py` | `Board` abstract base class (Arduino API incl. host timing, pin map, capabilities, `connect`) |
| `src/liveduino/boards/catalog/` | One `Board` subclass per board (e.g. `ArduinoUno`), auto-discovered |
| `src/liveduino/boards/registry.py` | Auto-discovery + lookup (`get_board`, `available_boards`) |
| `src/liveduino/protocols/` | Protocol clients (native `FirmataProtocol` today; `LiveProtocol` for Pinguino later) |
| `src/liveduino/drivers/` | Byte channels: `SerialDriver`, `TcpDriver`, `BluetoothDriver` (shared `SocketDriver` base) |
| `src/liveduino/connection.py` | Factory `connect("arduino:uno", port)` |
| `firmware/` | Setup docs and future MCU firmware (Pinguino live interpreter) |
| `legacy/` | Frameduino 0.x Python 2 code and original Pinguino `.pde` |

## MVP data flow (Arduino UNO)

1. `ArduinoUno()` picks the board's protocol (`FirmataProtocol` by default; override at instantiation with `ArduinoUno(protocol=...)`). `.connect(port)` then builds a `SerialDriver(port)` — or uses the `driver=TcpDriver(...)` / `driver=BluetoothDriver(...)` you pass — wraps it in the chosen protocol, and opens the connection. The **protocol** is a property of the board instance; the **driver** is how it is connected.
2. `board.pinMode(13, OUTPUT)` validates pin 13 against the `ArduinoUno` pin map, then calls `protocol.pin_mode`.
3. `FirmataProtocol` encodes a `SET_PIN_MODE` Firmata message and writes the bytes to the driver. Inbound digital/analog reports are decoded by a small synchronous parser pumped on each read.
4. StandardFirmata on the UNO executes the command on the hardware.

## Host-side time

`board.delay()`, `board.delayMicroseconds()`, `board.millis()`, and `board.micros()` run on the **host Python process**, not on the microcontroller — matching Frameduino and Johnny-Five semantics. `millis`/`micros` count from the moment the board connection was created. The pure value helpers `map_range` and `constrain` are module-level functions (`from liveduino import map_range, constrain`).

## Analog pins

Analog pins follow the Arduino `A0`-`A7` constants, modelled as a small
board-agnostic `AnalogPin` value type that carries only the analog channel
(`A0` is channel 0, …). The numeric digital pin of `A0` is board-specific
(14 on the ATmega328 family, 54 on the Mega), so each board resolves the
constant itself: `analogRead` reads `AnalogPin.channel`, while digital ops
(`pinMode`/`digitalWrite`/…) translate it to a physical pin via
`first_analog_pin` (`first_analog_pin + channel`). `analogRead` also accepts a
raw channel (`analogRead(0)` == `analogRead(A0)`). Channels listed in
`analog_only_pins` (e.g. `{6, 7}` on the 8-channel Nano/Mini/Pro Mini/Fio)
reject digital use. A board with a non-contiguous analog map can override the
translation without touching the public API or the constants.

Boards may also declare `reserved_pins`: digital pins wired to onboard hardware
(e.g. pins 10-13 on the Arduino Ethernet, used by the W5100 over SPI). Any I/O
on a reserved pin (digital or PWM) raises `InvalidPinError`.

## Device functions and StandardFirmata limits

`tone`, `noTone`, `pulseIn`, `shiftOut`, and `shiftIn` exist on `Board` for API fidelity, but StandardFirmata cannot perform them, so `FirmataProtocol` raises `UnsupportedOperationError`. A future `LiveProtocol` (or custom firmware) can implement them without changing the public API.

## Drivers

| Driver | Channel | Notes |
|--------|---------|-------|
| `SerialDriver` | USB/UART serial | Default; built by `connect(port)` (pyserial) |
| `TcpDriver` | TCP (WiFi/Ethernet) | For StandardFirmataWiFi/Ethernet; `TcpDriver(host, port)` |
| `BluetoothDriver` | Bluetooth RFCOMM | Linux `AF_BLUETOOTH` sockets (stdlib), e.g. HC-05/HC-06 |

`TcpDriver` and `BluetoothDriver` share a `SocketDriver` base that buffers non-blocking socket reads so the synchronous Firmata pump works the same as over serial.

## Future: Pinguino

Pinguino boards will use **LiveProtocol**: a text command interpreter evolved from `legacy/pinguino/usb_interpreter.pde`, with explicit framing and a `LIVE V1` handshake. The same `Board` API will apply; a Pinguino board subclass just overrides `protocol_factory` to build the new protocol client.

## Testing

- **Unit tests** (`tests/unit/`, `@pytest.mark.unit`): mocks only, no hardware.
- **Integration tests** (`tests/integration/`, `@pytest.mark.integration`): require `LIVEDUINO_PORT` and StandardFirmata on the board.

Coverage gate: 100% line coverage on `src/liveduino/` via `make test-coverage`.
