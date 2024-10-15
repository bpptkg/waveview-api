import json
import uuid
from dataclasses import asdict, dataclass
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


def deepmerge(source: dict, dest: dict) -> dict:
    for key, value in source.items():
        if isinstance(value, dict):
            node = dest.setdefault(key, {})
            deepmerge(value, node)
        elif isinstance(value, list):
            if value:
                dest[key] = value
        else:
            dest[key] = value
    return dest


@dataclass
class ChannelConfigData:
    channel_id: str
    color: str | None

    @classmethod
    def from_dict(cls, data: dict) -> "ChannelConfigData":
        return cls(
            channel_id=data.get("channel_id"),
            color=data.get("color"),
        )


@dataclass
class AmplitudeConfigData:
    amplitude_calculator: str
    channels: list[ChannelConfigData]

    @classmethod
    def from_dict(cls, data: dict | None) -> "AmplitudeConfigData":
        if data is None:
            return cls(amplitude_calculator="bpptkg", channels=[])
        return cls(
            amplitude_calculator=data.get("amplitude_calculator", "bpptkg"),
            channels=[
                ChannelConfigData.from_dict(channel)
                for channel in data.get("channels", [])
            ],
        )


@dataclass
class BandpassFilterConfigData:
    type: str
    freqmin: float
    freqmax: float
    order: int
    zerophase: bool
    taper: str
    taper_width: float
    id: str

    @classmethod
    def from_dict(cls, data: dict) -> "BandpassFilterConfigData":
        freqmin = data.get("freqmin")
        freqmax = data.get("freqmax")
        order = data.get("order", 4)
        zerophase = data.get("zerophase", False)
        taper = data.get("taper", "hann")
        taper_width = data.get("taper_width", 0.01)
        if freqmin is None:
            raise ValueError("freqmin is required")
        if freqmax is None:
            raise ValueError("freqmax is required")

        return cls(
            type="bandpass",
            freqmin=freqmin,
            freqmax=freqmax,
            order=order,
            zerophase=zerophase,
            taper=taper,
            taper_width=taper_width,
            id=str(uuid4()),
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LowpassFilterConfigData:
    type: str
    freq: float
    order: int
    zerophase: bool
    taper: str
    taper_width: float
    id: str

    @classmethod
    def from_dict(cls, data: dict) -> "LowpassFilterConfigData":
        freq = data.get("freq")
        if freq is None:
            raise ValueError("freq is required")
        order = data.get("order", 4)
        zerophase = data.get("zerophase", False)
        taper = data.get("taper", "hann")
        taper_width = data.get("taper_width", 0.01)
        return cls(
            type="lowpass",
            freq=freq,
            order=order,
            zerophase=zerophase,
            taper=taper,
            taper_width=taper_width,
            id=str(uuid4()),
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class HighpassFilterConfigData:
    type: str
    freq: float
    order: int
    zerophase: bool
    taper: str
    taper_width: float
    id: str

    @classmethod
    def from_dict(cls, data: dict) -> "HighpassFilterConfigData":
        freq = data.get("freq")
        if freq is None:
            raise ValueError("freq is required")
        order = data.get("order", 4)
        zerophase = data.get("zerophase", False)
        taper = data.get("taper", "hann")
        taper_width = data.get("taper_width", 0.01)
        return cls(
            type="highpass",
            freq=freq,
            order=order,
            zerophase=zerophase,
            taper=taper,
            taper_width=taper_width,
            id=str(uuid4()),
        )

    def to_dict(self) -> dict:
        return asdict(self)


FiltersConfigData = list[
    HighpassFilterConfigData | LowpassFilterConfigData | HighpassFilterConfigData
]


@dataclass
class PickerConfigData:
    helicorder_channel: ChannelConfigData
    seismogram_channels: list[ChannelConfigData]
    force_center: bool
    window_size: int
    helicorder_interval: int
    helicorder_duration: int
    amplitude_config: AmplitudeConfigData
    seismogram_filters: FiltersConfigData

    @classmethod
    def from_dict(cls, data: dict) -> "PickerConfigData":
        helicorder_channel = data.get("helicorder_channel")
        if helicorder_channel is None:
            raise ValueError("helicorder_channel is required")

        seismogram_channels = [
            ChannelConfigData.from_dict(channel)
            for channel in data.get("seismogram_channels", [])
        ]

        force_center = data.get("force_center", True)
        window_size = data.get("window_size", 5)
        helicorder_interval = data.get("helicorder_interval", 30)
        helicorder_duration = data.get("helicorder_duration", 12)
        amplitude_config = AmplitudeConfigData.from_dict(data.get("amplitude_config"))

        raw_filters = data.get("seismogram_filters", [])
        seismogram_filters: FiltersConfigData = []
        for item in raw_filters:
            if item.get("type") == "highpass":
                fi = HighpassFilterConfigData.from_dict(item)
            elif item.get("type") == "lowpass":
                fi = LowpassFilterConfigData.from_dict(item)
            elif item.get("type") == "bandpass":
                fi = BandpassFilterConfigData.from_dict(item)
            else:
                raise ValueError("Invalid filter type")
            seismogram_filters.append(fi)

        return cls(
            helicorder_channel=helicorder_channel,
            seismogram_channels=seismogram_channels,
            force_center=force_center,
            window_size=window_size,
            helicorder_interval=helicorder_interval,
            helicorder_duration=helicorder_duration,
            amplitude_config=amplitude_config,
            seismogram_filters=seismogram_filters,
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
