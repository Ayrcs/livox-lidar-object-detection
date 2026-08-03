from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class FloorFitConfig:
    x_range_m: tuple[float, float] = (0.5, 6.0)
    abs_y_max_m: float = 0.8
    z_range_m: tuple[float, float] = (-1.5, -0.9)
    residual_threshold_m: float = 0.025
    iterations: int = 3


def fit_floor_plane(points: NDArray[np.float32], config: FloorFitConfig) -> NDArray[np.float64]:
    """Fit z = ax + by + c, iteratively rejecting non-floor returns."""
    finite = np.isfinite(points[:, :3]).all(axis=1)
    mask = (
        finite
        & (points[:, 0] > config.x_range_m[0])
        & (points[:, 0] < config.x_range_m[1])
        & (np.abs(points[:, 1]) < config.abs_y_max_m)
        & (points[:, 2] > config.z_range_m[0])
        & (points[:, 2] < config.z_range_m[1])
    )
    floor = np.asarray(points[mask, :3], dtype=np.float64)
    if len(floor) < 3:
        raise ValueError("not enough floor candidates")
    coefficients = _least_squares_plane(floor)
    for _ in range(config.iterations):
        residual = floor[:, 2] - _plane_z(floor[:, :2], coefficients)
        center = np.median(residual)
        floor = floor[np.abs(residual - center) < config.residual_threshold_m]
        if len(floor) < 3:
            raise ValueError("floor rejection removed too many points")
        coefficients = _least_squares_plane(floor)
    return coefficients


def heights_above_plane(points: NDArray[np.float32], coefficients: NDArray[np.float64]) -> NDArray[np.float64]:
    return points[:, 2] - _plane_z(points[:, :2], coefficients)


def count_target_returns(
    points: NDArray[np.float32],
    floor_coefficients: NDArray[np.float64],
    center_xy_m: tuple[float, float],
    half_size_xy_m: float = 0.12,
    height_range_m: tuple[float, float] = (0.02, 0.24),
) -> tuple[int, NDArray[np.float32]]:
    height = heights_above_plane(points, floor_coefficients)
    mask = (
        (np.abs(points[:, 0] - center_xy_m[0]) <= half_size_xy_m)
        & (np.abs(points[:, 1] - center_xy_m[1]) <= half_size_xy_m)
        & (height >= height_range_m[0])
        & (height <= height_range_m[1])
    )
    selected = points[mask]
    return len(selected), selected


def summarize_counts(counts: NDArray[np.integer]) -> dict[str, float | int]:
    if len(counts) == 0:
        raise ValueError("cannot summarize an empty count array")
    return {
        "frame_count": len(counts),
        "mean": float(np.mean(counts)),
        "std": float(np.std(counts)),
        "min": int(np.min(counts)),
        "median": float(np.median(counts)),
        "max": int(np.max(counts)),
        "zero_fraction": float(np.mean(counts == 0)),
        "under_3_fraction": float(np.mean(counts < 3)),
        "under_10_fraction": float(np.mean(counts < 10)),
    }


def _least_squares_plane(points_xyz: NDArray[np.float64]) -> NDArray[np.float64]:
    design = np.column_stack((points_xyz[:, 0], points_xyz[:, 1], np.ones(len(points_xyz))))
    return np.linalg.lstsq(design, points_xyz[:, 2], rcond=None)[0]


def _plane_z(points_xy: NDArray[np.floating], coefficients: NDArray[np.float64]) -> NDArray[np.float64]:
    return coefficients[0] * points_xy[:, 0] + coefficients[1] * points_xy[:, 1] + coefficients[2]
