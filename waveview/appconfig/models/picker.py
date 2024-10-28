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
    label: str | None
    is_analog: bool | None
    slope: float | None
    offset: float | None

    @classmethod
    def from_dict(cls, data: dict) -> "ChannelConfigData":
        return cls(
            channel_id=data.get("channel_id", ""),
            color=data.get("color"),
            label=data.get("label"),
            is_analog=data.get("is_analog"),
            slope=data.get("slope"),
            offset=data.get("offset"),
        )

    def to_dict(self) -> dict:
        return asdict(self)


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

    def to_dict(self) -> dict:
        return {
            "amplitude_calculator": self.amplitude_calculator,
            "channels": [channel.to_dict() for channel in self.channels],
        }


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
            id=data["id"],
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
            id=data["id"],
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
            id=data["id"],
        )

    def to_dict(self) -> dict:
        return asdict(self)


FilterConfigData = (
    BandpassFilterConfigData | HighpassFilterConfigData | LowpassFilterConfigData
)
FiltersConfigData = list[FilterConfigData]


def build_filter_config(cfg: dict) -> FilterConfigData:
    if cfg.get("type") == "highpass":
        return HighpassFilterConfigData.from_dict(cfg)
    elif cfg.get("type") == "lowpass":
        return LowpassFilterConfigData.from_dict(cfg)
    elif cfg.get("type") == "bandpass":
        return BandpassFilterConfigData.from_dict(cfg)
    else:
        raise ValueError("Invalid filter type")


@dataclass
class UserPickerConfigData:
    helicorder_channel: ChannelConfigData
    seismogram_channels: list[ChannelConfigData]
    window_size: int
    force_center: bool
    helicorder_filter: FilterConfigData

    @classmethod
    def from_dict(cls, data: dict) -> "UserPickerConfigData":
        helicorder_channel = data.get("helicorder_channel")
        if helicorder_channel is None:
            raise ValueError("helicorder_channel is required")
        helicorder_channel = ChannelConfigData.from_dict(helicorder_channel)

        seismogram_channels = [
            ChannelConfigData.from_dict(channel)
            for channel in data.get("seismogram_channels", [])
        ]

        window_size = data.get("window_size", 5)
        force_center = data.get("force_center", True)

        helicorder_filter = data.get("helicorder_filter")
        if helicorder_filter is not None:
            helicorder_filter = build_filter_config(helicorder_filter)

        return cls(
            helicorder_channel=helicorder_channel,
            seismogram_channels=seismogram_channels,
            window_size=window_size,
            force_center=force_center,
            helicorder_filter=helicorder_filter,
        )


@dataclass
class PickerConfigData:
    helicorder_channel: ChannelConfigData
    seismogram_channels: list[ChannelConfigData]
    helicorder_filters: FiltersConfigData
    seismogram_filters: FiltersConfigData
    helicorder_filter: FilterConfigData | None
    force_center: bool
    window_size: int
    helicorder_interval: int
    helicorder_duration: int
    amplitude_config: AmplitudeConfigData

    @classmethod
    def from_dict(cls, data: dict) -> "PickerConfigData":
        helicorder_channel = data.get("helicorder_channel")
        if helicorder_channel is None:
            raise ValueError("helicorder_channel is required")
        helicorder_channel = ChannelConfigData.from_dict(helicorder_channel)

        seismogram_channels = [
            ChannelConfigData.from_dict(channel)
            for channel in data.get("seismogram_channels", [])
        ]

        force_center = data.get("force_center", True)
        window_size = data.get("window_size", 5)
        helicorder_interval = data.get("helicorder_interval", 30)
        helicorder_duration = data.get("helicorder_duration", 12)
        amplitude_config = AmplitudeConfigData.from_dict(data.get("amplitude_config"))

        raw_seismogram_filters = data.get("seismogram_filters", [])
        seismogram_filters: FiltersConfigData = []
        for item in raw_seismogram_filters:
            fi = build_filter_config(item)
            seismogram_filters.append(fi)

        raw_helicorder_filters = data.get("helicorder_filters", [])
        helicorder_filters: FiltersConfigData = []
        for item in raw_helicorder_filters:
            fi = build_filter_config(item)
            helicorder_filters.append(fi)

        helicorder_filter = data.get("helicorder_filter")
        if helicorder_filter is not None:
            helicorder_filter = build_filter_config(helicorder_filter)

        return cls(
            helicorder_channel=helicorder_channel,
            seismogram_channels=seismogram_channels,
            force_center=force_center,
            window_size=window_size,
            helicorder_interval=helicorder_interval,
            helicorder_duration=helicorder_duration,
            amplitude_config=amplitude_config,
            seismogram_filters=seismogram_filters,
            helicorder_filters=helicorder_filters,
            helicorder_filter=helicorder_filter,
        )

    def to_dict(self) -> dict:
        return {
            "helicorder_channel": self.helicorder_channel.to_dict(),
            "seismogram_channels": [
                channel.to_dict() for channel in self.seismogram_channels
            ],
            "force_center": self.force_center,
            "window_size": self.window_size,
            "helicorder_interval": self.helicorder_interval,
            "helicorder_duration": self.helicorder_duration,
            "amplitude_config": self.amplitude_config.to_dict(),
            "seismogram_filters": [
                filter.to_dict() for filter in self.seismogram_filters
            ],
            "helicorder_filters": [
                filter.to_dict() for filter in self.helicorder_filters
            ],
            "helicorder_filter": (
                self.helicorder_filter.to_dict() if self.helicorder_filter else None
            ),
        }

    def merge(self, source: UserPickerConfigData) -> "PickerConfigData":
        self.helicorder_channel = source.helicorder_channel
        self.seismogram_channels = source.seismogram_channels
        self.force_center = source.force_center
        self.window_size = source.window_size
        self.helicorder_filter = source.helicorder_filter
        return self


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


def merge_picker_configs(
    orgconfig: PickerConfig, userconfig: PickerConfig
) -> PickerConfig:
    userdata = UserPickerConfigData.from_dict(userconfig.data)
    orgdata = PickerConfigData.from_dict(orgconfig.data)
    orgdata.merge(userdata)
    orgconfig.data = orgdata.to_dict()
    return orgconfig
