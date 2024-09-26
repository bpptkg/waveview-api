import logging
from dataclasses import dataclass
from datetime import timedelta

import numpy as np
from django.db import connection, transaction
from obspy import Inventory as ObspyInventory
from obspy import Stream, read_inventory

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
from waveview.event.observers import EventObserver
from waveview.inventory.datastream import DataStream
from waveview.inventory.models import Channel, Inventory

logger = logging.getLogger(__name__)


def calc_bpptkg_ml(amplitude: float) -> float:
    """
    Compute BPPTKG Richter local magnitude scale (ML) from amplitude.

    Note that amplitude zero to peak amplitude is in meter, but in calculation,
    it uses micro-meter. Calibration function log10(A0) for BPPTKG seismic
    network is -1.4.

    Richter magnitude scale is computed using the following equation:

        ml = log10(amplitude) - log10(A0)

    where log10(A0) equal to -1.4 and ml is Richter local magnitude scale.
    """
    ampl = amplitude * 1e6  # Convert to micro-meter.
    return np.log10(ampl) + 1.4


@dataclass
class MagnitudeEstimatorData:
    organization_id: str
    volcano_id: str
    event_id: str
    author_id: str
    channels: list[str]
    preferred_channel: str = ""
    is_preferred: bool = False


class MagnitudeEstimator:
    method = "bpptkg"

    def __init__(self) -> None:
        self.datastream = DataStream(connection)
        self.preferred_map: dict[str, bool] = {}

    @transaction.atomic
    def calc_magnitude(self, data: MagnitudeEstimatorData) -> None:
        organization_id = data.organization_id
        event_id = data.event_id
        author_id = data.author_id
        is_preferred = data.is_preferred
        preferred_channel = data.preferred_channel

        channels: list[Channel] = []
        for network_station_channel in data.channels:
            network, station, channel = network_station_channel.split(".")
            try:
                instance = Channel.objects.filter(
                    code=channel, station__code=station, station__network__code=network
                ).get()
                channels.append(instance)
                channel_id = str(instance.id)
                if network_station_channel == preferred_channel:
                    self.preferred_map[channel_id] = True
                else:
                    self.preferred_map[channel_id] = False
            except Channel.DoesNotExist:
                logger.error(f"Channel {network_station_channel} does not exist.")

        inventory = self.get_inventory(organization_id)
        event = Event.objects.get(id=event_id)

        self.calc_ML_magnitude(
            event, inventory, channels, author_id, is_preferred=is_preferred
        )

    def get_inventory(self, organization_id: str) -> Inventory:
        inventory = Inventory.objects.get(organization_id=organization_id)
        return inventory

    def get_amax(self, stream: Stream) -> float:
        """
        Get Amax (peak-to-peak/2) value from stream in m.
        """
        if len(stream) == 0:
            return None

        data: np.ndarray = stream[0].data
        minval = np.min(data)
        maxval = np.max(data)
        amplitude = (maxval - minval) / 2
        if np.isnan(amplitude):
            return None
        return amplitude

    def get_zeropk(self, stream: Stream) -> float:
        """
        Get zero-to-peak value from stream in m.
        """
        if len(stream) == 0:
            return None

        data: np.ndarray = stream[0].data
        amplitude = np.max(np.abs(data))
        if np.isnan(amplitude):
            return None
        return amplitude

    def calc_ML_magnitude(
        self,
        event: Event,
        inventory: Inventory,
        channels: list[Channel],
        author_id: str,
        is_preferred: bool = False,
    ) -> None:
        buffer = 3  # Buffer in seconds.
        starttime = event.time - timedelta(seconds=buffer)
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
                "is_preferred": is_preferred,
            },
        )

        magnitude_values: list[float] = []
        stations: set[str] = set()

        def remove_response(st: Stream) -> Stream:
            for inv_file in inventory.files.all():
                inv: ObspyInventory = read_inventory(inv_file.file)
                try:
                    st.merge(fill_value=0)
                    st.detrend("demean")
                    pre_filt = [0.001, 0.005, 45, 50]
                    st.remove_response(
                        inventory=inv, pre_filt=pre_filt, output="DISP", water_level=60
                    )
                    return st
                except Exception:
                    pass
            raise Exception("No matching inventory found.")

        for channel in channels:
            stream = self.datastream.get_waveform(channel.id, starttime, endtime)
            try:
                stream = remove_response(stream)
            except Exception as e:
                logger.error(f"Failed to remove response: {e}")
                continue

            amax = self.get_amax(stream)
            if amax is None:
                continue
            zeropk = self.get_zeropk(stream)
            if zeropk is None:
                continue
            ml = calc_bpptkg_ml(zeropk)
            magnitude_values.append(ml)
            stations.add(channel.station.code)

            amplitude, _ = Amplitude.objects.update_or_create(
                event=event,
                waveform=channel,
                method=self.method,
                defaults={
                    "amplitude": amax * 1e3,  # Convert to mm
                    "type": "Amax",
                    "category": AmplitudeCategory.DURATION,
                    "time": event.time,
                    "begin": buffer,
                    "end": event.duration,
                    "snr": 0,
                    "unit": AmplitudeUnit.MM,
                    "evaluation_mode": EvaluationMode.AUTOMATIC,
                    "author_id": author_id,
                    "is_preferred": self.preferred_map.get(str(channel.id), False),
                },
            )
            station_magnitude, _ = StationMagnitude.objects.update_or_create(
                amplitude=amplitude,
                defaults={
                    "magnitude": ml,
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
        avg = np.mean(magnitude_values)
        if np.isnan(avg):
            return
        magnitude.magnitude = avg
        magnitude.station_count = len(stations)
        magnitude.save()


class MagnitudeObserver(EventObserver):
    """
    This observer calculates BPPTKG local magnitude (ML) for an event. The
    observer uses the following formula to compute Richter local magnitude scale
    (ML) from amplitude:

        ml = log10(amplitude) - log10(A0)

    where log10(A0) equal to -1.4 and ml is Richter local magnitude scale.

    The observer calculates ML magnitude for each channel and then computes the
    average magnitude value.

    Required data are:

    - channels: list of channels to calculate ML magnitude, e.g.
      ["network.station.channel", ...]
    """

    name = "bpptkg.magnitude"

    def update(self, event_id: str, data: dict) -> None:
        event = Event.objects.get(id=event_id)
        event_id = str(event.id)
        volcano_id = str(event.catalog.volcano.id)
        organization_id = str(event.catalog.volcano.organization.id)
        author_id = str(event.author.id)
        channels = data.get("channels", [])
        is_preferred = data.get("is_preferred", False)
        preferred_channel = data.get("preferred_channel", "")

        estimator = MagnitudeEstimator()
        estimator.calc_magnitude(
            MagnitudeEstimatorData(
                organization_id=organization_id,
                volcano_id=volcano_id,
                event_id=event_id,
                author_id=author_id,
                channels=channels,
                is_preferred=is_preferred,
                preferred_channel=preferred_channel,
            )
        )

    def create(self, event_id: str, data: dict) -> None:
        self.update(event_id, data)
