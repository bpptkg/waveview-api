import logging
from datetime import datetime, timedelta

import numpy as np
from obspy import Stream

from waveview.contrib.bpptkg.outliers import remove_outliers
from waveview.contrib.bpptkg.response import remove_instrument_response
from waveview.event.amplitude import AmplitudeCalculator, SignalAmplitude
from waveview.event.header import AmplitudeCategory, AmplitudeUnit
from waveview.inventory.models import Channel, Inventory

logger = logging.getLogger(__name__)


class BPPTKGAmplitudeCalculator(AmplitudeCalculator):
    method = "bpptkg"

    def get_amax(self, data: np.ndarray) -> float | None:
        """
        Get Amax (peak-to-peak/2) value from stream in m.
        """
        if len(data) == 0:
            return None
        minval = np.nanmin(data)
        maxval = np.nanmax(data)
        amplitude = (maxval - minval) / 2
        if np.isnan(amplitude):
            return None
        return amplitude

    def calc(
        self,
        time: datetime,
        duration: float,
        channel_id: str,
        organization_id: str,
        use_outlier_filter: bool = False,
    ) -> SignalAmplitude:
        inventory = Inventory.objects.get(organization_id=organization_id)
        if use_outlier_filter:
            buffer = 5  # Buffer in seconds.
            starttime = time - timedelta(seconds=buffer)
            endtime = time + timedelta(seconds=duration + buffer)
        else:
            buffer = 0
            starttime = time
            endtime = time + timedelta(seconds=duration)

        def remove_response(st: Stream) -> Stream:
            return remove_instrument_response(inventory, st)

        try:
            channel = Channel.objects.get(id=channel_id)
            stream = self.datastream.get_waveform(channel.id, starttime, endtime)
            if len(stream) == 0:
                raise Exception(
                    f"No matching data found for channel {channel.stream_id}."
                )
            stream = remove_response(stream)
            data = stream[0].data
            if use_outlier_filter:
                data = remove_outliers(data)
            amax = self.get_amax(data)
        except Exception as e:
            logger.error(f"Failed to calculate amplitude: {e}")
            amax = None

        if amax is not None:
            uamax = amax * 1e6  # Convert to µm.
        else:
            uamax = None

        return SignalAmplitude(
            time=time,
            duration=duration,
            amplitude=uamax,
            method=self.method,
            category=AmplitudeCategory.DURATION,
            unit=AmplitudeUnit.UM.label,
            channel_id=channel_id,
            stream_id=channel.stream_id,
            label=channel.stream_id,
            begin=buffer,
            end=duration + buffer,
        )
