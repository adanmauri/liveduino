# 0013. The runtime depends only on the standard library and pyserial

**Status:** Accepted · **Date:** 2026-10-08

## Context

Liveduino installs into its users' environments: scripts, notebooks, test rigs, data pipelines.
Each runtime dependency is one more version to resolve against theirs. The library needs a serial
port, TCP sockets, Bluetooth RFCOMM sockets, the Firmata protocol, an Intel HEX parser and an
STK500v1 programmer.

## Options

- **Use a package for each need** (a Firmata client, a Bluetooth library, an HEX parser, avrdude):
  less code here, more to resolve and keep up with.
- **The standard library, plus pyserial for the serial port:** the standard library has no
  portable serial API, and pyserial is the de facto one.

## Decision

- The only runtime dependency is `pyserial`, declared with a compatible range (`pyserial>=3.5`).
- Everything else uses the standard library: TCP through `socket`, Bluetooth through Linux
  `AF_BLUETOOTH` RFCOMM sockets, Firmata in-house
  ([ADR-0009](0009-firmata-is-implemented-in-house-over-standardfirmata.md)), the HEX parser and
  the STK500v1 programmer in-house
  ([ADR-0014](0014-firmware-is-bundled-and-flashed-in-pure-python.md)).
- A new runtime dependency needs the maintainer's approval.

## Consequences

### Positive

- `pip install liveduino` pulls one package, with no compiled extensions.
- Fewer upstream changes can break the library.

### Negative / trade-offs

- `BluetoothDriver` works on Linux only, where the standard library has `AF_BLUETOOTH`.
- BLE needs a library (`bleak`); it is on the roadmap (`TODO.md`) and would need that approval.

### Follow-ups

- [`coding-standards.md`](../../.agents/rules/coding-standards.md) (dependencies) and
  [`library-guardrails.md`](../../.agents/rules/library-guardrails.md) cite this ADR.
