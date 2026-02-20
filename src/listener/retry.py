from dataclasses import dataclass
from random import uniform as random

from src.listener.message_router import UnknownEventTypeError

PERMANENT_ERRORS: tuple[type[Exception], ...] = (ValueError, UnknownEventTypeError)


@dataclass(frozen=True)
class RetryPolicy:
    max_retries: int = 3
    base_delay: float = 1.0
    backoff_factor: float = 2.0
    max_delay: float = 60.0


def calculate_delay(policy: RetryPolicy, attempt: int) -> float:
    exponential = policy.base_delay * (policy.backoff_factor ** attempt)
    cap = min(exponential, policy.max_delay)
    return random(0, cap)


def is_transient_error(error: Exception) -> bool:
    return not isinstance(error, PERMANENT_ERRORS)
