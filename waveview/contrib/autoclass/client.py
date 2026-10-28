"""Single-event contract with the pinned, private autoclass service."""

import json
import math
from datetime import UTC
from urllib.parse import urlsplit

import requests
from django.conf import settings

TYPES = {
    "VTA": "VTA",
    "VTB": "VTB",
    "MP": "MP",
    "LF": "LF",
    "TECT": "TECT",
    "DG": "GASBURST",
    "RF": "ROCKFALL",
    "APG": "AWANPANAS",
}


class PredictionError(Exception):
    def __init__(self, code, retryable=False):
        self.code = code
        self.retryable = retryable
        super().__init__(code)


def probability(value):
    return type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 1


def predict(event):
    base = settings.AUTOCLASS_URL.rstrip("/")
    url = urlsplit(base)
    if (
        url.scheme not in ("http", "https")
        or not url.netloc
        or url.username
        or not settings.AUTOCLASS_TOKEN
    ):
        raise PredictionError("configuration")
    try:
        response = requests.post(
            base + "/predict",
            headers={"X-Token": settings.AUTOCLASS_TOKEN},
            json={
                "eventid": str(event.id),
                "waktu": event.time.astimezone(UTC).isoformat().replace("+00:00", "Z"),
                "utc": True,
                "simpan": False,
                "tunggu": False,
                "sumber": "veps",
            },
            timeout=(10, 180),
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        raise PredictionError("unavailable", True) from exc
    if response.status_code != 200:
        raise PredictionError(
            "unavailable"
            if response.status_code >= 500 or response.status_code == 429
            else "configuration",
            response.status_code >= 500 or response.status_code == 429,
        )
    try:
        result = response.json()
        if isinstance(result, dict) and result.get("status") == "gagal":
            raise PredictionError("data_unavailable", True)
        # PostgreSQL JSON and every consumer require finite JSON values.
        json.dumps(result, allow_nan=False)
        valid = (
            isinstance(result, dict)
            and result.get("status") == "ok"
            and result.get("eventid") == str(event.id)
            and result.get("waktu_utc")
            == event.time.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S")
            and result.get("model") == "model_merapi_v6ga_m1348"
            and result.get("versi") == "0.3.1"
            and result.get("jenis") in TYPES
            and probability(result.get("prob_jenis"))
            and result.get("arah") in (None, "kiri", "kanan")
            and result.get("arah_model") in (None, "kiri", "kanan")
            and (result.get("prob_arah") is None or probability(result["prob_arah"]))
            and isinstance(result.get("top3", []), list)
            and all(
                isinstance(row, dict)
                and row.get("kelas") in TYPES
                and probability(row.get("p"))
                for row in result.get("top3", [])
            )
            and all(
                result.get(key) is None or isinstance(result[key], str)
                for key in (
                    "kelas",
                    "kelas_10",
                    "arah_sumber",
                    "catatan",
                    "tanda_awan_panas",
                    "diproses_utc",
                )
            )
            and (
                result.get("saran") is None
                or isinstance(result["saran"], list)
                and all(isinstance(item, str) for item in result["saran"])
            )
            and (
                result.get("cek_tektonik") is None
                or isinstance(result["cek_tektonik"], dict)
                and all(
                    result["cek_tektonik"].get(key) is None
                    or isinstance(result["cek_tektonik"][key], str)
                    for key in ("saran", "tanda")
                )
            )
        )
        if not valid:
            raise PredictionError("invalid_result")
        return result
    except (ValueError, TypeError, KeyError) as exc:
        raise PredictionError("invalid_result") from exc
