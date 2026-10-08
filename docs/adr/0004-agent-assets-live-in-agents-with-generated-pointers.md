# 0004. Agent assets live in `.agents/` with generated pointers

**Status:** Accepted · **Date:** 2026-10-08

## Context

`AGENTS.md` held everything at once: project context, coding standards, Arduino guardrails and
the definition of done. Skills lived in `.agents/skills/` with hand-written wrappers in
`.claude/skills/` and `.github/skills/`, so a renamed or removed skill left a stale wrapper behind,
and Cursor and GitHub Copilot got no rules at all. Several early commits also carried a tool
attribution trailer, which had to be removed by rewriting the history.

## Options

- **One file per tool, written by hand:** simple, but a copy of every rule per tool, which drifts.
- **Symlinks from each tool's location:** one copy, but not portable (Windows, some tools ignore
  them).
- **One canonical copy in `.agents/`, with thin generated pointers per tool:** one copy, portable,
  and drift is detectable by a script. The owner's other repositories already work this way.

## Decision

- [`AGENTS.md`](../../AGENTS.md) at the root is the operating manual ([agents.md](https://agents.md/)
  standard): what the repo is, where to read, workflow, definition of done, boundaries.
  `CLAUDE.md` and `.github/copilot-instructions.md` are hand-written pointers to it.
- Rules (`.agents/rules/`: coding standards, library guardrails) and skills (`.agents/skills/`)
  live once, following the [`.agents` protocol](https://dotagentsprotocol.com/), with `SKILL.md`
  spelled for Claude Code.
- `tooling/sync_agents.py` (standard library) writes a pointer per tool: `.claude/skills/`,
  `.github/skills/`, `.github/instructions/`, `.cursor/rules/`. Pointers carry frontmatter and a
  link, never instructions, and are committed so a fresh clone works without a build step.
  `make check-agents`, also a pre-commit hook, fails on drift.
- `.claude/settings.json` is committed: it allows the repository's own check commands and denies
  what the boundaries forbid (force-push, `--no-verify`, tags, releases, `uv publish`).
- No tool is credited in commits, PRs, issues or docs; a commit-msg hook
  (`tooling/check_commit_msg.py`) rejects attribution lines.

## Consequences

### Positive

- One place to edit a rule or a skill, and every tool sees the change after `make sync-agents`.
- The same layout as the owner's other repositories, so moving between them costs nothing.

### Negative / trade-offs

- Generated files in four directories, which must not be edited by hand.
- When a tool reads `.agents/` natively, its pointers become dead weight to remove.

### Follow-ups

- [`.agents/README.md`](../../.agents/README.md) holds the operating procedure and cites this ADR.
