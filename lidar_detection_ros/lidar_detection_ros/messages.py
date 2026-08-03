"""JSON and RViz/Foxglove visualization outputs."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from lidar_detection_ros.types import Detection3D


def detection_payload(
    detections: Iterable[Detection3D],
    *,
    source_header: Any,
    corrected_frame: str,
    correct_upside_down: bool,
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
    return {
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


def marker_array_message(
    detections: Iterable[Detection3D],
    *,
    source_header: Any,
    correct_upside_down: bool,
) -> Any:
    """Create red 3D boxes in the original cloud frame for direct overlay."""

    try:
        from visualization_msgs.msg import Marker, MarkerArray
    except ImportError as exc:  # pragma: no cover - requires ROS
        raise RuntimeError("visualization_msgs is required to publish detection markers") from exc

    output = MarkerArray()
    clear = Marker()
    clear.action = Marker.DELETEALL
    output.markers.append(clear)

    for index, detection in enumerate(detections):
        marker = Marker()
        marker.header = source_header
        marker.ns = "lidar_detection_boxes"
        marker.id = index
        marker.type = Marker.CUBE
        marker.action = Marker.ADD
        marker.pose.position.x = detection.x
        marker.pose.position.y = -detection.y if correct_upside_down else detection.y
        marker.pose.position.z = -detection.z if correct_upside_down else detection.z
        # The pilot class is spherical, so its orientation is intentionally identity.
        marker.pose.orientation.w = 1.0
        marker.scale.x = detection.length
        marker.scale.y = detection.width
        marker.scale.z = detection.height
        marker.color.r = 1.0
        marker.color.g = 0.0
        marker.color.b = 0.0
        marker.color.a = 0.45
        output.markers.append(marker)
    return output
