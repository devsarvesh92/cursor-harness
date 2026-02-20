import pytest
from unittest.mock import patch

from src.listener.retry import RetryPolicy, calculate_delay


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
