import numpy as np
from numpy.typing import NDArray

from .types import Box3D


def points_in_oriented_box(points: NDArray[np.floating], box: Box3D) -> NDArray[np.bool_]:
    """Return a mask for points inside a Z-axis-oriented 3D box."""
    xyz = np.asarray(points[:, :3], dtype=np.float64)
    centered = xyz - np.asarray(box.center_xyz)
    cosine, sine = np.cos(box.yaw), np.sin(box.yaw)
    local_x = cosine * centered[:, 0] + sine * centered[:, 1]
    local_y = -sine * centered[:, 0] + cosine * centered[:, 1]
    half = np.asarray(box.size_lwh) / 2.0
    return (
        (np.abs(local_x) <= half[0])
        & (np.abs(local_y) <= half[1])
        & (np.abs(centered[:, 2]) <= half[2])
    )
