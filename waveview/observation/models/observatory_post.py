import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class ObservatoryPost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    volcano = models.ForeignKey(
        "volcano.Volcano",
        on_delete=models.CASCADE,
        related_name="observatory_posts",
        related_query_name="observatory_post",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True
    )
    elevation = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Observatory Post")
        verbose_name_plural = _("Observatory Posts")

    def __str__(self) -> str:
        return self.name
