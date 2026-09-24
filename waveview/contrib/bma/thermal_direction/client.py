import logging
from datetime import datetime
from typing import Any

import requests

from waveview.contrib.bma.thermal_direction.classifier import (
    FETCH_RIVERS,
    LOOKAHEAD,
    LOOKBACK,
    ThermalSample,
)
from waveview.contrib.bma.thermal_direction.times import format_bma_time, parse_bma_time

logger = logging.getLogger(__name__)

THERMAL_AXIS_PATH = "api/v1/thermal-axis-jrg/"
_TIME_KEYS = ("datetime", "timestamp", "time", "date", "eventdate")
_TEMP_KEYS = ("temperature", "temp", "suhu", "value", "max_temp", "thermal")
_RIVER_KEYS = ("river", "sungai", "name", "axis", "lokasi")
_SERIES_KEYS = ("data", "results", "items", "samples", "series")


class ThermalAxisError(Exception):
    def __init__(self, message: str, *, retryable: bool = True) -> None:
        super().__init__(message)
        self.retryable = retryable


class ThermalAxisClient:
    """Read river-axis temperatures from BMA ``thermal-axis-jrg``."""

    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    @classmethod
    def from_settings(cls) -> "ThermalAxisClient":
        from django.conf import settings

        return cls(settings.BMA_URL, settings.BMA_API_KEY)

    def fetch(self, event_time: datetime) -> list[ThermalSample]:
        if not self.base_url:
            raise ThermalAxisError("BMA_URL is empty", retryable=False)
        if not self.api_key:
            raise ThermalAxisError("BMA_API_KEY is empty", retryable=False)

        before = event_time - LOOKBACK
        after = event_time + LOOKAHEAD
        url = f"{self.base_url}/{THERMAL_AXIS_PATH}"
        params = {
            "eventdate": format_bma_time(event_time),
            "datetime_before": format_bma_time(before),
            "datetime_after": format_bma_time(after),
            "rivers": ",".join(FETCH_RIVERS),
        }
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Accept": "application/json",
        }
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
        except requests.RequestException as exc:
            raise ThermalAxisError(
                f"Thermal axis request failed: {exc}", retryable=True
            ) from exc

        if response.status_code in (401, 403):
            raise ThermalAxisError(
                f"Thermal axis rejected the API key ({response.status_code})",
                retryable=False,
            )
        if not response.ok:
            retryable = response.status_code == 429 or response.status_code >= 500
            detail = response.text[:500]
            raise ThermalAxisError(
                f"Thermal axis request failed ({response.status_code}): {detail}",
                retryable=retryable,
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise ThermalAxisError(
                "Thermal axis response was not JSON", retryable=True
            ) from exc
        return parse_thermal_payload(payload)


def parse_thermal_payload(payload: Any) -> list[ThermalSample]:
    samples: list[ThermalSample] = []
    for row in _flatten(payload):
        sample = _sample_from_row(row)
        if sample is not None:
            samples.append(sample)
    return samples


def _flatten(payload: Any, river: str | None = None) -> list[dict]:
    if payload is None:
        return []
    if isinstance(payload, list):
        rows: list[dict] = []
        for item in payload:
            rows.extend(_flatten(item, river))
        return rows
    if not isinstance(payload, dict):
        return []

    river_name = _river_of(payload) or river
    if _is_sample(payload):
        row = dict(payload)
        if river_name and not _river_of(row):
            row["river"] = river_name
        return [row]

    for key in _SERIES_KEYS:
        nested = payload.get(key)
        if isinstance(nested, (list, dict)):
            return _flatten(nested, river_name)

    rows = []
    for key, value in payload.items():
        if key in _SERIES_KEYS or key in _RIVER_KEYS or key in _TIME_KEYS:
            continue
        if isinstance(value, (list, dict)):
            rows.extend(_flatten(value, river=str(key)))
    return rows


def _is_sample(payload: dict) -> bool:
    return _first(payload, _TIME_KEYS) is not None and _first(payload, _TEMP_KEYS) is not None


def _river_of(payload: dict) -> str | None:
    value = _first(payload, _RIVER_KEYS)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _first(payload: dict, keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in payload and payload[key] not in (None, ""):
            return payload[key]
    return None


def _sample_from_row(row: dict) -> ThermalSample | None:
    river = _river_of(row)
    raw_time = _first(row, _TIME_KEYS)
    raw_temp = _first(row, _TEMP_KEYS)
    if not river or raw_time is None or raw_temp is None:
        return None
    try:
        temperature = float(raw_temp)
        stamp = parse_bma_time(str(raw_time))
    except (TypeError, ValueError):
        logger.warning("Skipping thermal sample with unreadable time or temperature")
        return None
    return ThermalSample(river=river, time=stamp, temperature=temperature)
