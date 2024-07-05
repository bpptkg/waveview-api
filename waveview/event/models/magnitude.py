import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from waveview.event.header import AmplitudeCategory, EvaluationMode, EvaluationStatus
from waveview.event.models.event import Event


class Magnitude(models.Model):
    """
    Describes a magnitude which can, but does not need to be associated with an
    origin or it represents the reported magnitude for the given event.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="magnitudes",
        related_query_name="magnitude",
    )
    magnitude = models.FloatField(
        help_text=_(
            """
            Resulting magnitude value from combining values of type
            StationMagnitude. If no estimations are available, this value can
            represent the reported magnitude.
            """
        )
    )
    type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text=_("Describes the type of magnitude."),
    )
    method = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Identifies the method of magnitude estimation."),
    )
    station_count = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Number of used stations for this magnitude computation."),
    )
    azimuthal_gap = models.FloatField(
        null=True,
        blank=True,
        help_text=_("Azimuthal gap for this magnitude computation in degrees."),
    )
    evaluation_status = models.CharField(
        max_length=255, null=True, blank=True, choices=EvaluationStatus.choices
    )
    is_preferred = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="+",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("magnitude")
        verbose_name_plural = _("magnitudes")

    def __str__(self) -> str:
        return f"{self.type}: {self.magnitude}"


class Amplitude(models.Model):
    """
    This class represents a quantification of the waveform anomaly, usually a
    single amplitude measurement or a measurement of the visible signal duration
    for duration magnitudes.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="amplitudes",
        related_query_name="amplitude",
    )
    amplitude = models.FloatField(help_text=_("Measured amplitude value."))
    type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text=_("String that describes the type of amplitude."),
    )
    category = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        choices=AmplitudeCategory.choices,
        help_text=_("Category of the amplitude."),
    )
    time = models.DateTimeField(
        null=True, blank=True, help_text=_("Reference point in time or central point.")
    )
    begin = models.FloatField(
        null=True,
        blank=True,
        help_text=_("Duration of time interval before reference point in time window."),
    )
    end = models.FloatField(
        null=True,
        blank=True,
        help_text=_("Duration of time interval after reference point in time window."),
    )
    snr = models.FloatField(
        null=True,
        blank=True,
        help_text=_(
            "Signal-to-noise ratio of the spectrogram "
            "at the location the amplitude was measured."
        ),
    )
    unit = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Unit of the amplitude value."),
    )
    waveform = models.ForeignKey(
        "inventory.Channel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text=_(
            "Identifies the waveform stream on which the amplitude was measured."
        ),
    )
    method = models.CharField(max_length=255, null=True, blank=True)
    evaluation_mode = models.CharField(
        max_length=255, null=True, blank=True, choices=EvaluationMode.choices
    )
    is_preferred = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="+",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("amplitude")
        verbose_name_plural = _("amplitudes")

    def __str__(self) -> str:
        return f"{self.type}: {self.amplitude} {self.unit}"

    @property
    def duration(self) -> float:
        if self.begin is None or self.end is None:
            return 0
        return self.begin + self.end


class StationMagnitude(models.Model):
    """
    This class describes the magnitude derived from a single waveform stream.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    amplitude = models.OneToOneField(
        Amplitude,
        on_delete=models.CASCADE,
        related_name="station_magnitude",
        related_query_name="station_magnitude",
        help_text=_("Reference to the amplitude object."),
    )
    magnitude = models.FloatField(help_text=_("Estimated magnitude."))
    type = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Describes the type of magnitude."),
    )
    method = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Identifies the method of magnitude estimation."),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="+",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("station magnitude")
        verbose_name_plural = _("station magnitudes")

    def __str__(self) -> str:
        return f"{self.type}: {self.magnitude}"


class StationMagnitudeContribution(models.Model):
    """
    This class describes the weighting of magnitude values from several
    StationMagnitude objects for computing a network magnitude estimation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    magnitude = models.ForeignKey(
        Magnitude,
        on_delete=models.CASCADE,
        related_name="station_magnitude_contributions",
        related_query_name="station_magnitude_contribution",
        help_text=_("Magnitude value of the contribution to the station magnitude."),
    )
    station_magnitude = models.OneToOneField(
        StationMagnitude,
        on_delete=models.CASCADE,
        help_text=_("Reference to the station magnitude object."),
    )
    residual = models.FloatField(
        null=True,
        blank=True,
        help_text=_("Residual of the contribution to the station magnitude."),
    )
    weight = models.FloatField(
        null=True,
        blank=True,
        help_text=_("Weight of the contribution to the station magnitude."),
    )

    class Meta:
        verbose_name = _("station magnitude contribution")
        verbose_name_plural = _("station magnitude contributions")

    def __str__(self) -> str:
        return f"StationMagnitudeContribution: {self.id}"
