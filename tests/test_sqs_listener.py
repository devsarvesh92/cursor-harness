import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from botocore.exceptions import ClientError

from src.listener.sqs_listener import SQSListener
from src.listener.message_router import MessageRouter, UnknownEventTypeError


def _make_listener(router=None, dlq_url="https://sqs/dlq", max_retries=3):
    router = router or MagicMock(spec=MessageRouter)
    with patch("src.listener.sqs_listener.boto3") as mock_boto:
        mock_sqs = MagicMock()
        mock_boto.client.return_value = mock_sqs
        listener = SQSListener(
            queue_url="https://sqs/queue",
            router=router,
            dlq_url=dlq_url,
            max_retries=max_retries,
        )
    return listener, mock_sqs


def _make_sqs_message(body: dict, receive_count: str = "1") -> dict:
    msg = {
        "ReceiptHandle": "receipt-123",
        "Body": json.dumps(body),
        "Attributes": {"ApproximateReceiveCount": receive_count},
    }
    return msg


@pytest.mark.asyncio
async def test_calculate_backoff_exponential_with_jitter():
    """Backoff follows base_delay * 2^(attempt-1) + jitter and increases per attempt."""
    listener, _ = _make_listener()

    backoff_1 = listener._calculate_backoff(attempt=1)
    backoff_2 = listener._calculate_backoff(attempt=2)
    backoff_3 = listener._calculate_backoff(attempt=3)

    assert 2.0 <= backoff_1 <= 4.0  # 2 * 2^0 = 2, + up to 2s jitter
    assert 4.0 <= backoff_2 <= 6.0  # 2 * 2^1 = 4, + up to 2s jitter
    assert 8.0 <= backoff_3 <= 10.0  # 2 * 2^2 = 8, + up to 2s jitter


@pytest.mark.asyncio
async def test_calculate_backoff_capped_at_max():
    """Backoff never exceeds MAX_BACKOFF_SECONDS (900)."""
    listener, _ = _make_listener()

    backoff = listener._calculate_backoff(attempt=100)

    assert backoff <= 900


@pytest.mark.asyncio
async def test_change_visibility_failure_logs_gracefully():
    """ClientError on change_message_visibility is logged, not raised."""
    listener, mock_sqs = _make_listener()
    mock_sqs.change_message_visibility.side_effect = ClientError(
        {"Error": {"Code": "InvalidParameterValue", "Message": "bad"}},
        "ChangeMessageVisibility",
    )

    # Should not raise
    await listener._change_visibility("receipt-123", 10)

    mock_sqs.change_message_visibility.assert_called_once()


@pytest.mark.asyncio
async def test_successful_message_is_acknowledged():
    """Successful processing deletes the message from the queue."""
    router = MagicMock(spec=MessageRouter)
    router.route = AsyncMock()
    listener, mock_sqs = _make_listener(router=router)
    message = _make_sqs_message({"type": "user.created", "data": {}})

    result = await listener.process_message(message)

    assert result is True
    mock_sqs.delete_message.assert_called_once_with(
        QueueUrl="https://sqs/queue", ReceiptHandle="receipt-123"
    )
    mock_sqs.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_transient_error_retries_via_visibility_change():
    """Transient error with receive count < max_retries changes visibility, no DLQ."""
    router = MagicMock(spec=MessageRouter)
    router.route = AsyncMock(side_effect=RuntimeError("DB timeout"))
    listener, mock_sqs = _make_listener(router=router, max_retries=3)
    message = _make_sqs_message({"type": "order.placed", "data": {}}, receive_count="1")

    result = await listener.process_message(message)

    assert result is False
    mock_sqs.change_message_visibility.assert_called_once()
    call_kwargs = mock_sqs.change_message_visibility.call_args[1]
    assert call_kwargs["ReceiptHandle"] == "receipt-123"
    assert 2 <= call_kwargs["VisibilityTimeout"] <= 4
    mock_sqs.delete_message.assert_not_called()
    mock_sqs.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_transient_error_exhausted_retries_sends_to_dlq():
    """Transient error with receive count >= max_retries sends to DLQ and acks."""
    router = MagicMock(spec=MessageRouter)
    router.route = AsyncMock(side_effect=RuntimeError("DB timeout"))
    listener, mock_sqs = _make_listener(router=router, max_retries=3)
    message = _make_sqs_message({"type": "order.placed", "data": {}}, receive_count="3")

    result = await listener.process_message(message)

    assert result is False
    mock_sqs.send_message.assert_called_once()
    mock_sqs.delete_message.assert_called_once()
    mock_sqs.change_message_visibility.assert_not_called()


@pytest.mark.asyncio
async def test_validation_error_sends_to_dlq_immediately():
    """ValueError sends to DLQ immediately without retry."""
    router = MagicMock(spec=MessageRouter)
    router.route = AsyncMock(side_effect=ValueError("Missing email"))
    listener, mock_sqs = _make_listener(router=router, max_retries=3)
    message = _make_sqs_message({"type": "user.created", "data": {}}, receive_count="1")

    result = await listener.process_message(message)

    assert result is False
    mock_sqs.send_message.assert_called_once()
    mock_sqs.delete_message.assert_called_once()
    mock_sqs.change_message_visibility.assert_not_called()


@pytest.mark.asyncio
async def test_unknown_event_type_acknowledged_no_dlq():
    """UnknownEventTypeError is acknowledged, no DLQ, no retry."""
    router = MagicMock(spec=MessageRouter)
    router.route = AsyncMock(side_effect=UnknownEventTypeError("bad.type"))
    listener, mock_sqs = _make_listener(router=router)
    message = _make_sqs_message({"type": "bad.type", "data": {}})

    result = await listener.process_message(message)

    assert result is False
    mock_sqs.delete_message.assert_called_once()
    mock_sqs.send_message.assert_not_called()
    mock_sqs.change_message_visibility.assert_not_called()


@pytest.mark.asyncio
async def test_missing_receive_count_defaults_to_first_attempt():
    """When ApproximateReceiveCount is absent, treat as attempt 1 and retry."""
    router = MagicMock(spec=MessageRouter)
    router.route = AsyncMock(side_effect=RuntimeError("transient"))
    listener, mock_sqs = _make_listener(router=router, max_retries=3)
    message = {
        "ReceiptHandle": "receipt-123",
        "Body": json.dumps({"type": "user.created", "data": {}}),
    }

    result = await listener.process_message(message)

    assert result is False
    mock_sqs.change_message_visibility.assert_called_once()
    mock_sqs.delete_message.assert_not_called()
    mock_sqs.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_poll_requests_approximate_receive_count():
    """poll() must request ApproximateReceiveCount in AttributeNames."""
    listener, mock_sqs = _make_listener()
    mock_sqs.receive_message.return_value = {"Messages": []}

    await listener.poll()

    call_kwargs = mock_sqs.receive_message.call_args[1]
    assert "ApproximateReceiveCount" in call_kwargs.get("AttributeNames", [])
