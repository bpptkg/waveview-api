from django.db import models


class PermissionType(models.TextChoices):
    """
    Permission choices for organization roles.
    """

    FULL_ACCESS = "full_access", "Full Access"
