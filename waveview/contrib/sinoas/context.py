from dataclasses import dataclass

from waveview.organization.models import Organization
from waveview.volcano.models import Volcano
from waveview.users.models import User


@dataclass
class SinoasContext:
    organization: Organization
    volcano: Volcano
    user: User
