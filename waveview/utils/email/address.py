from django.conf import settings
from django.core.mail.utils import DNS_NAME


def get_from_email_domain() -> str:
    return DNS_NAME


def get_default_from_email() -> str:
    return settings.EMAIL_FROM_ADDRESS or f"noreply@{get_from_email_domain()}"
