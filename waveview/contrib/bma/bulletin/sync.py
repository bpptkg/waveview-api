import logging
from dataclasses import dataclass
from datetime import datetime

from waveview.contrib.bma.bulletin.client import BulletinClient
from waveview.contrib.bma.bulletin.payload import BulletinPayloadBuilder
from waveview.event.models import Catalog, Event
from waveview.organization.models import Organization
from waveview.volcano.models import Volcano

logger = logging.getLogger(__name__)


@dataclass
class BulletinSynchronizerContext:
    client: BulletinClient
    organization: Organization
    volcano: Volcano
    catalog: Catalog


class BulletinSynchronizer:
    def __init__(self, context: BulletinSynchronizerContext) -> None:
        self.context = context
        self.client = context.client

    def update(self, event: Event, dry_run: bool = False) -> None:
        payload = BulletinPayloadBuilder(event).build()
        event_id = event.id.hex
        logger.info(f"Uploading bulletin for event {event.id} with payload: {payload}")
        if not dry_run:
            self.client.update(event_id, payload)
            logger.info(f"Bulletin uploaded for event {event.id}")
        else:
            logger.info(f"Would upload bulletin for event {event.id}")

    def delete(self, event: Event, dry_run: bool = False) -> None:
        event_id = event.id.hex
        logger.info(f"Deleting bulletin for event {event.id}")
        if not dry_run:
            self.client.delete(event_id)
            logger.info(f"Bulletin deleted for event {event.id}")
        else:
            logger.info(f"Would delete bulletin for event {event.id}")

    def sync_by_id(self, event_id: str, dry_run: bool = False) -> None:
        catalog = self.context.catalog
        event = Event.objects.get(catalog=catalog, id=event_id)
        self.update(event, dry_run=dry_run)

    def sync_in_range(
        self,
        start: datetime,
        end: datetime,
        dry_run: bool = False,
        info_only: bool = False,
    ) -> None:
        catalog = self.context.catalog
        events = Event.objects.filter(
            catalog=catalog, time__gte=start, time__lt=end
        ).all()

        logger.info(f"Found {len(events)} events to sync")
        if not info_only:
            for event in events:
                self.update(event, dry_run=dry_run)

        remotes = self.client.list(start, end)
        remote_ids = {remote["eventid"] for remote in remotes}
        local_ids = {event.id.hex for event in events}
        diff = remote_ids - local_ids
        logger.info(f"Found {len(diff)} remote events to delete")

        if not info_only:
            for event_id in diff:
                if not dry_run:
                    self.client.delete(event_id)
                    logger.info(f"Deleted remote event {event_id}")
                else:
                    logger.info(f"Would delete remote event {event_id}")
