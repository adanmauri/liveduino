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
| `wire` | Yes | Arduino `Wire` I2C interface (`begin`, `beginTransmission`/`write`/`endTransmission`, `requestFrom`/`available`/`read`) |
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

## Servo

StandardFirmata bundles the Arduino `Servo` library, so servos work with no extra setup.
`servoWrite(pin, angle)` attaches the servo and moves it (0-180°); `servoConfig` customises
the pulse-width range (µs) first if your servo needs it:

```python
board.servoWrite(9, 90)           # center a servo on pin 9
board.servoConfig(9, 600, 2400)   # optional: min/max pulse before writing
board.servoWrite(9, 180)
```

Servo works on any digital pin (including `A0`-`A5`), not only PWM pins.

## I2C (`board.wire`)

I2C is the Arduino `Wire` library, so liveduino exposes it as `board.wire` — the exact same
calls. A sketch ports almost verbatim; alias it once (`Wire = board.wire`, in place of
`#include <Wire.h>`) and the rest is identical:

```python
Wire = board.wire

Wire.begin()

# Wake an MPU-6050: write 0x00 into register 0x6B.
Wire.beginTransmission(0x68)
Wire.write(0x6B)
Wire.write(0x00)
Wire.endTransmission()

# Read 6 accelerometer bytes starting at register 0x3B.
Wire.requestFrom(0x68, 6, 0x3B)     # register overload -> one efficient transaction
values = []
while Wire.available():
    values.append(Wire.read())
```

| `Wire` method | Arduino | Notes |
| --- | --- | --- |
| `begin()` | `Wire.begin()` | Enable the bus |
| `beginTransmission(a)` / `write(b)` / `endTransmission()` | same | Buffered write; `endTransmission` returns `0` |
| `requestFrom(a, n)` | `Wire.requestFrom(a, n)` | Request `n` bytes; returns the count |
| `requestFrom(a, n, register)` | `Wire.requestFrom(a, n, iaddress, ...)` | Register read in one transaction |
| `requestFrom(a, n, sendStop=False)` | `Wire.requestFrom(..., false)` | Repeated start instead of stop |
| `available()` / `read()` | same | `read()` returns the next byte, or `-1` |

Addresses are 7-bit (`0`-`0x7F`), data bytes are `0`-`255`; 10-bit addressing is not
supported (a StandardFirmata limit). `endTransmission(stop)` accepts the `stop` flag for
compatibility but a write always ends with a stop, so for a guaranteed repeated-start
register read use `requestFrom(a, n, register, sendStop=False)`.

### Continuous reads (Firmata extension)

Arduino `Wire` has no equivalent: the board keeps reporting a register on its own (at the
`samplingInterval` rate) and you poll the latest value.

```python
board.wire.readContinuous(0x68, 6, register=0x3B)
data = board.wire.value(0x68, register=0x3B)   # latest block, or None yet
board.wire.stopReading(0x68)
```

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
can, then caches them** (they are never re-requested). Until the board can be queried — not
connected yet, or the firmware doesn't answer — it falls back to the class/catalog
definition as a bypass. Once cached, pin validation (digital / analog / PWM) follows the
board's own answer:

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

**Sampling interval.** Set how often the board auto-reports analog inputs and continuous
I2C reads (see [I2C continuous reads](#continuous-reads-firmata-extension)):

```python
board.samplingInterval(20)   # report every 20 ms
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

## Reset and unsupported functions

`board.reset()` returns the board to its power-on Firmata state (all pins to default,
reporting cleared) via SYSTEM_RESET.

`tone`, `noTone`, `pulseIn`, `shiftOut`, and `shiftIn` exist on `Board` for API fidelity but
raise `UnsupportedOperationError`: the Firmata protocol does not define them (they are in
neither StandardFirmata nor StandardFirmataPlus), so they would need custom firmware. See
[`docs/ARCHITECTURE.md`](ARCHITECTURE.md#not-supported-tone--pulsein--shift).

See also: [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) for how the API maps onto the protocol
and driver layers.
