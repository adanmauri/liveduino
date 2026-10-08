# 0005. Pull requests check what they change; main checks everything

**Status:** Accepted · **Date:** 2026-10-08

## Context

Every pull request ran every workflow over the whole repository, whatever it touched. A finding
in a file the pull request did not change is noise for its author, and a pull request that only
edits docs gains nothing from the tests.

## Options

- **Everything on every pull request:** simplest, and the noise above.
- **Only what changed, everywhere:** fastest, but nothing ever looks at the whole repository, so
  findings that span files are never seen.
- **What changed on pull requests, everything on `main`:** focused pull requests, and a full run
  on every merge.

## Decision

What changed on pull requests; everything on push to `main`. The daily `security.yaml` scan is
not affected: it always scans the whole repository.

- **MegaLinter** gets `VALIDATE_ALL_CODEBASE: false` on pull requests and lints the files that
  differ from the merge base with `main` (`git diff origin/main...`). The checkout fetches the full
  history, which that diff needs.
- A pull request that changes a file that decides what the linters report (`.mega-linter.yml`,
  `.pre-commit-config.yaml`, `pyproject.toml`, the linter config files, `code-quality.yaml`) lints
  everything. Otherwise a stricter rule would pass its own pull request and fail `main`.
- MegaLinter's project-mode linters (Trivy, Grype, OSV-Scanner, Syft, betterleaks, secretlint,
  trufflehog, checkov, jscpd) always scan the whole repository; MegaLinter cannot narrow them.
- **Tests** run in full whenever they run: selecting tests by diff would miss a change that breaks
  a module through another one. Pull requests that touch none of `src/`, `tests/`, `scripts/` or
  the packaging files skip them; `main` always runs them. The decision is a job (`changes`) that
  the tests depend on, not a `paths:` filter, so the check reports as skipped instead of pending
  if it is ever made required.
- **Firmware** keeps its `paths:` filter: the job is slow, it only matters when boards, the
  bundle or the build script change, and it is not a required check.
- **Locally**, the hooks run on the staged files, and mypy, Pyright, Pylint and Bandit check the
  whole project whenever a Python file changes (`pass_filenames: false`).

## Consequences

### Positive

- A pull request shows findings in the files it touches, and docs-only pull requests do not wait
  for the tests.

### Negative / trade-offs

- A pull request can pass and `main` fail, on a check that spans files or on a file the pull
  request did not touch. The fix goes in the next pull request.

### Follow-ups

- The scope logic lives in [`code-quality.yaml`](../../.github/workflows/code-quality.yaml) and
  [`tests.yaml`](../../.github/workflows/tests.yaml).
