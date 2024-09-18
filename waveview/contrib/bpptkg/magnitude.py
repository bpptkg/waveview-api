import logging
from datetime import timedelta

import numpy as np
from django.db import connection, transaction
from obspy import Inventory as ObspyInventory
from obspy import Stream, read_inventory

from waveview.appconfig.models import MagnitudeConfig
from waveview.event.header import (
    AmplitudeCategory,
    AmplitudeUnit,
    EvaluationMode,
    EvaluationStatus,
)
from waveview.event.magnitude import BaseMagnitudeEstimator, MagnitudeEstimatorData
from waveview.event.models import (
    Amplitude,
    Event,
    Magnitude,
    StationMagnitude,
    StationMagnitudeContribution,
)
from waveview.event.observers import EventObserver
from waveview.inventory.datastream import DataStream
from waveview.inventory.models import Channel, Inventory
from waveview.tasks.calc_magnitude import calc_magnitude

logger = logging.getLogger(__name__)


def calc_bpptkg_ml(amplitude: float) -> float:
    """
    Compute BPPTKG Richter local magnitude scale (ML) from amplitude.

    Note that amplitude zero to peak amplitude is in mm. Calibration function
    log10(A0) for BPPTKG seismic network is -1.4.

    Richter magnitude scale is computed using the following equation:

        ml = log10(amplitude) - log10(A0)

    where log10(A0) equal to -1.4 and ml is Richter local magnitude scale.
    """
    return np.log10(amplitude) + 1.4


class MagnitudeEstimator(BaseMagnitudeEstimator):
    method = "bpptkg"

    def __init__(self, config: MagnitudeConfig) -> None:
        super().__init__(config)

        self.datastream = DataStream(connection)

    @transaction.atomic
    def calc_magnitude(self, data: MagnitudeEstimatorData) -> None:
        organization_id = data.organization_id
        event_id = data.event_id
        author_id = data.author_id

        channel_ids = StationMagnitudeConfig.objects.filter(
            magnitude_config_id=self.config.id, is_enabled=True
        ).values_list("channel", flat=True)
        channels = Channel.objects.filter(id__in=channel_ids).all()
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
        minval = np.abs(data).min()
        maxval = np.abs(data).max()
        amplitude = (maxval - minval) / 2
        if np.isnan(amplitude):
            return None
        return amplitude * 1e3  # Convert to mm

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
                "is_preferred": True,
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
            magnitude_value = calc_bpptkg_ml(amplitude_value)
            magnitude_values.append(magnitude_value)

            amplitude, _ = Amplitude.objects.update_or_create(
                event=event,
                waveform=channel,
                method=self.method,
                defaults={
                    "amplitude": amplitude_value,
                    "type": "Amax",
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

        if not magnitude_values:
            return
        avg_magnitude = np.mean(magnitude_values)
        if np.isnan(avg_magnitude):
            return
        magnitude.magnitude = avg_magnitude
        magnitude.station_count = len(magnitude_values)
        magnitude.save()


class MagnitudeObserver(EventObserver):
    def run(self, event: Event) -> None:
        event_id = str(event.id)
        volcano_id = str(event.catalog.volcano.id)
        organization_id = str(event.catalog.volcano.organization.id)
        author_id = str(event.author.id)
        calc_magnitude.delay(organization_id, volcano_id, event_id, author_id)
