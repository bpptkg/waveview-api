import logging
from dataclasses import dataclass
from datetime import UTC, datetime

import pandas as pd

from waveview.contrib.sinoas.context import SinoasContext

logger = logging.getLogger(__name__)


@dataclass
class DetectedEvent:
    time: datetime
    duration: float
    mepas_rsam: float


class Detector:
    """
    Detector class to detect event from the RSAM data.
    """

    def __init__(self, context: SinoasContext | None = None) -> None:
        self.context = context
        self.time: datetime | None = None
        self.triggered: bool = False
        self.duration: float = 0
        self.mepas_rsam: float = 0

    def reset(self) -> None:
        self.time = None
        self.triggered = False
        self.duration = 0
        self.mepas_rsam = 0

    def detect(self, raw: pd.DataFrame) -> None:
        if raw.empty:
            return

        # Get the last 3 seconds.
        df = raw.iloc[-3:]

        # Find median and round it.
        median = df["rsam"].median()
        median = round(median)

        if self.triggered:
            self.duration = (datetime.now(UTC) - self.time).total_seconds()
            if self.mepas_rsam < median:
                self.mepas_rsam = median

            if median <= 750:
                is_event = (self.mepas_rsam > 2500 and self.duration > 10) or (
                    self.mepas_rsam <= 2500 and self.duration > 25
                )
                if is_event:
                    event = DetectedEvent(
                        time=self.time,
                        duration=self.duration,
                        mepas_rsam=self.mepas_rsam,
                    )
                    self.on_detected(event.time, event.duration, event.mepas_rsam)
                self.reset()
        else:
            if median > 3000:
                self.time = df["time"].iloc[-1]
                self.mepas_rsam = median
                self.triggered = True

    def on_detected(self, event: DetectedEvent) -> None:
        logger.info(
            f"Detected event at {event.time} with duration {event.duration} and MEPAS rsam {event.mepas_rsam}"
        )
