"""Framework-independent inference backend contract."""

from __future__ import annotations

from typing import Protocol

import numpy as np

from lidar_detection_ros.types import Detection3D


class DetectorBackend(Protocol):
    def predict(self, points: np.ndarray) -> list[Detection3D]:
        """Return detections in the corrected model coordinate frame."""


def assert_backend(backend: DetectorBackend) -> DetectorBackend:
    """Type-checking helper that also provides a simple runtime guard."""

    if not callable(getattr(backend, "predict", None)):
        raise TypeError("detector backend must provide a callable predict(points) method")
    return backend
