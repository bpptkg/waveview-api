import logging

from django.conf import settings

from waveview.event.observers import EventObserver

logger = logging.getLogger(__name__)

DEFAULT_DELAY_SECONDS = 120


class ThermalDirectionObserver(EventObserver):
    """
    Schedule thermal river-axis classification after an event is saved.

    Register this observer in Django admin as ``bma.thermal_direction``.
    ``delete`` is ignored. ``update`` re-queues the task; the task itself
    skips events whose type code/name is not RF or APG.
    """

    name = "bma.thermal_direction"

    def create(self, event_id: str, data: dict, **options) -> None:
        self._schedule(event_id, data)

    def update(self, event_id: str, data: dict, **options) -> None:
        self._schedule(event_id, data)

    def delete(self, event_id: str, data: dict, **options) -> None:
        return

    def _schedule(self, event_id: str, data: dict) -> None:
        from waveview.contrib.bma.thermal_direction.task import (
            classify_thermal_direction,
        )

        countdown = _countdown(data)
        logger.info(
            "Scheduling thermal direction for event %s in %s seconds",
            event_id,
            countdown,
        )
        classify_thermal_direction.apply_async(
            args=[str(event_id)],
            countdown=countdown,
        )


def _countdown(data: dict | None) -> int:
    if isinstance(data, dict) and data.get("delay") is not None:
        return int(data["delay"])
    return int(getattr(settings, "THERMAL_DIRECTION_DELAY", DEFAULT_DELAY_SECONDS))
