from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    arguments = [
        DeclareLaunchArgument("model_path"),
        DeclareLaunchArgument("config_path", default_value=""),
        DeclareLaunchArgument("input_topic", default_value="/utlidar/cloud_livox_mid360"),
        DeclareLaunchArgument("json_topic", default_value="/lidar/detections_json"),
        DeclareLaunchArgument("marker_topic", default_value="/lidar/detection_markers"),
        DeclareLaunchArgument("diagnostics_topic", default_value="/diagnostics"),
        DeclareLaunchArgument("corrected_frame", default_value="lidar_corrected"),
        DeclareLaunchArgument("device", default_value="cuda:0"),
        DeclareLaunchArgument("score_threshold", default_value="0.10"),
    ]
    node = Node(
        package="lidar_detection_ros",
        executable="lidar_detection_node",
        name="lidar_detection",
        output="screen",
        parameters=[
            {
                "model_path": LaunchConfiguration("model_path"),
                "config_path": LaunchConfiguration("config_path"),
                "input_topic": LaunchConfiguration("input_topic"),
                "json_topic": LaunchConfiguration("json_topic"),
                "marker_topic": LaunchConfiguration("marker_topic"),
                "diagnostics_topic": LaunchConfiguration("diagnostics_topic"),
                "corrected_frame": LaunchConfiguration("corrected_frame"),
                "device": LaunchConfiguration("device"),
                "score_threshold": LaunchConfiguration("score_threshold"),
            }
        ],
    )
    return LaunchDescription(arguments + [node])
