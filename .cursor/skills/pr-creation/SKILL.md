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
4. Create a Mermaid diagram showing the change flow or architecture impact.
5. Capture token usage for the session.
6. Propose a PR title in imperative style.
7. Push branch and create PR only when clean.

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

## Architecture / Flow

> Include a Mermaid diagram that illustrates the change — e.g. data flow,
> component interaction, state transitions, or before/after architecture.
> Choose the diagram type (flowchart, sequence, class, state, etc.) that
> best communicates the change.

```mermaid
<diagram here>
```

## Test Plan

| # | Scenario | Type | Status |
|---|----------|------|--------|
| 1 | <describe scenario> | Unit / Integration / Manual | :white_check_mark: / :hourglass: |
| 2 | <describe scenario> | Unit / Integration / Manual | :white_check_mark: / :hourglass: |

### Coverage Notes
- <any gaps, edge cases deferred, or known limitations>

## Token Usage

| Metric | Value |
|--------|-------|
| Prompt tokens | <value> |
| Completion tokens | <value> |
| Total tokens | <value> |
| Estimated cost | <value> |

> Token counts reflect the AI-assisted session that produced this PR.
> If exact counts are unavailable, note "not tracked" in the table.

## JIRA
- <JIRA ticket link if applicable>
```

## Quality Bar

- Include all commits relevant to the feature.
- Call out migrations, breaking changes, and operational impact explicitly.
- Keep summary grounded in behavior, not implementation trivia.
- Mermaid diagram must add clarity — skip if the change is trivial (e.g. config-only).
- Test plan table must list every scenario validated, not just generic checkboxes.
- Token usage should be filled when AI-assisted; omit the section for manual PRs.
