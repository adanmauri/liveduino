# 0003. Non-Python linter versions follow the MegaLinter image

**Status:** Accepted · **Date:** 2026-10-08

## Context

Most linters run twice ([ADR-0002](0002-quality-gates-pre-commit-locally-megalinter-in-ci.md)):
in the local hooks and in CI, inside the MegaLinter image. When the repository has no config file
by the name a MegaLinter linter looks for, MegaLinter uses its own default (a `.pylintrc`, a
`.ruff.toml` with line length 88, a `.markdownlint.json` with line length 400), so the same
linter would report different things on each side. Versions drift the same way unless something
ties them.

## Options

- **Let each side keep its versions and settings:** no work, and findings that appear on one side
  only.
- **Pin every local linter to the image's version:** the same results everywhere, but the Python
  development dependencies become `==` pins that move only with MegaLinter, and Dependabot has to
  ignore them.
- **Pin to the image only what needs a pin anyway:** a pre-commit hook outside uv must name a
  version, so it names the image's. The Python linters stay ordinary development dependencies.

## Decision

The settings are shared everywhere; the versions are shared for the non-Python linters.

- [`.mega-linter.yml`](../../.mega-linter.yml) points the Python linters at `pyproject.toml`, and
  the settings MegaLinter would take from its defaults live in the repository (`.flake8`,
  `.cspell.json`, `.markdownlint.json`, `.yamllint.yml`, `.secretlintrc.json`, `.jscpd.json`,
  `lychee.toml`), so both sides read the same files.
- The Python linters are development dependencies like any other: unpinned in `pyproject.toml`,
  locked in `uv.lock`, updated by Dependabot. Their hooks run them with `uv run --locked`.
- Every other linter in the image that checks files offline is a local hook at the image's
  version: markdownlint, markdown-table-formatter, prettier, jsonlint, cspell, secretlint and jscpd
  (Node.js, in `additional_dependencies`), shfmt (Go, the same), and betterleaks, actionlint,
  shellcheck and zizmor (their `rev`).
- markdown-table-formatter owns table layout, so markdownlint's MD060 (table column style) is off:
  the two measure wide characters such as emoji differently and would fight over the same table.
- Nothing checks the alignment automatically: the pull request that bumps MegaLinter updates the
  hook versions by hand, from the image's Dockerfile ([`docs/CI.md`](../CI.md)).
- The scanners that need the network or a vulnerability database (Trivy, Grype, OSV-Scanner,
  trufflehog, checkov, lychee, v8r) run only in CI.

## Consequences

### Positive

- A Markdown, YAML, JSON, spelling, secret or workflow finding shows up on commit, the same way CI
  reports it.
- The Python development dependencies update on their own schedule.

### Negative / trade-offs

- A Python linter can disagree between the hooks and CI while its versions differ.
- A MegaLinter bump that forgets the hooks lets them drift silently until a linter disagrees.
- A scanner finding shows up only in CI.

### Follow-ups

- [`docs/CI.md`](../CI.md) describes how to bump MegaLinter.
