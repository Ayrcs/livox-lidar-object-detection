from types import SimpleNamespace

import numpy as np

from lidar_detection_ros.backends.mmdet3d_backend import detections_from_result


def test_normalizes_filters_and_fixes_ball_box() -> None:
    boxes = SimpleNamespace(
        tensor=np.array(
            [
                [1.5, -0.2, -1.1, 0.30, 0.19, 0.25, 1.2],
                [3.0, 0.1, -1.1, 0.20, 0.20, 0.20, -0.4],
            ],
            dtype=np.float32,
        )
    )
    result = {
        "pred_instances_3d": {
            "bboxes_3d": boxes,
            "scores_3d": np.array([0.91, 0.05], dtype=np.float32),
            "labels_3d": np.array([0, 0], dtype=np.int64),
        }
    }

    detections = detections_from_result(
        result,
        class_names=("ball",),
        score_threshold=0.10,
        fixed_box_sizes={"ball": (0.22, 0.22, 0.22)},
    )

    assert len(detections) == 1
    detection = detections[0]
    assert detection.class_name == "ball"
    assert detection.score == np.float32(0.91)
    assert (detection.length, detection.width, detection.height) == (0.22, 0.22, 0.22)
    assert detection.yaw == 0.0


def test_accepts_tuple_and_object_result() -> None:
    instances = SimpleNamespace(
        bboxes_3d=np.array([[2.0, 0.0, -1.0, 0.2, 0.2, 0.2, 0.0]], dtype=np.float32),
        scores_3d=np.array([0.8], dtype=np.float32),
        labels_3d=np.array([0], dtype=np.int64),
    )
    sample = SimpleNamespace(pred_instances_3d=instances)

    detections = detections_from_result(
        ([sample], {"unused": True}),
        class_names=("ball",),
        score_threshold=0.5,
    )

    assert len(detections) == 1
    assert detections[0].x == 2.0
