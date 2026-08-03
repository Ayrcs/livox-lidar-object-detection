from dataclasses import dataclass
from itertools import product

import numpy as np

from .types import Box3D
from .visibility import FloorFitConfig, fit_floor_plane, heights_above_plane


@dataclass(frozen=True)
class BaselineConfig:
    roi_min_xyz: tuple[float, float, float] = (1.2, -0.8, -1.5)
    roi_max_xyz: tuple[float, float, float] = (6.0, 0.8, 1.0)
    object_height_range_m: tuple[float, float] = (0.025, 0.35)
    range_cluster_eps_m: tuple[tuple[float, float, float], ...] = (
        (1.2, 2.25, 0.08),
        (2.25, 4.0, 0.10),
        (4.0, 6.01, 0.15),
    )
    min_points: int = 3
    diameter_range_m: tuple[float, float] = (0.02, 0.35)
    max_vertical_extent_m: float = 0.30
    merge_distance_m: float = 0.25
    floor_fit: FloorFitConfig = FloorFitConfig()


def filter_roi_and_ground(
    points: np.ndarray, config: BaselineConfig
) -> tuple[np.ndarray, np.ndarray]:
    """Return low objects in the ROI and the fitted floor coefficients."""
    xyz = points[:, :3]
    finite = np.isfinite(xyz).all(axis=1)
    roi = finite & (xyz >= np.asarray(config.roi_min_xyz)).all(axis=1)
    roi &= (xyz <= np.asarray(config.roi_max_xyz)).all(axis=1)
    floor = fit_floor_plane(points, config.floor_fit)
    height = heights_above_plane(points, floor)
    roi &= height >= config.object_height_range_m[0]
    roi &= height <= config.object_height_range_m[1]
    return points[roi], floor


def euclidean_clusters(xyz: np.ndarray, eps_m: float, min_points: int) -> list[np.ndarray]:
    """Deterministic Euclidean connected components using a spatial hash."""
    if eps_m <= 0:
        raise ValueError("eps_m must be positive")
    if min_points <= 0:
        raise ValueError("min_points must be positive")
    if len(xyz) == 0:
        return []

    cells = np.floor(np.asarray(xyz, dtype=np.float64) / eps_m).astype(np.int64)
    cell_members: dict[tuple[int, int, int], list[int]] = {}
    for index, cell in enumerate(cells):
        cell_members.setdefault(tuple(cell), []).append(index)
    neighbor_offsets = list(product((-1, 0, 1), repeat=3))
    visited = np.zeros(len(xyz), dtype=bool)
    clusters: list[np.ndarray] = []
    eps_squared = eps_m**2

    for start in range(len(xyz)):
        if visited[start]:
            continue
        visited[start] = True
        stack = [start]
        component: list[int] = []
        while stack:
            current = stack.pop()
            component.append(current)
            cell = cells[current]
            candidates: list[int] = []
            for offset in neighbor_offsets:
                candidates.extend(cell_members.get(tuple(cell + offset), ()))
            for neighbor in sorted(candidates):
                if visited[neighbor]:
                    continue
                delta = xyz[current] - xyz[neighbor]
                if float(delta @ delta) <= eps_squared:
                    visited[neighbor] = True
                    stack.append(neighbor)
        if len(component) >= min_points:
            clusters.append(np.asarray(sorted(component), dtype=np.int64))
    return clusters


def detect_ball_candidates(
    points: np.ndarray, config: BaselineConfig = BaselineConfig()
) -> list[Box3D]:
    filtered, floor = filter_roi_and_ground(points, config)
    candidates: list[Box3D] = []
    for range_min, range_max, eps_m in config.range_cluster_eps_m:
        in_range = (filtered[:, 0] >= range_min) & (filtered[:, 0] < range_max)
        range_points = filtered[in_range]
        for indices in euclidean_clusters(range_points[:, :3], eps_m, config.min_points):
            cluster = range_points[indices, :3]
            extent = np.ptp(cluster, axis=0)
            horizontal_diameter = float(np.linalg.norm(extent[:2]))
            if not config.diameter_range_m[0] <= horizontal_diameter <= config.diameter_range_m[1]:
                continue
            if extent[2] > config.max_vertical_extent_m:
                continue
            center = np.mean(cluster, axis=0)
            floor_z = floor[0] * center[0] + floor[1] * center[1] + floor[2]
            center[2] = floor_z + 0.11
            candidates.append(
                Box3D(
                    "ball",
                    tuple(float(value) for value in center),
                    (0.22, 0.22, 0.22),
                    0.0,
                    {
                        "num_points": int(len(cluster)),
                        "observed_extent_xyz_m": [float(value) for value in extent],
                        "cluster_eps_m": eps_m,
                        "source": "geometric_baseline",
                    },
                )
            )
    return _merge_nearby_candidates(candidates, config.merge_distance_m)


def _merge_nearby_candidates(candidates: list[Box3D], distance_m: float) -> list[Box3D]:
    kept: list[Box3D] = []
    ordered = sorted(candidates, key=lambda item: int(item.attributes["num_points"]), reverse=True)
    for candidate in ordered:
        center = np.asarray(candidate.center_xyz[:2])
        if any(np.linalg.norm(center - np.asarray(other.center_xyz[:2])) <= distance_m for other in kept):
            continue
        kept.append(candidate)
    return sorted(kept, key=lambda item: item.center_xyz)
