from dataclasses import dataclass

from django.db import transaction

from waveview.event.models import Event, EventType, Magnitude, Origin
from waveview.seeds.base import BaseDataSeeder
from waveview.seeds.utils import (
    random_choices,
    random_datetime,
    random_duration,
    random_evaluation_mode,
    random_evaluation_status,
    random_methods,
    random_range,
)


@dataclass
class EventDataSeederOptions:
    catalog_id: str
    station_of_first_arrival_id: str
    user_id: str
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    depth_min: float
    depth_max: float
    num_events: int
    hours: int

    @classmethod
    def from_dict(cls, data: dict) -> "EventDataSeederOptions":
        return cls(**data)


class EventDataSeeder(BaseDataSeeder):
    @transaction.atomic
    def run(self, options: EventDataSeederOptions) -> None:
        catalog_id = options.catalog_id
        station_of_first_arrival_id = options.station_of_first_arrival_id
        num_events = options.num_events
        lat_min = options.lat_min
        lat_max = options.lat_max
        lon_min = options.lon_min
        lon_max = options.lon_max
        depth_min = options.depth_min
        depth_max = options.depth_max
        hours = options.hours

        event_types = list(EventType.objects.all())

        for _ in range(num_events):
            event = Event.objects.create(
                catalog_id=catalog_id,
                station_of_first_arrival_id=station_of_first_arrival_id,
                time=random_datetime(hours),
                duration=random_duration(),
                type=random_choices(event_types),
                note="",
                author_id=options.user_id,
                method=random_methods(),
                evaluation_mode=random_evaluation_mode(),
                evaluation_status=random_evaluation_status(),
            )
            Origin.objects.create(
                event=event,
                latitude=random_range(lat_min, lat_max),
                longitude=random_range(lon_min, lon_max),
                depth=random_range(depth_min, depth_max),
                method=random_methods(),
                evaluation_mode=random_evaluation_mode(),
                evaluation_status=random_evaluation_status(),
                author_id=options.user_id,
            )
            Magnitude.objects.create(
                event=event,
                magnitude=random_range(0, 5),
                type="ML",
                method=random_methods(),
                station_count=1,
                azimuthal_gap=0,
                evaluation_status=random_evaluation_status(),
                author_id=options.user_id,
            )
