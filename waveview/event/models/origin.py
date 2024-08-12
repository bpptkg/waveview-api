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
    time = models.DateTimeField(db_index=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    depth = models.FloatField(null=True, blank=True)
    method = models.CharField(max_length=255, null=True, blank=True)
    earth_model = models.CharField(max_length=255, null=True, blank=True)
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
