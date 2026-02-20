---
name: sqs-listener
description: Patterns for building SQS message listeners and handlers
---

# SQS Listener Patterns

## Architecture

Use a handler-based architecture:

```python
# Message Router
class MessageRouter:
    def __init__(self):
        self.handlers: dict[str, MessageHandler] = {}
    
    def register(self, event_type: str, handler: MessageHandler):
        self.handlers[event_type] = handler
    
    async def route(self, message: dict):
        event_type = message.get('type')
        handler = self.handlers.get(event_type)
        if not handler:
            raise UnknownEventTypeError(f"Unknown event: {event_type}")
        await handler.handle(message)
```

## Handler Pattern

```python
from abc import ABC, abstractmethod

class MessageHandler(ABC):
    @abstractmethod
    async def handle(self, message: dict) -> None:
        """Process a single message"""
        pass

class UserCreatedHandler(MessageHandler):
    def __init__(self, db: Database, email_service: EmailService):
        self.db = db
        self.email_service = email_service
    
    async def handle(self, message: dict) -> None:
        user_data = message['data']
        async with self.db.transaction():
            user = await self.db.create_user(user_data)
            await self.email_service.send_welcome(user.id)
```

## SQS Polling

```python
import boto3
from botocore.exceptions import ClientError

class SQSListener:
    def __init__(self, queue_url: str, router: MessageRouter):
        self.sqs = boto3.client('sqs')
        self.queue_url = queue_url
        self.router = router
    
    async def poll(self):
        """Long-poll for messages"""
        try:
            response = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20,  # Long polling
                MessageAttributeNames=['All']
            )
            
            messages = response.get('Messages', [])
            for msg in messages:
                await self.process_message(msg)
                
        except ClientError as e:
            logger.error(f"SQS polling error: {e}")
            raise
```

## Error Handling

- **ValidationError**: Log and send to DLQ (don't retry)
- **DatabaseError**: Retry with exponential backoff
- **ExternalAPIError**: Retry with backoff, then DLQ
- **FatalError**: Send directly to DLQ

## Dead Letter Queue

```python
async def process_with_dlq(self, message: dict):
    try:
        await self.router.route(message)
        await self.acknowledge(message)
    except RetryableError as e:
        if self.should_retry(message):
            await self.retry_with_backoff(message)
        else:
            await self.send_to_dlq(message, e)
    except FatalError as e:
        await self.send_to_dlq(message, e)
```
