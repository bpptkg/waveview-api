import logging
import time

logger = logging.getLogger(__name__)


def retry(max_retries: int = 5, retry_delay: int = 5) -> callable:
    """
    Retry execution of a function if operation failed until max_retries reached.
    """

    if int(max_retries) < 1:
        raise ValueError("max_retries value must be a positive integer and at least 1")

    def inner(func: callable) -> callable:
        def wrapper(*args, **kwargs):
            status = False

            for _ in range(int(max_retries)):
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    logger.error(
                        "%s function execution failed: %s. Retrying in %ss...",
                        func.__name__,
                        e,
                        retry_delay,
                    )
                    time.sleep(retry_delay)
            return status

        return wrapper

    return inner
