# 0006. Actions are pinned to a commit

**Status:** Accepted · **Date:** 2026-10-08

## Context

The workflows named actions by major tag (`actions/checkout@v7`, `astral-sh/setup-uv@v7`,
`alstr/todo-to-issue-action@v5`). A major tag moves on purpose with every release, and any version
tag can be force-pushed by its owner, or by anyone holding the owner's credentials, so the code a
workflow runs could change with no change in this repository. In March 2026 an attacker rewrote 76
of the 77 version tags of `aquasecurity/trivy-action` to code that reads the runner's memory for
secrets ([GHSA-69fq-xp46-6x23](https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23)).
This repository's publish workflow holds an OIDC token that can upload to PyPI, which makes a
moved tag here a supply-chain risk for every user of the package.

## Options

- **Major tags (`@v7`):** no upkeep, and every upstream release, or rewrite, runs here unseen.
- **Version tags (`@v7.0.1`):** readable, and safe only where the publisher made the release
  immutable, which has to be checked action by action.
- **Commit SHAs for every action, with the version in a comment:** a rewritten tag changes nothing
  here, whoever the publisher is.

## Decision

- Every action in the workflows is pinned to a full commit SHA, with the version it corresponds to
  in a comment: `uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`. No
  exception for first-party actions.
- zizmor enforces it, as a local hook and in MegaLinter.
- Dependabot updates actions monthly, with a 14-day cooldown, as for packages. It moves the SHA
  and the comment together, so an upgrade is a reviewed pull request.
- A tool an action downloads is pinned as well when the action allows it: `security.yaml` sets the
  Trivy binary to `v0.70.0`.
- Every workflow starts with `permissions: {}`, and each job asks for what it needs.
- A container image runs by digest. The MegaLinter action, even pinned to a commit, pulled its
  image by tag (`ghcr.io/oxsecurity/megalinter-python:v10.1.0`), so `code-quality.yaml` runs the
  image directly, as `docker://...:v10.1.0@sha256:...`.
- Checkouts drop their credentials (`persist-credentials: false`), except in the job that pushes
  the coverage badge; `create-pull-request` in the firmware workflow brings its own token.
- The publish workflow restores no cache (`enable-cache: false`), so a poisoned cache cannot end
  up in a release.

## Consequences

### Positive

- A rewritten or deleted tag cannot change the code a workflow runs.
- Every change to the code CI runs goes through a pull request in this repository.

### Negative / trade-offs

- A SHA says nothing to a reader; the version comment must stay next to it, and Dependabot keeps
  both in step.
- A fix released upstream reaches this repository only through that monthly pull request, two
  weeks after its release at the earliest.
- Dependabot does not update `docker://` references, so MegaLinter is bumped by hand.

### Follow-ups

- The workflow rules in [`coding-standards.md`](../../.agents/rules/coding-standards.md) cite
  this ADR.
