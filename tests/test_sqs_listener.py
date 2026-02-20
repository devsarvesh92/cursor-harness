import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.listener.sqs_listener import SQSListener
from src.listener.message_router import MessageRouter, UnknownEventTypeError


def make_sqs_message(body: str = '{"type": "user.created", "data": {}}') -> dict:
    return {
        "ReceiptHandle": "fake-receipt-handle",
        "Body": body,
    }


@pytest.fixture
def router() -> MessageRouter:
    return MessageRouter()


@pytest.fixture
def listener(router: MessageRouter) -> SQSListener:
    with patch("src.listener.sqs_listener.boto3.client"):
        return SQSListener(
            queue_url="https://sqs.example.com/test-queue",
            router=router,
            dlq_url="https://sqs.example.com/test-dlq",
        )


@pytest.mark.asyncio
async def test_retries_once_on_transient_error_then_succeeds(listener: SQSListener):
    # Arrange
    message = make_sqs_message()
    listener.router.route = AsyncMock(
        side_effect=[RuntimeError("transient"), None],
    )
    listener.sqs.delete_message = MagicMock()

    # Act
    with patch("src.listener.sqs_listener.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await listener.process_message(message)

    # Assert
    assert result is True
    assert listener.router.route.call_count == 2
    listener.sqs.delete_message.assert_called_once()
    listener.sqs.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_retries_once_on_transient_error_then_sends_to_dlq(listener: SQSListener):
    # Arrange
    message = make_sqs_message()
    listener.router.route = AsyncMock(
        side_effect=[RuntimeError("fail-1"), RuntimeError("fail-2")],
    )
    listener.sqs.delete_message = MagicMock()
    listener.sqs.send_message = MagicMock()

    # Act
    with patch("src.listener.sqs_listener.asyncio.sleep", new_callable=AsyncMock):
        result = await listener.process_message(message)

    # Assert
    assert result is False
    assert listener.router.route.call_count == 2
    listener.sqs.send_message.assert_called_once()
    listener.sqs.delete_message.assert_called_once()


@pytest.mark.asyncio
async def test_no_retry_on_unknown_event_type_error(listener: SQSListener):
    # Arrange
    message = make_sqs_message()
    listener.router.route = AsyncMock(
        side_effect=UnknownEventTypeError("unknown.event"),
    )
    listener.sqs.delete_message = MagicMock()
    listener.sqs.send_message = MagicMock()

    # Act
    result = await listener.process_message(message)

    # Assert
    assert result is False
    listener.router.route.assert_called_once()
    listener.sqs.delete_message.assert_called_once()
    listener.sqs.send_message.assert_not_called()
