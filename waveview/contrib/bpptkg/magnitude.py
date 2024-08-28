import logging
from datetime import timedelta

import numpy as np
from django.db import connection
from obspy import Inventory as ObspyInventory
from obspy import Stream, read_inventory

from waveview.contrib.magnitude.base import (
    BaseMagnitudeCalculator,
    register_magnitude_calculator,
)
from waveview.event.header import (
    AmplitudeCategory,
    AmplitudeUnit,
    EvaluationMode,
    EvaluationStatus,
)
from waveview.event.models import (
    Amplitude,
    Event,
    Magnitude,
    StationMagnitude,
    StationMagnitudeContribution,
)
from waveview.inventory.models import Channel, Inventory
from waveview.inventory.streamio import DataStream
from waveview.appconfig.models import (
    MagnitudeConfig,
    StationMagnitudeConfig,
)

logger = logging.getLogger(__name__)


def calculate_bpptkg_ml(amplitude: float) -> float:
    """
    Compute BPPTKG Richter local magnitude scale (ML) from amplitude.

    Note that amplitude zero to peak amplitude is in mm. Calibration function
    log10(A0) for BPPTKG seismic network is -1.4.

    Richter magnitude scale is computed using the following equation:

        ml = log10(amplitude) - log10(A0)

    where log10(A0) equal to -1.4 and ml is Richter local magnitude scale.
    """
    return np.log10(amplitude) + 1.4


class MagnitudeCalculator(BaseMagnitudeCalculator):
    method = "bpptkg"

    def __init__(self) -> None:
        super().__init__()

        self.datastream = DataStream(connection)

    def calc_magnitude(
        self,
        organization_id: str,
        volcano_id: str,
        event_id: str,
        author_id: str,
    ) -> None:
        config = MagnitudeConfig.objects.filter(
            organization_id=organization_id,
            volcano_id=volcano_id,
            is_enabled=True,
            is_preferred=True,
        ).first()
        if not config:
            logger.error("No preferred magnitude config found.")
            return

        channels = StationMagnitudeConfig.objects.filter(
            magnitude_config_id=config.id, is_enabled=True
        ).values_list("channel", flat=True)
        inventory = self.get_inventory(organization_id)
        event = Event.objects.get(id=event_id)

        self.calc_ML_magnitude(event, inventory, channels, author_id)

    def get_inventory(self, organization_id: str) -> Inventory:
        inventory = Inventory.objects.get(organization_id=organization_id)
        return inventory

    def get_amplitude(self, stream: Stream) -> float:
        if len(stream) == 0:
            return None

        data: np.ndarray = stream[0].data
        amplitude = np.abs(data).max()
        return amplitude * 1e3

    def calc_ML_magnitude(
        self,
        event: Event,
        inventory: Inventory,
        channels: list[Channel],
        author_id: str,
    ) -> None:
        inv: ObspyInventory = read_inventory(inventory.file.path)
        starttime = event.time
        endtime = starttime + timedelta(seconds=event.duration)
        magnitude_type = "ML"

        magnitude, _ = Magnitude.objects.get_or_create(
            event=event,
            method=self.method,
            type=magnitude_type,
            defaults={
                "magnitude": 0,
                "station_count": 0,
                "azimuthal_gap": 0,
                "evaluation_status": EvaluationStatus.PRELIMINARY,
                "author_id": author_id,
            },
        )

        magnitude_values: list[float] = []

        for channel in channels:
            stream = self.datastream.get_waveform(channel.id, starttime, endtime)
            stream.merge(fill_value=0)
            stream.detrend("demean")
            pre_filt = [0.001, 0.005, 45, 50]
            stream.remove_response(
                inventory=inv, pre_filt=pre_filt, output="DISP", water_level=60
            )

            amplitude_value = self.get_amplitude(stream)
            if amplitude_value is None:
                continue
            magnitude_value = calculate_bpptkg_ml(amplitude_value)
            magnitude_values.append(magnitude_value)

            amplitude, _ = Amplitude.objects.update_or_create(
                event=event,
                waveform=channel,
                method=self.method,
                defaults={
                    "amplitude": amplitude_value,
                    "type": "Zero-to-Peak",
                    "category": AmplitudeCategory.DURATION,
                    "time": starttime,
                    "begin": 0,
                    "end": event.duration,
                    "snr": 0,
                    "unit": AmplitudeUnit.MM,
                    "evaluation_mode": EvaluationMode.AUTOMATIC,
                    "author_id": author_id,
                },
            )
            station_magnitude, _ = StationMagnitude.objects.update_or_create(
                amplitude=amplitude,
                defaults={
                    "magnitude": magnitude_value,
                    "type": magnitude_type,
                    "method": self.method,
                    "author_id": author_id,
                },
            )
            StationMagnitudeContribution.objects.update_or_create(
                magnitude=magnitude,
                station_magnitude=station_magnitude,
                defaults={
                    "weight": 1,
                    "residual": 0,
                },
            )

        magnitude.magnitude = np.mean(magnitude_values)
        magnitude.station_count = len(magnitude_values)
        magnitude.save()


register_magnitude_calculator("bpptkg", MagnitudeCalculator())
