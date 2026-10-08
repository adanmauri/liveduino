# 0011. Unsupported operations keep their Arduino signature and raise

**Status:** Accepted · **Date:** 2026-10-08

## Context

`tone`, `noTone`, `pulseIn`, `shiftOut` and `shiftIn` are part of the Arduino API
([ADR-0007](0007-the-public-api-mirrors-arduino-wiring.md)), but the Firmata protocol does not
define them: they are absent from StandardFirmata and StandardFirmataPlus alike. Supporting them
needs custom firmware with a sysex per function, plus the matching client code.

## Options

- **Leave them out:** an honest API surface, but the API stops being Arduino's, and code fails
  with `AttributeError`.
- **Emulate them on the host** (toggle a pin for `tone`, poll for `pulseIn`): available, but the
  link's latency makes the result wrong, silently.
- **Keep them, and raise a specific error:** the API stays complete, and the limit is explicit.

## Decision

- The methods exist on `Board` with Arduino's signatures, validate their arguments like any other
  call, and delegate to the protocol client.
- A protocol that cannot perform an operation raises `UnsupportedOperationError`;
  `FirmataProtocol` does so for these five. `NotImplementedError` stays for abstract methods and
  unimplemented protocols.
- Supporting them is a roadmap item (`TODO.md`): custom firmware or a future protocol implements
  them without a change to the public API.

## Consequences

### Positive

- The public API does not change when a protocol learns an operation.
- Code fails loudly, with an error that says why, instead of producing wrong timing.

### Negative / trade-offs

- The API advertises five methods that always fail today.

### Follow-ups

- [`library-guardrails.md`](../../.agents/rules/library-guardrails.md) cites this ADR.
