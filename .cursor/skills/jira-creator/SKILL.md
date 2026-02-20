---
name: jira-creator
description: Creates JIRA tickets and subtasks from acceptance criteria and task plans. Use when the user wants to create a JIRA story, break work into subtasks, or track implementation progress.
---

# JIRA Creator

## Goal

Translate acceptance criteria and a task plan into a well-structured JIRA story with actionable subtasks.

## Workflow

1. Confirm the JIRA project key (e.g. `HARNESS`, `PROJ`).
2. Draft a story with summary, description, and acceptance criteria.
3. Break the plan tasks into subtasks (one per deliverable chunk).
4. Create tickets using the Atlassian MCP server (`atlassian` in `.cursor/mcp.json`).
5. If MCP is unavailable, output the ticket content for manual creation.

## Story Template

```
Summary: <imperative, concise title>
Type: Story
Description:
  ## Context
  <what and why>

  ## Acceptance Criteria
  - Given ..., when ..., then ...

  ## Non-goals
  - <out of scope>

Labels: <relevant labels>
```

## Subtask Naming

Subtask titles are actionable and map to implementation tasks:

- `Add validation for user email on create`
- `Implement order.placed handler`
- `Add tests for inventory decrement edge cases`
- `Update API documentation for new endpoint`

## Branch Naming

Reference the JIRA key in branch names:

`feat/<PROJ-123>-short-description`

## Rules

- One subtask per shippable unit of work.
- Subtasks should be completable in a single TDD cycle or small set of cycles.
- Link PR to JIRA ticket when opening.
