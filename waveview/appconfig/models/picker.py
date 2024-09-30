import json
import uuid
from dataclasses import asdict, dataclass

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


def deepmerge(source: dict, dest: dict) -> dict:
    for key, value in source.items():
        if isinstance(value, dict):
            node = dest.setdefault(key, {})
            deepmerge(value, node)
        else:
            dest[key] = value
    return dest


@dataclass
class ChannelConfigData:
    channel_id: str
    color: str

    @classmethod
    def from_dict(cls, data: dict) -> "ChannelConfigData":
        return cls(
            channel_id=data.get("channel_id"),
            color=data.get("color"),
        )


@dataclass
class MagnitudeConfigData:
    channels: list[str]
    preferred_channel: str
    magnitude_estimator: str
    amplitude_calculator: str

    @classmethod
    def from_dict(cls, data: dict) -> "MagnitudeConfigData":
        return cls(
            channels=data.get("channels", []),
            preferred_channel=data.get("preferred_channel"),
            magnitude_estimator=data.get("magnitude_estimator"),
            amplitude_calculator=data.get("amplitude_calculator"),
        )


@dataclass
class PickerConfigData:
    helicorder_channel: ChannelConfigData
    seismogram_channels: list[ChannelConfigData]
    force_center: bool
    window_size: int
    helicorder_interval: int
    helicorder_duration: int
    magnitude_config: MagnitudeConfigData

    @classmethod
    def from_dict(cls, data: dict) -> "PickerConfigData":
        return cls(
            helicorder_channel=ChannelConfigData.from_dict(
                data.get("helicorder_channel")
            ),
            seismogram_channels=[
                ChannelConfigData.from_dict(channel)
                for channel in data.get("seismogram_channels", [])
            ],
            force_center=data.get("force_center"),
            window_size=data.get("window_size"),
            helicorder_interval=data.get("helicorder_interval"),
            helicorder_duration=data.get("helicorder_duration"),
            magnitude_config=MagnitudeConfigData.from_dict(
                data.get("magnitude_config")
            ),
        )

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def merge(self, data: dict) -> "PickerConfigData":
        source = self.to_dict()
        dest = data
        merged = deepmerge(source, dest)
        return PickerConfigData.from_dict(merged)


class SeismogramComponent(models.TextChoices):
    Z = "Z", _("Vertical")
    N = "N", _("North")
    E = "E", _("East")


class PickerConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organization.Organization",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    volcano = models.ForeignKey(
        "volcano.Volcano",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    data = models.JSONField(null=True, blank=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("picker")
        verbose_name_plural = _("picker")

    def __str__(self) -> str:
        return f"{self.volcano}"

    def merge(self, other: "PickerConfig") -> "PickerConfig":
        data = PickerConfigData.from_dict(self.data).merge(other.data)
        self.data = data.to_dict()
        return self

    def get_raw_data(self) -> dict:
        return self.data

    def get_data(self) -> PickerConfigData:
        return PickerConfigData.from_dict(self.data)
