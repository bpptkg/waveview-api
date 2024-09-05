from django.db import models
from django.utils.translation import gettext_lazy as _


class ObservationForm(models.TextChoices):
    NOT_OBSERVED = "not_observed", _("Not Observed")
    VISIBLE = "visible", _("Visible")
    AUDIBLE = "audible", _("Audible")
    VISIBLE_AND_AUDIBLE = "visible_and_audible", _("Visible and Audible")


class EventSize(models.TextChoices):
    SMALL = "small", _("Small")
    MEDIUM = "medium", _("Medium")
    LARGE = "large", _("Large")
    NOT_OBSERVED = "not_observed", _("Not Observed")


class EmissionColor(models.TextChoices):
    WHITE = "white", _("White")
    GRAY = "gray", _("Gray")
    BLACK = "black", _("Black")
    YELLOW = "yellow", _("Yellow")
    BLUE = "blue", _("Blue")
    RED = "red", _("Red")
    ORANGE = "orange", _("Orange")


class MMIScale(models.TextChoices):
    I = "I", _("I - Not felt")
    II = "II", _("II - Weak")
    III = "III", _("III - Weak")
    IV = "IV", _("IV - Light")
    V = "V", _("V - Moderate")
    VI = "VI", _("VI - Strong")
    VII = "VII", _("VII - Very strong")
    VIII = "VIII", _("VIII - Severe")
    IX = "IX", _("IX - Violent")
    X = "X", _("X - Extreme")
    XI = "XI", _("XI - Extreme")
    XII = "XII", _("XII - Extreme")


class VEI(models.IntegerChoices):
    VEI_0 = 0, _("VEI 0")
    VEI_1 = 1, _("VEI 1")
    VEI_2 = 2, _("VEI 2")
    VEI_3 = 3, _("VEI 3")
    VEI_4 = 4, _("VEI 4")
    VEI_5 = 5, _("VEI 5")
    VEI_6 = 6, _("VEI 6")
    VEI_7 = 7, _("VEI 7")
    VEI_8 = 8, _("VEI 8")
