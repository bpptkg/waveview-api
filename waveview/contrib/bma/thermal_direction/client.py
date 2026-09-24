from __future__ import annotations

from datetime import datetime, timedelta, timezone

import requests

from waveview.contrib.bma.thermal_direction.classifier import ThermalSample

QUERY_RIVERS = ("Sat", "Bebeng", "Krasak", "Putih", "Boyong", "Kuning", "Gendol")
WINDOW_BEFORE = timedelta(minutes=10)
WINDOW_AFTER = timedelta(minutes=2)
RIVER_KEYS = ("river", "sungai", "name", "axis", "river_name")
TIME_KEYS = ("datetime", "time", "timestamp", "date")
TEMP_KEYS = ("temperature", "temp", "suhu", "value", "max_temp")
_WRAPPER_KEYS = ("results", "data", "samples")


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
        params: list[tuple[str, str]] = [
            ("eventdate", _format_utc(event_time)),
            ("datetime_before", _format_utc(event_time - WINDOW_BEFORE)),
            ("datetime_after", _format_utc(event_time + WINDOW_AFTER)),
        ]
        params.extend(("river", river) for river in QUERY_RIVERS)
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


def parse_thermal_payload(payload: object) -> list[ThermalSample]:
    rows = _unwrap(payload)
    samples: list[ThermalSample] = []
    if isinstance(rows, dict):
        for river, items in rows.items():
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict):
                    parsed = _parse_row(item, default_river=str(river))
                    if parsed is not None:
                        samples.append(parsed)
        return samples
    if isinstance(rows, list):
        for item in rows:
            if isinstance(item, dict):
                parsed = _parse_row(item)
                if parsed is not None:
                    samples.append(parsed)
    return samples


def _unwrap(payload: object) -> object:
    if not isinstance(payload, dict):
        return payload
    for key in _WRAPPER_KEYS:
        inner = payload.get(key)
        if isinstance(inner, list):
            return inner
        if isinstance(inner, dict):
            if _is_river_map(inner):
                return inner
            return _unwrap(inner)
    if _is_river_map(payload):
        return payload
    return payload


def _is_river_map(payload: dict) -> bool:
    return bool(payload) and all(isinstance(value, list) for value in payload.values())


def _parse_row(
    row: dict, default_river: str | None = None
) -> ThermalSample | None:
    river = default_river
    for key in RIVER_KEYS:
        if row.get(key):
            river = str(row[key])
            break
    if not river or not str(river).strip():
        return None
    raw_time = next((row.get(key) for key in TIME_KEYS if row.get(key)), None)
    raw_temp = next(
        (
            row.get(key)
            for key in TEMP_KEYS
            if row.get(key) is not None and row.get(key) != ""
        ),
        None,
    )
    if raw_time is None or raw_temp is None:
        return None
    try:
        temperature = float(raw_temp)
    except (TypeError, ValueError):
        return None
    parsed_time = _parse_time(raw_time)
    if parsed_time is None:
        return None
    return ThermalSample(river=str(river), time=parsed_time, temperature=temperature)


def _parse_time(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return _as_utc(value)
    if not isinstance(value, str):
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed: datetime | None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        parsed = None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
            try:
                parsed = datetime.strptime(value.strip(), fmt)
                break
            except ValueError:
                parsed = None
        if parsed is None:
            return None
    # ponytail: naive timestamps are UTC, the same clock as the query params.
    return _as_utc(parsed)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
