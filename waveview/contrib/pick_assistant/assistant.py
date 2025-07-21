import random
from datetime import timedelta

import numpy as np
from obspy import Stream, UTCDateTime

from waveview.contrib.pick_assistant.types import (
    PickAssistantInput,
    PickAssistantOutput,
)
from waveview.contrib.pick_assistant.waveform import (
    DummyWaveformResolver,
    WaveformResolver,
)


def random_duration() -> float:
    return random.uniform(10.0, 30.0)


class BaseDurationEstimator:
    def get_duration(self, start: UTCDateTime, st: Stream) -> float:
        raise NotImplementedError("Subclasses must implement get_duration method.")


class RandomDurationEstimator(BaseDurationEstimator):
    def get_duration(self, start: UTCDateTime, st: Stream) -> float:
        return random_duration()


class DefaultDurationEstimator(BaseDurationEstimator):
    def get_duration(self, start: UTCDateTime, st: Stream) -> float:
        T_ONSET = start
        T_MAX_BUFFER = 60.0
        SDV_WINDOW = 3.0
        PRE_NOISE = SDV_WINDOW
        POST_NOISE = 240.0 - PRE_NOISE
        THRESHOLD = 1.3

        st.trim((T_ONSET - PRE_NOISE), (T_ONSET + POST_NOISE))
        st.detrend(type="demean")
        st.filter("bandpass", freqmin=0.5, freqmax=15.0, corners=4, zerophase=True)

        df_1 = st[0].stats.sampling_rate
        t_start_1 = st[0].stats.starttime
        data_in = st.traces[0].data
        N_data = len(data_in)
        t_in = np.linspace(0, (N_data - 1) / df_1, num=N_data)
        t_onset_rel = abs(t_in - (T_ONSET - t_start_1))
        id_onset = np.where(t_onset_rel <= (1 / df_1))[0]
        idx_onset = id_onset[0].item()

        t_end_rel = abs(t_in - (T_MAX_BUFFER + SDV_WINDOW))
        id_end_candidate = np.where(t_end_rel <= (1 / df_1))[0]
        idx_end_candidate = id_end_candidate[0].item()
        data_candidate = data_in[0:idx_end_candidate]

        idx_max_abs = np.argmax(abs(data_candidate))

        sdv_lst = []
        idx_stop = []
        idx_start_sdv = 0

        for _ in t_in:
            idx_analys = np.arange(
                idx_start_sdv, idx_start_sdv + 1 + (SDV_WINDOW * df_1), dtype=int
            )
            data_analys = data_in[idx_analys]
            sdv_analys = np.std(data_analys)
            sdv_lst.append(sdv_analys)

            if idx_analys[-1] == N_data - 1:
                idx_stop.append(idx_analys[0])
                break
            if (
                sdv_lst[-1].item() <= (THRESHOLD * sdv_lst[0].item())
                and idx_analys[0] > idx_max_abs
            ):
                idx_stop.append(idx_analys[0])
                break
            idx_start_sdv = idx_start_sdv + 1

        idx_stop_array = np.array(idx_stop)
        dur = t_in[idx_stop_array[0]] - t_in[idx_onset]
        return dur


class PickAssistant:
    def __init__(self, simulate: bool = False) -> None:
        if simulate:
            self.waveform_resolver = DummyWaveformResolver()
            self.duration_resolver = RandomDurationEstimator()
        else:
            self.waveform_resolver = WaveformResolver()
            self.duration_resolver = DefaultDurationEstimator()

    def process(self, input_data: PickAssistantInput) -> PickAssistantOutput:
        start = input_data.t_onset - timedelta(seconds=input_data.pre_noise)
        end = start + timedelta(seconds=input_data.post_noise)

        waveform = self.waveform_resolver.get_waveform(start, end)
        t_onset = input_data.t_onset
        if waveform.resolved:
            duration = self.duration_resolver.get_duration(
                start=UTCDateTime(t_onset.timestamp()),
                st=waveform.stream,
            )
            output_data = PickAssistantOutput(
                start=t_onset,
                end=t_onset + timedelta(seconds=duration),
                duration=duration,
                stream_id=waveform.channel.stream_id,
                channel_id=str(waveform.channel.id),
            )
        else:
            output_data = PickAssistantOutput(
                start=t_onset,
                end=t_onset,
                duration=0,
                stream_id="",
                channel_id="",
            )
        return output_data
