---
name: async-patterns
description: Async/await patterns and best practices
---

# Async Patterns

## Database Operations

Always use async database operations:

```python
# ✅ GOOD
async def create_user(self, data: dict) -> User:
    async with self.db.transaction():
        user = await self.db.execute(
            insert(User).values(**data)
        )
        await self.db.commit()
        return user

# ❌ BAD
def create_user(self, data: dict) -> User:
    # Blocking operation
    user = self.db.execute(...)
    return user
```

## Transaction Management

Use async context managers for transactions:

```python
async with db.transaction():
    user = await db.create_user(data)
    await email_service.send_welcome(user.id)
    # Both succeed or both rollback
```

## Error Handling in Async

```python
async def process_message(self, message: dict):
    try:
        await self.handler.handle(message)
    except ValidationError as e:
        logger.warning(f"Invalid message: {e}")
        await self.dlq.send(message)
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise  # Let retry logic handle it
```

## Retry with Exponential Backoff

```python
import asyncio
from functools import wraps

def retry_with_backoff(max_attempts: int = 3, base_delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except RetryableError as e:
                    if attempt == max_attempts - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
            raise MaxRetriesExceededError()
        return wrapper
    return decorator

@retry_with_backoff(max_attempts=3)
async def process_with_retry(message: dict):
    await handler.handle(message)
```
