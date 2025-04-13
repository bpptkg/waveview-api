import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

from waveview.celery import app
from waveview.event.models import Event, EventType
from waveview.event.observers import OperationType
from waveview.notifications.serializers import (
    EventDeleteNotificationDataSerializer,
    EventUpdateNotificationDataSerializer,
    NewEventNotificationDataSerializer,
)
from waveview.notifications.types import (
    NotificationMessage,
    NotificationType,
    NotifyEventData,
)
from waveview.notifications.utils import user_channel
from waveview.organization.models import Organization
from waveview.users.models import User

logger = logging.getLogger(__name__)


def get_participants(organization: Organization, excluded: list[str]) -> list:
    members = [member for member in organization.members.all()] + [organization.author]
    return [member for member in members if str(member.pk) not in excluded]


def get_event(event_id: str) -> Event:
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        raise ValueError(f"Event not found: {event_id}")
    return event


def get_actor(actor_id: str) -> User:
    try:
        actor = User.objects.get(pk=actor_id)
    except User.DoesNotExist:
        raise ValueError(f"Actor not found: {actor_id}")
    return actor


def get_event_type(event_type_code: str) -> EventType:
    try:
        event_type = EventType.objects.get(code=event_type_code)
    except EventType.DoesNotExist:
        raise ValueError(f"Event type not found: {event_type_code}")
    return event_type


def get_actor_name(actor: User) -> str:
    if actor.name is not None:
        return actor.name
    return actor.username


def build_message(operation: OperationType, data: NotifyEventData) -> dict:
    actor_id = data.actor_id
    event_id = data.event_id
    event_time = data.event_time
    event_type_code = data.event_type_code
    catalog_name = data.catalog_name

    if operation == OperationType.CREATE:
        event = get_event(event_id)
        actor = get_actor(actor_id)
        actor_name = get_actor_name(actor)
        payload = NewEventNotificationDataSerializer(
            {"event": event, "actor": actor}
        ).data
        message = NotificationMessage(
            type=NotificationType.NEW_EVENT.value,
            title=f"New Event ({event_type_code})",
            body=f"Time {event_time} UTC by {actor_name} in {catalog_name}",
            data=payload,
        ).to_dict()

    elif operation == OperationType.UPDATE:
        event = get_event(event_id)
        actor = get_actor(actor_id)
        actor_name = get_actor_name(actor)
        payload = EventUpdateNotificationDataSerializer(
            {"event": event, "actor": actor}
        ).data
        message = NotificationMessage(
            type=NotificationType.EVENT_UPDATE.value,
            title=f"Event Updated ({event_type_code})",
            body=f"Time {event_time} UTC by {actor_name} in {catalog_name}",
            data=payload,
        ).to_dict()

    elif operation == OperationType.DELETE:
        actor = get_actor(actor_id)
        actor_name = get_actor_name(actor)
        event_type = get_event_type(event_type_code)
        payload = EventDeleteNotificationDataSerializer(
            {
                "event": {
                    "id": event_id,
                    "time": event_time,
                    "type": event_type,
                    "duration": data.event_duration,
                    "deleted_at": timezone.now(),
                    "catalog_name": catalog_name,
                },
                "actor": actor,
            }
        ).data
        message = NotificationMessage(
            type=NotificationType.EVENT_DELETE.value,
            title=f"Event Deleted ({event_type_code})",
            body=f"Time {event_time} UTC by {actor_name} in {catalog_name}",
            data=payload,
        ).to_dict()
    else:
        raise ValueError(f"Invalid operation: {operation}")

    return message


def send_message(participants: list[User], message: NotificationMessage) -> None:
    channel_layer = get_channel_layer()
    for participant in participants:
        channel = user_channel(participant.pk)
        async_to_sync(channel_layer.group_send)(
            channel,
            {
                "type": "notify",
                "data": message,
            },
        )


@app.task(
    name="waveview.tasks.notify_event_update",
    default_retry_delay=60 * 5,
    max_retries=None,
)
def notify_event(operation: OperationType, payload: dict) -> None:
    data = NotifyEventData.from_dict(payload)
    organization_id = data.organization_id
    try:
        organization = Organization.objects.get(pk=organization_id)
    except Organization.DoesNotExist:
        logger.error(f"Organization not found: {organization_id}")
        return

    try:
        actor_id = data.actor_id
        participants = get_participants(organization, [actor_id])
        msg = build_message(operation, data)
        send_message(participants, msg)
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
