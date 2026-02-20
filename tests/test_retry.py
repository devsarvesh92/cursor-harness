import pytest
from unittest.mock import patch

from botocore.exceptions import ClientError
from src.listener.message_router import UnknownEventTypeError
from src.listener.retry import RetryPolicy, calculate_delay, is_transient_error


class TestRetryPolicyDefaults:
    def test_default_values(self):
        policy = RetryPolicy()

        assert policy.max_retries == 3
        assert policy.base_delay == 1.0
        assert policy.backoff_factor == 2.0
        assert policy.max_delay == 60.0


class TestCalculateDelay:
    def test_first_attempt_bounded_by_base_delay(self):
        policy = RetryPolicy(base_delay=1.0, backoff_factor=2.0)

        delay = calculate_delay(policy, attempt=0)

        assert 0 <= delay <= 1.0

    def test_second_attempt_bounded_by_base_times_factor(self):
        policy = RetryPolicy(base_delay=1.0, backoff_factor=2.0)

        delay = calculate_delay(policy, attempt=1)

        assert 0 <= delay <= 2.0

    def test_third_attempt_bounded_by_base_times_factor_squared(self):
        policy = RetryPolicy(base_delay=1.0, backoff_factor=2.0)

        delay = calculate_delay(policy, attempt=2)

        assert 0 <= delay <= 4.0

    def test_delay_capped_at_max_delay(self):
        policy = RetryPolicy(base_delay=1.0, backoff_factor=10.0, max_delay=5.0)

        delay = calculate_delay(policy, attempt=5)

        assert 0 <= delay <= 5.0

    @patch("src.listener.retry.random")
    def test_full_jitter_uses_random_uniform(self, mock_random):
        mock_random.return_value = 0.5
        policy = RetryPolicy(base_delay=2.0, backoff_factor=2.0, max_delay=60.0)

        delay = calculate_delay(policy, attempt=1)

        mock_random.assert_called_once_with(0, 4.0)
        assert delay == 0.5


class TestIsTransientError:
    def test_value_error_is_permanent(self):
        assert is_transient_error(ValueError("bad data")) is False

    def test_unknown_event_type_error_is_permanent(self):
        assert is_transient_error(UnknownEventTypeError("nope")) is False

    def test_connection_error_is_transient(self):
        assert is_transient_error(ConnectionError("refused")) is True

    def test_timeout_error_is_transient(self):
        assert is_transient_error(TimeoutError("timed out")) is True

    def test_os_error_is_transient(self):
        assert is_transient_error(OSError("network unreachable")) is True

    def test_client_error_is_transient(self):
        error = ClientError(
            {"Error": {"Code": "ServiceUnavailable", "Message": "try later"}},
            "ReceiveMessage",
        )
        assert is_transient_error(error) is True

    def test_generic_runtime_error_defaults_to_transient(self):
        assert is_transient_error(RuntimeError("unknown")) is True

    def test_generic_exception_defaults_to_transient(self):
        assert is_transient_error(Exception("surprise")) is True
