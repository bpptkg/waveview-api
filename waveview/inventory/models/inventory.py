import uuid
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from waveview.inventory.models.network import Network


class Inventory(models.Model):
    """
    This class describes an inventory of seismic networks.
    """

    networks: QuerySet["Network"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.OneToOneField(
        "organization.Organization", on_delete=models.CASCADE, related_name="inventory"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True, default="")
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
        verbose_name = _("inventory")
        verbose_name_plural = _("inventories")

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Inventory: {self.name}>"

    @property
    def network_count(self) -> int:
        return self.networks.count()
