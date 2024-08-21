from django.db import models
from django.utils.translation import gettext_lazy as _


class DEMFileFormat(models.TextChoices):
    SURFER_GRID = "surfer_grid", _("Surfer Grid")
    GEOTIFF = "geotiff", _("GeoTIFF")
    NETCDF = "netcdf", _("NetCDF")
    ASCII = "ascii", _("ASCII")
    OTHER = "other", _("Other")
