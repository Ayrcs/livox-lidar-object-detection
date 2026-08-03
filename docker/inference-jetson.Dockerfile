# Lightweight application layer. The heavyweight CUDA/MMDetection runtime is
# built once from inference-jetson-base.Dockerfile and then kept stable.
ARG BASE_IMAGE=lidar-detection-jetson-base:0.1.0
FROM ${BASE_IMAGE}

WORKDIR /opt/lidar_detection
COPY lidar_detection_ros lidar_detection_ros
RUN python3 -m pip install --no-cache-dir --no-deps --force-reinstall ./lidar_detection_ros

COPY docker/ros_entrypoint.sh /ros_entrypoint.sh
RUN chmod 0755 /ros_entrypoint.sh
ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["ros2", "run", "lidar_detection_ros", "lidar_detection_node"]
