import uuid
from dataclasses import dataclass

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


@dataclass
class SeedLinkData:
    server_url: str


@dataclass
class ScreamData:
    server_url: str


@dataclass
class ArclinkData:
    server_url: str


@dataclass
class FdsnwsData:
    server_url: str


class DataSourceType(models.TextChoices):
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
    source = models.CharField(max_length=50, choices=DataSourceType.choices)
    name = models.CharField(max_length=100, null=True, blank=True)
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="+",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Data Source")
        verbose_name_plural = _("Data Sources")

    def __str__(self) -> str:
        return self.source
