from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import median

from waveview.contrib.bma.thermal_direction.times import as_utc

# Left bank (Kiri) and right bank (Kanan) of the Merapi river axis.
# Kuning and Gendol are returned by the thermal-axis API but are not in
# either set, so a winning spike there keeps the river name and sets arah
# to "Tidak terdeteksi".
LEFT_RIVERS = frozenset({"Krasak", "Boyong", "Sat"})
RIGHT_RIVERS = frozenset({"Bebeng", "Putih", "Lamat", "Senowo"})
UNMAPPED_RIVERS = frozenset({"Kuning", "Gendol"})

# Rivers the thermal-axis-jrg endpoint is normally asked for.
FETCH_RIVERS = (
    "Sat",
    "Bebeng",
    "Krasak",
    "Putih",
    "Boyong",
    "Kuning",
    "Gendol",
)

LOOKBACK = timedelta(minutes=10)
LOOKAHEAD = timedelta(minutes=2)
SPIKE_DELTA_C = 5.0

TIDAK_TERDETEKSI = "Tidak terdeteksi"
ARAH_KIRI = "Kiri"
ARAH_KANAN = "Kanan"

_KNOWN_RIVERS = {
    name.casefold(): name
    for name in (*LEFT_RIVERS, *RIGHT_RIVERS, *UNMAPPED_RIVERS)
}
_RIVER_PREFIXES = ("kali ", "k. ")


@dataclass(frozen=True)
class ThermalSample:
    river: str
    time: datetime
    temperature: float


@dataclass(frozen=True)
class DirectionResult:
    hasil_akhir: str
    arah: str
    winner: str | None
    spike_time: datetime | None = None
    baseline: float | None = None


def canonical_river(name: str) -> str:
    cleaned = " ".join(name.strip().split())
    lowered = cleaned.casefold()
    for prefix in _RIVER_PREFIXES:
        if lowered.startswith(prefix):
            cleaned = cleaned[len(prefix) :].strip()
            lowered = cleaned.casefold()
            break
    return _KNOWN_RIVERS.get(lowered, cleaned)


def direction_for(river: str | None) -> str:
    if river in LEFT_RIVERS:
        return ARAH_KIRI
    if river in RIGHT_RIVERS:
        return ARAH_KANAN
    return TIDAK_TERDETEKSI


def classify(samples: list[ThermalSample], event_time: datetime) -> DirectionResult:
    """
    Pick the river whose temperature spikes first after the event.

    Baseline is the median of samples strictly before ``event_time``. A spike
    is the first sample at or after the event whose temperature is at least
    baseline + 5°C. The earliest spike wins. Equal spike times break
    alphabetically by river name.
    """
    event_utc = as_utc(event_time)
    by_river: dict[str, list[ThermalSample]] = {}
    for sample in samples:
        river = canonical_river(sample.river)
        if not river:
            continue
        normalized = ThermalSample(
            river=river,
            time=as_utc(sample.time),
            temperature=sample.temperature,
        )
        by_river.setdefault(river, []).append(normalized)

    candidates: list[tuple[datetime, str, float]] = []
    for river, rows in by_river.items():
        before = [row.temperature for row in rows if row.time < event_utc]
        if not before:
            continue
        baseline = float(median(before))
        threshold = baseline + SPIKE_DELTA_C
        after = sorted(
            (row for row in rows if row.time >= event_utc),
            key=lambda row: row.time,
        )
        for row in after:
            if row.temperature >= threshold:
                candidates.append((row.time, river, baseline))
                break

    if not candidates:
        return DirectionResult(
            hasil_akhir=TIDAK_TERDETEKSI,
            arah=TIDAK_TERDETEKSI,
            winner=None,
        )

    spike_time, river, baseline = min(candidates, key=lambda item: (item[0], item[1]))
    return DirectionResult(
        hasil_akhir=river,
        arah=direction_for(river),
        winner=river,
        spike_time=spike_time,
        baseline=baseline,
    )
