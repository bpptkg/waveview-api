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

    def get_amax(self, data: np.ndarray) -> float:
        """
        Get Amax (peak-to-peak/2) value from stream in m.
        """
        if len(data) == 0:
            return 0
        minval = np.min(data)
        maxval = np.max(data)
        amplitude = (maxval - minval) / 2
        if np.isnan(amplitude):
            return 0
        return amplitude

    def calc(
        self,
        time: datetime,
        duration: float,
        channel_id: str,
        organization_id: str,
        **options,
    ) -> SignalAmplitude:
        inventory = Inventory.objects.get(organization_id=organization_id)
        starttime = time
        endtime = starttime + timedelta(seconds=duration)
        use_outlier_filter = options.get("use_outlier_filter", False)

        def remove_response(st: Stream) -> Stream:
            return remove_instrument_response(inventory, st)

        try:
            channel = Channel.objects.get(id=channel_id)
            stream = self.datastream.get_waveform(channel.id, starttime, endtime)
            if len(stream) == 0:
                raise Exception("No matching data found.")
            stream = remove_response(stream)
            data = stream[0].data
            if use_outlier_filter:
                data = remove_outliers(data)
            amax = self.get_amax(data)
        except Exception as e:
            logger.error(f"Failed to calculate amplitude: {e}")
            amax = 0

        return SignalAmplitude(
            time=time,
            duration=duration,
            amplitude=amax * 1e6,  # Convert to µm.
            method=self.method,
            category=AmplitudeCategory.DURATION,
            unit=AmplitudeUnit.UM.label,
            channel_id=channel_id,
            stream_id=channel.stream_id,
            label=channel.stream_id,
        )
