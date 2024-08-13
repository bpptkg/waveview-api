import uuid
from typing import TYPE_CHECKING, Optional

from django.conf import settings
from django.db import models
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from waveview.event.header import EventTypeCertainty
from waveview.event.models.catalog import Catalog
from waveview.utils.media import MediaPath, MediaType
from waveview.event.header import EvaluationMode, EvaluationStatus

if TYPE_CHECKING:
    from waveview.event.models.magnitude import Amplitude, Magnitude
    from waveview.event.models.origin import Origin


class EventType(models.Model):
    """
    This class represents the type of an event. For volcanic events, this could
    be an eruption, explosion, volcano-tectonic earthquake, rockfall, etc.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organization.Organization",
        on_delete=models.CASCADE,
        related_name="event_types",
        related_query_name="event_type",
    )
    code = models.CharField(max_length=50, db_index=True)
    name = models.CharField(max_length=150, null=True, blank=True)
    description = models.TextField(null=True, blank=True, default="")
    color = models.CharField(max_length=32, null=True, blank=True)
    color_light = models.CharField(max_length=32, null=True, blank=True)
    color_dark = models.CharField(max_length=32, null=True, blank=True)
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
        verbose_name = _("Event type")
        verbose_name_plural = _("Event types")
        unique_together = ("organization", "code")

    def __str__(self) -> str:
        return self.code


class Event(models.Model):
    """
    The class Event describes a seismic event.
    """

    origins: QuerySet["Origin"]
    magnitudes: QuerySet["Magnitude"]
    amplitudes: QuerySet["Amplitude"]
    attachments: QuerySet["Attachment"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    catalog = models.ForeignKey(
        Catalog,
        on_delete=models.CASCADE,
        related_name="events",
        related_query_name="event",
    )
    station_of_first_arrival = models.ForeignKey(
        "inventory.Station",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    time = models.DateTimeField(null=True, blank=True, db_index=True)
    duration = models.FloatField(null=True, blank=True)
    type = models.ForeignKey(
        EventType,
        on_delete=models.SET_NULL,
        related_name="events",
        related_query_name="event",
        null=True,
        blank=True,
    )
    type_certainty = models.CharField(
        max_length=255, null=True, blank=True, choices=EventTypeCertainty.choices
    )
    note = models.TextField(null=True, blank=True, default="")
    method = models.CharField(max_length=255, null=True, blank=True)
    evaluation_mode = models.CharField(
        max_length=255,
        choices=EvaluationMode.choices,
        null=True,
        blank=True,
    )
    evaluation_status = models.CharField(
        max_length=255,
        choices=EvaluationStatus.choices,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="events",
        related_query_name="event",
        null=True,
        blank=True,
    )
    bookmarked_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="bookmarked_events",
        related_query_name="bookmarked_event",
        blank=True,
    )

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")

    def __str__(self) -> str:
        return f"Event: {self.id}"

    def preferred_origin(self) -> Optional["Origin"]:
        return self.origins.filter(is_preferred=True).first()

    def preferred_magnitude(self) -> Optional["Magnitude"]:
        return self.magnitudes.filter(is_preferred=True).first()

    def preferred_amplitude(self) -> Optional["Amplitude"]:
        return self.amplitudes.filter(is_preferred=True).first()


class Attachment(models.Model):
    """
    This class represents an attachment. An attachment is a file that is
    associated with an event.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        Event,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="attachments",
        related_query_name="attachment",
    )
    media_type = models.CharField(max_length=255, choices=MediaType.choices)
    file = models.FileField(upload_to=MediaPath("event-attachments"))
    name = models.CharField(max_length=255)
    size = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Attachment")
        verbose_name_plural = _("Attachments")

    def __str__(self) -> str:
        return self.name

    def delete(self, *args, **kwargs) -> None:
        self.file.delete()
        super().delete(*args, **kwargs)
