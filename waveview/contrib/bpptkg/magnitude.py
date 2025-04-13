import logging
from dataclasses import dataclass
from datetime import timedelta

import numpy as np
from django.db import connection, transaction
from obspy import Stream

from waveview.contrib.bpptkg.outliers import remove_outliers
from waveview.contrib.bpptkg.response import remove_instrument_response
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


@dataclass
class AnalogChannel:
    stream_id: str
    label: str
    slope: float
    offset: float

    @classmethod
    def from_dict(cls, data: dict) -> "AnalogChannel":
        return cls(
            stream_id=data.get("stream_id"),
            label=data.get("label"),
            slope=data.get("slope", 1),
            offset=data.get("offset", 0),
        )


@dataclass
class MagnitudeObserverData:
    stream_ids: list[str] | str
    analogs: list[AnalogChannel]
    preferred_stream_id: str
    is_preferred: bool

    @classmethod
    def from_dict(cls, data: dict) -> "MagnitudeObserverData":
        stream_ids: str | None = data.get("stream_ids")
        if stream_ids != "all":
            stream_ids = stream_ids or []
        analogs = [AnalogChannel.from_dict(a) for a in data.get("analogs", [])]
        preferred_stream_id = data.get("preferred_stream_id", "")
        is_preferred = data.get("is_preferred", False)
        return cls(
            stream_ids=stream_ids,
            analogs=analogs,
            preferred_stream_id=preferred_stream_id,
            is_preferred=is_preferred,
        )


def calc_bpptkg_ml(amplitude: float) -> float:
    """
    Compute BPPTKG Richter local magnitude scale (ML) from amplitude.

    Note that amplitude is in meter, but in calculation, it uses micro-meter.
    Calibration function log10(A0) for BPPTKG seismic network is -1.4.

    Richter magnitude scale is computed using the following equation:

        ml = log10(amplitude) - log10(A0)

    where log10(A0) equal to -1.4 and ml is Richter local magnitude scale.
    """
    ampl = amplitude * 1e6  # Convert to micro-meter.
    return np.log10(ampl) + 1.4


@dataclass
class MagnitudeEstimatorData:
    event: Event
    data: MagnitudeObserverData


class MagnitudeEstimator:
    method = "bpptkg"

    def __init__(self) -> None:
        self.datastream = DataStream(connection)
        self.preferred_map: dict[str, bool] = {}

    def get_inventory(self, organization_id: str) -> Inventory:
        inventory = Inventory.objects.get(organization_id=organization_id)
        return inventory

    def get_amax(self, data: np.ndarray) -> float | None:
        """
        Get Amax (peak-to-peak/2) value from stream in m.
        """
        if len(data) == 0:
            return None

        minval = np.min(data)
        maxval = np.max(data)
        amplitude = (maxval - minval) / 2
        if np.isnan(amplitude):
            return None
        return amplitude

    def get_zeropk(self, data: np.ndarray) -> float | None:
        """
        Get zero-to-peak value from stream in m.
        """
        if len(data) == 0:
            return None

        amplitude = np.max(np.abs(data))
        if np.isnan(amplitude):
            return None
        return amplitude

    def remove_response(self, inventory: Inventory, st: Stream) -> Stream:
        return remove_instrument_response(inventory, st)

    @transaction.atomic
    def calc_magnitude(
        self, data: MagnitudeEstimatorData, use_outlier_filter: bool = False
    ) -> None:
        event = data.event
        organization_id = event.catalog.volcano.organization.id
        inventory = self.get_inventory(organization_id)

        options = data.data
        author_id = event.author.id
        is_preferred = options.is_preferred
        preferred_stream_id = options.preferred_stream_id
        analogs = options.analogs
        stream_ids = options.stream_ids

        logger.info(f"Calculating BPPTKG ML magnitude for event {event.id}...")

        if use_outlier_filter:
            buffer = 5  # Buffer in seconds.
            starttime = event.time - timedelta(seconds=buffer)
            endtime = event.time + timedelta(seconds=event.duration + buffer)
        else:
            buffer = 0
            starttime = event.time
            endtime = event.time + timedelta(seconds=event.duration)

        magnitude_type = "ML"

        magnitude, _ = Magnitude.objects.get_or_create(
            event=event,
            method=self.method,
            type=magnitude_type,
            defaults={
                "magnitude": None,
                "station_count": 0,
                "azimuthal_gap": 0,
                "evaluation_status": EvaluationStatus.PRELIMINARY,
                "author_id": author_id,
                "is_preferred": is_preferred,
            },
        )

        magnitude_values: list[float] = []
        stations: set[str] = set()
        amplitude_map: dict[str, Amplitude] = {}

        for channel in Channel.objects.all():
            st = self.datastream.get_waveform(channel.id, starttime, endtime)

            try:
                st = self.remove_response(inventory, st)
            except Exception as e:
                logger.error(
                    f"Failed to remove response for channel {channel.stream_id}: {e}"
                )
                continue

            if len(st) == 0:
                amax = None
                ml = None
            else:
                data = remove_outliers(st[0].data) if use_outlier_filter else st[0].data
                amax = self.get_amax(data)
                ml = calc_bpptkg_ml(amax)

            if channel.contains_stream_id(stream_ids) and ml is not None:
                magnitude_values.append(ml)
                stations.add(channel.station.code)

            uamax = (
                amax * 1e6 if amax is not None else None
            )  # Convert to µm if amax exists

            amplitude, _ = Amplitude.objects.update_or_create(
                event=event,
                waveform=channel,
                method=self.method,
                defaults={
                    "amplitude": uamax,
                    "type": "Amax",
                    "category": AmplitudeCategory.DURATION,
                    "time": event.time,
                    "begin": buffer,
                    "end": event.duration + buffer,
                    "snr": 0,
                    "unit": AmplitudeUnit.UM.label,
                    "evaluation_mode": EvaluationMode.AUTOMATIC,
                    "author_id": author_id,
                    "is_preferred": channel.matches_stream_id(preferred_stream_id),
                },
            )
            amplitude_map[str(channel.id)] = amplitude

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
                station_magnitude=station_magnitude,
                defaults={
                    "magnitude": magnitude,
                    "weight": 1,
                    "residual": 0,
                },
            )

        if magnitude_values:
            avg = np.mean(magnitude_values)
            if not np.isnan(avg):
                magnitude.magnitude = avg
                magnitude.station_count = len(stations)
                magnitude.save()

        for analog in analogs:
            network, station, __, channel = analog.stream_id.split(".")
            try:
                channel = Channel.objects.filter(
                    code=channel, station__code=station, station__network__code=network
                ).get()
            except Channel.DoesNotExist:
                logger.error(f"Channel {analog.stream_id} does not exist.")
                continue

            ampl = amplitude_map.get(str(channel.id))
            value = (
                analog.slope * ampl.amplitude + analog.offset
                if ampl and ampl.amplitude is not None
                else None
            )
            Amplitude.objects.update_or_create(
                event=event,
                waveform=channel,
                method="analog",
                defaults={
                    "amplitude": value,
                    "type": "Amax",
                    "category": AmplitudeCategory.DURATION,
                    "time": event.time,
                    "begin": buffer,
                    "end": event.duration + buffer,
                    "snr": 0,
                    "unit": AmplitudeUnit.MM.label,
                    "evaluation_mode": EvaluationMode.AUTOMATIC,
                    "author_id": author_id,
                    "is_preferred": False,
                    "label": analog.label,
                },
            )

        logger.info(f"BPPTKG ML magnitude calculation for event {event.id} is done.")


class MagnitudeObserver(EventObserver):
    """
    This observer calculates BPPTKG local magnitude (ML) for an event.
    """

    name = "bpptkg.magnitude"

    def update(
        self, event_id: str, data: dict, use_outlier_filter: bool = False
    ) -> None:
        event = Event.objects.get(id=event_id)
        estimator = MagnitudeEstimator()
        estimator.calc_magnitude(
            MagnitudeEstimatorData(
                event=event, data=MagnitudeObserverData.from_dict(data)
            ),
            use_outlier_filter=use_outlier_filter,
        )

    def create(
        self, event_id: str, data: dict, use_outlier_filter: bool = False
    ) -> None:
        self.update(event_id, data, use_outlier_filter=use_outlier_filter)
