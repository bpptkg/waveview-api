from django.contrib import admin
from django.http import HttpRequest

from waveview.organization.models import (
    Organization,
    OrganizationMember,
    OrganizationRole,
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "slug",
        "name",
        "email",
        "description",
        "url",
        "address",
        "author",
        "created_at",
        "updated_at",
    )
    search_fields = ("name",)

    def has_delete_permission(
        self, request: HttpRequest, obj: Organization = None
    ) -> None:
        return False


@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = (
        "organization",
        "user",
        "date_added",
        "expiration_date",
        "inviter",
    )
    search_fields = ("organization",)


@admin.register(OrganizationRole)
class OrganizationRoleAdmin(admin.ModelAdmin):
    list_display = (
        "slug",
        "name",
        "permissions",
        "order",
        "organization",
    )
    search_fields = ("name",)
