# Lightweight application layer. The heavyweight CUDA/MMDetection runtime is
# built once from inference-jetson-base.Dockerfile and then kept stable.
ARG BASE_IMAGE=lidar-detection-jetson-runtime:0.2.0
FROM ${BASE_IMAGE}

WORKDIR /opt/lidar_detection
COPY lidar_detection_ros lidar_detection_ros
# pip places console entry points in /usr/local/bin, while ROS 2 Foxy resolves
# node executables from the package-specific libexec directory.
RUN python3 -m pip install --no-cache-dir --no-deps --force-reinstall ./lidar_detection_ros \
    && mkdir -p /usr/local/lib/lidar_detection_ros \
    && ln -sf \
        /usr/local/bin/lidar_detection_node \
        /usr/local/lib/lidar_detection_ros/lidar_detection_node

COPY docker/ros_entrypoint.sh /ros_entrypoint.sh
RUN chmod 0755 /ros_entrypoint.sh
ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["ros2", "run", "lidar_detection_ros", "lidar_detection_node"]
