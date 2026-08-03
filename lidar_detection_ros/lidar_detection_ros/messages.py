"""Conversion from framework-independent detections to vision_msgs."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from lidar_detection_ros.types import Detection3D


def detection_array_message(
    detections: Iterable[Detection3D],
    *,
    source_header: Any,
    output_frame: str,
) -> Any:
    """Build a Foxy/newer-compatible vision_msgs Detection3DArray."""

    try:
        from vision_msgs.msg import Detection3D as Detection3DMessage
        from vision_msgs.msg import Detection3DArray, ObjectHypothesisWithPose
    except ImportError as exc:  # pragma: no cover - requires ROS
        raise RuntimeError("vision_msgs is required to publish 3D detections") from exc

    output = Detection3DArray()
    output.header.stamp = source_header.stamp
    output.header.frame_id = output_frame
    for index, detection in enumerate(detections):
        message = Detection3DMessage()
        message.header = output.header
        message.id = str(index)
        message.bbox.center.position.x = detection.x
        message.bbox.center.position.y = detection.y
        message.bbox.center.position.z = detection.z
        half_yaw = detection.yaw / 2.0
        from math import cos, sin

        message.bbox.center.orientation.z = sin(half_yaw)
        message.bbox.center.orientation.w = cos(half_yaw)
        message.bbox.size.x = detection.length
        message.bbox.size.y = detection.width
        message.bbox.size.z = detection.height

        hypothesis = ObjectHypothesisWithPose()
        # vision_msgs changed numeric `id` to string `class_id` after Foxy.
        if hasattr(hypothesis.hypothesis, "class_id"):
            hypothesis.hypothesis.class_id = detection.class_name
        else:
            hypothesis.hypothesis.id = detection.class_id
        hypothesis.hypothesis.score = detection.score
        hypothesis.pose.pose = message.bbox.center
        message.results.append(hypothesis)
        output.detections.append(message)
    return output
