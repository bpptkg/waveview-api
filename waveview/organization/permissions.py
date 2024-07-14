from django.db import models
from django.utils.translation import gettext_lazy as _


class PermissionType(models.TextChoices):
    """
    Permission choices for organization roles.
    """

    ADD_MEMBER = "member:add", _("Add Member")
    REMOVE_MEMBER = "member:remove", _("Remove Member")
    UPDATE_MEMBER = "member:update", _("Update Member")

    CREATE_VOLCANO = "volcano:create", _("Create Volcano")
    UPDATE_VOLCANO = "volcano:update", _("Update Volcano")
    DELETE_VOLCANO = "volcano:delete", _("Delete Volcano")

    CREATE_CATALOG = "catalog:create", _("Create Catalog")
    UPDATE_CATALOG = "catalog:update", _("Update Catalog")
    DELETE_CATALOG = "catalog:delete", _("Delete Catalog")

    CREATE_EVENT = "event:create", _("Create Event")
    UPDATE_EVENT = "event:update", _("Update Event")
    DELETE_EVENT = "event:delete", _("Delete Event")

    MANAGE_EVENT_TYPE = "event_type:manage", _("Manage Event Type")

    MANAGE_INVENTORY = "inventory:manage", _("Manage Inventory")
