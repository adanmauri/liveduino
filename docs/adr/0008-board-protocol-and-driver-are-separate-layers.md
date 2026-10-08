# 0008. Board, protocol and driver are separate layers

**Status:** Accepted · **Date:** 2026-10-08

## Context

A board can be reached over USB serial, over TCP (StandardFirmataWiFi and
StandardFirmataEthernet) or over Bluetooth RFCOMM (HC-05, HC-06), and the same board could speak
a protocol other than Firmata: the Pinguino roadmap has considered a text interpreter
(`LiveProtocol`). Frameduino tied the board, the protocol and the USB channel together in one
class.

## Options

- **One class per board and transport:** direct, but the combinations multiply.
- **Board plus a transport, with Firmata built into the board:** fewer classes, but a second
  protocol means rewriting every board.
- **Three layers:** the board validates and exposes the API, a protocol client encodes what is
  said, a driver moves bytes; each can change without the others.

## Decision

```text
Board subclass (Arduino API, pin map, validation)
    → ProtocolClient (FirmataProtocol)
    → Driver (SerialDriver, TcpDriver, BluetoothDriver)
    → firmware on the board
```

- The **board** validates pins, modes and values before anything is sent, and raises the
  specific `liveduino.exceptions` error.
- The **protocol client** is a property of the board instance (`FirmataProtocol` by default,
  `ArduinoUno(protocol=...)` to override). It talks only to a `Driver`.
- The **driver** is how the board is connected: `connect(port)` builds a `SerialDriver`, or the
  caller passes `driver=TcpDriver(...)` or `driver=BluetoothDriver(...)`. Socket drivers share a
  `SocketDriver` base that buffers reads, so the synchronous Firmata pump works as over serial.
- No layer is skipped, and protocol bytes and driver internals never reach the public API.

## Consequences

### Positive

- A transport is one new `Driver`, and every board and protocol works over it.
- A protocol is one new `ProtocolClient`, with no change to the public API.
- Each layer is tested alone against mocks of the next (`tests/shared/`).

### Negative / trade-offs

- Every call crosses three objects, and a feature such as I2C touches all of them.
- `connect()` has to reject ambiguous combinations (a port and baud rate together with a driver).

### Follow-ups

- [`library-guardrails.md`](../../.agents/rules/library-guardrails.md) cites this ADR for the
  layers.
