from dataclasses import dataclass


@dataclass
class Rect:
    x: int
    y: int
    width: int
    height: int

    def __str__(self) -> str:
        return f"Rect(x={self.x}, y={self.y}, width={self.width}, height={self.height})"

    def __repr__(self) -> str:
        return str(self)

    def contains(self, x: float, y: float) -> bool:
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height

    def intersects(self, other: "Rect") -> bool:
        return (
            self.x < other.x + other.width
            and other.x < self.x + self.width
            and self.y < other.y + other.height
            and other.y < self.y + self.height
        )

    def intersection(self, other: "Rect") -> "Rect":
        if not self.intersects(other):
            return None
        x = max(self.x, other.x)
        y = max(self.y, other.y)
        width = min(self.x + self.width, other.x + other.width) - x
        height = min(self.y + self.height, other.y + other.height) - y
        return Rect(x, y, width, height)

    def union(self, other: "Rect") -> "Rect":
        x = min(self.x, other.x)
        y = min(self.y, other.y)
        width = max(self.x + self.width, other.x + other.width) - x
        height = max(self.y + self.height, other.y + other.height) - y
        return Rect(x, y, width, height)

    def move(self, dx: float, dy: float) -> "Rect":
        return Rect(self.x + dx, self.y + dy, self.width, self.height)

    def scale(self, sx: float, sy: float) -> "Rect":
        return Rect(self.x * sx, self.y * sy, self.width * sx, self.height * sy)

    def translate(self, x: float, y: float) -> "Rect":
        return Rect(self.x + x, self.y + y, self.width, self.height)

    def to_tuple(self) -> tuple[float, float, float, float]:
        return self.x, self.y, self.width, self.height

    @staticmethod
    def from_tuple(t) -> "Rect":
        return Rect(*t)

    @staticmethod
    def from_dict(d) -> "Rect":
        return Rect(**d)

    def to_dict(self) -> dict[str, int]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }
