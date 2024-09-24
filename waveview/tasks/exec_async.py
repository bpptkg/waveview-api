import logging
from typing import Any, Callable, Dict, Iterable, Optional

from waveview.celery import app

logger = logging.getLogger(__name__)


@app.task(
    name="waveview.tasks.exec_async",
    default_retry_delay=60 * 5,
    max_retries=None,
)
def exec_async(
    function: Callable[..., Any],
    args: Optional[Iterable] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    **options,
) -> Any:
    """
    Execute a function asynchronously using Celery.
    """
    if args is None:
        args = ()
    if kwargs is None:
        kwargs = {}
    return function(*args, **kwargs)
