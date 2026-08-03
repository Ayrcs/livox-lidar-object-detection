#!/bin/bash
set -euo pipefail

BASE_TAG="lidar-detection-jetson-base:0.1.0"
DDS_RUNTIME_TAG="lidar-detection-jetson-runtime:0.2.0"
APP_TAG="lidar-detection-jetson:0.2.0"
REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPOSITORY_ROOT"

if ! docker image inspect "$BASE_TAG" >/dev/null 2>&1; then
  echo "Building heavyweight Jetson runtime once: $BASE_TAG"
  docker build \
    --network host \
    -f docker/inference-jetson-base.Dockerfile \
    -t "$BASE_TAG" \
    .
else
  echo "Reusing heavyweight Jetson runtime: $BASE_TAG"
fi

if ! docker image inspect "$DDS_RUNTIME_TAG" >/dev/null 2>&1; then
  echo "Building Unitree-compatible Cyclone DDS runtime: $DDS_RUNTIME_TAG"
  docker build \
    --network host \
    --build-arg "HEAVY_BASE_IMAGE=$BASE_TAG" \
    -f docker/inference-jetson-dds.Dockerfile \
    -t "$DDS_RUNTIME_TAG" \
    .
else
  echo "Reusing Unitree-compatible DDS runtime: $DDS_RUNTIME_TAG"
fi

echo "Building lightweight detector application: $APP_TAG"
docker build \
  --network host \
  --build-arg "BASE_IMAGE=$DDS_RUNTIME_TAG" \
  -f docker/inference-jetson.Dockerfile \
  -t "$APP_TAG" \
  .
