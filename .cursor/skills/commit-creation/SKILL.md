---
name: commit-creation
description: Produces conventional commit messages from staged changes with clear intent, scope, and atomic sizing. Use when preparing git commits, reviewing staged changes, or revising commit messages.
---

# Commit Creation

## Goal

Create conventional commits that communicate intent and keep history scannable.

## Format

```
<type>(<scope>): <short summary>

[optional body — why this change is needed]
[optional footer — breaking changes, references]
```

## Types

| Type | When |
|------|------|
| `feat` | New functionality |
| `fix` | Bug fix |
| `test` | Tests only |
| `refactor` | Structural improvement, no behavior change |
| `docs` | Documentation only |
| `chore` | Tooling or maintenance |
| `ci` | CI/CD changes |
| `perf` | Performance improvement |

## Rules

- Subject line in imperative mood, lowercase after type/scope.
- Keep subject under 72 characters.
- Use scope when helpful (e.g. `listener`, `handlers`, `database`).
- Atomic sizing: prefer 1-5 files per commit, one logical change.
- Every commit leaves tests green.
- Mark breaking changes clearly: `BREAKING CHANGE:` in footer.

## Examples

- `feat(listener): add event-type routing guard`
- `fix(database): handle transient connection timeout on retry`
- `test(handlers): cover invalid payload rejection path`
- `refactor(services): extract email template resolution`
