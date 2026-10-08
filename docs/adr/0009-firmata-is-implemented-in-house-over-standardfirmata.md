# 0009. Firmata is implemented in-house, over StandardFirmata

**Status:** Accepted · **Date:** 2026-10-08

## Context

Driving a board live needs firmware that executes commands sent from the host. StandardFirmata
ships with the Arduino IDE and already covers digital and analog I/O, PWM, servo, I2C, a serial
relay and discovery queries. Python clients exist (pyFirmata, Telemetrix), but each brings its own
API and dependencies, and Telemetrix needs its own firmware.

## Options

- **A custom firmware and protocol:** full control, but a firmware to build, flash and maintain
  per board, and users cannot reuse a board that already runs StandardFirmata.
- **StandardFirmata through a third-party client:** less code here, but that library's API,
  release cycle and dependencies come along, under liveduino's own API.
- **StandardFirmata through an in-house client:** the Firmata 2.x wire protocol encoded and
  decoded here, over a `Driver`.

## Decision

- Boards run **stock StandardFirmata** (and its Wi-Fi, Ethernet and Plus variants); liveduino
  ships no custom firmware for Arduino boards.
- `FirmataProtocol` implements the Firmata 2.x wire protocol itself: messages, sysex, a small
  synchronous parser pumped on each read, and the whole StandardFirmata surface (digital and
  analog I/O, extended analog for pins above 15, servo, I2C with continuous reads, serial relay,
  sampling interval, string messages, discovery queries, system reset).
- No third-party Firmata library is added.

## Consequences

### Positive

- A board that already runs StandardFirmata works as is; one without it gets flashed by liveduino
  ([ADR-0014](0014-firmware-is-bundled-and-flashed-in-pure-python.md)).
- No runtime dependency for the protocol
  ([ADR-0013](0013-the-runtime-depends-only-on-the-standard-library-and-pyserial.md)), and
  behavior is under this repository's tests.

### Negative / trade-offs

- The protocol code is maintained here, including its bugs: PWM above pin 15 needed
  `EXTENDED_ANALOG`, fixed in 0.2.0.
- What Firmata does not define, liveduino cannot do over it
  ([ADR-0011](0011-unsupported-operations-keep-their-arduino-signature-and-raise.md)).

### Follow-ups

- [`library-guardrails.md`](../../.agents/rules/library-guardrails.md) cites this ADR.
