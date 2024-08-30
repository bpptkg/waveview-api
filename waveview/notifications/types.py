from dataclasses import asdict, dataclass

from django.db import models


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
