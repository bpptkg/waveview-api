from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import quote
from zoneinfo import ZoneInfo

import requests

from waveview.contrib.bma.thermal_direction.classifier import DirectionResult

REMARK_KEYS = ("remark", "note", "catatan")
REMARK_PREFIX = "thermal-direction:"
_JAKARTA = ZoneInfo("Asia/Jakarta")


class ThermalBulletinError(Exception):
    pass


def direction_fields(result: DirectionResult) -> dict[str, str]:
    return {
        "hasil_akhir": result.hasil_akhir,
        "arah": result.arah,
        "arah_sumber": result.hasil_akhir,
    }


def merge_bulletin_payload(payload: dict, result: DirectionResult) -> dict:
    """
    Attach direction fields to a bulletin payload.

    The WaveView bulletin schema has no free-form attributes column. Top-level
    ``hasil_akhir``, ``arah``, and ``arah_sumber`` are always set. When the
    fetched object already has ``attributes`` or a remark/note/catatan string,
    those are updated too.
    """
    merged = dict(payload)
    fields = direction_fields(result)
    merged.update(fields)
    attributes = payload.get("attributes")
    if isinstance(attributes, dict):
        merged["attributes"] = {**attributes, **fields}
    for key in REMARK_KEYS:
        current = payload.get(key)
        if isinstance(current, str):
            merged[key] = _replace_remark(current, result)
            break
    return merged


def partial_direction_body(existing: dict, result: DirectionResult) -> dict:
    fields = direction_fields(result)
    body = dict(fields)
    if isinstance(existing.get("attributes"), dict):
        body["attributes"] = {**existing["attributes"], **fields}
    for key in REMARK_KEYS:
        current = existing.get(key)
        if isinstance(current, str):
            body[key] = _replace_remark(current, result)
            break
    return body


def push_bulletin_direction(
    *,
    base_url: str,
    api_key: str,
    bulletin_id: str | None,
    result: DirectionResult,
    fallback_payload: dict | None = None,
    event_time: datetime | None = None,
    session: requests.Session | None = None,
) -> None:
    """
    Best-effort update of one BMA bulletin.

    Uses ``Authorization: Api-Key``. Looks the bulletin up by ``refid`` or, when
    that is empty, by event time on ``/api/v1/bulletin/``.
    """
    api = session or requests.Session()
    headers = {
        "Authorization": f"Api-Key {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    resolved_id = bulletin_id or _find_bulletin_id(api, base_url, headers, event_time)
    if not resolved_id:
        raise ThermalBulletinError("No BMA bulletin id for thermal direction")

    crud_url = _crud_url(base_url, resolved_id)
    existing = _get_json(api, crud_url, headers)
    if existing is None:
        existing = _get_json(api, _public_url(base_url, resolved_id), headers)

    if isinstance(existing, dict):
        response = api.patch(
            crud_url,
            json=partial_direction_body(existing, result),
            headers=headers,
            timeout=30,
        )
        if response.status_code == 405:
            response = api.put(
                crud_url,
                json=merge_bulletin_payload(existing, result),
                headers=headers,
                timeout=30,
            )
        if not response.ok:
            raise ThermalBulletinError(
                f"BMA bulletin update failed with status {response.status_code}"
            )
        return

    if fallback_payload is None:
        raise ThermalBulletinError("BMA bulletin not found")
    response = api.put(
        crud_url,
        json=merge_bulletin_payload(fallback_payload, result),
        headers=headers,
        timeout=30,
    )
    if not response.ok:
        raise ThermalBulletinError(
            f"BMA bulletin update failed with status {response.status_code}"
        )


def _replace_remark(text: str, result: DirectionResult) -> str:
    line = f"{REMARK_PREFIX} hasil_akhir={result.hasil_akhir}; arah={result.arah}"
    kept = [row for row in text.splitlines() if not row.strip().startswith(REMARK_PREFIX)]
    body = "\n".join(kept).strip()
    if not body:
        return line if not text.endswith("\n") else f"{line}\n"
    if text.endswith("\n"):
        return f"{body}\n{line}\n"
    return f"{body}\n{line}"


def _crud_url(base_url: str, bulletin_id: str) -> str:
    quoted = quote(str(bulletin_id), safe="")
    return f"{base_url.rstrip('/')}/api/v1/crud/bulletin/{quoted}/"


def _public_url(base_url: str, bulletin_id: str) -> str:
    quoted = quote(str(bulletin_id), safe="")
    return f"{base_url.rstrip('/')}/api/v1/bulletin/{quoted}/"


def _get_json(
    api: requests.Session, url: str, headers: dict[str, str]
) -> dict | None:
    try:
        response = api.get(url, headers=headers, timeout=30)
    except requests.RequestException as exc:
        raise ThermalBulletinError("BMA bulletin request failed") from exc
    if response.status_code == 404:
        return None
    if not response.ok:
        raise ThermalBulletinError(
            f"BMA bulletin request failed with status {response.status_code}"
        )
    payload = response.json()
    if isinstance(payload, dict):
        return payload
    return None


def _find_bulletin_id(
    api: requests.Session,
    base_url: str,
    headers: dict[str, str],
    event_time: datetime | None,
) -> str | None:
    if event_time is None:
        return None
    if event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=timezone.utc)
    start = (event_time - timedelta(minutes=2)).astimezone(_JAKARTA)
    end = (event_time + timedelta(minutes=2)).astimezone(_JAKARTA)
    url = f"{base_url.rstrip('/')}/api/v1/bulletin/"
    try:
        response = api.get(
            url,
            headers=headers,
            params={
                "eventdate__gte": start.strftime("%Y-%m-%d %H:%M:%S"),
                "eventdate__lt": end.strftime("%Y-%m-%d %H:%M:%S"),
                "nolimit": "true",
            },
            timeout=30,
        )
    except requests.RequestException as exc:
        raise ThermalBulletinError("BMA bulletin lookup failed") from exc
    if not response.ok:
        return None
    payload = response.json()
    rows: object = payload
    if isinstance(payload, dict):
        rows = payload.get("results", payload.get("data", []))
    if not isinstance(rows, list):
        return None
    best_id: str | None = None
    best_delta: float | None = None
    target = event_time.astimezone(timezone.utc)
    for row in rows:
        if not isinstance(row, dict) or not row.get("eventid"):
            continue
        parsed = _parse_eventdate(row.get("eventdate"))
        if parsed is None:
            continue
        delta = abs((parsed - target).total_seconds())
        if best_delta is None or delta < best_delta:
            best_delta = delta
            best_id = str(row["eventid"])
    return best_id


def _parse_eventdate(value: object) -> datetime | None:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
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
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=_JAKARTA).astimezone(timezone.utc)
    return parsed.astimezone(timezone.utc)
