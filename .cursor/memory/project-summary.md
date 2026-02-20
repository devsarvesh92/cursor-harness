# Project Summary — Harness

## Purpose

An SQS message listener that demonstrates **Cursor as a structured development harness** — rules, skills, commands, and agents guide all incremental changes for consistency and quality.

## Stack

- **Language**: Python 3.13+
- **Package manager**: `uv` (lockfile: `uv.lock`)
- **Key deps**: boto3, SQLAlchemy (async), aiosqlite, Pydantic, pytest + pytest-asyncio
- **Formatting/linting**: ruff, isort

## Architecture

```
src/
├── handlers/       # Event handlers (one per event type, extend MessageHandler ABC)
│   ├── base.py     # MessageHandler abstract base class
│   ├── user_created.py
│   └── order_placed.py
├── listener/       # SQS polling loop + MessageRouter
│   ├── sqs_listener.py
│   └── message_router.py
├── database/       # SQLAlchemy models, async connection, repository pattern
│   ├── models.py
│   ├── connection.py
│   └── repository.py
├── services/       # Domain services (email, etc.)
│   └── email.py
└── main.py         # Entry point — wires DI and starts listener
```

## Patterns in Use

- **Handler pattern**: `MessageHandler` ABC → concrete handlers per event type
- **Router pattern**: `MessageRouter` dispatches by `message["type"]`
- **Repository pattern**: DB access via repository classes with async sessions
- **Transaction management**: `async with db.begin()` for multi-step ops
- **Error classification**: `ValueError` for invalid data, `UnknownEventTypeError` for unregistered event types (custom exceptions like `DatabaseError` can be introduced as the codebase grows)
- **DLQ**: Failed messages sent to dead-letter queue

## Common Commands

- `make sync` — install/sync dependencies
- `make test` — run pytest
- `make run` — start SQS listener
- `make clean` — remove caches and artifacts

## Quality Expectations

- Follow scoped Cursor rules in `.cursor/rules/`
- Prefer async-safe patterns and explicit error classification
- Keep tests close to behavior changes (TDD)
- Run formatting (`ruff format . && ruff check --fix . && isort .`) before commits
