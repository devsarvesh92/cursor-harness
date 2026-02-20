---
name: tdd-red-green-refactor
description: Applies disciplined TDD using red-green-refactor cycles with atomic test-first development. Use when implementing features, fixing bugs, or when correctness and maintainability are critical.
---

# TDD Red Green Refactor

## Goal

Implement behavior through small cycles: failing test first, minimal passing code, then clean up safely.

## Cycle

1. **Red**: Write one focused failing test that defines the next behavior.
2. **Green**: Write the minimum production code to make that test pass.
3. **Refactor**: Improve design, naming, duplication — tests must stay green.
4. **Commit**: Each cycle is a candidate for an atomic commit.
5. Repeat.

## Rules

- Never add production logic without a failing test.
- Change one behavior per cycle.
- Run relevant tests after each step (`make test` or project equivalent).
- Keep tests deterministic and independent.

## Test Structure

- Arrange, Act, Assert — each section clearly separated.
- Name tests by behavior: `test_<expected_behavior>`.
- Cover happy path, boundary conditions, and failure path.
- Assert outputs and side effects, not internal implementation.

## Progress Reporting

When reporting progress, use:

```markdown
### TDD Cycle
- **Red**: `test_<name>` — <what it asserts>
- **Green**: <minimal code added>
- **Refactor**: <cleanup performed>
- **Status**: tests passing / failing
```
