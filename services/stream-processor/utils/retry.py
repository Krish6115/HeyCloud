"""
Retry utility with exponential backoff for DynamoDB/S3 writes.

Why:
  - DynamoDB can return ProvisionedThroughputExceededException
  - S3 can have transient 500 errors
  - Retrying with jitter prevents thundering herd
"""

import random
import time
from functools import wraps
from typing import Callable

from utils.logger import get_logger

logger = get_logger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 0.1,
    max_delay: float = 5.0,
    retryable_exceptions: tuple = (Exception,),
) -> Callable:
    """Decorator that retries a function with exponential backoff + jitter.

    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay cap in seconds.
        retryable_exceptions: Tuple of exception types to retry on.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        # Exponential backoff with full jitter
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        jitter = random.uniform(0, delay)
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__}: "
                            f"{e}. Waiting {jitter:.2f}s"
                        )
                        time.sleep(jitter)

            logger.error(
                f"All {max_retries} retries exhausted for {func.__name__}",
                extra={"error": str(last_exception)},
            )
            raise last_exception

        return wrapper
    return decorator
