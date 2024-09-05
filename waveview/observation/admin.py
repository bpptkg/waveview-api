from django.contrib import admin

from waveview.observation.models import (
    Explosion,
    FallDirection,
    ObservatoryPost,
    PyroclasticFlow,
    Rockfall,
    Tectonic,
    VolcanicEmission,
)


@admin.register(Explosion)
class ExplosionAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "observatory_post",
        "occurred_at",
    )


@admin.register(FallDirection)
class FallDirectionAdmin(admin.ModelAdmin):
    list_display = (
        "volcano",
        "name",
    )


@admin.register(ObservatoryPost)
class ObservatoryPostAdmin(admin.ModelAdmin):
    list_display = (
        "volcano",
        "name",
    )


@admin.register(PyroclasticFlow)
class PyroclasticFlowAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "observatory_post",
        "occurred_at",
    )


@admin.register(Rockfall)
class RockfallAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "observatory_post",
        "occurred_at",
    )


@admin.register(Tectonic)
class TectonicAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "observatory_post",
        "occurred_at",
    )


@admin.register(VolcanicEmission)
class VolcanicEmissionAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "observatory_post",
        "occurred_at",
    )
