import json
import pytest
from unittest.mock import AsyncMock, MagicMock, call, patch

from botocore.exceptions import ClientError

from src.listener.message_router import MessageRouter, UnknownEventTypeError
from src.listener.retry import RetryPolicy
from src.listener.sqs_listener import SQSListener


def make_sqs_message(body: dict) -> dict:
    return {
        "ReceiptHandle": "test-receipt-handle",
        "Body": json.dumps(body),
    }


@pytest.fixture
def router():
    return MagicMock(spec=MessageRouter)


@pytest.fixture
def listener(router):
    policy = RetryPolicy(max_retries=3, base_delay=0.01, backoff_factor=2.0)
    with patch("src.listener.sqs_listener.boto3"):
        sqs_listener = SQSListener(
            queue_url="https://sqs.example.com/test-queue",
            router=router,
            dlq_url="https://sqs.example.com/test-dlq",
            retry_policy=policy,
        )
    return sqs_listener


class TestProcessMessageRetryTransient:
    @pytest.mark.asyncio
    async def test_retries_transient_error_then_succeeds(self, listener, router):
        # Arrange
        router.route = AsyncMock(
            side_effect=[ConnectionError("refused"), None]
        )
        message = make_sqs_message({"type": "user.created", "data": {}})

        # Act
        result = await listener.process_message(message)

        # Assert
        assert result is True
        assert router.route.call_count == 2

    @pytest.mark.asyncio
    async def test_exhausts_retries_then_sends_to_dlq(self, listener, router):
        # Arrange
        router.route = AsyncMock(
            side_effect=ConnectionError("refused")
        )
        listener.send_to_dlq = AsyncMock()
        listener.acknowledge_message = AsyncMock()
        message = make_sqs_message({"type": "order.placed", "data": {}})

        # Act
        result = await listener.process_message(message)

        # Assert
        assert result is False
        assert router.route.call_count == 4  # 1 initial + 3 retries
        listener.send_to_dlq.assert_called_once()
        listener.acknowledge_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_logs_each_retry_attempt(self, listener, router):
        # Arrange
        router.route = AsyncMock(
            side_effect=[ConnectionError("refused"), None]
        )
        message = make_sqs_message({"type": "user.created", "data": {}})

        # Act
        with patch("src.listener.sqs_listener.logger") as mock_logger:
            await listener.process_message(message)

        # Assert — at least one warning log for the retry attempt
        retry_logs = [
            call for call in mock_logger.warning.call_args_list
            if "Retry" in str(call) or "retry" in str(call)
        ]
        assert len(retry_logs) >= 1

    @pytest.mark.asyncio
    async def test_logs_exhaustion_before_dlq(self, listener, router):
        # Arrange
        router.route = AsyncMock(side_effect=ConnectionError("refused"))
        listener.send_to_dlq = AsyncMock()
        listener.acknowledge_message = AsyncMock()
        message = make_sqs_message({"type": "test.event", "data": {}})

        # Act
        with patch("src.listener.sqs_listener.logger") as mock_logger:
            await listener.process_message(message)

        # Assert — error log about exhausting retries
        exhaustion_logs = [
            call for call in mock_logger.error.call_args_list
            if "exhausted" in str(call).lower() or "Exhausted" in str(call)
        ]
        assert len(exhaustion_logs) >= 1


class TestProcessMessagePermanentErrors:
    @pytest.mark.asyncio
    async def test_value_error_skips_retries_sends_to_dlq(self, listener, router):
        # Arrange
        router.route = AsyncMock(side_effect=ValueError("bad data"))
        listener.send_to_dlq = AsyncMock()
        listener.acknowledge_message = AsyncMock()
        message = make_sqs_message({"type": "user.created", "data": {}})

        # Act
        result = await listener.process_message(message)

        # Assert
        assert result is False
        assert router.route.call_count == 1  # no retries
        listener.send_to_dlq.assert_called_once()

    @pytest.mark.asyncio
    async def test_unknown_event_type_skips_retries_no_dlq(self, listener, router):
        # Arrange
        router.route = AsyncMock(
            side_effect=UnknownEventTypeError("unknown")
        )
        listener.send_to_dlq = AsyncMock()
        listener.acknowledge_message = AsyncMock()
        message = make_sqs_message({"type": "unknown.event", "data": {}})

        # Act
        result = await listener.process_message(message)

        # Assert
        assert result is False
        assert router.route.call_count == 1  # no retries
        listener.send_to_dlq.assert_not_called()
        listener.acknowledge_message.assert_called_once()


class TestVisibilityTimeoutExtension:
    @pytest.mark.asyncio
    async def test_extends_visibility_before_retry(self, listener, router):
        # Arrange
        router.route = AsyncMock(
            side_effect=[ConnectionError("refused"), None]
        )
        message = make_sqs_message({"type": "user.created", "data": {}})

        # Act
        await listener.process_message(message)

        # Assert — change_message_visibility was called for the retry
        listener.sqs.change_message_visibility.assert_called_once()
        call_kwargs = listener.sqs.change_message_visibility.call_args
        assert call_kwargs[1]["QueueUrl"] == listener.queue_url
        assert call_kwargs[1]["ReceiptHandle"] == "test-receipt-handle"
        assert call_kwargs[1]["VisibilityTimeout"] > 0

    @pytest.mark.asyncio
    async def test_visibility_extension_failure_does_not_block_retry(
        self, listener, router
    ):
        # Arrange
        router.route = AsyncMock(
            side_effect=[ConnectionError("refused"), None]
        )
        listener.sqs.change_message_visibility.side_effect = ClientError(
            {"Error": {"Code": "InvalidParameterValue", "Message": "bad"}},
            "ChangeMessageVisibility",
        )
        message = make_sqs_message({"type": "user.created", "data": {}})

        # Act
        result = await listener.process_message(message)

        # Assert — retry still succeeded despite visibility extension failure
        assert result is True
        assert router.route.call_count == 2

    @pytest.mark.asyncio
    async def test_visibility_extension_logs_on_failure(self, listener, router):
        # Arrange
        router.route = AsyncMock(
            side_effect=[ConnectionError("refused"), None]
        )
        listener.sqs.change_message_visibility.side_effect = ClientError(
            {"Error": {"Code": "InvalidParameterValue", "Message": "bad"}},
            "ChangeMessageVisibility",
        )
        message = make_sqs_message({"type": "user.created", "data": {}})

        # Act
        with patch("src.listener.sqs_listener.logger") as mock_logger:
            await listener.process_message(message)

        # Assert
        visibility_logs = [
            c for c in mock_logger.warning.call_args_list
            if "visibility" in str(c).lower()
        ]
        assert len(visibility_logs) >= 1


class TestPollingBackoff:
    @pytest.mark.asyncio
    async def test_poll_error_uses_exponential_backoff(self, listener):
        # Arrange
        listener.sqs.receive_message.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable", "Message": "down"}},
            "ReceiveMessage",
        )

        # Act
        with patch("src.listener.sqs_listener.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await listener.poll()

        # Assert — sleep was called with a value derived from backoff, not flat 5s
        mock_sleep.assert_called_once()
        delay = mock_sleep.call_args[0][0]
        assert 0 <= delay <= listener.retry_policy.base_delay

    @pytest.mark.asyncio
    async def test_consecutive_poll_errors_increase_backoff(self, listener):
        # Arrange
        listener.sqs.receive_message.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable", "Message": "down"}},
            "ReceiveMessage",
        )
        delays = []

        async def capture_delay(d):
            delays.append(d)

        # Act — poll three times in a row
        with patch("src.listener.sqs_listener.asyncio.sleep", side_effect=capture_delay):
            await listener.poll()
            await listener.poll()
            await listener.poll()

        # Assert — three delays recorded, max bound increases each time
        assert len(delays) == 3
        policy = listener.retry_policy
        for i, delay in enumerate(delays):
            cap = min(policy.base_delay * (policy.backoff_factor ** i), policy.max_delay)
            assert 0 <= delay <= cap

    @pytest.mark.asyncio
    async def test_successful_poll_resets_backoff(self, listener):
        # Arrange — first call fails, second succeeds, third fails
        error = ClientError(
            {"Error": {"Code": "ServiceUnavailable", "Message": "down"}},
            "ReceiveMessage",
        )
        listener.sqs.receive_message.side_effect = [
            error,
            {"Messages": []},
            error,
        ]
        delays = []

        async def capture_delay(d):
            delays.append(d)

        # Act
        with patch("src.listener.sqs_listener.asyncio.sleep", side_effect=capture_delay):
            await listener.poll()   # fail -> attempt 0 backoff
            await listener.poll()   # success -> reset
            await listener.poll()   # fail -> attempt 0 backoff again (reset)

        # Assert — both error delays bounded by attempt-0 cap (reset happened)
        assert len(delays) == 2
        cap_attempt_0 = listener.retry_policy.base_delay
        assert 0 <= delays[0] <= cap_attempt_0
        assert 0 <= delays[1] <= cap_attempt_0

    @pytest.mark.asyncio
    async def test_polling_backoff_capped_at_max_delay(self, listener):
        # Arrange — use a policy with aggressive factor to hit the cap fast
        listener.retry_policy = RetryPolicy(
            base_delay=1.0, backoff_factor=100.0, max_delay=5.0
        )
        listener.sqs.receive_message.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable", "Message": "down"}},
            "ReceiveMessage",
        )
        delays = []

        async def capture_delay(d):
            delays.append(d)

        # Act — poll twice so attempt=1 would be 100.0 without cap
        with patch("src.listener.sqs_listener.asyncio.sleep", side_effect=capture_delay):
            await listener.poll()
            await listener.poll()

        # Assert
        assert len(delays) == 2
        assert delays[1] <= 5.0
