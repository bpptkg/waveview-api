import logging
import re
from datetime import datetime, timedelta
from urllib.parse import quote, unquote

import requests

from waveview.contrib.bma.thermal_direction.classifier import DirectionResult
from waveview.contrib.bma.thermal_direction.times import (
    as_utc,
    format_bma_time,
    parse_bma_time,
)

logger = logging.getLogger(__name__)

# BulletinPayloadBuilder has a fixed column set and no direction field.
# These names are sent as extra JSON keys. ``arah_sumber`` mirrors ``arah``
# (Kiri/Kanan/Tidak terdeteksi). The remark line is the fallback when the
# bulletin serializer only keeps free text.
TEXT_FIELDS = ("remark", "keterangan", "catatan", "note")
_REMARK_RE = re.compile(r"Arah termal:.*?(?:; Hasil akhir: [^;\n]*)")


class BulletinUpdateError(Exception):
    """Transient failure while writing direction onto a BMA bulletin."""


def thermal_remark(result: DirectionResult) -> str:
    return f"Arah termal: {result.arah}; Hasil akhir: {result.hasil_akhir}"


def direction_attributes(result: DirectionResult) -> dict[str, str]:
    return {
        "arah": result.arah,
        "hasil_akhir": result.hasil_akhir,
        "arah_sumber": result.arah,
    }


def upsert_remark(text: str | None, summary: str) -> str:
    current = text or ""
    if _REMARK_RE.search(current):
        return _REMARK_RE.sub(summary, current, count=1)
    if current and not current.endswith("\n"):
        current += "\n"
    return current + summary


def apply_direction_fields(payload: dict | None, result: DirectionResult) -> dict:
    """Copy ``payload`` and set arah, hasil_akhir, arah_sumber, and remark text."""
    body = dict(payload or {})
    body.update(direction_attributes(result))
    summary = thermal_remark(result)
    chosen = next((key for key in TEXT_FIELDS if key in body), None)
    if chosen is None:
        body["remark"] = summary
        return body
    current = body[chosen]
    body[chosen] = upsert_remark(current if isinstance(current, str) else None, summary)
    return body


def closest_bulletin_id(
    rows: list[dict],
    event_time: datetime,
    event_type: str | None = None,
) -> str | None:
    candidates: list[tuple[float, str]] = []
    typed: list[tuple[float, str]] = []
    target = as_utc(event_time)
    for row in rows:
        if not isinstance(row, dict):
            continue
        eventid = row.get("eventid")
        raw_time = row.get("eventdate")
        if not eventid or not raw_time:
            continue
        try:
            stamp = parse_bma_time(str(raw_time))
        except (TypeError, ValueError):
            continue
        delta = abs((stamp - target).total_seconds())
        item = (delta, unquote(str(eventid)))
        candidates.append(item)
        row_type = str(row.get("eventtype") or "").strip().casefold()
        if event_type and row_type == event_type.strip().casefold():
            typed.append(item)
    pool = typed or candidates
    if not pool:
        return None
    pool.sort(key=lambda item: (item[0], item[1]))
    return pool[0][1]


class BulletinDirectionClient:
    """Best-effort write of thermal direction onto a BMA seismic bulletin."""

    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    @classmethod
    def from_settings(cls) -> "BulletinDirectionClient":
        from django.conf import settings

        return cls(settings.BMA_URL, settings.BMA_API_KEY)

    def push(
        self,
        *,
        refid: str | None,
        event_time: datetime,
        result: DirectionResult,
        event_type: str | None = None,
    ) -> None:
        if not self.base_url or not self.api_key:
            logger.warning("Skipping BMA bulletin direction update; BMA settings empty")
            return

        bulletin_id = self._resolve_id(refid, event_time, event_type)
        if not bulletin_id:
            logger.info("No BMA bulletin matched refid=%s", refid)
            return

        url = f"{self.base_url}/api/v1/crud/bulletin/{quote(bulletin_id, safe='')}/"
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        fields = apply_direction_fields({}, result)
        response = self._request("patch", url, headers=headers, json=fields)
        if response.status_code == 404:
            logger.info("BMA bulletin %s was not found", bulletin_id)
            return
        if response.ok:
            logger.info("Patched thermal direction onto BMA bulletin %s", bulletin_id)
            return
        if response.status_code not in (400, 405, 415, 422):
            raise BulletinUpdateError(
                f"PATCH bulletin {bulletin_id} failed ({response.status_code})"
            )

        logger.warning(
            "PATCH bulletin %s rejected (%s); retrying with the stored bulletin",
            bulletin_id,
            response.status_code,
        )
        current = self._request("get", url, headers=headers)
        if current.status_code == 404:
            logger.info("BMA bulletin %s was not found", bulletin_id)
            return
        if not current.ok:
            raise BulletinUpdateError(
                f"GET bulletin {bulletin_id} failed ({current.status_code})"
            )
        try:
            payload = current.json()
        except ValueError as exc:
            raise BulletinUpdateError(
                f"Bulletin {bulletin_id} was not JSON"
            ) from exc
        if not isinstance(payload, dict):
            logger.warning("BMA bulletin %s payload was not an object", bulletin_id)
            return

        merged = apply_direction_fields(payload, result)
        updated = self._request("put", url, headers=headers, json=merged)
        if updated.ok:
            logger.info("Updated thermal direction on BMA bulletin %s", bulletin_id)
            return
        if updated.status_code >= 500 or updated.status_code == 429:
            raise BulletinUpdateError(
                f"PUT bulletin {bulletin_id} failed ({updated.status_code})"
            )
        logger.error(
            "BMA bulletin %s rejected direction fields (%s): %s",
            bulletin_id,
            updated.status_code,
            updated.text[:500],
        )

    def _resolve_id(
        self,
        refid: str | None,
        event_time: datetime,
        event_type: str | None,
    ) -> str | None:
        if refid:
            return unquote(str(refid))

        start = event_time - timedelta(seconds=60)
        end = event_time + timedelta(seconds=60)
        url = f"{self.base_url}/api/v1/bulletin/"
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Accept": "application/json",
        }
        response = self._request(
            "get",
            url,
            headers=headers,
            params={
                "eventdate__gte": format_bma_time(start),
                "eventdate__lt": format_bma_time(end),
                "nolimit": "true",
            },
        )
        if response.status_code == 404:
            return None
        if not response.ok:
            raise BulletinUpdateError(
                f"Bulletin search failed ({response.status_code})"
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise BulletinUpdateError("Bulletin search was not JSON") from exc
        rows = _bulletin_rows(payload)
        return closest_bulletin_id(rows, event_time, event_type=event_type)

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        try:
            return requests.request(method, url, timeout=30, **kwargs)
        except requests.RequestException as exc:
            raise BulletinUpdateError(f"BMA bulletin request failed: {exc}") from exc


def _bulletin_rows(payload) -> list[dict]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("results", "data", "objects"):
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
    return []
