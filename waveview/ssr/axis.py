from typing import Literal

from waveview.ssr.rect import Rect

AxisOrientation = Literal["vertical", "horizontal"]


class Axis:
    def __init__(
        self, extent: tuple[float, float], rect: Rect, orientation: AxisOrientation
    ) -> None:
        minValue, maxValue = extent
        self.min = minValue
        self.max = maxValue
        self.rect = rect
        self.orientation = orientation

    def __str__(self) -> str:
        return f"Axis(min={self.min}, max={self.max}, rect={self.rect})"

    def __repr__(self) -> str:
        return str(self)

    def get_extent(self) -> tuple[float, float]:
        return (self.min, self.max)

    def is_horizontal(self) -> bool:
        return self.orientation == "horizontal"

    def is_vertical(self) -> bool:
        return self.orientation == "vertical"

    def contains(self, value: float) -> bool:
        return self.min <= value <= self.max

    def scale(self, sx: float) -> "Axis":
        return Axis((self.min * sx, self.max * sx), self.rect)

    def translate(self, x: float) -> "Axis":
        return Axis((self.min + x, self.max + x), self.rect)

    def invert(self, value: float) -> float:
        if self.is_horizontal():
            return self.rect.x + (value - self.min) * self.rect.width / (
                self.max - self.min
            )
        return self.rect.y + (value - self.min) * self.rect.height / (
            self.max - self.min
        )
