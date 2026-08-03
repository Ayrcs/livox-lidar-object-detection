import numpy as np
import pytest

from lidar_training.baseline import BaselineConfig, detect_ball_candidates, euclidean_clusters
from lidar_training.visibility import FloorFitConfig


def test_deterministic_ball_candidate() -> None:
    x, y = np.meshgrid(np.linspace(0.5, 3.0, 20), np.linspace(-0.5, 0.5, 10))
    floor = np.column_stack((x.ravel(), y.ravel(), np.full(x.size, -1.2), np.zeros(x.size)))
    cluster = np.array([[1.42, 0.00, -1.10, 20], [1.50, 0.00, -1.04, 30], [1.58, 0.00, -1.10, 25]])
    config = BaselineConfig(
        range_cluster_eps_m=((1.2, 2.0, 0.11),),
        floor_fit=FloorFitConfig(z_range_m=(-1.3, -1.1)),
    )
    detections = detect_ball_candidates(np.vstack((floor, cluster)), config)
    assert len(detections) == 1
    assert detections[0].attributes["num_points"] == 3
    assert detections[0].center_xyz[2] == pytest.approx(-1.09)


def test_spatial_hash_keeps_clusters_separate() -> None:
    xyz = np.array([[0, 0, 0], [0.05, 0, 0], [0.1, 0, 0], [1, 1, 1], [1.05, 1, 1], [1.1, 1, 1]])
    clusters = euclidean_clusters(xyz, eps_m=0.06, min_points=3)
    assert [cluster.tolist() for cluster in clusters] == [[0, 1, 2], [3, 4, 5]]
