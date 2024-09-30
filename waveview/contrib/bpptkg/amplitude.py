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

    def calc(
        self, time: datetime, duration: float, stream_id: str, organization_id: str
    ) -> SignalAmplitude:
        inventory = Inventory.objects.get(organization_id=organization_id)
        starttime = time
        endtime = starttime + timedelta(seconds=duration)

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
            channel = Channel.objects.get_by_stream_id(stream_id)
            stream = self.datastream.get_waveform(channel.id, starttime, endtime)
            stream = remove_response(stream)
            amax = self.get_amax(stream)
            if amax is None:
                amax = 0
        except Exception as e:
            logger.error(f"Failed to remove response: {e}")
            amax = 0

        return SignalAmplitude(
            time=time,
            duration=duration,
            amplitude=amax * 1e6,  # Convert to µm.
            method=self.method,
            category=AmplitudeCategory.DURATION,
            unit=AmplitudeUnit.UM.label,
            stream_id=stream_id,
        )
