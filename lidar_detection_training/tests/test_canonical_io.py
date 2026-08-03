import json

import numpy as np

from lidar_training.canonical_io import load_canonical_sample, write_canonical_sample


def test_canonical_sample_is_deterministic(tmp_path) -> None:
    points = np.array([[1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12]], dtype=np.float32)
    metadata = {
        "session_id": "session_a",
        "header_timestamp_ns": 123,
        "bag_timestamp_ns": 456,
        "frame_id": "lidar_corrected",
    }
    first = write_canonical_sample(tmp_path / "first", "sample_a", points, metadata)
    second = write_canonical_sample(tmp_path / "second", "sample_a", points, metadata)
    assert first["points_sha256"] == second["points_sha256"]
    assert first["metadata_sha256"] == second["metadata_sha256"]
    sample = load_canonical_sample(tmp_path / "first", "sample_a")
    np.testing.assert_array_equal(sample.points, points)
    assert sample.frame_id == "lidar_corrected"
    payload = json.loads((tmp_path / "first/metadata/sample_a.json").read_text())
    assert payload["point_fields"] == ["x", "y", "z", "intensity", "ring", "time"]
