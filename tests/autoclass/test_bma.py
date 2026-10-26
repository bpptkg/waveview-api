from datetime import timedelta
from types import SimpleNamespace

import pytest

from waveview.contrib.autoclass import task
from waveview.contrib.bma.bulletin.observer import BulletinObserver
from waveview.contrib.bma.bulletin.loader import BulletinLoader, BulletinLoaderContext
from waveview.contrib.bma.bulletin.serializers import BulletinPayloadSerializer
from waveview.event.models import Event, EventType
from waveview.event.serializers.event import EventPayloadSerializer
from .test_pipeline import run_prediction

pytestmark = pytest.mark.django_db


def confirm(event):
    serializer = EventPayloadSerializer(event, data={'evaluation_mode':'manual',
        'evaluation_status':'confirmed','method':'veps'}, partial=True,
        context={'request':SimpleNamespace(user=event.author)})
    assert serializer.is_valid(), serializer.errors
    return serializer.save()


def test_preliminary_cannot_bypass_sync_via_old_observer(event, monkeypatch):
    run_prediction(event, monkeypatch)
    def unexpected(*args, **kwargs):
        pytest.fail('preliminary bulletin must not be sent')
    monkeypatch.setattr('waveview.contrib.bma.bulletin.client.BulletinClient.create', unexpected)
    BulletinObserver().create(str(event.id), {'server_url':'http://bma.test/','token':'test'})
    task.sync_event(str(event.id))
    event.refresh_from_db()
    assert event.autoclass['sync']['state'] == 'waiting_validation'


def test_sync_uses_manual_type_and_retains_prediction(event, monkeypatch):
    run_prediction(event, monkeypatch)
    kind = EventType.objects.get(organization=event.catalog.volcano.organization, code='MP')
    Event.objects.filter(pk=event.pk).update(type=kind)
    event.refresh_from_db()
    event = confirm(event)
    writes=[]
    monkeypatch.setattr(task, 'push_bulletin', lambda e: writes.append((e.id.hex,e.type.code,e.autoclass['result']['jenis'])))
    task.sync_event(str(event.id))
    event.refresh_from_db()
    assert writes == [(event.id.hex,'MP','VTB')]
    assert event.autoclass['sync']['state'] == 'synced'


def test_bma_failure_does_not_repeat_inference(event, monkeypatch):
    run_prediction(event, monkeypatch)
    event=confirm(event)
    def unavailable(e):
        raise OSError('BMA unavailable')
    monkeypatch.setattr(task, 'push_bulletin', unavailable)
    task.sync_event(str(event.id))
    event.refresh_from_db()
    assert event.autoclass['state'] == 'succeeded'
    assert event.autoclass['attempts'] == 1
    assert event.autoclass['sync']['state'] == 'retrying'


def test_sync_reconciles_manual_change_during_request(event, monkeypatch):
    run_prediction(event, monkeypatch)
    event=confirm(event)
    writes=[]
    def push(e):
        writes.append(e.type.code)
        if len(writes)==1:
            kind=EventType.objects.get(organization=event.catalog.volcano.organization,code='MP')
            current=Event.objects.get(pk=e.pk)
            serializer=EventPayloadSerializer(current,data={'type_id':str(kind.id)},partial=True,
                context={'request':SimpleNamespace(user=event.author)})
            assert serializer.is_valid(),serializer.errors
            serializer.save()
    monkeypatch.setattr(task, 'push_bulletin', push)
    task.sync_event(str(event.id))
    event.refresh_from_db()
    assert writes == ['VTB','MP']
    assert event.autoclass['sync']['state'] == 'synced'


def test_import_and_clean_cannot_duplicate_or_confirm_native_event(event, monkeypatch, settings):
    run_prediction(event, monkeypatch)
    payload={'eventid':event.id.hex,'eventdate':event.time,'eventtype':'MP'}
    serializer=BulletinPayloadSerializer(context={'catalog_id':event.catalog_id,'user':event.author})
    imported=serializer.create(payload)
    assert imported.pk == event.pk
    event.refresh_from_db()
    assert event.evaluation_status == 'preliminary'
    assert event.type.code == 'VTB'
    assert Event.objects.count() == 1
    settings.BMA_URL='http://bma.test'
    settings.BMA_API_KEY='test'
    context=BulletinLoaderContext(organization=event.catalog.volcano.organization,
        volcano=event.catalog.volcano,catalog=event.catalog,user=event.author)
    BulletinLoader(context).clean([],event.time-timedelta(seconds=1),event.time+timedelta(seconds=1))
    assert Event.objects.filter(pk=event.pk).exists()


@pytest.mark.django_db(transaction=True)
def test_concurrent_sync_is_serialized_without_blocking_validation(event, monkeypatch):
    import threading
    from concurrent.futures import ThreadPoolExecutor
    from django.db import close_old_connections
    run_prediction(event, monkeypatch)
    event=confirm(event)
    first, release, second = threading.Event(), threading.Event(), threading.Event()
    writes=[]
    def push(e):
        writes.append(e.type.code)
        if len(writes)==1:
            first.set()
            assert release.wait(5)
        elif len(writes)==2:
            second.set()
            assert release.wait(5)
    monkeypatch.setattr(task, 'push_bulletin', push)
    def sync():
        close_old_connections()
        try:
            task.sync_event(str(event.pk))
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=2) as pool:
        running=pool.submit(sync)
        try:
            assert first.wait(3)
            other=pool.submit(sync)
            other.result(timeout=2)
            kind=EventType.objects.get(organization=event.catalog.volcano.organization,code='MP')
            serializer=EventPayloadSerializer(Event.objects.get(pk=event.pk),data={'type_id':str(kind.id)},
                partial=True,context={'request':SimpleNamespace(user=event.author)})
            assert serializer.is_valid(),serializer.errors
            serializer.save()
        finally:
            release.set()
        running.result(timeout=5)
    assert writes == ['VTB','MP']


def test_real_bma_transport_upserts_then_patches_exact_event(event, monkeypatch, settings):
    import json
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from waveview.appconfig.models import EventObserverConfig
    from waveview.contrib.autoclass.bma import push_bulletin
    run_prediction(event, monkeypatch)
    event=confirm(event)
    writes=[]
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            writes.append((self.path,self.headers['Authorization'],body))
            self.send_response(201)
            self.end_headers()
        do_PATCH=do_POST
        def log_message(self,*args):
            pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    settings.BMA_URL=f'http://127.0.0.1:{server.server_port}'
    settings.BMA_API_KEY='patch-key'
    EventObserverConfig.objects.create(volcano=event.catalog.volcano,name='bma.bulletin',
        data={'server_url':settings.BMA_URL,'token':'crud-token'})
    try:
        push_bulletin(event)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
    assert writes[0][1] == 'Token crud-token'
    assert writes[0][2]['eventid'] == event.id.hex
    assert writes[0][2]['valid'] == 1
    assert writes[1][0] == f'/api/v1/crud/bulletin/{event.id.hex}/autoclass/'
    assert writes[1][1] == 'Api-Key patch-key'
    assert writes[1][2]['autoclass']['jenis'] == 'VTB'
