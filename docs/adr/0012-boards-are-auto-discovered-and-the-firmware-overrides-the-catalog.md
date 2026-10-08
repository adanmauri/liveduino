# 0012. Boards are auto-discovered, and the firmware overrides the catalog

**Status:** Accepted · **Date:** 2026-10-08

## Context

Each board has its own pin map: digital and analog pins, PWM pins, analog-only channels (A6 and
A7 on the Nano), pins wired to onboard hardware (10-13 on the Arduino Ethernet). The catalog
started with the ATmega328 family and grows a board at a time. A board running StandardFirmata
can also report its real per-pin modes (`CAPABILITY_QUERY`), which may differ from the
datasheet: a minimal firmware, or a variant that reserves pins.

## Options

- **A hand-maintained registry:** explicit, but every new board edits a shared list.
- **Auto-discovery:** a board is a file; the registry imports the catalog package and registers
  every `Board` subclass it finds.
- **Pin map from the firmware only:** always accurate, but nothing can be validated before
  connecting, and a silent firmware leaves the board unusable.

## Decision

- Each board is a `Board` subclass in its own file under `src/liveduino/boards/catalog/`, with
  class attributes for its id, name and pin map. `boards/registry.py` imports every module there
  at import time and registers each subclass, for `connect("<id>", port)` and
  `available_boards()`. The catalog holds board definitions only.
- The catalog's pin map validates calls until the board answers. `capabilities()` then reads the
  firmware's per-pin modes once, caches them, and uses them over the catalog for that instance. If
  the firmware does not answer, it falls back to the catalog and asks again next time.

## Consequences

### Positive

- Adding a board is adding a file ([`docs/BOARDS.md`](../BOARDS.md)).
- Validation reflects the firmware actually running, and works before connecting.

### Negative / trade-offs

- Importing `liveduino.boards` imports the whole catalog.
- A bad file in the catalog breaks the import of every board.
- Validation can change after the first `capabilities()` call on a board whose firmware differs
  from its catalog entry.

### Follow-ups

- [`library-guardrails.md`](../../.agents/rules/library-guardrails.md) cites this ADR for the
  board catalog.
