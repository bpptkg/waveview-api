import logging

from waveview.contrib.bma.thermal_direction.events import is_rf_or_apg
from waveview.event.models import Event
from waveview.event.observers import EventObserver

logger = logging.getLogger(__name__)

# Seconds to wait after the seismic event so the thermal axis has samples
# covering the ~2 minutes after the origin.
DEFAULT_DELAY_SECONDS = 120


def delay_seconds() -> int:
    from django.conf import settings

    raw = getattr(settings, "THERMAL_DIRECTION_DELAY", DEFAULT_DELAY_SECONDS)
    try:
        return max(int(raw), 0)
    except (TypeError, ValueError):
        return DEFAULT_DELAY_SECONDS


class ThermalDirectionObserver(EventObserver):
    """
    Schedule thermal river-axis direction classification for RF and APG events.

    Register this observer in Django admin Event Observer with name
    ``bma.thermal_direction``. Leave ``Run async`` unchecked. Set the order
    after ``bma.bulletin`` so the bulletin row exists before the delayed task
    writes direction fields.

    ``data`` is unused. Delay defaults to 120 seconds and can be overridden
    with the ``THERMAL_DIRECTION_DELAY`` setting.
    """

    name = "bma.thermal_direction"

    def create(self, event_id: str, data: dict, **options) -> None:
        self._schedule(event_id)

    def update(self, event_id: str, data: dict, **options) -> None:
        # Observers are not given the previous time or type. Re-schedule while
        # the event is RF/APG so a time change or a type change onto RF/APG
        # is classified again. The note block is replaced in place.
        self._schedule(event_id)

    def delete(self, event_id: str, data: dict, **options) -> None:
        logger.debug("Ignoring delete for thermal direction event %s", event_id)

    def _schedule(self, event_id: str) -> None:
        try:
            event = Event.objects.select_related("type").get(id=event_id)
        except Event.DoesNotExist:
            logger.error("Event %s not found", event_id)
            return
        if event.time is None or not is_rf_or_apg(event):
            logger.info(
                "Skipping thermal direction for event %s (not an RF/APG with time)",
                event_id,
            )
            return

        from waveview.contrib.bma.thermal_direction.tasks import (
            classify_thermal_direction,
        )

        countdown = delay_seconds()
        classify_thermal_direction.apply_async(
            args=[str(event_id)],
            countdown=countdown,
        )
        logger.info(
            "Scheduled thermal direction for event %s in %ss", event_id, countdown
        )
