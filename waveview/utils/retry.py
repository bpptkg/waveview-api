import logging
import random
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)


def retry(
    max_retries=5,
    initial_delay=1,
    backoff_factor=2,
    jitter=0.1,
    name: str | None = None,
    exc_info: bool = False,
) -> callable:
    """
    Retry execution of a function if operation failed until max_retries reached.
    """

    if int(max_retries) < 1:
        raise ValueError("max_retries value must be a positive integer and at least 1")

    def inner(func) -> Callable[..., Any]:
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.error(
                        f"Attempt {attempt + 1} failed: {e}",
                        exc_info=exc_info,
                        extra={"func": name},
                    )
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(delay + random.uniform(-jitter, jitter))
                    delay *= backoff_factor

        return wrapper

    return inner
