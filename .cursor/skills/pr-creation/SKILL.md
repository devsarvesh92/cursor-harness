---
name: pr-creation
description: Creates high-quality pull requests with clear summaries and test plans from branch changes. Use when the user asks to open a PR, prepare PR content, or review branch readiness.
---

# PR Creation

## Goal

Create a concise, reviewable PR that explains why the change exists and how it was validated.

## Workflow

1. Inspect branch state — run `git status`, `git log`, and `git diff <base>...HEAD`.
2. Summarize user-facing and technical impact across **all** commits (not just the latest).
3. Build a focused test plan with concrete verification steps.
4. Propose a PR title in imperative style.
5. Push branch and create PR only when clean.

## PR Title Pattern

`<type>: <short intent>`

Examples:
- `feat: add idempotency guard for message handlers`
- `fix: prevent duplicate retries for transient db failures`

## PR Body Template

```markdown
## Summary
- <what changed and why>
- <key design decisions or tradeoffs>
- <risk areas or operational notes>

## Test Plan
- [ ] Unit tests updated and passing
- [ ] Integration behavior validated
- [ ] Manual verification completed (if applicable)

## JIRA
- <JIRA ticket link if applicable>
```

## Quality Bar

- Include all commits relevant to the feature.
- Call out migrations, breaking changes, and operational impact explicitly.
- Keep summary grounded in behavior, not implementation trivia.
