---
name: review-pr
description: Triage PR feedback, apply requested fixes, and keep pull requests merge-ready. Use when the user asks to review comments, address PR feedback, or stabilize CI before merge.
---

# Review Pull Request

## Objective

Process PR feedback end-to-end: classify comments, apply fixes, verify checks, and prepare a concise update for reviewers.

## Workflow

1. Gather PR context:
   - Preferred: GitHub MCP (`user-github`) for PR metadata and status.
   - Fallback: `gh pr view --json number,title,headRefName,baseRefName,url,reviewDecision`
   - Fallback: `gh pr status`
2. Collect feedback:
   - Review comments and threads
   - Preferred: GitHub MCP (`user-github`) for PR comments/reviews.
   - Fallback: `gh api repos/<owner>/<repo>/pulls/<number>/comments`
3. Triage each item:
   - `must-fix` (bug, regression, failing test, security)
   - `should-fix` (clarity, maintainability)
   - `discussion` (needs decision)
4. Apply clear fixes first:
   - Group related changes
   - Keep behavior stable unless explicitly requested
5. Validate locally:
   - Run relevant checks (lint, types, tests)
6. Commit and push:
   - Use clear commit message linked to feedback scope
7. Post review update:
   - What was fixed
   - What remains open
   - Evidence (commands/checks)

## Comment Handling Rules

- Prioritize correctness and regressions over style nits.
- If a request is ambiguous, ask one focused question.
- Avoid silent behavior changes not requested by feedback.
- Resolve conversations only when the requested change is demonstrably addressed.

## CI Recovery Loop

When checks fail:

1. Identify first failing job/log.
2. Reproduce locally with closest command.
3. Fix root cause (not symptom).
4. Re-run targeted checks.
5. Push and monitor checks again.

Repeat until all required checks pass.

## Safety Rules

- Never force push unless explicitly requested.
- Never dismiss review comments without addressing or clarifying.
- Never merge PR unless explicitly requested.
- Do not modify unrelated files to satisfy a single comment.
- Prefer MCP over `gh` for GitHub operations when both are available.

## Update Template

```markdown
## Addressed
- <feedback item and fix>
- <feedback item and fix>

## Verification
- `make lint`
- `make type-check`
- `make test-coverage` (when `app/` changed)
- `make test-integration` (when persistence/HTTP changed)

## Open items
- <question or pending decision>
```
