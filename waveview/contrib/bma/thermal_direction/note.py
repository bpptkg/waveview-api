import re
from datetime import datetime

from waveview.contrib.bma.thermal_direction.classifier import DirectionResult
from waveview.contrib.bma.thermal_direction.times import as_utc

BLOCK_START = "[thermal-direction]"
BLOCK_END = "[/thermal-direction]"
_BLOCK_RE = re.compile(
    r"\[thermal-direction\].*\[/thermal-direction\]\n?",
    re.DOTALL,
)


def render_thermal_note(result: DirectionResult, classified_at: datetime) -> str:
    winner = result.winner or "-"
    stamp = as_utc(classified_at).isoformat(timespec="seconds")
    return "\n".join(
        [
            BLOCK_START,
            f"hasil_akhir: {result.hasil_akhir}",
            f"arah: {result.arah}",
            f"winner: {winner}",
            f"classified_at: {stamp}",
            BLOCK_END,
        ]
    )


def upsert_event_note(note: str | None, block: str) -> str:
    """Insert ``block`` or replace an existing thermal-direction block."""
    text = note or ""
    if _BLOCK_RE.search(text):
        updated = _BLOCK_RE.sub(block + "\n", text, count=1)
        return updated.rstrip() + "\n"
    if text and not text.endswith("\n"):
        text += "\n"
    if text:
        text += "\n"
    return text + block + "\n"
