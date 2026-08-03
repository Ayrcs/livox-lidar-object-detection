# Jetson PyTorch 2.0 image for JetPack 5 / L4T R35.
FROM nvcr.io/nvidia/l4t-pytorch:r35.2.1-pth2.0-py3

ARG DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# ROS 2 Foxy matches the Unitree G1 host. The container communicates with the
# host DDS graph through --network host; no ROS installation is modified on the robot.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg2 \
        build-essential \
        git \
        ninja-build \
        python3-dev \
        python3-pip \
    && curl -fsSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
        -o /usr/share/keyrings/ros-archive-keyring.gpg \
    && echo "deb [arch=arm64 signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu focal main" \
        > /etc/apt/sources.list.d/ros2.list \
    && apt-get update && apt-get install -y --no-install-recommends \
        ros-foxy-ros-base \
        ros-foxy-rmw-cyclonedds-cpp \
        ros-foxy-diagnostic-msgs \
        ros-foxy-sensor-msgs \
        ros-foxy-std-msgs \
        ros-foxy-visualization-msgs \
    && rm -rf /var/lib/apt/lists/*

# Match the training framework versions. MMCV and MMDetection3D compile their
# CUDA extensions for the Orin (compute capability 8.7) during this image build.
ENV TORCH_CUDA_ARCH_LIST=8.7 \
    FORCE_CUDA=1 \
    MAX_JOBS=4
# NVIDIA's base image provides PyYAML 5.3.1 through distutils. pip cannot
# uninstall that legacy package, so install the required wheel over it.
RUN python3 -m pip install --no-cache-dir --upgrade "pip<25" \
    && python3 -m pip install --no-cache-dir --ignore-installed "PyYAML>=6,<7" \
    && python3 -m pip install --no-cache-dir \
        "numpy<2" \
        openmim==0.3.9 \
        mmengine==0.10.7 \
        mmdet==3.2.0 \
    && mim install mmcv==2.1.0 \
    && python3 -m pip install --no-cache-dir mmdet3d==1.4.0

WORKDIR /opt/lidar_detection
COPY lidar_detection_ros lidar_detection_ros
RUN python3 -m pip install --no-cache-dir --no-deps ./lidar_detection_ros

COPY docker/ros_entrypoint.sh /ros_entrypoint.sh
RUN chmod 0755 /ros_entrypoint.sh
ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["ros2", "run", "lidar_detection_ros", "lidar_detection_node"]
