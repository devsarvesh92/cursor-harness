# Ship Command

End-to-end orchestrator for feature delivery. Works like helm for your dev workflow — takes a story from idea to merged PR.

**Invoke**: type `/ship <story description or JIRA key>` in chat.

---

## Pipeline

### Phase 1: Brainstorm

Use the `brainstorming` skill (`.cursor/skills/brainstorming/SKILL.md`).

1. Read `.cursor/memory/project-summary.md` for project context.
2. Restate the request and ask iterative clarifying questions (1-3 per round).
3. Produce acceptance criteria (Given/When/Then).
4. Draft an actionable plan using the [plan template](../skills/brainstorming/plan.md).
5. **Checkpoint**: Present plan and criteria — wait for user sign-off before continuing.

### Phase 2: JIRA

Use the `jira-creator` skill (`.cursor/skills/jira-creator/SKILL.md`).

1. Create (or identify) a JIRA story with the acceptance criteria.
2. Break plan tasks into JIRA subtasks.
3. Create a feature branch: `feat/<PROJ-ID>-short-description`.

### Phase 3: Implement (TDD)

Use the `tdd-red-green-refactor` skill (`.cursor/skills/tdd-red-green-refactor/SKILL.md`).

For each task/subtask:

1. **Red**: Write a focused failing test.
2. **Green**: Write minimum code to pass.
3. **Refactor**: Clean up while green.
4. **Commit**: Use the `commit-creation` skill — atomic conventional commit (1-5 files).
5. Report TDD cycle progress.
6. Repeat until subtask is complete, then move to next subtask.

Follow project rules:
- `.cursor/rules/event-handlers.mdc` for handler code
- `.cursor/rules/python-clean-coding.mdc` for source code
- `.cursor/rules/test-case-writing.mdc` for tests

### Phase 4: PR

Use the `pr-creation` skill (`.cursor/skills/pr-creation/SKILL.md`).

1. Push the feature branch.
2. Create PR with summary, test plan, and JIRA link.
3. Ensure all tests pass (`make test`).

### Phase 5: Notify (Optional)

If the environment variable `SLACK_WEBHOOK_URL` is set:

```bash
curl -s -X POST "$SLACK_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d "{\"text\": \"Ship complete: <PR title> — <PR URL>\"}"
```

Skip silently if `SLACK_WEBHOOK_URL` is not set.

---

## Summary

```
/ship "add payment.received handler"
  │
  ├─ Brainstorm → questions → acceptance criteria → plan
  ├─ JIRA → story + subtasks → feature branch
  ├─ Implement → TDD cycles → atomic commits
  ├─ PR → summary + test plan + JIRA link
  └─ Notify → Slack (if configured)
```
