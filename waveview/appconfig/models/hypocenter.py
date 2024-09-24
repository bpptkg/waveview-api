import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class HypocenterConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    volcano = models.ForeignKey(
        "volcano.Volcano",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    is_preferred = models.BooleanField(default=False)
    event_types = models.ManyToManyField("event.EventType", blank=True)
    data = models.JSONField(null=True, blank=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("hypocenter")
        verbose_name_plural = _("hypocenter")

    def __str__(self) -> str:
        return f"<HypocenterConfig: {self.volcano}>"
