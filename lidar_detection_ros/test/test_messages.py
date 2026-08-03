from types import SimpleNamespace

from lidar_detection_ros.messages import (
    BOX_EDGE_INDICES,
    axis_aligned_box_corners,
    detection_label,
    detection_payload,
)
from lidar_detection_ros.types import Detection3D


def test_json_payload_exposes_corrected_and_source_coordinates() -> None:
    header = SimpleNamespace(
        stamp=SimpleNamespace(sec=12, nanosec=34),
        frame_id="livox_frame",
    )
    detection = Detection3D(
        class_id=0,
        class_name="ball",
        score=0.8,
        x=4.9,
        y=0.36,
        z=-1.21,
        length=0.22,
        width=0.22,
        height=0.22,
        yaw=0.0,
    )

    payload = detection_payload(
        [detection],
        source_header=header,
        corrected_frame="lidar_corrected",
        correct_upside_down=True,
        point_count=20042,
        processing_ms=42.5,
        received_frames=100,
        dropped_frames=3,
    )

    assert payload["stamp"] == {"sec": 12, "nanosec": 34}
    assert payload["coordinate_convention"] == "x_forward_y_left_z_up"
    assert payload["point_count"] == 20042
    assert payload["processing_ms"] == 42.5
    assert payload["received_frames"] == 100
    assert payload["dropped_frames"] == 3
    assert payload["detections"][0]["y"] == 0.36
    assert payload["detections"][0]["source_frame_position"] == {
        "x": 4.9,
        "y": -0.36,
        "z": 1.21,
    }


def test_wireframe_geometry_and_label() -> None:
    detection = Detection3D(
        class_id=0,
        class_name="ball",
        score=0.204,
        x=4.96,
        y=0.36,
        z=-1.21,
        length=0.22,
        width=0.22,
        height=0.22,
        yaw=0.0,
    )
    corners = axis_aligned_box_corners(
        center=(detection.x, detection.y, detection.z),
        size=(detection.length, detection.width, detection.height),
    )
    assert len(corners) == 8
    assert len(BOX_EDGE_INDICES) == 12
    for start, end in BOX_EDGE_INDICES:
        differing_axes = sum(a != b for a, b in zip(corners[start], corners[end]))
        assert differing_axes == 1
    assert detection_label(detection) == "ball 0.20 | 4.97 m"
