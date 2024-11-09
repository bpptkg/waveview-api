from django.db import models
from django.utils.translation import gettext_lazy as _


class RestrictedStatus(models.TextChoices):
    OPEN = "open", _("Open")
    CLOSE = "close", _("Close")
    PARTIAL = "partial", _("Partial")


class FieldType(models.TextChoices):
    DISP = "DISP", _("Displacement")
    VEL = "VEL", _("Velocity")
    ACC = "ACC", _("Acceleration")
    DEF = "DEF", _("Default")
