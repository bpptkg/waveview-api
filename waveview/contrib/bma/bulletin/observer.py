import logging
from uuid import UUID

from waveview.contrib.bma.bulletin.client import BulletinClient
from waveview.contrib.bma.bulletin.payload import BulletinPayloadBuilder
from waveview.contrib.bma.bulletin.types import BulletinData
from waveview.event.models import Event
from waveview.event.observers import EventObserver
from waveview.utils.retry import retry

logger = logging.getLogger(__name__)


class BulletinObserver(EventObserver):
    """
    This observer is responsible for creating, updating and deleting bulletins
    in the BMA system.

    When the observer receives an event, it should wait for certain amount of
    time before performing the operation to wait for the data, e.g magnitude,
    amplitude, and location to be available in the database.
    """

    name = "bma.bulletin"

    @retry(initial_delay=5)
    def create(self, event_id: str, data: dict) -> None:
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            logger.error(f"Event {event_id} not found")
            return

        payload = BulletinPayloadBuilder(event).build()
        logger.info(f"Creating bulletin for event {event_id} with payload: {payload}")

        conf = BulletinData.from_dict(data)
        client = BulletinClient(conf.server_url, conf.token)
        client.create(payload)

        logger.info(f"Bulletin created for event {event_id}")

    @retry(initial_delay=5)
    def update(self, event_id: str, data: dict, **options) -> None:
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            logger.error(f"Event {event_id} not found")
            return

        payload = BulletinPayloadBuilder(event).build()
        logger.info(f"Updating bulletin for event {event_id} with payload: {payload}")

        conf = BulletinData.from_dict(data)
        client = BulletinClient(conf.server_url, conf.token)
        refid = options.get("refid")
        if refid:
            event_id = str(refid)
        else:
            event_id = UUID(event_id).hex
        client.update(event_id, payload)

        logger.info(f"Bulletin updated for event {event_id}")

    @retry(initial_delay=5)
    def delete(self, event_id: str, data: dict, **options) -> None:
        conf = BulletinData.from_dict(data)
        client = BulletinClient(conf.server_url, conf.token)
        refid = options.get("refid")
        if refid:
            event_id = str(refid)
        else:
            event_id = UUID(event_id).hex
        client.delete(event_id)

        logger.info(f"Bulletin deleted for event {event_id}")
