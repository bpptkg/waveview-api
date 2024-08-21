import uuid
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from waveview.event.models.event import Event


class Catalog(models.Model):
    """
    The class Catalog describes a collection of events. A catalog is usually
    associated with a volcano and contains information about the events that
    occurred at the volcano.
    """

    events: QuerySet["Event"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    volcano = models.ForeignKey(
        "volcano.Volcano",
        on_delete=models.CASCADE,
        related_name="catalogs",
        related_query_name="catalog",
    )
    name = models.CharField(max_length=200, help_text=_("Catalog name."))
    description = models.TextField(
        null=True, blank=True, default="", help_text=_("Catalog description.")
    )
    is_default = models.BooleanField(
        default=False, help_text=_("Whether the catalog is the default for volcano.")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="catalogs",
        related_query_name="catalog",
    )

    class Meta:
        verbose_name = _("catalog")
        verbose_name_plural = _("catalogs")

    def __str__(self) -> str:
        return self.name

    @property
    def event_count(self) -> int:
        return self.events.count()
