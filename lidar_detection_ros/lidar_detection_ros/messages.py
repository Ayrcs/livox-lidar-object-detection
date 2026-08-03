"""JSON and RViz/Foxglove visualization outputs."""

from __future__ import annotations

from collections.abc import Iterable
from math import hypot
from typing import Any, Optional

from lidar_detection_ros.types import Detection3D


BOX_EDGE_INDICES = (
    (0, 1), (1, 2), (2, 3), (3, 0),
    (4, 5), (5, 6), (6, 7), (7, 4),
    (0, 4), (1, 5), (2, 6), (3, 7),
)


def axis_aligned_box_corners(
    *, center: tuple[float, float, float], size: tuple[float, float, float]
) -> list[tuple[float, float, float]]:
    half_x, half_y, half_z = (value / 2.0 for value in size)
    center_x, center_y, center_z = center
    return [
        (center_x - half_x, center_y - half_y, center_z - half_z),
        (center_x + half_x, center_y - half_y, center_z - half_z),
        (center_x + half_x, center_y + half_y, center_z - half_z),
        (center_x - half_x, center_y + half_y, center_z - half_z),
        (center_x - half_x, center_y - half_y, center_z + half_z),
        (center_x + half_x, center_y - half_y, center_z + half_z),
        (center_x + half_x, center_y + half_y, center_z + half_z),
        (center_x - half_x, center_y + half_y, center_z + half_z),
    ]


def detection_label(detection: Detection3D) -> str:
    distance = hypot(detection.x, detection.y)
    return f"{detection.class_name} {detection.score:.2f} | {distance:.2f} m"


def detection_payload(
    detections: Iterable[Detection3D],
    *,
    source_header: Any,
    corrected_frame: str,
    correct_upside_down: bool,
    point_count: Optional[int] = None,
    processing_ms: Optional[float] = None,
    received_frames: Optional[int] = None,
    dropped_frames: Optional[int] = None,
) -> dict[str, Any]:
    """Build the stable, framework-independent JSON structure."""

    items = []
    for detection in detections:
        item = detection.to_dict()
        item["frame_id"] = corrected_frame
        item["source_frame_position"] = {
            "x": detection.x,
            "y": -detection.y if correct_upside_down else detection.y,
            "z": -detection.z if correct_upside_down else detection.z,
        }
        items.append(item)
    payload = {
        "schema_version": 1,
        "stamp": {
            "sec": int(source_header.stamp.sec),
            "nanosec": int(source_header.stamp.nanosec),
        },
        "source_frame_id": str(source_header.frame_id),
        "coordinate_frame_id": corrected_frame,
        "coordinate_convention": "x_forward_y_left_z_up",
        "detections": items,
    }
    if point_count is not None:
        payload["point_count"] = int(point_count)
    if processing_ms is not None:
        payload["processing_ms"] = float(processing_ms)
    if received_frames is not None:
        payload["received_frames"] = int(received_frames)
    if dropped_frames is not None:
        payload["dropped_frames"] = int(dropped_frames)
    return payload


def marker_array_message(
    detections: Iterable[Detection3D],
    *,
    source_header: Any,
    correct_upside_down: bool,
) -> Any:
    """Create red 3D boxes in the original cloud frame for direct overlay."""

    try:
        from geometry_msgs.msg import Point
        from visualization_msgs.msg import Marker, MarkerArray
    except ImportError as exc:  # pragma: no cover - requires ROS
        raise RuntimeError("visualization_msgs is required to publish detection markers") from exc

    output = MarkerArray()
    clear = Marker()
    clear.action = Marker.DELETEALL
    output.markers.append(clear)

    for index, detection in enumerate(detections):
        center = (
            detection.x,
            -detection.y if correct_upside_down else detection.y,
            -detection.z if correct_upside_down else detection.z,
        )
        marker = Marker()
        marker.header = source_header
        marker.ns = "lidar_detection_boxes"
        marker.id = index * 2
        marker.type = Marker.LINE_LIST
        marker.action = Marker.ADD
        marker.pose.orientation.w = 1.0
        marker.scale.x = 0.025
        marker.color.r = 1.0
        marker.color.g = 0.0
        marker.color.b = 0.0
        marker.color.a = 1.0
        corners = axis_aligned_box_corners(
            center=center,
            size=(detection.length, detection.width, detection.height),
        )
        for start, end in BOX_EDGE_INDICES:
            for corner_index in (start, end):
                x, y, z = corners[corner_index]
                marker.points.append(Point(x=x, y=y, z=z))
        output.markers.append(marker)

        label = Marker()
        label.header = source_header
        label.ns = "lidar_detection_labels"
        label.id = index * 2 + 1
        label.type = Marker.TEXT_VIEW_FACING
        label.action = Marker.ADD
        label.pose.position.x = center[0]
        label.pose.position.y = center[1]
        label.pose.position.z = center[2] + detection.height / 2.0 + 0.12
        label.pose.orientation.w = 1.0
        label.scale.z = 0.14
        label.color.r = 1.0
        label.color.g = 0.15
        label.color.b = 0.15
        label.color.a = 1.0
        label.text = detection_label(detection)
        output.markers.append(label)
    return output
