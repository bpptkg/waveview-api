import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField

from waveview.utils.media import MediaPath, MediaType


class Volcano(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organization.Organization",
        on_delete=models.CASCADE,
        related_name="volcanoes",
        related_query_name="volcano",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True, default="")
    elevation = models.IntegerField(null=True, blank=True)
    location = models.TextField(null=True, blank=True, default="")
    country = CountryField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name = _("volcano")
        verbose_name_plural = _("volcanoes")

    def __str__(self) -> str:
        return self.name


class VolcanoMedia(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    volcano = models.ForeignKey(
        Volcano,
        on_delete=models.CASCADE,
        related_name="media",
        related_query_name="media",
    )
    file = models.FileField(upload_to=MediaPath("volcano-media"))
    name = models.CharField(max_length=200, null=True, blank=True)
    size = models.PositiveBigIntegerField()
    media_type = models.CharField(max_length=50, choices=MediaType.choices)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name = _("volcano media")
        verbose_name_plural = _("volcano media")

    def __str__(self) -> str:
        return self.name
