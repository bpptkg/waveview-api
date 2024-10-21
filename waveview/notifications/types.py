from dataclasses import asdict, dataclass

from django.db import models

from waveview.event.models import Event


class NotificationType(models.TextChoices):
    NEW_EVENT = "new_event", "New Event"
    EVENT_UPDATE = "event_update", "Event Update"
    EVENT_DELETE = "event_delete", "Event Delete"


@dataclass
class NotificationMessage:
    type: NotificationType
    title: str
    body: str
    data: dict

    def to_dict(self) -> dict:
        return {
            "type": str(self.type),
            "title": self.title,
            "body": self.body,
            "data": dict(self.data),
        }


@dataclass
class NotifyEventData:
    organization_id: str
    event_id: str
    event_time: str
    event_type_code: str
    event_duration: float
    actor_id: str

    @classmethod
    def from_dict(cls, data: dict) -> "NotifyEventData":
        return cls(**data)

    @classmethod
    def from_event(
        cls, actor_id: str, organization_id: str, event: Event
    ) -> "NotifyEventData":
        return cls(
            organization_id=organization_id,
            event_id=str(event.id),
            event_time=event.time.isoformat(),
            event_type_code=event.type.code,
            event_duration=event.duration,
            actor_id=actor_id,
        )

    def to_dict(self) -> dict:
        return asdict(self)
