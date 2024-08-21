import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class SeismogramComponent(models.TextChoices):
    Z = "Z", _("Vertical")
    N = "N", _("North")
    E = "E", _("East")


class PickerConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organization.Organization",
        related_name="picker_configs",
        on_delete=models.CASCADE,
    )
    volcano = models.ForeignKey(
        "volcano.Volcano",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    is_preferred = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("picker config")
        verbose_name_plural = _("picker configs")

    def __str__(self) -> str:
        return f"{self.organization.name} {self.name}"


class HelicorderConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    picker_config = models.OneToOneField(
        "PickerConfig",
        related_name="helicorder_config",
        on_delete=models.CASCADE,
    )
    channel = models.ForeignKey(
        "inventory.Channel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    color = models.CharField(max_length=32, null=True, blank=True)
    color_light = models.CharField(max_length=32, null=True, blank=True)
    color_dark = models.CharField(max_length=32, null=True, blank=True)

    class Meta:
        verbose_name = _("helicorder config")
        verbose_name_plural = _("helicorder configs")

    def __str__(self) -> str:
        return f"{self.picker_config.organization.name} Helicorder Config"


class SeismogramConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    picker_config = models.OneToOneField(
        "PickerConfig",
        related_name="seismogram_config",
        on_delete=models.CASCADE,
    )
    component = models.CharField(
        max_length=32,
        choices=SeismogramComponent.choices,
        default=SeismogramComponent.Z,
    )

    class Meta:
        verbose_name = _("seismogram config")
        verbose_name_plural = _("seismogram configs")

    def __str__(self) -> str:
        return f"{self.picker_config.organization.name} Seismogram Config"


class SeismogramStationConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seismogram_config = models.ForeignKey(
        SeismogramConfig,
        related_name="station_configs",
        on_delete=models.CASCADE,
    )
    station = models.ForeignKey(
        "inventory.Station",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    color = models.CharField(max_length=32, null=True, blank=True)
    color_light = models.CharField(max_length=32, null=True, blank=True)
    color_dark = models.CharField(max_length=32, null=True, blank=True)
    order = models.IntegerField(default=0, null=False, blank=False)

    class Meta:
        verbose_name = _("seismogram station config")
        verbose_name_plural = _("seismogram station configs")
        ordering = ("order",)
        unique_together = ("seismogram_config", "station")

    def __str__(self) -> str:
        return f"{self.seismogram_config.picker_config.organization.name} Seismogram Station Config"


class HypocenterConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organization.Organization",
        related_name="hypocenter_configs",
        on_delete=models.CASCADE,
    )
    volcano = models.ForeignKey(
        "volcano.Volcano",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    is_preferred = models.BooleanField(default=False)
    event_types = models.ManyToManyField(
        "event.EventType",
        related_name="hypocenter_configs",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("hypocenter config")
        verbose_name_plural = _("hypocenter configs")

    def __str__(self) -> str:
        return f"{self.organization.name} {self.name}"
