import numpy as np

from lidar_training.geometry import points_in_oriented_box
from lidar_training.measurements import measure_box_returns
from lidar_training.types import Box3D


def test_points_in_rotated_box_and_measurement() -> None:
    points = np.array([[0.0, 0.0, 0.0, 10.0], [0.09, 0.0, 0.0, 20.0], [1.0, 1.0, 1.0, 99.0]])
    box = Box3D("ball", (0.0, 0.0, 0.0), (0.22, 0.22, 0.22), yaw=0.4)
    assert points_in_oriented_box(points, box).tolist() == [True, True, False]
    result = measure_box_returns(points, box)
    assert result.num_points == 2
    assert result.intensity_mean == 15.0
