import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from waveview.inventory.header import RestrictedStatus


class Channel(models.Model):
    """
    This class describes a seismic channel.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    station = models.ForeignKey(
        "inventory.Station",
        on_delete=models.CASCADE,
        related_name="channels",
        related_query_name="channel",
    )
    code = models.CharField(max_length=64, help_text=_("Channel code."))
    alternate_code = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text=_("Alternate code used for display or association."),
    )
    start_date = models.DateTimeField(
        null=True, blank=True, help_text=_("Start date of channel.")
    )
    end_date = models.DateTimeField(
        null=True, blank=True, help_text=_("End date of channel.")
    )
    historical_code = models.CharField(
        max_length=64, null=True, blank=True, help_text=_("Historical code of channel.")
    )
    location_code = models.CharField(
        max_length=64, help_text=_("Location code of channel.")
    )
    latitude = models.FloatField(
        help_text=_(
            """
            Latitude of this channel’s sensor, in degrees. Often the same as the
            station latitude, but when different the channel latitude is the true
            location of the sensor.
            """
        )
    )
    longitude = models.FloatField(
        help_text=_(
            """
            Longitude of this channel’s sensor, in degrees. Often the same as the
            station longitude, but when different the channel longitude is the true
            location of the sensor.
            """
        )
    )
    elevation = models.FloatField(help_text=_("Elevation of the sensor, in meters."))
    depth = models.FloatField(
        help_text=_(
            "The depth of the sensor relative to the local ground surface level, in meters."
        )
    )
    restricted_status = models.CharField(
        max_length=32,
        choices=RestrictedStatus.choices,
        default=RestrictedStatus.OPEN,
        help_text=_("Restricted status of channel."),
    )
    description = models.TextField(
        null=True, blank=True, default="", help_text=_("Channel description.")
    )
    azimuth = models.FloatField(
        null=True,
        blank=True,
        help_text=_(
            "Azimuth of the component in degrees clockwise from geographic (true) north."
        ),
    )
    dip = models.FloatField(
        null=True,
        blank=True,
        help_text=_(
            """
            Dip of the component in degrees, positive is down from horizontal.
            For horizontal dip=0, for vertical upwards dip=-90 and for vertical
            downwards dip=+90.
            """
        ),
    )
    water_level = models.FloatField(
        null=True,
        blank=True,
        help_text=_(
            """
            Elevation of the water surface in meters for underwater sites, where
            0 is mean sea level. If you put an OBS on a lake bottom, where the
            lake surface is at elevation=1200 meters, then you should set
            WaterLevel=1200. An OBS in the ocean would have WaterLevel=0.
            """
        ),
    )
    sample_rate = models.FloatField(
        null=True, blank=True, help_text=_("Sample rate in samples per second.")
    )
    sample_rate_ratio_number_samples = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Integer number of samples that span a number of seconds."),
    )
    sample_rate_ratio_number_seconds = models.FloatField(
        null=True,
        blank=True,
        help_text=_("Integer number of seconds that span a number of samples."),
    )
    clock_drift = models.FloatField(
        null=True,
        blank=True,
        help_text=_(
            """
            A tolerance value, measured in seconds per sample, used as a
            threshold for time error detection in data from the channel.
            """
        ),
    )
    calibration_units = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text=_(
            """
            Symbol or name of units, e.g. "m/s", "V", "Pa", "C".
            """
        ),
    )
    calibration_units_description = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_(
            """
            Description of units, e.g. "Velocity in meters per second", "Volts",
            "Pascals", "Degrees Celsius".
            """
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        verbose_name = _("channel")
        verbose_name_plural = _("channels")

    def __str__(self) -> str:
        return f"{self.station.code}.{self.code}"

    def __repr__(self) -> str:
        return f"<Channel: {self.code}>"

    def get_datastream_id(self) -> str:
        pk = self.id.hex
        return f"datastream_{pk}"

    @property
    def stream_id(self) -> str:
        network = self.station.network.code
        station = self.station.code
        location = self.location_code
        if location is None:
            location = ""
        channel = self.code
        sid = f"{network}.{station}.{location}.{channel}"
        return sid

    @property
    def network_station_code(self) -> str:
        network = self.station.network.code
        station = self.station.code
        return f"{network}.{station}"

    @property
    def station_channel_code(self) -> str:
        station = self.station.code
        channel = self.code
        return f"{station}.{channel}"
