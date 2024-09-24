import time
from typing import Any, Callable


def delay(seconds: float) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            time.sleep(seconds)
            return func(*args, **kwargs)

        return wrapper

    return decorator
