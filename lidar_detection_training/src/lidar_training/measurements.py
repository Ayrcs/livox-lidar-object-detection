from dataclasses import dataclass

import numpy as np

from .geometry import points_in_oriented_box
from .types import Box3D


@dataclass(frozen=True)
class BallReturnMeasurement:
    num_points: int
    distance_m: float
    azimuth_deg: float
    intensity_mean: float | None
    intensity_std: float | None
    cluster_size_xyz_m: tuple[float, float, float] | None


def measure_box_returns(points: np.ndarray, box: Box3D, intensity_column: int | None = 3) -> BallReturnMeasurement:
    selected = points[points_in_oriented_box(points, box)]
    center = np.asarray(box.center_xyz)
    distance = float(np.linalg.norm(center[:2]))
    azimuth = float(np.degrees(np.arctan2(center[1], center[0])))
    has_intensity = intensity_column is not None and points.shape[1] > intensity_column
    intensity_mean = float(np.mean(selected[:, intensity_column])) if has_intensity and len(selected) else None
    intensity_std = float(np.std(selected[:, intensity_column])) if has_intensity and len(selected) else None
    cluster_size = tuple(np.ptp(selected[:, :3], axis=0).tolist()) if len(selected) else None
    return BallReturnMeasurement(len(selected), distance, azimuth, intensity_mean, intensity_std, cluster_size)
