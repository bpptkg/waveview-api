from django.db import models


class AmplitudeCategory(models.TextChoices):
    """
    Amplitude category. This attribute describes the way the waveform trace is
    evaluated to derive an amplitude value. This can be just reading a single
    value for a given point in time (point), taking a mean value over a time
    interval (mean), integrating the trace over a time interval (integral),
    specifying just a time interval (duration), or evaluating a period (period).
    """

    POINT = "point", "Point"
    MEAN = "mean", "Mean"
    DURATION = "duration", "Duration"
    PERIOD = "period", "Period"
    INTEGRAL = "integral", "Integral"
    OTHER = "other", "Other"


class AmplitudeUnit(models.TextChoices):
    """
    Amplitude unit. This attribute provides the most likely measurement units
    for the physical quantity in the amplitude. Possible values are specified as
    combinations of SI base units.
    """

    MM = "mm", "mm"
    M = "m", "M"
    S = "s", "s"
    M_S = "m/s", "m/s"
    M_S2 = "m/s**2", "m/s**2"
    MS = "m*s", "m*s"
    DIMENSIONLESS = "", "Dimensionless"
    OTHER = "other", "Other"


class EvaluationMode(models.TextChoices):
    """
    Mode of an evaluation.
    """

    AUTOMATIC = "automatic", "Automatic"
    MANUAL = "manual", "Manual"


class EvaluationStatus(models.TextChoices):
    """
    Status of an evaluation.
    """

    PRELIMINARY = "preliminary", "Preliminary"
    CONFIRMED = "confirmed", "Confirmed"
    REVIEWED = "reviewed", "Reviewed"
    FINAL = "final", "Final"
    REJECTED = "rejected", "Rejected"


class EventTypeCertainty(models.TextChoices):
    """
    Denotes how certain the information on event type is.
    """

    KNOWN = "known", "Known"
    SUSPECTED = "suspected", "Suspected"
    DAMAGING = "damaging", "Damaging"
    FELT = "felt", "Felt"


class OriginDepthType(models.TextChoices):
    """
    Type of origin depth determination.
    """

    FROM_LOCATION = "from_location", "From Location"
    FROM_MOMENT_TENSOR_INVERSION = (
        "from_moment_tensor_inversion",
        "From Moment Tensor Inversion",
    )
    BROAD_BAND_P_WAVEFORMS = "broad_band_p_waveforms", "Broad Band P Waveforms"
    CONSTRAINED_BY_DEPTH_PHASES = (
        "constrained_by_depth_phases",
        "Constrained By Depth Phases",
    )
    CONSTRAINED_BY_DIRECT_PHASES = (
        "constrained_by_direct_phases",
        "Constrained By Direct Phases",
    )
    OPERATOR_ASSIGNED = "operator_assigned", "Operator Assigned"
    OTHER_ORIGIN_DEPTH = "other_origin_depth", "Other Origin Depth"


class OriginType(models.TextChoices):
    """
    Origin type.
    """

    HYPOCENTER = "hypocenter", "Hypocenter"
    CENTROID = "centroid", "Centroid"
    AMPITUDE = "amplitude", "Amplitude"
    MACROSEISMIC = "macroseismic", "Macroseismic"
    RUPTURE_START = "rupture_start", "Rupture Start"
    RUPTURE_END = "rupture_end", "Rupture End"


class OriginUncertaintyDescription(models.TextChoices):
    """
    Preferred origin uncertainty description.
    """

    HORIZONTAL = "horizontal", "Horizontal"
    ELLIPSE = "ellipse", "Uncertainty Ellipse"
    ELLIPSOID = "ellipsoid", "Confidence Ellipsoid"
    PDF = "pdf", "Probability Density Function"


class PickOnset(models.TextChoices):
    """
    Flag that roughly categorizes the sharpness of the pick onset.
    """

    EMERGENT = "emergent", "Emergent"
    IMPULSIVE = "impulsive", "Impulsive"
    QUESTIONABLE = "questionable", "Questionable"


class PickPolarity(models.TextChoices):
    """
    Indicates the polarity of first motion, usually from impulsive onsets.
    """

    POSITIVE = "positive", "Positive"
    NEGATIVE = "negative", "Negative"
    UNDECIDABLE = "undecidable", "Undecidable"


class MagnitudeType(models.TextChoices):
    """
    Magnitude type.
    """

    M = "M", "Unspecified Magnitude"
    ML = "ML", "Local Magnitude"
    MB = "Mb", "Body Wave Magnitude"
    MS = "MS", "Surface Wave Magnitude"
    MW = "Mw", "Moment Magnitude"
    MD = "Md", "Duration Magnitude"
    ME = "Me", "Energy Magnitude"
    MC = "Mc", "Coda Magnitude"
    OTHER = "other", "Other"


class ObservationType(models.TextChoices):
    EXPLOSION = "explosion", "Explosion"
    PYROCLASTIC_FLOW = "pyroclastic_flow", "Pyroclastic Flow"
    ROCKFALL = "rockfall", "Rockfall"
    TECTONIC = "tectonic", "Tectonic"
    VOLCANIC_EMISION = "volcanic_emision", "Volcanic Emision"
    LAHAR = "lahar", "Lahar"
    SOUND = "sound", "Sound"
