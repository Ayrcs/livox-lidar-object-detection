# Stable heavyweight runtime for JetPack 5 / L4T R35. Rebuild this image only
# when ROS, PyTorch, MMCV or MMDetection3D versions change.
FROM nvcr.io/nvidia/l4t-pytorch:r35.2.1-pth2.0-py3

ARG DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

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

ENV TORCH_CUDA_ARCH_LIST=8.7 \
    FORCE_CUDA=1 \
    MAX_JOBS=4
RUN python3 -m pip install --no-cache-dir --upgrade "pip<25" \
    && python3 -m pip install --no-cache-dir --ignore-installed "PyYAML>=6,<7" \
    && python3 -m pip install --no-cache-dir \
        "numpy<2" \
        openmim==0.3.9 \
        mmengine==0.10.7 \
        mmdet==3.2.0 \
    && mim install mmcv==2.1.0 \
    && python3 -m pip install --no-cache-dir mmdet3d==1.4.0
