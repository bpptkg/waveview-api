import uuid
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from waveview.inventory.header import RestrictedStatus

if TYPE_CHECKING:
    from waveview.inventory.models.station import Station


class Network(models.Model):
    """
    This class describes a network of seismic stations.
    """

    stations: QuerySet["Station"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inventory = models.ForeignKey(
        "inventory.Inventory",
        on_delete=models.CASCADE,
        related_name="networks",
        related_query_name="network",
    )
    code = models.CharField(max_length=64, help_text=_('Network code, e.g. "VG"'))
    alternate_code = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text=_("A code used for display or association."),
    )
    start_date = models.DateTimeField(
        null=True, blank=True, help_text=_("Start date of network.")
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("End date of network."),
    )
    historical_code = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text=_("A previously used code if different from the current code."),
    )
    description = models.TextField(
        null=True, blank=True, default="", help_text=_("Network description.")
    )
    region = models.CharField(
        max_length=255, null=True, blank=True, help_text=_("Region of network.")
    )
    restricted_status = models.CharField(
        max_length=32,
        choices=RestrictedStatus.choices,
        default=RestrictedStatus.OPEN,
        help_text=_("Restricted status of network."),
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
        verbose_name = _("network")
        verbose_name_plural = _("networks")

    def __str__(self) -> str:
        return self.code

    def __repr__(self) -> str:
        return f"<Network: {self.code}>"

    @property
    def station_count(self) -> int:
        return self.stations.count()
