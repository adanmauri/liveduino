---
name: make-pr
description: Create pull requests with consistent title/body, correct base branch, and verified branch state. Use when the user asks to open a PR from the current branch.
---

# Make Pull Request

## Objective

Open a clean, review-ready pull request from the current branch using a clear summary and test plan.

## Workflow

1. Validate repository state:
   - `git status --short --branch`
   - Confirm current branch is not `main`.
2. Understand PR scope:
   - `git log --oneline origin/main...HEAD`
   - `git diff --stat origin/main...HEAD`
3. Ensure remote branch exists:
   - If needed: `git push -u origin HEAD`
4. Draft PR title:
   - Format: `<type>: <short outcome>`
   - Reuse commit intent when possible.
5. Draft PR body with:
   - `## Summary` (2-4 bullets)
   - `## Test plan` (checklist)
   - Optional risks/notes only when relevant
6. Create PR:
   - Preferred: GitHub MCP (`user-github`) to create PR and return URL.
   - Fallback: `gh pr create --base main --head <branch> --title "<title>" --body "<body>"`
7. Report outcome:
   - PR URL
   - base/head branches
   - final title used

## PR Content Rules

- Explain user-facing impact first.
- Keep bullets concrete and reviewable.
- Avoid generic text like "misc fixes".
- Include test commands actually run.

## Safety Rules

- Never open PR from `main`.
- Never force push unless explicitly requested.
- Do not change git config.
- Prefer MCP over `gh` for GitHub operations.
- If neither MCP nor `gh` is authenticated, stop and ask user to authenticate.

## Body Template

```markdown
## Summary
- <change 1>
- <change 2>

## Test plan
- [ ] <test command or scenario 1>
- [ ] <test command or scenario 2>
```

## Command Template

```bash
git status --short --branch
git log --oneline origin/main...HEAD
git diff --stat origin/main...HEAD
git push -u origin HEAD
gh pr create --base main --head <branch> --title "<title>" --body "<body>"
```
