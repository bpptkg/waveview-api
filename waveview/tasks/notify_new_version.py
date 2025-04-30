import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

from waveview.celery import app
from waveview.notifications.types import NotificationMessage, NotificationType
from waveview.notifications.utils import user_channel
from waveview.users.models import User

logger = logging.getLogger(__name__)


@app.task(
    name="waveview.tasks.notify_new_version",
    default_retry_delay=60 * 5,
    max_retries=None,
)
def notify_new_version(
    version: str, reload: bool = True, timeout: int = -1, reload_timeout: int = 10
) -> None:
    title = "New Version Available"
    body = f"A new version of the application is available: {version}."
    channel_layer = get_channel_layer()
    for user in User.objects.all():
        channel = user_channel(user.pk)
        message = NotificationMessage(
            type=NotificationType.NEW_APP_VERSION,
            title=title,
            body=body,
            data={
                "version": version,
                "reload": reload,
                "reload_timeout": reload_timeout,
                "timestamp": timezone.now().isoformat(),
            },
            timeout=timeout,
        ).to_dict()
        async_to_sync(channel_layer.group_send)(
            channel,
            {
                "type": "notify",
                "data": message,
            },
        )
