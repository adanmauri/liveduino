# Arduino API

Public board methods use **camelCase** to match Arduino/Wiring exactly.

| Method | On hardware? | What it does |
| --- | :---: | --- |
| `pinMode(pin, mode)` | Yes | Set pin to `INPUT`, `OUTPUT`, or `INPUT_PULLUP` |
| `digitalWrite(pin, value)` | Yes | Drive a digital pin `HIGH` / `LOW` |
| `digitalRead(pin)` | Yes | Read a digital pin |
| `analogRead(pin)` | Yes | Read an analog channel (`0`-`1023`) |
| `analogWrite(pin, value)` | Yes | PWM duty cycle (`0`-`255`) on a PWM pin |
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

See also: [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) for how the API maps onto the protocol
and driver layers.
