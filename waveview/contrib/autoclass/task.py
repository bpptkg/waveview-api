"""Durable event work; the broker is a wake-up mechanism, not completion state."""
import logging
import math
import uuid
from datetime import timedelta
from functools import partial

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from waveview.celery import app
from waveview.contrib.autoclass.client import TYPES, PredictionError, predict
from waveview.event.models import Event, EventType
from waveview.event.observers import OperationType
from waveview.notifications.types import NotifyEventData
from waveview.tasks.notify_event import notify_event

logger = logging.getLogger(__name__)
RETRIES = (30, 120, 300)


def enabled(event):
    return (str(event.catalog_id) in settings.AUTOCLASS_CATALOG_IDS
            and event.catalog.volcano.slug == 'merapi')


def eligible(event):
    return (enabled(event) and not event.refid and event.time is not None
            and event.method in ('stelte', 'sinoas') and event.type is not None
            and event.type.code == 'AUTO' and event.evaluation_mode == 'automatic'
            and event.evaluation_status == 'preliminary')


def _dispatch(job, event_id, delay=0):
    try:
        job.apply_async(args=[event_id], countdown=delay)
    except Exception:
        logger.exception('Could not dispatch autoclass work for event %s; recovery will retry', event_id)


def _notify(event):
    if event.author_id is None:
        return
    payload = NotifyEventData.from_event(str(event.author_id), str(event.catalog.volcano.organization_id), event)
    try:
        notify_event.delay(OperationType.UPDATE, payload.to_dict())
    except Exception:
        logger.exception('Could not notify autoclass update for event %s', event.id)


def _save(event, data):
    event.autoclass = data
    Event.objects.filter(pk=event.pk).update(autoclass=data, updated_at=timezone.now())


def _schedule(event, data):
    delay = max(0, math.ceil((parse_datetime(data['due_at']) - timezone.now()).total_seconds()))
    transaction.on_commit(partial(_dispatch, classify_event, str(event.id), delay))


@transaction.atomic
def enqueue_event(event):
    event = Event.objects.select_for_update(of=('self',)).select_related('type', 'catalog__volcano').get(pk=event.pk)
    if not eligible(event) or event.autoclass is not None:
        return
    now = timezone.now()
    data = {'state': 'pending', 'source': event.method, 'input_time': event.time.isoformat(),
            'revision': settings.AUTOCLASS_REVISION, 'attempts': 0, 'result': None, 'applied': False,
            'due_at': max(now, event.time + timedelta(seconds=150)).isoformat(),
            'sync': {'state': 'waiting_validation', 'attempts': 0}}
    if event.time > now + timedelta(minutes=5):
        data.update(state='failed', error='invalid_time')
    _save(event, data)
    if data['state'] == 'pending':
        _schedule(event, data)


@app.task(name='waveview.contrib.autoclass.classify_event')
def classify_event(event_id):
    with transaction.atomic():
        event = Event.objects.select_for_update(of=('self',)).select_related('type', 'catalog__volcano').filter(pk=event_id).first()
        if event is None or not event.autoclass:
            return
        data = event.autoclass
        if data['state'] not in ('pending', 'retrying', 'running'):
            return
        now = timezone.now()
        if not enabled(event):
            _save(event, dict(data, state='skipped', error='disabled'))
            return
        if event.time is None or data['input_time'] != event.time.isoformat() or data['revision'] != settings.AUTOCLASS_REVISION:
            _save(event, dict(data, state='stale'))
            return
        if not eligible(event):
            _save(event, dict(data, state='skipped', error='manual_change'))
            return
        if data['state'] == 'running' and parse_datetime(data['started_at']) > now - timedelta(seconds=600):
            return
        if parse_datetime(data['due_at']) > now:
            return
        if data['attempts'] >= 4:
            _save(event, dict(data, state='failed', error='retries_exhausted'))
            return
        attempt = uuid.uuid4().hex
        data.update(state='running', started_at=now.isoformat(), attempt_id=attempt,
                    attempts=data['attempts'] + 1, error=None)
        _save(event, data)
    try:
        result, error = predict(event), None
    except PredictionError as exc:
        result, error = None, exc
    except Exception:
        logger.exception('Autoclass failed for event %s', event_id)
        result, error = None, PredictionError('unavailable', True)
    with transaction.atomic():
        event = Event.objects.select_for_update(of=('self',)).select_related('type', 'catalog__volcano').filter(pk=event_id).first()
        if event is None or not event.autoclass or event.autoclass.get('attempt_id') != attempt:
            return
        data = event.autoclass
        if event.time is None or data['input_time'] != event.time.isoformat() or data['revision'] != settings.AUTOCLASS_REVISION:
            _save(event, dict(data, state='stale', result=result))
            return
        if not enabled(event):
            _save(event, dict(data, state='skipped', result=result, error='disabled'))
            return
        if error:
            data.update(state='failed', error=error.code)
            if error.retryable and data['attempts'] <= len(RETRIES) and eligible(event):
                data.update(state='retrying', due_at=(timezone.now() + timedelta(seconds=RETRIES[data['attempts'] - 1])).isoformat())
                _schedule(event, data)
        else:
            data.update(state='succeeded', result=result, finished_at=timezone.now().isoformat(), applied=False)
            if eligible(event):
                event_type = EventType.objects.filter(organization_id=event.catalog.volcano.organization_id,
                                                      code=TYPES[result['jenis']]).first()
                if event_type is None:
                    data.update(state='failed', error='mapping_missing')
                else:
                    data['previous_type'] = event.type.code
                    event.type = event_type
                    Event.objects.filter(pk=event.pk).update(type=event_type)
                    data['applied'] = True
        _save(event, data)
        transaction.on_commit(partial(_notify, event))


@app.task(name='waveview.contrib.autoclass.recover_events')
def recover_events():
    now = timezone.now()
    due = Q(autoclass__state__in=['pending', 'retrying'], autoclass__due_at__lte=now.isoformat())
    expired = Q(autoclass__state='running', autoclass__started_at__lte=(now - timedelta(seconds=600)).isoformat())
    ids = Event.objects.filter(due | expired, catalog_id__in=settings.AUTOCLASS_CATALOG_IDS).values_list('id', flat=True)[:200]
    for event_id in ids:
        _dispatch(classify_event, str(event_id))
