from django.contrib import admin

from waveview.organization.models import Organization, OrganizationMember, Role


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "slug",
        "name",
        "email",
        "description",
        "url",
        "address",
        "authority_domain",
        "author",
        "created_at",
        "updated_at",
    )
    search_fields = ("name",)


@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = (
        "organization",
        "user",
        "role",
        "email",
        "date_added",
        "expiration_date",
        "inviter",
    )
    search_fields = ("organization",)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = (
        "slug",
        "name",
        "permissions",
        "order",
        "organization",
    )
    search_fields = ("name",)
