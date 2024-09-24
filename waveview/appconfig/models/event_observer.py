import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class EventObserverConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    volcano = models.ForeignKey(
        "volcano.Volcano",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    name = models.CharField(
        max_length=255,
        help_text=_("Name of the registered event observer adapter class."),
    )
    data = models.JSONField(
        null=True,
        blank=True,
        default=dict,
        help_text=_("Configuration data for the event observer."),
    )
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("event observer")
        verbose_name_plural = _("event observer")

    def __str__(self) -> str:
        return self.name
