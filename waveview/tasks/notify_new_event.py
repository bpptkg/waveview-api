import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from waveview.celery import app
from waveview.event.models import Event
from waveview.notifications.serializers import NewEventNotificationDataSerializer
from waveview.notifications.types import NotificationMessage, NotificationType
from waveview.notifications.utils import user_channel
from waveview.organization.models import Organization

logger = logging.getLogger(__name__)


@app.task(
    name="waveview.tasks.notify_new_event",
    default_retry_delay=60 * 5,
    max_retries=None,
)
def notify_new_event(organization_id: str, event_id: str) -> None:
    try:
        organization = Organization.objects.get(pk=organization_id)
    except Organization.DoesNotExist:
        logger.error(f"Organization not found: {organization_id}")
        return

    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        logger.error(f"Event not found: {event_id}")
        return

    data = NewEventNotificationDataSerializer({"event": event}).data
    excluded = [event.author]
    members = [member for member in organization.members.all()] + [organization.author]
    participants = [member for member in members if member not in excluded]
    if event.author.name:
        author_name = event.author.name
    else:
        author_name = event.author.username
    channel_layer = get_channel_layer()
    for participant in participants:
        channel = user_channel(participant.pk)
        message = NotificationMessage(
            type=NotificationType.NEW_EVENT.value,
            title=f"New Event ({event.type.code})",
            body=f"Occurred at {event.time.strftime('%Y-%m-%d %H:%M:%S')} UTC with duration of {event.duration:.2f}s ({author_name})",
            data=data,
        ).to_dict()
        async_to_sync(channel_layer.group_send)(
            channel,
            {
                "type": "notify",
                "data": message,
            },
        )
