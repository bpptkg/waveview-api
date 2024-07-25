import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class StreamSource(models.TextChoices):
    SEEDLINK = "seedlink", "Seedlink"
    SCREAM = "scream", "Scream"
    ARCLINK = "arclink", "Arclink"
    FDSNWS = "fdsnws", "FDSN Web Service"
    EARTHWORM = "earthworm", "Earthworm"
    WINSTON = "winston", "Winston Wave Server"
    FILE = "file", "File"


class DataSource(models.Model):
    """Data stream model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inventory = models.ForeignKey(
        "inventory.Inventory",
        on_delete=models.CASCADE,
        related_name="data_sources",
        related_query_name="data_source",
    )
    source = models.CharField(max_length=50, choices=StreamSource.choices)
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Data Source")
        verbose_name_plural = _("Data Sources")
        unique_together = ("inventory", "source")

    def __str__(self) -> str:
        return self.source
