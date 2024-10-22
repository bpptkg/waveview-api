from dataclasses import dataclass

from waveview.organization.models import Organization
from waveview.volcano.models import Volcano


@dataclass
class SinoasContext:
    organization: Organization
    volcano: Volcano
