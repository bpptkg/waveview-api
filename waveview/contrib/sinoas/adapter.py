import logging
import time

from django.conf import settings

from waveview.contrib.sinoas.channels import WinstonChannel
from waveview.contrib.sinoas.context import SinoasContext
from waveview.contrib.sinoas.detector import Detector
from waveview.contrib.sinoas.fetcher import Fetcher, build_rsam_url
from waveview.organization.models import Organization
from waveview.volcano.models import Volcano

logger = logging.getLogger(__name__)


class Sinoas:
    def __init__(self, organization: Organization, volcano: Volcano) -> None:
        self.organization = organization
        self.volcano = volcano
        self.is_running = True

    def stop(self) -> None:
        self.is_running = False

    def run(self) -> None:
        context = SinoasContext(organization=self.organization, volcano=self.volcano)
        detector = Detector(context=context)
        url = build_rsam_url(WinstonChannel.VG_MEPAS_HHZ)
        fetcher = Fetcher()

        while self.is_running:
            try:
                raw = fetcher.fetch(url)
                detector.detect(raw)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error processing data: {e}")
            time.sleep(1)


def run_sinoas(organization: Organization, volcano: Volcano) -> None:
    logger.info(
        f"Running SINOAS event detection using Winston server at {settings.SINOAS_WINSTON_URL}"
    )
    logger.info(f"Organization: {organization}")
    logger.info(f"Volcano: {volcano}")
    logger.info("Press Ctrl+C to stop.")

    sinoas = Sinoas(organization=organization, volcano=volcano)
    sinoas.run()
