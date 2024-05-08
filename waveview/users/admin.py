from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from waveview.users.forms import UserChangeForm
from waveview.users.models import User


@admin.register(User)
class UserManager(UserAdmin):
    form = UserChangeForm
    list_display = (
        "id",
        "username",
        "email",
        "name",
        "is_staff",
        "is_active",
        "is_superuser",
        "date_joined",
    )

    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        (
            "General Info",
            {
                "fields": (
                    "name",
                    "bio",
                    "avatar",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                )
            },
        ),
    )
