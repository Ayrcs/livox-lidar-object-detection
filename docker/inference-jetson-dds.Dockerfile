# Unitree-compatible DDS layer. It is separate from the heavyweight CUDA/MMCV
# base so upgrading Cyclone DDS never recompiles MMDetection3D.
ARG HEAVY_BASE_IMAGE=lidar-detection-jetson-base:0.1.0
FROM ${HEAVY_BASE_IMAGE}

ARG CYCLONEDDS_VERSION=0.10.2
ARG RMW_CYCLONEDDS_COMMIT=c12abc56983204f1d91f2d839d394528c7b29b42

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN git clone --depth 1 --branch "${CYCLONEDDS_VERSION}" \
        https://github.com/eclipse-cyclonedds/cyclonedds.git /tmp/cyclonedds \
    && cmake -S /tmp/cyclonedds -B /tmp/cyclonedds/build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/opt/cyclonedds-0.10.2 \
        -DBUILD_EXAMPLES=OFF \
        -DBUILD_TESTING=OFF \
    && cmake --build /tmp/cyclonedds/build --parallel 4 \
    && cmake --install /tmp/cyclonedds/build \
    && git clone https://github.com/ros2/rmw_cyclonedds.git /tmp/rmw_cyclonedds \
    && git -C /tmp/rmw_cyclonedds checkout "${RMW_CYCLONEDDS_COMMIT}" \
    && source /opt/ros/foxy/setup.bash \
    && cmake \
        -S /tmp/rmw_cyclonedds/rmw_cyclonedds_cpp \
        -B /tmp/rmw_cyclonedds/build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/opt/rmw-cyclonedds-0.7.11 \
        -DCMAKE_PREFIX_PATH="/opt/cyclonedds-0.10.2:${CMAKE_PREFIX_PATH}" \
        -DBUILD_TESTING=OFF \
    && cmake --build /tmp/rmw_cyclonedds/build --parallel 4 \
    && cmake --install /tmp/rmw_cyclonedds/build \
    && rm -rf /tmp/cyclonedds /tmp/rmw_cyclonedds

COPY docker/cyclonedds-unitree.xml /etc/cyclonedds-unitree.xml

ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
    CYCLONEDDS_URI=/etc/cyclonedds-unitree.xml
