from __future__ import annotations

from urllib.parse import quote

import requests

from waveview.contrib.bma.thermal_direction.classifier import DirectionResult


class ThermalBulletinError(Exception):
    pass


def push_bulletin_direction(
    *,
    base_url: str,
    api_key: str,
    bulletin_id: str,
    result: DirectionResult,
    session: requests.Session | None = None,
) -> None:
    """
    Best-effort write of the winning river name onto one BMA bulletin.

    Uses ``Authorization: Api-Key``. ``bulletin_id`` is the event ``refid`` or its
    UUID hex, the same id the ``bma.bulletin`` observer writes. ``arah_kubah_termal``
    is ``result.hasil_akhir`` (the river name).
    """
    api = session or requests.Session()
    headers = {
        "Authorization": f"Api-Key {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    try:
        response = api.patch(
            _arah_kubah_termal_url(base_url, bulletin_id),
            json={"arah_kubah_termal": result.hasil_akhir},
            headers=headers,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise ThermalBulletinError("BMA bulletin request failed") from exc
    if not response.ok:
        raise ThermalBulletinError(
            f"BMA bulletin update failed with status {response.status_code}"
        )


def _arah_kubah_termal_url(base_url: str, bulletin_id: str) -> str:
    quoted = quote(str(bulletin_id), safe="")
    return f"{base_url.rstrip('/')}/api/v1/crud/bulletin/{quoted}/arah_kubah_termal/"

