import logging

from django.core.mail import EmailMultiAlternatives

from waveview.celery import app
from waveview.utils.email import send_messages

logger = logging.getLogger(__name__)


@app.task(
    name="waveview.tasks.send_email",
    default_retry_delay=60 * 5,
    max_retries=None,
)
def send_email(message: EmailMultiAlternatives) -> None:
    if not hasattr(message, "reply_to"):
        message.reply_to = []

    send_messages([message])
