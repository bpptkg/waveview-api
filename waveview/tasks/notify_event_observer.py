import logging

from waveview.appconfig.models import EventObserverConfig
from waveview.celery import app
from waveview.event.observers import OperationType, observer_registry
from waveview.tasks.functions import exec_async

logger = logging.getLogger(__name__)


@app.task(
    name="waveview.tasks.notify_event_observer",
    default_retry_delay=60 * 5,
    max_retries=None,
)
def notify_event_observer(
    operation: OperationType,
    event_id: str,
    volcano_id: str,
    **options,
) -> None:
    """
    Notify an event observer that a new event has been created or updated.
    """
    items = EventObserverConfig.objects.filter(volcano_id=volcano_id).all()
    for item in items:
        if not observer_registry.has(item.name):
            logger.error(
                f"Observer class with name {item.name} is not registered. Skipping."
            )
            continue
        adapter = observer_registry.get(item.name)()
        if operation == OperationType.CREATE:
            exec_async(
                adapter.create,
                args=(event_id, item.data),
            )
        elif operation == OperationType.UPDATE:
            exec_async(
                adapter.update,
                args=(event_id, item.data),
            )
        elif operation == OperationType.DELETE:
            exec_async(
                adapter.delete,
                args=(event_id, item.data),
            )
