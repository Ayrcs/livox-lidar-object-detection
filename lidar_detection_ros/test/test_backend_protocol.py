import numpy as np
import pytest

from lidar_detection_ros.backends import FakeBackend, assert_backend
from lidar_detection_ros.types import Detection3D


def test_fake_backend_is_deterministic_and_tracks_calls() -> None:
    expected = Detection3D(0, "ball", 0.9, 2.0, 0.1, -1.0, 0.22, 0.22, 0.22, 0.0)
    backend = FakeBackend([expected])
    assert assert_backend(backend) is backend

    cloud = np.zeros((12, 4), dtype=np.float32)
    assert backend.predict(cloud) == [expected]
    assert backend.predict(cloud) == [expected]
    assert backend.calls == 2
    assert backend.last_point_count == 12


def test_backend_guard_rejects_missing_predict() -> None:
    with pytest.raises(TypeError, match="predict"):
        assert_backend(object())  # type: ignore[arg-type]
