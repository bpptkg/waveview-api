import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField

from waveview.utils.media import MediaPath, MediaType
from waveview.volcano.geo.adapter import DEMDataReader
from waveview.volcano.geo.types import XYZGrid


class Volcano(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organization.Organization",
        on_delete=models.CASCADE,
        related_name="volcanoes",
        related_query_name="volcano",
    )
    slug = models.SlugField(max_length=200)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True, default="")
    elevation = models.FloatField(null=True, blank=True)
    location = models.TextField(null=True, blank=True, default="")
    country = CountryField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    type = models.CharField(max_length=100, null=True, blank=True)
    last_eruption_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)
    vei = models.IntegerField(null=True, blank=True)
    nearby_population = models.IntegerField(null=True, blank=True)
    hazard_level = models.CharField(max_length=50, null=True, blank=True)
    monitoring_status = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    is_default = models.BooleanField(default=False)

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


class DigitalElevationModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    volcano = models.ForeignKey(
        Volcano,
        on_delete=models.CASCADE,
        related_name="digital_elevation_models",
        related_query_name="digital_elevation_model",
    )
    file = models.FileField(upload_to=MediaPath("digital-elevation-models"))
    type = models.CharField(max_length=50, null=True, blank=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    size = models.PositiveBigIntegerField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    utm_zone = models.CharField(max_length=10, null=True, blank=True)
    x_min = models.FloatField(null=True, blank=True)
    x_max = models.FloatField(null=True, blank=True)
    y_min = models.FloatField(null=True, blank=True)
    y_max = models.FloatField(null=True, blank=True)
    z_min = models.FloatField(null=True, blank=True)
    z_max = models.FloatField(null=True, blank=True)
    resolution = models.FloatField(null=True, blank=True)
    crs = models.CharField(max_length=50, null=True, blank=True)
    data_source = models.CharField(max_length=200, null=True, blank=True)
    acquisition_date = models.DateField(null=True, blank=True)
    processing_method = models.TextField(null=True, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("digital elevation model")
        verbose_name_plural = _("digital elevation models")

    def __str__(self) -> str:
        if not self.name:
            return self.file.name
        return self.name

    @property
    def zone_number(self) -> int:
        return int(self.utm_zone[:-1])

    @property
    def zone_letter(self) -> str:
        return self.utm_zone[-1]

    @property
    def is_northern(self) -> bool:
        return self.zone_letter >= "N"

    @property
    def grid(self) -> XYZGrid:
        reader = DEMDataReader(self.type)
        return reader.read(self.file.path)
