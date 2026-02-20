---
name: brainstorming
description: Facilitates iterative requirement discovery through focused questions to arrive at clear acceptance criteria and an actionable plan. Use when scoping a feature, clarifying ambiguous requests, or preparing before implementation.
---

# Brainstorming

## Goal

Turn a vague request into testable acceptance criteria and a simple plan through short question rounds.

## Workflow

1. **Restate** the request in one sentence to confirm understanding.
2. **Question rounds** — ask 1-3 focused questions per round (never a long questionnaire):
   - Round 1: Problem & user impact
   - Round 2: Scope boundaries and non-goals
   - Round 3: Edge cases, error scenarios, dependencies
3. **Draft acceptance criteria** using Given/When/Then.
4. **Draft a plan** — list ordered tasks with estimated sizes (S/M/L).
5. **Get explicit sign-off** before any implementation starts.

## Acceptance Criteria Template

```markdown
## Acceptance Criteria
- Given <context>, when <action>, then <expected outcome>
- Given <edge case>, when <action>, then <expected outcome>

## Non-goals
- <explicitly out of scope>

## Done When
- [ ] Implementation matches criteria
- [ ] Tests cover happy path and edge cases
- [ ] Documentation updated if behavior changed
```

## Plan Output

After sign-off, produce a plan document. See [plan.md](plan.md) for the template.
