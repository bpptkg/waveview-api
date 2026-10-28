"""Durable event work; the broker is a wake-up mechanism, not completion state."""

import logging
import math
import uuid
from datetime import timedelta
from functools import partial

from django.conf import settings
from django.db import connection, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from waveview.celery import app
from waveview.contrib.autoclass.bma import push_bulletin
from waveview.contrib.autoclass.client import TYPES, PredictionError, predict
from waveview.event.models import Event, EventType
from waveview.event.observers import OperationType
from waveview.notifications.types import NotifyEventData
from waveview.tasks.notify_event import notify_event

logger = logging.getLogger(__name__)
RETRIES = (30, 120, 300)


def enabled(event):
    return (
        str(event.catalog_id) in settings.AUTOCLASS_CATALOG_IDS
        and event.catalog.volcano.slug == "merapi"
    )


def eligible(event):
    return (
        enabled(event)
        and not event.refid
        and event.time is not None
        and event.method in ("stelte", "sinoas")
        and event.type is not None
        and (event.type.code == "AUTO" or event.autoclass is not None)
        and event.evaluation_mode == "automatic"
        and event.evaluation_status == "preliminary"
    )


def classifiable(event):
    return eligible(event) or (
        enabled(event)
        and not event.refid
        and event.time is not None
        and event.method == "veps"
        and event.type is not None
        and event.evaluation_mode == "manual"
    )


def _dispatch(job, event_id, delay=0):
    try:
        job.apply_async(args=[event_id], countdown=delay)
    except Exception:
        logger.exception(
            "Could not dispatch autoclass work for event %s; recovery will retry",
            event_id,
        )


def _notify(event):
    if event.author_id is None:
        return
    try:
        payload = NotifyEventData.from_event(
            str(event.author_id), str(event.catalog.volcano.organization_id), event
        )
        notify_event.delay(OperationType.UPDATE, payload.to_dict())
    except Exception:
        logger.exception("Could not notify autoclass update for event %s", event.id)


def _save(event, data):
    event.autoclass = data
    Event.objects.filter(pk=event.pk).update(autoclass=data, updated_at=timezone.now())
    transaction.on_commit(partial(_notify, event))


def _schedule(event, data):
    delay = max(
        0, math.ceil((parse_datetime(data["due_at"]) - timezone.now()).total_seconds())
    )
    transaction.on_commit(partial(_dispatch, classify_event, str(event.id), delay))


@transaction.atomic
def enqueue_event(event):
    if str(event.catalog_id) not in settings.AUTOCLASS_CATALOG_IDS:
        return
    original_event = event
    event = (
        Event.objects.select_for_update(of=("self",))
        .select_related("type", "catalog__volcano")
        .get(pk=event.pk)
    )
    if not classifiable(event):
        return
    input_time = event.time.isoformat()
    previous = event.autoclass or {}
    if previous.get("input_time") == input_time:
        return
    now = timezone.now()
    data = {
        "state": "pending",
        "source": event.method,
        "input_time": input_time,
        "revision": settings.AUTOCLASS_REVISION,
        "attempts": 0,
        "result": None,
        "applied": False,
        "due_at": max(now, event.time + timedelta(seconds=150)).isoformat(),
        "sync": {"state": "waiting_validation", "attempts": 0},
    }
    if previous.get("validation"):
        data["validation"] = previous["validation"]
    if event.time > now + timedelta(minutes=5):
        data.update(state="failed", error="invalid_time")
    _save(event, data)
    original_event.autoclass = data
    if data["state"] == "pending":
        _schedule(event, data)


@app.task(name="waveview.contrib.autoclass.classify_event")
def classify_event(event_id):
    with transaction.atomic():
        event = (
            Event.objects.select_for_update(of=("self",))
            .select_related("type", "catalog__volcano")
            .filter(pk=event_id)
            .first()
        )
        if event is None or not event.autoclass:
            return
        data = event.autoclass
        if data["state"] not in ("pending", "retrying", "running"):
            return
        now = timezone.now()
        if not enabled(event):
            _save(event, dict(data, state="skipped", error="disabled"))
            return
        if (
            event.time is None
            or data["input_time"] != event.time.isoformat()
            or data["revision"] != settings.AUTOCLASS_REVISION
        ):
            _save(event, dict(data, state="stale"))
            return
        if not classifiable(event):
            _save(event, dict(data, state="skipped", error="manual_change"))
            return
        if data["state"] == "running" and parse_datetime(
            data["started_at"]
        ) > now - timedelta(seconds=600):
            return
        if parse_datetime(data["due_at"]) > now:
            return
        if data["attempts"] >= 4:
            _save(event, dict(data, state="failed", error="retries_exhausted"))
            return
        attempt = uuid.uuid4().hex
        data.update(
            state="running",
            started_at=now.isoformat(),
            attempt_id=attempt,
            attempts=data["attempts"] + 1,
            error=None,
        )
        _save(event, data)
    try:
        result, error = predict(event), None
    except PredictionError as exc:
        result, error = None, exc
    except Exception:
        logger.exception("Autoclass failed for event %s", event_id)
        result, error = None, PredictionError("unavailable", True)
    with transaction.atomic():
        event = (
            Event.objects.select_for_update(of=("self",))
            .select_related("type", "catalog__volcano")
            .filter(pk=event_id)
            .first()
        )
        if (
            event is None
            or not event.autoclass
            or event.autoclass.get("attempt_id") != attempt
        ):
            return
        data = event.autoclass
        if (
            event.time is None
            or data["input_time"] != event.time.isoformat()
            or data["revision"] != settings.AUTOCLASS_REVISION
        ):
            _save(event, dict(data, state="stale", result=result))
            return
        if not enabled(event):
            _save(event, dict(data, state="skipped", result=result, error="disabled"))
            return
        if error:
            data.update(state="failed", error=error.code)
            if (
                error.retryable
                and data["attempts"] <= len(RETRIES)
                and classifiable(event)
            ):
                data.update(
                    state="retrying",
                    due_at=(
                        timezone.now()
                        + timedelta(seconds=RETRIES[data["attempts"] - 1])
                    ).isoformat(),
                )
                _schedule(event, data)
        else:
            data.update(
                state="succeeded",
                result=result,
                finished_at=timezone.now().isoformat(),
                applied=False,
            )
            if eligible(event):
                event_type = EventType.objects.filter(
                    organization_id=event.catalog.volcano.organization_id,
                    code=TYPES[result["jenis"]],
                ).first()
                if event_type is None:
                    data.update(state="failed", error="mapping_missing")
                else:
                    data["previous_type"] = event.type.code
                    event.type = event_type
                    Event.objects.filter(pk=event.pk).update(type=event_type)
                    data["applied"] = True
        _save(event, data)
        if event.evaluation_mode == "manual":
            schedule_sync(event)


@app.task(name="waveview.contrib.autoclass.recover_events")
def recover_events():
    now = timezone.now()
    due = Q(
        autoclass__state__in=["pending", "retrying"],
        autoclass__due_at__lte=now.isoformat(),
    )
    expired = Q(
        autoclass__state="running",
        autoclass__started_at__lte=(now - timedelta(seconds=600)).isoformat(),
    )
    ids = Event.objects.filter(
        due | expired, catalog_id__in=settings.AUTOCLASS_CATALOG_IDS
    ).values_list("id", flat=True)[:200]
    for event_id in ids:
        _dispatch(classify_event, str(event_id))
    sync_ids = Event.objects.filter(
        catalog_id__in=settings.AUTOCLASS_CATALOG_IDS,
        autoclass__sync__state__in=["pending", "retrying"],
        autoclass__sync__due_at__lte=now.isoformat(),
    ).values_list("id", flat=True)[:200]
    for event_id in sync_ids:
        _dispatch(sync_event, str(event_id))


@transaction.atomic
def schedule_sync(event):
    current = Event.objects.select_for_update().filter(pk=event.pk).first()
    if current is None or not current.autoclass or not enabled(current):
        return
    ready = current.evaluation_mode == "manual" and current.evaluation_status in (
        "confirmed",
        "reviewed",
        "final",
        "rejected",
    )
    data = current.autoclass
    data["sync"] = {
        "state": "pending" if ready else "waiting_validation",
        "attempts": 0,
        "revision": uuid.uuid4().hex,
        "due_at": timezone.now().isoformat(),
    }
    _save(current, data)
    event.autoclass = data
    if ready:
        transaction.on_commit(partial(_dispatch, sync_event, str(event.pk)))


@app.task(name="waveview.contrib.autoclass.sync_event")
def sync_event(event_id):
    # Serialize outbound writes without blocking the operator's row during HTTP.
    key = uuid.UUID(event_id).int % (2**63)
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_try_advisory_lock(%s)", [key])
        if not cursor.fetchone()[0]:
            return
    try:
        for _ in range(2):
            event = (
                Event.objects.select_related("type", "author", "catalog__volcano")
                .filter(pk=event_id)
                .first()
            )
            if event is None or not event.autoclass or not enabled(event):
                return
            sync = event.autoclass.get("sync", {})
            if event.evaluation_mode != "manual" or event.evaluation_status not in (
                "confirmed",
                "reviewed",
                "final",
                "rejected",
            ):
                return
            if (
                sync.get("state") not in ("pending", "retrying")
                or parse_datetime(sync["due_at"]) > timezone.now()
            ):
                return
            revision = sync["revision"]
            try:
                push_bulletin(event)
                error = False
            except Exception:
                logger.exception("BMA autoclass sync failed for event %s", event_id)
                error = True
            with transaction.atomic():
                current = Event.objects.select_for_update().filter(pk=event_id).first()
                if current is None:
                    return
                if current.autoclass["sync"]["revision"] != revision:
                    continue
                sync["attempts"] += 1
                sync.update(
                    state="synced" if not error else "failed",
                    error="bma_unavailable" if error else None,
                )
                if error and sync["attempts"] <= len(RETRIES):
                    delay = RETRIES[sync["attempts"] - 1]
                    sync.update(
                        state="retrying",
                        due_at=(timezone.now() + timedelta(seconds=delay)).isoformat(),
                    )
                    transaction.on_commit(
                        partial(_dispatch, sync_event, event_id, delay)
                    )
                _save(current, dict(current.autoclass, sync=sync))
                return
    finally:
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_unlock(%s)", [key])
