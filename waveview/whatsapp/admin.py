from django.contrib import admin

from waveview.whatsapp.models import Group


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "group_id",
        "description",
        "excluded",
        "created_at",
        "updated_at",
    )
