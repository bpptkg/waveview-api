from django.contrib import admin

from waveview.volcano.models import DigitalElevationModel, Volcano, VolcanoMedia


@admin.register(Volcano)
class VolcanoAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "elevation",
        "location",
        "country",
        "latitude",
        "longitude",
        "author",
        "created_at",
        "updated_at",
    )


@admin.register(VolcanoMedia)
class VolcanoMediaAdmin(admin.ModelAdmin):
    list_display = (
        "volcano",
        "name",
        "size",
        "media_type",
        "uploaded_at",
        "author",
    )


@admin.register(DigitalElevationModel)
class DigitalElevationModelAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "type",
        "utm_zone",
        "uploaded_at",
        "author",
        "is_default",
    )
