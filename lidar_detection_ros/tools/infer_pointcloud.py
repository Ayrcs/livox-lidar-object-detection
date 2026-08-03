#!/usr/bin/env python3
"""Run the pilot PointPillars model on one canonical binary point cloud."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ROS_PYTHON_ROOT = REPOSITORY_ROOT / "lidar_detection_ros"
if str(ROS_PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(ROS_PYTHON_ROOT))

from lidar_detection_ros.backends import MMDetection3DBackend  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pointcloud", type=Path, help="Binary float32 point cloud with x,y,z,intensity")
    parser.add_argument("--model-dir", type=Path, required=True, help="Packaged model registry directory")
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--score-threshold", type=float, default=0.10)
    parser.add_argument("--output", type=Path, help="Optional JSON output file")
    return parser.parse_args()


def read_pointcloud(path: Path) -> np.ndarray:
    flat = np.fromfile(path, dtype=np.float32)
    if flat.size == 0 or flat.size % 4:
        raise ValueError(f"{path} does not contain a non-empty N x 4 float32 cloud")
    return flat.reshape(-1, 4)


def main() -> int:
    args = parse_args()
    points = read_pointcloud(args.pointcloud)
    backend = MMDetection3DBackend(
        config_path=args.model_dir / "config.py",
        checkpoint_path=args.model_dir / "model.pth",
        device=args.device,
        class_names=("ball",),
        score_threshold=args.score_threshold,
        fixed_box_sizes={"ball": (0.22, 0.22, 0.22)},
    )

    started = time.perf_counter()
    detections = backend.predict(points)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    payload = {
        "pointcloud": str(args.pointcloud),
        "point_count": int(len(points)),
        "device": args.device,
        "score_threshold": args.score_threshold,
        "inference_ms": elapsed_ms,
        "detections": [detection.to_dict() for detection in detections],
    }
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
