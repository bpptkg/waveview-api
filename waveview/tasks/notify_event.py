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


def notify_new_event(organization: Organization, data: NotifyEventData) -> None:
    author_name = data.author_name
    event_type_code = data.event_type_code
    event_time = data.event_time
    actor_id = data.actor_id

    participants = get_participants(organization, [actor_id])

    try:
        event = Event.objects.get(pk=data.event_id)
        payload = NewEventNotificationDataSerializer({"event": event}).data
    except Event.DoesNotExist:
        logger.error(f"Event not found: {data.event_id}")
        return

    channel_layer = get_channel_layer()
    for participant in participants:
        channel = user_channel(participant.pk)

        message = NotificationMessage(
            type=NotificationType.NEW_EVENT.value,
            title=f"New Event ({event_type_code})",
            body=f"Time {event_time} UTC by {author_name}",
            data=payload,
        ).to_dict()

        async_to_sync(channel_layer.group_send)(
            channel,
            {
                "type": "notify",
                "data": message,
            },
        )


def notify_event_update(organization: Organization, data: NotifyEventData) -> None:
    author_name = data.author_name
    event_type_code = data.event_type_code
    event_time = data.event_time
    actor_id = data.actor_id

    participants = get_participants(organization, [actor_id])

    try:
        event = Event.objects.get(pk=data.event_id)
        payload = EventUpdateNotificationDataSerializer({"event": event}).data
    except Event.DoesNotExist:
        logger.error(f"Event not found: {data.event_id}")
        return

    channel_layer = get_channel_layer()
    for participant in participants:
        channel = user_channel(participant.pk)

        message = NotificationMessage(
            type=NotificationType.EVENT_UPDATE.value,
            title=f"Event Updated ({event_type_code})",
            body=f"Time {event_time} UTC by {author_name}",
            data=payload,
        ).to_dict()

        async_to_sync(channel_layer.group_send)(
            channel,
            {
                "type": "notify",
                "data": message,
            },
        )


def notify_event_delete(organization: Organization, data: NotifyEventData) -> None:
    event_id = data.event_id
    author_id = data.author_id
    author_name = data.author_name
    event_type_code = data.event_type_code
    event_time = data.event_time
    actor_id = data.actor_id

    participants = get_participants(organization, [actor_id])

    try:
        type = EventType.objects.get(code=event_type_code)
    except EventType.DoesNotExist:
        logger.error(f"Event type not found: {event_type_code}")
        return

    try:
        author = User.objects.get(pk=author_id)
    except User.DoesNotExist:
        logger.error(f"Author not found: {author_id}")
        return

    payload = EventDeleteNotificationDataSerializer(
        {
            "event": {
                "id": event_id,
                "time": event_time,
                "type": type,
                "duration": data.event_duration,
                "author": author,
                "deleted_at": timezone.now(),
            }
        }
    ).data

    channel_layer = get_channel_layer()
    for participant in participants:
        channel = user_channel(participant.pk)

        message = NotificationMessage(
            type=NotificationType.EVENT_DELETE.value,
            title=f"Event Deleted ({event_type_code})",
            body=f"Time {event_time} UTC by {author_name}",
            data=payload,
        ).to_dict()

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

    if operation == OperationType.CREATE:
        notify_new_event(organization, data)
    elif operation == OperationType.UPDATE:
        notify_event_update(organization, data)
    elif operation == OperationType.DELETE:
        notify_event_delete(organization, data)
