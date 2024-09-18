from django.contrib import admin

from waveview.appconfig.models import (
    HypocenterConfig,
    MagnitudeConfig,
    PickerConfig,
    SeismicityConfig,
)


@admin.register(PickerConfig)
class PickerConfigAdmin(admin.ModelAdmin):
    list_display = (
        "volcano",
        "organization",
        "user",
        "created_at",
        "updated_at",
    )


@admin.register(HypocenterConfig)
class HypocenterConfigAdmin(admin.ModelAdmin):
    list_display = (
        "volcano",
        "name",
        "is_preferred",
        "created_at",
        "updated_at",
    )


@admin.register(SeismicityConfig)
class SeismicityConfigAdmin(admin.ModelAdmin):
    list_display = (
        "volcano",
        "type",
        "order",
        "created_at",
        "updated_at",
    )
    ordering = ("order",)


@admin.register(MagnitudeConfig)
class MagnitudeConfigAdmin(admin.ModelAdmin):
    list_display = (
        "volcano",
        "name",
        "method",
        "created_at",
        "updated_at",
    )
