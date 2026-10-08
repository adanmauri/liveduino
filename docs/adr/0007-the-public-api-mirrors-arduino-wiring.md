# 0007. The public API mirrors Arduino/Wiring

**Status:** Accepted · **Date:** 2026-10-08

## Context

Liveduino is the successor of Frameduino (2014, Python 2, Pinguino only), rewritten from scratch
in June 2026. Its users are people who already write Arduino sketches and want to drive a board
live from Python, without the compile and upload loop. Python libraries for the same job, such as
pyFirmata and Telemetrix, each define their own API, and MicroPython moves the code onto the chip
with a different language and runtime.

## Options

- **A Pythonic API** (`board.pin(13).write(True)`, snake_case): familiar to Python developers,
  but a new API to learn for Arduino users, and every sketch needs translating.
- **Pin objects, as in pyFirmata:** compact, but another library-specific model.
- **The Arduino/Wiring API itself:** the names, argument order and semantics Arduino users know,
  at the cost of camelCase methods that Python linters flag.

## Decision

The public API is the Arduino/Wiring API:

- Board methods keep Arduino's camelCase names, argument order and semantics: `pinMode`,
  `digitalWrite`, `digitalRead`, `analogRead`, `analogWrite`, `servoWrite`, `tone`, `pulseIn`,
  `shiftOut`, and the rest.
- Constants mirror Arduino (`INPUT`, `OUTPUT`, `INPUT_PULLUP`, `HIGH`, `LOW`, `LSBFIRST`,
  `MSBFIRST`, `A0`-`A20`), typed with `Literal` aliases (`PinMode`, `DigitalValue`, `BitOrder`).
- Arduino objects keep their shape: I2C is `board.wire`, Arduino's `Wire`, and nothing else (a
  batched `i2c*` API was removed for that reason); a serial relay port is `board.serial(n)`,
  Arduino's `HardwareSerial`.
- Discovery methods that Arduino lacks (`capabilities`, `pinState`, `status`, `info`) follow the
  same camelCase style and name pin modes the Arduino way (`'INPUT'`, `'PWM'`), never as protocol
  bytes.
- The API is published on PyPI and does not break.

## Consequences

### Positive

- An Arduino user needs nothing new, and a sketch ports almost line for line.
- The Arduino reference is the specification: a behavior question has an answer outside this
  repository.

### Negative / trade-offs

- camelCase method and argument names go against PEP 8: Pylint's `invalid-name` is disabled in
  `pyproject.toml`.
- An operation the protocol cannot perform still has to exist
  ([ADR-0011](0011-unsupported-operations-keep-their-arduino-signature-and-raise.md)).
- A Pythonic convenience that Arduino lacks needs a reason to exist.

### Follow-ups

- [`library-guardrails.md`](../../.agents/rules/library-guardrails.md) cites this ADR for API
  fidelity.
