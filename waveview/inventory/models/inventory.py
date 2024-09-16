import uuid
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from waveview.utils.media import MediaPath

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
        return str(self.organization.name)

    def __repr__(self) -> str:
        return f"<Inventory: {self.organization.name}>"

    @property
    def network_count(self) -> int:
        return self.networks.count()

    def get_seedlink_container_name(self) -> str:
        return f"wv_seedlink_{self.id.hex}"


class InventoryFile(models.Model):
    """
    This class describes an inventory file.
    """

    inventory = models.ForeignKey(
        "inventory.Inventory",
        on_delete=models.CASCADE,
        related_name="files",
        related_query_name="file",
    )
    type = models.CharField(max_length=50, null=True, blank=True)
    file = models.FileField(upload_to=MediaPath("inventories/"))
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
        verbose_name = _("inventory file")
        verbose_name_plural = _("inventory files")

    def __str__(self) -> str:
        return self.file.name

    def __repr__(self) -> str:
        return f"<InventoryFile: {self.file.name}>"
