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

If the environment variable `SLACK_WEBHOOK_URL` is set, post a rich Slack notification using Block Kit.

Gather these values from the session before building the payload:

| Variable | Source |
|----------|--------|
| `PR_TITLE` | PR title (imperative style) |
| `PR_URL` | GitHub PR URL |
| `BRANCH` | Feature branch name |
| `JIRA_URL` | JIRA ticket URL (or "N/A") |
| `COMMIT_COUNT` | Number of commits in the PR |
| `FILES_CHANGED` | Number of files changed |
| `TEST_RESULT` | "All passing" or summary of failures |
| `TDD_CYCLES` | Number of red-green-refactor cycles completed |

```bash
curl -s -X POST "$SLACK_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{
  "blocks": [
    {
      "type": "header",
      "text": { "type": "plain_text", "text": "🚢 Ship Complete", "emoji": true }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*<'"$PR_URL"'|'"$PR_TITLE"'>*"
      }
    },
    { "type": "divider" },
    {
      "type": "section",
      "fields": [
        { "type": "mrkdwn", "text": "*Branch:*\n`'"$BRANCH"'`" },
        { "type": "mrkdwn", "text": "*JIRA:*\n'"$JIRA_URL"'" },
        { "type": "mrkdwn", "text": "*Commits:*\n'"$COMMIT_COUNT"'" },
        { "type": "mrkdwn", "text": "*Files Changed:*\n'"$FILES_CHANGED"'" },
        { "type": "mrkdwn", "text": "*Tests:*\n'"$TEST_RESULT"'" },
        { "type": "mrkdwn", "text": "*TDD Cycles:*\n'"$TDD_CYCLES"'" }
      ]
    },
    { "type": "divider" },
    {
      "type": "actions",
      "elements": [
        {
          "type": "button",
          "text": { "type": "plain_text", "text": "Review PR", "emoji": true },
          "url": "'"$PR_URL"'",
          "style": "primary"
        },
        {
          "type": "button",
          "text": { "type": "plain_text", "text": "View JIRA", "emoji": true },
          "url": "'"$JIRA_URL"'"
        }
      ]
    },
    {
      "type": "context",
      "elements": [
        { "type": "mrkdwn", "text": "Shipped via `/ship` • Cursor Harness" }
      ]
    }
  ]
}'
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
