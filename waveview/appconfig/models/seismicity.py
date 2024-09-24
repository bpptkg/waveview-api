import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from waveview.event.models.event import EventType


class SeismicityConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    volcano = models.ForeignKey(
        "volcano.Volcano",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    type = models.ForeignKey(
        EventType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    order = models.IntegerField(
        default=0,
        null=False,
        blank=False,
        help_text=_("Order of the seismicity config in the list."),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("seismicity")
        verbose_name_plural = _("seismicity")

    def __str__(self) -> str:
        return f"{self.volcano}"
