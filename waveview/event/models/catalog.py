import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Catalog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    volcano = models.ForeignKey(
        "volcano.Volcano",
        on_delete=models.CASCADE,
        related_name="catalogs",
        related_query_name="catalog",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True, default="")
    is_default = models.BooleanField(default=False)
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
