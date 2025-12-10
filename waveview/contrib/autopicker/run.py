import logging
import time

from obspy.clients.seedlink.easyseedlink import EasySeedLinkClient
from obspy.core.trace import Trace

from waveview.contrib.autopicker.task import create_event
from waveview.contrib.bpptkg.realtime_detect_pick import DetectionResult, LteSteDetector

logger = logging.getLogger(__name__)


class AutoPickerLteSteDetector(LteSteDetector):
    def enable_debug(self) -> None:
        self.debug = True

    def on_event_confirmed(self, result: DetectionResult) -> None:
        create_event.delay(result.to_dict())


class AutoPickerSeedLinkClient(EasySeedLinkClient):
    def __init__(self, *args, debug: bool = False, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.detector = AutoPickerLteSteDetector(
            network="VG",
            station="MELAB",
            channel="HHZ",
            debug=False,
        )
        if debug:
            self.detector.enable_debug()

    def on_data(self, trace: Trace) -> None:
        self.detector.on_data(trace)


def run_autopicker(debug: bool = False) -> None:
    server_url = "192.168.0.25:18000"
    logger.info(f"Starting AutoPickerSeedLink client connecting to {server_url}")

    client = AutoPickerSeedLinkClient(
        server_url=server_url, autoconnect=True, debug=debug
    )
    client.select_stream("VG", "MELAB", "HHZ")
    client.select_stream("VG", "MEPET", "HHZ")
    client.select_stream("VG", "MEDEL", "HHZ")
    client.select_stream("VG", "MEGRA", "HHZ")
    client.select_stream("VG", "MEPSL", "HHZ")
    client.select_stream("VG", "MESEL", "HHZ")
    client.select_stream("VG", "MEGEM", "HHZ")
    client.select_stream("VG", "MEPAC", "HHZ")

    while True:
        try:
            client.run()
        except KeyboardInterrupt:
            logger.info("Client stopped by user.")
            client.close()
            break
        except Exception as e:
            logger.error(
                f"Error running AutoPickerSeedLink client: {e} - retrying in 5 seconds"
            )
            time.sleep(5)
