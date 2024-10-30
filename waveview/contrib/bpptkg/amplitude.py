import logging
from datetime import datetime, timedelta

import numpy as np
from obspy import Stream, read_inventory
from obspy.core.inventory import Inventory as ObspyInventory

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
            return None
        return amplitude

    def remove_outliers(self, data: np.ndarray) -> np.ndarray:
        if len(data) == 0:
            return data
        q1 = np.quantile(data, 0.1)
        q3 = np.quantile(data, 0.9)
        iqr = q3 - q1
        threshold = 1.5 * iqr

        lower_bound = q1 - threshold
        upper_bound = q3 + threshold
        data[(data <= lower_bound) | (data >= upper_bound)] = 0
        return data

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

        try:
            channel = Channel.objects.get(id=channel_id)
            stream = self.datastream.get_waveform(channel.id, starttime, endtime)
            stream = remove_response(stream)
            if len(stream) == 0:
                raise Exception("No matching data found.")
            data = stream[0].data
            if use_outlier_filter:
                data = self.remove_outliers(data)

            amax = self.get_amax(data)
            if amax is None:
                raise Exception("Amax is none.")
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
