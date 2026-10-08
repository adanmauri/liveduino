# 0015. Python 3.13 is the minimum version

**Status:** Accepted · **Date:** 2026-10-08

## Context

The rewrite of June 2026 targeted Python 3.13 from the start: `requires-python = ">=3.13"`, the
type checkers and formatters set to 3.13, and 3.13 in `.python-version`. Frameduino ran on
Python 2. The code uses built-in generics, `X | None` and `Literal` types; as of this ADR it uses
no feature that needs 3.13 itself (no `type` aliases, no type parameter syntax, no `TypeIs`).

## Options

- **An older floor (3.10 or 3.11):** reaches older distributions and environments, at the cost of
  testing on more versions.
- **3.13:** one version to test and support, with no compatibility code.

## Decision

- `requires-python = ">=3.13"`, and the tooling targets 3.13 (Black, Ruff, mypy, Pyright).
- Code uses the syntax 3.13 allows; nothing guards for older versions.

## Consequences

### Positive

- One supported version to test, and no compatibility code.

### Negative / trade-offs

- Users on 3.12 or older cannot install liveduino.
- Lowering the floor later is possible while the code needs nothing from 3.13, but would need the
  tests on the new minimum.

### Follow-ups

- [`coding-standards.md`](../../.agents/rules/coding-standards.md) cites this ADR for the Python
  version.
