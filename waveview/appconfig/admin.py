from django.contrib import admin

from waveview.appconfig.models import (
    HelicorderConfig,
    HypocenterConfig,
    MagnitudeConfig,
    PickerConfig,
    SeismicityConfig,
    SeismogramConfig,
    SeismogramStationConfig,
    StationMagnitudeConfig,
)


@admin.register(PickerConfig)
class PickerConfigAdmin(admin.ModelAdmin):
    list_display = (
        "organization",
        "volcano",
        "name",
        "is_preferred",
        "created_at",
        "updated_at",
    )


@admin.register(HelicorderConfig)
class HelicorderConfigAdmin(admin.ModelAdmin):
    list_display = (
        "picker_config",
        "channel",
        "color",
        "color_light",
        "color_dark",
    )


@admin.register(SeismogramConfig)
class SeismogramConfigAdmin(admin.ModelAdmin):
    list_display = (
        "picker_config",
        "component",
    )


@admin.register(SeismogramStationConfig)
class SeismogramStationConfigAdmin(admin.ModelAdmin):
    list_display = (
        "picker_config",
        "station",
        "color",
        "color_light",
        "color_dark",
        "order",
    )

    def picker_config(self, obj: SeismogramStationConfig) -> PickerConfig:
        return obj.seismogram_config.picker_config


@admin.register(HypocenterConfig)
class HypocenterConfigAdmin(admin.ModelAdmin):
    list_display = (
        "organization",
        "volcano",
        "name",
        "is_preferred",
        "created_at",
        "updated_at",
    )


@admin.register(SeismicityConfig)
class SeismicityConfigAdmin(admin.ModelAdmin):
    list_display = (
        "organization",
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
        "organization",
        "volcano",
        "name",
        "method",
        "created_at",
        "updated_at",
    )


@admin.register(StationMagnitudeConfig)
class StationMagnitudeConfigAdmin(admin.ModelAdmin):
    list_display = (
        "magnitude_config",
        "channel",
        "is_enabled",
    )
