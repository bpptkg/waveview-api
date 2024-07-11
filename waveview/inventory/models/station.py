import uuid
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from waveview.inventory.header import RestrictedStatus

if TYPE_CHECKING:
    from waveview.inventory.models.channel import Channel


class Station(models.Model):
    """
    This class describes a seismic station.
    """

    channels: QuerySet["Channel"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    network = models.ForeignKey(
        "inventory.Network",
        on_delete=models.CASCADE,
        related_name="stations",
        related_query_name="station",
    )
    code = models.CharField(max_length=64, help_text=_("Station code."))
    alternate_code = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text=_("Alternate code used for display or association."),
    )
    start_date = models.DateTimeField(
        null=True, blank=True, help_text=_("Start date of station.")
    )
    end_date = models.DateTimeField(
        null=True, blank=True, help_text=_("End date of station.")
    )
    historical_code = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text=_("Historical code of station."),
    )
    latitude = models.FloatField(
        null=True, blank=True, help_text=_("Station latitude, in degrees.")
    )
    longitude = models.FloatField(
        null=True, blank=True, help_text=_("Station longitude, in degrees.")
    )
    elevation = models.FloatField(
        null=True, blank=True, help_text=_("Station elevation, in meters.")
    )
    restricted_status = models.CharField(
        max_length=32,
        choices=RestrictedStatus.choices,
        default=RestrictedStatus.OPEN,
        help_text=_("Restricted status of station."),
    )
    description = models.TextField(
        null=True, blank=True, default="", help_text=_("Station description.")
    )
    place = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Place where the station is located."),
    )
    country = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Country where the station is located."),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        verbose_name = _("station")
        verbose_name_plural = _("stations")

    def __str__(self) -> str:
        return self.code

    @property
    def channel_count(self) -> int:
        return self.channels.count()
