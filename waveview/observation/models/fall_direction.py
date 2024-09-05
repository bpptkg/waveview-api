import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class FallDirection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    volcano = models.ForeignKey(
        "volcano.Volcano",
        on_delete=models.CASCADE,
        related_name="fall_directions",
        related_query_name="fall_direction",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Fall Direction")
        verbose_name_plural = _("Fall Directions")

    def __str__(self) -> str:
        return self.name
