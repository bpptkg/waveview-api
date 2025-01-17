import logging

from waveview.appconfig.models import EventObserverConfig
from waveview.celery import app
from waveview.event.observers import OperationType, observer_registry
from waveview.tasks.exec_async import exec_async

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
    Notify an event observer based on the operation type.
    """
    names = options.pop("names", None)
    if names:
        if isinstance(names, str):
            names = [names]
        else:
            names = list(names)
        items = (
            EventObserverConfig.objects.filter(
                volcano_id=volcano_id, name__in=names, is_enabled=True
            )
            .order_by("order")
            .all()
        )
    else:
        items = (
            EventObserverConfig.objects.filter(volcano_id=volcano_id, is_enabled=True)
            .order_by("order")
            .all()
        )

    for item in items:
        if not observer_registry.has(item.name):
            logger.error(
                f"Observer class with name {item.name} is not registered. Skipping."
            )
            continue
        adapter = observer_registry.get(item.name)()
        try:
            if operation == OperationType.CREATE:
                if item.run_async:
                    exec_async.delay(
                        adapter.create,
                        args=(event_id, item.data),
                        kwargs=options,
                    )
                else:
                    adapter.create(event_id, item.data, **options)
            elif operation == OperationType.UPDATE:
                if item.run_async:
                    exec_async.delay(
                        adapter.update,
                        args=(event_id, item.data),
                        kwargs=options,
                    )
                else:
                    adapter.update(event_id, item.data, **options)
            elif operation == OperationType.DELETE:
                if item.run_async:
                    exec_async.delay(
                        adapter.delete,
                        args=(event_id, item.data),
                        kwargs=options,
                    )
                else:
                    adapter.delete(event_id, item.data, **options)
        except Exception as e:
            logger.error(
                f"Error notifying event observer {item.name} for event {event_id}: {e}"
            )
