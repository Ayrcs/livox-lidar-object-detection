"""Deterministic backend for tests and ROS integration checks without CUDA."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from lidar_detection_ros.types import Detection3D


class FakeBackend:
    def __init__(self, detections: Sequence[Detection3D] = ()) -> None:
        self._detections = tuple(detections)
        self.calls = 0
        self.last_point_count = 0

    def predict(self, points: np.ndarray) -> list[Detection3D]:
        cloud = np.asarray(points)
        if cloud.ndim != 2 or cloud.shape[1] != 4:
            raise ValueError(f"Expected point cloud with shape (N, 4), received {cloud.shape}")
        self.calls += 1
        self.last_point_count = len(cloud)
        return list(self._detections)
