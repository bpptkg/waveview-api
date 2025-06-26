import logging
from dataclasses import dataclass

import numpy as np
from django.db import connection, transaction

from waveview.contrib.bpptkg.amplitude import BPPTKGAmplitudeCalculator
from waveview.event.header import AmplitudeUnit, EvaluationMode, EvaluationStatus
from waveview.event.models import (
    Amplitude,
    Event,
    Magnitude,
    StationMagnitude,
    StationMagnitudeContribution,
)
from waveview.event.observers import EventObserver
from waveview.inventory.datastream import DataStream
from waveview.inventory.models import Channel

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


@dataclass
class MagnitudeEstimatorData:
    event: Event
    data: MagnitudeObserverData


class BPPTKGMagnitudeEstimator:
    method = "bpptkg"

    def __init__(self) -> None:
        self.datastream = DataStream(connection)
        self.preferred_map: dict[str, bool] = {}

    def calc_bpptkg_ml(self, amplitude: float) -> float | None:
        """
        Compute BPPTKG Richter local magnitude scale (ML) from amplitude.

        Note that amplitude is in meter, but in calculation, it uses micro-meter.
        Calibration function log10(A0) for BPPTKG seismic network is -1.4.

        Richter magnitude scale is computed using the following equation:

            ml = log10(amplitude) - log10(A0)

        where log10(A0) equal to -1.4 and ml is Richter local magnitude scale.
        """
        try:
            ml = np.log10(amplitude) + 1.4
            if not np.isfinite(ml):  # Check for -inf, inf, or NaN
                return None
            return ml
        except (ValueError, OverflowError):
            return None

    @transaction.atomic
    def calc(
        self, data: MagnitudeEstimatorData, use_outlier_filter: bool = False
    ) -> None:
        event = data.event
        logger.info(f"Calculating BPPTKG ML magnitude for event {event.id}...")

        organization_id = event.catalog.volcano.organization.id
        options = data.data
        author_id = event.author.id
        is_preferred = options.is_preferred
        preferred_stream_id = options.preferred_stream_id
        analogs = options.analogs
        stream_ids = options.stream_ids
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

        amplitude_calculator = BPPTKGAmplitudeCalculator()

        for channel in Channel.objects.filter(
            station__network__inventory__organization_id=organization_id
        ).all():
            logger.info(
                f"Processing channel {channel.stream_id} for event {event.id}..."
            )

            channel_id = channel.id
            sa = amplitude_calculator.calc(
                event.time,
                event.duration,
                channel_id,
                organization_id,
                use_outlier_filter=use_outlier_filter,
            )

            amax = sa.amplitude
            ml = self.calc_bpptkg_ml(amax) if amax is not None else None

            if channel.contains_stream_id(stream_ids) and ml is not None:
                magnitude_values.append(ml)
                stations.add(channel.station.code)

            amplitude, _ = Amplitude.objects.update_or_create(
                event=event,
                waveform=channel,
                method=self.method,
                defaults={
                    "amplitude": amax,
                    "type": "Amax",
                    "category": sa.category,
                    "time": sa.time,
                    "begin": sa.begin,
                    "end": sa.end,
                    "snr": 0,
                    "unit": sa.unit,
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
            if not np.isnan(avg) or np.isfinite(avg):
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
                    "category": ampl.category,
                    "time": ampl.time,
                    "begin": ampl.begin,
                    "end": ampl.end,
                    "snr": 0,
                    "unit": AmplitudeUnit.MM.label,
                    "evaluation_mode": EvaluationMode.AUTOMATIC,
                    "author_id": author_id,
                    "is_preferred": False,
                    "label": analog.label,
                },
            )

        logger.info(f"BPPTKG ML magnitude for event {event.id} calculated.")


class MagnitudeObserver(EventObserver):
    """
    This observer calculates BPPTKG local magnitude (ML) for an event.
    """

    name = "bpptkg.magnitude"

    def update(
        self, event_id: str, data: dict, use_outlier_filter: bool = False
    ) -> None:
        event = Event.objects.get(id=event_id)
        estimator = BPPTKGMagnitudeEstimator()
        estimator.calc(
            MagnitudeEstimatorData(
                event=event, data=MagnitudeObserverData.from_dict(data)
            ),
            use_outlier_filter=use_outlier_filter,
        )

    def create(
        self, event_id: str, data: dict, use_outlier_filter: bool = False
    ) -> None:
        self.update(event_id, data, use_outlier_filter=use_outlier_filter)
