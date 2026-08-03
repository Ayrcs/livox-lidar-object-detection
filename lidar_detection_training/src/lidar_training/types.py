from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class Box3D:
    class_name: str
    center_xyz: tuple[float, float, float]
    size_lwh: tuple[float, float, float]
    yaw: float = 0.0
    attributes: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        values = np.asarray((*self.center_xyz, *self.size_lwh, self.yaw), dtype=float)
        if not np.isfinite(values).all():
            raise ValueError("box values must be finite")
        if any(dimension <= 0 for dimension in self.size_lwh):
            raise ValueError("box dimensions must be positive")


@dataclass(frozen=True)
class Sample:
    sample_id: str
    session_id: str
    timestamp_ns: int
    frame_id: str
    points: NDArray[np.floating]
    boxes: tuple[Box3D, ...] = ()

    def __post_init__(self) -> None:
        if self.points.ndim != 2 or self.points.shape[1] < 3:
            raise ValueError("points must have shape (N, F) with F >= 3")
        if not self.sample_id or not self.session_id or not self.frame_id:
            raise ValueError("sample_id, session_id and frame_id are required")
        if self.timestamp_ns < 0:
            raise ValueError("timestamp_ns must be non-negative")
