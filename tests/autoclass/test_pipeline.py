from datetime import timedelta
from unittest.mock import Mock

import pytest
from django.utils import timezone

from waveview.event.models import Event, EventType
from .conftest import result_for
from waveview.contrib.autoclass import task
from waveview.contrib.autoclass.client import PredictionError, predict

pytestmark = pytest.mark.django_db


def run_prediction(event, monkeypatch, **result):
    task.enqueue_event(event)
    monkeypatch.setattr(task, 'predict', lambda e: result_for(e, **result))
    task.classify_event(str(event.id))
    event.refresh_from_db()
    return event


def test_disabled_catalog_has_no_work(event, settings):
    settings.AUTOCLASS_CATALOG_IDS = []
    task.enqueue_event(event)
    event.refresh_from_db()
    assert event.autoclass is None


def test_schedule_uses_event_time_and_survives_broker_failure(event, monkeypatch):
    event.time = timezone.now()
    event.save(update_fields=['time'])
    task.enqueue_event(event)
    event.refresh_from_db()
    assert event.autoclass['state'] == 'pending'
    assert timezone.datetime.fromisoformat(event.autoclass['due_at']) == event.time + timedelta(seconds=150)
    task.classify_event(str(event.id))
    event.refresh_from_db()
    assert event.autoclass['attempts'] == 0


@pytest.mark.parametrize('kind,code', [('VTA','VTA'), ('VTB','VTB'), ('MP','MP'), ('LF','LF'),
                                     ('TECT','TECT'), ('DG','GASBURST'), ('RF','ROCKFALL'), ('APG','AWANPANAS')])
def test_prediction_maps_type_without_validation(event, monkeypatch, kind, code):
    run_prediction(event, monkeypatch, jenis=kind, kelas='APRF_1' if kind in ('RF','APG') else kind)
    assert event.type.code == code
    assert (event.evaluation_mode, event.evaluation_status) == ('automatic','preliminary')
    assert event.method == 'stelte'
    assert event.autoclass['state'] == 'succeeded'
    assert event.autoclass['result']['jenis'] == kind


def test_inference_deduplicates_success(event, monkeypatch):
    run_prediction(event, monkeypatch)
    fail = Mock(side_effect=AssertionError('must not infer twice'))
    monkeypatch.setattr(task, 'predict', fail)
    task.classify_event(str(event.id))
    event.refresh_from_db()
    assert event.autoclass['attempts'] == 1


def test_manual_edit_while_predicting_wins(event, monkeypatch):
    task.enqueue_event(event)
    def inference(e):
        Event.objects.filter(id=e.id).update(
            evaluation_mode='manual', evaluation_status='confirmed', note='operator note',
            type=EventType.objects.get(organization=event.catalog.volcano.organization, code='MP'))
        return result_for(e)
    monkeypatch.setattr(task, 'predict', inference)
    task.classify_event(str(event.id))
    event.refresh_from_db()
    assert (event.type.code, event.evaluation_status, event.note) == ('MP','confirmed','operator note')
    assert event.autoclass['result']['jenis'] == 'VTB'
    assert event.autoclass['applied'] is False


def test_changed_time_and_deleted_event_do_not_apply(event, monkeypatch):
    task.enqueue_event(event)
    def inference(e):
        Event.objects.filter(id=e.id).update(time=e.time + timedelta(seconds=2))
        return result_for(e)
    monkeypatch.setattr(task, 'predict', inference)
    task.classify_event(str(event.id))
    event.refresh_from_db()
    assert event.type.code == 'AUTO'
    assert event.autoclass['state'] == 'stale'
    identity = str(event.id)
    event.delete()
    task.classify_event(identity)


def test_retry_exhausts_and_recovery_reclaims_lease(event, monkeypatch):
    task.enqueue_event(event)
    monkeypatch.setattr(task, 'predict', Mock(side_effect=PredictionError('data_unavailable', True)))
    for attempt in range(4):
        task.classify_event(str(event.id))
        event.refresh_from_db()
        assert event.autoclass['attempts'] == attempt + 1
        if attempt < 3:
            assert event.autoclass['state'] == 'retrying'
            event.autoclass['due_at'] = (timezone.now()-timedelta(seconds=1)).isoformat()
            event.save(update_fields=['autoclass'])
    assert event.autoclass['state'] == 'failed'


@pytest.mark.parametrize('change', [{'status':'gagal'}, {'jenis':'NOISE'}, {'prob_jenis':True},
    {'prob_jenis':float('nan')}, {'prob_jenis':1.1}, {'model':'different'}, {'versi':'9'},
    {'waktu_utc':'2020-01-01 00:00:00'}, {'eventid':'wrong'}, {'top3':[{'kelas':'BAD','p':1}]}])
def test_client_rejects_wrong_prediction_contract(event, monkeypatch, change):
    response = Mock(status_code=200, json=lambda: result_for(event, **change))
    monkeypatch.setattr('waveview.contrib.autoclass.client.requests.post', lambda *a, **k: response)
    with pytest.raises(PredictionError):
        predict(event)


def test_client_preserves_fractional_utc_and_disables_sinks(event, monkeypatch):
    def post(url, **kwargs):
        assert url == 'http://autoclass:8765/predict'
        assert kwargs['json']['waktu'] == event.time.isoformat().replace('+00:00','Z')
        assert kwargs['json']['simpan'] is False
        assert kwargs['json']['tunggu'] is False
        assert kwargs['headers']['X-Token'] == 'test-token'
        assert kwargs['allow_redirects'] is False
        return Mock(status_code=200, json=lambda: result_for(event))
    monkeypatch.setattr('waveview.contrib.autoclass.client.requests.post', post)
    assert predict(event)['jenis'] == 'VTB'


def test_recovery_reclaims_expired_work_and_late_attempt_cannot_apply(event, monkeypatch):
    task.enqueue_event(event)
    event.refresh_from_db()
    event.autoclass.update(state='running', attempts=1, attempt_id='old',
                           started_at=(timezone.now()-timedelta(seconds=601)).isoformat())
    event.save(update_fields=['autoclass'])
    monkeypatch.setattr(task, 'predict', lambda e: result_for(e))
    monkeypatch.setattr(task, '_dispatch', lambda job, identity, delay=0: job(identity))
    task.recover_events()
    event.refresh_from_db()
    assert event.autoclass['state'] == 'succeeded'
    assert event.autoclass['attempts'] == 2


def test_time_cleared_after_schedule_is_stale(event):
    task.enqueue_event(event)
    Event.objects.filter(pk=event.pk).update(time=None)
    task.classify_event(str(event.id))
    event.refresh_from_db()
    assert event.autoclass['state'] == 'stale'


def test_crash_retries_are_bounded(event, monkeypatch):
    task.enqueue_event(event)
    event.refresh_from_db()
    event.autoclass.update(state='running', attempts=4, attempt_id='old',
                           started_at=(timezone.now()-timedelta(seconds=601)).isoformat())
    event.save(update_fields=['autoclass'])
    monkeypatch.setattr(task, 'predict', Mock(side_effect=AssertionError('retries exhausted')))
    task.classify_event(str(event.id))
    event.refresh_from_db()
    assert event.autoclass['state'] == 'failed'
    assert event.autoclass['attempts'] == 4


def test_rolled_back_detector_work_is_not_persisted(event):
    from django.db import transaction
    with pytest.raises(RuntimeError), transaction.atomic():
        task.enqueue_event(event)
        raise RuntimeError('rollback')
    event.refresh_from_db()
    assert event.autoclass is None


def test_sinoas_creates_durable_work(event):
    from waveview.contrib.sinoas.context import SinoasContext
    from waveview.contrib.sinoas.detector import Detector, DetectedEvent
    context = SinoasContext(organization=event.catalog.volcano.organization,
                           volcano=event.catalog.volcano, user=event.author)
    Detector(context=context).create_event(DetectedEvent(event.time, 35, 4000))
    detected = Event.objects.exclude(pk=event.pk).get()
    assert detected.autoclass['state'] == 'pending'
    assert detected.autoclass['source'] == 'sinoas'


def test_autopicker_creates_durable_work(event, monkeypatch):
    from waveview.contrib.autopicker.task import create_event
    monkeypatch.setattr('waveview.contrib.autopicker.task.notify_event.delay', lambda *args: None)
    create_event({'t_on':event.time.isoformat(), 't_off':(event.time+timedelta(seconds=35)).isoformat(),
                  'picks':[{'stream_id':'VG.MEPAC.00.HHZ', 't_pick':event.time.isoformat(), 'offset':0}]})
    detected = Event.objects.exclude(pk=event.pk).get()
    assert detected.autoclass['state'] == 'pending'
    assert detected.autoclass['source'] == 'stelte'
