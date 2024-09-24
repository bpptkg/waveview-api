import logging

from waveview.contrib.bma.bulletin.client import BulletinClient
from waveview.contrib.bma.bulletin.payload import BulletinPayloadBuilder
from waveview.contrib.bma.bulletin.types import BulletinData
from waveview.event.models import Event
from waveview.event.observers import EventObserver
from waveview.utils.retry import retry

logger = logging.getLogger(__name__)


class BulletinObserver(EventObserver):
    name = "bma.bulletin"

    @retry()
    def create(self, event_id: str, data: dict) -> None:
        event = Event.objects.get(id=event_id)
        payload = BulletinPayloadBuilder(event).build()
        conf = BulletinData.from_dict(data)
        client = BulletinClient(conf.server_url, conf.token)
        client.create(payload)

    @retry()
    def update(self, event_id: str, data: dict) -> None:
        event = Event.objects.get(id=event_id)
        payload = BulletinPayloadBuilder(event).build()
        conf = BulletinData.from_dict(data)
        client = BulletinClient(conf.server_url, conf.token)
        client.update(event_id, payload)

    @retry()
    def delete(self, event_id: str, data: dict) -> None:
        conf = BulletinData.from_dict(data)
        client = BulletinClient(conf.server_url, conf.token)
        client.delete(event_id)
