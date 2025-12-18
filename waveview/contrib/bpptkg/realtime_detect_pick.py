import os
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime

import numpy as np
from obspy.clients.seedlink.easyseedlink import EasySeedLinkClient
from obspy.core import UTCDateTime
from obspy.core.stream import Stream, read
from obspy.core.trace import Trace


@dataclass
class PickResult:
    stream_id: str
    t_pick: UTCDateTime
    offset: float


@dataclass
class DetectionResult:
    t_on: UTCDateTime
    t_off: UTCDateTime
    picks: list[PickResult]

    def to_dict(self) -> dict:
        return {
            "t_on": self.t_on.isoformat(),
            "t_off": self.t_off.isoformat(),
            "picks": [
                {
                    "stream_id": pick.stream_id,
                    "t_pick": pick.t_pick.isoformat(),
                    "offset": pick.offset,
                }
                for pick in self.picks
            ],
        }

    def get_sof(self) -> str:
        index = [pick.offset for pick in self.picks].index(
            min([pick.offset for pick in self.picks])
        )
        try:
            return self.picks[index].stream_id.split(".")[1]
        except IndexError:
            return ""

    def get_sof_pick(self) -> PickResult | None:
        index = [pick.offset for pick in self.picks].index(
            min([pick.offset for pick in self.picks])
        )
        try:
            return self.picks[index]
        except IndexError:
            return None

    def get_duration(self) -> float:
        return self.t_off - self.t_on

    @classmethod
    def from_dict(cls, data: dict) -> "DetectionResult":
        picks = [
            PickResult(
                stream_id=pick_data["stream_id"],
                t_pick=UTCDateTime(pick_data["t_pick"]),
                offset=pick_data["offset"],
            )
            for pick_data in data.get("picks", [])
        ]
        return cls(
            t_on=UTCDateTime(data["t_on"]),
            t_off=UTCDateTime(data["t_off"]),
            picks=picks,
        )


class LteSteDetector:
    def __init__(
        self,
        network: str,
        station: str,
        channel: str = "HHZ",
        location: str = "00",
        instance_id: str = "",
        debug: bool = True,
    ) -> None:
        # --- Properti Konfigurasi ---
        self.net = network
        self.sta = station  # Stasiun utama untuk deteksi
        self.cha = channel
        self.loc = location
        self.instance_id = instance_id
        self.debug = debug

        # --- Properti Status Internal (Menggantikan Global Variables) ---
        self.i = 1
        self.day = UTCDateTime.now().strftime("%d")
        self.onset = 0
        self.t_on = None
        self.t_off = None
        temp_dir = tempfile.gettempdir()
        if instance_id:
            self.fn = os.path.join(temp_dir, f"D.{self.day}_{instance_id}.mseed")
        else:
            self.fn = os.path.join(temp_dir, f"D.{self.day}.mseed")

        # Inisialisasi Stream data
        self._initialize_stream()

    def _log(self, message: str) -> None:
        """Helper method for logging messages."""
        if self.debug:
            print(f"{datetime.now(UTC)} {message}")

    def _initialize_stream(self):
        """Memuat data hari ini jika ada, atau membuat Stream baru."""
        if os.path.isfile(self.fn):
            self._log(f"Found {self.fn}, reading...")
            self.traces = read(self.fn)
            self._log("Done.")
        else:
            self._log("No data found. Creating new blank Stream...")
            self.traces = Stream()

    # ----------------------------------------------------------------------
    # --- Metode Deteksi dan Picking ---
    # ----------------------------------------------------------------------

    def _detect_onset(self, trace1: Trace, trace2: Trace) -> UTCDateTime | None:
        """Deteksi onset berdasarkan lonjakan standar deviasi."""
        t_trace2 = trace2.stats.starttime
        std1 = np.std(trace1.data)
        std2 = np.std(trace2.data)
        rstd = std2 / std1

        # Kriteria Onset
        if std2 > 500 and rstd > 1.3:
            t_on = t_trace2
            self._log(f"ONSET DETECTED: std2={std2:.2f}, rstd={rstd:.2f}, t_on={t_on}")
            return t_on
        return None

    def _detect_offset(self, trace1: Trace, trace2: Trace) -> UTCDateTime | None:
        """Deteksi offset berdasarkan penurunan standar deviasi."""
        t_trace2 = trace2.stats.starttime
        std1 = np.std(trace1.data)
        std2 = np.std(trace2.data)
        rstd = std2 / std1

        # Kriteria Offset
        if std2 < 400 and rstd > 1:
            t_off = t_trace2
            self._log(
                f"OFFSET DETECTED: std2={std2:.2f}, rstd={rstd:.2f}, t_off={t_off}"
            )
            return t_off
        return None

    def _lte_ste(self, st: Trace, snlte: int, snste: int, fgr: int = 0) -> list:
        """
        Calculates the LTE/STE ratio for phase picking.
        snlte: LTE window in seconds, snste: STE window in seconds.
        """
        tm = st.stats.starttime
        srate = st.stats.sampling_rate
        adata = st.data

        nlte = int(snlte * srate)
        nste = int(snste * srate)

        # Hitung Kernel
        lte_kernel = np.ones(nlte) / nlte
        ste_kernel = np.ones(nste) / nste

        # Hitung Konvolusi (Moving Average of Power)
        numlte = np.convolve(adata**2, lte_kernel, mode="same")
        numste = np.convolve(adata**2, ste_kernel, mode="full")

        # Ambil data yang relevan (misalnya 200 hingga 1500 sampel)
        start_idx = 200
        end_idx = 1500

        # Pastikan indeks berada dalam batas yang valid
        lteList = numlte[start_idx:end_idx]
        steList = numste[start_idx:end_idx]

        # Hitung Characteristic Function (LTE/STE Ratio)
        # Tambahkan epsilon untuk menghindari pembagian dengan nol
        chrFunc = np.divide(
            lteList,
            steList,
            out=np.zeros_like(lteList, dtype=float),
            where=steList != 0,
        )

        # Temukan indeks maksimum untuk onset pick
        if chrFunc.size > 0:
            idx_onset = np.argmax(chrFunc)
            # Offset 200 sampel + 2 detik buffer + Indeks terpilih
            onset_offset = start_idx / srate
            onset = tm + onset_offset + idx_onset / srate
        else:
            # Fallback jika chrFunc kosong
            onset = tm + 5

        # Optional Plotting (fgr == 1) dihilangkan agar tidak mengganggu operasional real-time.

        return [chrFunc, lteList, steList, onset]

    # ----------------------------------------------------------------------
    # --- Metode Utama: Dipanggil saat data baru diterima ---
    # ----------------------------------------------------------------------

    def on_event_confirmed(self, result: DetectionResult) -> None:
        pass

    def on_data(self, trace: Trace) -> None:
        """Metode yang dipanggil oleh EasySeedLinkClient saat data baru tiba."""

        # 1. Pengecekan Hari dan Reset (Logika Rotasi File Harian)
        current_day = UTCDateTime.now().strftime("%d")
        if self.day != current_day:
            self._log(f"New day detected: {current_day}. Resetting client state.")
            self.day = current_day
            temp_dir = tempfile.gettempdir()
            if self.instance_id:
                self.fn = os.path.join(
                    temp_dir, f"D.{self.day}_{self.instance_id}.mseed"
                )
            else:
                self.fn = os.path.join(temp_dir, f"D.{self.day}.mseed")
            self.i = 1
            self.traces = Stream()  # Memulai Stream baru untuk hari baru
            self.onset = 0
            self.t_on = None
            self.t_off = None
            # Pastikan trace pertama hanya ditambahkan, tidak digabungkan
            self.traces.append(trace)
            self.i += 1
            return

        # 2. Akumulasi dan Penyimpanan Data
        if self.i == 1:
            # Trace pertama, inisialisasi traces dengan trace ini
            self.traces.append(trace)
        else:
            # Gabungkan trace baru dan simpan
            self.traces.append(trace)
            # Menggunakan fill_value="latest" untuk merge
            self.traces.merge(fill_value="latest")
            self.traces.write(self.fn, format="MSEED")

        # self._log(f"Trace {self.i} received: {trace.id}")

        # 3. Logika Deteksi (Hanya pada stasiun utama dan setelah 10 paket)
        if self.i > 10 and trace.stats.station == self.sta:

            # Persiapan trace saat ini (trace2)
            trace2 = trace.copy()
            trace2.detrend().taper(0.01).filter("bandpass", freqmin=3, freqmax=15)
            df = trace2.stats.starttime

            # Persiapan trace sebelumnya (trace1) dari Stream yang terakumulasi
            # Kita ambil data 2 detik SEBELUM waktu mulai trace2
            trace1 = self.traces.copy().select(station=self.sta, channel=self.cha)
            if trace1:
                trace1 = trace1[0].trim(df - 2, df - 0.01)
                trace1.detrend().taper(0.01).filter("bandpass", freqmin=3, freqmax=15)
            else:
                # Jika stream kosong atau data sebelumnya tidak cukup, skip deteksi
                self.i += 1
                return

            if self.onset == 0:
                # Coba deteksi ONSET
                t_on_new = self._detect_onset(trace1, trace2)
                if t_on_new is not None:
                    self.onset = 1
                    self.t_on = t_on_new

            else:  # self.onset == 1 (Event sedang berlangsung)
                # Coba deteksi OFFSET
                t_off_new = self._detect_offset(trace1, trace2)

                if t_off_new is not None:
                    self.t_off = t_off_new
                    duration = self.t_off - self.t_on

                    if duration > 10:
                        # Event Terkonfirmasi > 10 detik. Lakukan picking pada SEMUA stasiun.
                        self._log(
                            f"--- EVENT CONFIRMED (Duration: {duration:.2f}s) ---"
                        )

                        picks: list[PickResult] = []

                        # Loop melalui SEMUA trace di Stream yang terakumulasi
                        for trace3 in self.traces.copy():
                            sta3 = trace3.stats.station

                            # Trim data untuk picking (10s sebelum onset hingga 5s setelah onset)
                            trimmed_trace = trace3.trim(self.t_on - 10, self.t_on + 5)

                            if (
                                trimmed_trace.stats.npts == 1501
                            ):  # Check jika trim berhasil (15s @ 100Hz + 1)
                                trimmed_trace.detrend().taper(0.01).filter(
                                    "bandpass", freqmin=3, freqmax=15
                                )
                                # Lakukan LTE/STE pick
                                pick = self._lte_ste(trimmed_trace, 5, 1, 0)
                                t_pick = pick[3]
                                self._log(
                                    f"PICK for {sta3}: {t_pick} ({t_pick - self.t_on:.2f}s after onset)"
                                )
                                picks.append(
                                    PickResult(
                                        stream_id=f"{self.net}.{sta3}.{self.loc}.{self.cha}",
                                        t_pick=t_pick,
                                        offset=t_pick - self.t_on,
                                    )
                                )
                            else:
                                self._log(
                                    f"PICK for {sta3}: Incomplete trace ({trimmed_trace.stats.npts} points)"
                                )

                        event_result = DetectionResult(
                            t_on=self.t_on, t_off=self.t_off, picks=picks
                        )
                        self.on_event_confirmed(event_result)

                        self._log("--- END EVENT PROCESSING ---")

                    # Reset status event, terlepas dari durasi
                    self.onset = 0
                    self.t_on = None
                    self.t_off = None

        self.i += 1


class DetectionCallback:
    """
    Subclass untuk menerima callback dari metode on_data dan menyimpan hasil deteksi.
    """

    def __init__(self):
        self.t_on = None
        self.t_off = None
        self.t_pick = None

    def update(self, t_on=None, t_off=None, t_pick=None):
        """
        Metode untuk memperbarui nilai t_on, t_off, dan t_pick.
        """
        if t_on is not None:
            self.t_on = t_on
        if t_off is not None:
            self.t_off = t_off
        if t_pick is not None:
            self.t_pick = t_pick

    def __str__(self):
        return f"DetectionCallback(t_on={self.t_on}, t_off={self.t_off}, t_pick={self.t_pick})"


class MySeedLinkClient(EasySeedLinkClient):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.detector = LteSteDetector(
            network="VG",
            station="MELAB",
            channel="HHZ",
            debug=True,
        )
        self.callback = DetectionCallback()

    def on_data(self, trace: Trace) -> None:
        self.detector.on_data(trace)

        if self.detector.t_on is not None:
            self.callback.update(t_on=self.detector.t_on)
        if self.detector.t_off is not None:
            self.callback.update(t_off=self.detector.t_off)

        # Cetak hasil callback untuk debugging
        if self.detector.t_off is not None:
            print(self.callback)


if __name__ == "__main__":
    """Use this script to test the SeedLink client and detection logic."""

    # Konfigurasi
    client_addr = "192.168.0.25:18000"

    # Inisialisasi Klien
    client = MySeedLinkClient(client_addr)

    # Dapatkan informasi Stream
    streams_xml = client.get_info("STREAMS")
    print(streams_xml)

    # Pilih Stream yang ingin dimonitor
    print("Selecting streams...")
    try:
        # Panggil select_stream pada instance client

        client.select_stream("VG", "MELAB", "HHZ")
        client.select_stream("VG", "MEPET", "HHZ")
        client.select_stream("VG", "MEDEL", "HHZ")
        client.select_stream("VG", "MEGRA", "HHZ")
        client.select_stream("VG", "MEPSL", "HHZ")
        client.select_stream("VG", "MESEL", "HHZ")
        client.select_stream("VG", "MEGEM", "HHZ")
        client.select_stream("VG", "MEPAC", "HHZ")

        print("Starting client run. Press Ctrl+C to stop.")
        client.run()

    except KeyboardInterrupt:
        print("\nClient stopped by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
