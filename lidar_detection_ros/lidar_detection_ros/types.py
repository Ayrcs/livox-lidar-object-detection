"""Framework-independent detection types."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Detection3D:
    """One LiDAR-frame 3D detection.

    Coordinates follow the model convention: x forward, y left and z up.
    """

    class_id: int
    class_name: str
    score: float
    x: float
    y: float
    z: float
    length: float
    width: float
    height: float
    yaw: float

    def to_dict(self) -> dict[str, int | float | str]:
        return asdict(self)
