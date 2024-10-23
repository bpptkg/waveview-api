import logging
import time

from django.conf import settings

from waveview.contrib.sinoas.channels import WinstonChannel
from waveview.contrib.sinoas.context import SinoasContext
from waveview.contrib.sinoas.detector import Detector
from waveview.contrib.sinoas.fetcher import Fetcher, build_rsam_url
from waveview.organization.models import Organization
from waveview.users.models import User
from waveview.volcano.models import Volcano

logger = logging.getLogger(__name__)


class Sinoas:
    """
    SINOAS event detection class.

    This class is responsible for running the SINOAS event detection process. It
    fetches the RSAM data from the Winston server, detects events, and creates
    events in the database. The process runs in a loop until it is stopped.
    """

    def __init__(
        self,
        organization: Organization,
        volcano: Volcano,
        user: User,
        interval: int = 1,
        max_sleep: int = 60,
        dry_run: bool = False,
    ) -> None:
        self.organization = organization
        self.volcano = volcano
        self.user = user
        self.is_running = True
        self.interval = interval
        self.max_sleep = max_sleep
        self.dry_run = dry_run

    def stop(self) -> None:
        self.is_running = False

    def run(self) -> None:
        context = SinoasContext(
            organization=self.organization, volcano=self.volcano, user=self.user
        )
        detector = Detector(context=context)
        url = build_rsam_url(WinstonChannel.VG_MEPAS_HHZ)
        fetcher = Fetcher()
        retry_duration = self.interval

        while self.is_running:
            try:
                raw = fetcher.fetch(url)
                detector.detect(raw)

                time.sleep(self.interval)
                retry_duration = self.interval
            except KeyboardInterrupt:
                logger.info("Stopping SINOAS event detection.")
                self.stop()
            except Exception as e:
                logger.error(f"Error processing data: {e}")
                retry_duration = min(retry_duration * 2, self.max_sleep)
                time.sleep(retry_duration)


def run_sinoas(
    organization: Organization, volcano: Volcano, user: User, dry_run: bool = False
) -> None:
    """
    Run the SINOAS event detection.
    """
    logger.info(
        f"Running SINOAS event detection using Winston server at {settings.SINOAS_WINSTON_URL}"
    )
    logger.info(f"Organization: {organization}, Volcano: {volcano}, User: {user}")
    logger.info("Press Ctrl+C to stop.")

    sinoas = Sinoas(
        organization=organization, volcano=volcano, user=user, dry_run=dry_run
    )
    sinoas.run()
