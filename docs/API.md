# Arduino API

Public board methods use **camelCase** to match Arduino/Wiring exactly.

| Method | On hardware? | What it does |
| --- | :---: | --- |
| `pinMode(pin, mode)` | Yes | Set pin to `INPUT`, `OUTPUT`, or `INPUT_PULLUP` |
| `digitalWrite(pin, value)` | Yes | Drive a digital pin `HIGH` / `LOW` |
| `digitalRead(pin)` | Yes | Read a digital pin |
| `analogRead(pin)` | Yes | Read an analog channel (`0`-`1023`) |
| `analogWrite(pin, value)` | Yes | PWM duty cycle (`0`-`255`) on a PWM pin |
| `servoWrite(pin, angle)` | Yes | Attach a servo and move it to an angle (`0`-`180`°) |
| `servoConfig(pin, minPulse, maxPulse)` | Yes | Set a servo's min/max pulse width (µs) before writing |
| `i2cConfig(delay=0)` | Yes | Enable the I2C bus (optional read delay in µs) |
| `i2cWrite(address, data)` | Yes | Write bytes to a 7-bit I2C address |
| `i2cRead(address, count, register=None, *, restart=False)` | Yes | Read `count` bytes, optionally from a register |
| `i2cReadContinuous(address, count, register=None)` | Yes | Keep reporting a register until stopped |
| `i2cValue(address, register=None)` | Yes | Latest continuously-reported reply (or `None`) |
| `i2cStopReading(address)` | Yes | Stop a continuous read |
| `samplingInterval(ms)` | Yes | How often the board auto-reports analog / continuous I2C |
| `readString()` | Yes | Latest text message from the board (e.g. an error), or `None` |
| `serial(port)` | Yes | A serial-relay port (Arduino `Serial1`/`Serial2`/...) |
| `reset()` | Yes | Reset the board's Firmata state (pins default, reporting off) |
| `info()` | Yes | Firmware name/version + board identity (`BoardInfo`) |
| `capabilities()` | Once | Per-pin supported modes; reads the firmware once and caches, else catalog (`Capabilities`) |
| `pinState(pin)` | Yes | A pin's current mode and value (`PinState`) |
| `status()` | Yes | Live snapshot of every pin (`BoardStatus`) |
| `delay` / `delayMicroseconds` | Host | Block on the Python host |
| `millis` / `micros` | Host | Elapsed time since the connection was created |
| `tone` / `noTone` / `pulseIn` / `shiftOut` / `shiftIn` | n/a | Defined for fidelity; raise `UnsupportedOperationError` under StandardFirmata |

Host-side timing runs on the Python process, mirroring the Arduino sketch API. The pure
value helpers `map_range` and `constrain` are module-level functions
(`from liveduino import map_range, constrain`).

## Analog pins

Analog pins use the Arduino `A0`-`A20` constants. They are board-agnostic (each carries
only its analog channel), so the same `A0` works on any board and the board maps it to the
right pin. `analogRead(A0)` equals `analogRead(0)`, and where the hardware allows it
`A0`-`A5` double as digital pins (`pinMode(A0, OUTPUT)`); analog-only channels reject
digital use.

```python
from liveduino import A0

val = board.analogRead(A0)  # same as analogRead(0); returns 0-1023
```

## I2C

StandardFirmata bundles the Arduino `Wire` library, so liveduino can act as an I2C master
over the same connection. Enable the bus once with `i2cConfig`, then read and write.

**Is it the same as Arduino?** Not byte-for-byte. Arduino models I2C as a stateful `Wire`
object (`beginTransmission` / `write` / `endTransmission`, then `requestFrom` / `read`).
liveduino exposes a higher-level, batched API over Firmata instead. The behaviour maps
directly:

| Arduino `Wire` | liveduino | Notes |
| --- | --- | --- |
| `Wire.begin()` | `board.i2cConfig()` | Call once before any transfer |
| `Wire.beginTransmission(a)` → `write(b)`… → `endTransmission()` | `board.i2cWrite(a, [b, …])` | One batched write |
| `Wire.requestFrom(a, n)` → `read()`… | `board.i2cRead(a, n)` | Returns `bytes` |
| write register, then `requestFrom` | `board.i2cRead(a, n, register=r)` | Register read in one call |
| `endTransmission(false)` (repeated start) | `board.i2cRead(a, n, restart=True)` | Restart instead of stop |

`address` is a 7-bit address (`0`-`0x7F`), data bytes are `0`-`255`, and 10-bit addressing
is not supported (a StandardFirmata limitation).

### Enable the bus

```python
board.i2cConfig()       # like Wire.begin()
board.i2cConfig(1000)   # optional: 1000 µs delay between a write and the following read
```

### Write

```python
# Wake an MPU-6050: write 0x00 into the power-management register 0x6B.
board.i2cWrite(0x68, [0x6B, 0x00])
```

### Read

```python
# Plain read of 2 bytes (device's current register pointer).
raw = board.i2cRead(0x68, 2)            # -> b'\x12\x34'

# Read 6 bytes starting at register 0x3B (MPU-6050 accelerometer block).
accel = board.i2cRead(0x68, 6, register=0x3B)

# Repeated-start read (no stop between the register write and the read).
data = board.i2cRead(0x68, 2, register=0x3B, restart=True)
```

`i2cRead` blocks until the board sends the matching I2C reply and returns it as `bytes`; it
raises `BoardConnectionError` if no reply arrives.

### Arduino `Wire`-style API

If you prefer the exact Arduino `Wire` calls, use `board.wire`. It mirrors the stateful
`Wire` library line for line, so a sketch ports almost verbatim:

| Method | Arduino equivalent | What it does |
| --- | --- | --- |
| `board.wire.begin()` | `Wire.begin()` | Enable the bus |
| `board.wire.beginTransmission(addr)` | `Wire.beginTransmission(addr)` | Start buffering a write |
| `board.wire.write(byte_or_bytes)` | `Wire.write(...)` | Queue one byte or a sequence |
| `board.wire.endTransmission()` | `Wire.endTransmission()` | Send the buffer; returns `0` |
| `board.wire.requestFrom(addr, n)` | `Wire.requestFrom(addr, n)` | Request `n` bytes; returns the count |
| `board.wire.available()` | `Wire.available()` | Bytes left to read |
| `board.wire.read()` | `Wire.read()` | Next byte, or `-1` when empty |

```python
# Read 6 accelerometer bytes from an MPU-6050, Arduino style.
board.wire.begin()

board.wire.beginTransmission(0x68)
board.wire.write(0x3B)              # point at register 0x3B
board.wire.endTransmission()

board.wire.requestFrom(0x68, 6)
values = []
while board.wire.available():
    values.append(board.wire.read())
```

For an even closer port, alias it once and your code reads exactly like an Arduino sketch —
`Wire = board.wire` stands in for `#include <Wire.h>`, and the rest is identical:

```python
Wire = board.wire          # in place of: #include <Wire.h>

Wire.begin()
Wire.beginTransmission(0x68)
Wire.write(0x3B)
Wire.endTransmission()
Wire.requestFrom(0x68, 6)
while Wire.available():
    value = Wire.read()
```

Caveats versus real Arduino: addresses are 7-bit only, and `endTransmission(stop)` accepts
the `stop` flag for compatibility but StandardFirmata always ends a write with a stop, so a
guaranteed repeated-start register read is best done with `i2cRead(addr, n, register=r,
restart=True)`.

## Discovery

StandardFirmata can describe itself, so you can ask a connected board who it is, what each
pin can do, and what state the pins are in right now.

```python
board.info()        # -> BoardInfo(id='arduino:uno', name='Arduino UNO',
                    #              firmware='StandardFirmata', firmwareVersion='2.5')

board.pinState(13)  # -> PinState(pin=13, mode='OUTPUT', value=1)

board.status()      # -> BoardStatus(connected=True, info=..., pins={pin: PinState, ...})
```

Modes are Arduino-style names (`'INPUT'`, `'OUTPUT'`, `'PWM'`, `'SERVO'`, `'ANALOG'`,
`'I2C'`, `'PULLUP'`, ...), never raw protocol bytes.

**`capabilities()` reads the board's real capabilities from the firmware the first time it
can, then caches them** (they are never re-requested). Before the board is reachable it
falls back to the class/catalog definition as a bypass. Once cached, pin validation
(digital / analog / PWM) follows the board's own answer:

```python
caps = board.capabilities()      # firmware if reachable (cached), else the catalog
caps.supports(9, 'SERVO')        # does pin 9 support servo?
caps.pinsSupporting('PWM')       # -> frozenset of PWM-capable pins
caps.modes[3]                    # -> ['INPUT', 'OUTPUT', 'PULLUP', 'PWM']

board.analogWrite(3, 128)        # allowed only if the board reports PWM on pin 3
```

`Capabilities` is a simple record:

```python
@dataclass(frozen=True)
class Capabilities:
    modes: dict[int, list[str]]        # pin -> the mode names it supports
    analogChannels: dict[int, int]     # pin -> its analog channel index
    def supports(self, pin: int, mode: str) -> bool: ...
    def pinsSupporting(self, mode: str) -> frozenset[int]: ...
```

`BoardInfo`, `PinState`, `Capabilities`, and `BoardStatus` are importable from `liveduino`.
Each query is one round-trip; `status()` queries every pin.

## Streaming and serial

**Continuous I2C.** Instead of a request per read, ask the board to keep reporting a register
and poll the latest value. The report rate follows `samplingInterval`:

```python
board.samplingInterval(20)                     # report every 20 ms
board.i2cReadContinuous(0x68, 6, register=0x3B)
data = board.i2cValue(0x68, register=0x3B)     # latest block, or None yet
board.i2cStopReading(0x68)
```

**Board messages.** StandardFirmata sends text (e.g. `"I2C: Too many bytes received"`) as
string messages; `readString()` returns the latest, or `None`:

```python
message = board.readString()
```

**Serial relay.** Bridge a UART device wired to one of the board's extra serial ports
(hardware `Serial1`/`Serial2`/`Serial3`, or software serial with rx/tx pins). The port
object mirrors Arduino's `HardwareSerial`:

```python
gps = board.serial(1)          # Arduino Serial1
gps.begin(9600)
gps.write(b"$PMTK605*31\r\n")
while gps.available():
    byte = gps.read()          # next byte, or -1 when empty
gps.end()
```

Serial relay needs a board with spare UARTs (e.g. a Mega) or a software-serial capable pin
pair; a plain UNO only has the USB serial.

See also: [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) for how the API maps onto the protocol
and driver layers.
