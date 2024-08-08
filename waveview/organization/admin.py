from django.contrib import admin

from waveview.organization.models import (
    Organization,
    OrganizationMember,
    OrganizationRole,
    OrganizationSettings,
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
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


@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = (
        "id",
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
        "id",
        "slug",
        "name",
        "permissions",
        "order",
        "organization",
    )
    search_fields = ("name",)


@admin.register(OrganizationSettings)
class OrganizationSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "organization",
        "updated_at",
    )
