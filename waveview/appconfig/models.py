import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from waveview.event.models.event import EventType


class SeismogramComponent(models.TextChoices):
    Z = "Z", _("Vertical")
    N = "N", _("North")
    E = "E", _("East")


class PickerConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    volcano = models.ForeignKey(
        "volcano.Volcano",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    data = models.JSONField(null=True, blank=True, default=dict)
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
        verbose_name = _("picker")
        verbose_name_plural = _("picker")

    def __str__(self) -> str:
        return f"<PickerConfig: {self.volcano}>"


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
    data = models.JSONField(null=True, blank=True, default=dict)

    class Meta:
        verbose_name = _("helicorder")
        verbose_name_plural = _("helicorder")

    def __str__(self) -> str:
        return f"<HelicorderConfig: {self.picker_config}>"


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
    data = models.JSONField(null=True, blank=True, default=dict)

    class Meta:
        verbose_name = _("seismogram")
        verbose_name_plural = _("seismogram")

    def __str__(self) -> str:
        return f"<SeismogramConfig: {self.picker_config}>"


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
        verbose_name = _("seismogram station")
        verbose_name_plural = _("seismogram station")
        ordering = ("order",)
        unique_together = ("seismogram_config", "station")

    def __str__(self) -> str:
        return f"<SeismogramStationConfig: {self.seismogram_config}>"


class HypocenterConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    volcano = models.ForeignKey(
        "volcano.Volcano",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    is_preferred = models.BooleanField(default=False)
    event_types = models.ManyToManyField("event.EventType", blank=True)
    data = models.JSONField(null=True, blank=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("hypocenter")
        verbose_name_plural = _("hypocenter")

    def __str__(self) -> str:
        return f"<HypocenterConfig: {self.volcano}>"


class SeismicityConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    volcano = models.ForeignKey(
        "volcano.Volcano",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    type = models.ForeignKey(
        EventType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    order = models.IntegerField(
        default=0,
        null=False,
        blank=False,
        help_text=_("Order of the seismicity config in the list."),
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
        verbose_name = _("seismicity")
        verbose_name_plural = _("seismicity")

    def __str__(self) -> str:
        return f"<SeismicityConfig: {self.volcano}>"


class MagnitudeConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    volcano = models.ForeignKey(
        "volcano.Volcano",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    method = models.CharField(max_length=255)
    name = models.CharField(max_length=255, null=True, blank=True)
    data = models.JSONField(null=True, blank=True, default=dict)
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("magnitude")
        verbose_name_plural = _("magnitude")

    def __str__(self) -> str:
        return f"<MagnitudeConfig: {self.volcano}>"


class StationMagnitudeConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    magnitude_config = models.ForeignKey(
        "MagnitudeConfig",
        related_name="station_magnitude_configs",
        on_delete=models.CASCADE,
    )
    channel = models.ForeignKey(
        "inventory.Channel",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    data = models.JSONField(null=True, blank=True, default=dict)
    is_enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("station magnitude")
        verbose_name_plural = _("station magnitude")
        unique_together = ("magnitude_config", "channel")

    def __str__(self) -> str:
        return f"{self.channel.stream_id}"

    def __repr__(self) -> str:
        return f"<StationMagnitudeConfig: {self.channel.stream_id}>"
