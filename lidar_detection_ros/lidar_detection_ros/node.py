"""ROS 2 node for PointPillars inference on Unitree/Livox point clouds."""

from __future__ import annotations

from pathlib import Path
import json

import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import PointCloud2
from std_msgs.msg import String
from visualization_msgs.msg import MarkerArray

from lidar_detection_ros.backends import MMDetection3DBackend
from lidar_detection_ros.messages import detection_payload, marker_array_message
from lidar_detection_ros.pointcloud_adapter import pointcloud2_to_model_array


class LidarDetectionNode(Node):
    def __init__(self) -> None:
        super().__init__("lidar_detection")
        self.declare_parameter("model_path", "")
        self.declare_parameter("config_path", "")
        self.declare_parameter("input_topic", "/utlidar/cloud_livox_mid360")
        self.declare_parameter("json_topic", "/lidar/detections_json")
        self.declare_parameter("marker_topic", "/lidar/detection_markers")
        self.declare_parameter("corrected_frame", "lidar_corrected")
        self.declare_parameter("device", "cuda:0")
        self.declare_parameter("score_threshold", 0.10)
        self.declare_parameter("correct_upside_down", True)

        model_path = Path(str(self.get_parameter("model_path").value))
        config_path = Path(str(self.get_parameter("config_path").value))
        if not model_path.is_file():
            raise ValueError("model_path must point to a readable .pth checkpoint")
        if not config_path.is_file():
            raise ValueError("config_path must point to the packaged MMDetection3D config.py")

        self._correct_upside_down = bool(self.get_parameter("correct_upside_down").value)
        self._corrected_frame = str(self.get_parameter("corrected_frame").value)
        self._backend = MMDetection3DBackend(
            config_path=config_path,
            checkpoint_path=model_path,
            device=str(self.get_parameter("device").value),
            class_names=("ball",),
            score_threshold=float(self.get_parameter("score_threshold").value),
            fixed_box_sizes={"ball": (0.22, 0.22, 0.22)},
        )

        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.BEST_EFFORT,
        )
        json_topic = str(self.get_parameter("json_topic").value)
        marker_topic = str(self.get_parameter("marker_topic").value)
        input_topic = str(self.get_parameter("input_topic").value)
        self._json_publisher = self.create_publisher(String, json_topic, 10)
        self._marker_publisher = self.create_publisher(MarkerArray, marker_topic, 10)
        self._subscription = self.create_subscription(PointCloud2, input_topic, self._on_cloud, qos)
        self.get_logger().info(
            f"Listening on {input_topic}; publishing JSON on {json_topic} and markers on {marker_topic}"
        )

    def _on_cloud(self, message: PointCloud2) -> None:
        try:
            points = pointcloud2_to_model_array(
                message, correct_upside_down=self._correct_upside_down
            )
            detections = self._backend.predict(points)
            payload = detection_payload(
                detections,
                source_header=message.header,
                corrected_frame=self._corrected_frame,
                correct_upside_down=self._correct_upside_down,
            )
            json_message = String()
            json_message.data = json.dumps(payload, separators=(",", ":"), sort_keys=True)
            markers = marker_array_message(
                detections,
                source_header=message.header,
                correct_upside_down=self._correct_upside_down,
            )
            self._json_publisher.publish(json_message)
            self._marker_publisher.publish(markers)
        except Exception as exc:  # keep the ROS executor alive on a malformed frame
            self.get_logger().error(f"LiDAR inference failed: {exc}")


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = LidarDetectionNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
