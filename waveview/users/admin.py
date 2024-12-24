from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpRequest

from waveview.users.forms import UserChangeForm
from waveview.users.models import User


@admin.register(User)
class UserManager(UserAdmin):
    form = UserChangeForm
    list_display = (
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

    def has_delete_permission(self, request: HttpRequest, obj: User = None) -> None:
        return False
