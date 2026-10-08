# 0016. Pinguino boards speak Firmata

**Status:** Proposed · **Date:** 2026-10-08

## Context

Frameduino drove Pinguino boards (8-bit PIC18F) with a text command interpreter running on the
chip (`pinguino/usb_interpreter.pde`). Liveduino's roadmap first planned to modernize it as
`LiveProtocol`: a text protocol with explicit framing and a `LIVE V1` handshake, behind a new
`ProtocolClient`. The `experimental` branch tries another approach: `PinguinoFirmata`, a firmware
for 8-bit Pinguino that implements the StandardFirmata surface, plus thirteen PIC18F boards in the
catalog. It is untested on hardware.

## Options

- **`LiveProtocol`:** a text protocol readable in a terminal and designed for this library, but a
  second protocol client to write and test, and a firmware with no other users.
- **`PinguinoFirmata`:** the existing `FirmataProtocol` drives Pinguino with no new client, and
  every Firmata feature carries over, but a Firmata firmware has to be written and kept compatible
  for PIC18F.

## Decision

Proposed: Pinguino boards run `PinguinoFirmata` and liveduino drives them with `FirmataProtocol`,
as on the `experimental` branch. This ADR becomes Accepted when that work merges to `main`, after a
run on a real Pinguino board.

## Consequences

### Positive

- No new protocol client: Pinguino gets the same API and features as Arduino boards
  ([ADR-0008](0008-board-protocol-and-driver-are-separate-layers.md)).

### Negative / trade-offs

- Pinguino boards are flashed with Pinguino's own tools; the bundled-firmware path
  ([ADR-0014](0014-firmware-is-bundled-and-flashed-in-pure-python.md)) does not cover them.
- The firmware must keep up with StandardFirmata's behavior on a different chip family.

### Follow-ups

- Validate `PinguinoFirmata` on hardware before merging `experimental`.
- `docs/ARCHITECTURE.md` (Future: Pinguino) describes both approaches until then.
