from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

from waveview.contrib.bma.thermal_direction.classifier import (
    LEFT_RIVERS,
    RIGHT_RIVERS,
    ThermalSample,
    river_key,
)

WINDOW_BEFORE = timedelta(minutes=10)
WINDOW_AFTER = timedelta(minutes=2)
# BMA parses naive start/end as WIB; an explicit "Z" makes it return 500.
BMA_TZ = ZoneInfo("Asia/Jakarta")
_AREA_SUFFIX = re.compile(r"_\d+$")


class ThermalAxisError(Exception):
    pass


class ThermalAxisClient:
    """Fetch river-axis temperatures from BMA. Credentials come from the caller."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = session or requests.Session()

    def fetch(self, event_time: datetime) -> list[ThermalSample]:
        event_time = _as_utc(event_time)
        params = {
            "start": _format_wib(event_time - WINDOW_BEFORE),
            "end": _format_wib(event_time + WINDOW_AFTER),
            "field_types": "max_temp",
        }
        url = f"{self.base_url}/api/v1/thermal-axis-jrg/"
        try:
            response = self.session.get(
                url,
                params=params,
                headers={
                    "Authorization": f"Api-Key {self.api_key}",
                    "Accept": "application/json",
                },
                timeout=30,
            )
        except requests.RequestException as exc:
            raise ThermalAxisError("thermal-axis-jrg request failed") from exc
        if not response.ok:
            raise ThermalAxisError(
                f"thermal-axis-jrg request failed with status {response.status_code}"
            )
        return parse_thermal_payload(response.json())


def parse_thermal_payload(payload: dict) -> list[ThermalSample]:
    """
    Read BMA's {"fields": [{"results": [{"area", "data": [{"timestamp", "temp"}]}]}]}.
    Non-river areas (Asap, Kubah_BD, Ref_*) are dropped; Sat_1/Sat_2 become Sat.
    """
    samples: list[ThermalSample] = []
    for field in payload.get("fields", []):
        for result in field.get("results", []):
            river = _AREA_SUFFIX.sub("", str(result.get("area", "")))
            if river_key(river) not in LEFT_RIVERS | RIGHT_RIVERS:
                continue
            for row in result.get("data", []):
                if row.get("temp") is None or not row.get("timestamp"):
                    continue
                samples.append(
                    ThermalSample(
                        river=river,
                        time=_as_utc(datetime.fromisoformat(row["timestamp"])),
                        temperature=float(row["temp"]),
                    )
                )
    return samples


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _format_wib(value: datetime) -> str:
    return value.astimezone(BMA_TZ).strftime("%Y-%m-%d %H:%M:%S")
