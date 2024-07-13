import logging
import typing

from django.conf import settings
from django.core import mail
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger("waveview.mail")


def get_mail_backend() -> str:
    return settings.EMAIL_BACKEND


def send_messages(
    messages: typing.Sequence[EmailMultiAlternatives], fail_silently: bool = False
) -> int:
    connection = get_connection(fail_silently=fail_silently)
    sent: int = connection.send_messages(messages)
    for message in messages:
        extra = {
            "message_id": message.extra_headers["Message-Id"],
            "size": len(message.message().as_bytes()),
        }
        logger.info("mail.sent", extra=extra)
    return sent


def get_connection(fail_silently: bool = False) -> typing.Any:
    """Gets an SMTP connection."""
    return mail.get_connection(
        backend=get_mail_backend(),
        host=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        username=settings.EMAIL_HOST_USER,
        password=settings.EMAIL_HOST_PASSWORD,
        use_tls=settings.EMAIL_USE_TLS,
        use_ssl=settings.EMAIL_USE_SSL,
        timeout=settings.EMAIL_TIMEOUT,
        fail_silently=fail_silently,
    )


def send_mail(
    subject: str,
    message: str,
    from_email: str,
    recipient_list: typing.Sequence[str],
    fail_silently: bool = False,
    **kwargs: typing.Any,
) -> int:
    """
    Uses EmailMessage class which has more options than the simple send_mail.
    """
    sent: int = mail.EmailMessage(
        subject,
        message,
        from_email,
        recipient_list,
        connection=get_connection(fail_silently=fail_silently),
        **kwargs,
    ).send(fail_silently=fail_silently)
    return sent
