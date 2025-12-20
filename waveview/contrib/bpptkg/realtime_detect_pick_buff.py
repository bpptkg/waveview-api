import numpy as np
from obspy.clients.seedlink.easyseedlink import EasySeedLinkClient
from obspy.core import UTCDateTime
from obspy.core.stream import Stream
from obspy.core.trace import Trace

class LteSteDetector:
    def __init__(
        self,
        network: str,
        station: str,
        channel: str = "HHZ",
        location: str = "00",
        instance_id: str = "",
        debug: bool = True,
        buffer_length_sec: int = 1800  # Menyimpan 30 menit data di RAM
    ) -> None:
        # --- Properti Konfigurasi ---
        self.net = network
        self.sta = station
        self.cha = channel
        self.loc = location
        self.instance_id = instance_id
        self.debug = debug
        self.buffer_length_sec = buffer_length_sec

        # --- Properti Status Internal ---
        self.i = 1
        self.onset = 0
        self.t_on = None
        self.t_off = None
        
        # Inisialisasi Stream buffer di memori (Pengganti file MSEED)
        self.stream_buffer = Stream()

    def _log(self, message: str) -> None:
        """Helper method for logging messages."""
        if self.debug:
            print(f"[{UTCDateTime.now().strftime('%H:%M:%S')}] {message}")

    # ----------------------------------------------------------------------
    # --- Metode Deteksi dan Picking ---
    # ----------------------------------------------------------------------

    def _detect_onset(self, trace1: Trace, trace2: Trace) -> UTCDateTime | None:
        """Deteksi onset berdasarkan lonjakan standar deviasi."""
        t_trace2 = trace2.stats.starttime
        std1 = np.std(trace1.data)
        std2 = np.std(trace2.data)
        rstd = std2 / (std1 + 1e-6) # Proteksi pembagian nol

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
        rstd = std2 / (std1 + 1e-6)

        if std2 < 400 and rstd > 1:
            t_off = t_trace2
            self._log(f"OFFSET DETECTED: std2={std2:.2f}, rstd={rstd:.2f}, t_off={t_off}")
            return t_off
        return None

    def _lte_ste(self, st: Trace, snlte: int, snste: int) -> list:
        """Kalkulasi LTE/STE ratio untuk phase picking."""
        tm = st.stats.starttime
        srate = st.stats.sampling_rate
        adata = st.data

        nlte = int(snlte * srate)
        nste = int(snste * srate)

        lte_kernel = np.ones(nlte) / nlte
        ste_kernel = np.ones(nste) / nste

        numlte = np.convolve(adata**2, lte_kernel, mode="same")
        numste = np.convolve(adata**2, ste_kernel, mode="full")

        start_idx, end_idx = 200, 1500
        lteList = numlte[start_idx:end_idx]
        steList = numste[start_idx:end_idx]

        chrFunc = np.divide(
            lteList, steList, out=np.zeros_like(lteList, dtype=float), where=steList != 0
        )

        if chrFunc.size > 0:
            idx_onset = np.argmax(chrFunc)
            onset = tm + (start_idx / srate) + (idx_onset / srate)
        else:
            onset = tm + 5

        return [chrFunc, lteList, steList, onset]

    # ----------------------------------------------------------------------
    # --- Metode Utama ---
    # ----------------------------------------------------------------------

    def on_data(self, trace: Trace) -> None:
        """Callback utama saat data baru tiba."""
        
        # 1. Akumulasi data ke buffer memori
        self.stream_buffer.append(trace)
        self.stream_buffer.merge(method=1, fill_value="latest")

        # 2. Trimming berkala agar RAM tidak penuh
        latest_time = self.stream_buffer[-1].stats.endtime
        self.stream_buffer.trim(starttime=latest_time - self.buffer_length_sec)

        # 3. Logika Deteksi (Setelah buffer stabil > 10 paket)
        if self.i > 10 and trace.stats.station == self.sta:
            self._run_detection(trace)

        self.i += 1

    def _run_detection(self, trace: Trace):
        """Internal detection runner."""
        t_now = trace.stats.starttime
        
        # Ambil data referensi (2 detik sebelum data sekarang) dari buffer
        st_ref = self.stream_buffer.select(station=self.sta, channel=self.cha)
        
        if len(st_ref) > 0:
            # slice() digunakan agar tidak memotong buffer utama
            trace1_raw = st_ref[0].slice(t_now - 2, t_now - 0.01)
            
            if len(trace1_raw.data) > 0:
                # Pre-processing
                tr1 = trace1_raw.copy().detrend().taper(0.01).filter("bandpass", freqmin=3, freqmax=15)
                tr2 = trace.copy().detrend().taper(0.01).filter("bandpass", freqmin=3, freqmax=15)

                if self.onset == 0:
                    t_on_new = self._detect_onset(tr1, tr2)
                    if t_on_new:
                        self.onset = 1
                        self.t_on = t_on_new
                else:
                    t_off_new = self._detect_offset(tr1, tr2)
                    if t_off_new:
                        duration = t_off_new - self.t_on
                        if duration > 10:
                            self._process_event(duration)
                        
                        self.onset, self.t_on = 0, None

    def _process_event(self, duration: float):
        """Metode picking saat event terkonfirmasi."""
        self._log(f"\n--- EVENT CONFIRMED (Duration: {duration:.2f}s) ---")
        
        for tr in self.stream_buffer:
            # Picking window: 10s sebelum hingga 5s setelah onset
            trimmed = tr.slice(self.t_on - 10, self.t_on + 5)
            
            if len(trimmed.data) >= 1500:
                trimmed.detrend().taper(0.01).filter("bandpass", freqmin=3, freqmax=15)
                pick_res = self._lte_ste(trimmed, 5, 1)
                t_pick = pick_res[3]
                self._log(f"PICK for {tr.stats.station}: {t_pick} ({t_pick - self.t_on:.2f}s after onset)")
            else:
                self._log(f"PICK for {tr.stats.station}: Insufficient buffer data")
        
        self._log("--- END EVENT PROCESSING ---\n")

class MySeedLinkClient(EasySeedLinkClient):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.detector = LteSteDetector(network="VG", station="MELAB", debug=True)

    def on_data(self, trace: Trace) -> None:
        self.detector.on_data(trace)

if __name__ == "__main__":
    client_addr = "192.168.0.25:18000"
    client = MySeedLinkClient(client_addr)

    try:
        stations = ["MELAB", "MEPET", "MEDEL", "MEGRA", "MEPSL", "MESEL", "MEGEM", "MEPAC"]
        for sta in stations:
            client.select_stream("VG", sta, "HHZ")

        print(f"Starting memory-buffered client. Tracking {len(stations)} stations.")
        client.run()
    except KeyboardInterrupt:
        print("\nStopped by user.")