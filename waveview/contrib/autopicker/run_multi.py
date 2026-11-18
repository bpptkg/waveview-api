"""
AutoPicker realtime dengan detektor voting multi-stasiun (multi_detect_pick.py).

Dijalankan BERDAMPINGAN dengan autopicker lama (run.py), tanpa mengubahnya.

Mode bawaan adalah "shadow": event hanya dicatat ke file CSV, TIDAK dibuat di
basis data, supaya tidak muncul event ganda di katalog selama masa uji.
Dengan shadow=False (opsi --live pada perintah manage.py), event yang
dikonfirmasi dikirim ke create_event seperti autopicker lama.

Event yang ditolak penyaring petir selalu dicatat ke file CSV dan log, supaya
setiap penolakan bisa diperiksa.

File log (di log_dir):
    autopicker_multi_events.csv    event yang dikonfirmasi
    autopicker_multi_rejected.csv  event yang ditolak (petir)
"""

import csv
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from obspy.clients.seedlink.easyseedlink import EasySeedLinkClient
from obspy.core.trace import Trace

from waveview.contrib.bpptkg import realtime_detect_pick as rdp
from waveview.contrib.bpptkg.multi_detect_pick import make_multi_class

logger = logging.getLogger(__name__)

SERVER_URL = "192.168.0.25:18000"
NETWORK = "VG"
CHANNEL = "HHZ"
ALL_STATIONS = ["MELAB", "MEPET", "MEDEL", "MEGRA", "MEPSL", "MESEL", "MEGEM", "MEPAC"]
VOTE_STATIONS = ["MELAB", "MEPAC", "MEPSL"]
MONITOR_STATIONS = ["MEGRA", "MEGEM"]

FIELDS = ["logged_at", "t_on", "t_on_pick", "onset_sumber", "t_off", "duration_s", "stations", "sof", "sof_kualitas",
          "monitor_dt", "lightning_flags", "note"]
PICK_FIELDS = ["event_t_on", "stream_id", "t_pick", "offset_s", "sigma_s", "early_s", "late_s",
               "snr", "kualitas"]

_MultiBase = make_multi_class(rdp.LteSteDetector, rdp)


def _fmt_dt(info: dict) -> str:
    return ";".join(
        f"{k}:{'' if v is None else format(v, '+.1f')}"
        for k, v in (info.get("monitor_dt") or {}).items()
    )


def _note(info: dict) -> str:
    if info.get("precursor"):
        return "pendahulu"
    if info.get("split_from") is not None:
        return f"dipisah dari {info['split_from']}"
    return ""


class AutoPickerMultiDetector(_MultiBase):
    def __init__(self, *args, shadow: bool = True, log_dir: str | None = None, **kwargs) -> None:
        self.shadow = shadow
        self.log_dir = Path(log_dir or os.environ.get("AUTOPICKER_MULTI_LOG_DIR", "autopicker_multi_logs"))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        super().__init__(*args, **kwargs)

    def enable_debug(self) -> None:
        self.debug = True

    def _append(self, filename: str, row: dict, fields=FIELDS) -> None:
        path = self.log_dir / filename
        if path.exists():
            with open(path, newline="") as f:
                header = next(csv.reader(f), [])
            if header != list(fields):
                # format kolom berubah: simpan file lama dengan nama lain
                stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
                path.rename(path.with_name(f"{path.stem}_sebelum_{stamp}{path.suffix}"))
        new = not path.exists()
        with open(path, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            if new:
                w.writeheader()
            w.writerow(row)

    def _row(self, t_on, t_off, info: dict, sof: str = "", sof_q: str = "") -> dict:
        return {
            "logged_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "t_on": str(t_on),
            "t_on_pick": str(info.get("t_on_pick", "")),
            "onset_sumber": info.get("onset_sumber", ""),
            "t_off": str(t_off),
            "duration_s": round(t_off - t_on, 2),
            "stations": "+".join(info.get("stations", [])),
            "sof": sof,
            "sof_kualitas": sof_q,
            "monitor_dt": _fmt_dt(info),
            "lightning_flags": ";".join(info.get("lightning_flags", [])),
            "note": _note(info),
        }

    def on_event_confirmed(self, result: rdp.DetectionResult) -> None:
        info = getattr(self, "last_event_info", {}) or {}
        # SOF lama = pick paling awal (tanpa melihat kualitas); dihitung di sini karena
        # get_sof() tidak ada di semua versi realtime_detect_pick.py
        sof = min(result.picks, key=lambda p: p.offset).stream_id.split(".")[1] if result.picks else ""
        sof_q = self.sof_quality(result.picks)
        try:
            self._append("autopicker_multi_events.csv", self._row(result.t_on, result.t_off, info, sof, sof_q))
            for p in result.picks:
                q = getattr(p, "quality_info", {}) or {}
                self._append("autopicker_multi_picks.csv", {
                    "event_t_on": str(result.t_on), "stream_id": p.stream_id, "t_pick": str(p.t_pick),
                    "offset_s": round(p.offset, 2), "sigma_s": q.get("sigma_s"), "early_s": q.get("early_s"),
                    "late_s": q.get("late_s"), "snr": q.get("snr"), "kualitas": q.get("quality"),
                }, PICK_FIELDS)
        except Exception as e:  # noqa: BLE001
            logger.error(f"Gagal menulis log event: {e}")
        logger.info(f"Event dikonfirmasi t_on={result.t_on} durasi={result.get_duration():.1f}s "
                    f"stasiun={info.get('stations')} shadow={self.shadow}")
        if not self.shadow:
            from waveview.contrib.autopicker.task import create_event

            if hasattr(rdp.DetectionResult, "get_sof_pick"):
                # task.py versi main. Kunci tambahan "sof_station" dan "event_time"
                # dibaca oleh task.py yang sudah disesuaikan (SOF = sof_kualitas,
                # waktu = onset dari pick); task.py lama mengabaikannya dan memakai
                # aturan MEPAC/MEPSL. Semua pick tetap diteruskan.
                data = result.to_dict()
                t_ev = info.get("t_on_pick") or result.t_on
                data["sof_station"] = sof_q or ""
                data["event_time"] = t_ev.isoformat()
                create_event.delay(data)
            else:
                # task.py versi lama: SOF = pick paling awal, waktu = t_on.
                # Hanya pick berkualitas (<= 2) diteruskan dan waktu = onset dari pick.
                good = [p for p in result.picks
                        if (getattr(p, "quality_info", {}) or {}).get("quality", 4) <= 2]
                t_ev = info.get("t_on_pick") or result.t_on
                create_event.delay(
                    rdp.DetectionResult(t_on=t_ev, t_off=result.t_off, picks=good).to_dict()
                )

    def on_event_rejected(self, info: dict) -> None:
        try:
            self._append("autopicker_multi_rejected.csv", self._row(info["t_on"], info["t_off"], info))
        except Exception as e:  # noqa: BLE001
            logger.error(f"Gagal menulis log event ditolak: {e}")
        logger.warning(f"Event DITOLAK (petir) t_on={info['t_on']} "
                       f"durasi={info['t_off'] - info['t_on']:.1f}s "
                       f"dt_pantau={info.get('monitor_dt')} tanda={info.get('lightning_flags')}")


class AutoPickerMultiSeedLinkClient(EasySeedLinkClient):
    def __init__(self, *args, debug: bool = False, shadow: bool = True,
                 log_dir: str | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.detector = AutoPickerMultiDetector(
            network=NETWORK,
            station=VOTE_STATIONS[0],
            channel=CHANNEL,
            # instance_id membedakan file buffer harian dari autopicker lama
            instance_id="multi",
            debug=False,
            shadow=shadow,
            log_dir=log_dir,
            vote_stations=VOTE_STATIONS,
            min_sta=2,
            close_min_sta=1,
            monitor_stations=MONITOR_STATIONS,
            lightning_action="reject",
            merge_gap=20,
            min_peak2=3.0,
        )
        if debug:
            self.detector.enable_debug()

    def on_data(self, trace: Trace) -> None:
        self.detector.on_data(trace)


def run_autopicker_multi(debug: bool = False, shadow: bool = True, log_dir: str | None = None,
                         server_url: str = SERVER_URL) -> None:
    logger.info(f"Starting AutoPicker MULTI client connecting to {server_url} "
                f"(mode={'shadow' if shadow else 'LIVE'})")

    client = AutoPickerMultiSeedLinkClient(
        server_url=server_url, autoconnect=True, debug=debug, shadow=shadow, log_dir=log_dir
    )
    for sta in ALL_STATIONS:
        client.select_stream(NETWORK, sta, CHANNEL)

    while True:
        try:
            client.run()
        except KeyboardInterrupt:
            logger.info("Client stopped by user.")
            client.close()
            break
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error running AutoPicker MULTI client: {e} - retrying in 5 seconds")
            time.sleep(5)


if __name__ == "__main__":
    # Uji tanpa Django (hanya mode shadow), dijalankan dari folder waveview-api:
    #     python -m waveview.contrib.autopicker.run_multi --debug
    import argparse

    ap = argparse.ArgumentParser(description="AutoPicker multi-stasiun, mode shadow, tanpa Django")
    ap.add_argument("--server", default=SERVER_URL, help="Alamat SeedLink host:port")
    ap.add_argument("--debug", action="store_true", help="Tampilkan log detektor")
    ap.add_argument("--log-dir", default=None, help="Folder log CSV")
    a = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run_autopicker_multi(debug=a.debug, shadow=True, log_dir=a.log_dir, server_url=a.server)
