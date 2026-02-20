# Harness Project

This project demonstrates using **Cursor as a Harness** - a structured, guided development environment with rules, commands, skills, and agents.

## Starting Point

This project has **identical code** to the copilot project initially. The difference emerges when making incremental changes:

- **Copilot**: Changes are ad-hoc, inconsistent, quality varies
- **Harness**: Changes follow rules/skills, consistent, high quality

## Structure

```
harness/
├── src/
│   ├── handlers/      # Message handlers
│   ├── listener/      # SQS listener and router
│   ├── database/      # Database models and repositories
│   └── services/      # Service layer
├── .cursor/
│   ├── rules/         # Coding standards (guides improvements)
│   ├── skills/        # Domain knowledge (guides patterns)
│   └── commands/      # Workflows
├── tests/             # Tests
├── Makefile           # Project commands
└── main.py            # Entry point
```

## Running

```bash
# Sync dependencies
make sync

# Run the listener
make run

# Run tests
make test
```

## Key Difference

When making incremental changes, this project (with rules/skills) will produce:
- ✅ Consistent patterns
- ✅ Proper implementations
- ✅ High code quality
- ✅ Clean separation of concerns

The `.cursor/rules/` and `.cursor/skills/` guide incremental improvements automatically.

## Rules & Skills

- **Rules**: Coding standards that guide improvements
- **Skills**: Domain patterns (SQS, async, handlers)
- **Commands**: Standardized workflows

See `.cursor/` directory for details.
