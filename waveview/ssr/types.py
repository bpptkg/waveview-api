from dataclasses import dataclass
from typing import Literal

from waveview.ssr.rect import Rect


@dataclass(frozen=True)
class TrackData:
    rect: Rect
    xaxis_extent: tuple[float, float]
    yaxis_extent: tuple[float, float]


@dataclass(frozen=True)
class ContextData:
    chart: Literal["helicorder", "seismogram"]
    width: float
    height: float
    device_pixel_ratio: float
    dark_mode: bool
    rect: Rect
    xaxis_extent: tuple[float, float]
    yaxis_extent: tuple[float, float]
    tracks: list[TrackData]

    @classmethod
    def parse_raw(cls, raw: dict) -> "ContextData":
        return cls(
            chart=raw["chart"],
            width=raw["width"],
            height=raw["height"],
            device_pixel_ratio=raw["devicePixelRatio"],
            dark_mode=raw["darkMode"],
            rect=Rect(**raw["rect"]),
            xaxis_extent=tuple(raw["xAxisExtent"]),
            yaxis_extent=tuple(raw["yAxisExtent"]),
            tracks=[
                TrackData(
                    rect=Rect(**track["rect"]),
                    xaxis_extent=tuple(track["xAxisExtent"]),
                    yaxis_extent=tuple(track["yAxisExtent"]),
                )
                for track in raw["tracks"]
            ],
        )
