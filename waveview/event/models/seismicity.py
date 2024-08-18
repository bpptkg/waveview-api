import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from waveview.event.models.event import EventType


class SeismicityConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organization.Organization",
        on_delete=models.CASCADE,
    )
    type = models.ForeignKey(
        EventType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    order = models.IntegerField(default=0, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("seismicity config")
        verbose_name_plural = _("seismicity configs")
        unique_together = ("organization", "type")

    def __str__(self) -> str:
        return f"SeismicityConfig: {self.id}"

    def __repr__(self) -> str:
        return f"<SeismicityConfig: {self.id}>"
