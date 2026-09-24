import logging

from django.conf import settings
from django.utils import timezone

from waveview.celery import app
from waveview.contrib.bma.thermal_direction.bulletin import push_bulletin_direction
from waveview.contrib.bma.thermal_direction.classifier import (
    classify,
    is_rf_or_apg,
    upsert_thermal_note,
)
from waveview.contrib.bma.thermal_direction.client import ThermalAxisClient
from waveview.event.models import Event

logger = logging.getLogger(__name__)


@app.task(
    name="waveview.contrib.bma.thermal_direction.classify_thermal_direction",
    default_retry_delay=30,
    max_retries=3,
)
def classify_thermal_direction(event_id: str) -> None:
    """
    Classify thermal river direction for one RF/APG event and store the result.
    """
    try:
        event = Event.objects.select_related("type").get(id=event_id)
    except Event.DoesNotExist:
        logger.error("Event %s not found for thermal direction", event_id)
        return

    event_type = event.type
    code = event_type.code if event_type is not None else None
    name = event_type.name if event_type is not None else None
    if not is_rf_or_apg(code, name):
        logger.info(
            "Skipping thermal direction for event %s (type code=%s name=%s)",
            event_id,
            code,
            name,
        )
        return
    if event.time is None:
        logger.error("Event %s has no time", event_id)
        return

    base_url = settings.BMA_URL
    api_key = settings.BMA_API_KEY
    if not base_url or not api_key:
        logger.error("BMA_URL or BMA_API_KEY is not configured")
        return

    client = ThermalAxisClient(base_url, api_key)
    try:
        samples = client.fetch(event.time)
    except Exception:
        logger.exception("Failed to fetch thermal axis data for event %s", event_id)
        return

    result = classify(event.time, samples)
    event.note = upsert_thermal_note(event.note, result, timezone.now())
    event.save(update_fields=["note", "updated_at"])
    logger.info(
        "Thermal direction for event %s: hasil_akhir=%s arah=%s",
        event_id,
        result.hasil_akhir,
        result.arah,
    )

    try:
        push_bulletin_direction(
            base_url=base_url,
            api_key=api_key,
            bulletin_id=str(event.refid) if event.refid else None,
            result=result,
            event_time=event.time,
        )
    except Exception:
        logger.exception(
            "Best-effort BMA bulletin update failed for event %s", event_id
        )
