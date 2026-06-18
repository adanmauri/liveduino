---
name: create-commit
description: Create safe, clear git commits with project-consistent messages and final verification. Use when the user asks to commit current changes or prepare a commit before opening a PR.
---

# Create Commit

## Objective

Create a clean commit from current changes, with a precise message and verification of the repository state.

## Workflow

1. Inspect current state:
   - `git status --short --branch`
   - `git diff --staged`
   - `git diff`
2. Confirm scope:
   - Stage only files related to the requested work.
   - Exclude generated caches, binaries, and secrets.
3. Build commit message:
   - Prefer `<type>: <short summary>`
   - Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `ci`
   - Focus on why/value, not only file names.
4. Stage and commit:
   - `git add <relevant-paths>`
   - `git commit -m "<message>"`
5. Verify result:
   - `git status --short --branch`
   - `git log -1 --oneline`
6. Report:
   - Commit hash
   - Commit message
   - Staged scope included
   - Remaining uncommitted changes (if any)

## Commit Message Rules

- Use imperative, concise phrasing.
- Keep subject around 50-72 chars when possible.
- Keep one concern per commit.
- For mixed unrelated changes, split into multiple commits.

## Safety Rules

- Never commit secrets (`.env`, credentials, tokens).
- Never use `--no-verify` unless explicitly requested.
- Never push unless explicitly requested.
- Never amend by default; use amend only when user asks.
- If hooks fail, report errors and fix before retrying.

## Command Template

```bash
git status --short --branch
git diff --staged
git diff
git add <paths>
git commit -m "<type>: <summary>"
git status --short --branch
git log -1 --oneline
```
