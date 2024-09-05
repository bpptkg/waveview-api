import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from waveview.observation.choices import EmissionColor, ObservationForm


class VolcanicEmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        "event.Event",
        on_delete=models.CASCADE,
        related_name="volcanic_emissions",
        related_query_name="volcanic_emission",
    )
    observatory_post = models.ForeignKey(
        "ObservatoryPost", on_delete=models.SET_NULL, null=True, blank=True
    )
    occurred_at = models.DateTimeField(null=True, blank=True)
    observation_form = models.CharField(
        max_length=100, choices=ObservationForm.choices, null=True, blank=True
    )
    height = models.FloatField(null=True, blank=True)
    color = models.CharField(
        max_length=100, choices=EmissionColor.choices, null=True, blank=True
    )
    intensity = models.FloatField(null=True, blank=True)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Volcanic Emission")
        verbose_name_plural = _("Volcanic Emissions")
