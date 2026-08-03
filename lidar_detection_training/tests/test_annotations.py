from lidar_training.annotations import difficulty_from_points, validate_annotation


def test_difficulty_thresholds() -> None:
    assert difficulty_from_points(0) == "hard"
    assert difficulty_from_points(2) == "hard"
    assert difficulty_from_points(3) == "medium"
    assert difficulty_from_points(9) == "medium"
    assert difficulty_from_points(10) == "easy"


def test_annotation_validation() -> None:
    payload = {
        "schema_version": 1,
        "sample_id": "sample",
        "frame_id": "lidar_corrected",
        "review_status": "unreviewed",
        "boxes": [
            {
                "annotation_id": "sample_ball_0",
                "class_name": "ball",
                "center_xyz": [1.0, 0.0, 0.1],
                "size_lwh": [0.22, 0.22, 0.22],
                "yaw": 0.0,
                "review_status": "unreviewed",
                "attributes": {
                    "difficulty": "medium",
                    "num_points": 4,
                    "num_points_in_box": 6,
                },
            }
        ],
    }
    assert validate_annotation(payload) == []
    payload["boxes"][0]["yaw"] = 1.0
    assert "boxes[0]: ball yaw must be zero" in validate_annotation(payload)


def test_annotation_rejects_inconsistent_point_counts() -> None:
    payload = {
        "schema_version": 1,
        "sample_id": "sample",
        "frame_id": "lidar_corrected",
        "review_status": "unreviewed",
        "boxes": [
            {
                "annotation_id": "sample_ball_0",
                "class_name": "ball",
                "center_xyz": [1.0, 0.0, 0.1],
                "size_lwh": [0.22, 0.22, 0.22],
                "yaw": 0.0,
                "review_status": "unreviewed",
                "attributes": {
                    "difficulty": "medium",
                    "num_points": 7,
                    "num_points_in_box": 6,
                },
            }
        ],
    }
    assert "boxes[0]: num_points cannot exceed num_points_in_box" in validate_annotation(payload)
