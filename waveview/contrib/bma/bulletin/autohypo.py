import logging
import math
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from django.conf import settings
from django.db import transaction

from waveview.contrib.bma.bulletin.loader import BulletinImporter
from waveview.event.header import EvaluationMode, EvaluationStatus
from waveview.event.models import Catalog, Event, Origin

logger = logging.getLogger(__name__)

VERIFIED = {
    EvaluationStatus.CONFIRMED,
    EvaluationStatus.REVIEWED,
    EvaluationStatus.FINAL,
}
EVENT_TYPES = {"VTA", "VTB"}


@dataclass(frozen=True)
class ApplyResult:
    status: str
    reason: str
    event_id: str | None = None
    preferred: bool | None = None
    latitude: float | None = None
    longitude: float | None = None
    depth: float | None = None


def _finite(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    return number


def _event_id(value: object) -> UUID | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return UUID(value)
    except ValueError:
        return None


def _select_nlloc(event: Event) -> Origin | None:
    rows = list(event.origins.filter(method="nlloc").order_by("created_at", "id"))
    for origin in rows:
        if origin.is_preferred:
            return origin
    return rows[0] if rows else None


def _preferred(event: Event, origin: Origin | None) -> bool:
    others = event.origins.filter(is_preferred=True)
    if origin is not None:
        others = others.exclude(pk=origin.pk)
    if others.exists():
        return bool(origin and origin.is_preferred)
    return True


def apply_autohypo(catalog: Catalog, row: dict, dry_run: bool = False) -> ApplyResult:
    eventtype = str(row.get("eventtype") or "").upper()
    if eventtype not in EVENT_TYPES:
        return ApplyResult("skipped", "type")
    autohypo = row.get("autohypo")
    if not isinstance(autohypo, dict):
        return ApplyResult("skipped", "autohypo")
    latitude = _finite(autohypo.get("lat"))
    longitude = _finite(autohypo.get("lon"))
    depth = _finite(autohypo.get("z"))
    if latitude is None or longitude is None or depth is None:
        return ApplyResult("skipped", "autohypo")
    raw_id = row.get("eventid")
    event_id = _event_id(raw_id)
    if event_id is None:
        return ApplyResult("skipped", "eventid", event_id=None if raw_id is None else str(raw_id))
    event = Event.objects.filter(catalog=catalog, pk=event_id).first()
    if event is None:
        return ApplyResult("skipped", "event", event_id=str(event_id))
    if event.evaluation_mode != EvaluationMode.MANUAL or event.evaluation_status not in VERIFIED:
        return ApplyResult("skipped", "status", event_id=str(event.pk))
    origin = _select_nlloc(event)
    preferred = _preferred(event, origin)
    result = ApplyResult(
        "dry_run" if dry_run else "written",
        "",
        event_id=str(event.pk),
        preferred=preferred,
        latitude=latitude,
        longitude=longitude,
        depth=depth,
    )
    if dry_run:
        return result
    with transaction.atomic():
        event = Event.objects.select_for_update().get(pk=event.pk, catalog=catalog)
        origin = _select_nlloc(event)
        preferred = _preferred(event, origin)
        if origin is None:
            Origin.objects.create(
                event=event,
                time=event.time,
                latitude=latitude,
                longitude=longitude,
                depth=depth,
                method="nlloc",
                evaluation_mode=EvaluationMode.AUTOMATIC,
                evaluation_status=EvaluationStatus.PRELIMINARY,
                is_preferred=preferred,
            )
        else:
            origin.time = event.time
            origin.latitude = latitude
            origin.longitude = longitude
            origin.depth = depth
            origin.evaluation_mode = EvaluationMode.AUTOMATIC
            origin.evaluation_status = EvaluationStatus.PRELIMINARY
            if preferred and not origin.is_preferred:
                origin.is_preferred = True
            origin.save()
    return ApplyResult(
        "written",
        "",
        event_id=str(event.pk),
        preferred=preferred,
        latitude=latitude,
        longitude=longitude,
        depth=depth,
    )


def bulletin_rows(payload: object) -> list[dict]:
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def sync_autohypo(
    catalog: Catalog,
    start: datetime,
    end: datetime,
    dry_run: bool = False,
    importer: BulletinImporter | None = None,
) -> list[ApplyResult]:
    if importer is None:
        importer = BulletinImporter(settings.BMA_URL, settings.BMA_API_KEY)
    payload = importer.fetch(start, end)
    results = []
    for item in bulletin_rows(payload):
        result = apply_autohypo(catalog, item, dry_run=dry_run)
        logger.info(
            "autohypo %s event=%s reason=%s preferred=%s lat=%s lon=%s depth=%s",
            result.status,
            result.event_id,
            result.reason,
            result.preferred,
            result.latitude,
            result.longitude,
            result.depth,
        )
        results.append(result)
    return results
