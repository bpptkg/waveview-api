from django.db import models
from django.utils.translation import gettext_lazy as _


class PermissionType(models.TextChoices):
    """
    Permission choices for organization roles.
    """

    ADD_MEMBER = "add_member", _("Add Member")
    REMOVE_MEMBER = "remove_member", _("Remove Member")
    UPDATE_MEMBER = "update_member", _("Update Member")

    CREATE_VOLCANO = "create_volcano", _("Create Volcano")
    UPDATE_VOLCANO = "update_volcano", _("Update Volcano")
    DELETE_VOLCANO = "delete_volcano", _("Delete Volcano")
