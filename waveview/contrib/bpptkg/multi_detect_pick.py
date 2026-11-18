"""
Detektor multi-stasiun dengan voting (mis. 2 dari 3 stasiun).

Subclass dari LteSteDetector (realtime_detect_pick.py). Buffer, rotasi harian,
picking LTE/STE dan on_event_confirmed tetap memakai kode asli; yang diganti
hanya cara menentukan onset/offset event.

Tiap stasiun voting punya kriteria relatif sendiri (sama dengan
relative_detect_pick.py):
  noise  = median std dari N paket terakhir saat stasiun itu tidak terpicu
  TERPICU : std2 > k_on  * noise
  LEPAS   : std2 < k_off * noise selama off_n paket berturut-turut
            (atau dipaksa setelah max_dur detik)

Event jaringan:
  BUKA  : >= min_sta stasiun sedang terpicu dan onset-nya saling berjarak
          <= coinc_win detik. t_on event = onset paling awal di kelompok itu.
  TUTUP : jumlah stasiun yang masih terpicu (dan bukan sisa event lama) turun
          di bawah close_min_sta (default = min_sta; isi 1 agar event baru
          ditutup setelah stasiun terakhir lepas). t_off event = waktu lepas
          stasiun tersebut.
  Event dikonfirmasi (picking di semua stasiun) jika durasi > min_event_dur.

Pemisahan event / "onset ulang" (split=True):
  Jika di tengah event amplitudo melonjak di >= split_min_sta stasiun voting
  dalam selang split_win detik, event lama ditutup di titik itu (ditandai
  "pendahulu") dan event baru dibuka. Lonjakan satu stasiun = rasio paket
  terhadap noise >= split_rmin DAN >= J kali median split_n paket sebelumnya:
    tingkat 1: J = split_j1 (3x), berlaku sejak split_age1 (10 s) setelah onset
    tingkat 2: J = split_j2 (2x), berlaku sejak split_age2 (30 s) setelah onset
  Penyaring petir untuk event hasil pemisahan memakai onset event asal sebagai
  acuan, supaya stasiun pantau yang sudah terpicu oleh bagian pendahulu tidak
  dianggap "tiba lebih awal".

Penyaring petir (opsional, aktif jika monitor_stations diisi):
  Stasiun pantau (mis. MEGRA, MEGEM; letaknya jauh) dicatat waktu picunya
  tetapi TIDAK ikut voting. Untuk tiap event dihitung dt = waktu picu stasiun
  pantau - t_on event. Gempa vulkanik: stasiun jauh selalu belakangan dan
  selisihnya kecil. Suara guntur merambat ~0.34 km/s sehingga selisihnya besar
  dan bisa negatif. Event ditandai petir bila ada stasiun pantau yang
    - "awal"  : terpicu lebih dari lt_neg detik SEBELUM t_on dan masih terpicu
                menjelang t_on, atau
    - "lambat": baru terpicu lebih dari lt_pos detik SETELAH t_on. Aturan ini
                MATI secara bawaan (lt_pos=0): pada uji 12-13 Nov 2026 ia hanya
                menolak event katalog yang naik perlahan / punya sinyal pendahulu
                (4 salah tolak, 0 benar), sedangkan aturan "awal" menolak 2
                kejadian petir tanpa salah tolak.
  Keputusan diambil lt_post_win detik setelah t_on (event ditahan dulu).
  lightning_action="reject": event tidak dikonfirmasi, on_event_rejected()
  dipanggil. "flag": event tetap dikonfirmasi, hanya ditandai.
"""

from collections import deque

import numpy as np


class _StationState:
    def __init__(self, noise_n):
        self.hist = deque(maxlen=noise_n)
        self.noise = None
        self.on = False
        self.t_on = None
        self.n_reject = 0
        self.off_count = 0
        self.off_start = None
        self.intervals = deque(maxlen=50)  # [t_on, t_off] tiap kali terpicu
        self.ratios = None                 # rasio beberapa paket terakhir
        self.jump_t = None                 # waktu lonjakan terakhir dalam event


# ---------------------------------------------------------------------------
# Ketidakpastian picking
# ---------------------------------------------------------------------------
QUALITY_LIMITS = (0.1, 0.2, 0.5, 1.0)  # batas sigma (detik) untuk kelas 0..3; di atasnya kelas 4


def pick_quality(data, sr, i_pick, env_win=0.2, k_early=1.5, k_late=3.0,
                 sig_win=2.0, min_snr=2.0, limits=QUALITY_LIMITS):
    """Perkirakan ketidakpastian satu pick dari selubung amplitudo.

    data   : trace yang sudah difilter (mis. t_on-10 s s/d t_on+5 s)
    i_pick : indeks sampel pick

    Noise = median selubung sebelum pick (sampai 0.5 s sebelum pick, minimal 2 s data).
    Selubung = RMS bergerak env_win detik.
      - paling awal (early): titik terakhir sebelum pick dengan selubung
        <= k_early x noise (sinyal belum bisa dibedakan dari noise)
      - paling lambat (late): titik pertama mulai dari pick dengan selubung
        >= k_late x noise (sinyal sudah pasti ada)
    sigma = (late - early) / 2. SNR = RMS sig_win detik setelah pick / noise.

    Kelas kualitas 0..3 menurut batas sigma `limits`; kelas 4 bila sigma lebih
    besar, SNR < min_snr, atau sinyal tidak pernah mencapai k_late x noise.
    Return dict: early_s, late_s (relatif pick, detik), sigma_s, snr, quality.
    """
    data = np.asarray(data, dtype=float)
    n = len(data)
    i_pick = int(round(min(max(i_pick, 0), n - 1)))
    nw = max(1, int(round(env_win * sr)))
    env = np.sqrt(np.convolve(data ** 2, np.ones(nw) / nw, mode="same"))

    i_noise_end = i_pick - int(0.5 * sr)
    if i_noise_end < int(2 * sr):
        i_noise_end = int(2 * sr)
    # median selubung: tidak ikut naik bila jendela noise tercampur awal sinyal
    noise = float(np.median(env[:i_noise_end])) if i_noise_end > 0 else 0.0
    sig = data[i_pick:i_pick + int(sig_win * sr)]
    snr = float(np.sqrt(np.mean(sig ** 2)) / noise) if noise > 0 and len(sig) else float("nan")

    out = {"early_s": None, "late_s": None, "sigma_s": None, "snr": round(snr, 2), "quality": 4}
    # celah data: bagian yang diisi nilai tetap (merge fill_value="latest") menjadi ~0
    # setelah difilter, sehingga "noise" nyaris nol dan SNR tak masuk akal
    if noise <= 1e-6 * float(env.max() or 1.0):
        out["snr"] = float("nan")
        out["celah_data"] = True
        return out

    below = np.where(env[:i_pick + 1] <= k_early * noise)[0]
    i_early = int(below[-1]) if len(below) else 0
    above = np.where(env[i_pick:] >= k_late * noise)[0]
    if not len(above):
        return out
    i_late = i_pick + int(above[0])
    i_early = min(i_early, i_pick)

    sigma = (i_late - i_early) / sr / 2.0
    out.update(early_s=round((i_early - i_pick) / sr, 2), late_s=round((i_late - i_pick) / sr, 2),
               sigma_s=round(sigma, 2))
    q = next((k for k, lim in enumerate(limits) if sigma <= lim), 4)
    out["quality"] = q if snr >= min_snr else 4
    return out


def lte_ste_onset(data, sr, starttime, snlte=5, snste=1):
    """Algoritma picking LTE/STE yang sama dengan LteSteDetector._lte_ste.

    Disalin ke sini supaya tidak bergantung pada versi realtime_detect_pick.py
    (tanda tangan _lte_ste berbeda antara cabang autoeventpicker dan main).
    """
    adata = np.asarray(data, dtype=float)
    nlte, nste = int(snlte * sr), int(snste * sr)
    numlte = np.convolve(adata ** 2, np.ones(nlte) / nlte, mode="same")
    numste = np.convolve(adata ** 2, np.ones(nste) / nste, mode="full")
    start_idx, end_idx = 200, 1500
    lte, ste = numlte[start_idx:end_idx], numste[start_idx:end_idx]
    cf = np.divide(lte, ste, out=np.zeros_like(lte, dtype=float), where=ste != 0)
    if cf.size > 0:
        return starttime + start_idx / sr + int(np.argmax(cf)) / sr
    return starttime + 5


def make_multi_class(base, mod):
    """base: kelas LteSteDetector; mod: modul realtime_detect_pick (untuk PickResult dll)."""

    class MultiStationDetector(base):
        def __init__(
            self,
            *args,
            vote_stations=("MELAB", "MEPAC", "MEPSL"),
            min_sta: int = 2,
            close_min_sta: int | None = None,
            coinc_win: float = 10.0,
            k_on: float = 2.5,
            k_off: float = 2.25,
            k_upd: float = 1.5,
            noise_n: int = 30,
            min_noise_n: int = 10,
            off_n: int = 1,
            max_dur: float = 600.0,
            min_event_dur: float = 10.0,
            max_reject: int = 60,
            monitor_stations=(),
            lightning_action: str = "reject",
            lt_neg: float = 2.0,
            lt_pos: float = 0.0,
            lt_pre_win: float = 15.0,
            lt_post_win: float = 20.0,
            lt_min_flags: int = 1,
            on_n: int = 1,
            merge_gap: float = 0.0,
            merge_peak: float = 5.0,
            merge_eval: float = 15.0,
            min_peak2: float = 0.0,
            split: bool = True,
            split_j1: float = 3.0,
            split_age1: float = 10.0,
            split_j2: float = 2.0,
            split_age2: float = 30.0,
            split_n: int = 3,
            split_rmin: float = 5.0,
            split_win: float = 5.0,
            split_min_sta: int = 2,
            **kwargs,
        ):
            self.vote_stations = list(vote_stations)
            self.min_sta = min_sta
            # event ditutup saat stasiun aktif < close_min_sta (default = min_sta)
            self.close_min_sta = min_sta if close_min_sta is None else close_min_sta
            self.coinc_win = coinc_win
            self.k_on, self.k_off, self.k_upd = k_on, k_off, k_upd
            self.min_noise_n = min_noise_n
            self.off_n = off_n
            self.max_dur = max_dur
            self.min_event_dur = min_event_dur
            self.max_reject = max_reject
            self.st_state = {s: _StationState(noise_n) for s in self.vote_stations}
            self.monitor_stations = [m for m in monitor_stations if m not in self.vote_stations]
            self.mon_state = {m: _StationState(noise_n) for m in self.monitor_stations}
            self.lightning_action = lightning_action
            self.lt_neg, self.lt_pos = lt_neg, lt_pos
            self.lt_pre_win, self.lt_post_win = lt_pre_win, lt_post_win
            self.lt_min_flags = lt_min_flags
            self.pending = []
            # onset stasiun voting butuh on_n paket berturut-turut > k_on (1 = seperti semula)
            self.on_n = on_n
            # event yang ditutup ditahan merge_gap detik; bila event baru terbuka dalam
            # selang itu, keduanya digabung (0 = mati)
            self.merge_gap = merge_gap
            # event lanjutan hanya digabung bila lemah: puncaknya < merge_peak x noise
            # selama merge_eval detik pertama (sinyal yang berfluktuasi di sekitar ambang)
            self.merge_peak, self.merge_eval = merge_peak, merge_eval
            self.closing = None
            self.merge_cand = None
            self.net_peak = 0.0
            # event dibatalkan bila puncak stasiun voting tertinggi KEDUA < min_peak2 x noise
            self.min_peak2 = min_peak2
            self.net_st_peak = {}
            # akhir event jaringan terakhir; picu stasiun pantau sebelum ini milik event
            # sebelumnya dan tidak dipakai penyaring petir
            self.last_net_end = None
            self.net_prev_end = None
            self.split = split
            self.split_j1, self.split_age1 = split_j1, split_age1
            self.split_j2, self.split_age2 = split_j2, split_age2
            self.split_n, self.split_rmin = split_n, split_rmin
            self.split_win, self.split_min_sta = split_win, split_min_sta
            for x in self.st_state.values():
                x.ratios = deque(maxlen=split_n)
            self.net_lt_ref = None
            self.net_split_from = None
            self.last_event_info = {}
            self.net_on = False
            self.net_t_on = None
            self.net_stations = []
            self.last_event_stations = []
            super().__init__(*args, **kwargs)
            # Matikan deteksi satu-stasiun milik kelas asli; on_data asli hanya
            # dipakai untuk mengelola buffer dan rotasi harian.
            self.sta = "__multi__"

        # ------------------------------------------------------------------
        def _update_noise(self, s, std2):
            if s.noise is not None and len(s.hist) >= self.min_noise_n and std2 >= self.k_upd * s.noise:
                s.n_reject += 1
                if s.n_reject <= self.max_reject:
                    return
            s.n_reject = 0
            s.hist.append(std2)
            s.noise = float(np.median(s.hist))

        def _station_step(self, name, s, std2, t2):
            """Perbarui status satu stasiun. Return 'on', 'off', atau None."""
            if not s.on:
                if len(s.hist) < self.min_noise_n:
                    self._update_noise(s, std2)
                    return None
                if std2 > self.k_on * s.noise:
                    if getattr(s, "on_count", 0) == 0:
                        s.on_start = t2
                    s.on_count = getattr(s, "on_count", 0) + 1
                    # stasiun pantau tetap 1 paket, supaya penyaring petir tidak melemah
                    need = self.on_n if name in self.st_state else 1
                    if s.on_count < need:
                        return None
                    t_on = s.on_start
                    s.on_count = 0
                    s.on, s.t_on = True, t_on
                    s.intervals.append([t_on, None])
                    s.off_count, s.off_start = 0, None
                    self._log(f"[{name}] TERPICU std2={std2:.1f} noise={s.noise:.1f} "
                              f"rasio={std2 / s.noise:.2f} t={t_on}")
                    return "on"
                s.on_count = 0
                self._update_noise(s, std2)
                return None

            # stasiun sedang terpicu
            t_off = None
            if t2 - s.t_on > self.max_dur:
                t_off = t2
            elif std2 < self.k_off * s.noise:
                if s.off_count == 0:
                    s.off_start = t2
                s.off_count += 1
                if s.off_count >= self.off_n:
                    t_off = s.off_start
            else:
                s.off_count, s.off_start = 0, None
            if t_off is not None:
                s.on = False
                s.off_count, s.off_start = 0, None
                s.last_t_off = t_off
                if s.intervals:
                    s.intervals[-1][1] = t_off
                self._log(f"[{name}] LEPAS std2={std2:.1f} noise={s.noise:.1f} t={t_off}")
                return "off"
            return None

        def _coincident_group(self):
            trig = sorted(((s.t_on, n) for n, s in self.st_state.items() if s.on), key=lambda x: x[0])
            for i in range(len(trig)):
                grp = [n for t, n in trig if 0 <= t - trig[i][0] <= self.coinc_win]
                if len(grp) >= self.min_sta:
                    return trig[i][0], grp
            return None, []

        def _buffer(self):
            """Buffer data milik kelas dasar: `traces` (cabang autoeventpicker) atau
            `stream_buffer` (cabang main)."""
            buf = getattr(self, "stream_buffer", None)
            return buf if buf is not None else getattr(self, "traces", [])

        def _pick_all(self, t_on):
            picks = []
            for trace3 in self._buffer():
                sta3 = trace3.stats.station
                # slice: tidak mengubah buffer
                trimmed = trace3.slice(t_on - 10, t_on + 5).copy()
                if trimmed.stats.npts >= 1500:
                    trimmed.detrend().taper(0.01).filter("bandpass", freqmin=3, freqmax=15)
                    t_pick = lte_ste_onset(trimmed.data, trimmed.stats.sampling_rate,
                                           trimmed.stats.starttime)
                    sr = trimmed.stats.sampling_rate
                    q = pick_quality(trimmed.data, sr, (t_pick - trimmed.stats.starttime) * sr)
                    self._log(f"PICK for {sta3}: {t_pick} ({t_pick - t_on:.2f}s after onset) "
                              f"sigma={q['sigma_s']} snr={q['snr']} kualitas={q['quality']}")
                    pk = mod.PickResult(
                        stream_id=f"{self.net}.{sta3}.{self.loc}.{self.cha}",
                        t_pick=t_pick,
                        offset=t_pick - t_on,
                    )
                    # atribut tambahan; to_dict() / create_event tidak terpengaruh
                    pk.quality_info = q
                    picks.append(pk)
                else:
                    self._log(f"PICK for {sta3}: Incomplete trace ({trimmed.stats.npts} points)")
            return picks

        # ------------------------------------------------------------------
        def on_data(self, trace):
            super().on_data(trace)  # buffer + rotasi harian (tanpa deteksi)

            name = trace.stats.station
            is_mon = name in self.mon_state
            if (name not in self.st_state and not is_mon) or self.i <= 11:
                return

            tr2 = trace.copy()
            tr2.detrend().taper(0.01).filter("bandpass", freqmin=3, freqmax=15)
            std2 = float(np.std(tr2.data))
            t2 = tr2.stats.starttime
            s = self.mon_state[name] if is_mon else self.st_state[name]
            was_on = s.on
            change = self._station_step(name, s, std2, t2)

            hook = getattr(self, "_diag_multi", None)
            if hook:
                hook(name, t2, len(tr2.data), std2, s.noise, was_on, change)

            # selesaikan event yang ditahan menunggu stasiun pantau
            while self.pending and self.pending[0]["ready_at"] <= t2:
                self._finalize(self.pending.pop(0))
            # event yang ditahan untuk penggabungan: selesaikan bila waktunya habis
            if self.closing is not None and not self.net_on and t2 > self.closing["deadline"]:
                ev, self.closing = self.closing, None
                self._close(ev, t2)
            if is_mon:
                return

            # rasio terhadap noise dan besar lonjakan terhadap paket-paket sebelumnya
            ratio = std2 / s.noise if s.noise else None
            jump = None
            if ratio is not None:
                if len(s.ratios) == s.ratios.maxlen:
                    base = float(np.median(s.ratios))
                    jump = ratio / base if base > 0 else None
                s.ratios.append(ratio)

            if not self.net_on:
                if change == "on":
                    t_on, grp = self._coincident_group()
                    if grp:
                        self.net_on, self.net_t_on, self.net_stations = True, t_on, list(grp)
                        self.net_lt_ref, self.net_split_from = t_on, None
                        self.net_prev_end = self.last_net_end
                        self.net_peak = 0.0
                        self.net_st_peak = {}
                        for x in self.st_state.values():
                            x.jump_t = None
                        if self.closing is not None:
                            # event baru terbuka tak lama setelah event sebelumnya ditutup:
                            # kandidat penggabungan, diputuskan setelah merge_eval detik
                            self.merge_cand, self.closing = self.closing, None
                            self.net_prev_end = self.merge_cand.get("prev_end")
                        self._log(f"EVENT DIBUKA t_on={t_on} stasiun={grp}")
                        self._update_peak(ratio, t2, name)
                return

            # event jaringan sedang berlangsung
            if change == "on" and name not in self.net_stations:
                self.net_stations.append(name)
            self._update_peak(ratio, t2, name)

            # --- pemisahan event (onset ulang) ---
            if self.split and jump is not None and ratio >= self.split_rmin:
                age = t2 - self.net_t_on
                if ((jump >= self.split_j1 and age >= self.split_age1)
                        or (jump >= self.split_j2 and age >= self.split_age2)):
                    s.jump_t = t2
                    grp = [(x.jump_t, n) for n, x in self.st_state.items()
                           if x.jump_t is not None and abs(x.jump_t - t2) <= self.split_win]
                    if len(grp) >= self.split_min_sta:
                        t_split = min(t for t, _ in grp)
                        self._log(f"EVENT DIPECAH di {t_split} (lonjakan di {[n for _, n in grp]})")
                        self._resolve_merge(False, t2)
                        if t_split - self.net_t_on > self.min_event_dur:
                            self._close({"t_on": self.net_t_on, "t_off": t_split,
                                         "stations": list(self.net_stations),
                                         "lt_ref": self.net_lt_ref, "precursor": True,
                                         "prev_end": self.net_prev_end,
                                         "peak2": self._peak2(),
                                         "split_from": self.net_split_from}, t2)
                        self.net_split_from = self.net_t_on
                        self.net_t_on = t_split
                        self.net_stations = [n for n, x in self.st_state.items() if x.on]
                        for x in self.st_state.values():
                            x.jump_t = None
                            if x.on:
                                x.t_on = t_split
                        return

            active = [n for n, x in self.st_state.items()
                      if x.on and x.t_on >= self.net_t_on - self.coinc_win]
            forced = t2 - self.net_t_on > self.max_dur
            if len(active) < self.close_min_sta or forced:
                t_off = t2 if (forced or change != "off") else s.last_t_off
                ev = {"t_on": self.net_t_on, "t_off": t_off,
                      "stations": list(self.net_stations),
                      "lt_ref": self.net_lt_ref, "precursor": False,
                      "prev_end": self.net_prev_end,
                      "peak2": self._peak2(), "st_peak": dict(self.net_st_peak),
                      "split_from": self.net_split_from}
                self.last_net_end = t_off
                if self.merge_cand is not None:
                    # event lanjutan selesai sebelum diputuskan: gabung bila lemah
                    weak = self.net_peak < self.merge_peak
                    pm, self.merge_cand = self.merge_cand, None
                    if weak:
                        ev["peak2"] = max(ev["peak2"], pm.get("peak2", 0.0))
                        ev.update(t_on=pm["t_on"], lt_ref=pm["lt_ref"], split_from=pm["split_from"],
                                  stations=pm["stations"] + [n for n in ev["stations"] if n not in pm["stations"]])
                        self._log(f"EVENT DIGABUNG dengan t_on={pm['t_on']} (puncak {self.net_peak:.1f}x)")
                    else:
                        self._close(pm, t2)
                if self.merge_gap > 0 and not forced:
                    ev["deadline"] = t_off + self.merge_gap
                    self.closing = ev
                else:
                    self._close(ev, t2)
                self.net_on, self.net_t_on, self.net_stations = False, None, []

        def _peak2(self):
            v = sorted(self.net_st_peak.values(), reverse=True)
            return v[1] if len(v) > 1 else 0.0

        def _update_peak(self, ratio, t2, name=None):
            if ratio is not None:
                self.net_peak = max(self.net_peak, ratio)
                if name is not None:
                    self.net_st_peak[name] = max(self.net_st_peak.get(name, 0.0), ratio)
            if self.merge_cand is None:
                return
            if self.net_peak >= self.merge_peak:
                self._resolve_merge(False, t2)
            elif t2 - self.net_t_on >= self.merge_eval:
                self._resolve_merge(True, t2)

        def _resolve_merge(self, merge, t2):
            pm, self.merge_cand = self.merge_cand, None
            if pm is None:
                return
            if merge:
                self.net_t_on = pm["t_on"]
                self.net_stations = pm["stations"] + [n for n in self.net_stations if n not in pm["stations"]]
                self.net_lt_ref, self.net_split_from = pm["lt_ref"], pm["split_from"]
                for k, v in pm.get("st_peak", {}).items():
                    self.net_st_peak[k] = max(self.net_st_peak.get(k, 0.0), v)
                self._log(f"EVENT DIGABUNG dengan t_on={pm['t_on']} (puncak {self.net_peak:.1f}x)")
            else:
                self._log(f"TIDAK DIGABUNG: event baru kuat (puncak {self.net_peak:.1f}x)")
                self.net_prev_end = pm["t_off"]
                self._close(pm, t2)

        def _close(self, ev, t_now):
            duration = ev["t_off"] - ev["t_on"]
            if self.min_peak2 and ev.get("peak2", 0.0) < self.min_peak2:
                self._log(f"EVENT DIBATALKAN (puncak stasiun ke-2 {ev.get('peak2', 0):.1f}x < {self.min_peak2}x)")
                return
            if duration > self.min_event_dur:
                self._queue(ev, t_now)
            else:
                self._log(f"EVENT DIBATALKAN (durasi {duration:.2f}s <= {self.min_event_dur}s)")

        # ------------------------------------------------------------------
        def _queue(self, ev, t_now):
            """Selesaikan event; tahan dulu hanya jika aturan petir "lambat" aktif.

            Aturan "awal" hanya memakai waktu picu stasiun pantau SEBELUM onset,
            jadi sudah bisa diputuskan saat event ditutup, tanpa menunggu.
            """
            hold = self.lt_post_win if self.lt_pos else 0.0
            ev["ready_at"] = ev["lt_ref"] + hold
            if self.mon_state and ev["ready_at"] > t_now:
                self.pending.append(ev)
            else:
                self._finalize(ev)

        def _lightning_check(self, t_on, prev_end=None):
            """Return (dt per stasiun pantau, daftar tanda petir).

            Picu stasiun pantau yang dimulai sebelum event jaringan sebelumnya
            berakhir (prev_end) diabaikan: itu sinyal event sebelumnya, bukan petir.
            """
            dts, flags = {}, []
            for m, s in self.mon_state.items():
                early, first = None, None
                for a, b in s.intervals:
                    if prev_end is not None and a < prev_end:
                        continue
                    dt = a - t_on
                    if dt < -self.lt_pre_win or dt > self.lt_post_win:
                        continue
                    if dt < -self.lt_neg:
                        if b is None or (b - t_on) >= -self.lt_neg:
                            early = dt if early is None else min(early, dt)
                    elif first is None:
                        first = dt
                if early is not None:
                    dts[m] = round(early, 2)
                    flags.append(f"{m}:awal")
                elif first is not None:
                    dts[m] = round(first, 2)
                    if self.lt_pos and first > self.lt_pos:
                        flags.append(f"{m}:lambat")
                else:
                    dts[m] = None
            return dts, flags

        def on_event_rejected(self, info: dict) -> None:
            pass

        @staticmethod
        def sof_quality(picks, max_quality: int = 2) -> str:
            """Stasiun dengan pick paling awal di antara pick berkualitas <= max_quality."""
            good = [p for p in picks
                    if getattr(p, "quality_info", {}).get("quality", 4) <= max_quality]
            if not good:
                return ""
            first = min(good, key=lambda p: p.offset)
            parts = first.stream_id.split(".")
            return parts[1] if len(parts) > 1 else ""

        @staticmethod
        def onset_from_picks(picks, t_on, max_quality: int = 2):
            """Onset event = pick paling awal berkualitas <= max_quality.

            Bila tidak ada pick berkualitas, dipakai onset detektor.
            Return (t_onset, sumber), sumber = kode stasiun atau "detektor".
            """
            good = [p for p in picks
                    if getattr(p, "quality_info", {}).get("quality", 4) <= max_quality]
            if not good:
                return t_on, "detektor"
            first = min(good, key=lambda p: p.offset)
            parts = first.stream_id.split(".")
            return first.t_pick, (parts[1] if len(parts) > 1 else "pick")

        def _finalize(self, ev):
            t_on, t_off = ev["t_on"], ev["t_off"]
            dts, flags = self._lightning_check(ev.get("lt_ref", t_on), ev.get("prev_end")) if self.mon_state else ({}, [])
            is_lightning = len(flags) >= self.lt_min_flags if self.mon_state else False
            info = {"t_on": t_on, "t_off": t_off, "stations": ev["stations"],
                    "monitor_dt": dts, "lightning_flags": flags, "lightning": is_lightning,
                    "precursor": ev.get("precursor", False), "split_from": ev.get("split_from")}
            self.last_event_info = info
            self.last_event_stations = list(ev["stations"])
            if is_lightning and self.lightning_action == "reject":
                self._log(f"--- EVENT DITOLAK (petir) t_on={t_on} dur={t_off - t_on:.2f}s "
                          f"dt={dts} tanda={flags} ---")
                self.on_event_rejected(info)
                return
            self._log(f"--- EVENT CONFIRMED (Duration: {t_off - t_on:.2f}s, "
                      f"stasiun={ev['stations']}, dt pantau={dts}) ---")
            picks = self._pick_all(t_on)
            info["t_on_pick"], info["onset_sumber"] = self.onset_from_picks(picks, t_on)
            self.on_event_confirmed(mod.DetectionResult(t_on=t_on, t_off=t_off, picks=picks))
            self._log("--- END EVENT PROCESSING ---")

        def flush(self):
            """Selesaikan event yang masih ditahan (dipanggil di akhir replay)."""
            if self.merge_cand is not None:
                ev, self.merge_cand = self.merge_cand, None
                self._close(ev, ev["deadline"])
            if self.closing is not None:
                ev, self.closing = self.closing, None
                self._close(ev, ev["deadline"])
            while self.pending:
                self._finalize(self.pending.pop(0))

    return MultiStationDetector


def _default_class():
    try:
        import realtime_detect_pick as _mod
    except ImportError:
        from waveview.contrib.bpptkg import realtime_detect_pick as _mod
    return make_multi_class(_mod.LteSteDetector, _mod)
