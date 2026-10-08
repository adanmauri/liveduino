# 0010. Timing runs on the host

**Status:** Accepted · **Date:** 2026-10-08

## Context

Arduino sketches use `delay`, `delayMicroseconds`, `millis` and `micros`, which run on the chip.
With liveduino the program runs on the host and the board only executes commands, and
StandardFirmata has no command to wait or to read the chip's clock. Frameduino and Johnny-Five
(the JavaScript equivalent) time on the host.

## Options

- **On the board:** the chip's own clock, but it needs firmware support that StandardFirmata does
  not have.
- **On the host:** the Python process sleeps and counts; nothing to add to the firmware.

## Decision

- `delay`, `delayMicroseconds`, `millis` and `micros` are `Board` methods that run in the host
  Python process. `millis` and `micros` count from the moment the board connection was created.
- The pure value helpers `map_range` and `constrain` are module-level functions, since they need
  no board.

## Consequences

### Positive

- Works over any firmware and any driver.
- A sketch's timing calls port unchanged.

### Negative / trade-offs

- Precision is the host's plus the link's latency: microsecond timing is not real time, and a
  `delay` between two writes does not guarantee the gap at the pins.
- `millis` restarts with each connection, not with the board's power-on.

### Follow-ups

- [`library-guardrails.md`](../../.agents/rules/library-guardrails.md) cites this ADR.
