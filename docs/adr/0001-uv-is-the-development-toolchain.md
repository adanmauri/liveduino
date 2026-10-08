# 0001. uv is the development toolchain

**Status:** Accepted · **Date:** 2026-10-08

## Context

Liveduino has used uv since the rewrite from Frameduino: `pyproject.toml`, `uv.lock` and the
`Makefile` all go through it, and the publish workflow builds and uploads with `uv build` and
`uv publish`. The decision was never written down, and the development tools sat in a single
`dev` group, so every CI job installed every linter and test tool whatever it needed.

## Options

- **pip and `requirements*.txt`:** universal, but no lock with hashes per platform and no
  interpreter management.
- **Poetry or Pipenv:** a lock, but a second tool next to the one the project already uses.
- **uv, with dependency groups per job:** one tool for interpreters, environments, locking,
  building and publishing, already in place.

## Decision

uv for everything in development and release:

- `pyproject.toml` declares the runtime dependencies with compatible ranges (`pyserial>=3.5`) and
  the development tools in two groups, `test` and `lint`; `dev` includes both and is uv's default
  group. pre-commit runs through `uvx`, at the version the `Makefile` pins.
- `uv.lock` and `.python-version` (3.13) are committed; CI installs with `--locked`, and each job
  installs only the group it needs.
- `make` targets, the local pre-commit hooks and CI (`astral-sh/setup-uv`) call uv.
- Dependabot watches the `uv` ecosystem.

## Consequences

### Positive

- One command sets everything up (`make setup`), and the same lock drives local runs and CI.
- The `uv-lock` hook rejects a `pyproject.toml` change without its lock.

### Negative / trade-offs

- Contributors need uv installed.
- MegaLinter does not use this environment: it brings its own linters, whose versions can differ
  ([ADR-0003](0003-non-python-linter-versions-follow-the-megalinter-image.md)), and its
  pre-commands install the runtime dependencies and the `test` group from the lock where the type
  checkers need them.

### Follow-ups

- [`coding-standards.md`](../../.agents/rules/coding-standards.md) cites this ADR for dependencies.
