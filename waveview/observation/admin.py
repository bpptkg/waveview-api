from django.contrib import admin

from waveview.observation.models import (
    Explosion,
    FallDirection,
    PyroclasticFlow,
    Rockfall,
    Tectonic,
    VolcanicEmission,
)


@admin.register(Explosion)
class ExplosionAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "observation_form",
        "column_height",
        "color",
        "intensity",
        "vei",
        "note",
    )


@admin.register(FallDirection)
class FallDirectionAdmin(admin.ModelAdmin):
    list_display = (
        "volcano",
        "name",
        "description",
        "azimuth",
    )


@admin.register(PyroclasticFlow)
class PyroclasticFlowAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "is_lava_flow",
        "observation_form",
        "event_size",
        "runout_distance",
        "amplitude",
        "duration",
        "note",
    )


@admin.register(Rockfall)
class RockfallAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "is_lava_flow",
        "observation_form",
        "event_size",
        "runout_distance",
        "amplitude",
        "duration",
        "note",
    )


@admin.register(Tectonic)
class TectonicAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "mmi_scale",
        "magnitude",
        "depth",
        "note",
    )


@admin.register(VolcanicEmission)
class VolcanicEmissionAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "observation_form",
        "height",
        "color",
        "intensity",
        "note",
    )
