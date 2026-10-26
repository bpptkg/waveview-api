from datetime import timedelta
from unittest.mock import Mock

import pytest
from django.utils import timezone

from waveview.event.models import Catalog, Event, EventType
from waveview.organization.models import Organization
from waveview.users.models import User
from waveview.volcano.models import Volcano


@pytest.fixture
def event(settings, monkeypatch):
    from waveview.contrib.autoclass import task

    monkeypatch.setattr(task, '_dispatch', Mock())
    user = User.objects.create(username='detector', email='detector@example.test')
    organization = Organization.objects.create(slug='test', name='Test', author=user)
    volcano = Volcano.objects.create(slug='merapi', name='Merapi', organization=organization)
    catalog = Catalog.objects.get(volcano=volcano, is_default=True)
    for code in ('AUTO', 'VTA', 'VTB', 'MP', 'LF', 'TECT', 'GASBURST', 'ROCKFALL', 'AWANPANAS'):
        EventType.objects.create(organization=organization, code=code)
    settings.AUTOCLASS_CATALOG_IDS = [str(catalog.id)]
    settings.AUTOCLASS_URL = 'http://autoclass:8765'
    settings.AUTOCLASS_TOKEN = 'test-token'
    settings.AUTOCLASS_REVISION = 'merapi-v6-test'
    return Event.objects.create(
        catalog=catalog, type=EventType.objects.get(organization=organization, code='AUTO'),
        time=timezone.now() - timedelta(seconds=200), duration=35, method='stelte',
        evaluation_mode='automatic', evaluation_status='preliminary', author=user)


def result_for(event, **changes):
    result = {'status': 'ok', 'eventid': str(event.id),
              'waktu_utc': event.time.strftime('%Y-%m-%d %H:%M:%S'),
              'model': 'model_merapi_v6_m1353', 'versi': '0.3.0',
              'jenis': 'VTB', 'kelas': 'VTB', 'prob_jenis': 0.93,
              'arah': None, 'arah_model': None, 'prob_arah': None, 'arah_sumber': None,
              'top3': [{'kelas': 'VTB', 'p': 0.93}, {'kelas': 'MP', 'p': 0.07}],
              'saran': []}
    result.update(changes)
    return result
