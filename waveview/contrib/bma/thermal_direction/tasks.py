import logging

from django.db import transaction
from django.utils import timezone

from waveview.celery import app
from waveview.contrib.bma.thermal_direction.bulletin import (
    BulletinDirectionClient,
    BulletinUpdateError,
)
from waveview.contrib.bma.thermal_direction.classifier import classify
from waveview.contrib.bma.thermal_direction.client import (
    ThermalAxisClient,
    ThermalAxisError,
)
from waveview.contrib.bma.thermal_direction.events import is_rf_or_apg
from waveview.contrib.bma.thermal_direction.note import (
    render_thermal_note,
    upsert_event_note,
)
from waveview.event.models import Event

logger = logging.getLogger(__name__)


@app.task(
    name="waveview.contrib.bma.thermal_direction.classify_thermal_direction",
    autoretry_for=(ThermalAxisError, BulletinUpdateError),
    retry_backoff=10,
    max_retries=3,
)
def classify_thermal_direction(event_id: str) -> None:
    """
    Classify thermal river direction for one RF/APG event and store it.

    Writes a thermal-direction block on ``Event.note`` and best-effort patches
    the related BMA bulletin. Non-RF/APG events are ignored.
    """
    try:
        event = Event.objects.select_related("type").get(id=event_id)
    except Event.DoesNotExist:
        logger.error("Event %s not found", event_id)
        return
    if event.time is None or not is_rf_or_apg(event):
        logger.info("Event %s is not an RF/APG with time; skipping", event_id)
        return

    client = ThermalAxisClient.from_settings()
    try:
        samples = client.fetch(event.time)
    except ThermalAxisError as exc:
        logger.error("Thermal axis fetch failed for event %s: %s", event_id, exc)
        if exc.retryable:
            raise
        return

    result = classify(samples, event.time)
    logger.info(
        "Thermal direction for event %s: hasil_akhir=%s arah=%s spike=%s",
        event_id,
        result.hasil_akhir,
        result.arah,
        result.spike_time,
    )

    with transaction.atomic():
        locked = (
            Event.objects.select_for_update().select_related("type").get(id=event_id)
        )
        if locked.time != event.time or not is_rf_or_apg(locked):
            logger.info(
                "Event %s changed during classification; leaving the note unchanged",
                event_id,
            )
            return
        block = render_thermal_note(result, timezone.now())
        locked.note = upsert_event_note(locked.note, block)
        locked.save(update_fields=["note", "updated_at"])
        refid = locked.refid
        event_time = locked.time
        event_type = locked.type.code if locked.type is not None else None

    BulletinDirectionClient.from_settings().push(
        refid=refid,
        event_time=event_time,
        result=result,
        event_type=event_type,
    )
