import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from waveview.observation.choices import VEI, EmissionColor, ObservationForm


class Explosion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.OneToOneField(
        "event.Event",
        on_delete=models.CASCADE,
        related_name="explosion",
    )
    observation_form = models.CharField(
        max_length=100, choices=ObservationForm.choices, null=True, blank=True
    )
    column_height = models.FloatField(null=True, blank=True)
    color = models.CharField(
        max_length=100, choices=EmissionColor.choices, null=True, blank=True
    )
    intensity = models.FloatField(null=True, blank=True)
    vei = models.IntegerField(choices=VEI.choices, null=True, blank=True)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Explosion")
        verbose_name_plural = _("Explosions")
