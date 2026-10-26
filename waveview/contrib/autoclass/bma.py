from urllib.parse import quote

import requests
from django.conf import settings

from waveview.appconfig.models import EventObserverConfig
from waveview.contrib.bma.bulletin.client import BulletinClient
from waveview.contrib.bma.bulletin.payload import BulletinPayloadBuilder


def push_bulletin(event):
    config = EventObserverConfig.objects.filter(volcano_id=event.catalog.volcano_id,
        name='bma.bulletin', is_enabled=True).order_by('order').first()
    if config is None or not settings.BMA_API_KEY:
        raise ValueError('BMA credentials/observer are not configured')
    base = settings.BMA_URL.rstrip('/')
    if config.data.get('server_url', '').rstrip('/') != base:
        raise ValueError('BMA observer and API-key target must use the same server')
    BulletinClient(config.data['server_url'], config.data['token']).create(BulletinPayloadBuilder(event).build())
    if event.autoclass.get('result') is not None:
        identity = quote(event.refid or event.id.hex, safe='')
        response = requests.patch(base + f'/api/v1/crud/bulletin/{identity}/autoclass/',
            headers={'Authorization': f'Api-Key {settings.BMA_API_KEY}'},
            json={'autoclass': dict(event.autoclass['result'], source='veps',
                input_time=event.autoclass['input_time'], revision=event.autoclass['revision'])},
            timeout=(10, 30), allow_redirects=False)
        if not 200 <= response.status_code < 300:
            raise ValueError('BMA autoclass PATCH failed')
