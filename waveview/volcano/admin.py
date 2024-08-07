from django.contrib import admin

from waveview.volcano.models import Volcano, VolcanoMedia


@admin.register(Volcano)
class VolcanoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
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
        "id",
        "volcano",
        "file",
        "name",
        "size",
        "media_type",
        "uploaded_at",
        "author",
    )
