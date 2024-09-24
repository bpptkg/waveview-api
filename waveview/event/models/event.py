import os
import tempfile
import uuid
from io import BytesIO
from typing import TYPE_CHECKING, Optional

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from moviepy.editor import ImageClip, VideoFileClip
from PIL import Image

from waveview.event.header import (
    EvaluationMode,
    EvaluationStatus,
    EventTypeCertainty,
    ObservationType,
)
from waveview.event.models.catalog import Catalog
from waveview.utils.media import MediaPath, MediaType

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
    code = models.CharField(
        max_length=50, db_index=True, help_text=_("Event type code.")
    )
    name = models.CharField(
        max_length=150, null=True, blank=True, help_text=_("Event type name.")
    )
    description = models.TextField(
        null=True, blank=True, default="", help_text=_("Event type description.")
    )
    color = models.CharField(
        max_length=32, null=True, blank=True, help_text=_("Event type default color.")
    )
    color_light = models.CharField(
        max_length=32, null=True, blank=True, help_text=_("Event type light color.")
    )
    color_dark = models.CharField(
        max_length=32, null=True, blank=True, help_text=_("Event type dark color.")
    )
    observation_type = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=ObservationType.choices,
        help_text=_("Type of observation for the event."),
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
        help_text=_("Catalog to which the event belongs."),
    )
    station_of_first_arrival = models.ForeignKey(
        "inventory.Station",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("Station of first arrival."),
    )
    time = models.DateTimeField(
        null=True, blank=True, db_index=True, help_text=_("Event time.")
    )
    duration = models.FloatField(null=True, blank=True, help_text=_("Event duration."))
    type = models.ForeignKey(
        EventType,
        on_delete=models.SET_NULL,
        related_name="events",
        related_query_name="event",
        null=True,
        blank=True,
        help_text=_("Event type."),
    )
    type_certainty = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=EventTypeCertainty.choices,
        help_text=_("Event type certainty."),
    )
    note = models.TextField(
        null=True, blank=True, default="", help_text=_("Additional event information.")
    )
    method = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Method used to determine the event."),
    )
    evaluation_mode = models.CharField(
        max_length=255,
        choices=EvaluationMode.choices,
        null=True,
        blank=True,
        help_text=_("Evaluation mode of the event."),
    )
    evaluation_status = models.CharField(
        max_length=255,
        choices=EvaluationStatus.choices,
        null=True,
        blank=True,
        help_text=_("Evaluation status of the event."),
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
    refid = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Reference ID."),
    )

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")

    def __str__(self) -> str:
        return str(self.time.isoformat())

    def preferred_origin(self) -> Optional["Origin"]:
        return self.origins.filter(is_preferred=True).first()

    def preferred_magnitude(self) -> Optional["Magnitude"]:
        return self.magnitudes.filter(is_preferred=True).first()


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
    thumbnail = models.ImageField(
        upload_to=MediaPath("event-attachments"), null=True, blank=True
    )
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
        self.file.delete(save=False)
        if self.thumbnail:
            self.thumbnail.delete(save=False)
        super().delete(*args, **kwargs)

    def generate_thumbnail(self) -> None:
        if self.media_type == MediaType.PHOTO:
            self.generate_photo_thumbnail()
        elif self.media_type == MediaType.VIDEO:
            self.generate_video_thumbnail()

    def generate_photo_thumbnail(self) -> None:
        with Image.open(self.file) as img:
            img.thumbnail((300, 300))
            thumb_io = BytesIO()
            img.save(thumb_io, img.format)
            self.thumbnail.save(
                f"thumb-{self.file.name}",
                ContentFile(thumb_io.getvalue(), name=f"thumb-{self.file.name}"),
                save=False,
            )
            self.save()

    def generate_video_thumbnail(self) -> None:
        with VideoFileClip(self.file.path) as clip:
            thumbnail_filename = f"{uuid.uuid4()}.jpg"
            thumbnail_path = os.path.join(tempfile.gettempdir(), thumbnail_filename)
            thumbnail_time = clip.duration / 2

            thumbnail = clip.get_frame(thumbnail_time)
            thumbnail_image = ImageClip(thumbnail)
            thumbnail_image.save_frame(thumbnail_path)

            with open(thumbnail_path, "rb") as f:
                self.thumbnail.save(
                    thumbnail_filename,
                    ContentFile(f.read(), name=thumbnail_filename),
                    save=True,
                )
            os.remove(thumbnail_path)
            self.save()
