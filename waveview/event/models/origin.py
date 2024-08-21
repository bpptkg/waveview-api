import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from waveview.event.header import EvaluationMode, EvaluationStatus
from waveview.event.models.event import Event


class Origin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="origins",
        related_query_name="origin",
    )
    time = models.DateTimeField(
        db_index=True, null=True, blank=True, help_text=_("Origin time.")
    )
    latitude = models.FloatField(null=True, blank=True, help_text=_("Origin latitude."))
    latitude_uncertainty = models.FloatField(
        null=True, blank=True, help_text=_("Origin latitude uncertainty.")
    )
    longitude = models.FloatField(
        null=True, blank=True, help_text=_("Origin longitude.")
    )
    longitude_uncertainty = models.FloatField(
        null=True, blank=True, help_text=_("Origin longitude uncertainty.")
    )
    depth = models.FloatField(null=True, blank=True, help_text=_("Origin depth."))
    depth_uncertainty = models.FloatField(
        null=True, blank=True, help_text=_("Origin depth uncertainty.")
    )
    method = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Method used to determine the origin."),
    )
    earth_model = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Earth model used to determine the origin."),
    )
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
    is_preferred = models.BooleanField(default=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="+",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("origin")
        verbose_name_plural = _("origins")

    def __str__(self) -> str:
        return f"Origin: {self.id}"

    def __repr__(self) -> str:
        return f"<Origin: {self.id}>"
