from django.contrib import admin
from django.http import HttpRequest

from waveview.volcano.models import DigitalElevationModel, Volcano, VolcanoMedia


@admin.register(Volcano)
class VolcanoAdmin(admin.ModelAdmin):
    list_display = (
        "slug",
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

    def has_delete_permission(self, request: HttpRequest, obj: Volcano = None) -> None:
        return False


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
