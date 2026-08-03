#!/bin/bash
set -e

source /opt/ros/foxy/setup.bash
# The Unitree host uses rmw_cyclonedds_cpp 0.7.11 rebuilt against Cyclone DDS
# 0.10.2. Keep this overlay ahead of the Foxy package linked to Cyclone 0.7.0.
export AMENT_PREFIX_PATH="/opt/rmw-cyclonedds-0.7.11:${AMENT_PREFIX_PATH}"
export LD_LIBRARY_PATH="/opt/rmw-cyclonedds-0.7.11/lib:/opt/cyclonedds-0.10.2/lib:${LD_LIBRARY_PATH}"
# pip installs the ament_python package and its resource index under
# /usr/local. Make that prefix visible to `ros2 run` and `ros2 launch`.
export AMENT_PREFIX_PATH="/usr/local:${AMENT_PREFIX_PATH}"
exec "$@"
