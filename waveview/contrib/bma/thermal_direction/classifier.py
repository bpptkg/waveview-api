from __future__ import annotations

import re
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone

LEFT_RIVERS = frozenset({"krasak", "boyong", "sat"})
RIGHT_RIVERS = frozenset({"bebeng", "putih", "lamat", "senowo"})
SPIKE_DELTA_C = 5.0
TIDAK_TERDETEKSI = "Tidak terdeteksi"
ARAH_KIRI = "Kiri"
ARAH_KANAN = "Kanan"
RF_APG_TYPES = frozenset({"rf", "apg"})

DISPLAY_NAMES = {
    "krasak": "Krasak",
    "boyong": "Boyong",
    "sat": "Sat",
    "bebeng": "Bebeng",
    "putih": "Putih",
    "lamat": "Lamat",
    "senowo": "Senowo",
    "kuning": "Kuning",
    "gendol": "Gendol",
}

NOTE_START = "[thermal-direction]"
NOTE_END = "[/thermal-direction]"
_NOTE_BLOCK = re.compile(
    re.escape(NOTE_START) + r".*?" + re.escape(NOTE_END),
    re.DOTALL,
)


@dataclass(frozen=True)
class ThermalSample:
    river: str
    time: datetime
    temperature: float


@dataclass(frozen=True)
class DirectionResult:
    hasil_akhir: str
    arah: str
    winner: str | None = None
    spike_time: datetime | None = None


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def river_key(name: str) -> str:
    return name.strip().casefold()


def display_river(name: str) -> str:
    cleaned = name.strip()
    return DISPLAY_NAMES.get(river_key(cleaned), cleaned)


def arah_for(name: str) -> str:
    key = river_key(name)
    if key in LEFT_RIVERS:
        return ARAH_KIRI
    if key in RIGHT_RIVERS:
        return ARAH_KANAN
    return TIDAK_TERDETEKSI


def is_rf_or_apg(code: str | None, name: str | None) -> bool:
    """True when event type code or name is RF or APG, ignoring case."""
    for value in (code, name):
        if value and value.strip().casefold() in RF_APG_TYPES:
            return True
    return False


def classify(event_time: datetime, samples: list[ThermalSample]) -> DirectionResult:
    """
    Pick the river whose temperature first rises at least 5°C above its
    pre-event median. Direction comes from the left/right river sets.
    """
    event_time = _as_utc(event_time)
    grouped: dict[str, list[ThermalSample]] = {}
    labels: dict[str, str] = {}
    for sample in samples:
        if not sample.river or not sample.river.strip():
            continue
        key = river_key(sample.river)
        grouped.setdefault(key, []).append(sample)
        labels.setdefault(key, display_river(sample.river))

    spikes: list[tuple[datetime, float, str]] = []
    for key, rows in grouped.items():
        baseline_values = [
            row.temperature for row in rows if _as_utc(row.time) < event_time
        ]
        if not baseline_values:
            continue
        baseline = statistics.median(baseline_values)
        threshold = baseline + SPIKE_DELTA_C
        after = sorted(
            (row for row in rows if _as_utc(row.time) >= event_time),
            key=lambda row: _as_utc(row.time),
        )
        for row in after:
            if row.temperature >= threshold:
                spikes.append(
                    (_as_utc(row.time), row.temperature - baseline, labels[key])
                )
                break

    if not spikes:
        return DirectionResult(
            hasil_akhir=TIDAK_TERDETEKSI,
            arah=TIDAK_TERDETEKSI,
        )

    spike_time, _excess, winner = min(
        spikes, key=lambda item: (item[0], -item[1], item[2])
    )
    return DirectionResult(
        hasil_akhir=winner,
        arah=arah_for(winner),
        winner=winner,
        spike_time=spike_time,
    )


def render_thermal_note(result: DirectionResult, classified_at: datetime) -> str:
    winner = result.winner or "-"
    return (
        f"{NOTE_START}\n"
        f"hasil_akhir: {result.hasil_akhir}\n"
        f"arah: {result.arah}\n"
        f"winner: {winner}\n"
        f"classified_at: {classified_at.isoformat()}\n"
        f"{NOTE_END}"
    )


def upsert_thermal_note(
    note: str | None, result: DirectionResult, classified_at: datetime
) -> str:
    block = render_thermal_note(result, classified_at)
    text = note or ""
    if _NOTE_BLOCK.search(text):
        return _NOTE_BLOCK.sub(block, text).strip()
    text = text.rstrip()
    if not text:
        return block
    return f"{text}\n\n{block}"
