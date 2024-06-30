from django.contrib import admin

from waveview.volcano.models import Volcano


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
