# 0002. Quality gates: pre-commit locally, MegaLinter in CI

**Status:** Accepted · **Date:** 2026-10-08

## Context

The local hooks ran ruff, ruff-format, Black and isort on staged files, while `make lint` and CI
ran Ruff, Flake8, Pylint, mypy and Pyright through the `Makefile`. Nothing checked formatting in
CI, and `ruff-format` and Black disagreed, so 24 files had drifted from Black's output by the time
this ADR was written. Markdown, YAML, JSON, workflows, spelling and secrets were not checked at
all, and the type checkers never looked at `scripts/`, where they found four real errors. The
owner's other repositories run one `.pre-commit-config.yaml` from the commit hook, `make check`
and CI alike, with MegaLinter adding the scanners in CI.

## Options

- **MegaLinter only:** one list, feedback only in CI, a heavy container to run it locally.
- **pre-commit everywhere, MegaLinter removed:** one list and fast feedback, but loses the
  scanners that need the network or a vulnerability database.
- **pre-commit locally, MegaLinter in CI:** fast local feedback on the checks that matter for the
  code, and the broad sweep stays in CI; the Python linters must appear in both.

## Decision

- **Locally:** [`.pre-commit-config.yaml`](../../.pre-commit-config.yaml) is the list. The commit
  hook runs it on staged files; `make lint` runs it on the whole repository; `make check` adds the
  unit tests with the 100% coverage gate. It covers file hygiene, secrets, the `uv-lock` check,
  the Python linters (through `uv run`, over `src`, `tests`, `tooling` and `scripts`), workflows,
  Markdown, YAML, JSON, spelling, copied code, the em dash rule, agent pointer sync, docs links and
  the ADR index, and the commit-msg check against tool attribution.
- Black is the only formatter; `ruff-format` is gone.
- **In CI:** MegaLinter's Python flavor, configured in [`.mega-linter.yml`](../../.mega-linter.yml),
  plus the tests and the build (`tests.yaml`), the bundled firmware check (`firmware.yaml`) and the
  daily security scan (`security.yaml`).
- Every linter MegaLinter runs on files offline is also a local hook, with the same settings
  ([ADR-0003](0003-non-python-linter-versions-follow-the-megalinter-image.md)).

[`docs/CI.md`](../CI.md) keeps the map of which tool runs where.

## Consequences

### Positive

- `make check` is the definition of done, for people and agents alike.
- The commit hook catches most problems before a push.

### Negative / trade-offs

- Two lists to keep aligned: a Python linter added to one goes into the other.
- The first `make setup` downloads Node.js and Go if missing, for the non-Python hooks.

### Follow-ups

- [ADR-0003](0003-non-python-linter-versions-follow-the-megalinter-image.md) ties the versions of
  the two lists together; [ADR-0005](0005-pull-requests-check-what-they-change-main-checks-everything.md)
  sets what each pull request checks.
