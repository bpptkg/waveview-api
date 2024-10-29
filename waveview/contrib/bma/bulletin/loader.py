import logging
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import unquote

import pytz
import requests
from django.conf import settings

from waveview.contrib.bma.bulletin.serializers import BulletinPayloadSerializer
from waveview.event.models import Catalog, Event
from waveview.organization.models import Organization
from waveview.tasks.notify_event_observer import OperationType, notify_event_observer
from waveview.users.models import User
from waveview.volcano.models import Volcano

logger = logging.getLogger(__name__)


class BulletinImporter:
    def __init__(self, url: str, api_key: str) -> None:
        if not url:
            raise ValueError("BMA URL is required.")
        if not api_key:
            raise ValueError("BMA API key is required.")

        self.url = url
        self.api_key = api_key

    def fetch(self, start: datetime, end: datetime) -> list[dict]:
        """
        Fetch bulletins from the BMA system.
        """
        tz = pytz.timezone("Asia/Jakarta")
        local_start = start.astimezone(tz)
        local_end = end.astimezone(tz)
        response = requests.get(
            f"{self.url}/api/v1/bulletin/",
            headers={"Authorization": f"Api-Key {self.api_key}"},
            params={
                "eventdate__gte": local_start.strftime("%Y-%m-%d %H:%M:%S"),
                "eventdate__lt": local_end.strftime("%Y-%m-%d %H:%M:%S"),
                "nolimit": "true",
            },
        )
        response.raise_for_status()
        return response.json()


@dataclass
class BulletinLoaderContext:
    organization: Organization
    volcano: Volcano
    catalog: Catalog
    user: User


class BulletinLoader:
    def __init__(self, context: BulletinLoaderContext) -> None:
        self.context = context
        self.bma = BulletinImporter(url=settings.BMA_URL, api_key=settings.BMA_API_KEY)

    def load(
        self,
        start: datetime,
        end: datetime,
        clean: bool = False,
        skip_update_amplitudes: bool = True,
        dry_run: bool = False,
    ) -> None:
        """
        Load bulletins from BMA system and save it to the database.

        Args:
            start (datetime): Start time of the bulletin to fetch.
            end (datetime): End time of the bulletin to fetch.
            clean (bool): Clean old events that are not in the fetched bulletins.
            skip_update_amplitudes (bool): Skip update amplitudes of the saved events.
            dry_run (bool): Do not save events to the database.
        """
        logger.info(f"Fetching BMA bulletins ({self.bma.url}) from {start} to {end}...")
        events = self.fetch(start, end)
        logger.info(f"Fetched {len(events)} events.")

        saved_events = self.save(events, dry_run=dry_run)
        if not dry_run:
            if clean:
                self.clean(events, start, end)
            if not skip_update_amplitudes:
                self.update_amplitudes(saved_events)

        logger.info("BMA bulletin loading completed.")

    def fetch(self, start: datetime, end: datetime) -> list[dict]:
        return self.bma.fetch(start, end)

    def save(self, events: list[dict], dry_run: bool = False) -> list[Event]:
        saved_events: list[str] = []
        for event in events:
            event_id = unquote(event["eventid"])
            logger.info(f"Processing event {event_id} ({event['eventtype']})...")
            if not dry_run:
                serializer = BulletinPayloadSerializer(
                    data=event,
                    context={
                        "user": self.context.user,
                        "organization_id": str(self.context.organization.id),
                        "catalog_id": str(self.context.catalog.id),
                        "event_id": event_id,
                    },
                )
                serializer.is_valid(raise_exception=True)
                event: Event = serializer.save()
                saved_events.append(event)
                logger.info(f"Event {event_id} saved.")
            else:
                logger.info(f"Event {event_id} is not saved (dry run).")
        return saved_events

    def clean(self, events: list[dict], start: datetime, end: datetime) -> None:
        refids = [unquote(event["eventid"]) for event in events]
        Event.objects.filter(
            catalog_id=self.context.catalog.id,
            time__gte=start,
            time__lt=end,
        ).exclude(refid__in=refids).delete()

    def update_amplitudes(self, events: list[Event]) -> None:
        for event in events:
            notify_event_observer.delay(
                OperationType.UPDATE,
                str(event.id),
                str(self.context.volcano.id),
                names="bpptkg.magnitude",
            )
