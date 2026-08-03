#!/bin/bash
set -e

source /opt/ros/foxy/setup.bash
# pip installs the ament_python package and its resource index under
# /usr/local. Make that prefix visible to `ros2 run` and `ros2 launch`.
export AMENT_PREFIX_PATH="/usr/local:${AMENT_PREFIX_PATH}"
exec "$@"
