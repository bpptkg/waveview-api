from dataclasses import asdict, dataclass


@dataclass
class XYZGrid:
    """
    Grid with x, y, and z coordinates.
    """

    name: str
    nx: int
    ny: int
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z_min: float
    z_max: float
    grid: list[tuple[float, float, float]]

    def to_dict(self) -> dict:
        return asdict(self)
