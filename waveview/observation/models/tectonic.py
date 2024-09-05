import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from waveview.observation.choices import MMIScale


class Tectonic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        "event.Event",
        on_delete=models.CASCADE,
        related_name="tectonics",
        related_query_name="tectonic",
    )
    observatory_post = models.ForeignKey(
        "ObservatoryPost", on_delete=models.SET_NULL, null=True, blank=True
    )
    occurred_at = models.DateTimeField(null=True, blank=True)
    mmi_scale = models.CharField(
        max_length=100, choices=MMIScale.choices, null=True, blank=True
    )
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Tectonic")
        verbose_name_plural = _("Tectonics")
