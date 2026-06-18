---
name: create-branch
description: Create and validate git branches safely with consistent naming, main synchronization, and optional upstream setup. Use when the user asks to create a branch, start a feature/fix/chore branch, or prepare a branch before commits or PRs.
---

# Create Branch

## Objective

Create a git branch in a safe, repeatable way, following naming conventions and verifying readiness for upcoming commits or PR creation.

## Workflow

1. Confirm branch intent from user input:
   - Type: `feature`, `fix`, `chore`, `refactor`, `docs`, `test`, `hotfix`
   - Scope/slug: short lowercase words separated with `-`
2. Build branch name with this default pattern:
   - `<type>/<slug>`
   - Example: `fix/cart-quantity-validation`
3. Validate repo state before creating the branch:
   - Run `git status --short --branch`
   - If there are unrelated changes, warn and continue only if user agrees.
4. Sync `main` before branching:
   - `git fetch origin main`
   - `git switch main`
   - `git pull --ff-only origin main`
5. Create the branch:
   - `git switch -c <branch-name>`
   - If branch already exists locally, use `git switch <branch-name>`.
6. Verify current branch:
   - Run `git branch --show-current`
7. Optional remote tracking when requested:
   - `git push -u origin <branch-name>`
8. Report outcome:
   - Branch created/switched
   - Current branch name
   - Whether `main` was synchronized successfully
   - Whether upstream was configured

## Naming Rules

- Use lowercase only.
- Use `-` as separator.
- Avoid spaces, underscores, and special characters.
- Keep names short but descriptive.
- Include ticket ID first when present:
  - `feature/abc-123-book-search-filters`

## Safety Rules

- Never delete or overwrite branches unless explicitly requested.
- Never use force push unless explicitly requested.
- Never change global git config.
- Use fast-forward only when updating `main`; if it fails, stop and report next action.
- If branch creation fails, show exact error and propose next command.

## Command Template

```bash
git status --short --branch
git fetch origin main
git switch main
git pull --ff-only origin main
git switch -c <type>/<slug> || git switch <type>/<slug>
git branch --show-current
```
